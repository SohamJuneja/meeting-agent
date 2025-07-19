from flask import Flask, jsonify, render_template, Response, request, redirect, url_for
import os
import datetime
import time
import whisper
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from agent import get_calendar_service, research_company_and_news, get_briefing_from_ai

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Page Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/briefing/<meeting_id>')
def show_briefing_page(meeting_id):
    service = get_calendar_service()
    meeting = service.events().get(calendarId='primary', eventId=meeting_id).execute()
    return render_template('briefing.html', meeting=meeting)

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

# --- API & Streaming Routes for PRE-MEETING ---
@app.route('/api/get-meetings', methods=['GET'])
def get_meetings_endpoint():
    try:
        service = get_calendar_service()
        now = datetime.datetime.now(datetime.UTC).isoformat()
        events_result = (
            service.events()
            .list(
                calendarId="primary", timeMin=now, maxResults=10,
                singleEvents=True, orderBy="startTime"
            ).execute()
        )
        events = events_result.get("items", [])
        return jsonify(events)
    except Exception as e:
        print(f"!!! An error occurred in /api/get-meetings: {e} !!!")
        return jsonify({"error": "Could not fetch calendar meetings."}), 500

@app.route('/stream-briefing/<meeting_id>')
def stream_briefing(meeting_id):
    def generate():
        service = get_calendar_service()
        meeting = service.events().get(calendarId='primary', eventId=meeting_id).execute()
        meeting_details = {
            "summary": meeting.get("summary", "No Title"),
            "attendees": [attendee['email'] for attendee in meeting.get('attendees', []) if 'resource' not in attendee]
        }
        yield f"data: STATUS: Found meeting: {meeting_details['summary']}\n\n"
        time.sleep(1)

        research_data = None
        for update in research_company_and_news(meeting_details["attendees"]):
            yield f"data: {update}\n\n"
            time.sleep(1)
            if update.startswith("DATA:"):
                research_data = update[6:]
        
        if not research_data:
            yield "data: DONE\n\n"
            return
        
        website_content, news_snippets = research_data.split('|||')
        briefing_text = None
        for update in get_briefing_from_ai(meeting_details, website_content, news_snippets):
            yield f"data: {update}\n\n"
            time.sleep(1)
            if update.startswith("DATA:"):
                briefing_text = update[6:]
        
        if briefing_text:
            formatted_briefing = briefing_text.replace('\n', '|||')
            yield f"event: final_briefing\ndata: {formatted_briefing}\n\n"
        
        yield "data: DONE\n\n"

    return Response(generate(), mimetype='text/event-stream')


# --- Routes for POST-MEETING Audio Processing ---
@app.route('/process-recording', methods=['POST'])
def process_recording():
    if 'audio_file' not in request.files: return "No file part", 400
    file = request.files['audio_file']
    recipients = request.form['recipients']
    if file.filename == '': return "No selected file", 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        print("Loading Whisper model and transcribing...")
        model = whisper.load_model("tiny")
        result = model.transcribe(filepath, fp16=False)
        transcript = result["text"]
        print("Transcription complete.")

        print("Generating AI summary...")
        summary = summarize_transcript(transcript)
        print("Summary complete.")

        send_summary_email(recipients, summary)
        os.remove(filepath)
        return render_template('results.html', summary=summary)
    
    return redirect(url_for('upload_page'))

def summarize_transcript(transcript):
    from agent import io_client
    prompt = f'Summarize the key decisions and action items from this meeting transcript: "{transcript}"'
    try:
        response = io_client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling IO API for summary: {e}")
        return "Could not generate AI summary."

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
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001)