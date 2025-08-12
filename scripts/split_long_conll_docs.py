"""
The script split the docs that are too long in the heb ud ti smaller docs
It uses the splitting done in: re_split_doc/done
and create a new file of conll documents in corpus/new_htb_zeldes/htb2_format_split_long
** Need to remove the old versions of htb2_format and htb2_format_with_underscore afterwards to reduce confusion **
The document created need to be turned into np format as well using:
 - The "count_docs_and_prepare_coref_files.py" script - need to make sure when overriding "corpus/coref_docs_2_tag/base"
   it overrides only the documents split
 - Upon the new "corpus/coref_docs_2_tag/base" we need to run make_tne_docs.py in otder to to create the new version(v4)
   of the tne documents

Comments:
- The docs original number of mentions and sentences could be found here: https://docs.google.com/document/d/1lXxsUus_wDhLBz_Y6WSQMLe3U935DdDe5zEF1-NkXrA/edit
"""
from collections import defaultdict
from count_docs_and_prepare_coref_files import dump_conllu_docs

"""
1. Read the files  /corpus/new_htb_zeldes/htb2_format_with_underscore
2. Read the split docs
3. Identify the documents needed to split by file name
4. Identify be sentnces the location of split
5. Create a new "base" folder and run over the old files
6. Check manually using git we changed only the files need to be changed.
7. Run make_tne_docs.py
"""

import os
import re
import shutil

from convert_tb2_to_ud import read_conllu


def get_docid2last_sentences(folder_path):
    split_docs = {}
    for file_name in os.listdir(folder_path):
        if "htb_" not in file_name:
            raise ValueError(f"All files in folder {folder_path} should be in the format htb_[id].txt")
        doc_id = extract_id_from_file_name(file_name)
        with open(os.path.join(folder_path, file_name)) as f:
            lines = f.readlines()
        last_sentences = []
        for i, l in enumerate(lines):
            if l.startswith("** "):
                last_sentences.append(lines[i - 1].strip())
        split_docs[doc_id] = last_sentences

    return split_docs


def extract_id_from_file_name(file_name):
    return file_name.split("_")[1].split(".")[0]


def identify_split_location(conllu_text):
    # Add your logic to identify the split location in the CONLLU text
    # In this example, it splits the document in the middle using "\n** \d+ \n" as a marker
    return re.split(r'\n\*\*\s?\d+\s?\n', conllu_text)


def create_base_folder():
    base_folder = 'base'
    if os.path.exists(base_folder):
        shutil.rmtree(base_folder)
    os.makedirs(base_folder)
    return base_folder


# def merge_and_split_conllu(conllu_folder, split_docs_folder, base_folder):
#     split_docs = read_split_docs(split_docs_folder)
#
#     for file_name in os.listdir(conllu_folder):
#         conllu_text = read_conllu(os.path.join(conllu_folder, file_name))
#         split_location = identify_split_location(conllu_text)
#
#         if split_location and file_name in split_docs:
#             base_doc_folder = os.path.join(base_folder, file_name.replace('.conllu', ''))
#             os.makedirs(base_doc_folder)
#
#             doc_id = split_docs[file_name]
#             for i, part in enumerate(split_location):
#                 output_file_path = os.path.join(base_doc_folder, f'{doc_id}_{i + 1}.conllu')
#                 with open(output_file_path, 'w', encoding='utf-8') as output_file:
#                     # Update the doc_id in each sentence
#                     updated_part = re.sub(r'# doc_id = htb:\d+', f'# doc_id = {doc_id}_{i + 1}', part)
#                     output_file.write(updated_part)


def check_git_changes(base_folder):
    pass


# Add your logic to check git changes in the base folder
# This may involve using GitPython or any other method to check changes in the repository

def run_make_tne_docs():
    pass


# Add your logic to run make_tne_docs.py
# You can use subprocess.run or any other method to execute the script

def read_conllu_folder(conllu_folder):
    conllus_by_doc = defaultdict(list)
    for file_name in os.listdir(conllu_folder):
        conllu_dataset = read_conllu(os.path.join(conllu_folder, file_name))
        for doc in conllu_dataset:
            conllus_by_doc[doc.metadata['doc_id']].append(doc)

    for idx, doc in conllus_by_doc.items():
        conllus_by_doc[idx].sort(key=lambda x: int(x.metadata['sent_id']))
    return conllus_by_doc


def split_docs(last_sentences, docs_metadata):
    result = []
    current_chunk = []

    for doc in docs_metadata:
        current_chunk.append(doc)

        # Check if the current text is in last_sentences
        if doc.metadata['text'] in last_sentences:
            result.append(current_chunk)
            current_chunk = []

    # Add any remaining documents to the last sublist
    if current_chunk:
        result.append(current_chunk)
    if len(last_sentences) != len(result):
        raise ValueError(f"Number of docs chunks ({len(result)}) and last sentences ({len(last_sentences)}) is not aligned!")
    return result


def merge_dicts(conllu_docs, docs_after_split):
    result_dict = {}

    for key, value_list in conllu_docs.items():
        if key in docs_after_split:
            sublists = docs_after_split[key]
            for i, sublist in enumerate(sublists, start=1):
                new_key = f"{key}_{i}"
                result_dict[new_key] = sublist
        else:
            result_dict[key] = value_list

    return result_dict


def get_split_docs(conllu_docs, docs_to_split):
    new_docs = defaultdict(list)
    for idx, last_sentences in docs_to_split.items():
        str_id = f"htb:{idx}"
        docs = conllu_docs[str_id]
        docs_after_split = split_docs(last_sentences, docs)
        for i, new_doc in enumerate(docs_after_split):
            for sent in new_doc:
                sent.metadata['doc_id'] += f"_{i + 1}"
        new_docs[str_id].extend(docs_after_split)
    return new_docs


def sort_docs_by_num_of_sent_and_if_new(merged_dicts):
    return sorted(merged_dicts.items(), key=lambda x: (x[0].count('_'), len(x[1])))


def main():
    conllu_folder = '../corpus/new_htb_zeldes/htb2_format_with_underscore'
    split_docs_folder = '../re_split_doc/done'
    output_folder = '../corpus/new_htb_zeldes/htb2_format_split_long'
    docid2last_sentences = get_docid2last_sentences(split_docs_folder)
    # base_folder = create_base_folder()
    base_folder = 'corpus/coref_docs_2_tag/split_base'
    conllu_docs = read_conllu_folder(conllu_folder)
    docs_after_split = get_split_docs(conllu_docs, docid2last_sentences)
    # Get the docs that are we didn't split + the bew docs
    # Write them as a conllu file in the relevant folder
    # Write the docs in a
    merged_dicts = merge_dicts(conllu_docs, docs_after_split)
    sorted_docs = sort_docs_by_num_of_sent_and_if_new(merged_dicts)

    dump_conllu_docs(output_folder, sorted_docs)
    # Manually check git changes in the base folder
    check_git_changes(base_folder)

    # Run make_tne_docs.py
    run_make_tne_docs()


if __name__ == "__main__":
    main()
