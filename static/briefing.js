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

    // Replace the existing eventSource.onerror function in briefing.js

eventSource.onerror = function(event) {
    // Check if the connection is really closed, if so, stop trying.
    if (event.target.readyState === EventSource.CLOSED) {
        console.log('EventSource closed by server.');
    } else {
        // Otherwise, it might be a temporary network issue, so just log it.
        console.log('EventSource error, but will remain open:', event);
    }
};
});