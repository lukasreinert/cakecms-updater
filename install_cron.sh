#!/usr/bin/bash

script_path=$(realpath "$0" | sed 's|\(.*\)/.*|\1|')
folder_path=$(dirname "$script_path")


read -p "[Cron] Do you wish to install a cronjob that runs every 15 minutes? [Y/n] " install_auto_update

if [ "$install_auto_update" == "" ] || [ "$install_auto_update" == "y" ] || [ "$install_auto_update" == "Y" ]
then
    echo "[Cron] Installing cronjob"
    (crontab -l; echo ""; echo "# cakecms"; echo "*/15 8-18 * * 1-5 python3 $folder_path/cakecms.py"; echo "") | crontab -
    echo "[Cron] Done"
else
    echo "[Cron] Aborted"
fi


echo ""
