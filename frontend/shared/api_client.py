import os
import streamlit as st
import requests

def _resolve_api_base_url() -> str:
    # 0. User override in Streamlit session state
    try:
        if hasattr(st, "session_state") and st.session_state.get("custom_api_base_url"):
            val = str(st.session_state["custom_api_base_url"]).strip()
            if val:
                return val.rstrip("/")
    except Exception:
        pass

    # 1. Environment variable (Render, Railway, Docker, Streamlit Cloud env var)
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")

    # 2. Streamlit secrets (.streamlit/secrets.toml)
    try:
        if hasattr(st, "secrets"):
            if "API_BASE_URL" in st.secrets:
                return str(st.secrets["API_BASE_URL"]).rstrip("/")
            if "api_base_url" in st.secrets:
                return str(st.secrets["api_base_url"]).rstrip("/")
            if "general" in st.secrets and "API_BASE_URL" in st.secrets["general"]:
                return str(st.secrets["general"]["API_BASE_URL"]).rstrip("/")
    except Exception:
        pass

    # 3. Default local FastAPI server
    return "http://127.0.0.1:8000"

def _format_http_error(error: requests.exceptions.HTTPError) -> str:
    status_code = getattr(error.response, "status_code", "Unknown")
    text = ""
    try:
        data = error.response.json()
        if isinstance(data, dict):
            if "detail" in data:
                text = str(data["detail"])
            elif "error" in data:
                text = str(data["error"])
            elif "message" in data:
                text = str(data["message"])
    except Exception:
        text = getattr(error.response, "text", "")

    if not text:
        reason = getattr(error.response, "reason", "")
        if status_code in (502, 503, 504):
            text = f"{reason or 'Service Unavailable'}. The backend server may be waking up from a cold start, deploying, or restarting. Please try again in 30 seconds."
        else:
            text = reason or "Server returned an empty error response"
    elif text.strip().startswith("<!DOCTYPE") or text.strip().startswith("<html"):
        reason = getattr(error.response, "reason", "Bad Gateway")
        text = f"{reason}. The backend server is currently starting up, deploying, or temporarily unavailable. Please wait 1-2 minutes and retry."

    return f"API error ({status_code}): {text}"

def get_request(endpoint: str):
    """
    Send GET request to FastAPI backend.
    """
    base_url = _resolve_api_base_url()
    try:
        response = requests.get(
            f"{base_url}{endpoint}",
            timeout=45
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        return {
            "error": f"Cannot connect to backend at {base_url}. Ensure FastAPI is running and accessible."
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Backend request timed out."
        }

    except requests.exceptions.HTTPError as error:
        return {
            "error": _format_http_error(error)
        }

    except requests.exceptions.RequestException as error:
        return {
            "error": str(error)
        }


def post_request(endpoint: str, payload: dict):
    """
    Send POST request to FastAPI backend.
    """
    base_url = _resolve_api_base_url()
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        return {
            "error": f"Cannot connect to backend at {base_url}. Ensure FastAPI is running and accessible."
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Backend request timed out after 180 seconds. The server might be under heavy load."
        }

    except requests.exceptions.HTTPError as error:
        return {
            "error": _format_http_error(error)
        }

    except requests.exceptions.RequestException as error:
        return {
            "error": str(error)
        }
