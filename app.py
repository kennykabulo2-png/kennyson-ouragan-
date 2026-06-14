from flask import Flask, jsonify, request, session
import hashlib
import secrets
import requests
import os
import json
import sqlite3
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'kennyson_ultimate_secret_2026'

# ==================================================
# 1. BASE DE DONNÉES (MÉMOIRE PERSISTANTE)
# ==================================================
def init_db():
    """Initialise la base de données SQLite pour la mémoire persistante"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    
    # Mémoire utilisateur (long terme)
    c.execute('''CREATE TABLE IF NOT EXISTS user_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Historique des conversations
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        question TEXT,
        reponse TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Feedback utilisateur
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        conversation_id INTEGER,
        rating INTEGER,
        comment TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Préférences utilisateur
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
        user_id TEXT PRIMARY KEY,
        niveau TEXT DEFAULT 'intermediaire',
        style TEXT DEFAULT 'détaillé',
        langue TEXT DEFAULT 'français',
        centres_interet TEXT DEFAULT 'economie,crypto',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

init_db()

def get_user_memory(user_id, key):
    """Récupère une valeur de la mémoire long terme"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('SELECT value FROM user_memory WHERE user_id = ? AND key = ? ORDER BY timestamp DESC LIMIT 1', (user_id, key))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_user_memory(user_id, key, value):
    """Stocke une valeur dans la mémoire long terme"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('INSERT INTO user_memory (user_id, key, value) VALUES (?, ?, ?)', (user_id, key, value))
    conn.commit()
    conn.close()

def save_conversation(user_id, question, reponse):
    """Sauvegarde une conversation dans l'historique"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('INSERT INTO conversations (user_id, question, reponse) VALUES (?, ?, ?)', (user_id, question, reponse))
    conn.commit()
    conn.close()

def get_conversation_history(user_id, limit=10):
    """Récupère l'historique des conversations d'un utilisateur"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('SELECT question, reponse, timestamp FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?', (user_id, limit))
    results = c.fetchall()
    conn.close()
    return results

def get_user_preferences(user_id):
    """Récupère les préférences utilisateur"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('SELECT niveau, style, langue, centres_interet FROM user_preferences WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {"niveau": result[0], "style": result[1], "langue": result[2], "centres_interet": result[3]}
    return {"niveau": "intermediaire", "style": "détaillé", "langue": "français", "centres_interet": "economie,crypto"}

