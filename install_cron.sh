#!/usr/bin/bash

script_path=$(realpath "$0" | sed 's|\(.*\)/.*|\1|')
folder_path=$(dirname "$script_path")

read -p "[Cron] Do you wish to install the optimized cronjob? [y/N] " install_auto_update

if [ "$install_auto_update" == "y" ] || [ "$install_auto_update" == "Y" ]
then
    echo "[Cron] Installing cronjob"
    (crontab -l; echo ""; echo "# cakecms"; echo "0 8-15 * * 1-5 python3 /root/cakecms/cakecms.py"; echo "") | crontab -
    echo "[Cron] Installed successfully"
else
    echo "[Cron] Not installed"
fi

echo ""