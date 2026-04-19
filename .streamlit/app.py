from __future__ import annotations

import csv
import json
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import requests
import streamlit as st

st.set_page_config(page_title="QuickLoan Connect", page_icon="💳", layout="centered")

st.title("💳 QuickLoan Connect")
st.caption("Public loan request portal for multiple banks.")

st.markdown(
    """
Use this form to request a loan. You can see estimated EMI + total interest by years,
and after submission you receive owner notification by email/webhook when configured.
"""
)

LOAN_TYPES = [
    "Personal Loan",
    "Home Loan",
    "Business Loan",
    "Car Loan",
    "Education Loan",
]

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
LEADS_FILE = DATA_DIR / "leads.csv"
DEFAULT_OWNER_EMAIL = "muza1406u@gmail.com"


def get_secret(name: str, default: str = "") -> str:
    return str(st.secrets.get(name, default)).strip()


def calculate_loan(principal: float, annual_rate: float, years: int) -> dict[str, float]:
    months = max(1, years * 12)
    monthly_rate = annual_rate / (12 * 100)

    if monthly_rate == 0:
        emi = principal / months
    else:
        factor = (1 + monthly_rate) ** months
        emi = principal * monthly_rate * factor / (factor - 1)

    total_payment = emi * months
    total_interest = total_payment - principal
    return {
        "emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
    }


def send_webhook(payload: dict[str, Any]) -> tuple[bool, str]:
    webhook_url = get_secret("NOTIFY_WEBHOOK_URL")
    if not webhook_url:
        return False, "NOTIFY_WEBHOOK_URL is not set in Streamlit secrets."

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if 200 <= response.status_code < 300:
            return True, "Webhook notification sent successfully."
        return False, f"Webhook returned HTTP {response.status_code}."
    except requests.RequestException as exc:
        return False, f"Webhook call failed: {exc}"


def send_email_notification(payload: dict[str, Any]) -> tuple[bool, str]:
    smtp_host = get_secret("SMTP_HOST")
    smtp_port = int(get_secret("SMTP_PORT", "587") or 587)
    smtp_username = get_secret("SMTP_USERNAME")
    smtp_password = get_secret("SMTP_PASSWORD")
    smtp_from = get_secret("SMTP_FROM", smtp_username)
    smtp_to = get_secret("SMTP_TO", DEFAULT_OWNER_EMAIL)

    if not all([smtp_host, smtp_username, smtp_password, smtp_from]):
        return (
            False,
            "SMTP credentials are missing. Add SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD/SMTP_FROM in secrets.",
        )

    message = EmailMessage()
    message["Subject"] = "New Loan Enquiry - QuickLoan Connect"
    message["From"] = smtp_from
    message["To"] = smtp_to
    message.set_content(
        "\n".join(
            [
                "A new loan enquiry has been submitted.",
                "",
                f"Submitted at (UTC): {payload['submitted_at']}",
                f"Name: {payload['full_name']}",
                f"Phone: {payload['phone']}",
                f"Email: {payload['email']}",
                f"Loan Type: {payload['loan_type']}",
                f"Preferred Bank: {payload['preferred_bank']}",
                f"Loan Amount (INR): {payload['loan_amount']}",
                f"Annual Interest (%): {payload['annual_interest_rate']}",
                f"Tenure (years): {payload['tenure_years']}",
                f"Estimated EMI (INR): {payload['estimated_emi']}",
                f"Estimated Total Interest (INR): {payload['estimated_total_interest']}",
                f"Estimated Total Payment (INR): {payload['estimated_total_payment']}",
                f"Notes: {payload['notes']}",
                f"Consent: {payload['consent']}",
            ]
        )
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        return True, f"Email notification sent to {smtp_to}."
    except Exception as exc:  # noqa: BLE001
        return False, f"Email notification failed: {exc}"


def persist_lead(payload: dict[str, Any]) -> None:
    headers = list(payload.keys())
    file_exists = LEADS_FILE.exists()

    with LEADS_FILE.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(payload)


st.subheader("Interest & EMI Estimator")
calc_col1, calc_col2, calc_col3 = st.columns(3)
with calc_col1:
    calc_amount = st.number_input("Loan Amount (INR)", min_value=1000, value=10000, step=500)
with calc_col2:
    calc_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=8.5, step=0.1)
with calc_col3:
    calc_years = st.number_input("Tenure (Years)", min_value=1, value=5, step=1)

