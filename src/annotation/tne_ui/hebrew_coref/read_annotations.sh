#!/bin/bash

PROJECT_DIR=${1:-'/Users/s0g0a87/studies/tne_ui'}
PYTHON_ENV=${2:-'/Users/s0g0a87/anaconda3/envs/hebrewCoreference'}

cd $PROJECT_DIR/hebrew_coref/download_annotated_coref || exit
$PYTHON_ENV/bin/python $PROJECT_DIR/hebrew_coref/download_annotated_coref/read_annotation.py

cd $PROJECT_DIR || exit
$PYTHON_ENV/bin/python $PROJECT_DIR/coref_results_to_db.py -in annotation_results/coref/output.jsonl -db_dir data -db hebrew_v4.dat -a annotation_results/coref/annotators.txt
$PYTHON_ENV/bin/python $PROJECT_DIR/mentions_results_to_db.py -in annotation_results/mention/output.jsonl -db_dir data -db hebrew_v4.dat -a annotation_results/mention/annotators.txt
$PYTHON_ENV/bin/python $PROJECT_DIR/get_coref_intersection.py -db_dir data -db hebrew_v4.dat

cd $PROJECT_DIR/hebrew_coref/create_final_mentions_table || exit
$PYTHON_ENV/bin/python $PROJECT_DIR/hebrew_coref/create_final_mentions_table/create_final_mention_db.py $PROJECT_DIR/data/hebrew_v4.dat
cd $PROJECT_DIR/hebrew_coref/create_agreement_files || exit
$PYTHON_ENV/bin/python $PROJECT_DIR/hebrew_coref/create_agreement_files/add_token_loc_to_nps.py -db_dir ../../data -db hebrew_v4.dat -c coref_docs_2_tag/base -t coref_docs_2_tag/tne_conll -o coref_docs_2_tag/tne_conll_final_mentions -nc

cd $PROJECT_DIR || exit
$PYTHON_ENV/bin/python $PROJECT_DIR/get_coref_intersection.py -db_dir data -db hebrew_v4.dat
echo Finish Run!