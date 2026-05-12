from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import threading
import uuid

app = Flask(__name__)

jobs = {}
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8"/>\n<meta name="viewport" content="width=device-width, initial-scale=1.0"/>\n<title>YT Grab — YouTube Downloader</title>\n<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>\n<style>\n  :root {\n    --bg: #0a0a0a;\n    --surface: #111111;\n    --card: #161616;\n    --border: #222222;\n    --red: #ff2d2d;\n    --red-glow: rgba(255,45,45,0.18);\n    --red-dim: #cc1a1a;\n    --text: #f0f0f0;\n    --muted: #666;\n    --success: #1db954;\n  }\n  * { box-sizing: border-box; margin: 0; padding: 0; }\n  body {\n    background: var(--bg);\n    color: var(--text);\n    font-family: \'DM Sans\', sans-serif;\n    min-height: 100vh;\n    display: flex;\n    flex-direction: column;\n    align-items: center;\n    overflow-x: hidden;\n  }\n\n  /* BG grid */\n  body::before {\n    content: \'\';\n    position: fixed;\n    inset: 0;\n    background-image:\n      linear-gradient(rgba(255,45,45,0.04) 1px, transparent 1px),\n      linear-gradient(90deg, rgba(255,45,45,0.04) 1px, transparent 1px);\n    background-size: 40px 40px;\n    pointer-events: none;\n    z-index: 0;\n  }\n\n  header {\n    width: 100%;\n    max-width: 760px;\n    padding: 60px 24px 0;\n    position: relative;\n    z-index: 1;\n    text-align: center;\n  }\n  .logo {\n    font-family: \'Bebas Neue\', cursive;\n    font-size: clamp(56px, 12vw, 96px);\n    letter-spacing: 4px;\n    background: linear-gradient(135deg, #fff 30%, var(--red));\n    -webkit-background-clip: text;\n    -webkit-text-fill-color: transparent;\n    background-clip: text;\n    line-height: 1;\n  }\n  .tagline {\n    color: var(--muted);\n    font-size: 13px;\n    font-weight: 300;\n    letter-spacing: 3px;\n    text-transform: uppercase;\n    margin-top: 8px;\n  }\n  .red-line {\n    width: 60px;\n    height: 3px;\n    background: var(--red);\n    margin: 20px auto 0;\n    border-radius: 2px;\n    box-shadow: 0 0 12px var(--red-glow);\n  }\n\n  main {\n    width: 100%;\n    max-width: 760px;\n    padding: 40px 24px 80px;\n    position: relative;\n    z-index: 1;\n    display: flex;\n    flex-direction: column;\n    gap: 24px;\n  }\n\n  /* URL Input */\n  .input-row {\n    display: flex;\n    gap: 10px;\n    background: var(--surface);\n    border: 1px solid var(--border);\n    border-radius: 12px;\n    padding: 6px 6px 6px 18px;\n    transition: border-color 0.2s, box-shadow 0.2s;\n  }\n  .input-row:focus-within {\n    border-color: var(--red);\n    box-shadow: 0 0 0 3px var(--red-glow);\n  }\n  .input-row input {\n    flex: 1;\n    background: transparent;\n    border: none;\n    outline: none;\n    color: var(--text);\n    font-family: \'DM Sans\', sans-serif;\n    font-size: 15px;\n    font-weight: 400;\n    min-width: 0;\n  }\n  .input-row input::placeholder { color: var(--muted); }\n  .btn-fetch {\n    background: var(--red);\n    color: #fff;\n    border: none;\n    border-radius: 8px;\n    padding: 12px 24px;\n    font-family: \'DM Sans\', sans-serif;\n    font-size: 14px;\n    font-weight: 600;\n    cursor: pointer;\n    white-space: nowrap;\n    transition: background 0.15s, transform 0.1s;\n    letter-spacing: 0.5px;\n  }\n  .btn-fetch:hover { background: var(--red-dim); }\n  .btn-fetch:active { transform: scale(0.97); }\n  .btn-fetch:disabled { background: #333; color: #555; cursor: not-allowed; }\n\n  /* Video Card */\n  #video-card {\n    display: none;\n    background: var(--card);\n    border: 1px solid var(--border);\n    border-radius: 16px;\n    overflow: hidden;\n    animation: fadeUp 0.35s ease;\n  }\n  @keyframes fadeUp {\n    from { opacity: 0; transform: translateY(16px); }\n    to { opacity: 1; transform: translateY(0); }\n  }\n  .video-meta {\n    display: flex;\n    gap: 16px;\n    padding: 20px;\n    align-items: flex-start;\n  }\n  .thumb-wrap {\n    flex-shrink: 0;\n    width: 130px;\n    height: 78px;\n    border-radius: 8px;\n    overflow: hidden;\n    background: #1a1a1a;\n  }\n  .thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }\n  .video-info { flex: 1; min-width: 0; }\n  .video-title {\n    font-size: 16px;\n    font-weight: 600;\n    line-height: 1.4;\n    margin-bottom: 6px;\n    display: -webkit-box;\n    -webkit-line-clamp: 2;\n    -webkit-box-orient: vertical;\n    overflow: hidden;\n  }\n  .video-duration {\n    font-size: 12px;\n    color: var(--muted);\n    font-weight: 400;\n    letter-spacing: 0.5px;\n  }\n\n  /* Format Grid */\n  .format-section { padding: 0 20px 20px; }\n  .format-label {\n    font-size: 11px;\n    font-weight: 600;\n    text-transform: uppercase;\n    letter-spacing: 2px;\n    color: var(--muted);\n    margin-bottom: 12px;\n  }\n  .format-grid {\n    display: grid;\n    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));\n    gap: 8px;\n    margin-bottom: 16px;\n  }\n  .fmt-btn {\n    background: var(--surface);\n    border: 1px solid var(--border);\n    border-radius: 10px;\n    padding: 12px 10px;\n    cursor: pointer;\n    text-align: center;\n    transition: all 0.15s;\n    color: var(--text);\n  }\n  .fmt-btn:hover { border-color: var(--red); background: rgba(255,45,45,0.06); }\n  .fmt-btn.selected {\n    border-color: var(--red);\n    background: var(--red-glow);\n    box-shadow: 0 0 0 2px var(--red-glow);\n  }\n  .fmt-res {\n    font-family: \'Bebas Neue\', cursive;\n    font-size: 22px;\n    letter-spacing: 1px;\n    color: var(--text);\n    line-height: 1;\n  }\n  .fmt-btn.selected .fmt-res { color: var(--red); }\n  .fmt-ext {\n    font-size: 10px;\n    font-weight: 500;\n    color: var(--muted);\n    text-transform: uppercase;\n    letter-spacing: 1px;\n    margin-top: 4px;\n  }\n  .fmt-size {\n    font-size: 11px;\n    color: var(--muted);\n    margin-top: 3px;\n  }\n\n  /* Best quality pill */\n  .best-btn {\n    display: flex;\n    align-items: center;\n    gap: 10px;\n    background: linear-gradient(135deg, rgba(255,45,45,0.1), rgba(255,45,45,0.04));\n    border: 1px solid rgba(255,45,45,0.3);\n    border-radius: 10px;\n    padding: 14px 18px;\n    cursor: pointer;\n    width: 100%;\n    margin-bottom: 8px;\n    color: var(--text);\n    transition: all 0.15s;\n  }\n  .best-btn:hover { border-color: var(--red); background: var(--red-glow); }\n  .best-btn.selected { border-color: var(--red); background: var(--red-glow); }\n  .best-icon { font-size: 20px; }\n  .best-text { text-align: left; }\n  .best-text strong { font-size: 14px; font-weight: 600; display: block; }\n  .best-text span { font-size: 12px; color: var(--muted); }\n\n  .btn-download {\n    width: 100%;\n    background: var(--red);\n    color: #fff;\n    border: none;\n    border-radius: 10px;\n    padding: 15px;\n    font-family: \'DM Sans\', sans-serif;\n    font-size: 15px;\n    font-weight: 700;\n    cursor: pointer;\n    letter-spacing: 0.5px;\n    transition: background 0.15s, transform 0.1s;\n    margin-top: 8px;\n  }\n  .btn-download:hover { background: var(--red-dim); }\n  .btn-download:active { transform: scale(0.99); }\n  .btn-download:disabled { background: #333; color: #555; cursor: not-allowed; }\n\n  /* Progress */\n  #progress-wrap {\n    display: none;\n    background: var(--card);\n    border: 1px solid var(--border);\n    border-radius: 16px;\n    padding: 24px;\n    animation: fadeUp 0.3s ease;\n  }\n  .prog-title {\n    font-size: 14px;\n    font-weight: 500;\n    margin-bottom: 16px;\n    display: flex;\n    align-items: center;\n    gap: 8px;\n  }\n  .spinner {\n    width: 16px;\n    height: 16px;\n    border: 2px solid #333;\n    border-top-color: var(--red);\n    border-radius: 50%;\n    animation: spin 0.7s linear infinite;\n    flex-shrink: 0;\n  }\n  @keyframes spin { to { transform: rotate(360deg); } }\n  .prog-bar-bg {\n    background: var(--surface);\n    border-radius: 100px;\n    height: 8px;\n    overflow: hidden;\n    margin-bottom: 12px;\n  }\n  .prog-bar-fill {\n    height: 100%;\n    background: linear-gradient(90deg, var(--red), #ff6b6b);\n    border-radius: 100px;\n    transition: width 0.4s ease;\n    width: 0%;\n    box-shadow: 0 0 8px var(--red-glow);\n  }\n  .prog-stats {\n    display: flex;\n    justify-content: space-between;\n    font-size: 12px;\n    color: var(--muted);\n  }\n  .prog-pct {\n    font-family: \'Bebas Neue\', cursive;\n    font-size: 32px;\n    color: var(--red);\n    letter-spacing: 1px;\n    margin-bottom: 4px;\n  }\n\n  /* Done state */\n  #done-card {\n    display: none;\n    background: var(--card);\n    border: 1px solid rgba(29,185,84,0.3);\n    border-radius: 16px;\n    padding: 28px 24px;\n    text-align: center;\n    animation: fadeUp 0.3s ease;\n  }\n  .done-icon { font-size: 40px; margin-bottom: 12px; }\n  .done-title { font-size: 20px; font-weight: 600; margin-bottom: 6px; color: var(--success); }\n  .done-sub { font-size: 13px; color: var(--muted); margin-bottom: 20px; }\n  .btn-save {\n    background: var(--success);\n    color: #fff;\n    border: none;\n    border-radius: 10px;\n    padding: 13px 32px;\n    font-family: \'DM Sans\', sans-serif;\n    font-size: 14px;\n    font-weight: 700;\n    cursor: pointer;\n    text-decoration: none;\n    display: inline-block;\n    transition: opacity 0.15s;\n  }\n  .btn-save:hover { opacity: 0.85; }\n  .btn-new {\n    background: transparent;\n    border: 1px solid var(--border);\n    color: var(--muted);\n    border-radius: 10px;\n    padding: 13px 32px;\n    font-family: \'DM Sans\', sans-serif;\n    font-size: 14px;\n    cursor: pointer;\n    margin-left: 10px;\n    transition: border-color 0.15s, color 0.15s;\n  }\n  .btn-new:hover { border-color: #444; color: var(--text); }\n\n  /* Error */\n  .error-msg {\n    background: rgba(255,45,45,0.08);\n    border: 1px solid rgba(255,45,45,0.25);\n    border-radius: 10px;\n    padding: 14px 18px;\n    font-size: 13px;\n    color: #ff7070;\n    display: none;\n  }\n\n  footer {\n    position: relative;\n    z-index: 1;\n    color: var(--muted);\n    font-size: 12px;\n    padding-bottom: 32px;\n    text-align: center;\n    letter-spacing: 0.5px;\n  }\n\n  @media (max-width: 500px) {\n    .video-meta { flex-direction: column; }\n    .thumb-wrap { width: 100%; height: 180px; }\n    .format-grid { grid-template-columns: repeat(auto-fill, minmax(100px,1fr)); }\n  }\n</style>\n</head>\n<body>\n\n<header>\n  <div class="logo">YT GRAB</div>\n  <div class="tagline">YouTube Video Downloader</div>\n  <div class="red-line"></div>\n</header>\n\n<main>\n  <!-- URL Input -->\n  <div class="input-row">\n    <input type="text" id="url-input" placeholder="Paste YouTube URL here…" autocomplete="off"/>\n    <button class="btn-fetch" id="btn-fetch" onclick="fetchInfo()">Fetch</button>\n  </div>\n\n  <div class="error-msg" id="error-msg"></div>\n\n  <!-- Video Card -->\n  <div id="video-card">\n    <div class="video-meta">\n      <div class="thumb-wrap"><img id="thumb" src="" alt="thumbnail"/></div>\n      <div class="video-info">\n        <div class="video-title" id="vid-title"></div>\n        <div class="video-duration" id="vid-duration"></div>\n      </div>\n    </div>\n    <div class="format-section">\n      <div class="format-label">Select Quality</div>\n      <button class="best-btn selected" id="best-btn" onclick="selectBest()">\n        <span class="best-icon">⚡</span>\n        <div class="best-text">\n          <strong>Best Available</strong>\n          <span>Highest resolution + audio (recommended)</span>\n        </div>\n      </button>\n      <div class="format-grid" id="format-grid"></div>\n      <button class="btn-download" id="btn-dl" onclick="startDownload()">Download</button>\n    </div>\n  </div>\n\n  <!-- Progress -->\n  <div id="progress-wrap">\n    <div class="prog-pct" id="prog-pct">0%</div>\n    <div class="prog-title"><div class="spinner"></div> <span id="prog-label">Preparing download…</span></div>\n    <div class="prog-bar-bg"><div class="prog-bar-fill" id="prog-bar"></div></div>\n    <div class="prog-stats">\n      <span id="prog-speed"></span>\n      <span id="prog-eta"></span>\n    </div>\n  </div>\n\n  <!-- Done -->\n  <div id="done-card">\n    <div class="done-icon">✅</div>\n    <div class="done-title">Download Complete!</div>\n    <div class="done-sub">Your video is ready to save.</div>\n    <a class="btn-save" id="btn-save" href="#">Save File</a>\n    <button class="btn-new" onclick="resetAll()">Download Another</button>\n  </div>\n</main>\n\n<footer>\n  For personal use only &nbsp;·&nbsp; Respect YouTube\'s Terms of Service\n</footer>\n\n<script>\nlet selectedFormatId = "bestvideo+bestaudio/best";\nlet currentUrl = "";\nlet pollInterval = null;\n\nfunction showError(msg) {\n  const el = document.getElementById("error-msg");\n  el.textContent = "⚠ " + msg;\n  el.style.display = "block";\n}\nfunction hideError() {\n  document.getElementById("error-msg").style.display = "none";\n}\n\nfunction formatDuration(s) {\n  if (!s) return "";\n  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;\n  if (h) return `${h}:${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")}`;\n  return `${m}:${String(sec).padStart(2,"0")}`;\n}\nfunction formatSize(b) {\n  if (!b) return "";\n  const units = ["B","KB","MB","GB"];\n  let i = 0;\n  while (b >= 1024 && i < units.length - 1) { b /= 1024; i++; }\n  return `${b.toFixed(1)} ${units[i]}`;\n}\n\nasync function fetchInfo() {\n  hideError();\n  const url = document.getElementById("url-input").value.trim();\n  if (!url) { showError("Please enter a YouTube URL."); return; }\n  currentUrl = url;\n\n  const btn = document.getElementById("btn-fetch");\n  btn.disabled = true;\n  btn.textContent = "Fetching…";\n  document.getElementById("video-card").style.display = "none";\n  document.getElementById("done-card").style.display = "none";\n  document.getElementById("progress-wrap").style.display = "none";\n\n  try {\n    const res = await fetch("/info", {\n      method: "POST",\n      headers: { "Content-Type": "application/json" },\n      body: JSON.stringify({ url })\n    });\n    const data = await res.json();\n    if (data.error) { showError(data.error); return; }\n\n    document.getElementById("thumb").src = data.thumbnail;\n    document.getElementById("vid-title").textContent = data.title;\n    document.getElementById("vid-duration").textContent = formatDuration(data.duration);\n\n    // Build format grid\n    const grid = document.getElementById("format-grid");\n    grid.innerHTML = "";\n    data.formats.forEach(f => {\n      const d = document.createElement("div");\n      d.className = "fmt-btn";\n      d.dataset.fmtId = f.format_id;\n      d.innerHTML = `\n        <div class="fmt-res">${f.resolution}</div>\n        <div class="fmt-ext">${f.ext}</div>\n        <div class="fmt-size">${formatSize(f.filesize)}</div>\n      `;\n      d.onclick = () => selectFormat(f.format_id, d);\n      grid.appendChild(d);\n    });\n\n    selectedFormatId = "bestvideo+bestaudio/best";\n    document.getElementById("best-btn").classList.add("selected");\n    document.getElementById("video-card").style.display = "block";\n  } catch(e) {\n    showError("Network error. Is the server running?");\n  } finally {\n    btn.disabled = false;\n    btn.textContent = "Fetch";\n  }\n}\n\nfunction selectBest() {\n  selectedFormatId = "bestvideo+bestaudio/best";\n  document.getElementById("best-btn").classList.add("selected");\n  document.querySelectorAll(".fmt-btn").forEach(b => b.classList.remove("selected"));\n}\nfunction selectFormat(id, el) {\n  selectedFormatId = id;\n  document.getElementById("best-btn").classList.remove("selected");\n  document.querySelectorAll(".fmt-btn").forEach(b => b.classList.remove("selected"));\n  el.classList.add("selected");\n}\n\nasync function startDownload() {\n  hideError();\n  const btn = document.getElementById("btn-dl");\n  btn.disabled = true;\n  btn.textContent = "Starting…";\n\n  try {\n    const res = await fetch("/download", {\n      method: "POST",\n      headers: { "Content-Type": "application/json" },\n      body: JSON.stringify({ url: currentUrl, format_id: selectedFormatId })\n    });\n    const data = await res.json();\n    if (data.error) { showError(data.error); btn.disabled = false; btn.textContent = "Download"; return; }\n\n    const jobId = data.job_id;\n    document.getElementById("video-card").style.display = "none";\n    document.getElementById("progress-wrap").style.display = "block";\n\n    pollInterval = setInterval(() => pollProgress(jobId), 800);\n  } catch(e) {\n    showError("Failed to start download.");\n    btn.disabled = false;\n    btn.textContent = "Download";\n  }\n}\n\nasync function pollProgress(jobId) {\n  try {\n    const res = await fetch(`/progress/${jobId}`);\n    const d = await res.json();\n\n    const pct = d.progress || 0;\n    document.getElementById("prog-pct").textContent = pct + "%";\n    document.getElementById("prog-bar").style.width = pct + "%";\n    document.getElementById("prog-speed").textContent = d.speed || "";\n    document.getElementById("prog-eta").textContent = d.eta ? "ETA " + d.eta : "";\n\n    if (d.status === "downloading") {\n      document.getElementById("prog-label").textContent = "Downloading…";\n    } else if (d.status === "finished") {\n      clearInterval(pollInterval);\n      document.getElementById("progress-wrap").style.display = "none";\n      document.getElementById("done-card").style.display = "block";\n      document.getElementById("btn-save").href = `/file/${jobId}`;\n    } else if (d.status === "error") {\n      clearInterval(pollInterval);\n      document.getElementById("progress-wrap").style.display = "none";\n      showError(d.error || "Download failed.");\n      document.getElementById("video-card").style.display = "block";\n      document.getElementById("btn-dl").disabled = false;\n      document.getElementById("btn-dl").textContent = "Download";\n    }\n  } catch(e) {}\n}\n\nfunction resetAll() {\n  clearInterval(pollInterval);\n  document.getElementById("url-input").value = "";\n  document.getElementById("video-card").style.display = "none";\n  document.getElementById("progress-wrap").style.display = "none";\n  document.getElementById("done-card").style.display = "none";\n  document.getElementById("btn-dl").disabled = false;\n  document.getElementById("btn-dl").textContent = "Download";\n  hideError();\n}\n\ndocument.getElementById("url-input").addEventListener("keydown", e => {\n  if (e.key === "Enter") fetchInfo();\n});\n</script>\n</body>\n</html>\n'


