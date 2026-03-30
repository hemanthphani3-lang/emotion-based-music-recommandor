const video = document.getElementById('webcam');
const canvas = document.getElementById('photo');
const captureBtn = document.getElementById('capture-btn');
const moodLabel = document.getElementById('mood-label');
const songsList = document.getElementById('songs-list');
const playerContainer = document.getElementById('player-container');
const ytPlayer = document.getElementById('yt-player');
const manualMood = document.getElementById('manual-mood');

let currentSong = null;

// Initialize Webcam
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
    } catch (err) {
        console.error("Camera access denied:", err);
        alert("Camera access is required for emotion detection. Falling back to manual selection.");
    }
}

startCamera();

// Capture and Detect
captureBtn.addEventListener('click', async () => {
    captureBtn.disabled = true;
    captureBtn.innerText = "Analyzing...";
    
    // Draw frame to canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg');

    try {
        const response = await fetch('/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData })
        });
        const data = await response.json();
        
        if (data.emotion) {
            updateMood(data.emotion);
        }
    } catch (err) {
        console.error("Detection error:", err);
    } finally {
        captureBtn.disabled = false;
        captureBtn.innerText = "Detect Emotion";
    }
});

// Manual/Fallback selection
manualMood.addEventListener('change', (e) => {
    if (e.target.value) {
        updateMood(e.target.value);
    }
});

function updateMood(emotion) {
    moodLabel.innerHTML = `Detected Mood: <span style="color:var(--accent);">${emotion}</span>`;
    fetchRecommendations(emotion);
}

// Fetch Music
async function fetchRecommendations(emotion) {
    songsList.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding-top:4rem;">Searching for ${emotion} vibes...</div>`;
    
    try {
        const response = await fetch(`/recommendations/${emotion}`);
        const data = await response.json();
        
        renderSongs(data.songs);
    } catch (err) {
        console.error("Recommendation error:", err);
    }
}

function renderSongs(songs) {
    if (!songs || songs.length === 0) {
        songsList.innerHTML = `<div style="grid-column:1/-1; text-align:center;">No songs found. Try another mood!</div>`;
        return;
    }

    songsList.innerHTML = '';
    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'song-card';
        card.innerHTML = `
            <img src="${song.thumbnail}" alt="${song.title}">
            <h3 title="${song.title}">${song.title}</h3>
        `;
        card.onclick = () => playSong(song);
        songsList.appendChild(card);
    });
}

function playSong(song) {
    currentSong = song;
    playerContainer.style.display = 'block';
    document.getElementById('now-playing-title').innerText = `Playing: ${song.title}`;
    
    // Embed YouTube Player
    ytPlayer.innerHTML = `<iframe width="100%" height="200" src="https://www.youtube.com/embed/${song.id}?autoplay=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
    
    // Track Interaction
    trackAction(song.id, song.title, 'play');
}

function closePlayer() {
    playerContainer.style.display = 'none';
    ytPlayer.innerHTML = '';
}

// Interaction Tracking
async function trackAction(songId, songTitle, action) {
    await fetch('/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_id: songId, song_title: songTitle, action: action })
    });
}

document.getElementById('skip-btn').onclick = () => {
    if (currentSong) {
        trackAction(currentSong.id, currentSong.title, 'skip');
        closePlayer();
        alert("Song skipped. We'll avoid this one in the future!");
    }
};

document.getElementById('fav-btn').onclick = () => {
    if (currentSong) {
        trackAction(currentSong.id, currentSong.title, 'favorite');
        alert("Added to favorites!");
    }
};
