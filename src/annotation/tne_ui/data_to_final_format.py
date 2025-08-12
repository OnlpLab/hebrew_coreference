import argparse
import ast
import json
from copy import deepcopy

import spacy
from tqdm import tqdm

import os
import sys
import sqlite3 as lite
import io

# not loading the parser and ner for speed. just need the tokenizer
nlp = spacy.load("en_core_web_sm", exclude=['parser', 'ner'])

TITLE = '\n\n'
SUB_TITLE = '\n\n'
PARAGRAPH = '\n'

uncovered_spans = 0
problematic_docs = []
tokenization_err = 0


def fix_encoding(in_json):
    new_dic = {}

    if type(in_json) == dict:
        for k, v in in_json.items():
            fix_v = fix_encoding(v)
            new_dic[k] = fix_v
    else:
        try:
            fix_json = ast.literal_eval(in_json)
        except:
            return in_json
        return fix_encoding(fix_json)
    return new_dic


def get_data(db_dir,db):
    

    documents_temp = []
    
    con = lite.connect(os.path.join(db_dir, db)) 
    con.row_factory = lite.Row
    c = con.cursor()

    c.execute("select cons.hit_id as internal_hit_id, cons.coref_ann_id as coref_ann_id, cons.annotator_id as cons_annotator, valid_links, coref.annotator_id as coref_annotator, clusters, text, nps, source_file, url from tne_cons_data as cons join tne_coref_data as coref on cons.hit_id = coref.hit_id and cons.coref_ann_id = coref.annotation_id join tne_original_data as orig on cons.hit_id = orig.hit_id")
    for r in c.fetchall():
        row_dict = dict(r)
        #Adding link annotators    
        k = row_dict['internal_hit_id']
        k1 = row_dict['coref_ann_id']
        c.execute("select annotator_id from tne_links_data where hit_id  = " + str(k) + " and coref_ann_id = " + str(k1))
        tne_annotators = [item['annotator_id'] for item in c.fetchall()]
        row_dict['tne_annotators'] = tne_annotators
        del row_dict['coref_ann_id']
        documents_temp.append(row_dict)
        
    
    con.close()
    # print(documents_temp)
    # sys.exit()
    
    print('=== Fixing Encoding ===')

    # internal_id_dict = {}
    documents_orig = []
    for d in tqdm(documents_temp):        
        t = fix_encoding(d)        
        documents_orig.append(t)
    return documents_orig


def add_explicit_entity_links(doc):
    aug_doc = deepcopy(doc)
    links_to_coref = doc['valid_links']
    coref_clusters_ = doc['clusters']
    coref_clusters = {item['id']: item for item in coref_clusters_}

    links_to_entities = []
    for row in links_to_coref:
        coref_id = row['complement']
        if coref_id in coref_clusters:
            for member in coref_clusters[coref_id]['members']:
                row = {'bridge': row['bridge'],
                       'complement': member,
                       'preposition': row['preposition'],
                       'type': row['type'],
                       'entity_source': coref_clusters[coref_id]['source'],
                       'coref_cluster': coref_clusters[coref_id]['id']
                       }
                links_to_entities.append(row)
        else:
            row = {'bridge': row['bridge'],
                   'complement': coref_id,
                   'preposition': row['preposition'],
                   'type': row['type'],
                   'entity_source': None,
                   'coref_cluster': None
                   }
            links_to_entities.append(row)
    aug_doc['entities_links'] = links_to_entities
    return aug_doc


def _fix_ws_offsets(link, entities_dic):
    from_ent = entities_dic[link['bridge']]
    to_ent = entities_dic[link['complement']]

    if from_ent['text'].startswith(' ') or from_ent['text'].startswith('\n'):
        from_ent['text'] = from_ent['text'][1:]
        from_ent['start_index'] += 1
    if to_ent['text'].startswith(' ') or to_ent['text'].startswith('\n'):
        to_ent['text'] = to_ent['text'][1:]
        to_ent['start_index'] += 1

    entities_dic[link['bridge']] = from_ent
    entities_dic[link['complement']] = to_ent
    return entities_dic


