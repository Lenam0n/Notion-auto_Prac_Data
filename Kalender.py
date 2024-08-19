import os
from notion_client import Client
from datetime import datetime, timedelta

# Laden der Datenbank-ID aus der Umgebungsvariable
DATABASE_ID = os.getenv("DATABASE_KALENDER")

# Erstellen des Notion-Clients
notion = Client(auth=os.getenv("NOTION_API_KEY"))


# Funktion zum Erstellen eines neuen Eintrags in der Notion-Datenbank
def create_page_in_database(date, day_name):
    new_page = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": day_name
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": date
                }
            }
        }
    }
    notion.pages.create(**new_page)

# Funktion zum Überprüfen, ob eine Seite für ein bestimmtes Datum existiert
def page_exists(date):
    query = notion.databases.query(
        **{
            "database_id": DATABASE_ID,
            "filter": {
                "property": "Date",
                "date": {
                    "equals": date
                }
            }
        }
    )
    return len(query['results']) > 0

# Hauptfunktion, die die Logik ausführt

# Berechne das Datum, das 4 Tage in der Zukunft liegt
target_date = datetime.now() + timedelta(days=10)
target_date_str = target_date.strftime("%Y-%m-%d")
day_name = target_date.strftime("%A")

# Überprüfen, ob die Seite bereits existiert
if not page_exists(target_date_str):
    # Wenn nicht, erstelle eine neue Seite
    create_page_in_database(target_date_str, day_name)
