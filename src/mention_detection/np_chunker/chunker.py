from typing import List

import spacy.tokens
from spacy.tokens import Token

COMPOUND_SMIXUT = "compound:smixut"


class Chunker:
    HEB_CLOSE_BRACKET = ")"
    HEB_OPEN_BRACKET = "("
    NOUNS = {"PROPN", "NOUN"}
    PROP = "PRON"
    NOUN_FAMILY = {"PROPN", "NOUN", "PRON"}
    VERBS_POS = {'VERB', 'AUX'}
    LOC_ADVERB = {
        "פה",
        "כאן",
        "שם",
        "למטה",
        "למעלה",
        "קדימה",
        "אחורה",
        "בצד",
        "מזרח",
        "מערב",
        "צפון",
        "דרום"
    }
    TIME_ADVERB = {
        "אתמול",
        "שלשום",
        "אמש",
        "מחר",
        "מחרתיים",
        "אז",
        "פעם",
        "השנה",
        "שנה",
        "החודש",
        "חודש",
        "השבוע",
        "שבוע",
        "היום",
        "יום"
    }

    QUANTIFIERS_NOT_TO_BREAK ={'אילו', 'ה_', 'אותן','אותם','אותה','אותו', 'ה'}
    QUANTIFIERS = {'דווקא', 'הללו', 'למשל', 'כמעט', 'אחד', '88', 'אולי', 'אלה', 'מין', 'מקצת', 'שאר', 'בוודאי',
                   'מרבה', 'לשעבר', 'אותן', 'כלשהו', 'כן', 'אותו', 'המון', 'רבות', '3', 'במיוחד', 'מאה',
                   '13', '10', 'בדיוק', 'מרבית',  'אלו', 'סתם', 'איזו', 'כל', 'רוב', 'הרבה', 'אינם', 'שום',
                   'פי', 'מספיק', 'אחת', '65', 'שתיים', 'די', 'לא', 'כלשהן', 'זה', 'אלא', 'דהיינו',
                   'אחדים', 'איזה', 'איש', 'שלושה', 'חלק', 'כלשהם', 'כלל', 'מרב', 'עוד', 'הכל',
                   'מדי', 'כבר', 'אפילו', 'שש', 'שליש', 'כלומר', 'בכלל', 'כלשהי', 'אף', 'מחצית', 'קצת', 'פלוס',
                   'שניים', 'כ', 'הן', 'בעיקר', 'שאט', 'לפחות', 'אותה', 'כמובן', 'מספר', 'רבים', 'הלא', 'עדיין',
                   'מעט', 'ארבעה', 'גם', 'כמה', 'זו', 'אותם', 'רק', 'מ', 'איזושהי', 'מעין', 'אחוז', 'זאת', 'יתר',
                   'בפירוש', 'בערך'} #TODO  does number always serve as quantifiers? if yes - catch all, if not, remove them


    PUNCT_IN_CHUNK = {"(", ")"}

    NEVER_MENTION = {"%", "$" }


    LOC_AND_TIME_ADVERB = LOC_ADVERB.union(TIME_ADVERB)
    NP_LABEL = "*"
    right_labels = {"det", "fixed", "nmod:poss", "amod", "nummod", "appos", COMPOUND_SMIXUT, "flat:name", "conj"}
    left_labels = {"fixed", "amod", "nummod", "cc", COMPOUND_SMIXUT, "appos", "flat:name", "nmod:poss", "conj", "nmod", "advmod", "acl:relcl", "acl"} #nmod זה אומר שמחברים "ב" "על" וכו


    left_labels_for_conj = left_labels.copy()
    left_labels_for_conj.remove("conj")
    left_labels_for_conj.remove("nmod")

    left_labels_for_appos = left_labels.copy()
    left_labels_for_appos.remove("appos")

    left_labels_for_without_verbs_relative_clause = left_labels.copy()
    left_labels_for_without_verbs_relative_clause.remove("acl:relcl")

    right_labels_for_quantitative = right_labels.copy()
    right_labels_for_quantitative.remove("nummod")

    right_labels_for_det_quantitative = right_labels.copy()
    right_labels_for_det_quantitative.remove("det")

    stop_labels = ["punct"]

    def __init__(self, take_longest: bool, allow_nested: bool, allow_loc_time_adv: bool, possessive: bool,
                 allow_inner_quantitative:bool, allow_inner_acl:bool):
        self.take_longest = take_longest
        self.allow_nested = allow_nested
        self.allow_loc_time_adv = allow_loc_time_adv
        self.possessive = possessive
        self.with_inner_quantitative = allow_inner_quantitative
        self.with_inner_acl = allow_inner_acl
        #TODO - try to chnage it to allow only specific punt
        # Becuase now I have an issue with this mention:
        #הערבים אלא על הנחשים
        #also I still have the issue with appos, I nee dto verify I take both sides, like I did with conj

        if self.take_longest:
            self.left_stop_condition = lambda t: self._stop_canonization(t)
        else:
            self.left_stop_condition = lambda t: self._stop_canonization(t) or (
                    t.dep_ in self.stop_labels and t.text != "-")

    def is_time_and_location_adv(self, token):
        return token.pos_ == "ADV" and token.lemma_ in self.LOC_AND_TIME_ADVERB

    @staticmethod
    def __remove_nested(chunks, is_chunk):
        for i, i_chunk in enumerate(chunks[:-1]):
            i_left, i_right, _ = i_chunk
            for j, j_chunk in enumerate(chunks[i + 1:], start=i + 1):
                j_left, j_right, _ = j_chunk
                if j_left <= i_left < i_right <= j_right:
                    is_chunk[i] = False
                if i_left <= j_left < j_right <= i_right:
                    is_chunk[j] = False

    @staticmethod
    def __take_longest_seq(chunks, is_chunk):
        to_remove = []
        to_change = []
        for i, i_chunk in enumerate(chunks[:-1]):
            i_left, i_right, _ = i_chunk
            for j, j_chunk in enumerate(chunks[i + 1:], start=i + 1):
                j_left, j_right, _ = j_chunk
                if not is_chunk[i] or not is_chunk[j]:
                    continue

                if j_left <= i_right < j_right:
                    to_change.append((i, (i_left, j_right, _)))
                    to_remove.append(j)

        for i, change in to_change:
            chunks[i] = change
        chunks = [i for j, i in enumerate(chunks) if j not in to_remove]
        is_chunk = [i for j, i in enumerate(is_chunk) if j not in to_remove]
        return chunks, is_chunk

    def _stop_canonization(self, tok):
        if tok.pos_ in self.VERBS_POS and tok.dep_ in {"amod", COMPOUND_SMIXUT, } and tok.head.pos_ == "NOUN":
            return False
        if tok.pos_ in self.VERBS_POS and any(t.pos_ in self.NOUNS and t.dep_ == COMPOUND_SMIXUT for t in self.get_heb_left_children(tok)):
            return False
        if tok.pos_ in self.VERBS_POS and tok.dep_ in {"acl:relcl"} and tok.head.pos_ in {"NOUN", "ADV"}:
            return False
        if tok.pos_ in self.VERBS_POS and tok.dep_ in {"xcomp"} and tok.head.pos_ in self.VERBS_POS:
            return False
        return tok.pos_ in self.VERBS_POS

    @staticmethod
    def get_heb_right_children(tok: Token):
        return tok.lefts

    def __get_right_bound(self, root, right_labels):
        right_bound = root
        for tok in reversed(list(self.get_heb_right_children(root))):
            if tok.dep_ in right_labels and not (tok.dep_ == "det" and tok.pos_ == 'CCONJ'): # אפילו [הם] במקום [אפילו הם]
                right_bound = tok
        if root != right_bound and right_bound.dep_ == "nummod" and right_bound.pos_ == "NUM":
            return self.__get_right_bound(right_bound, right_labels)
        return right_bound

    def part_of_acl(self, tok):
        return any(t.dep_ == "acl" for t in tok.ancestors)

    def _should_continue_canonization(self, root, tok, left_labels):

        # Allow to add acl sub-trees under a mention
        if self.part_of_acl(tok):
            return True
        # To allow the special case VERB-NOUN when the connection is COMPOUND_SMIXUT but not to stop canonization
        # for complex mentions that contain verbs

        if all([root.pos_ in self.VERBS_POS,
                root.dep_ not in {"acl:relcl", "xcomp"},
                tok.dep_ not in {COMPOUND_SMIXUT, "nmod:poss", "xcomp"}]):
            return False
        # relevant only for gold chunk - when we don't know for sure which tag is the head, I prefer not to take it
        if "HebSource=ConvUncertainHead" in tok._.conll_misc_field and tok.dep_ != "advmod":
            return False

        # Verify a word with a dep of conj and has a right children of case wouldn't be a mention
        # לא רק מהתופעה המבישה אלא גם מדרכי הערמה
        if tok.dep_ == "conj" and any(t.dep_ == "case" for t in self.get_heb_right_children(tok)):
            return False

        conditions = [tok.dep_ in left_labels,
                      tok.dep_ == "det" and tok.pos_ == "PRON",  # רקע זה, ולא -> רקע
                      tok.dep_ in {"obj", "obl"} and tok.pos_ in self.NOUN_FAMILY and root.dep_ in {'acl:relcl', 'xcomp' },  # allowing verbs  שדנה בנושא העסקת עובדים ולא שדנה ודוגמא נוספת: שהצליח להביס סנאטור מכהן ולא שהצליח
                      tok.dep_ in {"xcomp"} and tok.pos_ in self.VERBS_POS and root.dep_ == 'acl:relcl',  # allowing verbs שדנה בנושא העסקת עובדים ולא שדנה
                      ]

        if self.possessive:
            conditions.append(  # (מועמדים של_ _היא)
                tok.dep_ == "nmod" and any(i.dep_ == "case:gen" for i in self.get_heb_right_children(tok)))

        if self.take_longest:
            conditions.append(tok.text in self.PUNCT_IN_CHUNK)
        return any(conditions)

    @staticmethod
    def get_heb_left_children(tok: Token):
        return tok.rights

    def __exist_a_verb_token_span(self, doc, root, last_word):
        if self.part_of_acl(last_word):
            return False
        for t in doc[root.i: last_word.i + 1]:
            if self.left_stop_condition(t):
                return True
        return False

    def __get_left_bound(self, doc, cur_root, left_labels):
        left_bound = cur_root
        for tok in self.get_heb_left_children(cur_root):
            if self._should_continue_canonization(cur_root, tok, left_labels):
                left = self.__get_left_bound(doc, tok, left_labels)
                if self.__exist_a_verb_token_span(doc, cur_root, left):
                    break
                else:
                    left_bound = left
        return left_bound

    def _get_bounds(self, doc, cur_root, left_labels, right_labels) -> object:
        return self.__get_right_bound(cur_root, right_labels), self.__get_left_bound(doc, cur_root, left_labels)

    @staticmethod
    def _chunks2biose(chunks, sent_len):
        biose_tags = [''] * sent_len
        for (start, end, label) in chunks:

            if start + 1 == end:
                biose_tags[start] += f'S-{label}^'
            elif start + 2 == end:
                biose_tags[start] += f'B-{label}^'
                biose_tags[end - 1] += f'E-{label}^'
            else:
                biose_tags[start] += f'B-{label}^'
                for j in range(start + 1, end - 1):
                    biose_tags[j] += f'I-{label}^'
                biose_tags[end - 1] += f'E-{label}^'

        final_tags = [t.strip("^") if t != '' else "O" for t in biose_tags]
        return final_tags

    @staticmethod
    def _chunks2bio(chunks, sent_len):
        bio_tags = [''] * sent_len
        for (start, end, label) in chunks:
            bio_tags[start] += f'B-{label}^'
            for j in range(start + 1, end):
                bio_tags[j] += f'I-{label}^'
        final_tags = [t.strip("^") if t != '' else "O" for t in bio_tags]
        return final_tags

    def get_noun_chunks(self, spacy_doc: spacy.tokens.Doc, chunk_type: str) -> List:
        chunks = []
        for token in spacy_doc:
            if self.np_root_conditions(token):
                right, left = self._get_bounds(spacy_doc, token, self.left_labels, self.right_labels)
                right, left = self.postprocess(right, left)

                if self.should_filter_mention(right, left):
                    continue
                chunks.append((right.i, left.i + 1, self.NP_LABEL))

        for token in spacy_doc:  # conjunction
            if self.np_root_conditions(token) and any(c.dep_ == "conj" for c in token.children):
                right, left = self._get_bounds(spacy_doc, token, self.left_labels_for_conj, self.right_labels)
                right, left = self.postprocess(right, left)
                chunks.append((right.i, left.i + 1, self.NP_LABEL))

        for token in spacy_doc:  # apposition
            if self.np_root_conditions(token) and any(c.dep_ == "appos" for c in token.children):
                right, left = self._get_bounds(spacy_doc, token, self.left_labels_for_appos, self.right_labels)
                right, left = self.postprocess(right, left)
                chunks.append((right.i, left.i + 1, self.NP_LABEL))

        # Filtering mentions -->
        # can take only the chunks that came from here (the quantitative for-loop) and remove their inner mentions
        if self.with_inner_acl:
            for token in spacy_doc:  # mentions without relative clause
                if self.np_root_conditions(token) and any(c.dep_ == "acl:relcl" for c in token.children):
                    right, left = self._get_bounds(spacy_doc, token, self.left_labels_for_without_verbs_relative_clause, self.right_labels)
                    right, left = self.postprocess(right, left)
                    if self.should_filter_mention(right, left):
                        continue

                    chunks.append((right.i, left.i + 1, self.NP_LABEL))

        # Filtering mentions (עשרות אנשים" ולא "עשרות אנשים" ו"אנשים"  י")
        # can take only the chunks that came from here (the quantitative for-loop) and remove their inner mentions
        if self.with_inner_quantitative:
            quinataticve = self.extract_quantitative(spacy_doc)
            chunks.extend(quinataticve)
            for token in spacy_doc:  # inner det quantitative
                if self.np_root_conditions(token) and any(c.dep_ == "det" and c.text not in self.QUANTIFIERS_NOT_TO_BREAK for c in self.get_heb_right_children(token)):
                    right, left = self._get_bounds(spacy_doc, token, self.left_labels, self.right_labels_for_det_quantitative)
                    right, left = self.postprocess(right, left)
                    if self.should_filter_mention(right, left):
                        continue

                    chunks.append((right.i, left.i + 1, self.NP_LABEL))

        for token in spacy_doc:  # flat names
            if token.pos_ == "PROPN" and token.dep_ not in {"det"} or                                   \
               token.pos_ == "PROPN" and token.dep_ == COMPOUND_SMIXUT and token.head.pos_ == "VERB" or \
               token.pos_ == "NOUN" and any(tok.dep_ == "flat:name" for tok in token.children):
                right, left = self._get_bounds(spacy_doc, token, {"flat:name", COMPOUND_SMIXUT}, self.right_labels)
                right, left = self.postprocess(right, left)
                if right != left:
                    chunks.append((right.i, left.i + 1, self.NP_LABEL))

        for token in spacy_doc:  # verify pronouns
            if token.pos_ == "PRON" and token.dep_ not in {"det", "cop"} and token.text not in {"כן","כך"}:
                chunks.append((token.i, token.i + 1, self.NP_LABEL))

        chunks = self.dedup_chunks(chunks)
        is_chunk = [True] * len(chunks)
        if not self.allow_nested:
            self.__remove_nested(chunks, is_chunk)
            chunks, is_chunk = self.__take_longest_seq(chunks, is_chunk)
        final_chunks = [c for c, ischk in zip(chunks, is_chunk) if ischk]
        self.sort_chunks_by_order(final_chunks)
        if chunk_type == "BIO":
            return self._chunks2bio(final_chunks, len(spacy_doc))
        elif chunk_type == "BIOSE":
            res = self._chunks2biose(final_chunks, len(spacy_doc))
            return res
        elif chunk_type == "webanno":
            return self._rename_nested(final_chunks)
        elif chunk_type == "flat":
            return final_chunks

        else:
            raise ValueError("chunk type need to be one of the following {BIO, BIOSE, webanno, flat} "
                             "but flat is for inner use ")

    def should_filter_mention(self, right, left):
        # Not to break names and short COMPOUND_SMIXUT דרום לבנון תנועת המושבים
        return self.is_non_mention_single_word( right, left) or self.is_smixut_w_det( right, left)

    def is_smixut_w_det(self,  right, left):
        # תנועת ה מושבים | שכר ה מינימום |
        return self.is_successive_words(right, left) and right.dep_ == "det" and left.dep_ == COMPOUND_SMIXUT

    def is_non_mention_single_word(self,  right, left):
        return right == left and (right.dep_ in {"flat:name", COMPOUND_SMIXUT} or
                                  right.lemma_ in self.NEVER_MENTION)

    def extract_quantitative(self, spacy_doc):
        res =[]
        for token in spacy_doc:  # inner quantitative
            if self.np_root_conditions(token) and any(c.dep_ == "nummod" for c in self.get_heb_right_children(token)):
                right, left = self._get_bounds(spacy_doc, token, self.left_labels, self.right_labels_for_quantitative)
                right, left = self.postprocess(right, left)
                res.append((right.i, left.i + 1, self.NP_LABEL))
        return res


    def sort_chunks_by_order(self, final_chunks):
        final_chunks.sort(key=lambda x: (x[0], -x[1]))

    def np_root_conditions(self, token):
        return any([token.pos_ in self.NOUNS,
                    # allow smixut when the father is not NOUN -> ממלא מקום שר העבודה
                    token.pos_ == "VERB" and any(t.dep_ == COMPOUND_SMIXUT for t in self.get_heb_left_children(token)),
                    token.pos_ == "VERB" and any(t.dep_ == "det" for t in self.get_heb_right_children(token)),
                    token.pos_ == self.PROP and token.dep_ not in {"det", "cop"}, # Exclude demonstrative -> "רקע זה" and not "זה"
                    token.pos_ == "NUM" and token.dep_ == "obl", #ב [המאה הזו], ב [1967]
                    self.is_time_and_location_adv(token) and self.allow_loc_time_adv])

    def postprocess(self, right, left):
        """
        All edge cases may be dealt here.
        mostly punctuation issues.
        """
        if left.text == self.HEB_CLOSE_BRACKET and all([i.text != self.HEB_OPEN_BRACKET for i in right.doc[right.i:left.i]]):
            return right, left.doc[left.i - 1]
        elif left.i + 1 < len(left.doc) and len([t for t in right.doc[right.i: left.i+1] if t.text == '"']) == 1 and right.doc[left.i+1].text == '"':
            return right, left.doc[left.i + 1]
        elif self.has_only_one_quate(left, right) and right.doc[right.i - 1].text == '"':
            return right.doc[right.i - 1], left

        else:
            return right, left

    def has_only_one_quate(self, left, right):
        return len([t for t in right.doc[right.i: left.i + 1] if t.text == '"']) == 1

    @staticmethod
    def dedup_chunks(chunks):
        return list(dict.fromkeys(chunks))

    def _rename_nested(self, final_chunks):
        positions = []
        res = []
        for chunk in final_chunks:
            start, end, label = chunk
            if any(start >= s_cand and end <= e_cand for s_cand, e_cand in positions):
                res.append((start, end, self.NP_LABEL))
            else:
                res.append(chunk)
            positions.append((start, end))
        return res

    def is_successive_words(self, right, left):
        return left.i - right.i == 1
