@echo off

rem 从远程获取数据

set exec="C:\MyApp\putty\PSCP.EXE"
%exec% -sftp -l wk -pw Wk222333 -r wk@192.168.1.6:/home/wk/work/autoxd/autoxd/cnn_boll/datas ../autoxd/cnn_boll/
%exec% -sftp -l wk -pw Wk222333 -r wk@192.168.1.6:/home/wk/work/autoxd/autoxd/cnn_boll/img_labels ../autoxd/cnn_boll/
