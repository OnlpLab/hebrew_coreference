import bisect
import copy
import re
from itertools import chain
import spacy.tokens
from spacy.matcher import Matcher

from transformers import AutoModel, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('dicta-il/dictabert-seg')
model = AutoModel.from_pretrained('dicta-il/dictabert-seg', trust_remote_code=True)
model.eval()


def find_np_anchor(np, np_by_idx):
    for target_np in np_by_idx.values():
        if np['start_index'] == target_np['start_index'] or np['end_index'] == target_np['end_index']:
            return target_np
    # We prefer to find an easy anchor, and as a fallback we look for a hard one
    for target_np in np_by_idx.values():
        if target_np['start_index'] < np['start_index'] and target_np['end_index'] > np['end_index']:
            return target_np

    return None


def get_token_indices_from_spacy_doc(doc, start_char, end_char):
    indices = []
    for token in doc:
        if token.idx >= start_char and (token.idx + len(token)) <= end_char:
            indices.append(token.i)
    if indices:
        return indices[0], indices[-1] + 1
    else:
        return None, None


def enrich_np_by_anchor(np, anchor, full_doc):
    source_sent = full_doc[anchor['sent_num']]
    if np['end_index'] == anchor['end_index']:
        end_char = source_sent[anchor['end_token'] - 1].idx + len(source_sent[anchor['end_token'] - 1])
        start_char = end_char - len(np['text'])
    elif np['start_index'] == anchor['start_index']:

        start_char = source_sent[anchor['start_token']].idx
        end_char = start_char + len(np['text'])

    elif anchor['start_index'] < np['start_index'] and anchor['end_index'] > np['end_index']:
        np_loc = find_text_in_spacy_doc_single_sentence(np['text'],
                                                        source_sent[anchor['start_token']:anchor['end_token']])
        # TODO verify it is not dangerous - it already fucked me with doc 104 with:
        #  np['text'] == '411 301' that appear twice in a sentence

        try:
            start_token, end_token = np_loc
        except Exception as e:
            raise Exception("Too complex")
        start_char = source_sent[start_token].idx
        end_char = start_char + len(np['text'])

    else:
        raise Exception("Too complex")
    start, end = get_token_indices_from_spacy_doc(source_sent, start_char, end_char)
    if start is not None:
        np['start_token'] = start
        np['end_token'] = end
        np['sent_num'] = anchor['sent_num']

        return np
    else:
        raise Exception("Too complex")


def find_closest_nps(nps, target_np):
    target = (target_np['start_index'], target_np['end_index'])
    sorted_keys = sorted(list(nps.keys()))
    pos = bisect.bisect(sorted_keys, target)

    before = sorted_keys[max(0, pos - 1)] if pos - 1 >= 0 else None
    after = sorted_keys[min(len(sorted_keys) - 1, pos)] if pos < len(sorted_keys) else None

    return before, after


def find_start_token(doc, start_loc_in_sent):
    for t in doc:
        if t.idx == start_loc_in_sent:
            return t.i
        # if t.idx > start_loc_in_sent: # TODO a start of an idea of hueristic to solve this issue - but I think it would raise other issues and its too risky
        #     return doc[t.idx -1].i
    raise Exception(f"There is no token with this start location: {start_loc_in_sent} in doc {doc}")  # \n"
    # f"relevant span is {doc[] ")


def find_end_token(doc, end_loc_in_sent):
    for t in doc:
        if t.idx + len(t.text) == end_loc_in_sent:
            return t.i + 1
    raise Exception(f"There is no token with this end location: {end_loc_in_sent} ")


def final_np_matching_fallback(np, closest_after_sent, closest_before_sent):
    enriched_np = copy.deepcopy(np)
    # This is a hack - maybe can do something very complex
    # Update: we added find_text_in_spacy_doc_using_span_matching that supposed to be the very complex solution
    if np['text'] == 'אין. בי.איי' and np['start_index'] == 51 and np['end_index'] == 62:
        start = 0
        end = 1
        enriched_np['text'] = 'בי.איי'
        enriched_np['start_token'] = start
        enriched_np['start_index'] = 56
        enriched_np['end_token'] = end
        enriched_np['sent_num'] = closest_after_sent
        return enriched_np
    elif np['text'] == 'אחרונה' and np['start_index'] == 1416 and np['end_index'] == 1422:
        start = 0
        end = 1
        enriched_np['text'] = 'באחרונה'
        enriched_np['start_token'] = start
        enriched_np['end_token'] = end
        enriched_np['sent_num'] = closest_after_sent
        return enriched_np

    else:
        raise Exception("Too complex - fix manually")


