import streamlit as st
import requests

API_BASE_URL = st.secrets.get(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

def get_request(endpoint: str):
    """
    Send GET request to FastAPI backend.
    """

    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to backend. Start FastAPI first."
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Backend request timed out."
        }

    except requests.exceptions.HTTPError as error:
        return {
            "error": f"API error: {error.response.text}"
        }

    except requests.exceptions.RequestException as error:
        return {
            "error": str(error)
        }


def post_request(endpoint: str, payload: dict):
    """
    Send POST request to FastAPI backend.
    """

    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to backend. Start FastAPI first."
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Backend request timed out."
        }

    except requests.exceptions.HTTPError as error:
        return {
            "error": f"API error: {error.response.text}"
        }

    except requests.exceptions.RequestException as error:
        return {
            "error": str(error)
        }