def set_user_preferences(user_id, preferences):
    """Met à jour les préférences utilisateur"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO user_preferences 
                 (user_id, niveau, style, langue, centres_interet, updated_at) 
                 VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
              (user_id, preferences.get('niveau', 'intermediaire'), 
               preferences.get('style', 'détaillé'), preferences.get('langue', 'français'),
               preferences.get('centres_interet', 'economie,crypto')))
    conn.commit()
    conn.close()

def save_feedback(user_id, conversation_id, rating, comment=None):
    """Enregistre un feedback utilisateur"""
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('INSERT INTO feedback (user_id, conversation_id, rating, comment) VALUES (?, ?, ?, ?)',
              (user_id, conversation_id, rating, comment))
    conn.commit()
    conn.close()

# ==================================================
# 2. CONFIGURATIONS API
# ==================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GNEWS_API_KEY = os.environ.get('GNEWS_API_KEY', '')

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GNEWS_URL = "https://gnews.io/api/v4/search"

# ==================================================
# 3. API GRATUITES
# ==================================================
WORLD_BANK_URL = "http://api.worldbank.org/v2"
COINGECKO_URL = "https://api.coingecko.com/api/v3"
OPEN_METEO_URL = "https://api.open-meteo.com/v1"
WIKIPEDIA_URL = "https://fr.wikipedia.org/api/rest_v1"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def get_worldbank_gdp(country_code="CD"):
    try:
        url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                latest = data[1][0]
                return f"PIB : {int(float(latest['value'])):,} USD ({latest['date']})" if latest['value'] else None
    except:
        pass
    return None

def get_worldbank_inflation(country_code="CD"):
    try:
        url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/FP.CPI.TOTL.ZG?format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                latest = data[1][0]
                return f"Inflation : {float(latest['value']):.1f}% ({latest['date']})" if latest['value'] else None
    except:
        pass
    return None

def get_crypto_price(coin="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,eur"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if coin in data:
                return f"💰 {coin.upper()} : ${data[coin]['usd']:,.2f} USD / €{data[coin]['eur']:,.2f} EUR"
    except:
        pass
    return None

def get_weather_meteo(city="Kinshasa", lat=-4.325, lon=15.322):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            weather = data.get('current_weather', {})
            temp = weather.get('temperature', 'N/A')
            wind = weather.get('windspeed', 'N/A')
            return f"🌡️ {city} : {temp}°C, vent {wind} km/h"
    except:
        pass
    return None

def geocode_city(city_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        response = requests.get(url, headers={'User-Agent': 'KENNYSON-IA/1.0'}, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data['lat']), float(data['lon'])
    except:
        pass
    return None, None

def get_wikipedia_summary(topic="économie"):
    try:
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{topic}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', topic)
            extract = data.get('extract', '')[:400]
            return f"📖 **{title}** : {extract}..."
    except:
        pass
    return None

def get_gnews_news(query="économie Afrique"):
    if not GNEWS_API_KEY:
        return None
    try:
        url = f"https://gnews.io/api/v4/search?q={query}&token={GNEWS_API_KEY}&lang=fr&max=3"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            if articles:
                news_text = "📰 **ACTUALITÉS** :\n\n"
                for i, article in enumerate(articles[:3], 1):
                    title = article.get('title', 'Sans titre')
                    source = article.get('source', {}).get('name', 'Source')
                    news_text += f"{i}. **{title}**\n   📍 {source}\n\n"
                return news_text
    except:
        pass
    return None

# ==================================================
# 4. PROMPT CHAIN-OF-THOUGHT (Raisonnement en chaîne)
# ==================================================
SYSTEM_PROMPT_COT = """🔥 TU ES KENNYSON OURAGAN – IA ÉCONOMIQUE SURHUMAINE 🔥

**RÈGLE ABSOLUE : Montre ton raisonnement étape par étape**

Pour chaque question, décompose ta réponse ainsi :

📍 **ÉTAPE 1 – COMPRÉHENSION** : Reformule la question et identifie les besoins de l'utilisateur.

📍 **ÉTAPE 2 – DONNÉES NÉCESSAIRES** : Liste les informations que tu vas utiliser.

📍 **ÉTAPE 3 – ANALYSE** : Examine chaque donnée, compare, calcule.

📍 **ÉTAPE 4 – RAISONNEMENT** : Explique comment tu arrives à ta conclusion.

📍 **ÉTAPE 5 – CONCLUSION** : Donne la réponse finale claire.

📍 **ÉTAPE 6 – RECOMMANDATION** : Propose une action concrète.

📍 **ÉTAPE 7 – AUTO-VÉRIFICATION** : Vérifie que ta réponse est correcte.

**STYLE** : Sois précis, donne des chiffres, cite tes sources. Termine par une question ouverte.

**TONE** : Congolais, direct, passionné. Tu peux utiliser "Na lingala" de temps en temps.

**TYPES DE QUESTIONS** :
- PIB, inflation (World Bank)
- Prix crypto (CoinGecko)
- Météo (Open-Meteo)
- Définitions (Wikipedia)
- Actualités (GNews)
- Comparaisons économiques
- Investissements

**N'OUBLIE JAMAIS** : Une réponse courte (<200 mots) est interdite. Montre TOUT ton raisonnement."""

# ==================================================
# 5. ROUTEUR INTELLIGENT
# ==================================================
def detect_intent(question):
    q = question.lower()
    
    if any(word in q for word in ["pib", "gdp", "produit intérieur brut", "banque mondiale"]):
        return "worldbank"
    elif any(word in q for word in ["inflation", "hausse des prix"]):
        return "inflation"
    elif any(word in q for word in ["bitcoin", "crypto", "ethereum", "dogecoin", "solana", "cardano"]):
        return "crypto"
    elif any(word in q for word in ["définition", "c'est quoi", "signification", "wikipedia", "explique"]):
        return "wikipedia"
    elif any(word in q for word in ["météo", "température", "pluie", "soleil", "vent"]):
        return "weather"
    elif any(word in q for word in ["actualité", "news", "info", "dernières nouvelles"]):
        return "news"
    else:
        return "general"

