from flask import Flask, jsonify, request, session, redirect, url_for
from functools import wraps
import hashlib
import secrets
import requests
import os

app = Flask(__name__)
app.secret_key = 'oyebi_secret_key_2026'

# ==================================================
# CONFIGURATION GROQ
# ==================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================================================
# PROMPT SYSTÈME (NIVEAU CLAUDE/CHATGPT)
# ==================================================
SYSTEM_PROMPT = """Tu es OYEBI, un expert financier et économique congolais de classe mondiale.

RÈGLES ABSOLUES :
1. Réponds comme ChatGPT ou Claude : détaillé, intelligent, précis, avec des exemples concrets.
2. Structure OBLIGATOIRE (6 parties) :
   - 📊 CHIFFRE CLÉ : donne un chiffre précis et récent
   - 🔍 ANALYSE : explique pourquoi ce chiffre compte
   - ⚡ CAUSES PROFONDES : liste 2-3 causes structurelles
   - 💥 CONSÉQUENCES : impacts sur la population ou l'économie
   - 🎯 ACTION CONCRÈTE : conseil spécifique applicable dans les 10 secondes
   - 🔮 PRÉVISION : ce qui va probablement se passer dans les 12 prochains mois
3. Utilise des données réelles (PIB, inflation, chômage, prix des matières premières).
4. Sois pragmatique et actionable.
5. Réponds en français soutenu mais accessible.
6. MINIMUM 200 mots par réponse.

Tu es un agent IA surhumain. Tu dépasses les capacités humaines de 200%.
Ne donne jamais de réponse courte. Ne dis jamais "je ne sais pas"."""

# ==================================================
# FONCTION APPEL GROQ
# ==================================================
def chat_groq(question):
    """Appelle Groq et retourne la réponse IA"""
    if not GROQ_API_KEY or GROQ_API_KEY == "":
        return "⚠️ Clé API Groq non configurée sur Render. Ajoute GROQ_API_KEY dans Environment."
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Erreur API Groq ({response.status_code}): {response.text[:300]}"
    except Exception as e:
        return f"❌ Exception technique: {str(e)[:300]}"

