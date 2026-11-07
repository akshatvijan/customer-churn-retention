import os
import streamlit as st
import requests

def _resolve_api_base_url() -> str:
    # 1. Environment variable (Render, Railway, Docker, Streamlit Cloud env var)
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")

    # 2. Streamlit secrets (.streamlit/secrets.toml)
    try:
        if hasattr(st, "secrets") and "API_BASE_URL" in st.secrets:
            return str(st.secrets["API_BASE_URL"]).rstrip("/")
    except Exception:
        pass

    # 3. Default local FastAPI server
    return "http://127.0.0.1:8000"

API_BASE_URL = _resolve_api_base_url()

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
