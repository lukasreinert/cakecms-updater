from bs4 import BeautifulSoup
from datetime import datetime
from discord_webhook import DiscordWebhook
from markdownify import markdownify
from os import path
from requests.exceptions import Timeout
from sib_api_v3_sdk.rest import ApiException
import json
import pyotp
import sib_api_v3_sdk
import time


def get_path(file):
    dirname = path.dirname(__file__)
    return path.join(dirname, file)


with open(get_path('config.json'), 'r') as config_json:
    cakecms = json.load(config_json)


def validate_data():
    if not path.exists(get_path('data.json')):
        f = open(get_path('data.json'), 'w')
        f.write('{}')
        f.close()


def mkdict(section):
    new_dict = {
        section: {}
    }
    return new_dict


def logging(msg, level='LOG'):
    with open(get_path('cakecms.log'), 'a') as log:
        time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.write(f'[{level}][{time_stamp}] {msg}\n')


def send_notification(subject, main_info, all_info=''):        
    if cakecms['notifications']['discord']['enabled']:
        send_discord(subject, main_info, all_info='')  
        
    if cakecms['notifications']['mail']['enabled']:
        send_email(subject, main_info, all_info='')


def send_discord(subject, main_info, all_info=''):
    html_content = '<html><body>'
    html_content += subject
    html_content += main_info
    html_content += all_info
    html_content += '</body></html>'
    md_content = markdownify(html_content)

    try:
        for url in cakecms['notifications']['discord']['webhooks']:
            webhook = DiscordWebhook(url=url, content=md_content)
            webhook.execute()
        logging(f'Send discord: {subject}')
    except Timeout as e:
        logging(f'Exception when sending a discord message: {e}', 'ERROR')


def send_email(subject, main_info, all_info=''):        
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = cakecms['notifications']['mail']['api_key']
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    html_content = '<html><body>'
    html_content += main_info
    html_content += all_info
    html_content += '</body></html>'
    sender = cakecms['notifications']['mail']['sender']

    try:
        for receiver in cakecms['notifications']['mail']['receivers']:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender=sender, to=[receiver], subject=subject, html_content=html_content)
            api_instance.send_transac_email(send_smtp_email)
        logging(f'Send email: {subject}')
    except ApiException as e:
        logging('Exception when calling SMTPApi -> send_transac_email: %s\n' % e, 'ERROR')


def login(session):
    for cms in cakecms['cms']:
        # get csrf token
        req = session.get(cakecms['cms'][cms]['url'] + '/system/users/login')
        html = BeautifulSoup(req.text, 'html.parser')
        token_key = html.find('input', {'name': 'data[_Token][key]'}).attrs['value']
        token_fields = html.find('input', {'name': 'data[_Token][fields]'}).attrs['value']
        token_unlocked = html.find('input', {'name': 'data[_Token][unlocked]'}).attrs['value']

        # prepare and send payload to login
        payload = {
            '_method': "POST",
            'data[User][username]': cakecms['cms'][cms]['username'],
            'data[User][password]': cakecms['cms'][cms]['password'],
            'data[_Token][key]': token_key,
            'data[_Token][fields]': token_fields,
            'data[_Token][unlocked]': token_unlocked,
            'data[Auth][remember_me]': "0",
            'data[User][redirect]': cakecms['cms'][cms]['url'] + '/system/landing',
        }

        req = session.post(cakecms['cms'][cms]['url'] + '/system/users/login', data=payload)

        if ('Passwort' in req.text or 'Password' in req.text):
            logging(f'Login failed for {cms}', level='ERROR')
            exit()

        if not cakecms['cms'][cms]['2FA']['enabled']:
            continue

        # get csrf token and prepare totp
        html = BeautifulSoup(req.text, 'html.parser')
        token_key = html.find('input', {'name': 'data[_Token][key]'}).attrs['value']
        token_fields = html.find('input', {'name': 'data[_Token][fields]'}).attrs['value']
        token_unlocked = html.find('input', {'name': 'data[_Token][unlocked]'}).attrs['value']

        # wait if totp is about to become invalid
        until_new_topt = 30 - int(datetime.now().strftime('%S')) % 30
        if until_new_topt < 3:
            time.sleep(until_new_topt + 1)
        totp = pyotp.TOTP(cakecms['cms'][cms]['2FA']['secret_base32'])

        # prepare and send payload to login
        payload = {
            '_method': "POST",
            'data[authenticator]': totp.now(),
            'data[_Token][key]': token_key,
            'data[_Token][fields]': token_fields,
            'data[_Token][unlocked]': token_unlocked,
        }

        res = session.post(cakecms['cms'][cms]['url'] + '/system/TwoFA/checkSecondFactorMethod', data=payload)

        if ('Please enter a token' in res.text):
            logging(f'2FA failed for {cms}', level='ERROR')
            exit()


