./.env
data_mode='dev' # Options: 'dev', 'train'
data_path='data/dev/custom_query.json' # This is the file created with the question & datatype

config="./run/configs/CHESS_IR_CG_UT.yaml"

num_workers=1 # Number of workers to use for parallel processing, set to 1 for no parallel processing

python3 -u ./src/main.py --data_mode ${data_mode} --data_path ${data_path} --config "$config" \
        --num_workers ${num_workers} --pick_final_sql true 