def fix_offsets(doc):
    
    entities_dic = {x['id']: x for x in doc['nps']}

    for link in doc['entities_links']:
        if type(link['complement']) != int:
            c = doc['text']['raw_text'].count(link['complement'])
            if c <= 1:
                global uncovered_spans
                uncovered_spans += 1
            global problematic_docs
            problematic_docs.append(doc['internal_hit_id'])
            continue
        entities_dic = _fix_ws_offsets(link, entities_dic)

    nps = []
    for ind, row in entities_dic.items():
        nps.append(row)

    doc['nps'] = nps

    return doc


def testing_special_tokens_offsets(documents):
    for x in documents:
        title = x['text']['title']
        subtitles = x['text']['subtitles']

        # assert len(subtitles) <= 1, "more than a single subtitle. " + x['internal_hit_id']
        if len(subtitles) > 0:
            assert title['end_index'] + 1 == subtitles[0]['start_index'], "subtitle doesn't come exactly after title "\
                                                                          + x['internal_hit_id']
        for sub_ind in range(1, len(subtitles)):
            assert subtitles[sub_ind - 1]['end_index'] + 1 == subtitles[sub_ind]['start_index'],\
                "subtitle doesn't come exactly after title " + x['internal_hit_id']


def modeling_tokenization_augmentation(doc):
    # offsets of nps
    entities_extra_dic = {x['id']: 0 for x in doc['nps']}

    # original positions of nps
    entities_original_dic = {x['id']: x for x in doc['nps']}

    text = doc['text']['raw_text']
    title = doc['text']['title']
    title_end = title['end_index']

    # adding the title separation token
    text = text[:title_end] + TITLE + text[title_end + 1:]

    # updating the offsets of the nps that comes after the title
    for ent_id, item in entities_original_dic.items():
        if item['start_index'] >= title_end:
            entities_extra_dic[ent_id] += len(TITLE) - 1

    # assuming there is only 1 subtitle???
    subtitles = doc['text']['subtitles']
    len_subtitles = 0
    for subtitle in subtitles:
        subtitle_end = subtitle['end_index']

        # adding the substitle separation token
        text = text[: subtitle_end + len(TITLE) + len_subtitles] + SUB_TITLE + \
               text[subtitle_end + len(TITLE) + len_subtitles:]

        # updating the offsets of the nps that comes after the subtitle
        for ent_id, item in entities_original_dic.items():
            if item['start_index'] >= subtitle_end:
                entities_extra_dic[ent_id] += len(SUB_TITLE)
        len_subtitles += len(SUB_TITLE)

    paragraphs = doc['text']['paragraphs']

    # using the first two paragraphs (assuming there are three),
    #  and thus not adding a paragraph token after the last one???
    for ind, paragraph in enumerate(paragraphs[:-1]):
        paragraph_end = paragraph['end_index']

        # adding the paragraph separation token
        text = text[: paragraph_end + len(TITLE) + len_subtitles + (len(PARAGRAPH) * ind)] + PARAGRAPH + \
               text[paragraph_end + len(TITLE) + len_subtitles + (len(PARAGRAPH) * ind):]

        # updating the offsets of the nps that comes after the paragraph
        for ent_id, item in entities_original_dic.items():
            if item['start_index'] >= paragraph_end:
                entities_extra_dic[ent_id] += len(PARAGRAPH)

    # Creating a new dictionary, and updating the locations based on the offsets calculated above
    fix_entities = []
    for row in doc['nps']:
        row_id = row['id']
        start_index = row['start_index'] + entities_extra_dic[row_id]
        end_index = row['end_index'] + entities_extra_dic[row_id]
        row = {'text': row['text'],
               'start_index': start_index,
               'end_index': end_index,
               'id': f'np{row_id}',
               }
        fix_entities.append(row)
    doc['modeling_data'] = {'text': text,
                            'nps': fix_entities}
    return doc


