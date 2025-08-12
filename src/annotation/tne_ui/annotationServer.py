# bottleMain
from bottle import Bottle
import ast
import sqlite3 as lite
import os
import argparse
from bottle import static_file
from typing import List, Set, Tuple
from threading import Lock
import subprocess
import platform

import warnings

# from hebrew_coref.download_annotated_coref.read_annotation import check_last_emails  # Temporarily disabled

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.simplefilter(action='ignore', category=DeprecationWarning)
    # from hebrew_coref.create_agreement_files.conll_reader import ConllReader  # Temporarily disabled

app = Bottle()

# conll = ConllReader()  # Temporarily disabled due to import issues
conll = None  # Mock for testing

lock = Lock()

# conllu_folder = "hebrew_coref/create_agreement_files/coref_docs_2_tag/base"  # Temporarily disabled
# conllus = sorted([i for i in os.listdir(conllu_folder)], key=lambda x: int(x.split("_")[0]))  # Temporarily disabled
# conllus_by_hit_id = {int(file_name.split("_")[0]) - 1: file_name for file_name in conllus}  # Temporarily disabled
conllu_folder = None  # Mock for testing
conllus = []  # Mock for testing
conllus_by_hit_id = {}  # Mock for testing


def get_nps_done_nps(cursor, text_id):
    # Retrieve nps and done_nps from final_mention_data table if exists
    query = "SELECT nps, done_nps FROM final_mention_data WHERE hit_id = ?"
    cursor.execute(query, (text_id,))
    row = cursor.fetchone()
    if row is not None:
        # Key found in final_mention_data table, retrieve nps and done_nps
        nps, done_nps = row
        return nps, done_nps
    else:
        raise KeyError(f"Key {text_id} does not exist in any final mentions")


@app.route('/tne/tool/coref/<hit_id:int>')
def index(hit_id):
    """Annotation page"""
    con = lite.connect(os.path.join(db_dir, db))
    cur = con.cursor()
    text, pronouns = cur.execute("SELECT text, pronouns FROM tne_original_data WHERE hit_id = ?", (hit_id,)).fetchone()

    try:
        nps, done_nps = get_nps_done_nps(cur, hit_id)
    except KeyError:
        return return_error_window(hit_id)
    con.close()

    with open(os.path.join("static", "coref.html"), 'r', encoding="utf8") as f:
        s = f.read()
        s = s.replace('$text', text). \
            replace('$nps', nps). \
            replace('$done_nps', done_nps). \
            replace('$pronouns', pronouns). \
            replace('$hit_id', str(hit_id))
    with open(os.path.join("static", "heb_coref_utils.html"), 'r', encoding="utf8") as f:
        utils = f.read()
    s += utils
    return s


def get_valid_indices(hit_id, text):
    conllu_file = conllus_by_hit_id.get(hit_id)
    start_text_index = eval(text)['paragraphs'][0]['start_index']
    conllu_path = os.path.join(conllu_folder, conllu_file)
    sents = conll.read_conll(conllu_path, input_encoding="utf-8", merge_subtoken=False)
    curr_sent_index = start_text_index
    start_index_to_token = {}
    end_index_to_token = {}
    for i, doc in enumerate(sents):
        for token in doc:
            start_index = token.idx + curr_sent_index
            start_index_to_token[start_index] = {"sent": i, "token": token.i}

            end_index = token.idx + len(token) + curr_sent_index
            end_index_to_token[end_index] = {"sent": i, "token": token.i + 1}

        curr_sent_index += len(doc.text)
    return start_index_to_token, end_index_to_token


@app.route('/tne/tool/mentions/<hit_id:int>')
def index(hit_id):
    """Annotation page"""
    with lite.connect(os.path.join(db_dir, db)) as con:
        cur = con.cursor()
        cur.execute("SELECT text,nps,done_nps, pronouns FROM tne_original_data WHERE hit_id=" + str(hit_id))
        my_data = cur.fetchone()

    text, nps, done_nps, pronouns = my_data
    start_index_to_sent_and_tokens, end_index_to_sent_and_tokens = get_valid_indices(hit_id, text)

    with open(os.path.join("static", "mentions.html"), 'r', encoding="utf8") as f:
        html_content = f.read()
    html_content = html_content.replace('$text', my_data[0]). \
        replace('$nps', nps). \
        replace('$done_nps', done_nps). \
        replace('$pronouns', pronouns). \
        replace('$start_index_to_sent_and_tokens', str(start_index_to_sent_and_tokens)). \
        replace('$end_index_to_sent_and_tokens', str(end_index_to_sent_and_tokens)). \
        replace('$hit_id', str(hit_id))

    with open(os.path.join("static", "heb_coref_utils.html"), 'r', encoding="utf8") as f:
        utils = f.read()
    html_content += utils

    return html_content


