#!/bin/bash
search=hsbot.py
service=hsbot

if (( $(ps -ef | grep -v grep | grep $search | wc -l) > 0 ))
then
echo "$service is running!!!"
else
/etc/init.d/$service start
fi
