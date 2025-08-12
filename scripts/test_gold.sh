#!/bin/bash
which python
base_data_dir="/home/nlp/shaked571/pycharm_over_ssh/np/np_data"
base_project_dir="/home/nlp/shaked571/pycharm_over_ssh/np"
declare -a posOpt=("no_possessive" "with_possessive")

# "gold_seg/ud_parse" "amit_seg/stanza_parse"
for
  for pos in "${posOpt[@]}"
  do
    for (( i = 1; i <= 3; i++ ))
    do
          echo "Output: $base_data_dir/$pos/flat"
          python /home/nlp/shaked571/pycharm_over_ssh/np/bert_train/trainer.py \
          --model_name_or_path "$base_project_dir/gold_seg_ud_parse_${pos}_flat_seed_${i}_epoch_15" \
          --data_set_dir "$base_data_dir/$seg/$pos/flat"  \
          --gold_validation "${base_data_dir}/test_data/gold/${pos}/flat/dev.txt" \
          --gold_test "${base_data_dir}/test_data/gold/${pos}/flat/test.txt" \
          --output_dir "test_result/$seg"  \
          --do_eval  \
          --do_predict  \
          --overwrite_output_dir \
          --fp16 \
          --seed "$i"
      done
   done


