from __future__ import print_function
import datetime
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from notion_client import Client
import re

# .env Datei laden
load_dotenv()
calendar_id = os.getenv("GOOGLE_KALENDER_ID")
NOTION_PRAC_LIST = os.getenv("NOTION_PRAC_LIST")
NOTION_ENEMY_LIST = os.getenv("NOTION_ENEMY_LIST")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")

# Scopes definieren (Rechte für den Zugriff)
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
notion = Client(auth=NOTION_API_KEY)

def get_google_credentials():
    # Google Service-Konto-Authentifizierung
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(GOOGLE_SERVICE_ACCOUNT_KEY), scopes=SCOPES)
    return credentials

def extract_event_data(event):
    start = event['start'].get('dateTime', event['start'].get('date'))
    summary = event.get('summary', '')

    pattern = r'^vs\. (.+?) \(Map: (.+?)\)$'
    match = re.match(pattern, summary)

    if match:
        name = match.group(1).strip()
        map_info = match.group(2).strip()
    else:
        name = summary.strip()
        map_info = None

    event_data = {
        'Datum': start,
        'Name': name,
        'Map': map_info
    }

    return event_data

def page_exist_in_enemy_list(name):
    query = notion.databases.query(
        **{
            "database_id": NOTION_ENEMY_LIST,
            "filter": {
                "property": "Name",
                "title": {
                    "equals": name
                }
            }
        }
    )
    return len(query['results']) > 0

def create_page_in_enemy_list(name, date):
    new_page = {
        "parent": {"database_id": NOTION_ENEMY_LIST},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": name
                        }
                    }
                ]
            }
        }
    }
    notion.pages.create(**new_page)

def create_page_in_prac_list(date, map_name, gegner_id):
    new_page = {
        "parent": {"database_id": NOTION_PRAC_LIST},
        "properties": {
            "Map": {
                "title": [
                    {
                        "text": {
                            "content": map_name
                        }
                    }
                ]
            },
            "Wann gegen gespielt": {
                "date": {
                    "start": date
                }
            },
            "Prac Gegner": {
                "relation": [
                    {"id": gegner_id}
                ]
            }
        }
    }
    notion.pages.create(**new_page)

def page_exist_prac_list(date, map_name, related_task_id):
    query = notion.databases.query(
        **{
            "database_id": NOTION_PRAC_LIST,
            "filter": {
                "and": [
                    {
                        "property": "Wann gegen gespielt",
                        "date": {
                            "equals": date
                        }
                    },
                    {
                        "property": "Map",
                        "title": {
                            "equals": map_name
                        }
                    },
                    {
                        "property": "Prac Gegner",
                        "relation": {
                            "contains": related_task_id
                        }
                    }
                ]
            }
        }
    )
    return len(query['results']) > 0

def find_entry_id_by_name(name):
    query = notion.databases.query(
        **{
            "database_id": NOTION_ENEMY_LIST,
            "filter": {
                "property": "Name",
                "title": {
                    "equals": name
                }
            }
        }
    )

    results = query.get('results', [])
    if results:
        return results[0]['id']
    else:
        return None

def main():
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.datetime.utcnow()
    time_min = (now - datetime.timedelta(days=21)).isoformat() + 'Z'
    time_max = now.isoformat() + 'Z'

    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min,
                                          timeMax=time_max, maxResults=10, 
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    else:
        extracted_data = []
        for event in events:
            event_data = extract_event_data(event)
            extracted_data.append(event_data)
            date = event_data.get('Datum')
            name = event_data.get('Name')
            map_name = event_data.get('Map')
            if not page_exist_in_enemy_list(name):
                create_page_in_enemy_list(name, date)
                create_page_in_prac_list(date, map_name, find_entry_id_by_name(name))

            if not page_exist_prac_list(date, map_name, find_entry_id_by_name(name)):
                create_page_in_prac_list(date, map_name, find_entry_id_by_name(name))

        print("successfully posted")

if __name__ == '__main__':
    main()
