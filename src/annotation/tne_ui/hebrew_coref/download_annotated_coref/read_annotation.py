import os
import base64
import json
import pytz

from collections import defaultdict
import email
import re
from datetime import datetime

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from tqdm import tqdm

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']


def collect_json_files_and_folders(folder_path):
    json_files = []
    folders = []
    for dirpath, dirnames, filenames in os.walk(folder_path):
        dirnames.sort()
        filenames.sort()

        for filename in filenames:
            if filename.endswith('.json'):
                json_files.append(os.path.join(dirpath, filename))
                folders.append(os.path.basename(dirpath))
    return json_files, folders


def merge_json_files_and_folders(main_folder_path, phase):
    json_files, folders = collect_json_files_and_folders(f"../{phase}_annotation_data")
    output_path = os.path.join(main_folder_path, 'output.jsonl')
    folders_path = os.path.join(main_folder_path, 'annotators.txt')
    with open(output_path, 'w') as outfile, open(folders_path, 'w') as foldersfile:
        for i, json_file in enumerate(json_files):
            with open(json_file, encoding="utf-8") as infile:
                json_data = json.load(infile)
                outfile.write(json.dumps(json_data, ensure_ascii=False) + '\n')
                foldersfile.write(folders[i].replace(" ", "_") + '\n')


def get_annotator(text):
    annotator_name = re.search(r'From: (.*)$', text, re.MULTILINE).group(1).strip()
    return annotator_name


def get_annotation(text):
    m = re.search(r'Annotation Results:(.*)$', text, re.MULTILINE | re.DOTALL)
    if m:
        annotation_results = m.group(1).strip()
        # Extract the JSON string from the extracted text
        json_str = re.search(r'{.*}', annotation_results, re.DOTALL).group()
        # Load the JSON string using the json library
        json_obj = json.loads(json_str.replace("\n", " ").replace("\r", ""))
        return json_obj


def parse_msg(decoded_msg):
    # Parse the email message
    email_message = email.message_from_string(decoded_msg)

    # Extract the subject field
    subject = email_message['Subject']
    date = datetime.strptime(email_message['Date'], '%a, %d %b %Y %H:%M:%S %z')

    for part in email_message.walk():
        if part.get_content_type() == 'text/plain':
            text = part.get_payload(decode=True).decode()
            annotator = get_annotator(text)
            return {"annotator": annotator, 'subject': subject, 'date': date}


def get_creds():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'creds')
    token_path = os.path.join(creds_folder_path, 'token.json')
    # your creds file here. Please create json file as here https://cloud.google.com/docs/authentication/getting-started
    creds_file = 'client_secret_615794715096-h7oo6tu5n4qmjf7r8jafd4lsj584lj8v.apps.googleusercontent.com.json'
    creds_path = os.path.join(creds_folder_path, creds_file)
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds


def check_last_emails():
    creds = get_creds()
    messages_info = []

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', cache_discovery=True, credentials=creds)
        messages = get_messages(service, 20)
        if not messages:
            print('No new messages.')
            return messages_info
    except Exception as error:
        print(f'An error occurred: {error}')
        exit(1)

    for message in tqdm(messages):
        email_data_dict = get_msg_details(message, service)
        if 'Subject' not in email_data_dict or email_data_dict['Subject'] != 'New Coref Annotation HIT':
            continue
        full_msg = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
        decoded_msg = base64.urlsafe_b64decode(full_msg['raw'].encode("utf-8")).decode("utf-8")
        msg = parse_msg(decoded_msg)
        date = msg['date']
        annotation_detail = eval(email_data_dict["attachment_text"])
        phase = annotation_detail["phase"]
        hit_id = annotation_detail["hit_id"]

        israel_date = date.astimezone(pytz.timezone('Asia/Tel_Aviv'))
        info = {'day': str(israel_date.date()),
                'hour': str(israel_date.time()),
                'annotator': msg['annotator'],
                'phase': phase,
                'doc_id': hit_id}
        messages_info.append(info)
    return messages_info


def get_messages(service, max_results):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread",
                                              maxResults=max_results).execute()
    messages = results.get('messages', [])
    return messages


def readEmails():
    creds = get_creds()
    cached_msg = get_cached_msg()

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', cache_discovery=True, credentials=creds)

        messages = get_messages(service, 10000)
        if not messages:
            print('No new messages.')
    except Exception as error:
        print(f'An error occurred: {error}')
        exit(1)

    message_from = defaultdict(list)
    messages_id = []
    for message in tqdm(messages):
        email_data_dict = get_msg_details(message, service)
        if 'Subject' not in email_data_dict or email_data_dict['Subject'] != 'New Coref Annotation HIT':
            continue
        if message['id'] in cached_msg:
            continue
        full_msg = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
        decoded_msg = base64.urlsafe_b64decode(full_msg['raw'].encode("utf-8")).decode("utf-8")
        msg = parse_msg(decoded_msg)

        msg["annotation"] = eval(email_data_dict["attachment_text"])
        messages_id.append(message['id'])
        msg['id'] = message['id']
        message_from[msg['annotator']].append(msg)
    with open('.cache/parsed_msg.txt', mode='a') as f:
        for idx in messages_id:
            f.write(f"{idx}\n")
    return message_from


def get_cached_msg():
    with open(".cache/parsed_msg.txt") as f:
        cached_msg = f.readlines()
    cached_msg = [m.strip() for m in cached_msg]
    return set(cached_msg)


def get_msg_details(message, service):
    msg = service.users().messages().get(userId='me', id=message['id']).execute()
    payload_headers = msg['payload']['headers']
    for d in payload_headers:
        msg[d['name']] = d['value']
    # Check if there are any parts in the message payload
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['filename']:
                # Extracting attachment data
                attachment = service.users().messages().attachments().get(
                    userId='me', messageId=message['id'], id=part['body']['attachmentId']
                ).execute()
                attachment_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                attachment = attachment_data.decode('utf-8', 'ignore')

                if attachment:
                    # Retrieve the text content
                    msg['attachment_text'] = attachment
    return msg


def main():
    messages = readEmails()
    for user, content in messages.items():
        if not os.path.exists(f'../coref_annotation_data/{user}'):
            os.mkdir(f'../coref_annotation_data/{user}')
        if not os.path.exists(f'../mention_annotation_data/{user}'):
            os.mkdir(f'../mention_annotation_data/{user}')
        for massage in content:
            if massage['annotation']['phase'] == 'coref':
                phase = "coref"
            else:
                phase = "mention"
            doc = massage['annotation']['hit_id']
            with open(f'../{phase}_annotation_data/{user}/{doc}.json', mode='w', encoding="utf-8") as f:
                f.write(json.dumps(massage['annotation'], indent=4, ensure_ascii=False))
    folder_path = os.path.dirname(os.path.abspath(__file__))
    coref_annotation_path = os.path.join(folder_path, "..", "..", "annotation_results", "coref")
    merge_json_files_and_folders(coref_annotation_path, "coref")
    mention_annotation_path = os.path.join(folder_path, "..", "..", "annotation_results", "mention")
    merge_json_files_and_folders(mention_annotation_path, "mention")


if __name__ == '__main__':
    print("Downloading data")
    main()
