from pymongo import MongoClient
from bson import Binary
import uuid
import secrets

client = MongoClient("mongodb+srv://admin:admin@cluster0.immhkre.mongodb.net/CollaFilter")

ACCOUNT_COLLECTION = "accounts"
BOOKMARK_COLLECTION = "bookmarks"
PRODUCTS_COLLECTION = 'products'
CATEGORY_COLLECTION = 'categories'
RATINGS_COLLECTION = 'ratings'
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
    col, _ = connect(RATINGS_COLLECTION)
    doc = {**rating_details}
    result = col.insert_one(doc)
    return result

def get_category():
    col, _ = connect(CATEGORY_COLLECTION)
    categories = col.find({}, {"category": 1, "_id": 0})

    category_data = {}
    for doc in categories:
        category = doc.get("category")
        if category:
            category_data[category] = []  # Initialize empty list for each category

    return category_data

def update_authenticate_email(email):
    col, _= connect(ACCOUNT_COLLECTION)
    query = {"email": email}
    update_query = {"$set": {"authenticate": "1"}}
    result = col.update_one(query, update_query)
    if result.modified_count == 1:
        print("updated authenticate")
        return "Account authenticated"
    else:
        print("failed to authenticate")
        return "Unable to authenticate"
# ========================================
def store_reset_token(email, token):
    col, _ = connect(RESET_COLLECTION)
    if col.find_one({"email": email}):
        raise ValueError("Email already exists")
    
    query = {"email": email, "token": token}
    result = col.insert_one(query)
    print("Inserted")
    return result

def get_reset_token(email):
    col, _= connect(RESET_COLLECTION)
    query = {"email": email}
    token_data = col.find_one(query)
    return token_data

def get_email_from_token(token):
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
    
def get_products(userid):
    col, _ = connect(PRODUCTS_COLLECTION) 
    query = {"user_id": userid}
    projection = {"_id": 0}
    products = col.find(query, projection)
    return list(products)

def get_allproducts(): 
    col, _ = connect(PRODUCTS_COLLECTION) 
    projection = {"_id": False} 
    all_products = list(col.find({}, projection))
    return all_products

def delete_category(category):
    col, _ = connect(CATEGORY_COLLECTION) 
    query = {"category": category}
    result = col.delete_one(query)
    if result.deleted_count == 1:
        # Document was updated successfully
        return "deleted"
    else:
        # Document was not updated (either not found or no changes)
        return "no changes"

def add_category(category):
    col, _ = connect(CATEGORY_COLLECTION)
    doc = {"category": category}  # Assuming 'category' is the key name
    result = col.insert_one(doc)
    if result:
        return "Category added successfully"
    else:
        return "Failed to add category"
    
def update_category(old_cat,new_cat):
    col, _ = connect(CATEGORY_COLLECTION)
    query = {"category": old_cat}
    update = {"$set": {"category": new_cat}}
    
    # Update the document with the new category
    result = col.update_one(query, update)
    if result.modified_count == 1:
        # Document was updated successfully
        return "updated"
    else:
        # Document was not updated (either not found or no changes)
        return "no changes"
    
def delete_product(product):
    col, _ = connect(PRODUCTS_COLLECTION) 
    query = {"category": product}
    result = col.delete_one(query)
    if result.deleted_count == 1:
        # Document was updated successfully
        return "deleted"
    else:
        # Document was not updated (either not found or no changes)
        return "no changes"
    
def get_partnername(userid):
    col, _ = connect(ACCOUNT_COLLECTION)
    query = {"user_id": userid}
    projection = {"_id" : 0}
    result = col.find_one(query, projection)
    return result

def del_product(productid):
    col, _ = connect(PRODUCTS_COLLECTION)
    query = {"product_id": productid}
    result = col.delete_one(query)
    if result.deleted_count == 1:
        return True  # Deletion successful
    else:
        return False  # Deletion failed

def get_product_by_category(category):
    col, _ = connect(PRODUCTS_COLLECTION)
    query = {"category": category}
    projection = {"_id" : 0}
    result = col.find(query, projection)
    product_list = list(result)  # Convert cursor to list of documents
    return product_list

def get_averagerating(productid):
    col, _ = connect(RATINGS_COLLECTION)
    query = {"product_id": productid}
    result = col.find(query)

    total_rating = 0
    count = 0
    for rating_doc in result:
        total_rating += rating_doc['rating']
        count += 1

    if count == 0:
        return None  # Return None if no ratings found for the product_id
    else:
        averagerating = total_rating / count  # Calculate average rating
        return round(averagerating, 1)

