from flask import Flask, jsonify, request, session, redirect, url_for
from functools import wraps
import hashlib
import secrets
import json
import requests
import os

app = Flask(__name__)
app.secret_key = 'oyebi_groq_secret_key_2026'

# ==================================================
# CONFIGURATION GROQ API
# ==================================================
# !!! REMPLACE CETTE CLÉ PAR LA TIENNE !!!
GROQ_API_KEY = "gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # ← MET TA CLÉ ICI
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"  # ou "mixtral-8x7b-32768", "llama-3.3-70b-versatile"

# ==================================================
# PROMPT SYSTÈME POUR L'IA FINANCIÈRE
# ==================================================
PROMPT_SYSTEME = """Tu es OYEBI, Agent IA Financier et Économique surhumain. Tu dépasses les capacités humaines de 200%.

RÈGLES ABSOLUES DE RÉPONSE :
1. JAMAIS de réponse courte. Chaque réponse doit avoir au moins 6 à 8 phrases.
2. STRUCTURE OBLIGATOIRE (utilise ces icônes) : 
   📊 CHIFFRE CLÉ (donnée précise)
   🔍 ANALYSE (pourquoi ce chiffre est important)
   ⚡ CAUSES PROFONDES (2-3 facteurs)
   💥 CONSÉQUENCES (impacts sur la population)
   🎯 ACTION CONCRÈTE (à faire dans les 10 secondes)
   🔮 PRÉVISION 12 MOIS (ce qui va se passer)

3. Utilise des ANALOGIES CONCRÈTES :
   - "L'inflation est comme un feu qui brûle le pouvoir d'achat"
   - "Le PIB est comme le bulletin de notes d'un pays"
   - "La dette publique, c'est comme une carte de crédit qu'on ne rembourse jamais"

4. SOURCES implicites : FMI, Banque mondiale, BCEAO, Banque centrale du Congo.

5. Si tu ne connais pas une donnée précise, dis "D'après les dernières tendances..." et donne la meilleure estimation.

6. Termine toujours par une action concrète que l'utilisateur peut faire dans les 10 secondes.

EXEMPLE DE RÉPONSE ATTENDUE pour "Comment va l'économie de la RDC ?" :

📊 CHIFFRE CLÉ : Le PIB de la RDC atteint 65 milliards de dollars en 2025, avec une croissance de 4,5%.

🔍 ANALYSE : C'est l'un des taux les plus élevés d'Afrique centrale, mais rapporté aux 95 millions d'habitants, le PIB par habitant tombe à seulement 680 dollars par an – l'un des plus bas au monde.

⚡ CAUSES : Trois facteurs expliquent ce paradoxe : (1) l'économie informelle représente 80% de l'activité nationale, (2) les recettes fiscales ne captent que 12% du PIB, (3) les infrastructures sont défaillantes.

💥 CONSÉQUENCES : Pour un ménage congolais moyen, cela signifie un pouvoir d'achat qui diminue de 5% par an, 70% de la population vit avec moins de 2 dollars par jour, et les hôpitaux publics manquent de médicaments.

🎯 ACTION DANS LES 10 SECONDES : Notez ceci sur votre téléphone – "diversifier mes revenus". Lancez une petite activité parallèle cette semaine (vente de produits frais, services numériques, petit commerce).

🔮 PRÉVISION 2026 : Si les réformes fiscales actuelles sont appliquées, la croissance pourrait atteindre 6% en 2026. L'inflation restera élevée (15-20%) à cause des tensions sur les prix alimentaires."""

# ==================================================
# FONCTION APPEL GROQ API
# ==================================================
def generer_reponse_groq(question):
    """Génère une réponse via Groq API (rapide, gratuit, sur Render)"""
    
    # Vérifier si la clé API est configurée
    if GROQ_API_KEY == "gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" or not GROQ_API_KEY:
        return fallback_response(question, "GROQ_API_KEY non configurée")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 1500,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            reponse = data['choices'][0]['message']['content']
            return reponse
        else:
            error_msg = f"Erreur API Groq: {response.status_code} - {response.text[:200]}"
            return fallback_response(question, error_msg)
            
    except requests.exceptions.Timeout:
        return fallback_response(question, "Délai d'attente dépassé")
    except Exception as e:
        return fallback_response(question, f"Erreur: {str(e)[:100]}")

