#!/bin/bash

STATE="/tmp/last-lclb-run.state"
touch $STATE
LAST=$(cat $STATE)
CUR=$(echo $ETCD_WATCH_VALUE | md5sum | awk '{print $1}')
echo $CUR > $STATE

if [ "$CUR" != "$LAST" ]; then
  echo running lclb..
  docker run -e ETCD_WATCH_VALUE=$ETCD_WATCH_VALUE -e ETCD_WATCH_KEY=$ETCD_WATCH_KEY -e ETCD_WATCH_MODIFIED_INDEX=$ETCD_WATCH_MODIFIED_INDEX polvi/lclb python lclb.py
else
  echo doing nothing..
fi

