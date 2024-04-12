from typing import List
from pydantic import BaseModel


class LoginDetails(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    gender: str
    phone: str
    dob: str
    country: str
    role: str = "User"
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
    Category: str
    subCategory: List[str]

class Product(BaseModel):
    name: str
    price: str
    link: str
    description: str
    imageFile: str
    category: str
    subCategory: str
    email: str
    tags: list[str]

class Rating(BaseModel):
    email: str
    product_id: str
    rating: str

class SessionState(BaseModel):
    email: str
    role: str
    uuid: str

