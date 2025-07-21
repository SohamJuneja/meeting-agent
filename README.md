# 🚀 The Complete Meeting Agent

An autonomous AI assistant that handles the full meeting lifecycle, from pre-meeting preparation to post-meeting summaries and follow-ups.

## The Problem
Professionals are often unprepared for meetings, and after the meeting, key decisions and action items are often forgotten. This leads to inefficient work and missed opportunities.

## The Solution
This agent is a full-stack application that acts as a true meeting co-pilot:

1.  **Pre-Meeting Briefings (Preparation):** The agent connects to a user's Google Calendar and displays upcoming meetings. Before a meeting, it generates an AI-powered briefing by researching the attendees' company website and recent news, ensuring the user is always prepared.

2.  **Post-Meeting Summaries (Follow-up):** After a meeting, a user can upload an audio recording. The agent uses the Whisper model to transcribe the conversation, then leverages the **IO Intelligence API** to generate a concise summary of key decisions and action items, which it automatically emails to the specified recipients.

## How it Uses IO Intelligence
The core intelligence of this agent is powered by the **IO Intelligence Models API**. It uses the `meta-llama/Llama-3.3-70B-Instruct` model for two critical tasks:
* Synthesizing pre-meeting research into a strategic briefing.
* Distilling a long meeting transcript into a concise, actionable summary.

This demonstrates a powerful, end-to-end use case for AI in a professional workflow.

## Tech Stack
-   **Backend:** Python, Flask
-   **Frontend:** HTML, CSS, JavaScript
-   **Core AI:** IO Intelligence API
-   **Transcription:** OpenAI Whisper
-   **Data Sources:** Google Calendar API, Google Search
-   **Email:** smtplib