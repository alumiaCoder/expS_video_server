#! /bin/bash

password_1=<DEFINE_HERE>
password_2=<DEFINE_HERE>

sudo mount -t cifs -o username="phd",password=$password_1,uid=$(id -u),gid=$(id -g),forceuid,forcegid, //193.168.1.3/e /mnt/share
sudo mount -t cifs -o username="phd",password=$password_2,uid=$(id -u),gid=$(id -g),forceuid,forcegid, '//193.168.1.4/Public' /mnt/share_monitor
sleep 1
/usr/bin/python <PATH_TO_MAIN_RASP_SCRIPT>