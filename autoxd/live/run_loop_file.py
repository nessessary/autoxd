import subprocess
import time
import sys
from datetime import datetime

# 要运行的Python脚本文件名
script_name = sys.argv[1]

while True:
    # 使用subprocess运行脚本并捕获输出
    result = subprocess.run(["python", script_name], capture_output=True, text=True)
    
    #print("\r" + " " * 40 + "\r", end="")
    # 打印标准输出
    if result.stdout:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\rCurrent time: {current_time} {result.stdout}", end="")
    
    # 如果有错误输出，打印错误信息
    if result.stderr:
        print("Error:")
        print(result.stderr)
    
    # 每10秒运行一次
    time.sleep(20)