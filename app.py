from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
import threading
import uuid
import time

app = Flask(__name__)

# Store progress per job
jobs = {}
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HTML = open("templates/index.html").read()

@app.route("/")
def index():
    return render_template_string(HTML)

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

        return jsonify({
            "title": title,
            "thumbnail": thumbnail,
            "duration": duration,
            "formats": unique_formats
        })
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

        opts = {
            "format": format_id if format_id == "bestvideo+bestaudio/best" else f"{format_id}+bestaudio/best",
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
        # Try to find it
        files = os.listdir(DOWNLOAD_DIR)
        if files:
            filepath = os.path.join(DOWNLOAD_DIR, sorted(files)[-1])
        else:
            return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