@app.route('/tne/tool/links/<hit_id:int>/<coref_ann_id:int>')
def index(hit_id, coref_ann_id):
    """Annotation page"""
    con = lite.connect(os.path.join(db_dir, db))
    cur = con.cursor()
    cur.execute("SELECT text,nps,done_nps, pronouns FROM tne_original_data WHERE hit_id=" + str(hit_id))
    my_data = cur.fetchone()
    cur.execute(
        "SELECT clusters,states FROM tne_coref_data WHERE hit_id=" + str(hit_id) + " and annotation_id = " + str(
            coref_ann_id))
    my_data1 = cur.fetchone()
    print(my_data1)
    clusters = my_data1[0]
    states = my_data1[1]
    con.close()
    f = open(os.path.join("static", "links.html"), 'r', encoding="utf8")
    s = f.read().replace('$text', my_data[0]).replace('$nps', my_data[1]).replace('$done_nps', my_data[2]).replace(
        '$pronouns', my_data[3]).replace('$hit_id', str(hit_id)).replace('$ann_id', str(coref_ann_id)).replace('$coref',
                                                                                                               clusters).replace(
        '$STATES', states)
    f.close()
    return (s)


@app.route('/tne/tool/consolidation/<hit_id:int>/<coref_ann_id:int>')
def index(hit_id, coref_ann_id):
    """Annotation page"""
    con = lite.connect(os.path.join(db_dir, db))
    cur = con.cursor()
    cur.execute("SELECT text,nps,done_nps, pronouns FROM tne_original_data WHERE hit_id=" + str(hit_id))
    my_data = cur.fetchone()
    cur.execute(
        "SELECT clusters FROM tne_coref_data WHERE hit_id=" + str(hit_id) + " and annotation_id = " + str(coref_ann_id))
    my_data1 = cur.fetchone()
    print(my_data1)
    clusters = my_data1[0]
    cur.execute(
        'select links,annotation_id from tne_links_data where hit_id = ' + str(hit_id) + ' and coref_ann_id = ' + str(
            coref_ann_id))
    res = cur.fetchall()
    res_list = []
    for r in res:
        r_list = []
        links = ast.literal_eval(r[0])
        annotation_id = r[1]
        r_list.append("Annotator " + str(annotation_id))
        r_list.append(links)
        res_list.append(r_list)
    con.close()
    f = open(os.path.join("static", "consolidation.html"), 'r', encoding="utf8")
    s = f.read().replace('$text', my_data[0]).replace('$nps', my_data[1]).replace('$done_nps', my_data[2]).replace(
        '$pronouns', my_data[3]).replace('$hit_id', str(hit_id)).replace('$ann_id', str(coref_ann_id)).replace('$coref',
                                                                                                               clusters).replace(
        '$res', str(res_list))
    f.close()
    return (s)


@app.route('/tne/results/coref/<hit_id:int>')
def index(hit_id):
    """Annotation page"""
    con = lite.connect(os.path.join(db_dir, db))
    con.row_factory = lite.Row
    cur = con.cursor()
    cur.execute("SELECT text,nps,done_nps, pronouns FROM final_mention_data WHERE hit_id=" + str(hit_id))
    my_data = cur.fetchone()
    result = []
    cur.execute('select annotator_id, clusters from tne_coref_data where hit_id = ' + str(hit_id))
    my_data1 = cur.fetchall()
    for r in my_data1:
        print(r)
        row_dict = dict(r)
        row_dict["clusters"] = ast.literal_eval(row_dict["clusters"])
        result.append(row_dict)
    con.close()
    result = str(result).replace('annotator_id', 'annotator')
    f = open(os.path.join("static", "coref_results.html"), 'r', encoding="utf8")
    s = f.read().replace('$text', my_data[0]).replace('$nps', my_data[1]).replace('$done_nps', my_data[2]).replace(
        '$pronouns', my_data[3]).replace('$results', result)
    f.close()
    return s