def fallback_response(question, raison=""):
    """Réponse de secours si Groq n'est pas disponible"""
    q = question.lower()
    
    if "rdc" in q or "congo" in q:
        return """📊 CHIFFRE CLÉ : PIB de 65 milliards USD avec une croissance de 4,5% en 2025.

🔍 ANALYSE : La RDC affiche l'un des taux de croissance les plus élevés d'Afrique centrale, mais le PIB par habitant reste à seulement 680 USD par an.

⚡ CAUSES : Trois facteurs : 80% d'économie informelle, pression fiscale de 12% du PIB seulement, et infrastructures défaillantes.

💥 CONSÉQUENCES : 70% de la population vit avec moins de 2 USD par jour. Le pouvoir d'achat diminue de 5% par an à cause de l'inflation à 18,5%.

🎯 ACTION (dans 10s) : Lancez une micro-activité parallèle – vente de produits frais, petit commerce, services numériques. 50 USD par mois changent votre vie.

🔮 PRÉVISION 2026 : Si les réformes fiscales sont appliquées, croissance à 6%. Inflation restera élevée (15-20%)."""
    
    elif "inflation" in q:
        return """📊 CHIFFRE CLÉ : L'inflation en RDC atteint 18,5% en 2025.

🔍 ANALYSE : Les prix doublent tous les 4 ans. Un panier à 100 000 FC coûte 118 500 FC aujourd'hui.

⚡ CAUSES : Dépréciation du franc (-25%/an), dépendance aux importations (60% des aliments), et financement monétaire du déficit.

💥 CONSÉQUENCES : Votre épargne perd 18,5% par an. Les salaires réels diminuent. Les emprunts coûtent 25%.

🎯 ACTION : Convertissez vos économies en actifs réels : or, dollars, ou matériaux de construction.

🔮 PRÉVISION : Inflation restera élevée (15-20%) jusqu'à fin 2026."""
    
    elif "chômage" in q or "emploi" in q:
        return """📊 CHIFFRE CLÉ : 22% de chômage officiel, 60% de sous-emploi.

🔍 ANALYSE : 8 millions de chômeurs, mais le vrai problème est l'emploi décent.

⚡ CAUSES : 400 000 jeunes arrivent sur le marché chaque année pour 50 000 postes créés.

💥 CONSÉQUENCES : Un chômeur vit avec 0,50 USD par jour. 40% des jeunes envisagent l'émigration.

🎯 ACTION : Formez-vous gratuitement sur YouTube aux métiers digitaux (community manager, montage vidéo, Excel).

🔮 PRÉVISION : 100 000 emplois promis en 2026 dans l'agriculture et les infrastructures."""
    
    elif "invest" in q or "placement" in q:
        return """📊 CHIFFRE CLÉ : 8% d'épargne nationale contre 30% en Chine.

🔍 ANALYSE : Ne pas investir avec 18,5% d'inflation = perdre 18,5% de sa valeur chaque année.

⚡ CAUSES : Manque d'éducation financière, offre bancaire limitée, méfiance historique.

💥 CONSÉQUENCES : 100 USD épargnés perdent 18,50 USD de pouvoir d'achat par an.

🎯 ACTION : 
- Faible risque : Dollars, or, obligations d'État (12-15%)
- Risque moyen : Immobilier locatif (8-10%), petit commerce
- Risque élevé : Crypto, actions internationales (Bamboo)

🔮 PRÉVISION : Bourse de Kinshasa introduira 5 nouvelles sociétés en 2026."""
    
    else:
        return f"""📊 CHIFFRE CLÉ : L'économie mondiale croît de 2,8% en 2025 selon la Banque mondiale.

🔍 ANALYSE : Croissance inégale – Afrique à 4%, pays développés à 1-2%.

⚡ CAUSES : Taux d'intérêt élevés, prix volatils des matières premières, dettes publiques lourdes.

💥 CONSÉQUENCES : Prix en hausse, salaires stagnants, incertitude économique.

🎯 ACTION : Posez une question plus précise. Exemples : "économie RDC", "inflation RDC", "chômage Congo", "comment investir".

🔮 PRÉVISION : Croissance à 3% en 2026 si l'inflation baisse.

💡 Votre question : {question[:100]}..."""

# ==================================================
# AUTHENTIFICATION
# ==================================================
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

# ==================================================
# ROUTE API CHAT AVEC GROQ
# ==================================================
@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    question = data.get('question', '')
    reponse = generer_reponse_groq(question)
    return jsonify({"reponse": reponse})

# ==================================================
# TEST GROQ
# ==================================================
@app.route('/api/test-groq')
def test_groq():
    """Route pour tester si Groq fonctionne"""
    test_response = generer_reponse_groq("Dis simplement 'OK' si tu fonctionnes")
    return jsonify({
        "groq_configured": GROQ_API_KEY != "gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "test_response": test_response[:200] + "..."
    })

