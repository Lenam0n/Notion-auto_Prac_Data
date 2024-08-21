from datetime import datetime
import pytz
from notion_client import Client
import os

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
# Initialisiere den Notion-Client
notion = Client(auth=NOTION_API_KEY)
DATABASE_ID = os.getenv("DATABASE_KALENDER")

def time_render(hour, date_str):
    # Erstelle ein datetime-Objekt basierend auf dem bestehenden Datum und der Uhrzeit
    timezone = pytz.timezone('Europe/Berlin')
    local_time = timezone.localize(datetime.strptime(f"{date_str} {hour:02d}:00:00", "%Y-%m-%d %H:%M:%S"))
    
    # Konvertiere die lokale Zeit nach UTC
    utc_time = local_time.astimezone(pytz.utc)
    
    # Gebe die UTC-Zeit im ISO 8601 Format zurück
    return utc_time.isoformat()

def get_filtered_pages():
    query = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "and": [
                {
                    "property": "Start",
                    "number": {
                        "is_not_empty": True
                    }
                },
                {
                    "property": "End",
                    "number": {
                        "is_not_empty": True
                    }
                },
                {
                    "property": "Date",
                    "date": {
                        "is_not_empty": True
                    }
                }
            ]
        }
    )
    pages = query.get('results', [])
    return pages

def update_pages(pages):
    timezone = 'Europe/Berlin'  # Zeitzone festlegen

    for page in pages:
        # Hole das bestehende Datum aus der Date-Eigenschaft
        existing_date = page['properties']['Date']['date']['start']
        existing_date_str = existing_date.split("T")[0]  # Nur das Datum im Format "YYYY-MM-DD"

        start_number = page['properties']['Start']['number']
        end_number = page['properties']['End']['number']
        
        # Erstelle die Start- und Endzeiten in UTC
        start_time = time_render(int(start_number), existing_date_str)
        end_time = time_render(int(end_number), existing_date_str)
        
        # Aktualisiere die Date-Property
        notion.pages.update(
            page_id=page['id'],
            properties={
                "Date": {
                    "date": {
                        "start": start_time,
                        "end": end_time,
                        "time_zone": 'UTC'  # Zeit in UTC, da das notwendig ist, wenn eine Zeitzone explizit angegeben wird
                    }
                }
            }
        )
# Beispielnutzung
filtered_pages = get_filtered_pages()
update_pages(filtered_pages)
