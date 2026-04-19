# QuickLoan Connect (Streamlit + GitHub)
This project is implemented in **Streamlit** and ready for **GitHub-based public deployment**.
Users can calculate interest in Indian Rupees (INR) by amount + years, submit a loan form, and owner notification is sent to email.
## What is included
Interest + EMI estimator in Indian Rupees (shows monthly EMI, total interest, total payment)
- Year-wise interest preview table in INR for selected amount/rate
- Loan enquiry form with validation
- Lead persistence to `data/leads.csv`
- Email notification support (SMTP) with default recipient `muza1406u@gmail.com`
- Optional webhook notification (`NOTIFY_WEBHOOK_URL`)
## Files

- `app.py` - Streamlit app (calculator + form + notifications)
- `requirements.txt` - dependencies
- `.streamlit/secrets.toml.example` - secrets template
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit secrets with your SMTP credentials
streamlit run app.py
```
## Email notification setup (Gmail)

Set these in `.streamlit/secrets.toml` (or Streamlit Cloud secrets):

```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-gmail@gmail.com"
SMTP_PASSWORD = "your-gmail-app-password"
SMTP_FROM = "your-gmail@gmail.com"
SMTP_TO = "muza1406u@gmail.com"
NOTIFY_WEBHOOK_URL = "https://your-webhook-url" # optional
```

> Gmail requires an **App Password** (not your normal account password).

## Deploy publicly from GitHub

1. Push this repository to GitHub.
2. Open [https://share.streamlit.io](https://share.streamlit.io).
3. Click **New app**, select your GitHub repo, and choose `app.py`.
4. Add your secrets in Streamlit Cloud settings.
5. Deploy and share your public app URL.

## Notes

- `data/leads.csv` is local runtime storage; production systems should use a database.
- Never commit real credentials in `.streamlit/secrets.toml`.
