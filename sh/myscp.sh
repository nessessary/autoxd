#!/usr/bin/expect -f
# don't call , call by tar_and_scp.sh
set timeout 10
#tar -zcf  - autoxd |openssl des3 -salt -k password | dd of=autoxd.des3
#spawn scp /Users/wangkang/Desktop/autoxd.tar.gz root@mydocker.com:/home/wk/
spawn scp autoxd.tar.gz root@192.168.1.6:/home/wk/work
expect {
	"*assword:"
	{ send "Wk222333\n"}
}
interact  
