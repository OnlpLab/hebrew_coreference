import argparse
import sqlite3
import json

import sys


def read_consolidation(data_db):
    rows = query_db(data_db)

    # Dictionary to store the filtered nps data
    filtered_nps_dict = {}

    # Iterate over the rows and filter the nps data
    for row in rows:
        hit_id, nps_literal, clusters_literal = row
        nps = eval(nps_literal)
        clusters = eval(clusters_literal)
        valid_nps = set([cluster['members'][0] for cluster in clusters if cluster['source'] == 'mention' or cluster['source'][0] == 'mention'])
        filtered_nps = [np for np in nps if np['id'] in valid_nps]

        # Sort the filtered_nps based on start_index and end_index
        filtered_nps.sort(key=lambda x: (x['start_index'], x['end_index']))

        # Reassign the id values in an enumerated order
        for i, np in enumerate(filtered_nps):
            np['id'] = i

        filtered_nps_dict[hit_id] = filtered_nps
    is_debug = sys.gettrace() is not None
    if is_debug:
        # Print the filtered nps data
        for hit_id, filtered_nps in filtered_nps_dict.items():
            print(f"Hit ID: {hit_id}")
            for np in filtered_nps:
                print(f"Text: {np['text']}, Start Index: {np['start_index']}, End Index: {np['end_index']}")
            print()
    return filtered_nps_dict


def query_db(data_db):
    connection = sqlite3.connect(data_db)
    cursor = connection.cursor()
    # A SQL query to retrieve rows that match the conditions
    query = """
    SELECT hit_id, nps, clusters
    FROM tne_mention_data
    WHERE annotator_id =  'Consolidation' 
    """
    # Execute the query and fetch all matching rows
    cursor.execute(query)
    rows = cursor.fetchall()
    # Close the database connection
    connection.close()

    return rows


def create_table(data_db, filtered_nps_dict):
    # Connect to the SQLite database
    connection = sqlite3.connect(data_db)
    cursor = connection.cursor()

    # Read the tne_original_data table
    query = "SELECT * FROM tne_original_data"
    cursor.execute(query)
    rows = cursor.fetchall()

    # Create the final_mention_data table (delete if it already exists)
    cursor.execute("DROP TABLE IF EXISTS final_mention_data")
    cursor.execute("""
        CREATE TABLE final_mention_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hit_id INTEGER,
            text TEXT,
            nps TEXT,
            done_nps TEXT,
            pronouns TEXT,
            raw_text TEXT,
            text_id INTEGER,
            data_length INTEGER,
            source_file TEXT,
            url TEXT
        )
    """)

    # Iterate over the rows and process the data
    for row in rows:
        # Extract the original data
        (
            idx,
            hit_id,
            text,
            nps,
            done_nps,
            pronouns,
            raw_text,
            text_id,
            data_length,
            source_file,
            url
        ) = row

        # Process the new nps data (assuming you have the filtered_nps_dict from previous code)
        if hit_id in filtered_nps_dict:
            print(f"Uploading to final_mention_data document {hit_id} ")
            new_nps = filtered_nps_dict[hit_id]
            new_done_nps = {str(i): False for i in range(len(new_nps))}

            # Convert the data to JSON strings
            new_nps_json = json.dumps(new_nps, ensure_ascii=False)
            new_done_nps_json = json.dumps(new_done_nps, ensure_ascii=False)

            # Insert the modified data into the final_mention_data table
            cursor.execute("""
                INSERT INTO final_mention_data (
                    hit_id,
                    text,
                    nps,
                    done_nps,
                    pronouns,
                    raw_text,
                    text_id,
                    data_length,
                    source_file,
                    url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hit_id,
                text,
                new_nps_json,
                new_done_nps_json,
                pronouns,
                raw_text,
                text_id,
                data_length,
                source_file,
                url
            ))

    # Commit the changes and close the database connection
    connection.commit()
    connection.close()


def main():
    parser = argparse.ArgumentParser(description='Process data from SQLite database.')
    parser.add_argument('db_folder', help='Path to the folder containing the SQLite database')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    final_mentions = read_consolidation(args.db_folder)
    create_table(args.db_folder, final_mentions)


if __name__ == '__main__':
    main()
