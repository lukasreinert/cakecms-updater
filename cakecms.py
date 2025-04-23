from cakecms_lib import *
from bs4 import BeautifulSoup
import requests
import re

with open(get_path('config.json'), 'r') as config_json:
    cakecms = json.load(config_json)


def gather_points(points_dict, accordion_items):
    for accordion_item in accordion_items:
        # get title and if present total points
        # order-1 indicates title, order-3 indicates total points
        section = accordion_item.find_all('div', {'class': 'order-1'})[0].text.lower().replace(' ', '_')
        total_points_div = accordion_item.find_all('div', {'class': 'order-3'})
        total_points = ''
        if len(total_points_div) > 0:
            total_points = total_points_div[0].text[1:-1]

        # for each entry in the table get its information
        points_table = accordion_item.find_all('table', {'class': 'table'})[0]
        table_header = [elem.text for elem in points_table.select('tr')[0].select('th,td')]
        name_col = table_header.index('Name')
        points_col = table_header.index('Points')
        if not section in points_dict:
            points_dict[section] = {}
        if total_points != '':
            points_dict[section]['total_points'] = total_points
        for items in points_table.select('tr')[1:]:
            item = [elem.text for elem in items.select('th,td')]
            if item[points_col] != '' and not 'n.a.' in item[points_col]:
                points_dict[section][item[name_col].lower().replace(' ', '_')] = item[points_col]


def update_points(session):
    for course in cakecms['courses']:
        
        # skip if points are disabled
        if not cakecms['courses'][course]['points']:
            continue

        # get and filter html source code and store online state
        page_source = session.get(cakecms['courses'][course]['url'] + '/testings/viewresult').text
        points_section = BeautifulSoup(page_source, 'html.parser').find(id='content').find_all('section')
        if len(points_section) == 0:
            logging(f"No points section found in {course}")
            return
        
        accordion_items = points_section[0].find_all('div', {'class': 'accordion-item'})
        new_dict = mkdict('points')
        gather_points(new_dict['points'], accordion_items)

        # prepare for comparison between local state and online state
        with open(get_path('data.json'), 'r') as course_json:
            data_dict = json.load(course_json)
        if not course in data_dict:
            data_dict[course] = {}
        if not 'points' in data_dict[course]:
            data_dict[course]['points'] = {}

        # check if online state is different from local state
        # if so update local state and send notification
        if found_new_points(course, data_dict[course]['points'], new_dict['points']):
            data_dict[course]['points'] = new_dict['points']
            json_object = json.dumps(data_dict, indent=4)
            with open(get_path('data.json'), 'w') as course_json:
                course_json.write(json_object)


def gather_materials(course, subdict, accordion_items):
    for accordion_item in accordion_items:
        
        # get accordion title
        section_title = accordion_item.find('button', {'class': 'accordion-button'}).text.lower().replace(' ', '_')
        section_title = re.sub(r'[\n\t\r]*', '', section_title)
        section_title = section_title.replace('_(', '(')
        section_title = section_title.split("(")[0]

        # get table in accordion and skip if empty
        materials_tables = accordion_item.find_all('table', {'class': 'table'})
        if len(materials_tables) == 0:
            continue

        # prepare storing the information
        materials_table = materials_tables[0]
        if not section_title in subdict:
            subdict[section_title] = {}

        # for each entry in the table get its information
        for items in materials_table.select('tr'):
            url = items.find('a', href=True)['href']
            if not 'http' in url:
                url = url[1:]
                url = url[url.find('/'):]
                url = cakecms['courses'][course]['url'] + url
            row = [elem.text for elem in items.select('td')]
            item = row[0]
            description = row[1].replace('\n', '').strip()
            item = item.lower().replace('\n ', '').replace('\n', '').replace(' ', '_')
            if item != '':
                version = ''
                name = item
                if ',_rev_' in item:
                    version = item.split(',_rev_')[1].split(')')[0]
                    name = "_(".join(item.split('_(')[0:-1])
                subdict[section_title][name] = {}
                subdict[section_title][name]['version'] = version
                subdict[section_title][name]['url'] = url
                subdict[section_title][name]['description'] = description


def update_materials(session):
    for course in cakecms['courses']:

        # skip if points are disabled
        if not cakecms['courses'][course]['materials']:
            continue

        # get and filter html source code and store online state
        page_source = session.get(cakecms['courses'][course]['url'] + '/materials').text
        materials_section = BeautifulSoup(page_source, 'html.parser').find(id='content')
        accordion_items = materials_section.find_all('div', {'class': 'accordion-item'})
        new_dict = mkdict('materials')
        gather_materials(course, new_dict['materials'], accordion_items)

        # prepare for comparison between local state and online state
        with open(get_path('data.json'), 'r') as course_json:
            data_dict = json.load(course_json)
        if not course in data_dict:
            data_dict[course] = {}
        if not 'materials' in data_dict[course]:
            data_dict[course]['materials'] = {}

        # check if online state is different from local state
        # if so update local state and send notification
        if found_new_materials(course, data_dict[course]['materials'], new_dict['materials']):
            data_dict[course]['materials'] = new_dict['materials']
            json_object = json.dumps(data_dict, indent=4)
            with open(get_path('data.json'), 'w') as course_json:
                course_json.write(json_object)


if __name__ == '__main__':
    try:
        session = requests.session()
        login(session)
        
        validate_data()
        
        logging('Updating points')
        update_points(session)

        logging('Updating materials')
        update_materials(session)
        
        logout(session)

    except Exception as e:
        logging(e, level='ERROR')
