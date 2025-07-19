# agent.py
import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
from googlesearch import search # <-- New import

# ... (Keep existing setup code: load_dotenv, IO_API_KEY, etc.) ...
# ... (The get_calendar_service function remains the same) ...
load_dotenv()
IO_API_KEY = os.getenv("IO_API_KEY")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
FREE_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

io_client = openai.OpenAI(
    api_key=IO_API_KEY,
    base_url="https://api.intelligence.io.solutions/api/v1/",
)

def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

# UPDATED: This function now also searches for news
def research_company_and_news(attendees):
    # ... (The initial part of finding the domain is the same) ...
    if not attendees:
        yield "STATUS: No attendees found."
        return
    domain = None
    company_name_guess = "company" # Default search term
    for email in attendees:
        try:
            name, current_domain = email.split('@')
            if current_domain not in FREE_EMAIL_DOMAINS:
                domain = current_domain
                # Guess the company name from the domain for the news search
                company_name_guess = domain.split('.')[0].capitalize()
                break
        except IndexError:
            continue
    if not domain:
        yield "STATUS: No corporate domain found among attendees."
        return

    # 1. Scrape Website
    yield f"STATUS: Researching company website: {domain}..."
    try:
        response = requests.get(f"https://www.{domain}", timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        body_text = ' '.join(soup.body.get_text().split())
        website_content = body_text[:4000]
        yield "STATUS: Successfully scraped website content."
    except requests.RequestException:
        website_content = "Could not scrape website."
        yield f"STATUS: Could not scrape website {domain}."
    
    # 2. Search for News
    yield f"STATUS: Searching for recent news about {company_name_guess}..."
    try:
        query = f"{company_name_guess} news"
        news_results = [result for result in search(query, num_results=3, lang="en")]
        news_snippets = "\n - ".join(news_results)
        yield "STATUS: Found recent news articles."
    except Exception as e:
        news_snippets = "Could not fetch news articles."
        yield f"STATUS: Error fetching news: {e}"

    # 3. Yield final combined data
    yield f"DATA: {website_content}|||{news_snippets}"


# UPDATED: The prompt now includes the news section
def get_briefing_from_ai(meeting_details, company_research, news_snippets):
    yield "STATUS: Sending enhanced data to IO Intelligence AI..."
    
    prompt = f"""
    You are an expert executive assistant. Your task is to generate a concise, one-page meeting briefing.
    Use the provided context to structure your response with the following sections: "Company Snapshot", "Recent News", "Meeting Objective", and "Suggested Talking Points".
    If the news section is empty or irrelevant, intelligently omit it.

    **Context:**
    - Meeting Title: "{meeting_details['summary']}"
    - Attendees: {', '.join(meeting_details['attendees'])}
    - Raw company info scraped from their website: "{company_research}"
    - Recent news article links: "{news_snippets}"

    Generate the briefing now.
    """
    try:
        response = io_client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": "You are an expert executive assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        briefing = response.choices[0].message.content
        yield "STATUS: Deep Dive Briefing received from AI."
        yield f"DATA: {briefing}"
    except Exception as e:
        yield f"STATUS: Error calling IO Intelligence API: {e}"
        return