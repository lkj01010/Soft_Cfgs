### 去掉dock图标

拷贝系统python，修改app的[info.plist]，加上
```xml
    <key>LSUIElement</key>
	<string>1</string>
```
脚本使用这个python执行

### 包装成app
```shell
#!/usr/bin/env bash

APPNAME=${2:-$(basename "${1}" '.sh')};
DIR="${APPNAME}.app/Contents/MacOS";

if [ -a "${APPNAME}.app" ]; then
	echo "${PWD}/${APPNAME}.app already exists :(";
	exit 1;
fi;

mkdir -p "${DIR}";
cp "${1}" "${DIR}/${APPNAME}";
chmod +x "${DIR}/${APPNAME}";

echo "${PWD}/$APPNAME.app";
```
用这个脚本调用sh,如
```shell
    appify myScript.sh "AppName"
```
即可打包成一个app

### 修改app图标

选择app，cmd+i，copy一个png，点击信息ui的左上角appIcon，icon被蓝框选中，plast,即可更换刚才copy的png