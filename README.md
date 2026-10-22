# 📱 Phone Price Finder

A Streamlit app where users upload (or paste, or take) a photo of their mobile phone and get an
estimated used-market price. The photo is analysed by Claude, which identifies the phone, judges
its condition and returns a price range.

> Prices are AI estimates, not official valuations.

## Files
- `app.py` – the Streamlit app
- `requirements.txt` – Python dependencies
- `README.md` – this file

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"   # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
streamlit run app.py
```

Alternatively, create `.streamlit/secrets.toml` (never commit it):
```toml
ANTHROPIC_API_KEY = "your-key"
# ANTHROPIC_MODEL = "claude-sonnet-5-5"   # optional override
```

## Deploy on Streamlit Community Cloud
1. Push this repo to GitHub.
2. Go to https://share.streamlit.io and click **Create app**.
3. Select the repo, branch `main`, and main file `app.py`.
4. Open **Advanced settings > Secrets** and add `ANTHROPIC_API_KEY = "your-key"`.
5. Click **Deploy**.

## Notes
- Users can upload a file, paste one into the uploader (on supported browsers), or use the camera tab on mobile.
- Images are resized to at most 1568 px before being sent, which keeps requests fast and cheap.
- Add `.streamlit/secrets.toml` and `.venv/` to `.gitignore`.
- # Details-mobiles-phones-
