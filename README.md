# 🚀 Automated Meeting Briefing Agent

An autonomous AI agent that acts as a personal executive assistant, ensuring you're perfectly prepared for every meeting.

## The Problem
Professionals are often in back-to-back meetings and lack the time to prepare. They walk in "cold," not remembering the context of the last conversation or the roles of the people they're meeting. This leads to inefficient meetings and missed opportunities.

## The Solution
This agent connects to your Google Calendar and displays your upcoming meetings. With a single click, it:
1.  **Identifies** the meeting attendees and their company.
2.  **Performs "Deep Dive" Research** by scraping the company website and searching Google News for recent articles.
3.  **Synthesizes the Data** using the IO Intelligence API to generate a concise, structured briefing.
4.  **Streams Progress Live** to the user, showing its work in real-time before presenting the final summary.

## How it Uses IO Intelligence
The core intelligence of this agent is powered by the **IO Intelligence Models API**. It uses the powerful `meta-llama/Llama-3.3-70B-Instruct` model to transform raw, unstructured data (website text, news links) into a professional, actionable briefing. This demonstrates a high-value, real-world use case for large language models in a practical, agentic workflow.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Core AI:** IO Intelligence API
- **Data Sources:** Google Calendar API, Google Search
- **Web Scraping:** Requests, BeautifulSoup

## How to Run It
1.  Set up a Python virtual environment and run `pip install -r requirements.txt`.
2.  Enable the Google Calendar API in the Google Cloud Console and download your `credentials.json`.
3.  Get your `IO_API_KEY` from your IO Intelligence account.
4.  Create a `.env` file with your `IO_API_KEY`.
5.  Run the Flask server: `python app.py`
6.  Open your browser to `http://127.0.0.1:5001`.