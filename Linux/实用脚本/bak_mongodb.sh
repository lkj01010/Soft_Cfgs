#!/bin/sh

DBPATH=/opt/mongodb-setup/mongodb-linux-x86_64-rhel62-3.0.6
#mongodump path
DUMP=$DBPATH/bin/mongodump

#tmp bak path
OUT_DIR=/var/mongodb/data/db_bak_now

#bak save path
TAR_DIR=/var/mongodb/data/db_bak_list

#current time
DATE=`date +%Y_%m_%d_%H%M`

#account
DB_USER=midstream
#password
DB_PASS=123456

#nearest days count that save bak on
DAYS=7

#bak filename
TAR_BAK="mongod_bak_$DATE.tar.gz"

cd $OUT_DIR
rm -rf $OUT_DIR/*
mkdir -p $OUT_DIR/$DATE

#save all dbs
$DUMP -o $OUT_DIR/$DATE

#pack
tar -zcvf $TAR_DIR/$TAR_BAK $OUT_DIR/$DATE

#del baks 7 days ago
find $TAR_DIR/ -mtime +$DAYS -delete




