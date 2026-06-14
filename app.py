from flask import Flask, jsonify, request, session
import hashlib
import secrets
import requests
import os
import sqlite3
import json
import subprocess
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from difflib import get_close_matches

app = Flask(__name__)
app.secret_key = 'kennyson_complete_secret_2026'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================================================
# BASE DE DONNÉES COMPLÈTE
# ==================================================
def init_db():
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    
    # Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Conversations avec titres
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Messages
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Uploads
    c.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Mémoire vectorielle simplifiée
    c.execute('''CREATE TABLE IF NOT EXISTS memory_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        keywords TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

init_db()

# ==================================================
# CONFIGURATION API
# ==================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GNEWS_API_KEY = os.environ.get('GNEWS_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================================================
# API EXTERNES
# ==================================================
def get_worldbank_gdp():
    try:
        r = requests.get("http://api.worldbank.org/v2/country/CD/indicator/NY.GDP.MKTP.CD?format=json", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1 and data[1] and data[1][0].get('value'):
                return f"📊 PIB RDC: {int(float(data[1][0]['value'])):,} USD"
    except: pass
    return None

def get_crypto_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=8)
        if r.status_code == 200:
            return f"💰 Bitcoin: ${r.json()['bitcoin']['usd']:,} USD"
    except: pass
    return None

def get_weather():
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast?latitude=-4.325&longitude=15.322&current_weather=true", timeout=8)
        if r.status_code == 200:
            return f"🌤️ Kinshasa: {r.json()['current_weather']['temperature']}°C"
    except: pass
    return None

def search_news(query):
    if not GNEWS_API_KEY: return None
    try:
        r = requests.get(f"https://gnews.io/api/v4/search?q={query}&token={GNEWS_API_KEY}&lang=fr&max=3", timeout=8)
        if r.status_code == 200:
            articles = r.json().get('articles', [])
            if articles:
                result = "📰 ACTUALITÉS:\n"
                for a in articles[:3]:
                    result += f"- {a.get('title', '')}\n"
                return result
    except: pass
    return None

def search_web_advanced(query):
    if not GNEWS_API_KEY: return None
    try:
        r = requests.get(f"https://gnews.io/api/v4/search?q={query}&token={GNEWS_API_KEY}&lang=fr&max=5", timeout=8)
        if r.status_code == 200:
            articles = r.json().get('articles', [])
            if articles:
                result = f"🌐 RECHERCHE WEB pour '{query}':\n\n"
                for i, a in enumerate(articles[:5], 1):
                    result += f"{i}. **{a.get('title')}**\n"
                    result += f"   📍 {a.get('source', {}).get('name', '')}\n\n"
                return result
    except: pass
    return None

# ==================================================
# UPLOAD FICHIERS
# ==================================================
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'csv', 'md', 'py'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_file_content(filepath, filename):
    content = ""
    if filename.endswith('.txt') or filename.endswith('.md') or filename.endswith('.py'):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()[:2000]
    elif filename.endswith('.csv'):
        import csv
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)[:15]
            content = "\n".join([",".join(row) for row in rows])
    return content

# ==================================================
# MÉMOIRE VECTORIELLE SIMPLIFIÉE
# ==================================================
class SimpleMemory:
    def __init__(self):
        self.documents = []
    
    def add_document(self, content):
        keywords = set(re.findall(r'\b\w{4,}\b', content.lower()))
        self.documents.append({"content": content[:500], "keywords": keywords})
    
    def search(self, query, limit=3):
        query_keywords = set(re.findall(r'\b\w{4,}\b', query.lower()))
        scored = []
        for doc in self.documents:
            score = len(query_keywords & doc["keywords"])
            scored.append((score, doc))
        scored.sort(reverse=True)
        return [doc["content"] for score, doc in scored[:limit]]

memory = SimpleMemory()

# ==================================================
# IA CENTRALE AVEC CONTEXTE
# ==================================================
SYSTEM_PROMPT = """Tu es KENNYSON OURAGAN, un assistant intelligent de niveau ChatGPT.
Sois utile, précis, naturel. Structure tes réponses en paragraphes.
Tu peux aider sur: économie, météo, crypto, définitions, actualités.
Réponds en français de manière professionnelle et agréable."""

def get_conversation_history(user_id, conv_id, limit=5):
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?', (conv_id, limit))
    history = [{"role": row[0], "content": row[1][:300]} for row in c.fetchall()]
    conn.close()
    return history[::-1]

def kennyson_answer(question, user_id=None, conv_id=None):
    external = ""
    q = question.lower()
    
    # Appels API
    if "pib" in q or "économie" in q:
        ext = get_worldbank_gdp()
        if ext: external += ext + "\n\n"
    if "bitcoin" in q or "crypto" in q:
        ext = get_crypto_price()
        if ext: external += ext + "\n\n"
    if "météo" in q or "temps" in q:
        ext = get_weather()
        if ext: external += ext + "\n\n"
    if "actualité" in q or "news" in q:
        ext = search_news(question)
        if ext: external += ext + "\n\n"
    
    # Recherche web si demande explicite
    if "recherche" in q or "cherche" in q or "trouve" in q:
        ext = search_web_advanced(question)
        if ext: external += ext + "\n\n"
    
    # Contexte conversation
    context = ""
    if user_id and conv_id:
        history = get_conversation_history(user_id, conv_id, 3)
        if history:
            context = "Contexte récent:\n"
            for msg in history:
                context += f"{msg['role']}: {msg['content'][:150]}...\n\n"
    
    if not GROQ_API_KEY:
        return external or "KENNYSON OURAGAN prêt. Ajoute ta clé Groq."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    full_prompt = f"{context}\n{external}\nQuestion: {question}" if external else question
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": full_prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=40)
        if r.status_code == 200:
            rep = r.json()['choices'][0]['message']['content']
            return f"{external}\n{rep}" if external else rep
        return external or "Erreur technique. Veuillez réessayer."
    except:
        return external or "KENNYSON OURAGAN prêt. Reformulez votre question."

# ==================================================
# AUTHENTIFICATION
# ==================================================
users = {}
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email, pwd, name = data.get('email'), data.get('password'), data.get('name')
    if email in users: return jsonify({"error": "Email existe"}), 400
    if '@' not in email or len(pwd) < 6: return jsonify({"error": "Email ou mot de passe invalide"}), 400
    users[email] = {"name": name, "password": hash_password(pwd), "email": email}
    return jsonify({"message": "Compte créé !"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email, pwd = data.get('email'), data.get('password')
    user = users.get(email)
    if not user or user['password'] != hash_password(pwd):
        return jsonify({"error": "Identifiants incorrects"}), 401
    session['user'] = email
    return jsonify({"token": secrets.token_hex(32), "user": {"name": user['name'], "email": user['email']}}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"message": "Déconnecté"}), 200

@app.route('/api/me')
def me():
    email = session.get('user')
    if not email: return jsonify({"error": "Non authentifié"}), 401
    return jsonify(users[email]), 200

# ==================================================
# ROUTES API PRINCIPALES
# ==================================================
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    conv_id = data.get('conversation_id')
    user_id = session.get('user')
    reponse = kennyson_answer(question, user_id, conv_id)
    return jsonify({"reponse": reponse})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    user_id = session.get('user')
    if not user_id: return jsonify({"error": "Connectez-vous"}), 401
    if 'file' not in request.files: return jsonify({"error": "Aucun fichier"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "Nom vide"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        content = analyze_file_content(filepath, filename)
        
        # Sauvegarde en base
        conn = sqlite3.connect('kennyson_memory.db')
        c = conn.cursor()
        c.execute('INSERT INTO uploads (user_id, filename, content) VALUES (?, ?, ?)', (user_id, filename, content[:1000]))
        conn.commit()
        conn.close()
        
        # Ajout à la mémoire vectorielle
        memory.add_document(content)
        
        return jsonify({"message": f"✅ {filename} uploadé", "analysis": content[:500], "filename": filename})
    return jsonify({"error": "Type non autorisé"}), 400

@app.route('/api/uploads', methods=['GET'])
def get_uploads():
    user_id = session.get('user')
    if not user_id: return jsonify({"error": "Connectez-vous"}), 401
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('SELECT filename, timestamp FROM uploads WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10', (user_id,))
    uploads = [{"filename": row[0], "date": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(uploads)

@app.route('/api/execute', methods=['POST'])
def execute_code():
    user_id = session.get('user')
    if not user_id: return jsonify({"error": "Connectez-vous"}), 401
    code = request.json.get('code', '')
    try:
        result = subprocess.run(['python', '-c', code], capture_output=True, text=True, timeout=10)
        return jsonify({"output": result.stdout, "error": result.stderr, "success": result.returncode == 0})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout (10s)"}), 408

@app.route('/api/conversations', methods=['GET', 'POST'])
def manage_conversations():
    user_id = session.get('user')
    if not user_id: return jsonify({"error": "Connectez-vous"}), 401
    
    if request.method == 'GET':
        conn = sqlite3.connect('kennyson_memory.db')
        c = conn.cursor()
        c.execute('SELECT id, title, created_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC', (user_id,))
        convs = [{"id": row[0], "title": row[1], "date": row[2]} for row in c.fetchall()]
        conn.close()
        return jsonify(convs)
    
    elif request.method == 'POST':
        title = request.json.get('title', 'Nouvelle conversation')
        conn = sqlite3.connect('kennyson_memory.db')
        c = conn.cursor()
        c.execute('INSERT INTO conversations (user_id, title) VALUES (?, ?)', (user_id, title))
        conv_id = c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"id": conv_id, "title": title})

@app.route('/api/conversations/<int:conv_id>', methods=['GET', 'DELETE'])
def conversation_detail(conv_id):
    user_id = session.get('user')
    if not user_id: return jsonify({"error": "Connectez-vous"}), 401
    
    if request.method == 'GET':
        conn = sqlite3.connect('kennyson_memory.db')
        c = conn.cursor()
        c.execute('SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp', (conv_id,))
        messages = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
        conn.close()
        return jsonify(messages)
    
    elif request.method == 'DELETE':
        conn = sqlite3.connect('kennyson_memory.db')
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE conversation_id = ?', (conv_id,))
        c.execute('DELETE FROM conversations WHERE id = ? AND user_id = ?', (conv_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Conversation supprimée"})

@app.route('/api/health')
def health():
    return jsonify({"status": "online", "groq": bool(GROQ_API_KEY), "gnews": bool(GNEWS_API_KEY)})

# ==================================================
# FRONTEND STYLE CHATGPT COMPLET
# ==================================================
HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KENNYSON · Agent IA Complet</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto; background: #343541; color: #ececec; height: 100vh; overflow: hidden; }
        .app { display: flex; height: 100vh; }
        
        /* Sidebar */
        .sidebar { width: 260px; background: #202123; display: flex; flex-direction: column; border-right: 1px solid #4a4b5a; }
        .sidebar-header { padding: 16px; border-bottom: 1px solid #4a4b5a; }
        .new-chat-btn { width: 100%; background: #e94560; border: none; padding: 12px; border-radius: 8px; color: white; font-weight: 500; cursor: pointer; }
        .conversations-list { flex: 1; overflow-y: auto; padding: 12px; }
        .conv-item { padding: 10px; border-radius: 8px; cursor: pointer; margin-bottom: 4px; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .conv-item:hover { background: #2a2b32; }
        .conv-item.active { background: #e94560; }
        .sidebar-footer { padding: 16px; border-top: 1px solid #4a4b5a; }
        .upload-btn { background: #2a2b32; border: none; padding: 8px; border-radius: 8px; color: white; cursor: pointer; width: 100%; margin-bottom: 8px; }
        #fileInput { display: none; }
        
        /* Main chat */
        .main { flex: 1; display: flex; flex-direction: column; }
        .header { padding: 12px 20px; border-bottom: 1px solid #4a4b5a; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 18px; font-weight: bold; background: linear-gradient(135deg, #e94560, #ff5a7c); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; }
        .message { display: flex; gap: 16px; margin-bottom: 24px; }
        .avatar { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .avatar.user { background: #10a37f; }
        .avatar.bot { background: #e94560; }
        .content { flex: 1; line-height: 1.6; }
        .input-area { background: #202123; padding: 16px; border-top: 1px solid #4a4b5a; }
        .input-wrapper { max-width: 800px; margin: 0 auto; display: flex; gap: 12px; }
        textarea { flex: 1; background: #40414f; border: none; border-radius: 12px; padding: 12px 16px; color: white; font-family: inherit; resize: none; }
        button { background: #e94560; border: none; border-radius: 12px; padding: 12px 24px; color: white; cursor: pointer; font-weight: 500; }
        .suggestions { max-width: 800px; margin: 12px auto 0; display: flex; gap: 8px; flex-wrap: wrap; }
        .suggestion { background: #2a2b32; padding: 6px 14px; border-radius: 20px; font-size: 12px; cursor: pointer; }
        .suggestion:hover { background: #e94560; }
        .footer { text-align: center; padding: 8px; font-size: 11px; color: #565869; }
        .typing span { display: inline-block; width: 8px; height: 8px; background: #8e8ea0; border-radius: 50%; animation: pulse 1.4s infinite; margin: 0 2px; }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
    </style>
</head>
<body>
<div class="app">
    <div class="sidebar">
        <div class="sidebar-header">
            <button class="new-chat-btn" id="newChatBtn">✨ Nouvelle conversation</button>
        </div>
        <div class="conversations-list" id="convList"></div>
        <div class="sidebar-footer">
            <label class="upload-btn" id="uploadLabel">📎 Upload fichier<input type="file" id="fileInput"></label>
            <button class="upload-btn" id="codeBtn">💻 Code interpreter</button>
            <button class="upload-btn" id="loginBtn">🔐 Connexion</button>
        </div>
    </div>
    
    <div class="main">
        <div class="header">
            <div class="logo">🔥 KENNYSON OURAGAN</div>
            <div style="font-size:12px; color:#8e8ea0;">Upload · Code · Recherche · Mémoire</div>
        </div>
        <div class="chat-container" id="chat"></div>
        <div class="input-area">
            <div class="input-wrapper">
                <textarea id="input" rows="1" placeholder="Posez votre question..."></textarea>
                <button id="send">Envoyer</button>
            </div>
            <div class="suggestions">
                <div class="suggestion" data-q="PIB de la RDC">📊 PIB RDC</div>
                <div class="suggestion" data-q="Prix du Bitcoin">💰 Bitcoin</div>
                <div class="suggestion" data-q="Météo à Kinshasa">🌤️ Météo</div>
                <div class="suggestion" data-q="Recherche actualités économiques">🌐 Recherche web</div>
            </div>
            <div class="footer">KENNYSON OURAGAN · Upload fichiers · Code Python · Recherche web</div>
        </div>
    </div>
</div>

<script>
let currentConvId = null;
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const convList = document.getElementById('convList');

function addMessage(text, role) {
    const div = document.createElement('div');
    div.className = 'message';
    div.innerHTML = `<div class="avatar ${role}">${role === 'user' ? '👤' : 'K'}</div><div class="content">${text.replace(/\\n/g, '<br>')}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

async function send() {
    const q = input.value.trim();
    if (!q) return;
    addMessage(q, 'user');
    input.value = '';
    addMessage('<div class="typing"><span>●</span><span>●</span><span>●</span></div>', 'bot');
    try {
        const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q, conversation_id: currentConvId }) });
        const data = await res.json();
        chat.lastChild.remove();
        addMessage(data.reponse, 'bot');
    } catch(e) {
        chat.lastChild.remove();
        addMessage("Erreur technique.", 'bot');
    }
}

async function loadConversations() {
    const token = localStorage.getItem('token');
    if (!token) return;
    const res = await fetch('/api/conversations');
    const data = await res.json();
    convList.innerHTML = '';
    data.forEach(c => {
        const div = document.createElement('div');
        div.className = 'conv-item' + (currentConvId === c.id ? ' active' : '');
        div.textContent = c.title;
        div.onclick = () => { currentConvId = c.id; loadConversation(c.id); loadConversations(); };
        convList.appendChild(div);
    });
}

async function loadConversation(convId) {
    const res = await fetch(`/api/conversations/${convId}`);
    const messages = await res.json();
    chat.innerHTML = '';
    messages.forEach(m => addMessage(m.content, m.role));
}

document.getElementById('newChatBtn').onclick = async () => {
    const res = await fetch('/api/conversations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'Nouvelle conversation' }) });
    const data = await res.json();
    currentConvId = data.id;
    chat.innerHTML = '';
    addMessage('✨ Nouvelle conversation ! Comment puis-je vous aider ?', 'bot');
    loadConversations();
};

document.getElementById('fileInput').onchange = async (e) => {
    const token = localStorage.getItem('token');
    if (!token) { alert('Connectez-vous d\\'abord'); return; }
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/upload', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData });
    const data = await res.json();
    addMessage(`📎 Fichier uploadé: ${file.name}\\n\\n${data.analysis || 'Analyse terminée'}`, 'bot');
};

document.getElementById('codeBtn').onclick = () => {
    const code = prompt('Entrez votre code Python:');
    if (code) fetch('/api/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) }).then(r => r.json()).then(d => addMessage(`💻 Résultat:\\n${d.output || d.error}`, 'bot'));
};

document.getElementById('send').onclick = send;
input.onkeypress = (e) => { if(e.key === 'Enter') { e.preventDefault(); send(); } };
document.querySelectorAll('.suggestion').forEach(s => { s.onclick = () => { input.value = s.dataset.q; send(); }; });
document.getElementById('loginBtn').onclick = () => window.location.href = '/login';

const token = localStorage.getItem('token');
if(token) { fetch('/api/me').then(r => { if(r.ok) { loadConversations(); } else localStorage.removeItem('token'); }); }
addMessage('Bonjour ! Je suis KENNYSON OURAGAN, version complète avec upload, code, recherche web et mémoire. Posez vos questions !', 'bot');
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

# ==================================================
# PAGE LOGIN
# ==================================================
LOGIN_PAGE = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Connexion</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#343541;color:#ececec;display:flex;align-items:center;justify-content:center;min-height:100vh;}.login-container{background:#202123;padding:40px;border-radius:16px;width:400px;}h2{color:#e94560}input{width:100%;padding:12px;margin:10px 0;background:#40414f;border:none;border-radius:8px;color:white}button{width:100%;padding:12px;background:#e94560;border:none;border-radius:8px;color:white;cursor:pointer}.toggle{text-align:center;margin-top:12px;color:#8e8ea0;cursor:pointer}</style></head>
<body><div class="login-container"><h2>KENNYSON OURAGAN</h2>
<div id="regForm"><input type="text" id="name" placeholder="Nom"><input type="email" id="email" placeholder="Email"><input type="password" id="password" placeholder="Mot de passe"><button onclick="register()">Créer un compte</button><div class="toggle" onclick="showLogin()">Déjà un compte ?</div></div>
<div id="logForm" style="display:none"><input type="email" id="loginEmail" placeholder="Email"><input type="password" id="loginPassword" placeholder="Mot de passe"><button onclick="login()">Se connecter</button><div class="toggle" onclick="showReg()">Pas de compte ?</div></div>
<div id="msg"></div></div>
<script>
function showLogin(){document.getElementById('regForm').style.display='none';document.getElementById('logForm').style.display='block'}
function showReg(){document.getElementById('regForm').style.display='block';document.getElementById('logForm').style.display='none'}
async function register(){let n=document.getElementById('name').value,e=document.getElementById('email').value,p=document.getElementById('password').value;let r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n,email:e,password:p})});let d=await r.json();if(r.ok){alert('Compte créé !');showLogin()}else alert(d.error)}
async function login(){let e=document.getElementById('loginEmail').value,p=document.getElementById('loginPassword').value;let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})});let d=await r.json();if(r.ok){localStorage.setItem('token',d.token);window.location.href='/'}else alert(d.error)}
</script></body></html>
'''

@app.route('/login')
def login_page():
    return LOGIN_PAGE

@app.route('/mon-compte')
def mon_compte():
    return '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Mon compte</title><style>body{background:#343541;color:white;font-family:system-ui;display:flex;justify-content:center;align-items:center;height:100vh;}.card{background:#202123;padding:40px;border-radius:16px;text-align:center;}</style></head>
<body><div class="card"><div id="info">Chargement...</div><button onclick="logout()" style="background:#e94560;padding:10px 20px;border:none;border-radius:8px;color:white;margin-top:20px">Déconnexion</button><a href="/" style="display:block;margin-top:16px;color:#8e8ea0">← Retour</a></div>
<script>async function load(){let r=await fetch('/api/me');if(r.ok){let u=await r.json();document.getElementById('info').innerHTML=`<h2>${u.name}</h2><p>${u.email}</p>`}else window.location.href='/login'}async function logout(){await fetch('/api/logout',{method:'POST'});localStorage.removeItem('token');window.location.href='/'}load()</script></body></html>
    '''

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
