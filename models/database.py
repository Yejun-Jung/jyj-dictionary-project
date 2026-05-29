from pymongo import MongoClient
from config import MONGO_URI


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        if self.client is None:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client.dbsparta

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def get_db(self):
        if self.db is None:
            self.connect()
        return self.db


mongodb = MongoDB()
