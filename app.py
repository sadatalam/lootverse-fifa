import os
import json
import base64
import uuid
import time
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "lootverse_ultimate_secure_key_2026"
DB_FILE = 'database.json'

def load_db():
    default_db = {"streams": [], "active_pings": {}}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                db = json.load(f)
                if "active_pings" not in db: db["active_pings"] = {}
                if "streams" not in db: db["streams"] = []
                return db
        except: return default_db
    return default_db

def save_db(db):
    try:
        with open(DB_FILE, 'w') as f: json.dump(db, f)
    except: pass

@app.route('/', strict_slashes=False)
def index():
    return render_template_string(HTML_TEMPLATE, is_admin=False)

@app.route('/setup', methods=['GET', 'POST'], strict_slashes=False)
def setup():
    if request.method == 'POST':
        if request.form.get('password') == '123sadat':
            session['is_admin'] = True
            return redirect(url_for('setup'))
        return "Unauthorized", 401
    if not session.get('is_admin'):
        return '<!DOCTYPE html><html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-slate-900 flex items-center justify-center h-screen"><form method="POST" class="bg-slate-800 p-8 rounded-xl shadow-2xl border border-white/10 text-center"><h2 class="text-white text-xl font-bold mb-4">LootVerse Admin</h2><input type="password" name="password" placeholder="Password" class="w-full bg-slate-900 text-white px-4 py-2 rounded border border-white/20 mb-4"><button type="submit" class="w-full bg-emerald-600 text-white font-bold py-2 rounded">Access</button></form></body></html>'
    return render_template_string(HTML_TEMPLATE, is_admin=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/data')
def api_data():
    db = load_db()
    current_time = time.time()
    real_active_count = sum(1 for uid, last_ping in db["active_pings"].items() if current_time - last_ping < 60)
    save_db(db)
    
    safe_streams = []
    for s in db["streams"]:
        safe_s = s.copy()
        safe_s["url"] = base64.b64encode(s["url"].encode()).decode()
        safe_s["backups"] = [base64.b64encode(b.encode()).decode() for b in s.get("backups", [])]
        safe_streams.append(safe_s)
    
    return jsonify({"display_watching": real_active_count, "streams": safe_streams})

@app.route('/api/ping', methods=['POST'])
def api_ping():
    db = load_db()
    db["active_pings"][request.json.get('uid', 'anon')] = time.time()
    save_db(db)
    return jsonify({"status": "ok"})

@app.route('/api/admin/add', methods=['POST'])
def api_add():
    if not session.get('is_admin'): return "Unauthorized", 401
    db = load_db()
    data = request.json
    db["streams"].append({
        "id": str(uuid.uuid4()),
        "title": data.get("title", "Live"),
        "url": data.get("url"),
        "backups": data.get("backups", []),
        "isPinned": data.get("isPinned", False)
    })
    save_db(db)
    return jsonify({"status": "success"})

# The template string follows below, safely defined
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LootVerse | FIFA WORLD CUP LIVE WATCH ONLINE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
</head>
<body class="bg-slate-950 text-white font-sans">
    <header class="p-4 border-b border-white/10 flex justify-between items-center bg-slate-900">
        <h1 class="text-xl font-black text-emerald-500">LootVerse</h1>
        <a href="https://t.me/Lootversemen" class="bg-sky-500 px-4 py-2 rounded-lg text-sm font-bold">@Lootverse</a>
    </header>
    <main class="max-w-5xl mx-auto p-4">
        <div class="bg-slate-900 p-4 rounded-xl border border-emerald-500/20 mb-6 text-center">
            <span class="text-emerald-400 font-bold"><span id="watchingNow">0</span> Watching Now</span>
        </div>
        <div id="streamsGrid" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
    </main>
    <script>
        async function update() {
            const res = await fetch("/api/data");
            const data = await res.json();
            document.getElementById('watchingNow').innerText = data.display_watching;
            const grid = document.getElementById('streamsGrid');
            grid.innerHTML = data.streams.map(s => `
                <div class="bg-slate-900 p-2 rounded-xl border border-white/10">
                    <video id="v-${s.id}" class="w-full bg-black rounded" controls autoplay playsinline></video>
                    <div class="p-2 font-bold">${s.title}</div>
                    <button class="w-full bg-emerald-600 py-2 rounded text-xs">Premium Server</button>
                </div>
            `).join('');
            data.streams.forEach(s => {
                const video = document.getElementById('v-'+s.id);
                const hls = new Hls();
                hls.loadSource(atob(s.url));
                hls.attachMedia(video);
            });
        }
        setInterval(update, 5000);
        update();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