def logout(session):
    for cms in cakecms['cms']:
        # get csrf token
        req = session.get(cakecms['cms'][cms]['url'])
        html = BeautifulSoup(req.text, 'html.parser')
        method = html.find('input', {'name': '_method'}).attrs['value']
        token_key = html.find('input', {'name': 'data[_Token][key]'}).attrs['value']
        token_fields = html.find('input', {'name': 'data[_Token][fields]'}).attrs['value']
        token_unlocked = html.find('input', {'name': 'data[_Token][unlocked]'}).attrs['value']

        # prepare and send payload to logout
        payload = {
            '_method': "POST",
            'data[_Token][key]': token_key,
            'data[_Token][fields]': token_fields,
            'data[_Token][unlocked]': token_unlocked,
        }

        req = session.post(cakecms['cms'][cms]['url'] + '/system/users/logout', data=payload)


def get_points_diff(course_points_dict, new_points_dict):
    differences_dict_new = {}
    differences_dict_changes = {}
    for section in new_points_dict:
        if not section in course_points_dict:
            course_points_dict[section] = {}
        for elem in new_points_dict[section]:
            if not elem in course_points_dict[section]:
                if not section in differences_dict_new:
                    differences_dict_new[section] = {}
                differences_dict_new[section][elem] = new_points_dict[section][elem]
            elif course_points_dict[section][elem] != new_points_dict[section][elem]:
                if not section in differences_dict_changes:
                    differences_dict_changes[section] = {}
                differences_dict_changes[section][elem] = new_points_dict[section][elem]
    return differences_dict_new, differences_dict_changes


def found_new_points(course, course_points_dict, new_points_dict):
    differences_dict_new, differences_dict_changes = get_points_diff(course_points_dict, new_points_dict)

    if len(list(differences_dict_new)) > 0:
        subject = ''
        count = 0
        main_info = ''
        for section in differences_dict_new:
            for elem in differences_dict_new[section]:
                if subject == '':
                    subject = f'[{course.title()}] Points for {elem.replace("_", " ").title()}'
                main_info += (f'{elem.replace("_", " ").title()}:<br>'
                              f'{differences_dict_new[section][elem]}'
                              f'<br><br>')
                count += 1
        if count > 1:
            subject += f' (+{count - 1}) were entered'
        else :
            subject += ' was entered'
        students_view = cakecms['courses'][course]['url'] + '/students/view'
        all_info = f'Details: <a href="{students_view}">Students view</a>'
        send_notification(subject, main_info, all_info)

    if len(list(differences_dict_changes)) > 0:
        subject = ''
        count = 0
        main_info = ''
        for section in differences_dict_changes:
            for elem in differences_dict_changes[section]:
                if subject == '':
                    subject = f'[{course.title()}] Points for {elem.replace("_", " ").title()}'
                main_info += (f'{elem.replace("_", " ").title()}:<br>'
                              f'From: {course_points_dict[section][elem]}<br>'
                              f'To: {differences_dict_changes[section][elem]}'
                              f'<br><br>')
                count += 1
        if count > 1:
            subject += f' (+{count - 1}) have been changed'
        else:
            subject += ' has been changed'
        students_view = cakecms['courses'][course]['url'] + '/students/view'
        all_info = f'Details: <a href="{students_view}">Students view</a>'
        send_notification(subject, main_info, all_info)

    return len(list(differences_dict_new)) > 0 or len(list(differences_dict_changes)) > 0


