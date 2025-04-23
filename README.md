# cakecms-updater

This script notifies you about updated materials and updated points.
Compatible with the Saarland University's "cakecms" only.

## Features

-   Effortless setup
-   Basic login and logout
-   Support for MFA
-   Sending notifications via mail using SMTP
-   Sending notifications via discord using webhooks
-   Automatic cronjob installation via the correspoding shell script

## Requirements

-   Python 3.6+ (Tested with Python 3.12.3)

## Setup

Install neccessary python packages with `pip install -r requirements.txt`

What are they used for?

-   **beautifulsoup4:** Parses and extracts data from HTML or XML pages.
-   **discord-webhook:** - Sends automated messages or alerts to Discord channels.
-   **markdownify:** - Converts HTML content into clean Markdown format.
-   **pyotp:** - Generates time-based one-time passwords (2FA codes).
-   **requests:** - Handles HTTP requests for interacting with web APIs or scraping sites.

## Notice

The included config is just an example configuration and needs to be configured. You must enter your personal credentials and verify all data and links. You can add arbitrarily many entires for cms and courses and name them as you wish. However, note that adding more courses lead to a longer execution time. It's recommended to only scan for courses taken in the current semester and delete data from courses in the data.json after taking them. This is because the whole json will be converted into a dictionary which otherwise leads to an unnecessary overhead.

## Update frequency

I ask you to not increase the frequency of scans to more than once every 15 minutes as this would lead to performance issues on the server side. This script shall not be abused to cause any harm - use it with care!
Feel free to optimize the schedules according to your personal needs.

I recommend `0 8-15 * * 1-5` which runs monday to friday every hour from 8am until 3pm.
If you need help generating your own cronjob I recommend using [crontab.guru](https://crontab.guru/#) which assists you.