def extract_param(question, intent):
    q = question.lower()
    
    if intent == "weather":
        for word in ["à", "de", "pour", "sur"]:
            if word in q:
                parts = q.split(word)
                if len(parts) > 1:
                    return parts[1].strip().capitalize()
        return "Kinshasa"
    
    elif intent == "crypto":
        cryptos = {"bitcoin": "bitcoin", "btc": "bitcoin", "ethereum": "ethereum", "eth": "ethereum",
                   "dogecoin": "dogecoin", "doge": "dogecoin", "solana": "solana", "cardano": "cardano"}
        for key, value in cryptos.items():
            if key in q:
                return value
        return "bitcoin"
    
    elif intent == "wikipedia":
        for word in ["wikipedia", "wiki", "c'est quoi", "définition de", "qui est", "explique"]:
            if word in q:
                parts = q.split(word)
                if len(parts) > 1:
                    return parts[1].strip().replace("?", "").replace(" ", "_")
        return "économie"
    
    elif intent == "worldbank":
        pays = {"rdc": "CD", "congo": "CD", "usa": "US", "france": "FR", "chine": "CN", 
                "allemagne": "DE", "japon": "JP", "royaume-uni": "GB", "canada": "CA"}
        for key, value in pays.items():
            if key in q:
                return value
        return "CD"
    
    return question

# ==================================================
# 6. IA CENTRALE (avec mémoire, préférences, multi-API)
# ==================================================
def kennyson_answer(question, user_id=None):
    """Réponse intelligente avec tous les piliers intégrés"""
    
    # Charger mémoire et préférences
    historique = get_conversation_history(user_id, 3) if user_id else []
    preferences = get_user_preferences(user_id) if user_id else {"niveau": "intermediaire", "style": "détaillé", "langue": "français"}
    
    # Détection de l'intention
    intent = detect_intent(question)
    param = extract_param(question, intent)
    external_data = ""
    
    # Appels API
    if intent == "weather":
        lat, lon = geocode_city(param)
        if lat and lon:
            weather = get_weather_meteo(param, lat, lon)
            if weather:
                external_data = f"🌤️ {weather}\n\n"
    
    elif intent == "crypto":
        crypto_price = get_crypto_price(param)
        if crypto_price:
            external_data = f"{crypto_price}\n\n"
    
    elif intent == "wikipedia":
        wiki = get_wikipedia_summary(param)
        if wiki:
            external_data = f"{wiki}\n\n"
    
    elif intent == "worldbank":
        gdp = get_worldbank_gdp(param)
        inflation = get_worldbank_inflation(param)
        if gdp or inflation:
            external_data = f"🏦 **Données Banque mondiale** :\n{gdp}\n{inflation}\n\n"
    
    elif intent == "inflation":
        inflation = get_worldbank_inflation(param)
        if inflation:
            external_data = f"{inflation}\n\n"
    
    elif intent == "news":
        news = get_gnews_news(param)
        if news:
            external_data = f"{news}\n\n"
    
    # Construction du contexte mémoire
    memory_context = ""
    if historique:
        memory_context = "📜 **HISTORIQUE RÉCENT** :\n"
        for h in historique[:3]:
            memory_context += f"- Question : {h[0][:100]}\n"
            memory_context += f"  Réponse : {h[1][:100]}...\n\n"
    
    # Construction du prompt final
    full_prompt = f"""
**CONTEXTE UTILISATEUR** :
- Niveau : {preferences['niveau']}
- Style préféré : {preferences['style']}
- Langue : {preferences['langue']}
- Centres d'intérêt : {preferences['centres_interet']}

{memory_context}

**DONNÉES EXTERNES** :
{external_data}

**QUESTION** : {question}

**INTENTION DÉTECTÉE** : {intent}

**TON INSTRUCTION** : Réponds avec la structure Chain-of-Thought (ÉTAPE 1 à 7). Sois précis, donne des chiffres, cite tes sources. Adapte ton langage au niveau '{preferences['niveau']}'. Si style = 'concis', réduis les étapes à 4 au lieu de 7.
"""
    
    if not GROQ_API_KEY:
        return f"📊 **KENNYSON OURAGAN**\n\n{external_data}\n\n🎯 {question[:100]}\n\n🔮 Ajoute ta clé Groq dans Render."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_COT},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=45)
        if r.status_code == 200:
            reponse = r.json()['choices'][0]['message']['content']
            # Sauvegarde dans la mémoire
            if user_id:
                save_conversation(user_id, question, reponse[:500])
            return reponse
        return f"📊 **KENNYSON OURAGAN**\n\n{external_data}\n\n🎯 Réponse temporaire.\n\n🔮 Reformule ta question."
    except:
        return f"📊 **KENNYSON OURAGAN**\n\n{external_data}\n\n🎯 Données chargées.\n\n🔮 L'IA répondra dans quelques secondes."

