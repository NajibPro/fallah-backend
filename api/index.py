import re
import jwt
from flask import Flask, jsonify, render_template, request
import os
from supabase import create_client, Client

app = Flask(__name__)

#this code is just for testing, i will remove it after
supabase_url = "https://fwxlhbkjtsondgcimfnu.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3eGxoYmtqdHNvbmRnY2ltZm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTIwMDY3MTksImV4cCI6MjAyNzU4MjcxOX0.aiBwRgMT2bU8qRgcFVcv0Xkdxf_b2vX1rWQ29y1n124"

# Retrieve Supabase URL and API key from environment variables must be done instead
#supabase_url = os.environ.get("SUPABASE_URL")
#supabase_key = os.environ.get("SUPABASE_KEY")


# Initialize Supabase client
supabase: Client = create_client(supabase_url, supabase_key)
                                            

@app.route('/login', methods=['POST'])
def login():
    # Get phone num and password from the request
    phone = request.json.get('phone')
    password = request.json.get('password')

    # Validate phone
    if not phone or len(phone) != 13 or phone[:4] != '+213' or not(phone[1:].isdigit()):
        return jsonify({'message': 'Invalid phone number format'}), 400
    
    # Validate password
    if not password or len(password) < 8:
        return jsonify({'message': 'Password should be at least 8 characters long'}), 400
    
    # Sign in the user with Supabase
    try:
        response = supabase.auth.sign_in_with_password({
            "phone": phone,
            "password": password,
        })

        # Check if the login was successful
        if 'error' in response:
            return jsonify({'message': 'Invalid credentials'}), 401

        # User login was successful
        res = supabase.auth.get_session()

        # Workaround using postgrest-py
        postgrest_client = supabase.postgrest
        postgrest_client.auth(res.access_token)

        # Retrieve profile data
        data, count = postgrest_client.table('profile').select("*").eq('id', res.user.id).execute()

        return jsonify({'message': 'Login successful', 'data': {"profile": data[0], 'access_token': res.access_token}}), 200

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/signup', methods=['POST'])
def signup():
    # Get phone num and password from the request
    phone = request.json.get('phone')
    password = request.json.get('password')
    username = request.json.get('username')
    longitude = request.json.get('longitude')
    latitude = request.json.get('latitude')

    # Validate phone
    if not phone or len(phone) != 13 or phone[:4] != '+213' or not(phone[1:].isdigit()):
        return jsonify({'message': 'Invalid phone number format'}), 400
    
    # Validate password
    if not password or len(password) < 8:
        return jsonify({'message': 'Password should be at least 8 characters long'}), 400
    
    # Validate longitude and latitude
    if longitude and latitude:
        if longitude < -180 or longitude > 180 or latitude < -90 or latitude > 90:
            return jsonify({'message': 'Invalid longitude or latitude range'}), 400


    # Sign in the user with Supabase
    try:
        response = supabase.auth.sign_up({
            "phone": phone,
            "password": password,
            "options": {
                "data": {
                    "username": username,
                    "longitude": longitude,
                    "latitude": latitude
                }
            }
        })

        # Check if the login was successful
        if 'error' in response:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Extract the fake/real user
        user = response.user


        return jsonify({'message': 'User created successfully', "data": {'user_id': user.id, 'profile': user.user_metadata}}), 200

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/sms_verify', methods=['POST'])
def sms_verify():
    # Get token num and password from the request
    phone = request.json.get('phone')
    token = str(request.json.get('token'))

    if(len(token) == 5):
        token = '0' + token

    # Validate phone
    if not phone or len(phone) != 13 or phone[:4] != '+213' or not phone[1:].isdigit():
        return jsonify({'message': 'Invalid phone number format'}), 400
    
    # Validate token
    if not token or len(token) != 6:
        return jsonify({'message': 'SMS token should be exactly 6 characters long'}), 400
    
    
    # Sign in the user with Supabase
    try:
        response = supabase.auth.verify_otp({
            "phone": phone,
            "token": token,
            "type": "sms"
        })

        # Check if the login was successful
        if 'error' in response:
            return jsonify({'message': 'Invalid credentials'}), 401

        res = supabase.auth.get_session()
        user = supabase.auth.get_user().user

        return jsonify({'message': 'User verfified successfully', "data": {"profile": user.user_metadata, 'access_token': res.access_token}}), 200
        

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/check_session', methods=['GET'])
def check_session():
    try:
        token = request.headers.get('Authorization')

        # Workaround using postgrest-py
        postgrest_client = supabase.postgrest
        postgrest_client.auth(token)

        if postgrest_client == None:
            return jsonify({"error": "Invalid or missing Authorization header"}), 401

        

        try:
            response = supabase.auth.get_user(token)
        except Exception as auth_error:
            return jsonify({'message': 'Invalid or expired access token', 'error': str(auth_error)}), 401
        
        if 'error' in response:
            return jsonify({'message': 'Invalid or expired access token'}), 401
        
        return jsonify({"message": "User is logged in", "data": {'user_id': response.user.id}}), 200
    

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)