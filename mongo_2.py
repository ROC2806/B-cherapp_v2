from urllib.parse import quote_plus
from pymongo import MongoClient, UpdateOne
import streamlit as st
import uuid

# --- Verbindungsaufbau ---
mongo_secrets = st.secrets["mongodb"]
MONGO_USERNAME = quote_plus(mongo_secrets["MONGO_USERNAME"])
MONGO_PASSWORD = quote_plus(mongo_secrets["MONGO_PASSWORD"])
MONGO_CLUSTER = mongo_secrets["MONGO_CLUSTER"]

MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["Leseapp_2"]
wishlist_collection = db["wishlist_2"]
read_books_collection = db["read_books2"]

# --- Laden von Daten ---
def load_data():
    wishlist = list(wishlist_collection.find({}))
    read_books = list(read_books_collection.find({}))

    # Fehlende _id nachrüsten (sicherheitshalber – falls später mal manuell Daten eingetragen werden)
    for book in wishlist:
        if "_id" not in book:
            book["_id"] = str(uuid.uuid4())
    for book in read_books:
        if "_id" not in book:
            book["_id"] = str(uuid.uuid4())

    return {
        "wishlist": wishlist,
        "read_books": read_books
    }

# --- Speichern von Daten ---
def save_data(data):
    wishlist_ops = []
    for book in data.get("wishlist", []):
        if "_id" not in book:
            book["_id"] = str(uuid.uuid4())
        wishlist_ops.append(
            UpdateOne(
                {"_id": book["_id"]},
                {"$set": book},
                upsert=True
            )
        )

    read_books_ops = []
    for book in data.get("read_books", []):
        if "_id" not in book:
            book["_id"] = str(uuid.uuid4())
        read_books_ops.append(
            UpdateOne(
                {"_id": book["_id"]},
                {"$set": book},
                upsert=True
            )
        )

    if wishlist_ops:
        wishlist_collection.bulk_write(wishlist_ops)

    if read_books_ops:
        read_books_collection.bulk_write(read_books_ops)

# --- Entfernen einzelner Bücher ---
def delete_wishlist_entry(book_id):
    wishlist_collection.delete_one({"_id": book_id})

def delete_read_book_entry(book_id):
    read_books_collection.delete_one({"_id": book_id})
