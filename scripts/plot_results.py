import json
import os
from pathlib import Path

base_data_dir="/home/nlp/shaked571/pycharm_over_ssh/np/np_data"
baseParse=["gold_seg/stanza_parse", "gold_seg/ud_parse", "amit_seg/stanza_parse"]
posOpt=["no_possessive", "with_possessive"]
nestOpt=["flat", "nested"]
# "gold_seg/ud_parse" "amit_seg/stanza_parse"
out_dir = "/home/nlp/shaked571/pycharm_over_ssh/np/scripts/output"
for seg in baseParse:
    for pos in posOpt:
        for nest in nestOpt:
            for i in [1,2,3]:
                seg_tup = seg.split("/")
                seg = seg_tup[0]
                parse = seg_tup[1]
                model_name = "_".join([seg, parse, pos, nest, "seed", str(i), "epoch", "15"])
                out_path = os.path.join(out_dir, model_name, "predict_results.json" )
                with open(out_path) as f:
                    json.load(f)
