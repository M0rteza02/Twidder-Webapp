from flask import Flask, jsonify, request, send_from_directory
from flask_sock import Sock
from flask_bcrypt import Bcrypt
import hashlib
import database_helper
import re
import random
import hmac
import time


app = Flask(__name__, static_folder='static')
sock = Sock(app) #initialize the websocket
bcrypt = Bcrypt(app) #initialize the bcrypt
active_sessions = {} #dictionary to store active sessions

@app.route('/')
def serve_client():
    return send_from_directory('static', 'client.html')

# Helper functions and constants
MIN_PASSWORD_LENGTH = 8 
MAX_REQUEST_TIME = 300  # 5 minutes

class User:
    def __init__(self, email, password, firstname, lastname, gender, city, country):
        self.email = email
        self.password = password
        self.firstname = firstname
        self.lastname = lastname
        self.gender = gender
        self.city = city
        self.country = country

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$' #chek the email format using regex
    return re.match(email_regex, email) is not None

def check_email(email):
    data = database_helper.check_email(email)
    return data is None 

def generate_token(length=36):
    letters = 'abcdefghiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    return ''.join(random.choices(letters, k=length))

#---------------------------------------verify_request_signature----------------------------------------
def verify_request_signature(email, request_data, signature, timestamp):
    current_time = int(time.time())

    if current_time - timestamp > MAX_REQUEST_TIME:
        return False
    
    token = database_helper.getTokenByEmail(email)

    if not token:
        return False  
    
    #create a message by conbining the timestamp and the request data and then hash it
    message = f"{timestamp}.{request_data}"
    expected_signature = hmac.new(
        token.encode('utf-8'), 
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    #compare the expected signature with the signature in the request
    return hmac.compare_digest(signature, expected_signature)

#----------------------------------------websocket----------------------------------------
@sock.route("/ws")
def ws(ws):
    token = ws.receive() 
    email = database_helper.getEmailByToken(token)
    
    if not email:
        ws.close()
        return
    
    # Close any existing WebSocket connection for this user
    if email in active_sessions:
        try:
            active_sessions[email].send("logout")
            active_sessions[email].close()
        except Exception as e:
            print(f"Error closing old WebSocket for {email}: {e}")
    # Store the new WebSocket connection
    active_sessions[email] = ws

    # Listen for incoming messages
    try:
        while True:
            message = ws.receive()
            if not message:
                break 
    except:
        pass
    finally:
        # Remove the WebSocket connection when the connection is closed
        if active_sessions.get(email) == ws:
            del active_sessions[email]
        ws.close()

#----------------------------------------sign_up----------------------------------------
@app.route("/sign_up", methods=["POST"])
def sign_up():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    firstname = data.get("firstname")
    lastname = data.get("familyname")
    gender = data.get("gender")
    city = data.get("city")
    country = data.get("country")
    if request.method != "POST":
        return jsonify({"message": "Invalid request method"}), 405
    
    if not all([email, password, firstname, lastname, gender, city, country]): #check if all the required fields are present
        return jsonify({"message": "Missing required fields"}), 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"message": "Password must be at least 8 characters long"}), 400
    
    if not validate_email(email): #check if the email is in the correct format
        return jsonify({"message": "Invalid email"}), 400
    
    if not check_email(email): #check if the email is already registered
        return jsonify({"message": "Email already registered"}),409
    
    #hash the password before storing it in the database
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email, hashed_password, firstname, lastname, gender, city, country)

    try:
        if database_helper.add_user(new_user): #add the user to the database
            return jsonify({"message": "User created"}), 201
        else:
            return jsonify({"message": "Failed to create user"}), 500
    except Exception as e:
        return jsonify({"message": "Internal server error"}), 500
    

#----------------------------------------sign_in----------------------------------------
@app.route("/sign_in", methods=["POST"])
def sign_in():
    data = request.get_json()
    email = data.get("username")
    password = data.get("password")
    
    if request.method != "POST":
        return jsonify({"message": "Invalid request method"}), 405

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400
    
    if check_email(email):
        return jsonify({"message": "Email not registered"}), 401
    
    #check if the password is correct by comparing the hashed password in the database with the password entered by the user
    stored_password = database_helper.getPasswordByEmail(email)
    if not bcrypt.check_password_hash(stored_password, password):
        return jsonify({"message": "Wrong password"}), 401
    
    token = generate_token()

    if database_helper.add_session(email, token):
        return jsonify({"message": "User authenticated", "data": token}), 200
    else:
        return jsonify({"message": "Failed to authenticate user"}), 500

