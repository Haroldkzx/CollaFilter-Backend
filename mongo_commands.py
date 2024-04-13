from pymongo import MongoClient
import secrets

client = MongoClient("mongodb+srv://admin:admin@cluster0.immhkre.mongodb.net/CollaFilter")
ACCOUNT_COLLECTION = "accounts"
PRODUCTS_COLLECTION ='products'
CATEGORY_COLLECTION ='categories'
RATING_COLLECTION = 'ratings'
RESET_COLLECTION = 'Resets'


def connect(collection):
    db = client["CollaFilter"]
    collection = db[collection]
    return collection, db


def get_user(email):
    col, _ = connect(ACCOUNT_COLLECTION)
    query = {"email": email}
    result = col.find_one(query, {"_id": False})
    return result

def get_product(uuid):
    col, _ = connect(PRODUCTS_COLLECTION)
    query = {"uuid": uuid}
    result = col.find_one(query, {"_id": False})
    return result

def put_product(product_details):
    col, _ = connect(PRODUCTS_COLLECTION)
    doc = {**product_details}
    result = col.insert_one(doc)
    return result

def put_account(account_details):
    col, _ = connect(ACCOUNT_COLLECTION)
    doc = {**account_details}
    result = col.insert_one(doc)
    return result

def put_rating(rating_details):
    col, _ = connect(RATING_COLLECTION)
    doc = {**rating_details}
    result = col.insert_one(doc)
    return result

def get_category():
    col, _ = connect(CATEGORY_COLLECTION)
    categories = col.find({}, {"Category": 1, "subCategory": 1, "_id": 0})

    category_data = {}
    for doc in categories:
        category = doc["Category"]
        subcategory = doc["subCategory"]
        if category not in category_data:
            category_data[category] = []
        category_data[category].extend(subcategory)

    return category_data

# ========================================
def store_reset_token(email, token):
    col, _= connect(RESET_COLLECTION)
    query = {"email": email, "token": token}
    result = col.insert_one(query)
    return result

def get_reset_token(email):
    col, _= connect(RESET_COLLECTION)
    query = {"email": email}
    token_data = col.find_one(query)
    return token_data

def get_email_resets(token):
    col, _= connect(RESET_COLLECTION)
    query = {"token": token}
    projection = {"token": 0, "email": 1} 
    email = col.find_one(query, projection)
    return email

# ========================================

def get_useraccounts():
    col, _ = connect(ACCOUNT_COLLECTION)  
    query = {"role": "user"}  
    projection = {"_id": False} 
    result = col.find(query, projection)  
    return list(result)  

def get_partneraccounts():
    col, _ = connect(ACCOUNT_COLLECTION)  
    query = {"role": "partner"}  
    projection = {"_id": False} 
    result = col.find(query, projection)  
    return list(result)  