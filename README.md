# cakecms-updater
This script notifies you about updated materials an entered or updated points.
Compatible with the Saarland Universities "cakecms" only.

## Features
- Basic login and logout
- Supports login secured with 2FA
- Sending emails using [Brevo](https://www.brevo.com/) with its API as SMTP Server
- Automatic cronjob installation via the correspoding shell script or use [*/15 8-18 * * 1-5](https://crontab.guru/#*/15_8-18_*_*_1-5) as cron schedule

## Info
The included config is NOT ready to use but just an example configuration! You must enter your personal credentials and verify all data and links. You can add arbitrarily many entires for cms and courses and name them as you wish. However, note that adding more courses lead to a longer execution time. It's recommended to only scan for courses taken in the current semester and delete data for courses from the data.json after taking them as the whole json will be converted to a dictionary.

## Scan frequency
I kindly ask you to not increase the frequency of scans to more than once every 15 minutes as this leads to performance issues on the server side. This script shall not be abused to cause any harm - use it with care!
Feel free to optimize the schedules. I personally recommend [crontab.guru](https://crontab.guru/#*/15_8-18_*_*_1-5)