# cakecms-updater
This script notifies you about updated materials an entered or updated points.
Compatible with the Saarland Universities "cakecms" only.

## Features
- Basic login and logout (using requests)
- Support for MFA
- Sending emails using [Brevo](https://www.brevo.com/) with its API as SMTP Server
- Automatic cronjob installation via the correspoding shell script
- More features are planned (including discord notifications)

## Notice
The included config is  just an example configuration and need to be configured. You must enter your personal credentials and verify all data and links. You can add arbitrarily many entires for cms and courses and name them as you wish. However, note that adding more courses lead to a longer execution time. It's recommended to only scan for courses taken in the current semester and delete data from courses in the data.json after taking them as the whole json will be converted into a dictionary which otherwise leads to an unnecessary overhead.

## Update frequency
I ask you to not increase the frequency of scans to more than once every 15 minutes as this would lead to performance issues on the server side. This script shall not be abused to cause any harm - use it with care!
Feel free to optimize the schedules according to your personal needs.

I recommend 
`*/15 8-18 * * 1-5`
which runs monday to friday from 8am until 6pm every 15 minutes.
If you need help generating your own cronjob I recommend using [crontab.guru](https://crontab.guru/#) which assists you.