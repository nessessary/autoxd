import os
from autoxd import stock
import optparse,sys
from autoxd.cnn_boll import judge_boll_sign

def run(start_code, num):
    cmds = ['python pearson_clust.py --multi --code=%s',\
            'python pearson_clust.py --second --code=%s',\
            'python pearson_clust.py --genimg --code=%s'\
            ]
    codes = judge_boll_sign.codes
    codes.sort()
    #print(codes)
    index = codes.index(start_code)+1
    codes = codes[index:index+num]
    for code in codes:
        for cmd in cmds:
            cur_cmd = cmd % (code)    
            print(cur_cmd)
            os.system(cur_cmd)
        
        
if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('--start_code', dest='start_code', action="store", type="string")
    parser.add_option('--num', dest='num', action="store", type="int")
    
    options, args = parser.parse_args(sys.argv[1:])
    
    class MyOptions:
        start_code = 0
        num = 0
    if 0: options = MyOptions()
    if options.start_code is None or options.num is None:
        print('--start_code=x --num=1-n')
        exit(0)
    run(options.start_code, options.num)
        