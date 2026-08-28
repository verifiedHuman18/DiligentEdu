import os

import firebase_admin
import requests
from dotenv import load_dotenv
from firebase_admin import auth, credentials

load_dotenv()

FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")


def init_firebase():
    """Initializes the Firebase Admin SDK if not already initialized."""
    if not firebase_admin._apps:
        cred_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "firebase-adminsdk.json"
        )

        # 1. Try to load from local file first
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # 2. Try to load from Streamlit Secrets
            try:
                import streamlit as st

                if "firebase" in st.secrets:
                    # Convert AttrDict to normal dict for Firebase
                    firebase_creds = dict(st.secrets["firebase"])
                    # Ensure private key is formatted correctly with newlines
                    if "private_key" in firebase_creds:
                        firebase_creds["private_key"] = firebase_creds["private_key"].replace(
                            "\\n", "\n"
                        )

                    cred = credentials.Certificate(firebase_creds)
                    firebase_admin.initialize_app(cred)
                    return
            except Exception:
                pass

            raise FileNotFoundError(
                f"Firebase credentials not found at {cred_path} and not in Streamlit Secrets"
            )


def sign_in_with_email_and_password(email, password):
    """Signs in a user using Firebase REST API and returns the user data including idToken."""
    if not FIREBASE_WEB_API_KEY:
        raise ValueError("FIREBASE_WEB_API_KEY is not set in environment variables.")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        raise Exception(f"Login failed: {error_message}")


def verify_token(id_token):
    """Verifies a Firebase ID token using the Admin SDK."""
    init_firebase()
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise Exception(f"Token verification failed: {e}")


def get_user_by_uid(uid):
    """Fetches user details from Firebase Admin SDK."""
    init_firebase()
    try:
        return auth.get_user(uid)
    except Exception as e:
        raise Exception(f"Failed to fetch user: {e}")
