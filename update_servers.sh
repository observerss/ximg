#!/bin/bash 
USER="root"
LOCAL_PATH="/var/www/ximg-mongo"
SETTING_FILE="settings.py"
REMOTE_PATH="/var/www/ximg-mongo"
RESTART_IMG="$REMOTE_PATH/images/restart.sh" 
RESTART_APP="$REMOTE_PATH/restart.sh" 
APP_SERVERS=("hub.obmem.info" "app1.ximg.in" "app2.ximg.in")
IMG_SERVERS=()
#IMG_SERVERS=("i1.ximg.in" "i2.ximg.in" "i3.ximg.in" "i4.ximg.in")

# update files to IMG_SERVERS
echo "Updating Image Servers..."
for srv in ${IMG_SERVERS[*]}
do
    printf "\nRsyncing files to $srv...\n"
    rsync -avze ssh --exclude="$SETTING_FILE" "$LOCAL_PATH/" $USER@$srv:"$REMOTE_PATH/" 
    printf "\nRestarting remote service...\n"
    bash -c "ssh -f $USER@$srv '$RESTART_IMG'"
done

# update files to APP_SERVERS
echo "Updating App Servers..."
for srv in ${APP_SERVERS[*]}
do
    printf "\nRsyncing files to $srv...\n"
    rsync -avze ssh --exclude="$SETTING_FILE" "$LOCAL_PATH/" $USER@$srv:"$REMOTE_PATH/"
    printf "\nRestarting remote service...\n"
    bash -c "ssh -f $USER@$srv 'cd $REMOTE_PATH;$RESTART_APP'"
done
