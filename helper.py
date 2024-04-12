# helper.py
import bcrypt



def hash_password(password):
    # Generate a salt and hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password


def isValidPassword(input_password, hashed_password):
    # Check if the input password matches the hashed password
    input_password_bytes = input_password.encode('utf-8')

    # Decode hashed_password from string to bytes
    hashed_password_bytes = hashed_password.encode('utf-8')

    # Check if the input password matches the hashed password
    return bcrypt.checkpw(input_password_bytes, hashed_password_bytes)