from pymongo import MongoClient

client = MongoClient("mongodb+srv://admin:admin@cluster0.immhkre.mongodb.net/CollaFilter")
ACCOUNT_COLLECTION = "accounts"
PRODUCTS_COLLECTION ='products'
CATEGORY_COLLECTION ='categories'
RATING_COLLECTION = 'ratings'


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



"""
{
    'uuid': // store the products id
    'product_link': // link to partner
    'image': //
    'name': //name of product
    'category': str
    'sub category: str
    'price'://
    'tags': array [tag]
    'product text':
}
"""
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