from typing import Union
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from helper import isValidPassword, generate_unique_token
from model import LoginDetails, PartnerRegister, UserRegister, Product, Category, SessionState, Rating, ConnectionConfig, ForgetPasswordRequest, Resets
from mongo_commands import get_email_resets, get_user, put_product, put_account, get_category, get_useraccounts, get_partneraccounts, store_reset_token
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
import uvicorn
import time

from fastapi import (
    FastAPI,
    Response,
    Depends,
    status,
    HTTPException,
    APIRouter,
    Request,
    Body,
)
import random

app = FastAPI()
# User Database (for demonstration purposes)
users = {}

# In-memory session storage (for demonstration purposes)
sessions = {}

# ======================================= RESET PASSWORD ========================================
conf = ConnectionConfig(
    MAIL_USERNAME = "collafilter@gmail.com",
    MAIL_PASSWORD = "wbyo slqi yljy ztot",
    MAIL_FROM = "collafilter@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False
)

html = """
<html>
    <head></head>
    <body>
        <h1>Reset Password Instructions</h1>
        <p>To reset your password, click on the following link: <a href="http://localhost:3000/resetpassword/{token}">Reset Password</a></p>
    </body>
</html>
"""

@app.post("/forgetpassword")
async def forget_password(email: ForgetPasswordRequest):
    user = get_user(email.email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = generate_unique_token()

    store_reset_token(email.email, token)

    # Send reset password instructions to the user's email
    message = MessageSchema(
        subject="Password Reset Instructions",
        recipients=[email.email],
        body=html.replace("{token}", token),
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)  # Await the send_message method

    return "Reset password instructions sent to your email"

@app.post("/resetpassword")
def reset_password(reset : Resets):
    token = reset.token
    newpassword = reset.newpassword
    email = get_email_resets(token)
    print(email)
    return email



# ======================================= RESET PASSWORD ========================================


def get_session(email, uuid):
    session_uuid = sessions["email"]
    if uuid == session_uuid:
        return sessions["email"]
    else:
        return False


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


# ============================== LOGIN ==============================
@app.post("/login")
def login(login_details: LoginDetails, response: Response):
    email = login_details.email
    password = login_details.password
    user = get_user(email)

    if not user:
        print("Invalid username or password 1")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid username or password"

    if user:
        # check if password match
        if not isValidPassword(password, user["password"]):
            print("Invalid username or password")
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Invalid username or password 2"
        if user["role"] == "partner" and user["authenticate"] == "0":
            print("Awaiting admin approval")
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Awaiting admin approval"

    ## all checks done
    user_session = {**user, "session_uuid": uuid4(), "role": user["role"]}
    sessions[user["email"]] = user_session
    return user_session

@app.post("/logout")
def logout(response: Response):
    # Clear the session data
    response.delete_cookie(key="session_token")
    print("called")
    # You can also clear any other session-related data if needed
    return {"message": "Logged out successfully!"}

# ============================== Register ==============================
@app.post("/registeruser")
def registeruser(register_user : UserRegister, response: Response):
    if not all(register_user.model_dump().values()):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return "All fields are required"
    
    existing_user = get_user(register_user.email)
    if existing_user:
        response.status_code = status.HTTP_409_CONFLICT
        return "Email already registered"
    
    register_data = register_user.model_dump()
    put_account({**register_data})
    return "User Registered successfully"

@app.post("/registerpartner")
def registerpartner(register_partner: PartnerRegister, response: Response):
    if not all(register_partner.model_dump().values()):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return "All fields are required"
    
    existing_user = get_user(register_partner.email)
    if existing_user:
        response.status_code = status.HTTP_409_CONFLICT
        return "Email already registered"

    register_data = register_partner.model_dump()
    print(register_data)
    put_account({**register_data})
    return "Partner Registered successfully"

# ============================== Ratings ==============================
@app.post("/add_rating")
def add_ratings(ratings: Rating):
    rating_data = ratings.model_dump()
    put_product({**rating_data})
    return "Rating inserted"

# ============================== Retrieve Categories / Subcategories ==============================

@app.get("/get_categories")
def get_categories(response: Response):
    categories = get_category()
    print(categories)
    return {"categories": categories}

@app.get("/get_subcategories")
def get_subcategories(category: str):
    if category in get_category:
        return {"subcategories": get_category[category]}
    else:
        raise HTTPException(status_code=404, detail="Category not found")


# ============================== Add Product ==============================
@app.post("/add_product")
def add_product(product: Product, response: Response):
    product_data = product.model_dump()
    put_product({'product_id': str(uuid4()), **product_data})
    return "Product added successfully"



# ============================== User Account ==============================
@app.get("/get_useraccounts")
def get_user_accounts(response: Response):
    accounts = get_useraccounts() 
    print(accounts)
    return {"accounts": accounts}


# Endpoint to update user data
@app.put("/api/update_user_data/{user_id}")
def update_user_data(user_id: str, user: UserRegister):
    # Check if the user exists in the database
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user data in the database
    users[user_id].update(user.dict())

    # Return a success message
    return {"message": "User data updated successfully"}


# ============================== Partner Account ==============================
@app.get("/get_partneraccounts")
def get_partner_accounts(response: Response):
    accounts = get_partneraccounts() 
    filtered_accounts = [account for account in accounts if account.get("authentication") == '1']
    return {"accounts": filtered_accounts}