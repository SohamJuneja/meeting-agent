document.addEventListener('DOMContentLoaded', () => {
    const meetingsList = document.getElementById('meetings-list');
    const meetingsLoader = document.getElementById('meetings-loader');

    // Load meetings when the page loads
    fetch('/api/get-meetings')
        .then(response => response.json())
        .then(meetings => {
            meetingsLoader.style.display = 'none';
            if (meetings.error || meetings.length === 0) {
                meetingsList.innerHTML = '<p>No upcoming meetings found in your calendar.</p>';
                return;
            }

            meetings.forEach(meeting => {
                const li = document.createElement('li');
                li.className = 'meeting-item';

                const meetingDate = new Date(meeting.start.dateTime || meeting.start.date);
                // A cleaner date format
                const formattedDate = meetingDate.toLocaleString('en-US', { dateStyle: 'full', timeStyle: 'short' });

                li.innerHTML = `
                    <div class="meeting-details">
                        <strong>${meeting.summary || 'No Title'}</strong>
                        <span>${formattedDate}</span>
                    </div>
                    <a href="/briefing/${meeting.id}" class="action-btn">
                        Generate Briefing
                    </a>
                `;
                meetingsList.appendChild(li);
            });
        })
        .catch(error => {
            meetingsLoader.style.display = 'none';
            meetingsList.innerHTML = `<p style="color: red;">Could not load meetings. Please ensure you are logged into Google and the server is running.</p>`;
            console.error('Error:', error);
        });
});