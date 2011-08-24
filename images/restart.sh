#!/bin/bash
# Restart api_server 
kill -9 `pgrep -f api_server` ;
sleep 0.5;
ulimit -s 1024;
ulimit -n 2048;
python /var/www/ximg-mongo/images/api_server.py --log_file_max_size=10240000 --log_file_num_backups=10 --log_file_prefix=/var/www/ximg-mongo/logs/api8000.log --port=8000 &
python /var/www/ximg-mongo/images/api_server.py --log_file_max_size=10240000 --log_file_num_backups=10 --log_file_prefix=/var/www/ximg-mongo/logs/api8001.log --port=8001 &
printf "Restart OK"

