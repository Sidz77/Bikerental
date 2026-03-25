from pymongo import MongoClient

uri = "mongodb+srv://siduser:SidDB77@cluster0.imfvfas.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)
db = client["bikerental"]

print("Connected successfully")