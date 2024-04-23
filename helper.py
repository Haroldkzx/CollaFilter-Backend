# helper.py
import bcrypt
import secrets


def hash_password(password):
    # Generate a salt and hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password


def isValidPassword(input_password, hashed_password):
    # Check if the input password matches the hashed password
    input_password_bytes = input_password.encode('utf-8')

    # Check if the input password matches the hashed password
    return bcrypt.checkpw(input_password_bytes, hashed_password)

def generate_unique_token():
    return secrets.token_urlsafe(20) #make longer to decrease randomness


