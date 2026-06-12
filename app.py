from flask import Flask, jsonify, request, session, redirect, url_for
from functools import wraps
import hashlib
import secrets
import json

app = Flask(__name__)
app.secret_key = 'oyebi_secret_key'

# ==================== AUTH ====================
users = {}

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    if email in users:
        return jsonify({"error": "Email déjà utilisé"}), 400
    if '@' not in email:
        return jsonify({"error": "Email invalide"}), 400
    if len(password) < 6:
        return jsonify({"error": "Mot de passe trop court (min 6)"}), 400
    users[email] = {"name": name, "password": hash_password(password), "email": email}
    return jsonify({"message": "Compte créé avec succès !"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = users.get(email)
    if not user or user['password'] != hash_password(password):
        return jsonify({"error": "Email ou mot de passe incorrect"}), 401
    session['user'] = email
    return jsonify({"token": secrets.token_hex(32), "user": {"name": user['name'], "email": user['email']}}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"message": "Déconnecté"}), 200

@app.route('/api/me')
def me():
    email = session.get('user')
    if not email:
        return jsonify({"error": "Non authentifié"}), 401
    user = users.get(email)
    return jsonify({"name": user['name'], "email": user['email']}), 200

# ==================== DONNÉES ====================
COUNTRIES = [
    {"code": "CD", "nom": "RDC", "pib": 65000, "inflation": 18.5, "chomage": 22.0},
    {"code": "US", "nom": "États-Unis", "pib": 25400000, "inflation": 3.2, "chomage": 3.8},
    {"code": "FR", "nom": "France", "pib": 2780000, "inflation": 2.5, "chomage": 7.2},
]

# ==================== TEMPLATE ====================
BASE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OYEBI · Agent IA Finance</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0A0F1E; color: #F1F5F9; }
        .navbar { background: rgba(10,15,30,0.9); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .logo { font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF, #0085CA, #FACC15); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav-links { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .nav-links a { color: #F1F5F9; text-decoration: none; }
        .nav-links a:hover { color: #FACC15; }
        .container { max-width: 1280px; margin: 0 auto; padding: 2rem 1.5rem; }
        .hero { background: rgba(255,255,255,0.03); border-radius: 2rem; padding: 3rem 2rem; text-align: center; margin-bottom: 2rem; }
        .hero h1 { font-size: 2.5rem; background: linear-gradient(135deg, #FFFFFF, #0085CA, #FACC15); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card-glass { background: rgba(255,255,255,0.03); border-radius: 1rem; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); }
        .card-glass i { font-size: 2rem; color: #FACC15; margin-bottom: 1rem; }
        .kpi-value { font-size: 2rem; font-weight: 700; color: #FACC15; }
        .chat-container { max-height: 400px; overflow-y: auto; margin-bottom: 1rem; }
        .chat-message { padding: 0.8rem; margin: 0.5rem 0; border-radius: 1rem; }
        .user-message { background: rgba(0,133,202,0.2); text-align: right; }
        .bot-message { background: rgba(250,204,21,0.1); border-left: 3px solid #FACC15; }
        .footer { text-align: center; padding: 2rem; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.8rem; color: #64748B; }
        @media (max-width: 768px) { .hero h1 { font-size: 1.8rem; } .navbar { flex-direction: column; text-align: center; } }
    </style>
</head>
<body>
<nav class="navbar">
    <div class="logo">OYEBI · Agent IA Finance</div>
    <div class="nav-links">
        <a href="/">Accueil</a>
        <a href="/pays">Pays</a>
        <a href="/chat">Assistant IA</a>
        <a href="/login" id="authLink">Connexion</a>
    </div>
</nav>
<div class="container">[CONTENT]</div>
<footer class="footer">OYEBI · Agent IA Finance · Kinshasa, RDC</footer>
<script>
    const authLink = document.getElementById('authLink');
    if (localStorage.getItem('token')) {
        fetch('/api/me').then(r => {
            if (r.ok) { authLink.innerHTML = '<i class="fas fa-user-circle"></i> Mon compte'; authLink.href = '/mon-compte'; }
            else { localStorage.removeItem('token'); }
        });
    }
</script>
</body>
</html>
'''

def render(title, content):
    return BASE.replace("[CONTENT]", content)

# ==================== ACCUEIL ====================
ACCUEIL = '''
<div class="hero">
    <h1>OYEBI · Agent IA Financier</h1>
    <p>Analyse économique | Prévisions | Assistant intelligent</p>
</div>
<div class="grid-3">
    <div class="card-glass"><i class="fas fa-brain"></i><h3>IA surhumaine</h3><p>Prédictions et recommandations avancées</p></div>
    <div class="card-glass"><i class="fas fa-globe"></i><h3>Données mondiales</h3><p>PIB, inflation, chômage par pays</p></div>
    <div class="card-glass"><i class="fas fa-robot"></i><h3>Assistant IA</h3><p>Posez vos questions financières</p></div>
</div>
'''

@app.route('/')
def index():
    return render("Accueil", ACCUEIL)

# ==================== PAYS ====================
@app.route('/pays')
def pays():
    html = '<div class="hero"><h1>🌍 Indicateurs économiques par pays</h1></div><div class="grid-3">'
    for c in COUNTRIES:
        html += f'''
        <div class="card-glass">
            <i class="fas fa-flag-checkered"></i>
            <h3>{c['nom']}</h3>
            <p>PIB: {c['pib']} M$</p>
            <p>Inflation: {c['inflation']}%</p>
            <p>Chômage: {c['chomage']}%</p>
        </div>
        '''
    html += '</div>'
    return render("Pays", html)

# ==================== CHAT IA ====================
CHAT_PAGE = '''
<div class="hero"><h1>🤖 Assistant IA Financier</h1><p>Posez vos questions sur l'économie</p></div>
<div class="card-glass">
    <div class="chat-container" id="chatContainer">
        <div class="chat-message bot-message"><strong>🤖 OYEBI IA :</strong> Bonjour ! Je suis votre assistant financier. Posez-moi des questions sur le PIB, l'inflation, le chômage ou les investissements.</div>
    </div>
    <div style="display:flex; gap:1rem;">
        <input type="text" id="questionInput" placeholder="Ex: Quel est le PIB de la RDC ?" style="flex:1; padding:0.8rem; background:rgba(255,255,255,0.05); border-radius:1rem; color:white; border:1px solid rgba(255,255,255,0.1);">
        <button onclick="askQuestion()" style="background:#FACC15; color:#0A0F1E; border:none; border-radius:1rem; padding:0.8rem 1.5rem; cursor:pointer;">Envoyer</button>
    </div>
</div>
<script>
    async function askQuestion() {
        const q = document.getElementById('questionInput').value;
        if (!q) return;
        const chat = document.getElementById('chatContainer');
        chat.innerHTML += `<div class="chat-message user-message"><strong>👤 Vous :</strong> ${q}</div>`;
        document.getElementById('questionInput').value = '';
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: q})
        });
        const d = await r.json();
        chat.innerHTML += `<div class="chat-message bot-message"><strong>🤖 OYEBI IA :</strong> ${d.reponse}</div>`;
        chat.scrollTop = chat.scrollHeight;
    }
</script>
'''

@app.route('/chat')
def chat():
    return render("Assistant IA", CHAT_PAGE)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    q = request.json.get('question', '').lower()
    reponse = "Je suis OYEBI IA. Je peux vous donner des informations économiques."
    
    for c in COUNTRIES:
        if c['nom'].lower() in q or c['code'].lower() in q:
            reponse = f"{c['nom']} – PIB: {c['pib']} M$, Inflation: {c['inflation']}%, Chômage: {c['chomage']}%."
            break
    
    if 'pib' in q and 'rdc' in q:
        reponse = "Le PIB de la RDC est d'environ 65 000 M$."
    elif 'inflation' in q and 'rdc' in q:
        reponse = "L'inflation en RDC est actuellement de 18,5 %."
    elif 'investir' in q:
        reponse = "Recommandation IA : diversifiez vos investissements entre actions, obligations et matières premières."
    
    return jsonify({"reponse": reponse})

# ==================== CONNEXION ====================
LOGIN_PAGE = '''
<div style="max-width:500px; margin:0 auto;">
    <div class="card-glass">
        <h2 style="text-align:center;" id="formTitle">Connexion</h2>
        <div id="registerForm">
            <input type="text" id="regName" placeholder="Nom" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
            <input type="email" id="regEmail" placeholder="Email" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
            <input type="password" id="regPassword" placeholder="Mot de passe" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
            <button onclick="register()" style="width:100%; padding:0.8rem; background:#FACC15; color:#0A0F1E; border:none; border-radius:0.5rem; font-weight:bold; cursor:pointer;">Créer mon compte</button>
            <p style="text-align:center; margin-top:1rem;"><a href="#" onclick="showLogin()" style="color:#FACC15;">Déjà un compte ? Se connecter</a></p>
        </div>
        <div id="loginForm" style="display:none;">
            <input type="email" id="loginEmail" placeholder="Email" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
            <input type="password" id="loginPassword" placeholder="Mot de passe" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
            <button onclick="login()" style="width:100%; padding:0.8rem; background:#FACC15; color:#0A0F1E; border:none; border-radius:0.5rem; font-weight:bold; cursor:pointer;">Se connecter</button>
            <p style="text-align:center; margin-top:1rem;"><a href="#" onclick="showRegister()" style="color:#FACC15;">Pas de compte ? S'inscrire</a></p>
        </div>
        <div id="message" style="color:#EF4444; text-align:center; margin-top:1rem;"></div>
    </div>
</div>
<script>
    function showLogin() { document.getElementById('registerForm').style.display='none'; document.getElementById('loginForm').style.display='block'; document.getElementById('formTitle').innerText='Connexion'; }
    function showRegister() { document.getElementById('registerForm').style.display='block'; document.getElementById('loginForm').style.display='none'; document.getElementById('formTitle').innerText='Créer un compte'; }
    async function register() { let e=document.getElementById('regEmail').value, p=document.getElementById('regPassword').value; if(!e.includes('@')){ document.getElementById('message').innerHTML='Email invalide'; return; } if(p.length<6){ document.getElementById('message').innerHTML='Mot de passe trop court (min 6)'; return; } let r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('regName').value,email:e,password:p})}); let d=await r.json(); if(r.ok){ document.getElementById('message').innerHTML='<span style="color:#4ADE80;">Compte créé !</span>'; setTimeout(showLogin,2000); }else{ document.getElementById('message').innerHTML=d.error; } }
    async function login() { let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('loginEmail').value,password:document.getElementById('loginPassword').value})}); let d=await r.json(); if(r.ok){ localStorage.setItem('token',d.token); window.location.href='/mon-compte'; }else{ document.getElementById('message').innerHTML=d.error; } }
</script>
'''

@app.route('/login')
def login_page():
    return render("Connexion", LOGIN_PAGE)

MON_COMPTE = '''
<div class="hero"><h1>Mon compte</h1></div>
<div class="card-glass" style="text-align:center;">
    <div id="userInfo"></div>
    <button onclick="logout()" style="margin-top:1rem; background:#EF4444; border:none; border-radius:0.5rem; padding:0.5rem 1rem; color:white; cursor:pointer;">Déconnexion</button>
</div>
<script>
    async function loadUser() { let r=await fetch('/api/me'); if(r.ok){ let u=await r.json(); document.getElementById('userInfo').innerHTML=`<h2>${u.name}</h2><p>${u.email}</p>`; } else { window.location.href='/login'; } }
    async function logout() { await fetch('/api/logout',{method:'POST'}); localStorage.removeItem('token'); window.location.href='/'; }
    loadUser();
</script>
'''

@app.route('/mon-compte')
def mon_compte():
    return render("Mon compte", MON_COMPTE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
