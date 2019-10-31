killall -9 arenasrv


# nohup go run /home/gopath/src/_/moba-srv/arenasrv.go >log/arena.log 2>&1 &


root=/home/gopath/src/_/moba-srv

cd $root

if [ "$1" = '-r' ]; then
    go build arenasrv.go
else
    go build -gcflags "all=-N -l" arenasrv.go
fi

nohup ./arenasrv >~/arena.log 2>&1 &


echo arena start