export PATH=$PATH:/usr/local/git/bin

export GOROOT=/usr/local/go
export GOBIN=$GOROOT/bin
export GOPKG=$GOROOT/pkg/tool/linux_amd64
export GOARCH=amd64
export GOOS=linux
export GOPATH=/home/gopath
export PATH=$PATH:$GOBIN:$GOPKG:$GOPATH/bin

export PATH=$PATH:/opt/bin
export PATH=$PATH:/opt/gitea

##############################
#设置history格式
export HISTTIMEFORMAT="[%Y-%m-%d %H:%M:%S] [`who am i 2>/dev/null| \
awk '{print $NF}'|sed -e 's/[()]//g'`] "
 
#登录时清空当前缓存
echo "" > .bash_history
 
#记录shell执行的每一条命令
export PROMPT_COMMAND='\
if [ -z "$OLD_PWD" ];then
export OLD_PWD=$PWD;
fi;
if [ ! -z "$LAST_CMD" ] && [ "$(history 1)" != "$LAST_CMD" ]; then
logger -t `whoami`_shell_cmd "[$OLD_PWD]$(history 1)";
fi ;
export LAST_CMD="$(history 1)";
export OLD_PWD=$PWD;'
##############################
