MONGOD=/usr/bin/mongod
LOG=/var/opt/mongo/log/mongod.log
DB=/var/opt/mongo/data

$MONGOD --logpath=$LOG --logappend --dbpath=$DB --port=27017 --bind_ip_all --repair

