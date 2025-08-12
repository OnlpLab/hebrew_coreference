import ast
import sqlite3 as lite
import os
import argparse
from collections import Counter


def get_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-db_dir", "--database_dir", type=str,
                           help="name of the directory that contains the databse")
    argparser.add_argument("-db", "--data_base", type=str,
                           help="name of the database to which the consolidation data will be stored")
    argparser.add_argument("-sa", "--specific_annotators", nargs='+', type=str, required=False,
                           help="a list of specific annotators you wish to check seperated by space")
    args = argparser.parse_args()
    return args


def get_new_cluster_source(c1, c2, nc):
    if c1["members"][0] == c2["members"][0] and nc["members"][0] == c1["members"][0] and c1["source"] == c2["source"]:
        new_source = c1["source"]
    else:
        new_source = "new"
    return new_source


def contains_better_candidates(ids, i, clusters1,
                               clusters2):  # checks if an np in the complement of two intersecting clusters belongs to an even longer intersection
    for id in ids:
        c1 = [c for c in clusters1 if id in c["members"]][0]
        c2 = [c for c in clusters2 if id in c["members"]][0]
        intersection = list(set(c1["members"]) & set(c2["members"]))
        if len(intersection) > i:
            return True
    return False


def filter_sublists(data):
    """
    Filter out sublists in the 'members' field of the input data.

    Parameters:
    - data (list): A list of dictionaries, each containing a 'members' field.

    Returns:
    list: A filtered list where no 'members' list is a sublist of another.
    """

    filtered_data = []

    def is_sublist(list1, list2):
        return all(x in list2 for x in list1)

    for item in data:
        current_members = item['members']
        is_unique = True

        for existing_item in filtered_data:
            existing_members = existing_item['members']

            if is_sublist(current_members, existing_members) or is_sublist(existing_members, current_members):
                is_unique = False
                break

        if is_unique:
            filtered_data.append(item)

    return filtered_data


# this funcltion builds new clusters that are the longest intersections between clusters from coref results from 2 annotators
# whatever is not included in these new clusters is considered to be "disagreement items" and has to be reconsidered by the cosolidator

def has_consensus(clusters, minimum_agreement):
    cluster_counts = {}
    max_count = 0
    for cluster in clusters:
        if cluster['source'] == 'idiomatic':
            cluster['selected_preposition'] = 'idiomatic'
        if cluster['source'] == 'new':
            cluster['selected_preposition'] = 'of'
    for cluster in clusters:
        # Sort and convert members to a tuple (to make it hashable)
        members = tuple(sorted(cluster['members']))

        # Create a key using members and selected_preposition (if applicable)
        # Count the occurrence of each unique key
        cluster_counts[members] = cluster_counts.get(members, 0) + 1

        # Keep track of the maximum count found so far
        max_count = max(max_count, cluster_counts[members])

    # Check if the most common cluster occurrence is greater than 67 of the total clusters
    return max_count / len(clusters) > minimum_agreement


def get_intersection_unanimous(clusters, nps):
    new_clusters = []  # unified clusters
    covered_nps = []  # nps that have already been iterated over
    disagreement_nps = []  # disagreement items

    for np in nps:
        if np['id'] in covered_nps:  # to avoid considering the same np twice
            continue

        # get the clusters to which each annotator assigned the current np
        clusters_contains_np = [c for c_list in clusters for c in c_list if np['id'] in c["members"]]

        # get the intersection of all found clusters
        intersection = set(clusters_contains_np[0]["members"])
        for cluster in clusters_contains_np[1:]:
            intersection = intersection.intersection(cluster["members"])
        intersection = list(intersection)

        if len(intersection) > 1 or has_consensus(clusters_contains_np, 0.67):
            # create new cluster
            nc = {"members": intersection, "source": [cluster["source"] for cluster in clusters_contains_np]}
            # set source
            new_clusters.append(nc)
            covered_nps += intersection
        else:
            disagreement_nps += intersection
            covered_nps += intersection

    disagreement_nps = list(dict.fromkeys(disagreement_nps))  # dedupe
    new_clusters = filter_sublists(new_clusters)
    for np in nps:
        # check that no np belongs to multiple clusters
        if len([c for c in new_clusters if np["id"] in c["members"]]) > 1:
            raise Exception("Multiple clusters for the same np")
        # check that nps that are not in clusters are in disagreement_items
        elif len([c for c in new_clusters if np["id"] in c["members"]]) < 1 and not np["id"] in disagreement_nps:
            disagreement_nps.append(np["id"])

    x = 0
    for nc in new_clusters:
        # set id
        nc['id'] = x
        x += 1
        # set selected_preposition
        nc["selected_preposition"] = "of"

    return new_clusters, disagreement_nps


def main_sets(clusters_contains_element):
    value_dict = dict()
    num_of_annotators = len(clusters_contains_element)
    for s in clusters_contains_element:
        for val in s:
            if val in value_dict:
                value_dict[val] += 1
            else:
                value_dict[val] = 1
    result = {k for k, v in value_dict.items() if v > num_of_annotators / 2}
    return result