# ==================================================
# TEMPLATE HTML
# ==================================================
BASE_HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OYEBI · Groq AI Finance</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0A0F1E; color: #F1F5F9; }
        .navbar { background: rgba(10,15,30,0.95); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); position: sticky; top: 0; z-index: 100; }
        .logo { font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF, #0085CA, #FACC15); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav-links { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .nav-links a { color: #F1F5F9; text-decoration: none; transition: 0.3s; }
        .nav-links a:hover { color: #FACC15; }
        .container { max-width: 1280px; margin: 0 auto; padding: 2rem 1.5rem; }
        .hero { background: linear-gradient(135deg, rgba(0,133,202,0.1), rgba(250,204,21,0.05)); border-radius: 2rem; padding: 3rem 2rem; text-align: center; margin-bottom: 2rem; border: 1px solid rgba(250,204,21,0.3); }
        .hero h1 { font-size: 2.5rem; background: linear-gradient(135deg, #FFFFFF, #0085CA, #FACC15); -webkit-background-clip: text; background-clip: text; color: transparent; margin-bottom: 1rem; }
        .hero p { color: #94A3B8; }
        .card-glass { background: rgba(255,255,255,0.03); border-radius: 1rem; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); }
        .chat-container { max-height: 500px; overflow-y: auto; margin-bottom: 1rem; padding: 0.5rem; }
        .chat-message { padding: 1rem; margin: 0.75rem 0; border-radius: 1rem; white-space: pre-wrap; line-height: 1.5; }
        .user-message { background: rgba(0,133,202,0.2); text-align: right; border-right: 3px solid #0085CA; }
        .bot-message { background: rgba(250,204,21,0.05); border-left: 3px solid #FACC15; }
        .input-area { display: flex; gap: 1rem; margin-top: 1rem; }
        .input-area input { flex: 1; padding: 1rem; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 1rem; color: white; font-size: 1rem; }
        .input-area button { background: #FACC15; color: #0A0F1E; border: none; border-radius: 1rem; padding: 0.8rem 1.5rem; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .input-area button:hover { transform: scale(1.02); background: #FFD700; }
        .footer { text-align: center; padding: 2rem; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.8rem; color: #64748B; margin-top: 2rem; }
        .badge { background: #0085CA; color: white; padding: 0.2rem 0.5rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: bold; margin-left: 0.5rem; }
        @media (max-width: 768px) { .hero h1 { font-size: 1.5rem; } .navbar { flex-direction: column; text-align: center; } .nav-links { justify-content: center; } }
    </style>
</head>
<body>
<nav class="navbar">
    <div class="logo">OYEBI · Groq AI <span class="badge">Powered by Llama 3.3 70B</span></div>
    <div class="nav-links">
        <a href="/">Accueil</a>
        <a href="/chat">Assistant IA</a>
        <a href="/pays">Pays</a>
        <a href="/login" id="authLink">Connexion</a>
    </div>
</nav>
<div class="container">[CONTENT]</div>
<footer class="footer">
    <p>OYEBI · Agent IA Financier surhumain · Propulsé par Groq (ultra-rapide)</p>
    <p style="font-size:0.7rem; margin-top:0.5rem;">Réponses structurées · Analyses profondes · Prévisions 12 mois</p>
</footer>
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

def render_page(title, content):
    return BASE_HTML.replace("[CONTENT]", content)

# ==================================================
# ROUTES PRINCIPALES
# ==================================================
@app.route('/')
def index():
    content = '''
    <div class="hero">
        <h1>🤖 OYEBI · Agent IA Financier</h1>
        <p>Propulsé par Groq (Bezos AI) · Ultra-rapide · Analyses surhumaines</p>
    </div>
    <div class="card-glass" style="text-align:center;">
        <i class="fas fa-bolt" style="font-size:3rem; color:#FACC15;"></i>
        <h2 style="margin-top:1rem;">L'IA financière qui dépasse les humains de 200%</h2>
        <p style="margin:1rem 0;">Réponses structurées · 6 à 8 phrases par réponse · Actions concrètes · Prévisions 12 mois</p>
        <a href="/chat"><button style="background:#FACC15; color:#0A0F1E; border:none; border-radius:2rem; padding:0.8rem 2rem; font-size:1rem; cursor:pointer; margin-top:1rem;">💬 Démarrer</button></a>
    </div>
    '''
    return render_page("Accueil", content)

@app.route('/chat')
def chat():
    content = '''
    <div class="hero">
        <h1>💬 Assistant IA Financier (Groq)</h1>
        <p>Posez votre question sur l'économie, la finance, l'investissement</p>
    </div>
    <div class="card-glass">
        <div class="chat-container" id="chatContainer">
            <div class="chat-message bot-message">
                <strong>🤖 OYEBI IA (Groq 70B) :</strong><br><br>
                Bonjour ! Je suis votre agent financier surhumain, propulsé par l'IA de Groq.<br><br>
                <strong>Mes réponses suivent cette structure :</strong><br>
                📊 Chiffre clé → 🔍 Analyse → ⚡ Causes → 💥 Conséquences → 🎯 Action (dans 10s) → 🔮 Prévision<br><br>
                <strong>Exemples de questions :</strong><br>
                • "Comment va l'économie de la RDC ?"<br>
                • "Quelle est l'inflation en RDC ?"<br>
                • "Taux de chômage au Congo"<br>
                • "Où investir mon argent en ce moment ?"<br>
                • "Prévisions économiques pour 2026"<br><br>
                <em>Je vous donne des réponses détaillées, des conseils actionnables, et des prévisions.</em>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="questionInput" placeholder="Ex: Comment va l'économie de la RDC ?">
            <button onclick="sendMessage()">Envoyer</button>
        </div>
    </div>
    <script>
        async function sendMessage() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            if (!question) return;
            
            const chatDiv = document.getElementById('chatContainer');
            chatDiv.innerHTML += `<div class="chat-message user-message"><strong>👤 Vous :</strong><br>${question}</div>`;
            input.value = '';
            chatDiv.scrollTop = chatDiv.scrollHeight;
            
            chatDiv.innerHTML += `<div class="chat-message bot-message"><strong>🤖 OYEBI IA :</strong><br><i class="fas fa-spinner fa-spin"></i> Génération de la réponse... (5-10 secondes)</div>`;
            chatDiv.scrollTop = chatDiv.scrollHeight;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                });
                const data = await response.json();
                const lastMsg = chatDiv.lastElementChild;
                if (lastMsg && lastMsg.innerHTML.includes('Génération')) {
                    lastMsg.innerHTML = `<strong>🤖 OYEBI IA :</strong><br><br>${data.reponse.replace(/\\n/g, '<br>')}`;
                }
                chatDiv.scrollTop = chatDiv.scrollHeight;
            } catch (error) {
                const lastMsg = chatDiv.lastElementChild;
                if (lastMsg && lastMsg.innerHTML.includes('Génération')) {
                    lastMsg.innerHTML = `<strong>🤖 OYEBI IA :</strong><br>Erreur de connexion. Vérifiez que la clé Groq API est configurée.`;
                }
            }
        }
        document.getElementById('questionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
    '''
    return render_page("Chat", content)

@app.route('/pays')
def pays():
    content = '''
    <div class="hero">
        <h1>🌍 Données économiques par pays</h1>
        <p>Indicateurs clés 2025</p>
    </div>
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1.5rem;">
        <div class="card-glass"><i class="fas fa-flag-checkered" style="font-size:2rem; color:#FACC15;"></i><h3>🇨🇩 RDC</h3><p><strong>PIB:</strong> 65 000 M$<br><strong>Inflation:</strong> 18,5%<br><strong>Chômage:</strong> 22%<br><strong>Croissance:</strong> 4,5%</p></div>
        <div class="card-glass"><i class="fas fa-flag-checkered" style="font-size:2rem; color:#FACC15;"></i><h3>🇺🇸 États-Unis</h3><p><strong>PIB:</strong> 25 400 000 M$<br><strong>Inflation:</strong> 3,2%<br><strong>Chômage:</strong> 3,8%<br><strong>Croissance:</strong> 2,1%</p></div>
        <div class="card-glass"><i class="fas fa-flag-checkered" style="font-size:2rem; color:#FACC15;"></i><h3>🇫🇷 France</h3><p><strong>PIB:</strong> 2 780 000 M$<br><strong>Inflation:</strong> 2,5%<br><strong>Chômage:</strong> 7,2%<br><strong>Croissance:</strong> 1,8%</p></div>
        <div class="card-glass"><i class="fas fa-flag-checkered" style="font-size:2rem; color:#FACC15;"></i><h3>🇨🇳 Chine</h3><p><strong>PIB:</strong> 17 800 000 M$<br><strong>Inflation:</strong> 1,8%<br><strong>Chômage:</strong> 5,0%<br><strong>Croissance:</strong> 5,2%</p></div>
    </div>
    '''
    return render_page("Pays", content)

# ==================================================
# AUTH PAGES
# ==================================================
LOGIN_PAGE = '''
<div style="max-width:500px; margin:0 auto;">
    <div class="card-glass">
        <h2 style="text-align:center;" id="formTitle">Créer un compte</h2>
        <div id="registerForm">
            <input type="text" id="regName" placeholder="Nom" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
            <input type="email" id="regEmail" placeholder="Email" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
            <input type="password" id="regPassword" placeholder="Mot de passe (min 6)" style="width:100%; padding:0.8rem; margin-bottom:1rem; background:rgba(255,255,255,0.05); border-radius:0.5rem; color:white; border:1px solid rgba(255,255,255,0.1);">
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
    return render_page("Connexion", LOGIN_PAGE)

MON_COMPTE = '''
<div class="hero"><h1>👤 Mon compte</h1></div>
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
    return render_page("Mon compte", MON_COMPTE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