def find_np_in_docs(np, original_np_by_idx, spacy_docs):
    closest_before, closest_after = find_closest_nps(original_np_by_idx, np)
    if closest_before and closest_after:
        closest_before_sent = original_np_by_idx[closest_before]['sent_num']
        closest_after_sent = original_np_by_idx[closest_after]['sent_num']
        if closest_before_sent == closest_after_sent:
            sent_num = closest_after_sent
            spacy_sent = spacy_docs[sent_num]
            before_anchor = spacy_sent[original_np_by_idx[closest_before]['end_token'] - 1]
            diff_from_prev = np['start_index'] - original_np_by_idx[closest_before]['end_index']
            start_loc_in_sent = before_anchor.idx + len(before_anchor.text) + diff_from_prev

            after_anchor = spacy_sent[original_np_by_idx[closest_after]['start_token']]
            diff_from_next = original_np_by_idx[closest_after]['start_index'] - np['end_index']
            end_loc_in_sent = after_anchor.idx - diff_from_next

            start = find_start_token(spacy_sent, start_loc_in_sent)
            end = find_end_token(spacy_sent, end_loc_in_sent)
            np['start_token'] = start
            np['end_token'] = end
            np['sent_num'] = sent_num
            return np

        else:
            before_anchor = original_np_by_idx[closest_before]
            before_anchor_spacy = spacy_docs[before_anchor['sent_num']][
                                  before_anchor['start_token']:before_anchor['end_token']]

            after_anchor = original_np_by_idx[closest_after]
            after_anchor_spacy = spacy_docs[after_anchor['sent_num']][
                                 after_anchor['start_token']:after_anchor['end_token']]

            matched_np = find_text_in_spacy_doc_using_span_matching(np['text'],
                                                                    closest_before_sent,
                                                                    closest_after_sent,
                                                                    before_anchor_spacy,
                                                                    after_anchor_spacy,
                                                                    )

            if matched_np is not None:
                start, end, sent_num = matched_np
                np['start_token'] = start
                np['end_token'] = end
                np['sent_num'] = sent_num
                return np

            # if nothing was matched there was manually added nps
            # but this cases was added before implementing the find_text_in_spacy_doc_using_span_matching
            # function. So maybe this fallback can be removed
            return final_np_matching_fallback(np, closest_after_sent, closest_before_sent)


    elif closest_before is not None and closest_after is None:
        closest_before_np = original_np_by_idx[closest_before]
        closest_before_sent = closest_before_np['sent_num']
        closest_after_sent = closest_before_np['sent_num']

        before_anchor_spacy = spacy_docs[closest_before_sent][
                              closest_before_np['start_token']:closest_before_np['end_token']]
        after_anchor_spacy = None
        matched_np = find_text_in_spacy_doc_using_span_matching(np['text'],
                                                                closest_before_sent,
                                                                closest_after_sent,
                                                                before_anchor_spacy,
                                                                after_anchor_spacy,
                                                                )

        if matched_np is not None:
            start, end, sent_num = matched_np
            np['start_token'] = start
            np['end_token'] = end
            np['sent_num'] = sent_num
            return np
    elif closest_after is not None and closest_before is None:
        # TODO matching using closest_after
        pass
    else:
        raise Exception("Too complex - no sent before and after was found - might be a bug")


def phrase2pattern(text):
    text = re.compile(r'([א-ת]+)_(הוא|היא|הן|הם)').sub(r'\1 _\2', text)
    text = re.sub(r'__(?=[א-ת])', '_ _', text)
    text = re.sub(r'([א-ת]+)_של_', r'\1 _של_', text)
    # Use the sub method to add a space after the Hebrew pronoun
    raw_toks = model.predict([text], tokenizer)
    raw_toks_without_special = raw_toks[0][1:-1]
    toks = list(chain.from_iterable(raw_toks_without_special))  # flatten the list
    pattern = [{"ORTH": tok} for tok in toks]
    return pattern