#----------------------------------------sign_out----------------------------------------
@app.route("/sign_out", methods=["DELETE"])
def sign_out():

    #get the raw data from the request for signature verification
    raw_data = request.data.decode('utf-8') if request.data else ""
    email = request.headers.get("email")
    timestamp = request.headers.get("Timestamp")
    signature = request.headers.get("Signature")
    
    if request.method != "DELETE":
        return jsonify({"message": "Invalid request method"}), 405
    
    if not email or not timestamp or not signature:
        return jsonify({"message": "Missing authentication headers"}), 400
    
    token = database_helper.getTokenByEmail(email)
    try:
        #verify the authenticity of the request and the time limit
        if not verify_request_signature(email, raw_data, signature, int(timestamp)):
            return jsonify({"message": "Invalid signature"}), 401
        
        #delete the session from the database and the active sessions dictionary
        database_helper.delete_session(token)
        if email in active_sessions:
            del active_sessions[email]
        return jsonify({"message": "User signed out"}), 200
    
    except Exception as e:
        return jsonify({"message": "An error occurred during sign out", "error": str(e)}), 500


#----------------------------------------change_password----------------------------------------
@app.route("/change_password", methods=["PUT"])
def change_password():
    data = request.get_json()
    raw_data = request.data.decode('utf-8') if request.data else ""
    email = request.headers.get("email")
    signature = request.headers.get("Signature")
    timestamp = request.headers.get("Timestamp")
    old_password = data.get("oldpassword")
    new_password = data.get("newpassword")
  
    if request.method != "PUT":
        return jsonify({"message": "Invalid request method"}), 405
    
    if not all([old_password, new_password, email, signature, timestamp]):
        return jsonify({"message": "Missing required fields"}), 400
    
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return jsonify({"message": "Password must be at least 8 characters long"}), 400
    try:
        token = database_helper.getTokenByEmail(email)
        if token is None:
            return jsonify({"message": "Invalid Email"}), 401
        

        if not verify_request_signature(email, raw_data, signature, int(timestamp)):
            return jsonify({"message": "Invalid signature"}), 401
    
        #check if the old password is correct by comparing the hashed password in the database with the password entered by the user
        stored_password = database_helper.getPasswordByEmail(email)
        if not bcrypt.check_password_hash(stored_password, old_password):
            return jsonify({"message": "Wrong password"}), 401
        
        #hash the new password before storing it in the database
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        if database_helper.change_password(email, hashed_password):
            return jsonify({"message": "Password changed"}), 200
        else:
            return jsonify({"message": "Failed to change password"}), 500
        
    except Exception as e:
        return jsonify({"message": "An error occurred during password change", "error": str(e)}), 500


#----------------------------------------get_user_data_by_token----------------------------------------
@app.route("/get_user_data_by_token", methods=["GET"])
def get_user_data_by_token():
    raw_data = request.data.decode('utf-8') if request.data else ""
    email = request.headers.get("email")
    signature = request.headers.get("Signature")
    timestamp = request.headers.get("Timestamp")

    if request.method != "GET":
        return jsonify({"message": "Invalid request method"}), 405
    try:
        token = database_helper.getTokenByEmail(email)

        if token is None:
            return jsonify({"message": "Missing token"}), 401
        
        if not verify_request_signature(email, raw_data, signature, int(timestamp)):
            return jsonify({"message": "Invalid signature"}), 401
        
        #get the user data from the database by email
        user_data = database_helper.getUserDataByEmail(email)
        if user_data is None:
            return jsonify({"message": "No user data found"}), 401
        else:
            return jsonify({"message": "User data retrieved", "data": user_data}), 200
        
    except Exception as e:
        return jsonify({"message": "An error occurred during user data retrieval", "error": str(e)}), 500
    
  
