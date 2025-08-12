from typing import Union, List, Dict, Sequence, Optional
import platform

import pandas as pd
import spacy
import streamlit as st

from spacy import displacy
from spacy.tokens import Span
from spacy_streamlit.util import get_html
from trankit import Pipeline

from np_chunker import Chunker
from trankit_parser import Trankit2Spacy

class ServeChunker:
    def __init__(self):
        if platform.system() == "Linux":
            cache_dir = "/home/nlp/shaked571/models"
            use_gpu = True

        elif platform.system() == "Darwin":
            cache_dir=r"/Users/s0g0a87/studies/HebNpChunker/trankit_parser/cache/trankit"
            use_gpu = False

        else:
            cache_dir=r"C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\trankit_parser\cache\trankit"
            use_gpu = False
        self.p = Pipeline('hebrew', cache_dir=cache_dir, gpu=use_gpu)
        self.t2s = Trankit2Spacy()
        self.chunker = Chunker(True, True, True, True,True, True)


    def chunk(self, sent):

        parsed_sents = self.p(sent, is_sent=True)
        doc = self.t2s.transform(parsed_sents)
        chunks = self.chunker.get_noun_chunks(doc, 'flat')

        doc.spans["sc"] = [
            Span(doc, start,end,label)
            for start,end,label in chunks]
        return doc



def visualize_span(
        doc: Union[spacy.tokens.Doc, List[Dict[str, str]]],
        *,
        labels: Sequence[str] = tuple(),
        attrs: List[str] = ["text", "label_", "start", "end", "start_char", "end_char"],
        show_table: bool = True,
        title: Optional[str] = "Named Entities",
        colors: Dict[str, str] = {},
        key: Optional[str] = None,
        manual: Optional[bool] = False,
        displacy_options: Optional[Dict] = None,
):
    """
    Visualizer for named entities.

    doc (Doc, List): The document to visualize.
    labels (list): The entity labels to visualize.
    attrs (list):  The attributes on the entity Span to be labeled. Attributes are displayed only when the show_table
    argument is True.
    title (str): The title displayed at the top of the NER visualization.
    colors (Dict): Dictionary of colors for the entity spans to visualize, with keys as labels and corresponding colors
    as the values. This argument will be deprecated soon. In future the colors arg need to be passed in the displacy_options arg
    with the key "colors".
    key (str): Key used for the streamlit component for selecting labels.
    manual (bool): Flag signifying whether the doc argument is a Doc object or a List of Dicts containing entity span
    information.
    displacy_options (Dict): Dictionary of options to be passed to the displacy render method for generating the HTML to be rendered.
    """
    if not displacy_options:
        displacy_options = dict()
    if colors:
        displacy_options["colors"] = colors

    if title:
        st.header(title)

    if manual:
        if show_table:
            st.warning(
                "When the parameter 'manual' is set to True, the parameter 'show_table' must be set to False."
            )
        if not isinstance(doc, list):
            st.warning(
                "When the parameter 'manual' is set to True, the parameter 'doc' must be of type 'list', not 'spacy.tokens.Doc'."
            )
    else:
        labels = labels or [ent.label_ for ent in doc.ents]

    if not labels:
        st.warning("The parameter 'labels' should not be empty or None.")
    else:
        exp = st.expander("Select entity labels")
        label_select = exp.multiselect(
            "Entity labels",
            options=labels,
            default=list(labels),
            key=f"{key}_ner_label_select",
        )

        displacy_options["ents"] = label_select
        html = displacy.render(
            doc,
            style="span",
            options=displacy_options,
            manual=manual,
        )
        style = "<style>mark.entity { display: inline-block }</style>"
        html = html.replace('" style="line-height: 2.5', '" style="line-height: 3.5')
        st.write(f'{style}{get_html(html)}', unsafe_allow_html=True, height=500, )
        if show_table:
            data = [
                [str(getattr(ent, attr)) for attr in attrs]
                for ent in doc.spans["sc"]
            ]
            if data:
                df = pd.DataFrame(data, columns=attrs)
                st.dataframe(df, )

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_chunker():
    print("$"*400)
    return ServeChunker()

def main():
    st.title("Mention detection using Trankit and an Hebrew mention detector")
    st.markdown("""
<style>
input {
  unicode-bidi:bidi-override;
  direction: RTL;
}
</style>
    """, unsafe_allow_html=True)

    user_input = st.text_input("Write here the text you would like to chunk! (better to work in 'Wide Mode' - see in the right bar under setting)",
                               "עשרות אנשים מגיעים מתאילנד לישראל כשהם נרשמים כמתנדבים, אך למעשה משמשים עובדים שכירים זולים.")
    doc = get_chunker().chunk(user_input)
    visualize_span(
        doc,
        labels=["NP"],
        show_table=False,
        colors={"NP": "linear-gradient(90deg, #aa9cfc, #fc9ce7)"},
        title="",
        key="Default Colors"
    )

if __name__ == '__main__':
    main()


