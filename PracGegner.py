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
from datetime import datetime, timedelta
import re

GOOGLE_KALENDER_ID = os.getenv("GOOGLE_KALENDER_ID")
NOTION_PRAC_LIST = os.getenv("NOTION_PRAC_LIST")
NOTION_ENEMY_LIST = os.getenv("NOTION_ENEMY_LIST")
NOTION_ANALYSIS_MAP=os.getenv("NOTION_ANALYSIS_MAP")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GOOGLE_TOKEN=os.getenv("GOOGLE_TOKEN")

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

def page_exsist_in_analysis_page(name):
    query = notion.databases.query(
        **{
            "database_id" : NOTION_ANALYSIS_MAP,
            "filter" : {
                "property": "Name",
                "title": {
                    "equals": name
                }
            }
        }
    )
    pages = query.get('results', [])
    
    # Gibt nur das erste Ergebnis zurück, wenn vorhanden, ansonsten None
    return pages[0] if pages else None


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
        },
        "icon":{
                "type": "external",
                "external": {
                    "url": mapSelect(map_name)
                }
}
    }
    # Erstelle die neue Seite und speichere das Ergebnis
    created_page = notion.pages.create(**new_page)

    # Übergebe die erstellte Seite an die Funktion append_to_analysis
    append_to_analysis(map_name, created_page)

def page_exist_prac_list(date, map_name, related_task_id):
    query = notion.databases.query(
        database_id=NOTION_PRAC_LIST,
        filter={
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
    )
    return len(query['results']) > 0

def find_entry_id_by_name(name,db):
    query = notion.databases.query(
        **{
            "database_id": db,
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
    creds = Credentials.from_service_account_info(token_info,scopes=SCOPES)
    return creds

def mapSelect(map_name):
    if map_name == "Ascent":
        return "https://media.valorant-api.com/maps/7eaecc1b-4337-bbf6-6ab9-04b8f06b3319/splash.png"
    elif map_name == "Split":
        return "https://media.valorant-api.com/maps/d960549e-485c-e861-8d71-aa9d1aed12a2/splash.png"
    elif map_name == "Fracture":
        return "https://media.valorant-api.com/maps/b529448b-4d60-346e-e89e-00a4c527a405/splash.png"
    elif map_name == "Bind":
        return "https://media.valorant-api.com/maps/2c9d57ec-4431-9c5e-2939-8f9ef6dd5cba/splash.png"
    elif map_name == "Breeze":
        return "https://media.valorant-api.com/maps/2fb9a4fd-47b8-4e7d-a969-74b4046ebd53/splash.png"
    elif map_name == "Abyss":
        return "https://media.valorant-api.com/maps/224b0a95-48b9-f703-1bd8-67aca101a61f/splash.png"
    elif map_name == "Lotus":
        return "https://media.valorant-api.com/maps/2fe4ed3a-450a-948b-6d6b-e89a78e680a9/splash.png"
    elif map_name == "Sunset":
        return "https://media.valorant-api.com/maps/92584fbe-486a-b1b2-9faa-39b0f486b498/splash.png"
    elif map_name == "Pearl":
        return "https://media.valorant-api.com/maps/fd267378-4d1d-484f-ff52-77821ed10dc2/splash.png"
    elif map_name == "Icebox":
        return "https://media.valorant-api.com/maps/e2ad5c54-4114-a870-9641-8ea21279579a/splash.png"
    elif map_name == "Haven":
        return "https://media.valorant-api.com/maps/2bee0dc9-4ffe-519b-1cbd-7fbe763a6047/splash.png"
    #elif map_name == "Pearl":
        #return ""
    else:
        return ""

def append_to_analysis(map_name, created_page):
    # Suchen nach dem Map-Container in der Analysis Map
    mapContainer_results = page_exsist_in_analysis_page(map_name)

    if not mapContainer_results or mapContainer_results == None:
        return

    mapContainer = mapContainer_results

    # Extrahiere die Relation-Property
    existing_relations = mapContainer['properties']['Maps']['relation']
    existing_relation_ids = [relation['id'] for relation in existing_relations]

    # Finden der ID der Map, die wir hinzufügen möchten
    map_id = created_page['id']

    # Überprüfen, ob diese Map-ID bereits in den Beziehungen enthalten ist
    if map_id not in existing_relation_ids:
        # Füge die neue Relation hinzu
        updated_relations = existing_relations
        updated_relations.append({'id': map_id})
        
        # Aktualisiere die Seite mit den neuen Beziehungen
        notion.pages.update(
            page_id=mapContainer['id'],
            properties={
                "Maps": {
                    "relation": updated_relations
                }
            }
        )

def main():
    creds = google_auth()

    # Google Calendar API-Dienst erstellen
    service = build('calendar', 'v3', credentials=creds)

    # Aktuelle Zeit (in UTC)
    now = datetime.utcnow()


    # Startzeitpunkt auf 7 Tage zurücksetzen (oder nach Wunsch anpassen)
    time_min = (now - timedelta(days=2)).isoformat() + 'Z'
    time_max = (now + timedelta(hours=2)).isoformat() + 'Z'
    print(time_max)
    
    # Abrufen der letzten 10 Ereignisse aus der Vergangenheit
    events_result = service.events().list(calendarId=GOOGLE_KALENDER_ID, timeMin=time_min,
                                          timeMax=time_max, maxResults=15, 
                                          singleEvents=True, orderBy='updated').execute()
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
                create_page_in_prac_list(date, map_name,find_entry_id_by_name(name,NOTION_ENEMY_LIST))

            if not page_exist_prac_list(date, map_name, find_entry_id_by_name(name,NOTION_ENEMY_LIST)):
            #    # Wenn nicht, erstelle eine neue Seite
                create_page_in_prac_list(date, map_name,find_entry_id_by_name(name,NOTION_ENEMY_LIST))
        
        # Ergebnisse als JSON formatieren
        json_output = json.dumps(extracted_data, indent=4)
        #–––––––
        #–––––––
        #wie die ausgabe ist checken
        
        print(json_output)
        print("sucsessfully posted")

if __name__ == '__main__':
    main()
