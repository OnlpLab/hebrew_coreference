import json
import os
import sqlite3 as lite
import argparse


def main():
    parse = argparse.ArgumentParser("")
    parse.add_argument("-in", "--input_dir", type=str, help="input directory name")
    parse.add_argument("-out", "--output_dir", type=str, help="output directory that contains the databse")
    parse.add_argument("-db", "--data_base", type=str, help="name of the database in the output directory")
    args = parse.parse_args()

    in_d = args.input_dir
    out_d = args.output_dir
    db = args.data_base

    con = lite.connect(os.path.join(out_d, db))
    print("Creating database/table...")
    with con:
        cur = con.cursor()
        # DROP TABLE
        cur.execute("DROP TABLE IF EXISTS tne_original_data")

        # CREATE TABLES
        cur.execute(
            "CREATE TABLE IF NOT EXISTS tne_original_data(id INTEGER PRIMARY KEY AUTOINCREMENT, hit_id INTEGER, text TEXT, nps TEXT, done_nps TEXT, pronouns TEXT, raw_text TEXT, text_id INTEGER,  data_length INTEGER, source_file TEXT, url TEXT)")

    print("Database/table created")
    hit_id = 0

    directory = in_d
    sorted_files = sorted(os.listdir(directory), key=lambda x: int(x.split("_")[0]))
    for filename in sorted_files:
        raw_data = open(directory + '/' + filename, encoding="utf8")
        raw = json.load(raw_data)
        for text in raw:
            nps = text["nps"]
            done_nps = text["done_nps"]
            pronouns = text["pronouns"]
            tx = text["tx"]
            source_file = text["source_file"]
            text_id = text["text_id"]
            url = text["url"]

            cur.execute(
                "INSERT INTO tne_original_data (hit_id, text, nps, done_nps, pronouns, raw_text, text_id,  data_length, source_file, url) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (hit_id, str(tx), str(nps), str(done_nps).replace('False', 'false'), str(pronouns), tx['raw_text'],
                 text_id, len(nps), source_file, url))
            con.commit()
            print("Record inserted successfully into python_users table")
            hit_id += 1
            print()
            print("HIT " + str(hit_id))

    con.close()
    print("Connection is closed")


if __name__ == "__main__":
    main()