calc_result = calculate_loan(float(calc_amount), float(calc_rate), int(calc_years))
metric1, metric2, metric3 = st.columns(3)
metric1.metric("Estimated EMI / month", f"₹{calc_result['emi']:,.2f}")
metric2.metric("Total Interest", f"₹{calc_result['total_interest']:,.2f}")
metric3.metric("Total Payment", f"₹{calc_result['total_payment']:,.2f}")

preview_years = [1, 2, 3, 5, 7, 10, 15, 20, 30]
preview_rows = []
for years in preview_years:
    projected = calculate_loan(float(calc_amount), float(calc_rate), years)
    preview_rows.append(
        {
            "Years": years,
            "Monthly EMI (INR)": projected["emi"],
            "Total Interest (INR)": projected["total_interest"],
            "Total Payment (INR)": projected["total_payment"],
        }
    )

st.caption("Interest preview for the selected amount/rate across different year options")
st.table(preview_rows)

st.divider()
st.subheader("Loan Enquiry Form")
with st.form("loan_form", clear_on_submit=True):
    full_name = st.text_input("Full Name *")

    col1, col2 = st.columns(2)
    with col1:
        phone = st.text_input("Phone Number *")
    with col2:
        email = st.text_input("Email *")

    col3, col4 = st.columns(2)
    with col3:
        loan_type = st.selectbox("Loan Type *", options=[""] + LOAN_TYPES)
    with col4:
        preferred_bank = st.text_input("Preferred Bank", placeholder="Any bank / specific bank")

    col5, col6 = st.columns(2)
    with col5:
        loan_amount = st.number_input("Loan Amount (INR) *", min_value=1000, step=100)
    with col6:
        monthly_income = st.number_input("Monthly Income (INR) *", min_value=0, step=100)

    col7, col8 = st.columns(2)
    with col7:
        annual_interest_rate = st.number_input("Expected Annual Interest (%) *", min_value=0.0, value=8.5, step=0.1)
    with col8:
        tenure_years = st.number_input("Expected Tenure (Years) *", min_value=1, value=5, step=1)

    notes = st.text_area("Notes", placeholder="Share any details useful for your loan request")
    consent = st.checkbox("I agree to be contacted regarding this loan request.")

    submitted = st.form_submit_button("Submit Request")

if submitted:
    required_errors = []
    if not full_name.strip():
        required_errors.append("Full Name")
    if not phone.strip():
        required_errors.append("Phone Number")
    if not email.strip():
        required_errors.append("Email")
    if not loan_type:
        required_errors.append("Loan Type")
    if not consent:
        required_errors.append("Consent")

    if required_errors:
        st.error(f"Please complete required fields: {', '.join(required_errors)}")
    else:
        form_result = calculate_loan(float(loan_amount), float(annual_interest_rate), int(tenure_years))
        payload = {
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "full_name": full_name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "loan_type": loan_type,
            "preferred_bank": preferred_bank.strip() or "Any",
            "loan_amount": int(loan_amount),
            "monthly_income": int(monthly_income),
            "annual_interest_rate": round(float(annual_interest_rate), 2),
            "tenure_years": int(tenure_years),
            "estimated_emi": form_result["emi"],
            "estimated_total_interest": form_result["total_interest"],
            "estimated_total_payment": form_result["total_payment"],
            "notes": notes.strip(),
            "consent": consent,
        }

        persist_lead(payload)

        email_ok, email_message = send_email_notification(payload)
        webhook_ok, webhook_message = send_webhook(payload)

        if email_ok:
            st.success(email_message)
        else:
            st.warning(
                "Lead saved, but email notification was not sent. "
                f"Details: {email_message}"
            )

        if webhook_ok:
            st.success(webhook_message)
        else:
            st.info(f"Optional webhook status: {webhook_message}")

        st.success("Loan request submitted successfully.")
        with st.expander("View submitted payload"):
            st.code(json.dumps(payload, indent=2), language="json")

st.divider()
st.markdown(
    """
### Owner setup for your email (muza1406u@gmail.com)
In `.streamlit/secrets.toml`, configure SMTP and (optionally) webhook:

```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-gmail@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "your-gmail@gmail.com"
SMTP_TO = "muza1406u@gmail.com"
NOTIFY_WEBHOOK_URL = "https://your-webhook-url" # optional
```

For Gmail, create an App Password and use it as `SMTP_PASSWORD`.
"""
)