@app.route('/tne/upload_annotations')
def index():
    html_static_path = os.path.join("static", "run_annotations_status.html")
    with open(html_static_path, 'r', encoding="utf8") as f:
        html_content = f.read()

    if lock.locked():
        return html_content.replace("$message", "Another instance is already running")

    lock.acquire()
    try:

        script_path = os.path.join(os.path.dirname(__file__), 'hebrew_coref', 'read_annotations.sh')
        mac_project_dir = '/Users/s0g0a87/studies/tne_ui'
        mac_python_env = '/Users/s0g0a87/anaconda3/envs/hebrewCoreference'

        nlp_server_project_dir = '/home/nlp/shaked571/Dev/tne_ui'
        nlp_server_python_env = '/home/nlp/shaked571/miniconda3/envs/tne'

        gcp_server_project_dir = '/home/shakedgreenfeld/tne_ui'
        gcp_server_python_env = '/opt/conda/'

        if platform.system() == 'Darwin':  # Darwin means it is macOS
            project_dir = mac_project_dir
            python_env = mac_python_env
        elif platform.node() == 'Linux':  # server environment which is Linux
            project_dir = nlp_server_project_dir
            python_env = nlp_server_python_env
        else:
            project_dir = gcp_server_project_dir
            python_env = gcp_server_python_env

        subprocess.run(['bash', script_path, project_dir, python_env], check=True)
        return html_content.replace("$message",
                                    "The script execution was successful and the annotations have been uploaded!")
    except subprocess.CalledProcessError as e:
        return html_content.replace("$message", "Script execution failed: {}".format(str(e)))
    finally:
        lock.release()


@app.route('/tne/results/links/<hit_id:int>/<coref_ann_id:int>/<links_ann_id:int>')
def index(hit_id, coref_ann_id, links_ann_id):
    """Annotation page"""
    con = lite.connect(os.path.join(db_dir, db))
    con.row_factory = lite.Row
    cur = con.cursor()
    cur.execute("SELECT text,nps,done_nps, pronouns FROM tne_original_data WHERE hit_id=" + str(hit_id))
    my_data = cur.fetchone()
    cur.execute(
        "SELECT clusters FROM tne_coref_data WHERE hit_id=" + str(hit_id) + " and annotation_id = " + str(coref_ann_id))
    entities = cur.fetchone()[0]
    cur.execute('select links from tne_links_data where hit_id = ' + str(hit_id) + ' and coref_ann_id = ' + str(
        coref_ann_id) + ' and annotation_id = ' + str(links_ann_id))
    res = cur.fetchone()
    worker_id = links_ann_id
    links = ast.literal_eval(res[0])
    r_list = []
    r_list.append(worker_id)
    r_list.append(links)
    con.close()
    f = open(os.path.join("static", "linking_results.html"), 'r', encoding="utf8")
    s = f.read().replace('$text', my_data[0]) \
        .replace('$nps', my_data[1]) \
        .replace('$done_nps', my_data[2]) \
        .replace('$pronouns', my_data[3]) \
        .replace('$hit_id', str(hit_id)) \
        .replace('$ann_id', str(coref_ann_id)) \
        .replace('$coref', entities) \
        .replace('$res', str(r_list))
    f.close()
    return (s)


@app.route('/tne/results/consolidation/<hit_id:int>/<coref_ann_id:int>')
def index(hit_id, coref_ann_id):
    """Annotation page"""
    con = lite.connect(os.path.join(db_dir, db))
    con.row_factory = lite.Row
    cur = con.cursor()
    cur.execute("SELECT text,nps,done_nps, pronouns FROM tne_original_data WHERE hit_id=" + str(hit_id))
    my_data = cur.fetchone()
    cur.execute(
        "SELECT clusters FROM tne_coref_data WHERE hit_id=" + str(hit_id) + " and annotation_id = " + str(coref_ann_id))
    entities = cur.fetchone()[0]
    cur.execute(
        'select links,annotation_id from tne_links_data where hit_id = ' + str(hit_id) + ' and coref_ann_id = ' + str(
            coref_ann_id))
    res = cur.fetchall()
    res_list = []
    for r in res:
        r_list = []
        links = ast.literal_eval(r[0])
        annotation_id = r[1]
        r_list.append("Annotator " + str(annotation_id))
        r_list.append(links)
        res_list.append(r_list)

    cur.execute('select annotation_id, valid_links, comments from tne_cons_data where hit_id = ' + str(
        hit_id) + ' and coref_ann_id = ' + str(coref_ann_id))
    res = cur.fetchall()
    cons_res_list = []
    for r in res:
        r_list = []
        worker_id = r[0]
        links = ast.literal_eval(r[1])
        comments = ast.literal_eval(r[2])
        # print(links)
        r_list.append(worker_id)
        r_list.append(links)
        r_list.append(comments)
        cons_res_list.append(r_list)
    consolidation_results = cons_res_list
    con.close()

    f = open(os.path.join("static", "consolidation_results.html"), 'r', encoding="utf8")
    s = f.read().replace('$text', my_data[0]).replace('$nps', my_data[1]).replace('$done_nps', my_data[2]).replace(
        '$pronouns', my_data[3]).replace('$hit_id', str(hit_id)).replace('$ann_id', str(coref_ann_id)).replace('$coref',
                                                                                                               entities).replace(
        '$res', str(res_list)).replace('$consolidation_results', str(consolidation_results))
    f.close()
    return (s)


