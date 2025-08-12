#!/bin/bash
which python
base_data_dir="/home/nlp/shaked571/pycharm_over_ssh/np/np_data"
declare -a baseParse=("gold_seg/stanza_parse")
declare -a posOpt=("no_possessive" "with_possessive")
declare -a nestOpt=("flat" "nested")
# "gold_seg/ud_parse" "amit_seg/stanza_parse"

for seg in "${baseParse[@]}"
do
  for pos in "${posOpt[@]}"
  do
    for nest in "${nestOpt[@]}"
    do
      for (( i = 1; i <= 3; i++ ))
      do
            echo "Output: $base_data_dir/$seg/$pos/$nest"
            python /home/nlp/shaked571/pycharm_over_ssh/np/bert_train/trainer.py \
            --model_name_or_path biu-nlp/alephbert-base \
            --data_set_dir "$base_data_dir/$seg/$pos/$nest"  \
            --output_dir output  \
            --do_train  \
            --do_eval  \
            --do_predict  \
            --num_train_epochs 15 \
            --overwrite_output_dir \
            --fp16 \
            --seed "$i"
      done
   done
  done
done