def find_text_in_spacy_doc_using_span_matching(text: str,
                                               sent_num_before: int,
                                               sent_num_after: int,
                                               span_before: spacy.tokens.Span = None,
                                               span_after: spacy.tokens.Span = None):
    # Create a Matcher instance
    matcher = Matcher(span_before.vocab)
    pattern = phrase2pattern(text)
    # Add the pattern to the matcher
    matcher.add("TEXT_PATTERN", [pattern])

    # Get the doc to search in relevant span
    doc_to_search_before = span_before.doc[span_before.end:] if span_before else None
    doc_to_search_after = span_after.doc[:span_after.start] if span_after else None

    # Apply the matcher to the doc
    matches_before = matcher(doc_to_search_before) if doc_to_search_before else []
    matches_after = matcher(doc_to_search_after) if doc_to_search_after else []

    # verify we have only one match  - if not it is hard to know what was the original by script but it is a rare case
    if len(matches_after + matches_before) != 1:
        return None
    # If a match is found
    if matches_before:
        # Get the match id, start, and end
        match_id, start, end = matches_before[0]
        start += span_before.end
        end += span_before.end
        # Get the sentence containing the matched span
        sent = sent_num_before

        return start, end, sent
    elif matches_after:
        match_id, start, end = matches_after[0]

        # Get the sentence containing the matched span
        sent = sent_num_after

        return start, end, sent

    else:
        return None


# TODO rename to a better finction name
def find_text_in_spacy_doc_single_sentence(text: str,
                                           span: spacy.tokens.Span,
                                           ):
    # Create a Matcher instance
    matcher = Matcher(span.vocab)
    # Define a pattern to match the text
    pattern = phrase2pattern(text)
    # Add the pattern to the matcher
    matcher.add("TEXT_PATTERN", [pattern])

    # Get the doc to search in relevant span

    # Apply the matcher to the doc
    matches = matcher(span) if span else []

    # verify we have only one match
    if len(matches) == 0:
        return None

    # If a match is found
    if matches:
        # Get the match id, start, and end
        match_id, start, end = matches[0]  # TODO would take the first appearance
        start += span.start
        end += span.start
        # Get the sentence containing the matched span

        return start, end

    else:
        return None


def spans_are_from_same_doc(span_before, span_after):
    return span_before.doc == span_after.doc


def extract_nps_token_locations(final_mentions_nps, original_np_by_idx, spacy_docs):
    res_nps_for_hit_id = []
    for np in final_mentions_nps:
        np: dict
        if all(k in np for k in ['start_token', 'end_token', 'sent_num']):
            enriched_np = np
        else:
            try:
                if (np['start_index'], np['end_index']) in original_np_by_idx:
                    original_np = original_np_by_idx[(np['start_index'], np['end_index'])]
                    enriched_np = copy.deepcopy(np)
                    enriched_np['start_token'] = original_np['start_token']
                    enriched_np['end_token'] = original_np['end_token']
                    enriched_np['sent_num'] = original_np['sent_num']
                else:
                    anchor = find_np_anchor(np, original_np_by_idx)
                    if anchor:
                        enriched_np = enrich_np_by_anchor(np, anchor, spacy_docs)
                    else:
                        enriched_np = find_np_in_docs(np, original_np_by_idx, spacy_docs)
            except Exception as e:
                if np['text'] == 'ע"ר' and np['start_index'] == 22 and np['id'] == 2:
                    enriched_np = {'end_index': 25, 'end_token': 4, 'id': 2, 'sent_num': 0, 'start_index': 21,
                                   'start_token': 3, 'text': 'וע"ר'}
                elif np['text'] == 'הם' and np['start_index'] == 1190 and np['id'] == 95:
                    enriched_np = {'text': 'מיהם', 'start_index': 1188, 'end_index': 1192, 'start_token': 4,
                                   'end_token': 5,
                                   'sent_num': 12, 'id': 95}
                elif np['text'] == 'מחר' and np['start_index'] == 63 and np['id'] == 5:
                    enriched_np = {'text': 'למחר', 'start_index': 62, 'end_index': 66, 'start_token': 14,
                                   'end_token': 15,
                                   'sent_num': 0, 'id': 5}
                else:
                    raise e
        if text_is_not_aligned(spacy_docs, enriched_np):
            log_unexpected_text_alignment_issue(enriched_np, spacy_docs)
        res_nps_for_hit_id.append(enriched_np)

    res_nps_for_hit_id.sort(key=lambda x: x['id'])
    return res_nps_for_hit_id


def log_unexpected_text_alignment_issue(enriched_np, spacy_docs):
    print(f"np {enriched_np}")
    print(
        f'extracted np: {spacy_docs[enriched_np["sent_num"]][enriched_np["start_token"]:enriched_np["end_token"]].text}')
    print(f"doc {spacy_docs[enriched_np['sent_num']]}")


