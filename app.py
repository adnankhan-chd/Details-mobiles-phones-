"""Phone Price Finder: upload a photo of a mobile phone and get an estimated price."""

import base64
import io
import json
import os
import re

import streamlit as st
from anthropic import Anthropic
from PIL import Image, ImageOps

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_SIDE = 1568  # longest image side sent to the model, in pixels
CURRENCIES = ["USD", "EUR", "GBP", "INR", "AED", "PKR", "NGN", "CAD", "AUD"]

PROMPT = """You are a mobile phone pricing expert. Look at the photo and identify the phone.

Return ONLY a JSON object (no markdown, no commentary) with these keys:
{
  "is_phone": true or false,
  "brand": string or null,
  "model": string or null,
  "condition": "like new" | "good" | "fair" | "poor" | null,
  "condition_notes": short string,
  "price_low": number or null,
  "price_high": number or null,
  "currency": "%(currency)s",
  "confidence": "high" | "medium" | "low",
  "notes": short string
}

Rules:
- If the image does not show a mobile phone, set is_phone to false and the rest to null.
- price_low and price_high are the typical USED market price range for this model
  in its visible condition, expressed in %(currency)s.
- If you cannot tell the exact model, give your best guess and lower the confidence.
- Never invent precision: these are estimates."""


def get_secret(name, default=None):
    """Read a setting from Streamlit secrets first, then environment variables."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass  # no secrets file present
    return os.environ.get(name, default)


def prepare_image(raw_bytes):
    """Fix rotation, shrink and re-encode as JPEG. Returns (base64_str, media_type)."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"


def parse_json(text):
    """Extract a JSON object from the model reply, tolerating code fences or extra text."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("The model did not return valid JSON.")
        return json.loads(match.group(0))


def estimate_price(client, model, raw_bytes, currency):
    """Send the photo to the model and return the parsed result dict."""
    data, media_type = prepare_image(raw_bytes)
    response = client.messages.create(
        model=model,
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": data},
                    },
                    {"type": "text", "text": PROMPT % {"currency": currency}},
                ],
            }
        ],
    )
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    return parse_json(text)


def fmt_money(value, currency):
    try:
        return f"{float(value):,.0f} {currency}"
    except (TypeError, ValueError):
        return "N/A"


def show_result(result, currency):
    if not result.get("is_phone"):
        st.warning("I couldn't see a mobile phone in this photo. Please try a clearer picture.")
        if result.get("notes"):
            st.caption(result["notes"])
        return

    name = " ".join(x for x in [result.get("brand"), result.get("model")] if x) or "Unknown phone"
    st.subheader(name)

    low, high = result.get("price_low"), result.get("price_high")
    if low is not None and high is not None:
        st.metric("Estimated price", f"{fmt_money(low, currency)} to {fmt_money(high, currency)}")
    else:
        st.info("I couldn't work out a price for this phone.")

    col1, col2 = st.columns(2)
    col1.write(f"**Condition:** {result.get('condition') or 'unknown'}")
    col2.write(f"**Confidence:** {result.get('confidence') or 'unknown'}")
    if result.get("condition_notes"):
        st.caption(result["condition_notes"])
    if result.get("notes"):
        st.caption(result["notes"])
    st.caption("This is an AI estimate of the used-market price, not an official valuation.")


def main():
    st.set_page_config(page_title="Phone Price Finder", page_icon="📱", layout="centered")
    st.title("📱 Phone Price Finder")
    st.write("Add a photo of your phone and get an estimated price.")

    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY is not set. Add it to your Streamlit secrets or environment.")
        st.stop()
    model = get_secret("ANTHROPIC_MODEL", DEFAULT_MODEL)

    currency = st.selectbox("Currency", CURRENCIES, index=0)

    tab_upload, tab_camera = st.tabs(["Upload / paste", "Take a photo"])
    with tab_upload:
        uploaded = st.file_uploader("Phone photo", type=["jpg", "jpeg", "png", "webp"])
    with tab_camera:
        camera = st.camera_input("Take a picture of your phone")

    photo = uploaded or camera
    if photo is None:
        return

    raw = photo.getvalue()
    st.image(raw, caption="Your photo", use_container_width=True)

    if st.button("Get price", type="primary"):
        try:
            with st.spinner("Identifying your phone..."):
                client = Anthropic(api_key=api_key)
                result = estimate_price(client, model, raw, currency)
            show_result(result, currency)
        except Exception as exc:  # show a friendly error instead of a stack trace
            st.error(f"Something went wrong: {exc}")


if __name__ == "__main__":
    main()
  
