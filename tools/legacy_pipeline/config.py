basic_features = {'gen=F|gen=M': 'Gender=Fem,Masc', 'gen=F': 'Gender=Fem', 'gen=M': 'Gender=Masc',
                  'num=S': 'Number=Sing', 'num=P': 'Number=Plur',
                  'per=A': 'Person=1,2,3', 'per=': 'Person=',
                  'tense=BEINONI': 'VerbForm=Part', 'tense=TOINFINITIVE': 'VerbForm=Inf',
                  'tense=IMPERATIVE': 'Mood=Imp',
                  'tense=PAST': 'Tense=Past', 'tense=FUTURE': 'Tense=Fut'
                  }
basic_tag ={
    "num": "nummod",
    "number": "nummod",
    "subj": "nsubj"

}

basic_pos = {
    'IN': 'ADP', 'CC':'SCONJ','NNP': 'PROPN', 'JJ': 'ADJ', 'NN': 'NOUN', 'VB': 'VERB', 'RB': 'ADV', 'NCD': 'NUM', 'NEG': 'ADV',
    'PREPOSITION': 'ADP', 'REL': 'SCONJ', 'COM': 'SCONJ', 'CONJ': 'CCONJ', 'POS': 'ADP', 'PRP': 'PRON',
    'yyCLN': 'PUNCT', 'yyCM': 'PUNCT', 'yyDASH': 'PUNCT', 'yyDOT': 'PUNCT', 'yyELPS': 'PUNCT', 'yyEXCL': 'PUNCT',
    'yyLRB': 'PUNCT', 'yyQM': 'PUNCT', 'yyQUOT': 'PUNCT', 'yyRRB': 'PUNCT', 'yySCLN': 'PUNCT', 'ZVL': 'X'
}
entire_line_pos_conversion = {
    'AT': {'pos': 'ADP', 'deprel': 'case:acc', 'feats': {'old': '_', 'new': 'Case=Acc'}},
    'BN': {'pos': 'VERB', 'deprel': 'deprel', 'feats': {'old': 'feats+', 'new': "|VerbForm=Part"}},
    'BNT': {'pos': 'VERB', 'deprel': 'deprel',
            'feats': {'old': '+feats+', 'new': ['Definite=Cons|', '|VerbForm=Part']}},
    'CD': {'pos': 'NUM', 'deprel': 'deprel', 'feats': 'feats'},
    'CDT': {'pos': 'NUM', 'deprel': 'deprel', 'feats': {'old': '+feats', 'new': "Definite=Cons|"}},
    'NNT': {'pos': 'NOUN', 'deprel': 'deprel', 'feats': {'old': '+feats', 'new': "Definite=Cons|"}},
    'COP': {'pos': 'AUX', 'deprel': 'deprel', 'feats': {'old': 'feats+', 'new': "|VerbType=Cop|VerbForm=Part"}},
    'DEF': {'pos': 'DET', 'deprel': 'deprel', 'feats': {'old': '_', 'new': 'PronType=Art'}},
    'EX': {'pos': 'VERB', 'deprel': 'deprel', 'feats': {'old': '_', 'new': 'HebExistential=True'}},
    'P': {'pos': 'ADV', 'deprel': 'compound:affix', 'feats': {'old': '_', 'new': 'Prefix=True'}},
    'DUMMY_AT': {'pos': 'ADP', 'deprel': 'case:acc', 'feats': {'old': '_', 'new': 'Case=Acc'}},
    'JJT': {'pos': 'ADJ', 'deprel': 'deprel', 'feats': {'old': '+feats', 'new': 'Definite=Cons|'}},
    'MD': {'pos': 'AUX', 'deprel': 'deprel', 'feats': {'old': 'feats+', 'new': '|VerbType=Mod'}},
    'QW': {'pos': 'ADV', 'deprel': 'deprel', 'feats': {'old': '_', 'new': 'PronType=Int'}},
    'TEMP': {'pos': 'SCONJ', 'deprel': 'mark', 'feats': {'old': '_', 'new': 'Case=Tem'}},
    'DTT': {'pos': 'DET', 'deprel': 'deprel', 'feats': {'old': '_', 'new': 'Definite=Cons'}},
    'S_ANP': {'pos': 'PRON', 'deprel': 'deprel', 'feats': {'old': '+feats+', 'new': ['Case=Acc|', '|PronType=Prs']}}

}