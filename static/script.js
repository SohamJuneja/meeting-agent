document.addEventListener('DOMContentLoaded', async () => {
    const loginSection = document.getElementById('login-section');
    const appContent = document.getElementById('app-content');
    const meetingsList = document.getElementById('meetings-list');
    const meetingsLoader = document.getElementById('meetings-loader');
    const authControls = document.getElementById('auth-controls');

    // Check login status on page load
    try {
        const loginStatusResponse = await fetch('/api/check-login');
        const loginStatus = await loginStatusResponse.json();

        if (loginStatus.logged_in) {
            loginSection.style.display = 'none';
            appContent.style.display = 'block';
            authControls.innerHTML = '<a href="/logout" class="action-btn logout-btn">Logout</a>';
            fetchMeetings();
        } else {
            loginSection.style.display = 'block';
            appContent.style.display = 'none';
        }
    } catch (error) {
        console.error("Could not check login status:", error);
        loginSection.innerHTML = '<p style="color: red;">Could not connect to server. Please try again later.</p>';
    }

    async function fetchMeetings() {
        meetingsLoader.style.display = 'block';
        meetingsList.innerHTML = '';
        try {
            const response = await fetch('/api/get-meetings');
            const meetings = await response.json();
            meetingsLoader.style.display = 'none';

            if (meetings.error) {
                 meetingsList.innerHTML = `<p style="color: red;">Error: ${meetings.error}</p>`;
                 return;
            }
            if (meetings.length === 0) {
                meetingsList.innerHTML = '<p>No upcoming meetings found in your calendar.</p>';
                return;
            }

            meetings.forEach(meeting => {
                const li = document.createElement('li');
                li.className = 'meeting-item';
                const meetingDate = new Date(meeting.start.dateTime || meeting.start.date);
                const formattedDate = meetingDate.toLocaleString('en-US', { dateStyle: 'full', timeStyle: 'short' });
                li.innerHTML = `
                    <div class="meeting-details">
                        <strong>${meeting.summary || 'No Title'}</strong>
                        <span>${formattedDate}</span>
                    </div>
                    <a href="/briefing/${meeting.id}" class="action-btn">Generate Briefing</a>`;
                meetingsList.appendChild(li);
            });
        } catch (error) {
            meetingsLoader.style.display = 'none';
            meetingsList.innerHTML = `<p style="color: red;">Could not load meetings.</p>`;
        }
    }
});