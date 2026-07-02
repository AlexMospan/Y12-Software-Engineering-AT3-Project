from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory
from flask_cors import CORS
import json
import os
from google import genai

with open('API_Key.txt', 'r', encoding="utf-8") as file:
    API_key = file.read()
    clean_key = API_key.strip("[]'\"")
API_KEY = clean_key

client = genai.Client(api_key=API_KEY)
app = Flask(__name__)
CORS(app)

@app.route("/") 
def Home(): 
    return render_template("index.html")

@app.route('/save-input', methods=['POST'])
def save_input():
    received_data = request.get_json()
    chat_input_text = received_data.get("chatInput", "")
    
    print(f"Captured input from UI: {chat_input_text}")
    
    # Write to your data.json file
    with open("static\js\chatInputs.json", "w", encoding="utf-8") as file:
        json.dump({"chatInput": chat_input_text}, file, indent=4)
        
    return jsonify({"status": "success", "message": "Written to chatInputs.json!"})

@app.route('/response', methods=['POST'])
    def generate_response():
        user_input = input(chat_input_text)
    
        # Check if the user wants to leave
        if user_input.lower() in ['quit', 'exit']:
            print("Goodbye!")
            break
            
        # Skip empty messages
        if not user_input.strip():
            continue
            
        try:
            # Send the message and print the response
            response = chat_session.send_message(user_input)
            print(f"Onyx: {response.text}\n")
        except Exception as e:
            print(f"An error occurred: {e}\n")

@app.route("/login")
def login():
    user_id = session.get('id')

    if user_id:
        return redirect("/")
    if request.method == "POST": 
        username = request.form['username'] 
        password = request.form['password'] 

        user = db.CheckLogin(username, password) 
        if user: 

            session['id'] = user['id'] 
            session['username'] = user['username'] 
            
            return redirect("/")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)