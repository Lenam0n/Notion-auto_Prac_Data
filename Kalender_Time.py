from datetime import datetime
import pytz
from notion_client import Client
import os
from loadenv import dotenv
from dotenv import load_dotenv


# Initialisiere den Notion-Client
notion = Client(auth=os.getenv("NOTION_API_KEY"))

DATABASE_ID = os.getenv("DATABASE_KALENDER")

def time_render(num):
    hour = num
    timezone = pytz.timezone('Europe/Berlin')  # CEST ist die Sommerzeit für Berlin
    now = datetime.now()
    local_time = datetime(year=now.year, month=now.month, day=now.day, hour=hour, minute=0, second=0, tzinfo=timezone)
    return local_time.isoformat()  # ISO 8601 Format für Notion

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

# Beispielnutzung
filtered_pages = get_filtered_pages()
update_pages(filtered_pages)
