# YT Grab — YouTube Downloader Web App

## Files
```
yt-downloader-web/
├── app.py              ← Flask backend
├── requirements.txt    ← Python dependencies
└── templates/
    └── index.html      ← Frontend UI
```

## Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python app.py

# 3. Open in browser
http://localhost:5000
```

---

## Deploy Online (So Everyone Can Use It)

### Option A — Railway (Easiest, Free Tier)
1. Go to https://railway.app and sign up
2. Click "New Project" → "Deploy from GitHub"
3. Upload your files to a GitHub repo first
4. Railway auto-detects Python and deploys it
5. You get a public URL like `https://yt-grab.up.railway.app`

### Option B — Render (Free Tier)
1. Go to https://render.com
2. Create "New Web Service" → connect GitHub repo
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `python app.py`
5. Deploy — get a public URL

### Option C — VPS (Most Reliable for yt-dlp)
```bash
# On your VPS (Ubuntu)
git clone <your-repo>
cd yt-downloader-web
pip install -r requirements.txt

# Run with gunicorn
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

---

## ⚠️ Notes
- **Free hosting** platforms may block yt-dlp traffic. A VPS is most reliable.
- Downloads are saved in a `downloads/` folder on the server.
- Downloading YouTube videos may violate YouTube's Terms of Service.
- For personal/private use only.