def test_transformation(doc):
    original_nps = {f"np{x['id']}": x for x in doc['nps']}
    new_nps = {x['id']: x for x in doc['modeling_data']['nps']}

    original_text = doc['text']['raw_text']
    new_text = doc['modeling_data']['text']

    for np_id, np in original_nps.items():
        if original_text[np['start_index']: np['end_index']] !=\
                new_text[new_nps[np_id]['start_index']: new_nps[np_id]['end_index']]:
            print(original_text[np['start_index']: np['end_index']], '_ents_sep_',
                  new_text[new_nps[np_id]['start_index']: new_nps[np_id]['end_index']])
            raise Exception


def modeling_tokenization(doc):
    nlp_doc = nlp(doc['modeling_data']['text'])
    spacy_offset = 0
    entities_token_indices = {}

    for row in doc['modeling_data']['nps']:
        for i in range(spacy_offset, len(nlp_doc)):
            if nlp_doc[i].idx == row['start_index']:
                entities_token_indices[row['id']] = {'start_token': i}
            if nlp_doc[i].idx >= row['end_index']:
                if row['id'] not in entities_token_indices:
                    global tokenization_err
                    tokenization_err += 1
                    break
                entities_token_indices[row['id']]['end_token'] = i - 1
                break
        # in cases where the span end with the last token of the document,
        #  the former loop won't reach the assignment of the end token, thus
        #  adding it here, as the last token of the document
        if row['id'] in entities_token_indices and 'end_token' not in entities_token_indices[row['id']]:
            entities_token_indices[row['id']]['end_token'] = len(nlp_doc) - 1
    tokens = [x.text for x in nlp_doc]
    doc['modeling_data']['tokens'] = tokens
    doc['modeling_data']['tokenized_entities'] = entities_token_indices

    return doc


coref_source_dic = {
    'new': 'standard',
    'time/date/measurement expression': 'time/date/measurement',
    'idiomatic': 'idiomatic',
}


def add_additional_doc_info(doc):    
    source = doc['source_file']
    doc['source'] = source

    coref_data = doc['clusters']
    coref_clean_data = [{'id': f"cc{x['id']}",
                         'members': [f"np{mem}" for mem in x['members']],
                         'np_type': coref_source_dic[x['source']]}
                        for x in coref_data]
    doc['coref'] = coref_clean_data
    return doc


def _create_workers_dictionaries(documents):
    consolidators_annotators = []
    coref_annotators = []
    np_links_annotators = []
    for doc in documents:
        consolidators_annotators.append(doc['cons_annotator'])
        coref_annotators.append(doc['coref_annotator'])
        np_links_annotators.extend(doc['tne_annotators'])
        
    consolidators_annotators = list(set(consolidators_annotators))
    coref_annotators = list(set(coref_annotators))
    np_links_annotators = list(set(np_links_annotators))

    consolidators_annotators_dict = {x: ind for ind, x in enumerate(consolidators_annotators)}
    coref_annotators_dict = {x: ind for ind, x in enumerate(coref_annotators)}
    np_links_annotators_dict = {x: ind for ind, x in enumerate(np_links_annotators)}
    return consolidators_annotators_dict, coref_annotators_dict, np_links_annotators_dict


def add_annotators_ids(doc, consolidators_annotators_dict, coref_annotators_dict, np_links_annotators_dict):
    doc['anonymized_consolidator_worker_id'] = consolidators_annotators_dict[doc['cons_annotator']]
    doc['anonymized_coref_worker_id'] = coref_annotators_dict[doc['coref_annotator']]
    doc['anonymized_np-links_worker_id'] = [np_links_annotators_dict[x] for x in doc['tne_annotators']]    
    return doc


def merge_nps(doc):
    nps = doc['modeling_data']['nps']
    tokenized_entities = doc['modeling_data']['tokenized_entities']

    augmented_nps = {}
    for np in nps:
        np_id = np['id']
        d = {
            'text': np['text'],
            'first_char': np['start_index'],
            'last_char': np['end_index'],
            'first_token': tokenized_entities[np_id]['start_token'],
            'last_token': tokenized_entities[np_id]['end_token'],
            'id': np_id,
        }

        augmented_nps[np_id] = d
    return augmented_nps


