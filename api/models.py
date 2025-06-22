from dotenv import load_dotenv
load_dotenv()
from pymongo import MongoClient
import os

DB_URL=os.environ.get('DB_URL')

conn = MongoClient(DB_URL)
db = conn.get_database("main_db")
Schools = db.get_collection("schools")
Emails = db.get_collection("emails")
Senders = db.get_collection("senders")

Email_statuses = db.get_collection("email_statuses")
HostedUrls = db.get_collection("hosted_urls")