@app.route('/static/<filename>')
def server_static(filename):
    print("something")
    return static_file(filename, './static')


def fetch_coref_data(hit_id, table):
    """Fetch coref data from the given table"""
    with lite.connect(os.path.join(db_dir, db)) as con:
        cur = con.cursor()
        text, pronouns = cur.execute("SELECT text, pronouns FROM tne_original_data WHERE hit_id = ?",
                                     (hit_id,)).fetchone()

        try:
            nps, done_nps = get_nps_done_nps(cur, hit_id)
        except KeyError:
            return return_error_window(hit_id)
        try:
            new_entities, unconsolidated_np = cur.execute("SELECT  new_clusters, undone_nps "
                                                          f"FROM {table} "
                                                          f"WHERE hit_id={str(hit_id)}").fetchone()
        except TypeError:
            return return_error_window(hit_id)

        id2text = get_id2text_dict(con, hit_id)

        states = cur.execute("SELECT states FROM tne_coref_data WHERE hit_id=" + str(hit_id)).fetchall()[0][0]

        annotators = cur.execute(
            f"SELECT annotator_id, clusters FROM tne_coref_data WHERE hit_id= {str(hit_id)}").fetchall()
        cur.close()
    start_index_to_sent_and_tokens, end_index_to_sent_and_tokens = get_valid_indices(hit_id, text)
    annotation = []

    for name, anno_data in annotators:
        if name not in {"Tal", "Itay", "Hadar", "Ariela", "Hadas", "Yechiel", "Hinoy"}:
            continue  # Otherwise it would try to show also the new nps
            #  which the code doesnt support showing at the moment TODO - remove once finish with doc 59
        curr = {'Annotator': name}
        nps_repr = ""
        anno_data_json = ast.literal_eval(anno_data)
        idiomatic = []
        # idiomatic = "Idiomatic: "
        for d in anno_data_json:
            if d['source'] == "new" or 'new' in d['source']:
                nps_repr += f"{d['id']}. {[id2text[int(m)] for m in d['members']]}\n"
            else:
                idiomatic.extend([id2text[int(m)] for m in d['members']])
        nps_repr += f"Idiomatic: {idiomatic}"
        curr['nps'] = nps_repr
        annotation.append(curr)

    html_static_path = os.path.join("static", "coref_consolidation.html")
    with open(html_static_path, 'r', encoding="utf8") as f:
        html_content = f.read()
    html_content = html_content.replace('$text', text)
    html_content = html_content.replace('$nps', nps)
    html_content = html_content.replace('$done_nps', done_nps)
    html_content = html_content.replace('$pronouns', pronouns)
    html_content = html_content.replace('$hit_id', str(hit_id))
    html_content = html_content.replace('$new_entities', new_entities)
    html_content = html_content.replace('$unconsolidated_nps', unconsolidated_np)
    html_content = html_content.replace('$start_index_to_sent_and_tokens', str(start_index_to_sent_and_tokens))
    html_content = html_content.replace('$end_index_to_sent_and_tokens', str(end_index_to_sent_and_tokens))
    html_content = html_content.replace('$STATES', states)
    html_content = html_content.replace('$ANNOTATIONS', repr(annotation))

    with open(os.path.join("static", "heb_coref_utils.html"), 'r', encoding="utf8") as f:
        utils = f.read()
    html_content += utils

    return html_content


