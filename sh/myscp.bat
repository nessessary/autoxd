@echo off

set exec="C:\MyApp\putty\PSCP.EXE"
set z="c:\Program Files\7-Zip\7z.exe"

if exist autoxd.tar ( del autoxd.tar )
if exist autoxd.tar.gz ( del autoxd.tar.gz)
%z% a -ttar autoxd.tar ../../autoxd/
%z% a -tgzip autoxd.tar.gz autoxd.tar
%exec% -sftp -l wk -pw Wk222333 autoxd.tar.gz wk@192.168.1.6:/home/wk/work