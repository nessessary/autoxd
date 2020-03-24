import os
from autoxd import stock
import optparse,sys
#from autoxd.agl import array_val_to_pos

def run(start_code, num):
    cmds = ['python pearson_clust.py --multi --code=%s',\
            'python pearson_clust.py --second --code=%s',\
            'python pearson_clust.py --genimg --code=%s'\
            ]
    codes = stock.get_codes()
    #index = array_val_to_pos(codes, start_code)
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
    
    run(options.start_code, options.num)
        