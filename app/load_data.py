import csv
from app.db import db
from app.models import Podcast

def load_podcast_data():
    # Path to your CSV file
    csv_path = "app/static/assets/poddf.csv"  # ✅ adjust if needed

    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Name')
            if name:
                podcast = Podcast(name=name)
                db.session.add(podcast)

        db.session.commit()
        print(f"Loaded {db.session.query(Podcast).count()} podcast names.")
