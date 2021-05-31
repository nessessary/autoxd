# run pearson_clust.py

# find \r, not handle
#echo "$1";
python pearson_clust.py --multi --code=$1
python pearson_clust.py --second --code=$1
python pearson_clust.py --genimg --code=$1
#python label_submit/flask_submit.py