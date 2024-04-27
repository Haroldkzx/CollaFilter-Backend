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

# user_ids = [str(uuid4()) for _ in range(500)]

# # Create a DataFrame with the user IDs
# df = pd.DataFrame({'user_id': user_ids})

# # Save the DataFrame to an Excel file
# df.to_excel('user_ids.xlsx', index=False)

