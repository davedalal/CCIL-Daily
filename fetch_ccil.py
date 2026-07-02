
import smtplib
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# --- Config -------------------------------------------------------------

# Pages to check for the current day's Daily Market Analytics link.
# Update/add URLs here if CCIL restructures their site.
CANDIDATE_PAGES = [
"https://www.ccilindia.com/researchintroduction",
"https://www.ccilindia.com/analytics",
]

# IST is UTC+5:30, no DST
IST = timezone(timedelta(hours=5, minutes=30))

REQUEST_HEADERS = {
# A normal-looking browser UA reduces the chance of being blocked.
"User-Agent": (
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
"(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
}

TIMEOUT = 20 # seconds per request


# --- Helpers --------------------------------------------------------------

def today_ist():
return datetime.now(IST)


def date_tokens(dt):
"""Return a few plausible date-string formats CCIL might embed in filenames."""
return {
dt.strftime("%d_%m_%y"), # 25_06_26
dt.strftime("%d_%m_%Y"), # 25_06_2026
dt.strftime("%d-%m-%y"),
dt.strftime("%d%m%y"),
}


def find_pdf_link(page_url, dt):
"""
Fetch a page and look for an <a> tag whose href:
- ends in .pdf
- contains something like 'DAILY_ANALYSIS' or 'daily-market-analytics'
- AND contains today's date in one of the expected formats
Returns the absolute PDF URL, or None if not found on this page.
"""
resp = requests.get(page_url, headers=REQUEST_HEADERS, timeout=TIMEOUT)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

tokens = date_tokens(dt)
candidates = []

for a in soup.find_all("a", href=True):
href = a["href"]
if not href.lower().endswith(".pdf"):
continue
label = (a.get_text() or "") + " " + href
label_upper = label.upper()

looks_like_daily_analytics = (
"DAILY_ANALYSIS" in label_upper
or "DAILY MARKET ANALYTIC" in label_upper
or "DMA" in label_upper
)
if not looks_like_daily_analytics:
continue

candidates.append(href)

if not candidates:
return None

# Prefer a candidate whose href/text contains today's date token
for href in candidates:
if any(tok in href for tok in tokens):
return urljoin(page_url, href)

# Fall back: if there's exactly one Daily Analytics link on the page,
# assume it's today's (some pages only show the latest report).
if len(candidates) == 1:
return urljoin(page_url, candidates[0])

return None


def download_pdf(pdf_url):
resp = requests.get(pdf_url, headers=REQUEST_HEADERS, timeout=TIMEOUT)
resp.raise_for_status()
content_type = resp.headers.get("Content-Type", "")
if "pdf" not in content_type.lower() and not pdf_url.lower().endswith(".pdf"):
raise ValueError(f"Downloaded content doesn't look like a PDF (Content-Type: {content_type})")
return resp.content


def send_email(subject, body, attachment_bytes=None, attachment_name=None):
user = os.environ["EMAIL_USER"]
password = os.environ["EMAIL_APP_PASSWORD"]
recipient = os.environ["RECIPIENT_EMAIL"]

msg = EmailMessage()
msg["Subject"] = subject
msg["From"] = user
msg["To"] = recipient
msg.set_content(body)

if attachment_bytes is not None:
msg.add_attachment(
attachment_bytes,
maintype="application",
subtype="pdf",
filename=attachment_name,
)

with smtplib.SMTP("smtp.office365.com", 587) as smtp:
smtp.starttls()
smtp.login(user, password)
smtp.send_message(msg)


# --- Main -------------------------------------------------------------

def main():
dt = today_ist()
date_str = dt.strftime("%d %b %Y")

pdf_url = None
for page in CANDIDATE_PAGES:
try:
pdf_url = find_pdf_link(page, dt)
except requests.RequestException as e:
print(f"Warning: failed to fetch {page}: {e}", file=sys.stderr)
continue
if pdf_url:
print(f"Found PDF link on {page}: {pdf_url}")
break

if not pdf_url:
msg = (
f"Could not locate today's ({date_str}) Daily Market Analytics PDF "
f"on any of: {', '.join(CANDIDATE_PAGES)}. "
"The site structure may have changed, or the report isn't published yet."
)
print(msg, file=sys.stderr)
try:
send_email(f"CCIL Pull Failed – {date_str}", msg)
except Exception as e:
print(f"Also failed to send failure-notification email: {e}", file=sys.stderr)
sys.exit(1)

try:
pdf_bytes = download_pdf(pdf_url)
except Exception as e:
msg = f"Found the PDF link ({pdf_url}) but failed to download it: {e}"
print(msg, file=sys.stderr)
try:
send_email(f"CCIL Pull Failed – {date_str}", msg)
except Exception as e2:
print(f"Also failed to send failure-notification email: {e2}", file=sys.stderr)
sys.exit(1)

filename = f"CCIL_Daily_Market_Analytics_{dt.strftime('%d_%m_%Y')}.pdf"

try:
send_email(
subject=f"CCIL Daily Market Analytics – {date_str}",
body=f"Fetched successfully from {pdf_url}",
attachment_bytes=pdf_bytes,
attachment_name=filename,
)
print("Email sent successfully.")
except Exception as e:
print(f"Failed to send the report email: {e}", file=sys.stderr)
sys.exit(1)


if __name__ == "__main__":
main()