@app.route("/")
def index():
    return HTML

@app.route("/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title", "Unknown")
        thumbnail = info.get("thumbnail", "")
        duration = info.get("duration", 0)
        formats = info.get("formats", [])
        unique_formats = []
        seen = set()
        for f in formats:
            res = f.get("resolution", "audio only")
            ext = f.get("ext")
            filesize = f.get("filesize") or f.get("filesize_approx")
            key = (res, ext)
            if key not in seen and res != "audio only" and filesize:
                unique_formats.append({
                    "format_id": f["format_id"],
                    "resolution": res,
                    "ext": ext,
                    "filesize": filesize,
                    "note": f.get("format_note", "")
                })
                seen.add(key)
        return jsonify({"title": title, "thumbnail": thumbnail, "duration": duration, "formats": unique_formats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_id = data.get("format_id", "bestvideo+bestaudio/best")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "starting", "progress": 0, "speed": "", "eta": "", "filename": ""}

    def run():
        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                downloaded = d.get("downloaded_bytes", 0)
                jobs[job_id]["progress"] = round(downloaded / total * 100, 1)
                jobs[job_id]["speed"] = d.get("_speed_str", "")
                jobs[job_id]["eta"] = d.get("_eta_str", "")
                jobs[job_id]["status"] = "downloading"
            elif d["status"] == "finished":
                jobs[job_id]["status"] = "finished"
                jobs[job_id]["progress"] = 100
                jobs[job_id]["filename"] = d.get("filename", "")

        fmt = format_id if format_id == "bestvideo+bestaudio/best" else f"{format_id}+bestaudio/best"
        opts = {
            "format": fmt,
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as e:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/progress/<job_id>")
def progress(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)

@app.route("/file/<job_id>")
def serve_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "finished":
        return jsonify({"error": "Not ready"}), 404
    filepath = job.get("filename", "")
    if not os.path.exists(filepath):
        files = os.listdir(DOWNLOAD_DIR)
        if files:
            filepath = os.path.join(DOWNLOAD_DIR, sorted(files)[-1])
        else:
            return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
