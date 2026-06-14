from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ==================================================
# CONFIGURATION
# ==================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GNEWS_API_KEY = os.environ.get('GNEWS_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================================================
# 1. WIKIPEDIA API (source #1 de ChatGPT)
# ==================================================
def get_wikipedia(topic):
    """Récupère un résumé Wikipedia"""
    try:
        # Essayer d'abord en français
        url_fr = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{topic}"
        r = requests.get(url_fr, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if 'extract' in data:
                return f"📖 **Wikipedia ({topic})** :\n{data['extract'][:600]}..."
        
        # Sinon en anglais
        url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
        r = requests.get(url_en, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if 'extract' in data:
                return f"📖 **Wikipedia ({topic})** :\n{data['extract'][:600]}..."
    except:
        pass
    return None

# ==================================================
# 2. BANQUE MONDIALE (données économiques)
# ==================================================
COUNTRIES = {
    "rdc": "CD", "congo": "CD",
    "usa": "US", "etats-unis": "US",
    "france": "FR", "chine": "CN", "allemagne": "DE",
    "japon": "JP", "royaume-uni": "GB", "angleterre": "GB",
    "canada": "CA", "bresil": "BR", "inde": "IN",
    "nigeria": "NG", "afrique du sud": "ZA", "maroc": "MA"
}

def get_worldbank_gdp(country_code):
    try:
        url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1 and data[1] and data[1][0].get('value'):
                return int(float(data[1][0]['value']))
    except:
        pass
    return None

def get_worldbank_inflation(country_code):
    try:
        url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/FP.CPI.TOTL.ZG?format=json"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1 and data[1] and data[1][0].get('value'):
                return float(data[1][0]['value'])
    except:
        pass
    return None

# ==================================================
# 3. CRYPTO (CoinGecko)
# ==================================================
def get_crypto(coin="bitcoin"):
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,eur", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if coin in data:
                return {"usd": data[coin]['usd'], "eur": data[coin]['eur']}
    except:
        pass
    return None

# ==================================================
# 4. MÉTÉO (Open-Meteo)
# ==================================================
def get_weather_city(city):
    try:
        # Géocodage
        geo = requests.get(f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1", 
                          headers={'User-Agent': 'KENNYSON-IA/1.0'}, timeout=8)
        if geo.status_code == 200 and geo.json():
            lat = geo.json()[0]['lat']
            lon = geo.json()[0]['lon']
            r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=8)
            if r.status_code == 200:
                return r.json()['current_weather']['temperature']
    except:
        pass
    return None

# ==================================================
# 5. ACTUALITÉS (GNews)
# ==================================================
def get_news(query):
    if not GNEWS_API_KEY:
        return None
    try:
        r = requests.get(f"https://gnews.io/api/v4/search?q={query}&token={GNEWS_API_KEY}&lang=fr&max=4", timeout=8)
        if r.status_code == 200:
            articles = r.json().get('articles', [])
            return articles[:4]
    except:
        pass
    return None

# ==================================================
# 6. TAUX DE CHANGE
# ==================================================
def get_exchange_rate():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=8)
        if r.status_code == 200:
            data = r.json()
            return {"eur": data['rates'].get('EUR'), "gbp": data['rates'].get('GBP')}
    except:
        pass
    return None

# ==================================================
# IA CENTRALE
# ==================================================
SYSTEM_PROMPT = """Tu es KENNYSON OURAGAN, un assistant intelligent.

SOURCES DISPONIBLES :
- Wikipedia (savoir général)
- Banque mondiale (PIB, inflation)
- CoinGecko (Bitcoin, crypto)
- Open-Meteo (météo)
- GNews (actualités)
- Exchange Rate API (taux de change)

RÈGLES :
- Réponds en français, de manière professionnelle
- Cite TES SOURCES à la fin de chaque réponse
- Sois précis, donne des chiffres
- Ne jamais inventer d'informations
"""

