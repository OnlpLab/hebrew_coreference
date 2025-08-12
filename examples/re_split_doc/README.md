# How do I split documents?

1. Go to the `Document Distribution` Google Doc under the url: https://docs.google.com/document/d/1lXxsUus_wDhLBz_Y6WSQMLe3U935DdDe5zEF1-NkXrA/edit#
2. Find the longest un split document.
3. Go to the `TNE` UI. https://nlp.biu.ac.il/~shaked571/tne_heb_coref/tne/tool/coref/<doc_id> (the idx **not** hit_id - it would be in the end of teh documents - the 10th longest would be ~240 )
4. Find out how the document starts.
5. Look up this string under the files in: `corpus/UD_row_sentence_only\<files>`
6. Look again in `Document Distribution` Google Doc see how many sentences are they in the doc and copy this number of rows to a file.
