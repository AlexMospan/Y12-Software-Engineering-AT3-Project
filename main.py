from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from google import genai
import database as db

# Initialize database file
db.init_db()

with open('API_Key.txt', 'r', encoding="utf-8") as file:
    API_KEY = file.read().strip("[]'\" ")

client = genai.Client(api_key=API_KEY)
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Keep session cookies secure and active
CORS(app)

@app.route("/") 
def Home():
    if 'user_id' in session:
        user_chats = db.get_user_chats(session['user_id'])
        return render_template("index.html", username=session.get('username'), chats=user_chats, logged_in=True)
    else:
        return render_template("index.html", username="Guest", chats=[], logged_in=False)

@app.route("/auth")
def auth_page():
    if 'user_id' in session:
        return redirect(url_for('Home'))
    return render_template("auth.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Missing credentials."}), 400
        
    if db.register_user(username, password):
        return jsonify({"status": "success", "message": "User registered successfully!"})
    return jsonify({"status": "error", "message": "Username already exists."}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    user = db.check_login(username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({"status": "success", "redirect": url_for('Home')})
    return jsonify({"status": "error", "message": "Invalid username or password."}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('Home')) # Redirects to Home page so they go back to Guest view

# --- Chat & History REST API endpoints ---

@app.route("/chat/new", methods=["POST"])
def new_chat():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    chat_id = db.create_new_chat(session['user_id'])
    return jsonify({"status": "success", "chat_id": chat_id})

@app.route("/chat/<int:chat_id>/messages", methods=["GET"])
def get_messages(chat_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    rows = db.get_chat_messages(chat_id)
    messages = [{"sender": r["sender"], "content": r["content"]} for r in rows]
    return jsonify({"status": "success", "messages": messages})

@app.route('/save-input', methods=['POST'])
def save_input():
    received_data = request.get_json() or {}
    chat_input_text = received_data.get("chatInput", "").strip()
    chat_id = received_data.get("chatId")
    
    if not chat_input_text:
        return jsonify({"status": "error", "message": "Empty query text"}), 400

    user_id = session.get('user_id')

    # --- GUEST LOGIC ---
    if not user_id:
        onyx_reply = ""
        try:
            chat = client.chats.create(model="gemini-3.1-flash-lite")
            response = chat.send_message(chat_input_text)
            onyx_reply = response.text
        except Exception as e:
            onyx_reply = f"An error occurred executing context stream: {e}"
        
        return jsonify({
            "status": "success",
            "chat_id": None,
            "reply": onyx_reply
        })

    # --- REGISTERED USER LOGIC ---
    # Automatically provision a thread fallback context line if none provided
    if not chat_id:
        chat_id = db.create_new_chat(user_id, title=chat_input_text[:20])
    else:
        # If it's a first message or generic title, update the thread name context natively
        existing_msgs = db.get_chat_messages(chat_id)
        if len(existing_msgs) == 0:
            db.update_chat_title(chat_id, chat_input_text[:20])

    # Log user input securely inside SQLite state rows
    db.add_message(chat_id, "user", chat_input_text)
    
    onyx_reply = ""
    try:
        # Rehydrate localized dynamic session context histories cleanly for Gemini
        history_rows = db.get_chat_messages(chat_id)
        api_history = []
        for row in history_rows[:-1]: # Include previous messages up to this one
            role_map = "user" if row["sender"] == "user" else "model"
            api_history.append({"role": role_map, "parts": [{"text": row["content"]}]})
            
        # Spin dynamic isolated ephemeral client loop using gemini-3.1-flash-lite
        chat = client.chats.create(model="gemini-3.1-flash-lite", history=api_history)
        response = chat.send_message(chat_input_text)
        onyx_reply = response.text
        
        # Save structural responses back onto tracking frameworks
        db.add_message(chat_id, "bot", onyx_reply)
    except Exception as e:
        onyx_reply = f"An error occurred executing context stream: {e}"
        db.add_message(chat_id, "bot", onyx_reply)
        
    return jsonify({
        "status": "success",
        "chat_id": chat_id,
        "reply": onyx_reply
    })

if __name__ == "__main__":
    app.run(debug=True)