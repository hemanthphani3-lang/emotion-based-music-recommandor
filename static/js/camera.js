const video = document.getElementById('webcam');
const canvas = document.getElementById('photo');
const captureBtn = document.getElementById('capture-btn');
const captureLabel = document.getElementById('capture-label');
const moodLabel = document.getElementById('mood-label');
const songsList = document.getElementById('songs-list');
const playerContainer = document.getElementById('player-container');
const ytPlayer = document.getElementById('yt-player');
const manualMood = document.getElementById('manual-mood');
const detectOverlay = document.getElementById('detect-overlay');
const cameraCard = document.getElementById('camera-card');

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
    captureLabel.innerText = "Analyzing...";
    detectOverlay.classList.add('active');
    cameraCard.classList.add('scanning');
    
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
            if (data.emotion === 'No face found') {
                moodLabel.innerHTML = `<span style="color:#ef4444; font-size:1.1rem; display:flex; align-items:center; gap:0.5rem;"><ion-icon name="warning-outline"></ion-icon> No face detected. Adjust lighting or pose!</span>`;
                songsList.innerHTML = '';
            } else {
                updateMood(data.emotion);
            }
        }
    } catch (err) {
        console.error("Detection error:", err);
    } finally {
        captureBtn.disabled = false;
        captureLabel.innerText = "Detect Emotion";
        detectOverlay.classList.remove('active');
        cameraCard.classList.remove('scanning');
    }
});

// Manual/Fallback selection
manualMood.addEventListener('change', (e) => {
    if (e.target.value) {
        updateMood(e.target.value);
    }
});

function updateMood(emotion) {
    moodLabel.innerHTML = `Mood: <span class="mood-value">${emotion}</span>`;
    fetchRecommendations(emotion);
}

// Fetch Music
async function fetchRecommendations(emotion) {
    songsList.innerHTML = `
        <div class="empty-state">
            <div class="spinner" style="width: 32px; height: 32px; border-width: 2px;"></div>
            <p>Searching for ${emotion} vibes...</p>
        </div>`;
    
    try {
        const response = await fetch(`/recommendations/${emotion}`);
        const data = await response.json();
        
        renderSongs(data.songs);
    } catch (err) {
        console.error("Recommendation error:", err);
        songsList.innerHTML = `
            <div class="empty-state">
                <ion-icon name="alert-circle-outline" style="color:#ef4444;"></ion-icon>
                <p>Failed to load suggestions.</p>
            </div>`;
    }
}

function renderSongs(songs) {
    if (!songs || songs.length === 0) {
        songsList.innerHTML = `
            <div class="empty-state">
                <ion-icon name="search-outline"></ion-icon>
                <p>No songs found. Try another mood!</p>
            </div>`;
        return;
    }

    songsList.innerHTML = '';
    songs.forEach((song, index) => {
        const card = document.createElement('div');
        card.className = 'song-card';
        card.style.animationDelay = `${index * 0.1}s`;
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
    playerContainer.style.animation = 'fadeInUp 0.3s ease both';
    document.getElementById('now-playing-title').innerText = song.title;
    
    // Embed YouTube Player
    ytPlayer.innerHTML = `<iframe width="100%" height="180" src="https://www.youtube.com/embed/${song.id}?autoplay=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
    
    // Track Interaction
    trackAction(song.id, song.title, 'play');
}

function closePlayer() {
    playerContainer.style.display = 'none';
    ytPlayer.innerHTML = '';
    currentSong = null;
}

// Interaction Tracking
async function trackAction(songId, songTitle, action) {
    try {
        await fetch('/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ song_id: songId, song_title: songTitle, action: action })
        });
    } catch(err) {
        console.error("Tracking error:", err);
    }
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
