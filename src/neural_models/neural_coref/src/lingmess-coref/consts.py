SUPPORTED_MODELS = ['longformer', 'roberta', 'bert']
SPEAKER_START = '#####'
SPEAKER_END = '###'
NULL_ID_FOR_COREF = -1


PRONOUNS_GROUPS = {
            'i': 0, 'me': 0, 'my': 0, 'mine': 0, 'myself': 0,
            'you': 1, 'your': 1, 'yours': 1, 'yourself': 1, 'yourselves': 1,
            'he': 2, 'him': 2, 'his': 2, 'himself': 2,
            'she': 3, 'her': 3, 'hers': 3, 'herself': 3,
            'it': 4, 'its': 4, 'itself': 4,
            'we': 5, 'us': 5, 'our': 5, 'ours': 5, 'ourselves': 5,
            'they': 6, 'them': 6, 'their': 6, 'themselves': 6,
            'אני': 7, 'עצמי': 7,
            'הוא': 8, 'עצמו': 8,'אותו': 8,'כלשהו': 8,
            'היא': 9, 'עצמה': 9, 'אותה': 9, 'כלשהי': 9,
            'הן': 10, 'שתיהן': 10, 'בלשהן': 10,
            'הם': 11, 'עצמם': 11, 'שניהם': 11,'הללו': 11,'אלה': 11,'אלו': 11,
            'אנחנו': 12, 'אנו': 12, 'עצמנו': 12, 'הננו': 12, 'אותנו': 12,
            'אתה': 13,# 'עצמך': 13,
            'את': 14,# 'עצמך': 13,
            'זה': 15,'זהו': 15, 'כך': 15,
            'זו': 16, ';זאת': 16,

}

STOPWORDS = {"'s", 'a', 'all', 'an', 'and', 'at', 'for', 'from', 'in', 'into',
             'more', 'of', 'on', 'or', 'some', 'the', 'these', 'those',
    'ה',
    'ו',
    'או',
    'ב',
    'על',
    'ל',
    'מ',
    'מן',
    'של',
    'כל',
    'יותר',
    'כמה',
    'איזשהו',
    # 'אלה',
    # 'אלו',
    'לתוך',
    'אצל',
    'בשביל',
    'זה',
    'זאת',
    'מה',
    'מי',
}




CATEGORIES = {'pron-pron-comp': 0,
              'pron-pron-no-comp': 1,
              'pron-ent': 2,
              'match': 3,
              'contain': 4,
              'other': 5
              }

