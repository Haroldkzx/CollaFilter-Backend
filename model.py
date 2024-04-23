from typing import List
from pydantic import BaseModel


class LoginDetails(BaseModel):
    email: str
    password: str
 
class Email(BaseModel):
    email: str

class userID(BaseModel):
    user_id: str

class Partner(BaseModel):
    name: str
    email: str
    UEN: str
    phone: str
    doe: str
    category: str
    link: str
    country: str

class UpdateUserData(BaseModel):
    name: str
    dob: str
    email: str
    phone: str
    country: str

class User(BaseModel):
    name: str
    email: str
    phone: str
    dob: str
    country: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    gender: str
    phone: str
    dob: str
    country: str
    role: str = "User"
    authenticate: str = "0"
    suspended: str = "0"

class PartnerRegister(BaseModel):
    name: str
    email: str
    password: str
    UEN: str
    phone: str
    doe: str
    category: str
    link: str
    country: str
    role: str = "Partner"
    authenticate: str = "0"
    suspended: str = "0"

class Category(BaseModel):
    category: str

class EditedCategory(BaseModel):
    newCategory: str
    oldCategory: str

class Product(BaseModel):
    name: str
    price: str
    link: str
    description: str
    imageFile: str
    category: str
    email: str
    user_id: str

class Rating(BaseModel):
    email: str
    product_id: str
    rating: str

class SessionState(BaseModel):
    email: str
    role: str
    uuid: str

class Resets(BaseModel):
    token: str
    newpassword: str

class ForgetPasswordRequest(BaseModel):
    email: str

class ConnectionConfig(BaseModel):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_TLS : bool
    MAIL_SSL : bool

class UpdatedUserData(BaseModel):
    name: str
    phone: str
    country: str
   