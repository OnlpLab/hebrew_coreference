import json
import os
files = os.listdir('tne_conll_final_mentions')

for file in files:
    with open(os.path.join('tne_conll_final_mentions', file)) as f:
        doc = json.load(f)
    nps = doc[0]['nps']
    nps_for_unique_set = ["_".join([n['text'],str(n['start_index']), str(n['end_index'])]) for n in nps]
    if len(nps_for_unique_set) != len(list(set(nps_for_unique_set))):
        print(file)
