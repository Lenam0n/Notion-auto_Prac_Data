from __future__ import print_function
import datetime
import os.path
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from notion_client import Client
import re
from dotenv import load_dotenv

load_dotenv()
calendar_id = os.getenv("GOOGLE_KALENDER_ID")
NOTION_PRAC_LIST = os.getenv("NOTION_PRAC_LIST")
NOTION_ENEMY_LIST = os.getenv("NOTION_ENEMY_LIST")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GOOGLE_TOKEN=os.getenv("GOOGLE_TOKEN")
GOOGLE_SERVICE_ACCOUNT_KEY= os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")

# Scopes definieren (Rechte für den Zugriff)
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
notion = Client(auth=NOTION_API_KEY)


def extract_event_data(event):
    # Datum extrahieren
    start = event['start'].get('dateTime', event['start'].get('date'))

    # Name des Eintrags und Map-Informationen extrahieren
    summary = event.get('summary', '')

    # Regex zum Extrahieren der gewünschten Teile
    pattern = r'^vs\. (.+?) \(Map: (.+?)\)$'
    match = re.match(pattern, summary)

    if match:
        name = match.group(1).strip()  # Der Teil vor "(Map: "
        map_info = match.group(2).strip()  # Der Teil nach "(Map: "
    else:
        # Falls die Regex nicht passt, setze den Namen als gesamten Summary-Text
        name = summary.strip()
        map_info = None

    # Daten in ein JSON-kompatibles Format bringen
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
        # Assuming the first match is the correct one
        return results[0]['id']
    else:
        return None

def google_auth():
    if not GOOGLE_TOKEN:
        raise ValueError("Google token not found in environment variables. +" , GOOGLE_TOKEN)

    # Token in ein Dictionary umwandeln
    token_info = json.loads(GOOGLE_TOKEN)

    # Anmeldedaten aus dem Dictionary laden
    creds = Credentials.from_service_account_info(token_info)

    # Prüfen, ob die Anmeldedaten gültig sind oder erneuert werden müssen
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise ValueError("Credentials are invalid and cannot be refreshed.")

def main():
    #creds = None
    # Token laden, falls vorhanden
    #if GOOGLE_TOKEN:
        #creds = Credentials.from_authorized_user_info(GOOGLE_TOKEN, SCOPES)
        #creds = Credentials.from_service_account_info(json.loads(GOOGLE_SERVICE_ACCOUNT_KEY), scopes=SCOPES)
        
    # Neue Authentifizierung, falls nötig
    #if not creds or not creds.valid:
       # if creds and creds.expired and creds.refresh_token:
        #    creds.refresh(Request())
       # else:
        #    flow = InstalledAppFlow.from_client_config(json.loads(GOOGLE_SERVICE_ACCOUNT_KEY), SCOPES)
        #    auth_url, _ = flow.authorization_url(prompt='consent')
        #    print(f"Please go to this URL: {auth_url}")
        #    code = input("Enter the authorization code: ")
        #    creds = flow.fetch_token(code=code)

    google_auth()
    
    # Google Calendar API-Dienst erstellen
    service = build('calendar', 'v3', credentials=creds)

    # Aktuelle Zeit (in UTC)
    now = datetime.datetime.utcnow()

    # Startzeitpunkt auf 7 Tage zurücksetzen (oder nach Wunsch anpassen)
    time_min = (now - datetime.timedelta(days=21)).isoformat() + 'Z'
    time_max = now.isoformat() + 'Z'
    
    # Abrufen der letzten 10 Ereignisse aus der Vergangenheit
    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min,
                                          timeMax=time_max, maxResults=10, 
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    else:
        # Alle Ereignisse durchgehen und Daten extrahieren
        extracted_data = []
        for event in events:
            event_data = extract_event_data(event)
            extracted_data.append(event_data)
            date = event_data.get('Datum')
            name = event_data.get('Name')
            map_name = event_data.get('Map')
            if not page_exist_in_enemy_list(name):
                create_page_in_enemy_list(name,date)
                create_page_in_prac_list(date, map_name,find_entry_id_by_name(name))

            if not page_exist_prac_list(date, map_name, find_entry_id_by_name(name)):
            #    # Wenn nicht, erstelle eine neue Seite
                create_page_in_prac_list(date, map_name,find_entry_id_by_name(name))
        
        # Ergebnisse als JSON formatieren
        #json_output = json.dumps(extracted_data, indent=4)
        #–––––––
        #–––––––
        #wie die ausgabe ist checken
        
        print("sucsessfully posted")
        #print(json_output)

if __name__ == '__main__':
    main()
