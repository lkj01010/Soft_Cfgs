killall gitea
killall mongod
killall arenasrv
killall centersrv
nohup gitea &
nohup /root/mongod-start.sh &
nohup go run /home/gopath/src/_/moba-srv/centersrv.go &
nohup go run /home/gopath/src/_/moba-srv/arenasrv.go &