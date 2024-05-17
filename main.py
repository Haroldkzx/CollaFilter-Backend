from typing import Union
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
import pandas as pd

from helper import hash_password, isValidPassword, generate_unique_token
from machine_learning import CollaFilterRecommender
from model import Bookmark, EditedCategory, Email, LoginDetails, Partner, PartnerRegister, Recent, SendEmail, UpdateProductNoImage, UpdateUserData, User, UserRegister, Product, Category, SessionState, Rating, ConnectionConfig, ForgetPasswordRequest, Resets, UpdatedUserData, UpdateProduct, userID
from mongo_commands import activate_user, add_category, add_rating, authenticate_partner, bookmark_product, del_product, delete_token_data, get_allproducts, get_averagerating, get_bookmarks, get_product_by_category, get_email_from_token, get_partnername, get_products, get_token, get_unregpartneraccounts, get_user, increment_count, put_product, put_account, get_category, get_useraccounts, get_partneraccounts, recommended_product, reject_partner, remove_bookmark, retrieve_allcategories, retrieve_items, retrieve_recentlyviewed, store_reset_token, suspend_user, total_partners, total_products, total_users, update_authenticate_email, update_category, update_password, update_recentlyviewed, update_user, delete_category, updated_product
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from machine_learning import CollaFilterRecommender
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import uvicorn
import time

from fastapi.middleware.cors import CORSMiddleware

from fastapi import (
    FastAPI,
    Response,
    Depends,
    status,
    HTTPException,
    APIRouter,
    Request,
    Query,
    Body,
    Form,
)
import random

app = FastAPI()
scheduler = AsyncIOScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://collafilter.s3-website-ap-southeast-2.amazonaws.com",  # Frontend domain
        "http://localhost:3000",  # Development localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allowing all HTTP methods
    allow_headers=["*"],  # Allowing all headers
)


# ML

DB_URI = "mongodb+srv://admin:admin@cluster0.immhkre.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = 'CollaFilter'

recommender = CollaFilterRecommender(DB_URI, DB_NAME)

@app.on_event("startup")
async def startup_event():
    start_time = time.time()
    recommender.load_data()
    recommender.train_model()
    process_time = time.time() - start_time
    print(f"Recommendation system took {process_time} seconds")


scheduler.add_job(startup_event, "interval", minutes = 10)
scheduler.start()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"API call to {request.url.path} took {process_time} seconds")
    return response



# ================================================== TOKEN RELATED ==================================================

conf = ConnectionConfig(
    MAIL_USERNAME = "collafilter@gmail.com",
    MAIL_PASSWORD = "wbyo slqi yljy ztot",
    MAIL_FROM = "collafilter@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False
)

resetpasswordhtml = """
<html>
    <head></head>
    <body>
        <h1>Reset Password Instructions</h1>
        <p>To reset your password, click on the following link: <a href="http://collafilter.s3-website-ap-southeast-2.amazonaws.com/resetpassword/{token}">Reset Password</a></p>
    </body>
</html>
"""

emailauthenticationhtml = """
<html>
    <head></head>
    <body>
        <h1>Authenticate account Instructions</h1>
        <p>To authenticate your account, click on the following link: <a href="http://collafilter.s3-website-ap-southeast-2.amazonaws.com/resetpassword/{token}">Authenticate Password</a></p>
    </body>
</html>
"""