def return_error_window(hit_id):
    html_static_path = os.path.join("static", "default_error_for_consolidation.html")
    with open(html_static_path, 'r', encoding="utf8") as f:
        html_content = f.read()
    html_content = html_content.replace('$hit_id', str(hit_id))
    return html_content


@app.route('/tne/tool/coref_cons/<hit_id:int>')
def index(hit_id):
    return fetch_coref_data(hit_id, 'coref_data_for_consolidation')


@app.route('/tne/tool/coref_cons_unanimous/<hit_id:int>')
def index(hit_id):
    return fetch_coref_data(hit_id, 'coref_data_for_consolidation_unanimous')


def find_consensus_of_majority(my_sets: List[Set[Tuple[int, int]]]) -> Set[Tuple[int, int]]:
    # Count the occurrences of each tuple in the sets
    tuple_count = {}
    for my_set in my_sets:
        for tup in my_set:
            if tup in tuple_count:
                tuple_count[tup] += 1
            else:
                tuple_count[tup] = 1
    # Find tuples that are in more than 50% of the sets
    consensus_set = {tup for tup, count in tuple_count.items() if count > len(my_sets) / 2}
    return consensus_set


def find_consensus_nps(annotation):
    # Contains all the different nps lists
    consensus_keys = get_consensus_keys(annotation)
    index_loc_to_np = annotation_to_index_loc_dict(annotation)

    return consensus_keys, index_loc_to_np


def get_consensus_keys(annotation):
    nps_sets = [set((np['start_index'], np['end_index']) for np in annotator_nps) for annotator_nps in
                annotation.values()]
    # Find consensus using set intersection
    consensus_keys = find_consensus_of_majority(nps_sets)
    return consensus_keys


def annotation_to_index_loc_dict(annotation):
    index_loc_to_np = {}
    for annotator_nps in annotation.values():
        for np in annotator_nps:
            value = {'text': np['text'], 'start_index': np['start_index'], 'end_index': np['end_index']}
            # This for-loop has an 'if' for back compatability with old format without token location
            # All mentions should have now the start and end token
            for field in ['start_token', 'end_token', 'sent_num']:
                if field in np:
                    value[field] = np[field]
            index_loc_to_np[(np['start_index'], np['end_index'])] = value
    return index_loc_to_np


@app.route('/tne/tool/mentions_cons/<hit_id:int>')
def index(hit_id):
    pronouns = '[]'
    annotation = []

    with lite.connect(os.path.join(db_dir, db)) as con:
        cur = con.cursor()
        text = cur.execute("SELECT text "
                           "FROM tne_original_data "
                           f"WHERE hit_id={str(hit_id)}").fetchone()[0]
        annotators = cur.execute("SELECT annotator_id, nps, clusters "
                                 "FROM tne_mention_data "
                                 f"WHERE hit_id={str(hit_id)}").fetchall()
    if len(annotators) == 0:
        html_static_path = os.path.join("static", "default_error_for_consolidation.html")
        with open(html_static_path, 'r', encoding="utf8") as f:
            html_content = f.read()
        html_content = html_content.replace('$hit_id', str(hit_id))
        return html_content

    mentions_by_annotator = {}
    idiomatic_by_annotator = {}
    for name, curr_annotations, anno_is_np in annotators:
        annotator_mentions = []
        annotator_idiomatic = []
        nps_repr = ""
        idiomatic_repr = ""
        curr_annotations_list = ast.literal_eval(curr_annotations)
        annotator_is_np_list = ast.literal_eval(anno_is_np)
        for is_np in annotator_is_np_list:
            np = curr_annotations_list[is_np['members'][0]]
            if is_np['source'] == 'mention':
                annotator_mentions.append(np)
                nps_repr += f"{np['id']}. {np['text']}\n"
            else:
                annotator_idiomatic.append(np)
                idiomatic_repr += f"{np['id']}. {np['text']}\n"
        mentions_by_annotator[name] = annotator_mentions
        idiomatic_by_annotator[name] = annotator_idiomatic

        annotation.append({'Annotator': name, 'mentions': nps_repr, 'idiomatics': idiomatic_repr})

    consensus_mention_keys, index_loc_to_mention = find_consensus_nps(mentions_by_annotator)

    remove_consensus_idiomatic(consensus_mention_keys, idiomatic_by_annotator, index_loc_to_mention)

    sorted_mentions = sort_by_index_and_enrich_with_id(index_loc_to_mention)
    consensus = [index_loc_to_mention[key] for key in consensus_mention_keys]
    consensus = sorted(consensus, key=lambda x: x['id'])

    consensus_id = set(i['id'] for i in consensus)
    unconsolidated_nps = []
    for np in sorted_mentions:
        if np['id'] not in consensus_id:
            unconsolidated_nps.append(np['id'])

    done_nps = str({np['id']: False for np in sorted_mentions}).replace("False", "false")

    new_ents = [{'members': [np['id']], 'source': ['mention'], 'id': i, 'selected_preposition': 'of'} for i, np in
                enumerate(consensus)]
    start_index_to_sent_and_tokens, end_index_to_sent_and_tokens = get_valid_indices(hit_id, text)

    html_static_path = os.path.join("static", "mentions_consolidation.html")
    with open(html_static_path, 'r', encoding="utf8") as f:
        html_content = f.read()

    html_content = html_content.replace('$text', text)
    html_content = html_content.replace('$nps', str(sorted_mentions))
    html_content = html_content.replace('$done_nps', done_nps)
    html_content = html_content.replace('$new_entities', str(new_ents))
    html_content = html_content.replace('$pronouns', pronouns)
    html_content = html_content.replace('$hit_id', str(hit_id))
    html_content = html_content.replace('$unconsolidated_nps', str(unconsolidated_nps))
    html_content = html_content.replace('$start_index_to_sent_and_tokens', str(start_index_to_sent_and_tokens))
    html_content = html_content.replace('$end_index_to_sent_and_tokens', str(end_index_to_sent_and_tokens))
    html_content = html_content.replace('$ANNOTATIONS', repr(annotation))
    con.close()
    with open(os.path.join("static", "heb_coref_utils.html"), 'r', encoding="utf8") as f:
        utils = f.read()
    html_content += utils

    return html_content


