from flask import Flask, jsonify, render_template, Response, request, redirect, url_for, session
import os
import datetime
import time
import whisper
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google Auth Libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Import from our agent module
from agent import research_company_and_news, get_briefing_from_ai

app = Flask(__name__)
# A secret key is required for session management
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Helper function to get Google credentials from the session ---
def credentials_from_session():
    if 'credentials' not in session:
        return None
    return Credentials(**session['credentials'])

def get_calendar_service_from_session():
    creds = credentials_from_session()
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds)


# --- Login, Logout, and Auth Callback Routes ---
@app.route('/login')
def login():
    # Note: Use a client_secrets file ('credentials.json') for this flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )
    # This must match the URI in your Google Cloud Console
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        scopes=['https.googleapis.com/auth/calendar.readonly'],
        state=state
    )
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    
    credentials = flow.credentials
    # Store credentials in the session
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('credentials', None)
    return redirect(url_for('home'))


# --- Page Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/briefing/<meeting_id>')
def show_briefing_page(meeting_id):
    if 'credentials' not in session: return redirect(url_for('home'))
    service = get_calendar_service_from_session()
    meeting = service.events().get(calendarId='primary', eventId=meeting_id).execute()
    return render_template('briefing.html', meeting=meeting)

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/results')
def results_page():
    summary = request.args.get('summary', 'No summary was generated.')
    return render_template('results.html', summary=summary)


# --- API & Streaming Routes ---
@app.route('/api/check-login')
def check_login():
    return jsonify({"logged_in": 'credentials' in session})

@app.route('/api/get-meetings', methods=['GET'])
def get_meetings_endpoint():
    if 'credentials' not in session: return jsonify({"error": "User not logged in"}), 401
    service = get_calendar_service_from_session()
    if not service: return jsonify({"error": "Authentication failed"}), 500
    
    now = datetime.datetime.now(datetime.UTC).isoformat()
    events_result = service.events().list(
        calendarId="primary", timeMin=now, maxResults=10,
        singleEvents=True, orderBy="startTime"
    ).execute()
    return jsonify(events_result.get("items", []))

@app.route('/stream-briefing/<meeting_id>')
def stream_briefing(meeting_id):
    if 'credentials' not in session: return Response("data: STATUS: Error - Not logged in.\n\ndata: DONE\n\n", mimetype='text/event-stream')
    
    def generate():
        service = get_calendar_service_from_session()
        meeting = service.events().get(calendarId='primary', eventId=meeting_id).execute()
        meeting_details = {
            "summary": meeting.get("summary", "No Title"),
            "attendees": [attendee['email'] for attendee in meeting.get('attendees', []) if 'resource' not in attendee]
        }
        yield f"data: STATUS: Found meeting: {meeting_details['summary']}\n\n"
        # ... (rest of the generator logic is the same)
        time.sleep(1)
        research_data = None
        for update in research_company_and_news(meeting_details["attendees"]):
            yield f"data: {update}\n\n"
            time.sleep(1)
            if update.startswith("DATA:"): research_data = update[6:]
        if not research_data:
            yield "data: DONE\n\n"
            return
        website_content, news_snippets = research_data.split('|||')
        briefing_text = None
        for update in get_briefing_from_ai(meeting_details, website_content, news_snippets):
            yield f"data: {update}\n\n"
            time.sleep(1)
            if update.startswith("DATA:"): briefing_text = update[6:]
        if briefing_text:
            yield f"event: final_briefing\ndata: {briefing_text.replace('\n', '|||')}\n\n"
        yield "data: DONE\n\n"
    return Response(generate(), mimetype='text/event-stream')


# --- Routes for POST-MEETING Audio Processing ---
@app.route('/process-recording', methods=['POST'])
def process_recording():
    # ... (the logic for this function remains the same as before)
    if 'audio_file' not in request.files: return "No file part", 400
    file = request.files['audio_file']
    recipients = request.form['recipients']
    if file.filename == '': return "No selected file", 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        model = whisper.load_model("tiny")
        result = model.transcribe(filepath, fp16=False)
        summary = summarize_transcript(result["text"])
        send_summary_email(recipients, summary)
        os.remove(filepath)
        return redirect(url_for('results_page', summary=summary))
    return redirect(url_for('upload_page'))

def summarize_transcript(transcript):
    from agent import io_client
    prompt = f'Summarize the key decisions and action items from this meeting transcript: "{transcript}"'
    response = io_client.chat.completions.create(model="meta-llama/Llama-3.3-70B-Instruct", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

def send_summary_email(recipients, summary):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipients
    msg['Subject'] = "Your AI-Generated Meeting Summary"
    msg.attach(MIMEText(f"Here are the key takeaways from your meeting:\n\n{summary}", 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients.split(','), msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001, ssl_context='adhoc')