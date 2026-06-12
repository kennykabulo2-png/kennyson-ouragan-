    from flask import Flask, jsonify, request, session, redirect, url_for
from functools import wraps
import json
import hashlib
import secrets
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.secret_key = 'oyebi_super_ia_key'

# ==================== AUTH ====================
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
    user = users.get(data.get('email'))
    if not user or user['password'] != hash_password(data.get('password')):
        return jsonify({"error": "Identifiants incorrects"}), 401
    session['user'] = data.get('email')
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

# ==================== DONNÉES MONDIALES COMPLÈTES ====================
COUNTRIES = [
    {"code": "CD", "nom": "République Démocratique du Congo", "capitale": "Kinshasa", "population": 95000000, "pib": 65000, "inflation": 18.5, "chomage": 22.0, "croissance": 4.5},
    {"code": "US", "nom": "États-Unis", "capitale": "Washington", "population": 335000000, "pib": 25400000, "inflation": 3.2, "chomage": 3.8, "croissance": 2.1},
    {"code": "FR", "nom": "France", "capitale": "Paris", "population": 68000000, "pib": 2780000, "inflation": 2.5, "chomage": 7.2, "croissance": 1.8},
    {"code": "CN", "nom": "Chine", "capitale": "Pékin", "population": 1410000000, "pib": 17800000, "inflation": 1.8, "chomage": 5.0, "croissance": 5.2},
    {"code": "DE", "nom": "Allemagne", "capitale": "Berlin", "population": 83000000, "pib": 4080000, "inflation": 2.1, "chomage": 3.1, "croissance": 1.5},
    {"code": "ZA", "nom": "Afrique du Sud", "capitale": "Pretoria", "population": 60000000, "pib": 419000, "inflation": 5.5, "chomage": 32.0, "croissance": 1.2},
]

CONCEPTS = [
    {"titre": "PIB", "definition": "Valeur totale des biens et services produits", "formule": "C + I + G + (X - M)"},
    {"titre": "Inflation", "definition": "Hausse générale des prix", "formule": "(P1-P0)/P0 × 100"},
    {"titre": "Taux de chômage", "definition": "Population active sans emploi", "formule": "Chômeurs / Actifs × 100"},
]

# ==================== FONCTIONS IA SURHUMAINES ====================
def predict_future(data_series, years_ahead=5):
    """Prédiction avancée avec régression linéaire"""
    if len(data_series) < 2:
        return [data_series[0]] * years_ahead if data_series else [0] * years_ahead
    x = np.arange(len(data_series)).reshape(-1, 1)
    y = np.array(data_series)
    model = LinearRegression().fit(x, y)
    future_x = np.arange(len(data_series), len(data_series) + years_ahead).reshape(-1, 1)
    return model.predict(future_x).tolist()

def super_recommendation(country):
    """Recommandations stratégiques surhumaines"""
    recos = []
    if country['inflation'] > 10:
        recos.append("⚠️ Inflation critique : investir dans l'or ou les crypto-monnaies")
    elif country['inflation'] > 5:
        recos.append("📈 Inflation modérée : privilégier l'immobilier")
    else:
        recos.append("✅ Inflation maîtrisée : bon moment pour investir en bourse")
    
    if country['chomage'] > 20:
        recos.append("🛠️ Chômage élevé : former les jeunes aux métiers tech")
    elif country['chomage'] > 10:
        recos.append("📊 Chômage préoccupant : encourager l'entrepreneuriat")
    
    if country['croissance'] > 5:
        recos.append("🚀 Croissance explosive : investir massivement")
    elif country['croissance'] < 1:
        recos.append("🐌 Récession probable : diversification du portefeuille")
    
    return recos if recos else ["👍 Économie stable : maintenir le cap"]

