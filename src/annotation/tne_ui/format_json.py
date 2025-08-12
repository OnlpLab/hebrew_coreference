
import json
import spacy
import os
import sqlite3 as lite
import argparse

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("merge_entities")


def build_nps(input_text):
    doc = nlp(input_text)
    nps = []
    done_nps = {}
    pronouns = []
    np_id = 0
    chunks = list(doc.noun_chunks)
    for x in range(len(chunks)):
        chunk = chunks[x]
        if chunk.root.pos_ == "PRON":
            pronouns.append(np_id)
        np = {}
        np["start_index"] = chunk.start_char
        np["text"] = chunk.text
        np["end_index"] = chunk.end_char
        #if a determiner is left out of the np by mistake, include it back
        if chunk[0].i > 0:
            prev_token_idx = chunk[0].i - 1
            if doc[prev_token_idx].pos_ == "DET":
                np["start_index"] = doc[prev_token_idx].idx
                np["text"] = input_text[np["start_index"]:np["end_index"]]
        np["id"] = np_id
        done_nps[str(np_id)] = False
        nps.append(np)
        np_id += 1
    return (nps, done_nps, pronouns)

def build_text(input_text,text):
    tx = {}
    cur_index = 0
    raw_text = input_text.replace('\n',' ')
    tx['raw_text'] = raw_text
    title_start_index = 0
    title_end_index = len(text['title'])
    cur_index = title_end_index
    title = {}
    title['start_index'] = title_start_index
    title['end_index'] = title_end_index
    tx['title'] = title
    subtitles = []
    st_id = 0
    for st in text['sub_title']:
        subtitle = {}
        subtitle['start_index'] = cur_index + 1
        subtitle['end_index'] = subtitle['start_index'] + len(st)
        subtitle['id'] = st_id
        subtitles.append(subtitle)
        st_id = st_id + 1
        cur_index = subtitle['end_index']
    tx['subtitles'] = subtitles
    paragraphs = []
    p_id = 0
    for p in text['paragraph']:
        paragraph = {}
        paragraph['start_index'] = cur_index + 1
        paragraph['end_index'] = paragraph['start_index'] + len(p)
        paragraph['id'] = p_id
        paragraphs.append(paragraph)
        p_id = p_id + 1
        cur_index = paragraph['end_index']
    tx['paragraphs'] = paragraphs
    return(tx)

def main():
    parse = argparse.ArgumentParser("")
    parse.add_argument("-in", "--input_dir", type=str, help="input directory name")
    parse.add_argument("-out", "--output_dir", type=str, help="output directory that contains the databse")
    # parse.add_argument("-db", "--data_base", type=str, help="name of the database in the output directory")
    args = parse.parse_args()

    in_d = args.input_dir
    out_d = args.output_dir


    directory = in_d
    new_directory = out_d

    for filename in os.listdir(directory):
        raw_data = open(directory+'/'+filename, encoding="utf8")
        raw = json.load(raw_data)
        objs = []
        for text in raw:
            input_text = """"""
            input_text = input_text + text['title']+'\n'+'\n'.join(text['sub_title']) + '\n'+'\n'.join(text['paragraph']);
            obj = {}
            (nps, done_nps, pronouns) = build_nps(input_text)
            obj["nps"] = nps
            obj["done_nps"] = done_nps
            obj["pronouns"] = pronouns
            tx = build_text(input_text,text)
            source_file = filename.replace(".json","_formatted.json")
            text_id = text['id']
            obj["tx"] = tx
            obj["source_file"] = source_file

            obj["url"] = text["url"] if "url" in text else ""
            obj["text_id"] = text_id
            objs.append(obj)

        new_filename = filename.replace(".json","_formatted.json")
        with open(new_directory + '/' + new_filename, 'w+', encoding='utf8') as f:
            # x += len(new_objects)
            json.dump(objs, f, indent=4)
        raw_data.close()
        f.close()



if __name__ == "__main__":
    main()
