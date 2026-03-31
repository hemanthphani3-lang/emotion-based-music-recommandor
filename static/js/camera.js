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
let latestFaceBox = null;

// MediaPipe FaceMesh Setup
const meshOverlay = document.getElementById('mesh-overlay');
let meshCtx = null;
if (meshOverlay) {
    meshCtx = meshOverlay.getContext('2d');
}

let faceMesh = null;
if (typeof FaceMesh !== 'undefined') {
    faceMesh = new FaceMesh({locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
    }});
    faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });
    faceMesh.onResults((results) => {
        if (!meshCtx || !meshOverlay) return;
        meshCtx.save();
        meshCtx.clearRect(0, 0, meshOverlay.width, meshOverlay.height);
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            const landmarks = results.multiFaceLandmarks[0];
            
            // Calculate and store tight bounding box for the AI backend
            let minX=1, minY=1, maxX=0, maxY=0;
            for(const lm of landmarks) {
                if(lm.x < minX) minX = lm.x;
                if(lm.y < minY) minY = lm.y;
                if(lm.x > maxX) maxX = lm.x;
                if(lm.y > maxY) maxY = lm.y;
            }
            latestFaceBox = {minX, minY, maxX, maxY};

            for (const personLandmarks of results.multiFaceLandmarks) {
                drawConnectors(meshCtx, personLandmarks, FACEMESH_TESSELATION, 
                    {color: 'rgba(0, 229, 160, 0.25)', lineWidth: 0.8}); 
                drawConnectors(meshCtx, personLandmarks, FACEMESH_RIGHT_EYE, {color: '#00e5a0', lineWidth: 1.5});
                drawConnectors(meshCtx, personLandmarks, FACEMESH_LEFT_EYE, {color: '#00e5a0', lineWidth: 1.5});
                drawConnectors(meshCtx, personLandmarks, FACEMESH_FACE_OVAL, {color: '#00e5a0', lineWidth: 1.5});
            }
        } else {
            latestFaceBox = null;
        }
        meshCtx.restore();
    });
}

// Initialize Webcam
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.onloadedmetadata = () => {
            video.play().catch(err => console.error("Video play error:", err));
        };

        if (typeof Camera !== 'undefined' && faceMesh) {
            const camera = new Camera(video, {
                onFrame: async () => {
                    if (meshOverlay && meshOverlay.width !== video.videoWidth && video.videoWidth > 0) {
                        meshOverlay.width = video.videoWidth;
                        meshOverlay.height = video.videoHeight;
                    }
                    await faceMesh.send({image: video});
                },
                width: 640,
                height: 480
            });
            camera.start();
        }
    } catch (err) {
        console.error("Camera access denied:", err);
        alert("Camera access is required for emotion detection. Falling back to manual selection.");
    }
}

startCamera();

// Capture and Detect
captureBtn.addEventListener('click', async () => {
    if (!video.videoWidth || !video.videoHeight) {
        alert("Wait a second, the camera isn't fully ready yet or is blocked.");
        return;
    }

    captureBtn.disabled = true;
    captureLabel.innerText = "Analyzing...";
    detectOverlay.classList.add('active');
    cameraCard.classList.add('scanning');
    
    // Draw cropped face ONLY using MediaPipe boundaries
    if (latestFaceBox) {
        const vw = video.videoWidth;
        const vh = video.videoHeight;
        
        let pMinX = latestFaceBox.minX * vw;
        let pMinY = latestFaceBox.minY * vh;
        let pMaxX = latestFaceBox.maxX * vw;
        let pMaxY = latestFaceBox.maxY * vh;
        
        let width = pMaxX - pMinX;
        let height = pMaxY - pMinY;
        
        // Add robust padding for forehead/chin
        let padX = width * 0.20;
        let padY = height * 0.35;
        
        pMinX = Math.max(0, pMinX - padX);
        pMinY = Math.max(0, pMinY - padY);
        pMaxX = Math.min(vw, pMaxX + padX);
        pMaxY = Math.min(vh, pMaxY + padY);
        
        let cWidth = pMaxX - pMinX;
        let cHeight = pMaxY - pMinY;
        
        canvas.width = cWidth;
        canvas.height = cHeight;
        canvas.getContext('2d').drawImage(video, pMinX, pMinY, cWidth, cHeight, 0, 0, cWidth, cHeight);
    } else {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
    }
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
    moodLabel.innerHTML = `Mood: <span class="mood-value" style="color: var(--text-main);">${emotion}</span>`;
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
    
    // Embed YouTube Player with origin parameter to bypass syndication blocks
    ytPlayer.innerHTML = `<iframe width="100%" height="180" src="https://www.youtube.com/embed/${song.id}?autoplay=1&origin=${window.location.origin}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
    
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
