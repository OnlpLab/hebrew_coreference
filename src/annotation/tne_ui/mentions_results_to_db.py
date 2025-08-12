import json
import os
import sqlite3 as lite
import argparse


# coref results
def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-in", "--input_file", type=str, help="name of the file with coref annotation results")
    argparser.add_argument("-db_dir", "--database_dir", type=str,
                           help="name of the directory that contains the databse")
    argparser.add_argument("-db", "--data_base", type=str,
                           help="name of the database to which the coref annoation data will be stored")
    argparser.add_argument("-a", "--annotators", type=str, default=None,
                           help="name of the file with coref annotator ids for each annotation in the input file; the ids are listed 1 per line in the same order as the annotations themselves.")

    args = argparser.parse_args()

    in_file = args.input_file
    db_dir = args.database_dir
    db = args.data_base
    annotators = args.annotators

    con = lite.connect(os.path.join(db_dir, db))
    print("Creating database/table...")
    with con:
        cur = con.cursor()
        # DROP TABLE
        cur.execute("DROP TABLE IF EXISTS tne_mention_data")

        # CREATE TABLE
        cur.execute(
            "CREATE TABLE IF NOT EXISTS tne_mention_data(id INTEGER PRIMARY KEY AUTOINCREMENT, hit_id INTEGER, annotation_id INTEGER, clusters TEXT, nps TEXT, states TEXT, annotator_id TEXT)")
    try:
        with open(annotators, encoding="utf8") as a:
            annotator_ids = [idx.strip() for idx in a.readlines()]
    except:
        annotator_ids = []

    with open(in_file, encoding="utf8") as f:
        data = f.readlines()

        for ind, line in enumerate(data):
            doc = json.loads(line.strip())
            clusters = doc["clusters"]
            states = doc["states"]
            nps = doc["nps"]
            hit_id = doc["hit_id"]
            cur.execute('select * from tne_mention_data where hit_id =' + str(hit_id))
            annotation_id = len(cur.fetchall())
            try:
                annotator_id = annotator_ids[ind]
            except:
                annotator_id = None
            cur.execute(
                "INSERT INTO tne_mention_data(hit_id, annotation_id, clusters, nps, states, annotator_id) VALUES (?,?,?,?,?,?)",
                (hit_id, annotation_id, str(clusters), str(nps), json.dumps(states), annotator_id))
            con.commit()
            print("Record inserted successfully into python_users table")
            hit_id += 1
            print()
            print("HIT " + str(hit_id))

    con.close()
    print("Connection is closed")


if __name__ == '__main__':
    main()