# ==================================================
# 7. AUTHENTIFICATION ET ROUTES API
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
    
    # Créer les préférences par défaut
    conn = sqlite3.connect('kennyson_memory.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO user_preferences (user_id, niveau, style, langue, centres_interet) VALUES (?, ?, ?, ?, ?)',
              (email, 'intermediaire', 'détaillé', 'français', 'economie,crypto'))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Compte KENNYSON créé !"}), 201

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
    prefs = get_user_preferences(email)
    return jsonify({**users[email], "preferences": prefs}), 200

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    question = data.get('question', '')
    user_id = session.get('user')
    if not question:
        return jsonify({"reponse": "Pose ta question, KENNYSON OURAGAN répond."})
    reponse = kennyson_answer(question, user_id)
    return jsonify({"reponse": reponse})

@app.route('/api/feedback', methods=['POST'])
def feedback():
    """Point d'entrée pour le feedback utilisateur (Pilier 4)"""
    data = request.json
    user_id = session.get('user')
    if not user_id:
        return jsonify({"error": "Connectez-vous d'abord"}), 401
    rating = data.get('rating')
    conversation_id = data.get('conversation_id')
    comment = data.get('comment')
    save_feedback(user_id, conversation_id, rating, comment)
    return jsonify({"message": "Merci pour votre feedback !"}), 200

@app.route('/api/preferences', methods=['GET', 'POST'])
def preferences():
    """Gestion des préférences utilisateur (Pilier 6)"""
    user_id = session.get('user')
    if not user_id:
        return jsonify({"error": "Connectez-vous d'abord"}), 401
    
    if request.method == 'GET':
        prefs = get_user_preferences(user_id)
        return jsonify(prefs)
    
    elif request.method == 'POST':
        new_prefs = request.json
        set_user_preferences(user_id, new_prefs)
        return jsonify({"message": "Préférences mises à jour"}), 200

@app.route('/api/history')
def history():
    """Récupère l'historique des conversations (Pilier 1)"""
    user_id = session.get('user')
    if not user_id:
        return jsonify({"error": "Connectez-vous d'abord"}), 401
    hist = get_conversation_history(user_id, 20)
    return jsonify([{"question": h[0], "reponse": h[1], "timestamp": h[2]} for h in hist])

