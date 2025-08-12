from np_chunker import make_doc_files_tne
import sys
sys.path.append(".")

if __name__ == '__main__':
    """
    Run with:
    HebNpChunker/make_tne_docs.py corpus/coref_docs_2_tag/base corpus/coref_docs_2_tag/tne_conll tne -n -l
    """
    make_doc_files_tne()

