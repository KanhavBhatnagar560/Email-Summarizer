import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone
from datetime import date
import os
import requests
from dotenv import load_dotenv

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels and prints a daily digest of unread emails from the last 24 hours."""
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("gmail", "v1", credentials=creds)
    threads_result = service.users().threads().list(
        userId="me",
        q="is:unread newer_than:1d -category:promotions -category:social",
        maxResults=50
    ).execute()

    threads = threads_result.get("threads", [])
    if not threads:
        print("No unread emails in last 24 hours.")
        return

    digest_items = []  

    # 3) Loop over threads
    for thread in threads:
        thread_data = service.users().threads().get(
            userId="me",
            id=thread["id"]
        ).execute()

        # 4) Extract latest subject & participants
        latest_message = thread_data["messages"][-1]
        latest_ts = int(latest_message.get("internalDate", "0")) / 1000.0
        date_field = datetime.fromtimestamp(latest_ts).astimezone().strftime("%Y-%m-%d %H:%M")
        subject = find_header(latest_message, "Subject")
        from_field = find_header(latest_message, "From")

        thread_text = ""
        for msg in thread_data["messages"][-3:]:  
            plain_text = extract_plain_text(msg["payload"]).strip()
            if not plain_text:
                continue
            thread_text += f"From: {find_header(msg, 'From')}\n{plain_text}\n\n"

        if not thread_text.strip():
            continue
        
        MAX_CHARACTERS = 10000
        if len(thread_text) > MAX_CHARACTERS:
            thread_text = thread_text[-MAX_CHARACTERS:] 
            
        summary = summarize_with_llm(thread_text)

        digest_items.append({
            "subject": subject,
            "from": from_field,
            "date": date_field,
            "summary": summary,
            "gmail_link": f"https://mail.google.com/mail/u/0/#inbox/{thread['id']}"
        })

    print("===== DAILY GMAIL DIGEST =====")
    for item in digest_items:
        print(f"Subject: {item['subject']}")
        print(f"From: {item['from']} — Date: {item['date']}")
        print(f"Summary:\n{item['summary']}")
        print(f"Open in Gmail: {item['gmail_link']}\n")

    filename = f"digest-{date.today()}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Daily Gmail Digest\n\n")
        for item in digest_items:
            f.write(f"## {item['subject']}\n")
            f.write(f"**From:** {item['from']} — {item['date']}\n\n")
            f.write(f"{item['summary']}\n\n")
            f.write(f"[Open in Gmail]({item['gmail_link']})\n\n")
    
  except HttpError as error:
      print(f"An error occurred: {error}")
    
    

# Helper functions
def find_header(message, header_name):
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header.get("name", "").lower() == header_name.lower():
            return header.get("value", "")
    return ""

def extract_plain_text(payload):
    import base64, quopri, re, html

    def b64url_decode(data):
        return base64.urlsafe_b64decode(data.encode("utf-8"))

    def decode_bytes(b):
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError:
            return quopri.decodestring(b).decode("utf-8", errors="ignore")
    
    def strip_html(s):
        s = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", s) 
        ss = re.sub(r"(?is)<a[^>]*>(.*?)</a>", r"\1", s)                
        s = re.sub(r"(?s)<[^>]+>", " ", s)                     
        return html.unescape(s)

    def find_parts(part, mime_wanted):
        mt = part.get("mimeType", "")
        body = part.get("body", {}) or {}
        if mt == mime_wanted and body.get("data"):
            yield part
        for sub in part.get("parts", []) or []:
            yield from find_parts(sub, mime_wanted)
    for p in find_parts(payload, "text/plain"):
        try:
            return decode_bytes(b64url_decode(p["body"]["data"])).strip()
        except Exception:
            pass  

    for p in find_parts(payload, "text/html"):
        try:
            html_text = decode_bytes(b64url_decode(p["body"]["data"]))
            return strip_html(html_text)
        except Exception:
            pass

    def first_text(part):
        body = part.get("body", {}) or {}
        if body.get("attachmentId"):
            return "" 
        if body.get("data"):
            try:
                return decode_bytes(b64url_decode(body["data"])).strip()
            except Exception:
                return ""
        for sub in part.get("parts", []) or []:
            t = first_text(sub)
            if t:
                return t
        return ""
    return first_text(payload)
    
def _clean_for_preview(s):
    import re
    s = re.sub(r'https?://\S+', '', s)       
    s = re.sub(r'\b[A-Za-z0-9_-]{25,}\b', '', s) 
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def summarize_with_llm(text):
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "[GROQ_API_KEY not set]"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",  # You can change to another Groq model if desired
        "messages": [
            {"role": "system", "content": "Summarize the following email thread in 3-5 sentences, focusing on the main points and action items."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 256,
        "temperature": 0.5
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Groq API error: {e}]"



if __name__ == "__main__":
  main()
  

