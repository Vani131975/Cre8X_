import pymongo
from django.conf import settings
import os

MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://sheshumanthravadi147:SheshuVani@cluster0.pbbnd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

client = pymongo.MongoClient(MONGO_URI)

db = client['cre8x']


accounts_collection = db['accounts']
projects_collection = db['projects']
invitations_collection = db['invitations']
notifications_collection = db['notifications']
chat_collection = db['chat_messages']

class MongoDBConnector:
    @staticmethod
    def insert_one(collection, data):
        """Insert one document into the specified collection"""
        return db[collection].insert_one(data)
    
    @staticmethod
    def find_one(collection, query):
        """Find one document in the specified collection"""
        return db[collection].find_one(query)
    
    @staticmethod
    def find(collection, query=None, projection=None):
        """Find documents in the specified collection"""
        return db[collection].find(query or {}, projection or {})
    
    @staticmethod
    def update_one(collection, query, update_data):
        """Update one document in the specified collection"""
        return db[collection].update_one(query, {'$set': update_data})
    
    @staticmethod
    def delete_one(collection, query):
        """Delete one document from the specified collection"""
        return db[collection].delete_one(query)
    
    @staticmethod
    def count_documents(collection, query=None):
        """Count documents in the specified collection"""
        return db[collection].count_documents(query or {})