def np_relation_renaming(doc):
    relations = doc['entities_links']

    renamed_relations = []
    for rel in relations:
        d = {
            'anchor': f"np{rel['bridge']}",
            'complement': f"np{rel['complement']}",
            'preposition': rel['preposition'],
            'complement_coref_cluster_id': f"cc{rel['coref_cluster']}",
        }
        renamed_relations.append(d)
    return renamed_relations


def dump_keys(d, lvl=0):
    for k, v in d.items():
        print('%s%s' % (lvl * ' ', k))
        if type(v) == dict:
            dump_keys(v, lvl + 1)


def to_file(documents, out_f):
    with open(out_f, 'w') as f:
        for doc in documents:
            json.dump(doc, f)
            f.write('\n')


def main():
    
    parse = argparse.ArgumentParser("")
    parse.add_argument("-db_dir", "--database_dir", type=str, help="name of the directory that contains the databse")
    parse.add_argument("-db", "--data_base", type=str, help="name of the database to which the consolidation data will be stored")
    parse.add_argument("-out", "--output_file", type=str, help="name or path of the jsonl file where processed data in the final format will be stored")
       
    

    args = parse.parse_args()
    db_dir = args.database_dir
    db = args.data_base
    out_file = args.output_file
    

    documents_orig = get_data(db_dir,db)
    
    
    print('=== Adding explicit links ===')

    document_links = []
    for doc in tqdm(documents_orig):
        doc_aug = add_explicit_entity_links(doc)
        document_links.append(doc_aug)
    
    
    print('=== Fixing offsets ===')
    documents = []
    for d in tqdm(document_links):
        t = fix_offsets(d)
        documents.append(t)
        
    testing_special_tokens_offsets(documents)
    
    title_subtitle_merge = []
    aug_documents = []
    err = 0

    for ind, temp_doc in tqdm(enumerate(documents)):
        temp = modeling_tokenization_augmentation(temp_doc)
        try:
            test_transformation(temp)
        except:
            err += 1
            title_subtitle_merge.append(temp_doc['internal_hit_id'])
            
            continue
        aug_documents.append(temp)
    print('tokenization augmentation erroneous documents:', err, title_subtitle_merge)
         
    err = 0
    tokenized_aug_documents = []
    for d in tqdm(aug_documents):
        try:
            t = modeling_tokenization(d)
            tokenized_aug_documents.append(t)
        except:
            err += 1
            pass

    print('token errors in augmentation', tokenization_err)
    print('tokenization errors', err)
        
    wiki_coref_documents = []
    for doc in tokenized_aug_documents:
        doc_wa = add_additional_doc_info(doc)
        wiki_coref_documents.append(doc_wa)
    
    consolidators_annotators_dict, coref_annotators_dict,\
        np_links_annotators_dict = _create_workers_dictionaries(wiki_coref_documents)

    full_documents = []
    for doc in wiki_coref_documents:
        doc_ann = add_annotators_ids(doc, consolidators_annotators_dict, coref_annotators_dict,
                                     np_links_annotators_dict)
        full_documents.append(doc_ann)
    
    
    
    minimal_documents = []
    for d in full_documents:
        nps = merge_nps(d)
        relations = np_relation_renaming(d)
        m = {
            'id': f"r{d['internal_hit_id']}",

            'text': d['modeling_data']['text'],
            'tokens': d['modeling_data']['tokens'],
            'nps': nps,
            'np_relations': relations,
            'coref': d['coref'],
            'metadata': {
                'annotators': {
                    'coref_worker': d['anonymized_coref_worker_id'],
                    'consolidator_worker': d['anonymized_consolidator_worker_id'],
                    'np-relations_worker': d['anonymized_np-links_worker_id'],
                },
                'url': d['url'],
                'source': d['source'],
            },
        }
        minimal_documents.append(m)
    
    
    to_file(minimal_documents, out_file)
        


if __name__ == '__main__':
    main()