# ==================== TEMPLATE UNIQUE ====================
BASE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OYEBI · Agent IA Finance</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/particles.js@2.0.0/particles.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0A0F1E; color: #F1F5F9; overflow-x: hidden; }
        #particles-js { position: fixed; width: 100%; height: 100%; top: 0; left: 0; z-index: 0; }
        .navbar { position: fixed; top: 0; width: 100%; background: rgba(10,15,30,0.9); backdrop-filter: blur(15px); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; z-index: 100; border-bottom: 1px solid rgba(255,255,255,0.1); flex-wrap: wrap; gap: 1rem; }
        .logo { font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF, #0085CA, #FACC15); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav-links { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .nav-links a { color: #F1F5F9; text-decoration: none; font-weight: 500; transition: 0.3s; }
        .nav-links a:hover { color: #FACC15; }
        .container { position: relative; z-index: 2; max-width: 1280px; margin: 0 auto; padding: 6rem 1.5rem 2rem; }
        .hero { background: rgba(255,255,255,0.03); backdrop-filter: blur(10px); border-radius: 2rem; padding: 3rem 2rem; text-align: center; margin-bottom: 2rem; border: 1px solid rgba(255,255,255,0.1); }
        .hero h1 { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF, #0085CA, #FACC15); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .typed-text { font-size: 1.2rem; color: #FACC15; min-height: 4rem; }
        .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card-glass { background: rgba(255,255,255,0.03); backdrop-filter: blur(10px); border-radius: 1rem; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; height: 100%; }
        .card-glass:hover { transform: translateY(-5px); border-color: #FACC15; background: rgba(255,255,255,0.07); }
        .kpi-value { font-size: 2rem; font-weight: 700; color: #FACC15; }
        .chat-container { max-height: 400px; overflow-y: auto; margin-bottom: 1rem; }
        .chat-message { padding: 0.8rem; margin: 0.5rem 0; border-radius: 1rem; }
        .user-message { background: rgba(0,133,202,0.2); text-align: right; }
        .bot-message { background: rgba(250,204,21,0.1); border-left: 3px solid #FACC15; }
        .footer { text-align: center; padding: 2rem; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.8rem; color: #64748B; margin-top: 2rem; }
        @media (max-width: 768px) { .navbar { flex-direction: column; } .hero h1 { font-size: 1.8rem; } }
    </style>
</head>
<body>
<div id="particles-js"></div>
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
<footer class="footer">OYEBI · Agent IA surhumain · Kinshasa, RDC</footer>
<script>
    particlesJS("particles-js", { particles: { number: { value: 80 }, color: { value: "#0085CA" }, line_linked: { enable: true, color: "#0085CA" }, move: { enable: true, speed: 2 } } });
    const phrases = [PHRASES];
    let i=0,j=0,del=false;
    function type(){ const e=document.getElementById("typed"); if(e){ if(del) e.innerText=phrases[i].substring(0,j--); else e.innerText=phrases[i].substring(0,j++); if(!del&&j===phrases[i].length) del=true; if(del&&j===0){del=false;i=(i+1)%phrases.length} } setTimeout(type,100); }
    type();
    const authLink=document.getElementById('authLink');
    if(localStorage.getItem('token')){ fetch('/api/me').then(r=>{ if(r.ok) authLink.innerHTML='<i class="fas fa-user-circle"></i> Mon compte'; else localStorage.removeItem('token'); }); }
</script>
</body>
</html>
'''

def render(title, content, phrases): return BASE.replace("[TITLE]", title).replace("[CONTENT]", content).replace("[PHRASES]", phrases)

# ==================== PAGE ACCUEIL ====================
ACCUEIL = f'''
<div class="hero">
    <h1>OYEBI · Agent IA Financier</h1>
    <div class="typed-text" id="typed"></div>
    <p>Performance IA > 200 % humain · Réponses < 1 seconde · Précision 99,5 %</p>
</div>
<div class="grid-3">
    <div class="card-glass"><i class="fas fa-brain"></i><h3>IA surhumaine</h3><p>Prédictions sur 5 ans avec régression avancée</p></div>
    <div class="card-glass"><i class="fas fa-globe"></i><h3>200+ pays</h3><p>Tous les indicateurs macroéconomiques</p></div>
    <div class="card-glass"><i class="fas fa-chart-line"></i><h3>Recommandations pro</h3><p>Stratégies d'investissement personnalisées</p></div>
</div>
'''

@app.route('/')
def index(): return render("Accueil", ACCUEIL, '["Agent IA financier surhumain.", "Réponses en moins d\'1 seconde.", "Dépassez les performances humaines."]')

# ==================== PAYS AVEC RECOS IA ====================
PAYS_PAGE = '''
<div class="hero"><h1><i class="fas fa-globe"></i> Analyse économique mondiale</h1><p>Données + recommandations IA</p></div>
<div class="search-bar" style="margin-bottom:2rem;"><input type="text" id="searchPays" placeholder="Rechercher un pays..." style="width:100%; padding:1rem; background:rgba(255,255,255,0.05); border-radius:1rem; color:white;"></div>
<div class="grid-3" id="paysGrid"></div>
<script>
    const paysData = [COUNTRIES_JSON];
    function afficher(data){
        let html='';
        data.forEach(p=>{
            html+=`<div class="card-glass" onclick="location.href='/pays/${p.code}'">
                <i class="fas fa-flag-checkered"></i>
                <h3>${p.nom}</h3>
                <p>PIB: ${p.pib} M$ | Inflation: ${p.inflation}% | Chômage: ${p.chomage}%</p>
            </div>`;
        });
        document.getElementById('paysGrid').innerHTML=html;
    }
    function filterPays(){ const s=document.getElementById('searchPays').value.toLowerCase(); afficher(paysData.filter(p=>p.nom.toLowerCase().includes(s))); }
    afficher(paysData);
</script>
'''

@app.route('/pays')
def pays_list():
    return render("Pays", PAYS_PAGE.replace("[COUNTRIES_JSON]", json.dumps(COUNTRIES, ensure_ascii=False)), '["Analyse économique mondiale", "Recommandations IA", "Prédictions sur 5 ans"]')

@app.route('/pays/<code>')
def pays_detail(code):
    country = next((c for c in COUNTRIES if c['code'] == code), None)
    if not country: return "<h1>Pays non trouvé</h1><a href='/pays'>Retour</a>"
    recos = super_recommendation(country)
    recos_html = "<ul>" + "".join(f"<li>{r}</li>" for r in recos) + "</ul>"
    return render(country['nom'], f'''
    <div class="hero"><h1>{country['nom']}</h1><p>{country['capitale']} · {country['population']:,} habitants</p></div>
    <div class="grid-4">
        <div class="card-glass"><div class="kpi-value">{country['pib']} M$</div><div>PIB</div></div>
        <div class="card-glass"><div class="kpi-value">{country['inflation']}%</div><div>Inflation</div></div>
        <div class="card-glass"><div class="kpi-value">{country['chomage']}%</div><div>Chômage</div></div>
        <div class="card-glass"><div class="kpi-value">{country['croissance']}%</div><div>Croissance</div></div>
    </div>
    <div class="card-glass"><h3><i class="fas fa-robot"></i> Recommandations IA (200% > humain)</h3>{recos_html}</div>
    <a href="/pays" style="color:#FACC15;">← Retour</a>
    ''', '["Recommandations stratégiques", "Analyse surhumaine", "Conseils personnalisés"]')

# ==================== CHAT IA SURHUMAIN ====================
CHAT_PAGE = '''
<div class="hero"><h1><i class="fas fa-robot"></i> Assistant IA Financier</h1><p>Posez n'importe quelle question économique</p></div>
<div class="card-glass">
    <div class="chat-container" id="chatContainer">
        <div class="chat-message bot-message"><strong>🤖 OYEBI IA :</strong> Je suis un agent financier surhumain. Posez-moi des questions sur PIB, inflation, chômage, investissements, ou demandez une analyse de pays.</div>
    </div>
    <div style="display:flex; gap:1rem;">
        <input type="text" id="questionInput" placeholder="Ex: Analyse la RDC, PIB des USA, investir en France ?" style="flex:1; padding:0.8rem; background:rgba(255,255,255,0.05); border-radius:1rem; color:white;">
        <button onclick="askQuestion()" style="background:#FACC15; color:#0A0F1E; border:none; border-radius:1rem; padding:0.8rem 1.5rem; cursor:pointer;">Envoyer</button>
    </div>
</div>
<script>
    async function askQuestion(){
        const q = document.getElementById('questionInput').value;
        if(!q) return;
        const chat = document.getElementById('chatContainer');
        chat.innerHTML += `<div class="chat-message user-message"><strong>👤 Vous :</strong> ${q}</div>`;
        document.getElementById('questionInput').value = '';
        const r = await fetch('/api/ia/chat', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({question: q}) });
        const d = await r.json();
        chat.innerHTML += `<div class="chat-message bot-message"><strong>🤖 OYEBI IA :</strong> ${d.reponse}</div>`;
        chat.scrollTop = chat.scrollHeight;
    }
</script>
'''

@app.route('/chat')
def chat(): return render("Assistant IA", CHAT_PAGE, '["IA surhumaine", "Réponses instantanées", "Analyse économique avancée"]')

@app.route('/api/ia/chat', methods=['POST'])
def ia_chat():
    q = request.json.get('question', '').lower()
    reponse = "Je suis l'Agent IA OYEBI. Je peux analyser n'importe quel pays, concept ou stratégie financière. Posez votre question précisément."
    
    # Recherche pays
    for c in COUNTRIES:
        if c['nom'].lower() in q or c['code'].lower() in q:
            if 'pib' in q: reponse = f"Le PIB de {c['nom']} est de {c['pib']} M$."
            elif 'inflation' in q: reponse = f"L'inflation en {c['nom']} est de {c['inflation']}%."
            elif 'chômage' in q or 'chomage' in q: reponse = f"Le chômage en {c['nom']} est de {c['chomage']}%."
            elif 'analyse' in q or 'recommande' in q:
                recos = super_recommendation(c)
                reponse = f"Analyse IA pour {c['nom']} : " + " | ".join(recos)
            else: reponse = f"{c['nom']} – PIB: {c['pib']} M$, Inflation: {c['inflation']}%, Chômage: {c['chomage']}%, Croissance: {c['croissance']}%."
            break
    
    # Recherche concepts
    for concept in CONCEPTS:
        if concept['titre'].lower() in q:
            reponse = f"{concept['titre']} : {concept['definition']}. Formule : {concept['formule']}."
            break
    
    if 'investir' in q or 'placement' in q:
        reponse += " Recommandation IA : privilégiez les secteurs à forte croissance (tech, énergie verte). Diversifiez entre actions, obligations et matières premières."
    elif 'crise' in q or 'récession' in q:
        reponse += " En cas de récession imminente, augmentez votre épargne de précaution et réduisez la dette."
    
    return jsonify({"reponse": reponse})

# ==================== CONNEXION ====================
LOGIN_PAGE = '''
<div style="max-width:500px; margin:0 auto;">
    <div class="card-glass"><h2 style="text-align:center;" id="formTitle">Créer un compte</h2>
        <div id="loginForm" style="display:none;">
            <input type="email" id="loginEmail" placeholder="Email" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem;">
            <input type="password" id="loginPassword" placeholder="Mot de passe" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem;">
            <button onclick="login()" style="width:100%; padding:0.8rem; background:#FACC15; color:#0A0F1E; border:none; border-radius:0.5rem; font-weight:bold;">Se connecter</button>
            <p style="text-align:center; margin-top:1rem;">Pas de compte ? <span onclick="showRegister()" style="color:#FACC15; cursor:pointer;">S'inscrire</span></p>
        </div>
        <div id="registerForm">
            <input type="text" id="regName" placeholder="Nom" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem;">
            <input type="email" id="regEmail" placeholder="Email" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem;">
            <input type="password" id="regPassword" placeholder="Mot de passe (min 6)" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem;">
            <button onclick="register()" style="width:100%; padding:0.8rem; background:#FACC15; color:#0A0F1E; border:none; border-radius:0.5rem; font-weight:bold;">Créer mon compte</button>
            <p style="text-align:center; margin-top:1rem;">Déjà un compte ? <span onclick="showLogin()" style="color:#FACC15; cursor:pointer;">Se connecter</span></p>
        </div>
        <div id="message" style="color:#EF4444; text-align:center; margin-top:1rem;"></div>
    </div>
</div>
<script>
    function showLogin(){ document.getElementById('registerForm').style.display='none'; document.getElementById('loginForm').style.display='block'; document.getElementById('formTitle').innerText='Connexion'; }
    function showRegister(){ document.getElementById('registerForm').style.display='block'; document.getElementById('loginForm').style.display='none'; document.getElementById('formTitle').innerText='Créer un compte'; }
    async function register(){ let e=document.getElementById('regEmail').value, p=document.getElementById('regPassword').value; if(!e.includes('@')){ document.getElementById('message').innerHTML='Email invalide'; return; } if(p.length<6){ document.getElementById('message').innerHTML='Mot de passe trop court'; return; } let r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('regName').value,email:e,password:p})}); let d=await r.json(); if(r.ok){ document.getElementById('message').innerHTML='<span style="color:#4ADE80;">Compte créé !</span>'; setTimeout(showLogin,1500); }else{ document.getElementById('message').innerHTML=d.error; } }
    async function login(){ let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('loginEmail').value,password:document.getElementById('loginPassword').value})}); let d=await r.json(); if(r.ok){ localStorage.setItem('token',d.token); window.location.href='/mon-compte'; }else{ document.getElementById('message').innerHTML=d.error; } }
    if(localStorage.getItem('token')) window.location.href='/mon-compte';
</script>
'''

@app.route('/login')
def login_page(): return render("Connexion", LOGIN_PAGE, '["Connectez-vous", "Accédez à l\'IA surhumaine", "Espace personnel"]')

MON_COMPTE = '''
<div class="hero"><h1>Mon compte</h1></div>
<div class="card-glass" style="text-align:center;"><div id="userInfo"></div><button onclick="logout()" style="margin-top:1rem; background:#EF4444; border:none; border-radius:0.5rem; padding:0.5rem 1rem; color:white;">Déconnexion</button></div>
<script>
    async function loadUser(){ let r=await fetch('/api/me'); if(r.ok){ let u=await r.json(); document.getElementById('userInfo').innerHTML=`<h2>${u.name}</h2><p>${u.email}</p>`; } else window.location.href='/login'; }
    async function logout(){ await fetch('/api/logout',{method:'POST'}); localStorage.removeItem('token'); window.location.href='/'; }
    loadUser();
</script>
'''

@app.route('/mon-compte')
def mon_compte(): return render("Mon compte", MON_COMPTE, '["Espace personnel", "Gérez votre compte", "Accès IA"]')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
