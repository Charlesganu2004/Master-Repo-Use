@echo off
setlocal
if not defined BASE_DIR set "BASE_DIR={{HOME}}"
"{{HOME}}\.local\lib\kb\.venv\Scripts\python.exe" "{{HOME}}\.local\lib\kb\kb.py" %*
