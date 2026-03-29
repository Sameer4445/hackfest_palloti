from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_DETAILS)
database = client.nanocredit

application_collection = database.get_collection("applications")

def add_application(application_data: dict):
    application = application_collection.insert_one(application_data)
    new_application = application_collection.find_one({"_id": application.inserted_id})
    return new_application

def retrieve_applications():
    applications = []
    for application in application_collection.find():
        applications.append(application)
    return applications