def sort_by_index_and_enrich_with_id(index_loc_to_mention):
    sorted_mention_keys = sorted(index_loc_to_mention, key=lambda x: (x[0], x[1]))
    for i, key in enumerate(sorted_mention_keys):
        index_loc_to_mention[key]['id'] = i
    # Sort them by start_index and provide ID
    index_loc_to_mention = sorted(index_loc_to_mention.values(), key=lambda x: x['id'])
    return index_loc_to_mention


def remove_consensus_idiomatic(consensus_mention_keys, idiomatic_by_annotator, index_loc_to_mention):
    consensus_idiomatic_keys, index_loc_to_idiomatic = find_consensus_nps(idiomatic_by_annotator)
    for idiomatic_loc in consensus_idiomatic_keys:
        index_loc_to_mention.pop(idiomatic_loc, None)
        if idiomatic_loc in consensus_mention_keys:
            consensus_mention_keys.remove(idiomatic_loc)


@app.route('/tne/last_annotations')
def index():
    last_docs = check_last_emails()
    html_static_path = os.path.join("static", "last_docs.html")
    with open(html_static_path, 'r', encoding="utf8") as f:
        html_content = f.read()
    html_content = html_content.replace("$docs", str(last_docs))
    return html_content


def get_id2text_dict(con, hit_id):
    cur = con.cursor()
    original_data = cur.execute("SELECT nps FROM final_mention_data WHERE hit_id=" + str(hit_id)).fetchall()[0][0]
    original_data = ast.literal_eval(original_data)
    id2text = {d['id']: d['text'] for d in original_data}
    return id2text


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    '''
    -db_dir data -db hebrew_v4.dat --debug
    '''
    argparser.add_argument("--debug", action='store_true')
    argparser.add_argument("-db_dir", "--database_dir", type=str,
                           help="name of the directory that contains the databse")
    argparser.add_argument("-db", "--data_base", type=str,
                           help="name of the database to which the consolidation data will be stored")
    argparser.add_argument("-hst", "--host", type=str,
                           default="localhost" if platform.system() != "Linux" else "0.0.0.0",
                           help="server when default is localhost|0.0.0.0")
    argparser.add_argument("-p", "--port", type=int, default=8080, help="port when default is 8080")

    args = argparser.parse_args()

    db_dir = args.database_dir
    db = args.data_base

    if args.debug:
        app.run(reloader=True, host=args.host, port=args.port, debug=True)
    else:
        app.run(host=args.host, port=args.port, workers=3)