def get_intersection_majority(clusters, nps):
    new_clusters = []  # unified clusters
    covered_nps = set()  # nps that have already been iterated over
    disagreement_nps = []  # disagreement items
    for np in nps:
        if np['id'] in covered_nps:  # to avoid considering the same np twice
            continue

        # get the clusters to which each annotator assigned the current np
        clusters_contains_np = [c for c_list in clusters for c in c_list if np['id'] in c["members"]]

        # get the intersection of all found clusters
        cluster_members = [set(c['members']) for c in clusters_contains_np]
        intersection_majority = list(main_sets(cluster_members))
        in_other_clusters = any([i in covered_nps for i in intersection_majority])
        if in_other_clusters:
            disagreement_nps += [np['id']]
        elif len(intersection_majority) == 1:
            sources_list = [c['source'] for c in clusters_contains_np]
            sources_list_unique = [c[0] if type(c) == list else c for c in sources_list]
            sources = Counter(sources_list_unique)
            
            source = sources.most_common(1)[0][0]
            nc = {"members": intersection_majority, "source": [source]}
            # set source
            new_clusters.append(nc)

        elif len(intersection_majority) > 1:
            source = "new"
            nc = {"members": intersection_majority, "source": [source] * len(intersection_majority)}
            # set source
            new_clusters.append(nc)
        else:
            disagreement_nps += intersection_majority
        covered_nps.update(intersection_majority)

    disagreement_nps = list(dict.fromkeys(disagreement_nps))  # dedupe
    new_clusters = filter_sublists(new_clusters)
    for np in nps:
        # check that no np belongs to multiple clusters
        if len([c for c in new_clusters if np["id"] in c["members"]]) > 1:
            raise Exception("Multiple clusters for the same np")
        # check that nps that are not in clusters are in disagreement_items
        elif len([c for c in new_clusters if np["id"] in c["members"]]) < 1 and not np["id"] in disagreement_nps:
            disagreement_nps.append(np["id"])

    x = 0
    for nc in new_clusters:
        # set id
        nc['id'] = x
        x += 1
        # set selected_preposition
        nc["selected_preposition"] = "of"

    return new_clusters, disagreement_nps


def main():
    args = get_args()

    db_dir = args.database_dir
    db = args.data_base
    annotators_to_check = args.specific_annotators
    con = lite.connect(os.path.join(db_dir, db))
    cur = con.cursor()

    create_table(annotators_to_check, con, cur, get_intersection_majority, "coref_data_for_consolidation")
    create_table(annotators_to_check, con, cur, get_intersection_unanimous, "coref_data_for_consolidation_unanimous")


def create_table(annotators_to_check, con, cur, consensus_type, consolidation_table_name):
    intersection_dictionary = {}
    dbtable = 'tne_coref_data'
    # get the ids of hits completed by 2 annotators
    if annotators_to_check:
        cur.execute(
            "select group_concat(hit_id) FROM (select hit_id, count(annotator_id) as c from  " + dbtable + f" WHERE annotator_id IN {tuple(annotators_to_check)} group by hit_id) as t where c > 1")
    else:
        cur.execute(
            "select group_concat(hit_id) FROM (select hit_id, count(annotator_id) as c from  " + dbtable + " group by hit_id) as t where c > 1")
    hit_ids = cur.fetchone()[0].split(',')
    for id in hit_ids:
        # get coref results from annotators
        if annotators_to_check:
            cur.execute(
                f"SELECT annotator_id, clusters FROM tne_coref_data WHERE hit_id = ? AND annotator_id IN {tuple(annotators_to_check)}",
                (id,))
        else:
            cur.execute(f"SELECT annotator_id, clusters FROM {dbtable} where hit_id = ? ", (id,))
        fetched_result = cur.fetchall()
        # TODO -- START -- could be removed after finished reannoatation docs with hit_id <59
        clusters_from_annotators = [ast.literal_eval(c[1]) for c in fetched_result if
                                    c[0] in {"Hadar", "Itay", "Tal", "Ariela", "Yechiel", "Hadas", "Hinoy"}]
        if len(clusters_from_annotators) == 0:
            continue
        # TODO -- FINISH -- could be removed after finished reannoatation docs with hit_id <59
        cur.execute("SELECT nps from final_mention_data where hit_id = " + id)
        nps_literal = cur.fetchone()[0]
        nps = ast.literal_eval(nps_literal)
        # get unified clusters and list of disagreement items for the HIT in question
        intersection_dictionary[id] = (consensus_type(clusters_from_annotators, nps))
    cur.execute("DROP TABLE IF EXISTS " + consolidation_table_name)
    cur.execute(
        "CREATE TABLE IF NOT EXISTS " + consolidation_table_name + "(id INTEGER PRIMARY KEY AUTOINCREMENT, hit_id INTEGER, new_clusters TEXT, undone_nps TEXT)")
    for k in intersection_dictionary:
        v = intersection_dictionary[k]

        cur.execute("INSERT INTO " + consolidation_table_name + " (hit_id, new_clusters, undone_nps) VALUES (?,?,?)",
                    (int(k), str(v[0]), str(v[1])))
        con.commit()
        print("Record inserted successfully into python_users table")


if __name__ == '__main__':
    main()
