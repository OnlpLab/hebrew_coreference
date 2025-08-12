import os
import json

folder_path = "../corpus/coref_docs_2_tag/tne_conll/"

res = []
# Loop through all files in the folder
total_num_of_sent = 0
total_num_of_mentions = 0
file_list = sorted(os.listdir(folder_path), key=lambda c: int(c.split("_")[0]))
for filename in file_list:
    # Check if the file is a JSON file
    num = int(filename.split("_")[0])
    if filename.endswith('.tne'):
        # Open the file and load the JSON data
        with open(os.path.join(folder_path, filename), 'r') as file:
            json_data = json.load(file)
            file_parts = filename.strip(".tne").split("_")
            num_of_mentions = len(json_data[0]['done_nps'])

            # if len(file_parts) == 5:
            #     print(f"{file_parts[0]}. Doc id: {file_parts[4]} ,Number of Sentences: {file_parts[1]}, Number of mentions: {num_of_mentions}")
            # else:
            #     print(f"{file_parts[0]}. Doc id: {file_parts[4]}_{file_parts[5]} ,Number of Sentences: {file_parts[1]}, Number of mentions: {num_of_mentions}")

            total_num_of_sent += int(file_parts[1])
            total_num_of_mentions += num_of_mentions
print(f"Total num of sent: {total_num_of_sent}")
print(f"Total num of mentions: {total_num_of_mentions}")


