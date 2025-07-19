document.addEventListener('DOMContentLoaded', () => {
    const progressLog = document.getElementById('progress-log');
    const briefingContent = document.getElementById('briefing-content');

    // Get the meeting ID from the URL
    const pathParts = window.location.pathname.split('/');
    const meetingId = pathParts[pathParts.length - 1];

    // Create a connection to our streaming endpoint
    const eventSource = new EventSource(`/stream-briefing/${meetingId}`);

    eventSource.onmessage = function(event) {
        const data = event.data;

        if (data.startsWith('STATUS:')) {
            const statusText = data.substring(8); // Remove "STATUS: "
            const logEntry = document.createElement('p');
            logEntry.textContent = `> ${statusText}`;
            progressLog.appendChild(logEntry);
        } else if (data === 'DONE') {
            progressLog.innerHTML += '<p>> Process complete.</p>';
            eventSource.close();
        }
    };

    eventSource.addEventListener('final_briefing', function(event) {
        const briefingText = event.data.replace(/\|\|\|/g, '\n'); // Restore newlines
        
        // Format for HTML
        let formattedHtml = briefingText
            .replace(/\n/g, '<br>')
            .replace(/### (.*?)(<br>|$)/g, '<h3>$1</h3>')
            .replace(/- (.*?)(<br>|$)/g, '<li>$1</li>');

        // Hide progress and show final result
        progressLog.style.display = 'none';
        briefingContent.innerHTML = formattedHtml;
        briefingContent.style.display = 'block';
    });

    eventSource.onerror = function() {
        const errorEntry = document.createElement('p');
        errorEntry.style.color = 'red';
        errorEntry.textContent = '> Connection to server lost. Please try again.';
        progressLog.appendChild(errorEntry);
        eventSource.close();
    };
});