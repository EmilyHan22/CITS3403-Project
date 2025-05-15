import sqlite3
import pandas as pd
import os

# File paths
log_csv_path = "D:/programming_projevts/Podforlio/CITS3403-Project/app/podcast_log_dummy_data.csv"
podcast_csv_path = "D:/programming_projevts/Podforlio/CITS3403-Project/app/podcast_table_dummy_data.csv"
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "podfolio.db")
print("Loading data into:", db_path)

# Check files exist
if not os.path.exists(log_csv_path):
    print(f"ERROR: Log file not found: {log_csv_path}")
    exit(1)
if not os.path.exists(podcast_csv_path):
    print(f"ERROR: Podcast file not found: {podcast_csv_path}")
    exit(1)

# Load CSV files
try:
    log_df = pd.read_csv(log_csv_path)
    podcast_df = pd.read_csv(podcast_csv_path)
    print("CSV files loaded successfully.")
except Exception as e:
    print(f"Error loading CSV files: {e}")
    exit(1)

# Connect to SQLite DB
try:
    conn = sqlite3.connect(db_path)
    print("Connected to SQLite database.")
except Exception as e:
    print(f"Error connecting to database: {e}")
    exit(1)

# Upload data
try:
    podcast_df.to_sql("podcast", conn, if_exists="replace", index=False)
    log_df.to_sql("podcast_log", conn, if_exists="replace", index=False)
    print("Data loaded into SQLite tables.")
except Exception as e:
    print(f"Error uploading data to database: {e}")
    conn.close()
    exit(1)

# Verify tables
print("Tables in database:")
for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';"):
    print("-", row[0])

conn.close()
print("Database connection closed.")