@app.post("/forgetpassword")
async def forget_password(email: ForgetPasswordRequest):
    print("Enter: /forgetpassword")
    user = get_user(email.email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = generate_unique_token()
    try:
        store_reset_token(email.email, token)
        # Send reset password instructions to the user's email
        message = MessageSchema(
            subject="Password Reset Instructions",
            recipients=[email.email],
            body=resetpasswordhtml.replace("{token}", token),
            subtype="html"
        )
    
        fm = FastMail(conf)
        await fm.send_message(message)  # Await the send_message method

        print("Exit: /forgetpassword")

        return "Reset password instructions sent to your email"
    except ValueError as e:
        print("Error: ", e)
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/resetpassword")
def reset_password(reset : Resets, response: Response):
    token = reset.token
    newPassword = hash_password(reset.newpassword)
    email = get_email_from_token(token)
    
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


@app.get("/verifytoken/{token}")
def verify_token(token: str):
    # Check if the token is valid (e.g., exists in the database)
    if get_token(token):
        return {"valid": True}
    else:
        return {"valid": False}
    
@app.get("/verifyemail/{token}")
def verify_emailtoken(token: str):
    # Check if the token is valid (e.g., exists in the database)
    if get_token(token):
        email_token = get_email_from_token(token)
        email = email_token["email"]
        update_authenticate_email(email)
        delete_token_data(token)
        return {"authenticated": True}
    else:
        return {"authenticated": False}
    
# ================================================== ENQUIRY ==================================================
    
@app.post("/send_email")
async def send_email(sendemail : SendEmail):
    # Compose email message
    message_content = f"Name: {sendemail.name}\nPhone Number: {sendemail.number}\nEmail: {sendemail.email}\nMessage: {sendemail.message}"

    # Create FastMail instance
    fastmail = FastMail(conf)

    # Send email
    await fastmail.send_message(
        MessageSchema(
            subject="About us enquiry",
            recipients=["collafilter@gmail.com"],  # Specify the email address where you want to receive the form submissions
            body=message_content,
            subtype="plain"
        )
    )

    return {"message": "Email sent successfully"}

# ================================================== HOMEPAGE FUNCTIONS ==================================================

@app.get("/get_totalusers")
def total_userscount():
    result = total_users()
    return result

@app.get("/get_totalblogshops")
def total_partnerscount():
    result = total_partners()
    return result

@app.get("/get_totalproducts")
def total_productscount():
    result = total_products()
    return result

# ================================================== LOGIN FUNCTIONS ==================================================
@app.post("/login")
def login(login_details: LoginDetails, response: Response):
    email = login_details.email
    password = login_details.password
    user = get_user(email)
    print(user)

    if not user:
        print("Invalid username or password 1")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid email or password"
    print(user)
    if user:
        # check if password match
        if not isValidPassword(password, user["password"]):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Invalid email or password"
        if user["role"] == "Partner" and user["authenticate"] == "0":
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Awaiting admin approval"
        if user["role"] == "User" and user["authenticate"] == "0":
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Awaiting email verification"
        if user["suspended"] == "1":
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Account suspended"

    print(user)
    user_session = {**user, "session_uuid": uuid4(), "role": user["role"]}
    return user_session

@app.post("/logout")
def logout(response: Response):
    # Clear the session data
    response.delete_cookie(key="session_token")
    print("called")
    # You can also clear any other session-related data if needed
    return {"message": "Logged out successfully!"}

# ================================================== REGISTER ACCOUNTS ==================================================\

@app.post("/registeruser")
async def registeruser(register_user : UserRegister, response: Response):
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
    put_account({'user_id': str(uuid4()), **register_data})
    verification_token = generate_unique_token()
    store_reset_token(register_user.email, verification_token)

    # Construct email message
    message = MessageSchema(
        subject="Account Verification",
        recipients=[register_user.email],
        body=f"Click the following link to verify your account: <a href='http://collafilter.s3-website-ap-southeast-2.amazonaws.com/VerifyEmail/{verification_token}'>Verify Account</a>",
        subtype="html"
    )

    # Send email
    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": "Verification email sent successfully"}

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
    put_account({'user_id': str(uuid4()), **register_data})
    return "Partner Registered successfully"

# ================================================== UPDATE ACCOUNTS  ==================================================

@app.post("/update_user_data")
def update_user_data(data: User):
    try:
        email = data.email
        print("before")
        is_updated = update_user(email, data)
        if is_updated:
            return {"message": "Profile updated successfully!!!"}
        else:
            return {"message": "No changes or document not found."}
    
    except Exception as e:
        # Handle any exceptions that occur during the update operation
        print("uh oh")
        return {"error": str(e)}
    
@app.post("/update_partner_data")
def update_partner_data(data: Partner):
    try:
        email = data.email
        is_updated = update_user(email, data)
        if is_updated:
            return {"message": "Profile updated successfully!"}
        else:
            return {"message": "No changes or document not found."}
    
    except Exception as e:
        # Handle any exceptions that occur during the update operation
        print("uh oh")
        return {"error": str(e)}

# ================================================== ADMIN FUNCTIONS ==================================================

@app.get("/get_partneraccounts")
def get_partner_accounts(response: Response):
    accounts = get_partneraccounts() 
    print(accounts)
    return {"accounts": accounts}

@app.get("/get_useraccounts")
def get_user_accounts():
    accounts = get_useraccounts() 
    print(accounts)
    return {"accounts": accounts}

@app.get("/get_unregpartneraccounts")
def get_unregpartner_accounts(response: Response):
    accounts = get_unregpartneraccounts() 
    print(accounts)
    return {"accounts": accounts}

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

    return {"message": "User activated successfully"}

@app.post("/suspend_user")
def suspend_partner_account( email : Email):
    user = email.email
    partner = get_user(user)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    result = suspend_user(user)
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to suspend partner")

    return {"message": "User suspended successfully"}


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

    return {"message": "Partner authenticated successfully"}

@app.post("/reject_partner")
def suspend_partner_account(email : Email):
    user = email.email
    partner = get_user(user)
    print(partner)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    result = reject_partner(user)
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to suspend partner")

    return {"message": "Partner rejected successfully"}

@app.post("/delete_category")
def del_category(category: Category):
    cat = category.category
    result = delete_category(cat)
    return result

@app.post("/add_categories")
def add_categories(category: Category):
    cat = category.category
    print(cat)
    result = add_category(cat)
    return result

@app.post("/edit_category")
def edit_categories(category: EditedCategory):
    new_cat=category.newCategory
    old_cat=category.oldCategory
    result = update_category(old_cat,new_cat)
    return result


# ================================================== PARTNER FUNCTIONS  ==================================================

@app.post("/update_product")
def update_product(product: UpdateProduct):
    print(product)
    product_id = product.product_id
    updated_data = product.dict(exclude={"product_id"})  # Exclude product_id from the updated data
    print(updated_data)
    print(product_id)
    result = updated_product(product_id, updated_data)
    return result

@app.post("/update_product_noimage")
def update_product(product: UpdateProductNoImage):
    print(product)
    product_id = product.product_id
    updated_data = product.dict(exclude={"product_id"})  # Exclude product_id from the updated data
    print(updated_data)
    print(product_id)
    result = updated_product(product_id, updated_data)
    return result

@app.post("/add_product")
def add_product(product: Product, response: Response):
    product_data = product.model_dump()
    put_product({'product_id': str(uuid4()), **product_data, 'clicks' : 0})
    return "Product added successfully"

@app.get("/get_average_rating/{product_id}")
def get_average_rating(product_id: str):
    result = get_averagerating(product_id)
    return result

# ================================================== RECOMMENDATION SYSTEM  ==================================================

@app.get('/recommendations/{user_id}')
async def get_recommendations(user_id: str):
    max_recommendations = 75  # You can modify this as needed
    try:
        recommendations = recommender.get_recommendations(user_id, max_recommendations)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enpoint to get You May Also Like
@app.get("/additional-recommendations/{user_id}")
async def get_additional_recommendations(user_id: str):
    # This endpoint returns only the next 1000 products not included in the initial recommendations
    additional_recommendations = recommender.get_additional_recommendations(user_id, 2)
    return {"additional_recommendations": additional_recommendations}

# ================================================== USER FUNCTIONS ==================================================

@app.get('/get_recommended_products/{product_id}')
def get_recommended_products(product_id: str, user_id: str = Query(...)):
    result = recommended_product(product_id, user_id)
    return result

@app.get('/get_recent_products/{product_id}')
def get_recent_products(product_id: str):
    result = get_bookmarks(product_id)
    return result

@app.get('/get_bookmarked_products/{product_id}')
def get_recommended_products(product_id: str):
    result = get_bookmarks(product_id)
    return result

@app.post("/add_rating")
def add_ratings(ratings: Rating):
    ratings.timestamp = int(time.time())
    result = add_rating(ratings)
    result_recent = update_recentlyviewed(ratings.user_id,ratings.product_id)
    return result, result_recent

@app.post('/add_bookmark')
def add_bookmark(bookmark : Bookmark):
    result = bookmark_product(bookmark.user_id,bookmark.product_id)
    return result

@app.post('/remove_bookmark')
def del_bookmark(bookmark : Bookmark):
    result = remove_bookmark(bookmark.user_id,bookmark.product_id)
    return result

@app.post('/add_count/{product_id}')
def add_count(product_id : str):
    result = increment_count(product_id)
    return result

@app.get('/get_bookmarked_items/{user_id}')
def get_bookmarked_items(user_id:str):
    result = retrieve_items(user_id)
    return result

@app.get('/get_recently_viewed/{user_id}')
def get_recently_viewed(user_id: str):
    result = retrieve_recentlyviewed(user_id)
    return result

@app.get("/get_products_by_category/{category}")
def get_products_by_category(category: str):
    print(category)
    result = get_product_by_category(category)
    return result 

# ================================================== UNIVERSAL FUNCTIONS ==================================================

@app.post("/get_products")
def get_product(user_id : userID):
    id=user_id.user_id
    products = get_products(id)
    return {"products": products}

@app.get("/get_allproducts") 
def get_all_products():
    products = get_allproducts()
    return {"products": products}

@app.get("/get_partner_name/{user_id}")
def get_partner_name(user_id: str):
   result = get_partnername(user_id)
   print(result)
   return result

@app.post("/delete_product/{product_id}")
def delete_product(product_id: str):
    result = del_product(product_id)
    return result  

@app.get('/get_allcategories')
def get_allcategories():
    result = retrieve_allcategories()
    return result

@app.get("/get_categories")
def get_categories(response: Response):
    categories = get_category()
    print(categories)
    return {"categories": categories}

@app.post("/get_userdetails")
def get_userdetails(email : Email):
    user = get_user(email.email)
    return {"accounts": user}
