python run.py \
       --model_name_or_path=/home/nlp/shaked571/Dev/lingmess/results/final_split/aleph/model \
       --output_file=/home/nlp/shaked571/Dev/lingmess/results/final_split/aleph/test.hebrew.output.jsonlines \
       --test_file=/home/nlp/shaked571/Dev/lingmess/data/hebrew/test.hebrew.jsonlines \
       --eval_split=test \
       --max_tokens_in_batch=15000 \
       --device=cuda:3 \
       --experiment_name="lingmess_aleph_heb_test"

