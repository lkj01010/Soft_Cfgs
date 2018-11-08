on run argv
	set curPath to (item 1 of argv)
	set cmd to (item 2 of argv)
	tell application "Terminal"
		do script "cd " & curPath & cmd
	end tell
end run