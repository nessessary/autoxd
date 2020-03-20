import os
from autoxd import stock

cmd = 'python pearson_clust.py --multi --code=%s'
codes = stock.get_codes()
codes = codes[1:10]
for code in codes:
    cur_cmd = cmd % (code)    
    print(cur_cmd)
    os.system(cur_cmd)