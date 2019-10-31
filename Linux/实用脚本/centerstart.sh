killall -9 centersrv

# nohup go run /home/gopath/src/_/moba-srv/arenasrv.go >log/arena.log 2>&1 &

root=/home/gopath/src/_/moba-srv

cd $root

if [ "$1" = '-r' ]; then
    go build centersrv.go
else
    go build -gcflags "all=-N -l" centersrv.go
fi

# nohup $GOBIN/centersrv >log/center.log 2>&1 &
nohup ./centersrv >~/center.log 2>&1 &

echo center start
