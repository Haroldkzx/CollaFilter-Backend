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

# Updates password from restpassword.js
def update_password(email, new_password):
    col, _ = connect(ACCOUNT_COLLECTION)
    query = {"email": email}
    update_query = {"$set": {"password": new_password}}
    result = col.update_one(query, update_query)
    return result

def delete_token_data(token):
    col, _ = connect(RESET_COLLECTION)
    result = col.delete_one({"token": token})
    return result.deleted_count

def get_token(token):
    col, _= connect(RESET_COLLECTION)
    query = {"token": token}
    token_data = col.find_one(query)
    return token_data

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
    projection = {"_id": 0, "email": 1} 
    email = col.find_one(query, projection)
    return email

# ========================================

def get_useraccounts():
    col, _ = connect(ACCOUNT_COLLECTION)  
    query = {"role": "User"} 
    projection = {"_id": False} 
    result = col.find(query, projection)  
    return list(result)


def get_partneraccounts():
    col, _ = connect(ACCOUNT_COLLECTION)  
    query = {"role": {"$in": ["Partner", "partner"]}, "authenticate": "1"}  
    projection = {"_id": False} 
    result = col.find(query, projection)  
    return list(result)

def get_unregpartneraccounts():
    col, _ = connect(ACCOUNT_COLLECTION)  
    query = {"role": {"$in": ["Partner", "partner"]}, "authenticate": "0"}  
    projection = {"_id": False} 
    result = col.find(query, projection)  
    return list(result)

def get_useraccounts():
    col, _ = connect(ACCOUNT_COLLECTION)  
    query = {"role": {"$in": ["User", "user"]}}  
    projection = {"_id": False} 
    result = col.find(query, projection)  
    return list(result)

def suspend_user(email):
    col, _ = connect(ACCOUNT_COLLECTION) 
    query = {"email": email} 
    update = {"$set": {"suspended": "1"}}
    result = col.update_one(query, update)
    return result

def authenticate_partner(email):
    col, _ = connect(ACCOUNT_COLLECTION) 
    query = {"email": email} 
    update = {"$set": {"authenticate": "1"}}
    result = col.update_one(query, update)
    return result

def reject_partner(email):
    col, _ = connect(ACCOUNT_COLLECTION) 
    query = {"email": email} 
    result = col.delete_one(query)
    return result


def activate_user(email):
    col, _ = connect(ACCOUNT_COLLECTION) 
    query = {"email": email} 
    update = {"$set": {"suspended": "0"}}
    result = col.update_one(query, update)
    return result

def update_user(email, updated_details):
    col, _ = connect(ACCOUNT_COLLECTION) 
    query = {"email": email}  
    updated_dict = updated_details.__dict__

    # Remove the "__dict__" key and any other unwanted keys
    updated_dict.pop("__dict__", None)
    
    # Construct the update query
    update = {"$set": updated_dict}
    result = col.update_one(query, update)
    
    if result.modified_count == 1:
        # Document was updated successfully
        return "updated"
    else:
        # Document was not updated (either not found or no changes)
        return "no changes"