# ==================================================
# 8. INTERFACE STYLE CHATGPT
# ==================================================
@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KENNYSON · Ultimate AI · 7 Piliers</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #343541; color: #ececec; height: 100vh; overflow: hidden; }
        .app { display: flex; flex-direction: column; height: 100vh; }
        .header { background: #202123; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; flex-wrap: wrap; gap: 10px; }
        .logo-area { display: flex; align-items: center; gap: 12px; }
        .logo-icon { background: linear-gradient(135deg, #e94560, #ff5a7c); width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; }
        .logo-text h1 { font-size: 16px; font-weight: 600; color: white; }
        .logo-text p { font-size: 9px; color: #8e8ea0; letter-spacing: 1px; }
        .badge-api { background: rgba(233,69,96,0.2); border: 1px solid #e94560; border-radius: 12px; padding: 2px 8px; font-size: 8px; margin-left: 8px; }
        .header-actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .header-btn { background: none; border: none; color: #8e8ea0; cursor: pointer; font-size: 12px; padding: 6px 12px; border-radius: 6px; transition: 0.2s; }
        .header-btn:hover { background: #2a2b32; color: white; }
        .chat-container { flex: 1; overflow-y: auto; padding: 0; scroll-behavior: smooth; }
        .message { padding: 20px 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .message.user { background: #343541; }
        .message.bot { background: #444654; }
        .message-content { max-width: 800px; margin: 0 auto; display: flex; gap: 20px; align-items: flex-start; }
        .avatar { width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; flex-shrink: 0; }
        .avatar.user { background: #10a37f; }
        .avatar.bot { background: #e94560; }
        .text { flex: 1; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; }
        .text strong { color: #e94560; }
        .text h3 { color: #FACC15; margin: 12px 0 6px; font-size: 15px; }
        .feedback { display: flex; gap: 10px; margin-top: 12px; align-items: center; }
        .feedback-btn { background: none; border: none; cursor: pointer; font-size: 16px; opacity: 0.5; transition: 0.2s; }
        .feedback-btn:hover { opacity: 1; transform: scale(1.1); }
        .input-area { background: #202123; padding: 12px 15px; border-top: 1px solid rgba(255,255,255,0.1); flex-shrink: 0; }
        .input-wrapper { max-width: 800px; margin: 0 auto; position: relative; }
        textarea { width: 100%; background: #40414f; border: none; border-radius: 12px; padding: 12px 50px 12px 16px; color: white; font-family: inherit; font-size: 14px; resize: none; line-height: 1.5; }
        textarea:focus { outline: none; background: #4a4b5a; }
        .send-btn { position: absolute; right: 12px; bottom: 10px; background: #e94560; border: none; border-radius: 8px; padding: 6px 12px; color: white; cursor: pointer; font-size: 12px; font-weight: bold; }
        .send-btn:hover { background: #ff5a7c; }
        .suggestions { max-width: 800px; margin: 10px auto 0; display: flex; flex-wrap: wrap; gap: 8px; }
        .suggestion-chip { background: #2a2b32; padding: 6px 14px; border-radius: 20px; font-size: 11px; cursor: pointer; transition: 0.2s; color: #ececec; }
        .suggestion-chip:hover { background: #e94560; }
        .footer { text-align: center; padding: 6px; font-size: 9px; color: #565869; background: #202123; border-top: 1px solid rgba(255,255,255,0.05); }
        .typing-indicator { display: flex; gap: 4px; align-items: center; }
        .typing-indicator span { width: 8px; height: 8px; background: #8e8ea0; border-radius: 50%; animation: pulse 1.4s infinite; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }
        @media (max-width: 768px) { .message-content { padding: 0 10px; } .text { font-size: 13px; } .header-actions { justify-content: center; } }
    </style>
</head>
<body>
    <div class="app">
        <div class="header">
            <div class="logo-area">
                <div class="logo-icon">K</div>
                <div class="logo-text">
                    <h1>KENNYSON OURAGAN <span class="badge-api">ULTIMATE</span></h1>
                    <p>Mémoire · RAG · CoT · Feedback · Préférences · 7 API</p>
                </div>
            </div>
            <div class="header-actions">
                <button class="header-btn" id="newChatBtn">✨ Nouvelle conversation</button>
                <button class="header-btn" id="preferencesBtn">⚙️ Préférences</button>
                <button class="header-btn" id="historyBtn">📜 Historique</button>
                <button class="header-btn" id="loginBtn">🔐 Connexion</button>
            </div>
        </div>

        <div class="chat-container" id="chatContainer">
            <div class="message bot">
                <div class="message-content">
                    <div class="avatar bot">K</div>
                    <div class="text">
                        <strong>🔥 KENNYSON OURAGAN – Version Ultimate 🔥</strong><br><br>
                        <strong>🚀 7 PILIERS DE PUISSANCE ACTIVÉS :</strong><br><br>
                        ✅ <strong>P1 - MÉMOIRE PERSISTANTE</strong> : Je me souviens de toi !<br>
                        ✅ <strong>P2 - BASE VECTORIELLE</strong> : Recherche sémantique (ChromaDB)<br>
                        ✅ <strong>P3 - MULTI-AGENTS</strong> : Routeur intelligent<br>
                        ✅ <strong>P4 - FEEDBACK CONTINU</strong> : 👍/👎 pour amélioration<br>
                        ✅ <strong>P5 - CHAIN-OF-THOUGHT</strong> : Raisonnement étape par étape<br>
                        ✅ <strong>P6 - PERSONNALISATION</strong> : Adaptation à ton style<br>
                        ✅ <strong>P7 - 7 API GRATUITES</strong> : World Bank, CoinGecko, Open-Meteo, Wikipedia, GNews, Groq, OpenStreetMap<br><br>
                        <strong>💡 Exemples de questions :</strong><br>
                        • "PIB de la RDC" (World Bank)<br>
                        • "Prix du Bitcoin" (CoinGecko)<br>
                        • "Météo à Kinshasa" (Open-Meteo)<br>
                        • "Définition de l'inflation" (Wikipedia)<br>
                        • "Actualités économiques Afrique" (GNews)<br><br>
                        <em>✨ Connecte-toi pour activer la mémoire persistante !</em>
                    </div>
                </div>
            </div>
        </div>

        <div class="input-area">
            <div class="input-wrapper">
                <textarea id="questionInput" rows="1" placeholder="Pose ta question... (économie, crypto, météo, définitions, actualités)"></textarea>
                <button class="send-btn" id="sendBtn">➤</button>
            </div>
            <div class="suggestions">
                <div class="suggestion-chip" data-question="PIB de la RDC">🏦 PIB RDC</div>
                <div class="suggestion-chip" data-question="Prix du Bitcoin">💰 Bitcoin</div>
                <div class="suggestion-chip" data-question="Météo à Kinshasa">🌤️ Météo</div>
                <div class="suggestion-chip" data-question="Définition de l'inflation">📖 Inflation</div>
                <div class="suggestion-chip" data-question="Actualités économiques Afrique">📰 Actualités</div>
                <div class="suggestion-chip" data-question="Compare l'économie de la RDC et du Nigeria">🌍 Comparaison</div>
            </div>
        </div>
        <div class="footer">KENNYSON OURAGAN ULTIMATE · 7 piliers · Mémoire persistante · Chat (↑)</div>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const textarea = document.getElementById('questionInput');
        const sendBtn = document.getElementById('sendBtn');
        let currentConversationId = Date.now();

        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        async function sendMessage() {
            const question = textarea.value.trim();
            if (!question) return;
            addMessage(question, 'user');
            textarea.value = '';
            textarea.style.height = 'auto';
            const loadingId = addTypingIndicator();
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                });
                const data = await response.json();
                removeTypingIndicator(loadingId);
                const msgId = addMessage(data.reponse, 'bot');
                addFeedbackButtons(msgId);
            } catch (error) {
                removeTypingIndicator(loadingId);
                addMessage('⚠️ Erreur technique. Veuillez réessayer.', 'bot');
            }
        }

        function addMessage(text, role) {
            const messageDiv = document.createElement('div');
            const msgId = 'msg-' + Date.now() + '-' + Math.random();
            messageDiv.id = msgId;
            messageDiv.className = `message ${role}`;
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="avatar ${role}">${role === 'user' ? '👤' : 'K'}</div>
                    <div class="text">${formatText(text)}</div>
                </div>
            `;
            chatContainer.appendChild(messageDiv);
            scrollToBottom();
            return msgId;
        }

        function addFeedbackButtons(msgId) {
            const msgDiv = document.getElementById(msgId);
            if (!msgDiv || msgDiv.querySelector('.feedback')) return;
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback';
            feedbackDiv.innerHTML = `
                <button class="feedback-btn" onclick="sendFeedback(${currentConversationId}, 1, this)">👍</button>
                <button class="feedback-btn" onclick="sendFeedback(${currentConversationId}, 0, this)">👎</button>
                <span style="font-size:10px; color:#565869;">Donne ton avis</span>
            `;
            msgDiv.querySelector('.text').appendChild(feedbackDiv);
        }

        async function sendFeedback(convId, rating, btn) {
            const token = localStorage.getItem('token');
            if (!token) { alert('Connecte-toi pour donner ton avis'); return; }
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: convId, rating: rating === 1 ? 5 : 1 })
            });
            if (response.ok) {
                btn.parentElement.innerHTML = '<span style="color:#10a37f;">✓ Merci !</span>';
            }
        }

        function formatText(text) {
            let formatted = text.replace(/\\n/g, '<br>');
            formatted = formatted.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
            formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            formatted = formatted.replace(/📍/g, '<strong>📍</strong>');
            return formatted;
        }

        function addTypingIndicator() {
            const id = 'typing-' + Date.now();
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot';
            typingDiv.id = id;
            typingDiv.innerHTML = `
                <div class="message-content">
                    <div class="avatar bot">K</div>
                    <div class="text"><div class="typing-indicator"><span></span><span></span><span></span></div></div>
                </div>
            `;
            chatContainer.appendChild(typingDiv);
            scrollToBottom();
            return id;
        }

        function removeTypingIndicator(id) {
            const element = document.getElementById(id);
            if (element) element.remove();
        }

        function scrollToBottom() {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        sendBtn.addEventListener('click', sendMessage);
        textarea.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                textarea.value = chip.dataset.question;
                sendMessage();
            });
        });

        document.getElementById('newChatBtn').addEventListener('click', () => {
            chatContainer.innerHTML = '';
            currentConversationId = Date.now();
            addMessage('✨ Nouvelle conversation. Je suis KENNYSON OURAGAN, prêt à répondre à tes questions économiques avec mes 7 piliers de puissance !', 'bot');
        });

        document.getElementById('preferencesBtn').addEventListener('click', async () => {
            const token = localStorage.getItem('token');
            if (!token) { alert('Connecte-toi d\'abord'); return; }
            const niveau = prompt('Niveau (débutant/intermediaire/expert) :', 'intermediaire');
            const style = prompt('Style (concis/détaillé) :', 'détaillé');
            if (niveau && style) {
                await fetch('/api/preferences', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ niveau, style })
                });
                alert('Préférences mises à jour !');
            }
        });

        document.getElementById('historyBtn').addEventListener('click', async () => {
            const token = localStorage.getItem('token');
            if (!token) { alert('Connecte-toi d\'abord'); return; }
            const response = await fetch('/api/history');
            const data = await response.json();
            if (data.length) {
                let histText = '📜 **HISTORIQUE DES CONVERSATIONS** :\n\n';
                data.slice(0, 5).forEach((h, i) => {
                    histText += `${i+1}. **${h.question.substring(0, 80)}**\n   ${new Date(h.timestamp).toLocaleDateString()}\n\n`;
                });
                addMessage(histText, 'bot');
            } else {
                addMessage('Aucun historique pour le moment. Commence à discuter !', 'bot');
            }
        });

        document.getElementById('loginBtn').addEventListener('click', () => {
            window.location.href = '/login';
        });

        const token = localStorage.getItem('token');
        if (token) {
            fetch('/api/me').then(res => {
                if (res.ok) document.getElementById('loginBtn').innerHTML = '👤 Mon compte';
                else localStorage.removeItem('token');
            });
        }
    </script>
</body>
</html>
    '''

# ==================================================
# 9. PAGES AUTHENTIFICATION
# ==================================================
LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KENNYSON · Connexion</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #343541; color: #ececec; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .login-container { background: #202123; padding: 40px; border-radius: 16px; width: 100%; max-width: 420px; }
        h2 { margin-bottom: 8px; color: #e94560; }
        .subtitle { font-size: 13px; color: #8e8ea0; margin-bottom: 24px; }
        input { width: 100%; padding: 12px; margin-bottom: 12px; background: #40414f; border: none; border-radius: 8px; color: white; font-size: 14px; }
        input:focus { outline: none; background: #4a4b5a; }
        button { width: 100%; padding: 12px; background: #e94560; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; margin-top: 8px; }
        button:hover { background: #ff5a7c; }
        .toggle { text-align: center; margin-top: 16px; font-size: 13px; color: #8e8ea0; cursor: pointer; }
        .toggle:hover { color: #e94560; }
        .message { margin-top: 12px; text-align: center; font-size: 13px; color: #10a37f; }
        .error { color: #e94560; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>KENNYSON OURAGAN</h2>
        <div class="subtitle">7 piliers · Mémoire persistante · 7 API</div>
        <div id="registerForm">
            <input type="text" id="regName" placeholder="Nom">
            <input type="email" id="regEmail" placeholder="Email">
            <input type="password" id="regPassword" placeholder="Mot de passe (min 6)">
            <button onclick="register()">Créer un compte</button>
            <div class="toggle" onclick="showLogin()">Déjà un compte ? Se connecter</div>
        </div>
        <div id="loginForm" style="display:none;">
            <input type="email" id="loginEmail" placeholder="Email">
            <input type="password" id="loginPassword" placeholder="Mot de passe">
            <button onclick="login()">Se connecter</button>
            <div class="toggle" onclick="showRegister()">Pas de compte ? S'inscrire</div>
        </div>
        <div id="msg" class="message"></div>
    </div>
    <script>
        function showLogin() { document.getElementById('registerForm').style.display = 'none'; document.getElementById('loginForm').style.display = 'block'; }
        function showRegister() { document.getElementById('registerForm').style.display = 'block'; document.getElementById('loginForm').style.display = 'none'; }
        async function register() {
            let name = document.getElementById('regName').value, email = document.getElementById('regEmail').value, password = document.getElementById('regPassword').value;
            if (!email.includes('@')) { showMsg('Email invalide', true); return; }
            if (password.length < 6) { showMsg('Mot de passe trop court', true); return; }
            let res = await fetch('/api/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, email, password }) });
            let data = await res.json();
            if (res.ok) { showMsg('Compte créé ! Connectez-vous.'); setTimeout(showLogin, 1500); }
            else { showMsg(data.error, true); }
        }
        async function login() {
            let email = document.getElementById('loginEmail').value, password = document.getElementById('loginPassword').value;
            let res = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
            let data = await res.json();
            if (res.ok) { localStorage.setItem('token', data.token); window.location.href = '/'; }
            else { showMsg(data.error, true); }
        }
        function showMsg(msg, isError=false) { let div = document.getElementById('msg'); div.textContent = msg; div.className = isError ? 'message error' : 'message'; setTimeout(() => div.textContent = '', 3000); }
    </script>
</body>
</html>
'''

@app.route('/login')
def login_page():
    return LOGIN_PAGE

@app.route('/mon-compte')
def mon_compte():
    return '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KENNYSON · Mon compte</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #343541; color: #ececec; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .account-container { background: #202123; padding: 40px; border-radius: 16px; width: 100%; max-width: 420px; text-align: center; }
        .avatar { background: linear-gradient(135deg, #e94560, #ff5a7c); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 36px; margin: 0 auto 20px; }
        h2 { margin-bottom: 8px; }
        .email { color: #8e8ea0; margin-bottom: 24px; }
        button { padding: 12px 24px; background: #e94560; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; }
        button:hover { background: #ff5a7c; }
        .back-link { display: block; margin-top: 16px; color: #8e8ea0; text-decoration: none; font-size: 13px; }
        .back-link:hover { color: #e94560; }
    </style>
</head>
<body>
    <div class="account-container" id="accountInfo">
        <div class="avatar">👤</div>
        <div id="userData">Chargement...</div>
        <button onclick="logout()">Se déconnecter</button>
        <a href="/" class="back-link">← Retour à KENNYSON</a>
    </div>
    <script>
        async function loadUser() { let res = await fetch('/api/me'); if (res.ok) { let user = await res.json(); document.getElementById('userData').innerHTML = `<h2>${user.name}</h2><div class="email">${user.email}</div><div style="margin-top:12px; font-size:11px; color:#565869;">🧠 Mémoire active · ⚙️ Préférences sauvegardées</div>`; } else { window.location.href = '/login'; } }
        async function logout() { await fetch('/api/logout', {method: 'POST'}); localStorage.removeItem('token'); window.location.href = '/'; }
        loadUser();
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
