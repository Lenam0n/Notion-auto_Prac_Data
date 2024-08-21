import os
from notion_client import Client
from datetime import datetime, timedelta
import pytz

# Definiere die Stunde und die Zeitzone
hour = 18
timezone = pytz.timezone('Europe/Berlin')  # CEST ist die Sommerzeit für Berlin

# Erstelle ein datetime-Objekt für die angegebene Stunde heute
now = datetime.now()
local_time = datetime(year=now.year, month=now.month, day=now.day, hour=hour, minute=0, second=0, tzinfo=timezone)

# Formatiere die Zeit als String
formatted_time = local_time.strftime('%H:%M %Z')

print(f"{formatted_time} CEST")

# Laden der Datenbank-ID aus der Umgebungsvariable
DATABASE_ID = os.getenv("DATABASE_KALENDER")

# Erstellen des Notion-Clients
notion = Client(auth=os.getenv("NOTION_API_KEY"))
def page_exists():
    query = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "and": [
                # Filter für Start und End Properties, die nicht leer sein dürfen
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
                # Filter für Date Property, das irgendein Datum haben muss, aber keine Zeit und kein Enddatum
                {
                    "property": "Date",
                    "date": {
                        "is_not_empty": True
                    }
                },
                {
                    "property": "Date",
                    "date": {
                        "does_not_contain": "T"  # Annahme: "T" in der ISO-Zeit bedeutet, dass Zeit enthalten ist
                    }
                }
            ]
        }
    )
    pages = query.get('results', [])
    return pages

def time_render(num):
  now = datetime.now()
  local_time = datetime(year=now.year, month=now.month, day=now.day, hour=num, minute=0, second=0, tzinfo=pytz.timezone('Europe/Berlin'))
  return local_time

def update_pages(pages):
    for page in pages:
        start_number = page['properties']['Start']['number']
        end_number = page['properties']['End']['number']
        
        # Wandle die Start- und Endnummern in Zeit um
        start_time = time_render(int(start_number))
        end_time = time_render(int(end_number))
        
        # Aktualisiere die Date-Property
        notion.pages.update(
            page_id=page['id'],
            properties={
                "Date": {
                    "date": {
                        "start": start_time,  # Start-Zeit als ISO 8601 Format
                        "end": end_time  # End-Zeit als ISO 8601 Format
                    }
                }
            }
        )
def Main():
    update_pages(page_exists())

if __name__ == '__main__':
    main()
