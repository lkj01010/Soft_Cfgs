MONGOD=/usr/bin/mongod
LOG=/var/opt/mongo/log/mongod.log
DB=/var/opt/mongo/data

$MONGOD --logpath=$LOG --logappend --fork --dbpath=$DB --port=21017 --bind_ip_all --journal