# ==================================================
# AUTHENTIFICATION (inchangée)
# ==================================================
users = {}
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email, password, name = data.get('email'), data.get('password'), data.get('name')
    if email in users: return jsonify({"error": "Email déjà utilisé"}), 400
    if '@' not in email: return jsonify({"error": "Email invalide"}), 400
    if len(password) < 6: return jsonify({"error": "Mot de passe trop court"}), 400
    users[email] = {"name": name, "password": hash_password(password), "email": email}
    return jsonify({"message": "Compte créé !"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email, password = data.get('email'), data.get('password')
    user = users.get(email)
    if not user or user['password'] != hash_password(password):
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
# ROUTE CHAT AVEC GROQ
# ==================================================
@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({"reponse": "Veuillez poser une question."})
    
    reponse = chat_groq(question)
    return jsonify({"reponse": reponse})

# ==================================================
# ROUTE DE TEST (pour vérifier que Groq répond)
# ==================================================
@app.route('/api/test-groq')
def test_groq():
    if not GROQ_API_KEY:
        return jsonify({"status": "error", "message": "GROQ_API_KEY non configurée"})
    test = chat_groq("Dis simplement 'OK je fonctionne' en une phrase.")
    return jsonify({"status": "ok", "api_key_configured": True, "test_response": test[:200]})

# ==================================================
# PAGES HTML (version simplifiée mais fonctionnelle)
# ==================================================
BASE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OYEBI · IA Financière</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0A0F1E; color: #F1F5F9; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { text-align: center; padding: 30px; background: linear-gradient(135deg, #0085CA, #FACC15); border-radius: 20px; margin-bottom: 20px; }
        h1 { color: white; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #FACC15; margin: 0 15px; text-decoration: none; }
        .chat-box { background: rgba(255,255,255,0.05); border-radius: 20px; padding: 20px; height: 450px; overflow-y: auto; margin-bottom: 20px; }
        .message { margin: 10px 0; padding: 12px; border-radius: 12px; white-space: pre-wrap; line-height: 1.4; }
        .user { background: #0085CA; text-align: right; }
        .bot { background: rgba(250,204,21,0.15); border-left: 3px solid #FACC15; }
        input { width: 80%; padding: 12px; border-radius: 25px; border: none; background: rgba(255,255,255,0.1); color: white; }
        button { padding: 12px 25px; background: #FACC15; border: none; border-radius: 25px; cursor: pointer; margin-left: 10px; }
        .footer { text-align: center; margin-top: 20px; font-size: 0.8rem; color: #64748B; }
        @media (max-width: 600px) { input { width: 70%; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>🤖 OYEBI · Agent IA Financier</h1><p>Propulsé par Groq (qualité ChatGPT)</p></div>
        <div class="nav"><a href="/">Accueil</a><a href="/chat">Chat</a><a href="/login" id="authLink">Connexion</a></div>
        <div id="content">[CONTENT]</div>
        <div class="footer">OYEBI · Kinshasa, RDC</div>
    </div>
    <script>
        const token = localStorage.getItem('token');
        const authLink = document.getElementById('authLink');
        if (token) fetch('/api/me').then(r => { if(r.ok) authLink.innerHTML = '👤 Mon compte'; });
    </script>
</body>
</html>
'''

def render_page(content):
    return BASE_HTML.replace('[CONTENT]', content)

@app.route('/')
def index():
    content = '<div style="background:rgba(255,255,255,0.05); border-radius:20px; padding:40px; text-align:center;"><h2>💡 Expert financier surhumain</h2><p>Posez vos questions sur l\'économie, l\'inflation, les investissements...</p><a href="/chat"><button>💬 Démarrer</button></a></div>'
    return render_page(content)

@app.route('/chat')
def chat():
    content = '''
    <div class="chat-box" id="chat"><div class="message bot">🤖 Bonjour ! Je suis OYEBI. Posez-moi des questions sur l'économie de la RDC, l'inflation, le chômage, les investissements ou un business plan.</div></div>
    <div><input type="text" id="question" placeholder="Ex: Comment va l'économie de la RDC ?"><button onclick="sendMessage()">Envoyer</button></div>
    <script>
        async function sendMessage() {
            const input = document.getElementById('question');
            const question = input.value.trim();
            if (!question) return;
            const chat = document.getElementById('chat');
            chat.innerHTML += `<div class="message user">👤 ${question}</div>`;
            input.value = '';
            chat.innerHTML += `<div class="message bot">🤖 Génération de la réponse... (5-10s)</div>`;
            chat.scrollTop = chat.scrollHeight;
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: question})
                });
                const data = await response.json();
                const lastMsg = chat.lastElementChild;
                lastMsg.innerHTML = `🤖 ${data.reponse.replace(/\\n/g, '<br>')}`;
                chat.scrollTop = chat.scrollHeight;
            } catch(e) {
                const lastMsg = chat.lastElementChild;
                lastMsg.innerHTML = '🤖 Erreur technique. Vérifie la console.';
            }
        }
    </script>
    '''
    return render_page(content)

# Pages auth simplifiées
LOGIN_PAGE = '''
<div style="max-width:400px; margin:0 auto; background:rgba(255,255,255,0.05); border-radius:20px; padding:30px;">
    <h2 style="text-align:center;">Connexion / Inscription</h2>
    <input type="text" id="name" placeholder="Nom" style="width:100%; padding:10px; margin:10px 0; background:rgba(255,255,255,0.1); border:none; border-radius:10px; color:white;">
    <input type="email" id="email" placeholder="Email" style="width:100%; padding:10px; margin:10px 0; background:rgba(255,255,255,0.1); border:none; border-radius:10px; color:white;">
    <input type="password" id="password" placeholder="Mot de passe" style="width:100%; padding:10px; margin:10px 0; background:rgba(255,255,255,0.1); border:none; border-radius:10px; color:white;">
    <button onclick="register()" style="width:48%; background:#FACC15; padding:10px; margin:5px 1%;">S'inscrire</button>
    <button onclick="login()" style="width:48%; background:#0085CA; padding:10px; margin:5px 1%;">Se connecter</button>
    <div id="msg" style="margin-top:10px; text-align:center;"></div>
</div>
<script>
    async function register() {
        let r = await fetch('/api/register', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('name').value,email:document.getElementById('email').value,password:document.getElementById('password').value})});
        let d = await r.json();
        document.getElementById('msg').innerHTML = d.message || d.error;
        if (r.ok) setTimeout(() => window.location.href='/login', 1500);
    }
    async function login() {
        let r = await fetch('/api/login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('email').value,password:document.getElementById('password').value})});
        let d = await r.json();
        if (r.ok) { localStorage.setItem('token', d.token); window.location.href='/'; }
        else document.getElementById('msg').innerHTML = d.error;
    }
</script>
'''

@app.route('/login')
def login_page():
    return render_page(LOGIN_PAGE)

MON_COMPTE = '''
<div style="text-align:center; background:rgba(255,255,255,0.05); border-radius:20px; padding:40px;">
    <div id="userInfo"></div>
    <button onclick="logout()" style="background:#EF4444; padding:10px 20px; border:none; border-radius:10px; margin-top:20px;">Déconnexion</button>
</div>
<script>
    async function loadUser() { let r=await fetch('/api/me'); if(r.ok){ let u=await r.json(); document.getElementById('userInfo').innerHTML=`<h2>👤 ${u.name}</h2><p>${u.email}</p>`; } else window.location.href='/login'; }
    async function logout() { await fetch('/api/logout',{method:'POST'}); localStorage.removeItem('token'); window.location.href='/'; }
    loadUser();
</script>
'''

@app.route('/mon-compte')
def mon_compte():
    return render_page(MON_COMPTE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
