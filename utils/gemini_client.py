import os
import time
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

def get_api_key():
    try:
        import streamlit as st
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

def is_rate_limit_error(exception):
    return "429" in str(exception) or "RESOURCE_EXHAUSTED" in str(exception)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=10, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def generate_with_retry(prompt: str, model: str = "gemini-2.0-flash") -> str:
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text

def safe_generate(prompt: str, fallback: str = "", model: str = "gemini-2.0-flash") -> str:
    try:
        return generate_with_retry(prompt, model)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            time.sleep(5)
            try:
                return generate_with_retry(prompt, model)
            except:
                return fallback if fallback else "⏳ Gemini şu an meşgul, lütfen birkaç saniye bekleyip tekrar deneyin."
        return fallback if fallback else f"Yanıt üretilemiyor: {error_str[:100]}"