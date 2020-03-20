#!/bin/bash
#tar -zcf  - autoxd |openssl des3 -salt -k password | dd of=autoxd.des3
tar cfz autoxd.tar.gz ../../autoxd
#expect myscp.sh
#sshpass -p Wk222333 scp autoxd.tar.gz wk@192.168.1.6:/home/wk/work
