cd /Users/s0g0a87/studies/tne_ui/hebrew_coref/create_agreement_files/ || exit
/Users/s0g0a87/anaconda3/envs/hebrewCoreference/bin/python create_conll_file.py -db_dir ../../data -db hebrew_v4.dat -c coref_docs_2_tag/base -t coref_docs_2_tag/tne_conll_final_mentions -o coref_docs_2_tag/conllu_out_annotation

/Users/s0g0a87/anaconda3/envs/hebrewCoreference/bin/python add_token_loc_to_consolidation.py -c coref_docs_2_tag/base -t ../../hebrew_coref/coref_annotation_data/Consolidation -m coref_docs_2_tag/tne_conll_final_mentions -o ../../hebrew_coref/final_coref_files/tne
/Users/s0g0a87/anaconda3/envs/hebrewCoreference/bin/python create_conll_file_consolidation.py -c coref_docs_2_tag/base -t ../../hebrew_coref/final_coref_files/tne -o /Users/s0g0a87/studies/tne_ui/hebrew_coref/final_coref_files/conllu
