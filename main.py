from typing import Union
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from helper import hash_password, isValidPassword, generate_unique_token
from model import Email, LoginDetails, Partner, PartnerRegister, UpdateUserData, UserRegister, Product, Category, SessionState, Rating, ConnectionConfig, ForgetPasswordRequest, Resets, UpdatedUserData
from mongo_commands import activate_user, authenticate_partner, delete_token_data, get_email_resets, get_token, get_unregpartneraccounts, get_user, put_product, put_account, get_category, get_useraccounts, get_partneraccounts, reject_partner, store_reset_token, suspend_user, update_password, find_user_by_email, update_user_by_id
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

@app.get("/verifytoken/{token}")
def verify_token(token: str):
    # Check if the token is valid (e.g., exists in the database)
    if get_token(token):
        return {"valid": True}
    else:
        return {"valid": False}

@app.post("/resetpassword")
def reset_password(reset : Resets, response: Response):
    token = reset.token
    newPassword = hash_password(reset.newpassword)
    email = get_email_resets(token)
    
    if email:
        # If the email is found, update the password
        email = email["email"]
        update_result = update_password(email, newPassword)
        if update_result.modified_count == 1:
            delete_token_data(token)
            return {"message": "Password reset successfully"}
        else:
            # If update was unsuccessful, handle accordingly
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"message": "Failed to reset password"}

    # If the email associated with the token is not found
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"message": "Email not found"}

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
    print(user)

    if not user:
        print("Invalid username or password 1")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid username or password"
    print(user)
    if user:
        # check if password match
        if not isValidPassword(password, user["password"]):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Invalid username or password 2"
        if user["role"] == "Partner" and user["authenticate"] == "0":
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Awaiting admin approval"
        if user["suspended"] == "1":
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Account suspended"

    ## all checks done
    print(user)
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
    
    hashed_password = hash_password(register_user.password)
    register_data = register_user.model_dump()
    register_data['password'] = hashed_password
    put_account(register_data)
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

    hashed_password = hash_password(register_partner.password)
    register_data = register_partner.model_dump()
    register_data['password'] = hashed_password
    print(register_data)
    put_account(register_data)
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

@app.post("/get_userdetails")
def get_userdetails(email : Email):
    user = get_user(email.email)
    return {"accounts": user}

@app.post("update_user")


# ============================== Add Product ==============================
@app.post("/add_product")
def add_product(product: Product, response: Response):
    product_data = product.model_dump()
    put_product({'product_id': str(uuid4()), **product_data})
    return "Product added successfully"

@app.get("/get_useraccounts")
def get_user_accounts():
    accounts = get_useraccounts() 
    print(accounts)
    return {"accounts": accounts}

# ============================== User Account ==============================

# Endpoint to update user data
# @app.put("/api/update_user_data/{user_id}")
# def update_user_data(user_id: str, user: UserRegister):
#     # Check if the user exists in the database
#     if user_id not in users:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Update user data in the database
#     users[user_id].update(user.dict())

#     # Return a success message
#     return {"message": "User data updated successfully"}

# @app.put("/update_useraccount")
# def update_user(email : email)

@app.post("/update_user_data")
def update_user_data(data: UpdateUserData):
    print(data)
    update_user(data.email,data)
    return {"message": "User data updated successfully! "}

# ============================== Partner Account ==============================
@app.get("/get_partneraccounts")
def get_partner_accounts(response: Response):
    accounts = get_partneraccounts() 
    print(accounts)
    return {"accounts": accounts}

@app.post("/suspend_user")
def suspend_partner_account( email : Email):
    user = email.email
    partner = get_user(user)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    result = suspend_user(user)
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to suspend partner")

    return {"message": "Partner suspended successfully"}

@app.post("/activate_user")
def activate_partner_account( email : Email):
    user = email.email
    partner = get_user(user)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    # Update the partner's 'suspended' field to 1
    result = activate_user(user)
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to activate partner")

    return {"message": "Partner suspended successfully"}

# ============================== Unregister Partner Account ==============================
@app.get("/get_unregpartneraccounts")
def get_unregpartner_accounts(response: Response):
    accounts = get_unregpartneraccounts() 
    print(accounts)
    return {"accounts": accounts}

@app.post("/authenticate_partner")
def authenticate_partner_account(email : Email):
    user = email.email
    partner = get_user(user)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    # Update the partner's 'suspended' field to 1
    result = authenticate_partner(user)
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to activate partner")

    return {"message": "Partner suspended successfully"}

@app.post("/reject_partner")
def suspend_partner_account( email : Email):
    user = email.email
    partner = get_user(user)
    print(partner)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    result = reject_partner(user)
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to suspend partner")

    return {"message": "Partner suspended successfully"}


# Backend endpoint to update user data
@app.put('/user/{user_id}')
async def update_user(user_id: str, updated_user_data: UpdatedUserData):
    try:
        updated_user = update_user_by_id(user_id, updated_user_data.dict())
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while updating user data")