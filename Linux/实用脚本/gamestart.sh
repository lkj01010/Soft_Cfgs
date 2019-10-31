killall arenasrv
killall centersrv
# nohup go run /home/gopath/src/_/moba-srv/centersrv.go >log/center.log 2>&1 &
# nohup go run /home/gopath/src/_/moba-srv/arenasrv.go >log/arena.log 2>&1 &


./arenastart.sh
./centerstart.sh