def updated_product(product_id, updated_data):
    col, _ = connect(PRODUCTS_COLLECTION)
    query = {"product_id": product_id}
    update = {"$set": updated_data}
    
    # Update the document with the new data
    result = col.update_one(query, update)
    if result.modified_count == 1:
        # Document was updated successfully
        print("changed")
        return "updated"
    else:
        # Document was not updated (either not found or no changes)
        print("no changed")
        return "no changes"
    
def total_users():
    col, _ = connect(ACCOUNT_COLLECTION)
    query = {"role": "User"}
    user_count = col.count_documents(query)
    return user_count

def total_partners():
    col, _ = connect(ACCOUNT_COLLECTION)
    query = {"role": "Partner"}
    user_count = col.count_documents(query)
    return user_count

def total_products():
    col, _ = connect(PRODUCTS_COLLECTION)
    user_count = col.estimated_document_count()
    return user_count

def add_rating(rating_data):
    col, _ = connect(RATINGS_COLLECTION)
    rating_dict = rating_data.dict()
    result = col.insert_one(rating_dict)
    if result.acknowledged:
        print("rating added")
        return "Rating added successfully"
    else:
        print("rating not added")
        return "Failed to add rating"
    
def recommended_product(product_id, user_id: str):
    col, _ = connect(PRODUCTS_COLLECTION)
    ratings_col, _ = connect(RATINGS_COLLECTION)  # Connect to the ratings collection

    # Check if the user has already rated the product
    query = {"product_id": product_id, "user_id": user_id}
    existing_rating = ratings_col.find_one(query)
    
    if existing_rating:
        return {"message": "User has already rated this product"}

    # Fetch the recommended product if no rating exists
    query = {"product_id": product_id}
    projection = {"_id": 0}
    result = col.find_one(query, projection)
    return result

def get_bookmarks(product_id):
    col, _ = connect(PRODUCTS_COLLECTION)
    query = {"product_id": product_id}
    projection = {"_id" : 0}
    result = col.find_one(query, projection)
    return result
    
def bookmark_product(user_id, product_id):
    col, _ = connect(BOOKMARK_COLLECTION)
    query = {"user_id": user_id}
    existing_user = col.find_one(query)

    if existing_user:
        # Update the existing document by adding product_id to the bookmarks array
        col.update_one(query, {"$addToSet": {"bookmarks": product_id}})
        return "Product bookmarked successfully."
        print("Product bookmarked successfully.")
    else:
        # If the user document doesn't exist, create a new one and add the product_id
        new_user_doc = {"user_id": user_id, "bookmarks": [product_id]}
        col.insert_one(new_user_doc)
        return "New user bookmark record created."
    
def remove_bookmark(user_id, product_id):
    col, _ = connect(BOOKMARK_COLLECTION)
    col.update_one({"user_id": user_id}, {"$pull": {"bookmarks": product_id}})
    return "Product bookmark removed successfully."

def increment_count(product_id):
    col, _ = connect(PRODUCTS_COLLECTION)
    query = {"product_id": product_id}
    update = {"$inc": {"clicks": 1}}  # Increment the clicks field by 1
    col.update_one(query, update)
    return "Count increased"

def retrieve_items(user_id):
    col, _ = connect(BOOKMARK_COLLECTION)
    query = {"user_id": user_id}
    result = col.find_one(query)
    if result:
        return result["bookmarks"]
    else:
        return []
    
def update_recentlyviewed(user_id, product_id, max_length=10):
    col, _ = connect(BOOKMARK_COLLECTION)
    # Remove the oldest product if the array length exceeds max_length
    col.update_one(
        {"user_id": user_id},
        {"$push": {"recent": {"$each": [product_id], "$slice": -max_length}}},
        upsert=True  # Create the document if it doesn't exist
    )
    return "Added to recently viewed"

def retrieve_recentlyviewed(user_id):
    col, _ = connect(BOOKMARK_COLLECTION)
    query = {"user_id": user_id}
    result = col.find_one(query)
    if result:
        return result.get("recent", [])
    else:
        return []
    
def retrieve_allcategories():
    col, _ = connect(CATEGORY_COLLECTION)
    categories = col.distinct("category")
    return categories




    