#----------------------------------------get_user_data_by_email----------------------------------------
@app.route("/get_user_data_by_email/<email>", methods=["GET"])
def get_user_data_by_email(email):
    raw_data = request.data.decode('utf-8')
    userEmail = request.headers.get("email")
    signature = request.headers.get("Signature")
    timestamp = request.headers.get("Timestamp")

    if request.method != "GET":
        return jsonify({"message": "Invalid request method"}), 405
    
    if not all([email, signature, timestamp]):
        return jsonify({"message": "Missing required fields"}), 400
    try:
        if not verify_request_signature(userEmail, raw_data, signature, int(timestamp)):
            return jsonify({"message": "Invalid signature"}), 401
        
        #check if the email is registered in the database
        if check_email(email):
            return jsonify({"message": "Email not registered"}), 401
        
        user_data = database_helper.getUserDataByEmail(email)

        if user_data is None:
            return jsonify({"message": "No user data found"}), 404
        else:
            return jsonify({"message": "User data retrieved", "data": user_data}), 200
        
    except Exception as e:
        return jsonify({"message": "An error occurred during user data retrieval", "error": str(e)}), 500


#----------------------------------------get_user_messages_by_token----------------------------------------
# get the messages of the user that is logged in

@app.route("/get_user_messages_by_token", methods=["GET"])
def get_user_messages_by_token():
    raw_data = request.data.decode('utf-8') if request.data else ""
    email = request.headers.get("email")
    signature = request.headers.get("Signature")
    timestamp = request.headers.get("Timestamp")

    if request.method != "GET":
        return jsonify({"message": "Invalid request method"}), 405
    
    if not all([email, signature, timestamp]):
        return jsonify({"message": "Missing required fields"}), 400
    
    try:
        if not verify_request_signature(email, raw_data, signature, int(timestamp)):
            return jsonify({"message": "Invalid signature"}), 401

        messages = database_helper.getMessagesByEmail(email)

        return jsonify({"message": "User messages retrieved", "data": messages}), 200
    
    except Exception as e:
        return jsonify({"message": "An error occurred during message retrieval", "error":str(e)}),500


#----------------------------------------get_user_messages_by_email----------------------------------------
@app.route("/get_user_messages_by_email/<email>", methods=["GET"])
def get_user_messages_by_email(email):
    raw_data = request.data.decode('utf-8')
    UserEmail = request.headers.get("email")
    signature = request.headers.get("Signature")
    timestamp = request.headers.get("Timestamp")

    if request.method != "GET":
        return jsonify({"message": "Invalid request method"}), 405
    
    if not all([email, signature, timestamp]):
        return jsonify({"message": "Missing required fields"}), 400
    
    try:
        if not verify_request_signature(UserEmail, raw_data, signature, int(timestamp)):
            return jsonify({"message": "Invalid signature"}), 401
        
        if check_email(email):
            return jsonify({"message": "Email not registered"}), 404
        
        #get the messages from the database by email
        messages = database_helper.getMessagesByEmail(email)

        return jsonify({"message": "User messages retrieved", "data": messages}), 200
    
    except Exception as e:
        return jsonify({"message": "An error occurred during message retrieval", "error": str(e)}), 500


#----------------------------------------post_message----------------------------------------
@app.route("/post_message", methods=["POST"])
def post_message():
    data = request.get_json()
    raw_data = request.data.decode('utf-8') if request.data else ""
    UserEmail = request.headers.get("email")
    signature = request.headers.get("Signature")
    timestamp = request.headers.get("Timestamp")
    message = data.get("message")
    recipient = data.get("email")

    if request.method != "POST":
        return jsonify({"message": "Invalid request method"}), 405
    
    if not message:
        return jsonify({"message": "Missing message"}), 400
    
    #check if the recipient is registered in the database
    if recipient and check_email(recipient):
        return jsonify({"message": "Recipient not registered"}), 404
    
    try:
        
        if not verify_request_signature(UserEmail, raw_data, signature, int(timestamp)):
            return jsonify({"message": "Invalid signature"}), 401
        
        #modify the message to include the name of the sender and the recipient
        if UserEmail == recipient:
            modified_message = "Me: " + message
        else:
            userdata = database_helper.getUserDataByEmail(UserEmail)
            recipient_name = userdata["firstname"] + " " + userdata["lastname"]
            modified_message = recipient_name + ": " + message
        
        #add the message to the database
        database_helper.add_message(UserEmail, recipient, modified_message)

        return jsonify({"message": "Message posted"}), 200
    except Exception as e:
        return jsonify({"message": "An error occurred during message posting", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