def get_all_data(question):
    q = question.lower()
    context = ""
    
    # 1. Wikipedia (biographie, définition)
    topics = ["elon musk", "albert einstein", "marie curie", "napoleon", "poutine", "macron", "ia", "intelligence artificielle"]
    for topic in topics:
        if topic in q:
            wiki = get_wikipedia(topic.replace(" ", "_"))
            if wiki:
                context += f"\n{wiki}\n"
                break
    
    # 2. Banque mondiale (économie)
    for country_name, code in COUNTRIES.items():
        if country_name in q:
            gdp = get_worldbank_gdp(code)
            inflation = get_worldbank_inflation(code)
            if gdp:
                context += f"\n📊 **BANQUE MONDIALE - {country_name.upper()}**\n"
                context += f"   PIB: {gdp:,} USD\n"
                if inflation:
                    context += f"   Inflation: {inflation:.1f}%\n"
            break
    
    # 3. Crypto
    if "bitcoin" in q or "btc" in q:
        btc = get_crypto("bitcoin")
        if btc:
            context += f"\n💰 **COINGECKO**\n   Bitcoin: ${btc['usd']:,} USD / €{btc['eur']:,} EUR\n"
    if "ethereum" in q or "eth" in q:
        eth = get_crypto("ethereum")
        if eth:
            context += f"   Ethereum: ${eth['usd']:,} USD / €{eth['eur']:,} EUR\n"
    
    # 4. Météo
    for word in q.split():
        if len(word) > 3 and word[0].isupper():
            temp = get_weather_city(word)
            if temp:
                context += f"\n🌤️ **OPEN-METEO - {word}**\n   Température: {temp}°C\n"
                break
    
    # 5. Actualités
    if "actualité" in q or "news" in q or "actu" in q:
        news = get_news(q)
        if news:
            context += "\n🌍 **GNews - ACTUALITÉS**\n"
            for a in news[:3]:
                context += f"   • {a.get('title', '')[:100]}\n"
    
    # 6. Taux de change
    if "taux" in q or "change" in q or "euro" in q or "dollar" in q:
        rates = get_exchange_rate()
        if rates:
            context += f"\n💱 **EXCHANGE RATE API**\n   1 USD = {rates['eur']:.2f} EUR\n"
    
    return context

def get_ia_response(question):
    data_context = get_all_data(question)
    
    if not GROQ_API_KEY:
        return data_context or "KENNYSON OURAGAN prêt. Ajoute ta clé Groq dans Render."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DONNÉES EXTERNES:\n{data_context}\n\nQUESTION: {question}"}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=40)
        if r.status_code == 200:
            rep = r.json()['choices'][0]['message']['content']
            if data_context:
                return f"{data_context}\n---\n{rep}"
            return rep
        return data_context or "Erreur technique. Veuillez réessayer."
    except Exception as e:
        return data_context or f"KENNYSON OURAGAN prêt. Question reçue : {question[:100]}..."

# ==================================================
# ROUTES
# ==================================================
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    reponse = get_ia_response(question)
    return jsonify({"reponse": reponse})

@app.route('/api/health')
def health():
    return jsonify({"status": "online", "groq": bool(GROQ_API_KEY), "gnews": bool(GNEWS_API_KEY)})