def get_non_idiomatic_nps(consolidated_doc):
    valid_nps = set()
    for cluster in consolidated_doc['clusters']:
        if 'idiomatic' in cluster['source']:
            continue
        else:
            for m in cluster['members']:
                valid_nps.add(m)
    return valid_nps


def find_nested_mention_in_np(np, np_by_idx):
    for target_np in np_by_idx.values():
        if np['start_index'] < target_np['start_index'] and np['end_index'] > target_np['end_index']:
            return target_np

    return None


def extract_nps_token_locations_to_consolidate_data(final_mentions_nps, consolidated_doc, spacy_docs):
    res_nps_for_hit_id = []
    non_idiomatic = get_non_idiomatic_nps(consolidated_doc)
    consolidated_nps_by_idx = {(np['start_index'], np['end_index']): np for np in consolidated_doc['nps'] if
                               np['id'] in non_idiomatic}
    final_mentions_nps_by_idx = {(np['start_index'], np['end_index']): np for np in final_mentions_nps}
    for np_idx, np in consolidated_nps_by_idx.items():
        try:
            if np_idx in final_mentions_nps_by_idx:
                enriched_np = copy.deepcopy(final_mentions_nps_by_idx[np_idx])
            elif all(field in np for field in ['start_token', 'end_token', 'sent_num']):
                enriched_np = np
            else:
                anchor = find_np_anchor(np, final_mentions_nps_by_idx)
                if anchor:
                    enriched_np = enrich_np_by_anchor(np, anchor, spacy_docs)
                elif find_nested_mention_in_np(np, final_mentions_nps_by_idx):
                    # TODO - might be dangerous if the span marked is from differnt sentences
                    enriched_np = find_np_in_sent(final_mentions_nps_by_idx, np, spacy_docs)
                else:
                    enriched_np = find_np_in_docs(np, final_mentions_nps_by_idx, spacy_docs)
        except Exception as e:
            if np['text'] == 'ע"ר' and np['start_index'] == 22 and np['id'] == 2:
                enriched_np = {'end_index': 25, 'end_token': 4, 'id': 2, 'sent_num': 0, 'start_index': 21,
                               'start_token': 3, 'text': 'וע"ר'}
            elif np['text'] == 'הם' and np['start_index'] == 1190 and np['id'] == 95:
                enriched_np = {'text': 'מיהם', 'start_index': 1188, 'end_index': 1192, 'start_token': 4,
                               'end_token': 5,
                               'sent_num': 12, 'id': 95}
            elif np['text'] == 'מחר' and np['start_index'] == 63 and np['id'] == 5:
                enriched_np = {'text': 'למחר', 'start_index': 62, 'end_index': 66, 'start_token': 14,
                               'end_token': 15,
                               'sent_num': 0, 'id': 5}
            elif np['text'] == 'מחרתיים' and np['start_index'] == 131 and np['id'] == 8:
                enriched_np = {'text': 'מחרתיים', 'start_index': 124, 'end_index': 131, 'id': 5, 'start_token': 0,
                               'end_token': 1, 'sent_num': 1}
                # מחרתיים זה אזכור שמופיע פעמיים
            else:
                raise e

        if text_is_not_aligned(spacy_docs, enriched_np):
            log_unexpected_text_alignment_issue(enriched_np, spacy_docs)
        else:
            res_nps_for_hit_id.append(enriched_np)

    res_nps_for_hit_id.sort(key=lambda x: x['id'])

    return res_nps_for_hit_id


def find_np_in_sent(final_mentions_nps_by_idx, np, spacy_docs):
    sent_anchor = find_nested_mention_in_np(np, final_mentions_nps_by_idx)['sent_num']
    source_sent = spacy_docs[sent_anchor]
    sent_res = find_text_in_spacy_doc_single_sentence(np['text'],
                                                      source_sent[0:-1])
    if sent_res is not None:
        start, end = sent_res
        np['start_token'] = start
        np['end_token'] = end
        np['sent_num'] = sent_anchor
        return np
    else:
        return None


def text_is_not_aligned(spacy_docs, enriched_np):
    try:
        sent = spacy_docs[enriched_np['sent_num']]
    except TypeError as e:
        print(e)
    span = sent[enriched_np["start_token"]:enriched_np["end_token"]]
    return span.text != enriched_np["text"]
