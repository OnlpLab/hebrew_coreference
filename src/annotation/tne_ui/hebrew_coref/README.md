# Annotation and Modeling of Hebrew Coreference Resolution

## Load the data to a db

python load_to_db.py -in hebrew_coref/create_agreement_files/coref_docs_2_tag/tne_conll -out data -db hebrew_v4.dat

## Run the server

python --debug -db_dir data -db hebrew_v4.dat

## Scripts explanation

1. In order to read new annotations we use `read_annotation.sh` **bash script**.
   Which does the following:
    1. The script would read and save in the dedicated folder all the new annotation unless they were already saved in
       the `.cache/parsed_msg.txt` file.
    2. After reading the new annotations, the script creates 2 files: `annotators.txt` and `output.jsonl`
    3. Later, the script runs
       `coref_results_to_db.py -in annotation_results/output.jsonl -db_dir data -db hebrew_v4.dat -a annotation_results/annotators.txt`
       In order to update the `hebrew_v4.data`
    4. If Mentions
    5. Lastly, in order to allow the annotator to tag the consolidation we:
        1. Adding the data to the consolidation UI, using
           `get_coref_intersection.py -in annotation_results/output.jsonl -db_dir data -db hebrew_v4.dat `
           1.By `get_coref_intersection.py` we update the sql table of `data/hebrew_v4.dat`
    6. You need to upload it using GIT.
2. How to run agreement After finishing tagging the review we check the agreement using:
    1. Run the bash script `read_annotation.sh`  to download the annotations
    2. Run the bash script `create_conll_files_from_annotations.sh` to create the conll files
    4. It would create *all* the conllu files  (including one that were already created - it is done using the docs in
       the DB)
    5. manually copy the relevant documents in to conllu_out_annotation/[num]_batch
    6. create an agreement_round_[num] jupyter notebook change the folder path and run it