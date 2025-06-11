
import streamlit as st
from streamlit import session_state as sst

from frontend.settings import settings


def authenticate():
    """Handle authentication using the APP_PASSWORD from settings."""
    # Check if we're already authenticated
    if "authenticated" not in sst:
        sst["authenticated"] = False

    if sst["authenticated"]:
        return True

    # Get password from settings
    password = settings.app_password

    if not password:
        st.error("Keine APP_PASSWORD in den Umgebungsvariablen gefunden. Bitte überprüfen Sie Ihre .env-Datei.")
        st.stop()

    # Create a login container with better spacing
    _, center_col, _ = st.columns([1, 10, 1])

    with center_col:
        st.title("PureChat Login")

        password_placeholder = st.empty()
        entered_password = password_placeholder.text_input("Passwort", type="password")

        if entered_password:
            if entered_password == password:
                # Set authentication state
                sst["authenticated"] = True
                # Use rerun to refresh the page
                st.rerun()
            else:
                st.error("Falsches Passwort! Bitte versuchen Sie es erneut.")

    # Stop execution if not authenticated
    if not sst["authenticated"]:
        st.stop()

    return True