def get_materials_diff(course_materials_dict, new_materials_dict):
    differences_dict_new = {}
    differences_dict_changes = {}
    for section in new_materials_dict:
        if not section in course_materials_dict:
            course_materials_dict[section] = {}
        for elem in new_materials_dict[section]:
            if not elem in course_materials_dict[section]:
                if not section in differences_dict_new:
                    differences_dict_new[section] = {}
                differences_dict_new[section][elem] = new_materials_dict[section][elem]
            elif course_materials_dict[section][elem]['version'] != new_materials_dict[section][elem]['version'] or \
                    course_materials_dict[section][elem]['url'] != new_materials_dict[section][elem]['url']:
                if not section in differences_dict_changes:
                    differences_dict_changes[section] = {}
                differences_dict_changes[section][elem] = new_materials_dict[section][elem]
    return differences_dict_new, differences_dict_changes


def found_new_materials(course, course_materials_dict, new_materials_dict):
    differences_dict_new, differences_dict_changes = get_materials_diff(course_materials_dict, new_materials_dict)

    if len(list(differences_dict_new)) > 0:
        subject = ''
        count = 0
        main_info = ''
        for section in differences_dict_new:
            main_info += f'<u>{section.replace("_", " ").title()}</u><br><br>'
            for elem in differences_dict_new[section]:
                if subject == '':
                    subject = f'[{course.title()}] New materials: {elem.replace("_", " ").title()}'
                main_info += f'{elem.replace("_", " ").title()}<br>'
                if differences_dict_new[section][elem]["description"] != '':
                    main_info += f'Description: {differences_dict_new[section][elem]["description"]}<br>'
                main_info += (f'Link: <a href="{differences_dict_new[section][elem]["url"]}">Download</a><br>'
                              f'<br>')
                count += 1
            main_info += '<br>'
        if count > 1:
            subject += f' (+{count - 1}) were added'
        else:
            subject += ' was added'
        materials = cakecms['courses'][course]['url'] + '/materials'
        all_info = f'<a href="{materials}">[{course.title()}] Materials</a>'
        send_notification(subject, main_info, all_info)

    if len(list(differences_dict_changes)) > 0:
        subject = ''
        count = 0
        main_info = ''
        for section in differences_dict_changes:
            main_info += f'<u>{section.replace("_", " ").title()}</u><br><br>'
            for elem in differences_dict_changes[section]:
                old_version = course_materials_dict[section][elem]['version']
                new_version = differences_dict_changes[section][elem]['version']
                if subject == '':
                    subject = f'[{course.title()}] Materials: {elem.replace("_", " ").title()}'
                main_info += f'{elem.replace("_", " ").title()} (rev {new_version})<br>'
                if differences_dict_changes[section][elem]["description"] != '':
                    main_info += f'Description: {differences_dict_changes[section][elem]["description"]}<br>'
                main_info += (f'Link: <a href="{differences_dict_changes[section][elem]["url"]}">Download</a><br><br>')
                count += 1
            main_info += '<br>'
        if count > 1:
            subject += f' (+{count - 1}) have been changed'
        else:
            subject += ' has been changed'
        materials = cakecms['courses'][course]['url'] + '/materials'
        all_info = f'<a href="{materials}">[{course.title()}] Materials</a>'
        send_notification(subject, main_info, all_info)

    return len(list(differences_dict_new)) > 0 or len(list(differences_dict_changes)) > 0
