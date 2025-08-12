# tne_ui[^1]

[^1]:Please, note that this code is suitable for texts that inlude one title, one or more subtitles (optionally) and one or more paragraphs (strictly in this order). If the structure of the text is different (e.g. each paragraph has its own subtitle), the user will need to make necessary adjustments to the code.
## Loading Data

### Starting from unannotated text (only for English)
1\. The original texts should be saved in an input directory in json files as a list of objects (one object per text). The objects should have the following format:

```
{

        "id": int,        

        "title": str, 

	"url": str,	

        "sub_title": [

            str,

	    str,

	    str,

	    ...

        ],

        "paragraph": [

            str,

	    str,

	    str,

	    ...        
	]

}
```
	
(An example of the input format can be found in the directory ["original_format"](https://github.com/vikasaeta/tne_ui/tree/master/original_format) in this repository.)
	
2\. Convert the texts to the format suitable for further use (see detailed description of the format below).

  `>> python format_json.py -in <name-of-input-directory> -out <name-of-output-directory>` 

**The output directory of this step will be the input directory of step 3 below.**
An example of the resulting format can be found in the directory ["formatted_data"](https://github.com/vikasaeta/tne_ui/tree/master/formatted_data) in this repository.)

3\. Load the texts to the database.

 `>> python load_to_db.py -in <name-of-input-directory> -out <name-of-directory-with-db> -db <name-of-db>`

 **The input directory of this step is the output directory of step 2 above.**

4\. Go to step 5 below.

### Starting from text and a list of NPs[^2]

[^2]:When working with a language other than English, you might need to edit the list of prepositions, the instructions and prompts for annotators and the help boxes and the html files in the [static directory](https://github.com/vikasaeta/tne_ui/tree/master/static).

1\. The original texts should be saved in an input directory in json files as a list of objects (one object per text). 
An object consists of:

* `nps`: a list of nps to be annotated where each item contains a dictionary:
  * `text`: the text of the np (string)
  * `start_index`: an integer indicating the starting index in the text
  * `end_index`: an integer indicating the ending index in the text  
  * `id`: the id of the np (integer).
The start and end indexes refer to the raw_text field of the "tx" dictionary (see below).[^3]

[^3]:We used so-called base-NPs as annotation items. For English we used Spacy to identify base-nps.
* `done_nps`: a dictionary that  maps each np id (from nps) to a boolean (true/false).
An np is "done" when it has been visited and annotated. Therefore originally all the values in this dictionary should be "false".
* `pronouns`: a list that holds the ids of the nps that are pronouns.
At the linking stage these nps will be removed from the list of items for annotation and from the coref clusters shown to the annotators (but will remain in the data latently).
* `tx`: a dictionary holding the information about the text. It includes the following fields:
  * `raw_text`: the text of the document as a string with no separators between the title/subtitles/paragraphs.
  * `title`: the title of the text (string).
	  * `start_index`: an integer indicating the starting index of the title in the raw_text
	  * `end_index`: an integer indicating the ending index of the title in the raw_text
  * `subtitles`: a list of subtitles where each item contains a dictionary:  
	  * `start_index`: an integer indicating the starting index of the subtitle in the raw_text
	  * `end_index`: an integer indicating the ending index of the subtitle in the raw_text  
	  * `id`: the id of the subtitle (integer)
  * `paragraphs`: a list of paragraphs where each item contains a dictionary:  
	  * `start_index`: an integer indicating the starting index of the paragraph in the raw_text
	  * `end_index`: an integer indicating the ending index of the paragraph in the raw_text  
	  * `id`: the id of the paragraph (integer)
* `source_file`: the name of the file containing the current object	(string)  
* `url`: the url where the document was taken from (string, can be "None")
* `text_id`: the id of the current object (integer)

(An example of this format can be found in the directory ["formatted_data"](https://github.com/vikasaeta/tne_ui/tree/master/formatted_data) in this repository.)

2\. Load the texts to the database.

`>> python load_to_db.py -in <name-of-input-directory> -out <name-of-directory-with-db> -db <name-of-db>`

3\. Go to step 5 below.


## Annotating Coref Relations

5\. Run 

`>> python annotationServer.py --debug -db_dir <name-of-directory-with-db> -db <name-of-db>`

and use the URL 

`/tne/tool/coref/<hit_id:int>` 

in your browser to use the coref annotation UI.


We include a training tool for the coreference step. To use the tool, run

`>> python annotationServer.py --debug -db_dir <name-of-directory-with-db> -db <name-of-db>`

and use the URL 

`/static/coref_training.html` 

in your browser.

**The --debug flag is optional and is only used when the application is run locally for development purposes.**[^4]

[^4]: This flag exists mainly to make it possible to run the application locally on Windows, because when the --debug flag is omitted, the application uses gunicorn server which, in its turn, uses the fcntl module which is not available on Windows.


6\. After each HIT the annotator should transfer the annotation result to the user (e.g. submitting it to the requester through Amazon Mechanical Turk). It should be submitted exactly as it appears on the final screen of the UI. 

- Save the json documents submitted by the annotators in a jsonl file for coref annotation results, one document per line (as in [coref_annotations.jsonl](https://github.com/vikasaeta/tne_ui/tree/master/coref_annotations.jsonl)).

- Load the coref annotation results to the database.

`>> python coref_results_to_db.py -in <name-of-input-jsonl-file-with-coref-results> -db_dir <name-of-directory-with-db> -db <name-of-db> [ -a <name-of file-with-annotator_ids>]`[^5]

[^5]: Annotator ids in this file are stored 1 per line. You can find examples of this format in files [coref_annotators.txt](https://github.com/vikasaeta/tne_ui/tree/master/coref_annotators.txt), [link_annotators.txt](https://github.com/vikasaeta/tne_ui/tree/master/link_annotators.txt) and [cons_annotators.txt](https://github.com/vikasaeta/tne_ui/tree/master/cons_annotators.txt).
The lines correspond to the lines of the input file with the annotation results (the "-in" argument). E.g. annotator id in line 1 of [coref_annotators.txt](https://github.com/vikasaeta/tne_ui/tree/master/coref_annotators.txt) corresponds to the annotation in line 1 of [coref_annotations.jsonl](https://github.com/vikasaeta/tne_ui/tree/master/coref_annotations.jsonl). 
If no such file is provided, the database will contain no annotator ids.

## Annotating NP-Relations

7\. Now you can annotate the texts for links.

Run 

`>> python annotationServer.py --debug -db_dir <name-of-directory-with-db> -db <name-of-db>`

and use the URL 

`/tne/tool/links/<hit_id:int>/<coref_ann_id:int>` 

in your browser to use the link annotation UI.[^6]

[^6]:Since there might be multiple coref annotations of the same text (by different annotators), each annotation of the same HIT has its own id in the database (the "annotation_id" column). The coref_ann_id variable corresponds to the "annotation_id" of the coref annotation you want to use (e.g. 1 indicates that you want to use the first one etc.). 

We include an introduction and a training tool for the coreference step. To use the instructions, run

`>> python annotationServer.py --debug -db_dir <name-of-directory-with-db> -db <name-of-db>`

and use the URL 

`/static/intro_tne.html` 

in your browser.

To use the training tool, run

`>> python annotationServer.py --debug -db_dir <name-of-directory-with-db> -db <name-of-db>`

and use the URL 

`static/tne_training.html` 

in your browser.


**The --debug flag is optional and is only used when the application is run locally for development purposes.**[^4]


8\. After each HIT the annotator should transfer the annotation result to the user (e.g. submitting it to the requester through Amazon Mechanical Turk). It should be submitted exactly as it appears on the final screen of the UI. 

- Save the json documents submitted by the annotators in a jsonl file for link annotation results, one document per line (as in [link_annotations.jsonl](https://github.com/vikasaeta/tne_ui/tree/master/link_annotations.jsonl)).

- Load the links annotation results to the database.


`>> python link_results_to_db.py -in <name-of-input-jsonl-file-with-link-results> -db_dir <name-of-directory-with-db> -db <name-of-db> [ -a <name-of file-with-annotator_ids>]`[^5]



## Consolidation Step 
9\. Now you can perform the consolidation step.

Run 

`>> python annotationServer.py --debug -db_dir <name-of-directory-with-db> -db <name-of-db>` 

and use the URL 

`/tne/tool/consolidation/<hit_id:int>/<coref_ann_id:int>` 

in your browser to use the consolidation UI.[^6]


**The --debug flag is optional and is only used when the application is run locally for development purposes.**[^4]

10\. After each HIT the annotator should transfer the annotation result to the user (e.g. submitting it to the requester through Amazon Mechanical Turk). It should be submitted exactly as it appears on the final screen of the UI. 

- Save the json documents submitted by the annotators in a jsonl file for consolidation annotation results, one document per line (as in [cons_annotations.jsonl](https://github.com/vikasaeta/tne_ui/tree/master/cons_annotations.jsonl)).

- Load the consolidation annotation results to the database.

`>> python cons_results_to_db.py -in <name-of-input-jsonl-file-with-consolidation-results> -db_dir <name-of-directory-with-db> -db <name-of-db> [ -a <name-of file-with-annotator_ids>]`[^5]

## Exporting Your Results in Annoatated Corpus Format 

11\. Convert the data to the final output format.

`>> python data_to_final_format.py -db_dir <name-of-directory-with-db> -db <name-of-db> -out <name of the output jsonl file>`

You can find an example of the output format in [this file](https://github.com/vikasaeta/tne_ui/blob/master/final_data.jsonl). The description of the format can be found [here](https://github.com/yanaiela/TNE/blob/main/README.md).

## Browsing the Results

12\. To view the results of the three stages of the annotation, run 

`>> python annotationServer.py --debug -db_dir <name-of-directory-with-db> -db <name-of-db>`

and use the following URLs:

   - `/tne/results/coref/<hit_id:int>` (for coref)

   - `/tne/results/links/<hit_id:int>/<coref_ann_id:int>/<links_ann_id:int>` (for links)[^7]

[^7]:Since there might be multiple coref annotations of the same text (by different annotators), each annotation of the same HIT has its own id in the database (the "annotation_id" column). The coref_ann_id variable corresponds to the "annotation_id" of the coref annotation you want to use (e.g. 1 indicates that you want to use the first one etc.). 
The same principle applies to the links_ann_id variable which corresponds to the "annotation_id" from the tne_links_data table in the database. 


   - `/tne/results/consolidation/<hit_id:int>/<coref_ann_id:int>` (for consolidation)[^6]
   
**The --debug flag is optional and is only used when the application is run locally for development purposes.**[^4]