# ==================================================
# HTML INTERFACE
# ==================================================
HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KENNYSON OURAGAN · IA Internationale</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto; background: #343541; color: #ececec; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #202123; padding: 16px 20px; border-bottom: 1px solid #4a4b5a; text-align: center; }
        .logo { font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #e94560, #ff5a7c); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .sub { font-size: 11px; color: #8e8ea0; margin-top: 4px; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; max-width: 900px; margin: 0 auto; width: 100%; }
        .message { display: flex; gap: 16px; margin-bottom: 24px; }
        .avatar { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .avatar.user { background: #10a37f; }
        .avatar.bot { background: #e94560; }
        .content { flex: 1; line-height: 1.6; white-space: pre-wrap; font-size: 14px; }
        .content strong { color: #e94560; }
        .input-area { background: #202123; padding: 16px; border-top: 1px solid #4a4b5a; }
        .input-wrapper { max-width: 800px; margin: 0 auto; display: flex; gap: 12px; }
        textarea { flex: 1; background: #40414f; border: none; border-radius: 12px; padding: 12px 16px; color: white; font-family: inherit; resize: none; font-size: 14px; }
        button { background: #e94560; border: none; border-radius: 12px; padding: 12px 24px; color: white; cursor: pointer; font-weight: 500; }
        .suggestions { max-width: 800px; margin: 12px auto 0; display: flex; gap: 8px; flex-wrap: wrap; }
        .suggestion { background: #2a2b32; padding: 6px 14px; border-radius: 20px; font-size: 12px; cursor: pointer; }
        .suggestion:hover { background: #e94560; }
        .footer { text-align: center; padding: 8px; font-size: 10px; color: #565869; }
        .typing span { display: inline-block; width: 8px; height: 8px; background: #8e8ea0; border-radius: 50%; animation: pulse 1.4s infinite; margin: 0 2px; }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
        @media (max-width: 768px) { .suggestions { justify-content: center; } .content { font-size: 13px; } }
    </style>
</head>
<body>
<div class="header">
    <div class="logo">🔥 KENNYSON OURAGAN</div>
    <div class="sub">IA Internationale · 7 sources d'information</div>
</div>
<div class="chat-container" id="chat"></div>
<div class="input-area">
    <div class="input-wrapper">
        <textarea id="input" rows="1" placeholder="Posez votre question..."></textarea>
        <button id="send">Envoyer</button>
    </div>
    <div class="suggestions">
        <div class="suggestion" data-q="Qui est Albert Einstein ?">📖 Albert Einstein</div>
        <div class="suggestion" data-q="PIB des États-Unis">📊 PIB USA</div>
        <div class="suggestion" data-q="Prix du Bitcoin">💰 Bitcoin</div>
        <div class="suggestion" data-q="Météo à Paris">🌤️ Météo Paris</div>
        <div class="suggestion" data-q="Actualités économiques">📰 Actualités</div>
        <div class="suggestion" data-q="Taux de change USD/EUR">💱 Taux change</div>
    </div>
    <div class="footer">Sources: Wikipedia · Banque mondiale · CoinGecko · Open-Meteo · GNews · Exchange Rate API</div>
</div>

<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');

function addMessage(text, role) {
    const div = document.createElement('div');
    div.className = 'message';
    div.innerHTML = `<div class="avatar ${role}">${role === 'user' ? '👤' : 'K'}</div><div class="content">${text.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')}</div>`;
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
        const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q }) });
        const data = await res.json();
        chat.lastChild.remove();
        addMessage(data.reponse, 'bot');
    } catch(e) {
        chat.lastChild.remove();
        addMessage("❌ Erreur technique. Veuillez réessayer.", 'bot');
    }
}

document.getElementById('send').onclick = send;
input.onkeypress = (e) => { if(e.key === 'Enter') { e.preventDefault(); send(); } };
document.querySelectorAll('.suggestion').forEach(s => { s.onclick = () => { input.value = s.dataset.q; send(); }; });

addMessage('🌍 **KENNYSON OURAGAN - IA Internationale**\n\nBonjour ! Je suis votre assistant avec **6 sources d\'information** :\n\n📖 **Wikipedia** (biographies, définitions)\n📊 **Banque mondiale** (PIB, inflation)\n💰 **CoinGecko** (Bitcoin, crypto)\n🌤️ **Open-Meteo** (météo mondiale)\n📰 **GNews** (actualités)\n💱 **Exchange Rate API** (taux de change)\n\n**Exemples :**\n• "Qui est Elon Musk ?"\n• "PIB de la France"\n• "Prix du Bitcoin"\n• "Météo à Londres"\n• "Actualités économiques"\n• "Taux de change USD/EUR"\n\nPosez votre question ! 🔥', 'bot');
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
