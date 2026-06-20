from flask import Flask, jsonify, request
import requests
import os
import re

app = Flask(__name__)

# ==================================================
# CONFIGURATION API
# ==================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================================================
# BASE DE CONNAISSANCES
# ==================================================
KNOWLEDGE = {
    "latence": {"def": "Temps de transmission", "solutions": ["QoS", "Fibre optique"]},
    "wifi": {"def": "Technologie sans fil", "solutions": ["Changer canal", "5 GHz"]},
    "5g": {"def": "Réseau mobile 5G", "debit": "Jusqu'à 10 Gbps"},
    "vpn": {"def": "Réseau privé virtuel", "protocoles": ["OpenVPN", "WireGuard"]}
}

def get_context(question):
    q = question.lower()
    context = ""
    
    if "latence" in q or "ms" in q:
        ms_match = re.search(r'(\d+)\s*ms', q)
        if ms_match:
            ms = int(ms_match.group(1))
            status = "excellente" if ms < 50 else "modérée" if ms < 100 else "élevée"
            context += f"Latence: {ms} ms ({status})\n"
    
    if "wifi" in q:
        context += "Sujet: Wi-Fi - Problème identifié\n"
    
    return context

def get_ia_response(question):
    context = get_context(question)
    
    if not GROQ_API_KEY:
        return "⚠️ **GROQ_API_KEY manquante**\n\nAjoute ta clé Groq dans les variables d'environnement Render."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Tu es KENNYSON OURAGAN, un expert en télécommunications. Réponds en français de manière structurée avec diagnostic et solutions."},
            {"role": "user", "content": f"Contexte: {context}\n\nQuestion: {question}"}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return f"⚠️ Erreur API: {r.status_code}"
    except Exception as e:
        return f"⚠️ Erreur: {str(e)[:100]}"

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
    return jsonify({"status": "online", "groq": bool(GROQ_API_KEY)})

# ==================================================
# HTML
# ==================================================
HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KENNYSON · Agent Télécom</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto; background: #0A0F1E; color: #ececec; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #1a1a2e; padding: 16px 20px; border-bottom: 1px solid #0085CA; text-align: center; }
        .logo { font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #e94560, #0085CA); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .badge { background: #0085CA; border-radius: 20px; padding: 2px 12px; font-size: 10px; margin-left: 8px; }
        .sub { font-size: 11px; color: #8e8ea0; margin-top: 4px; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; max-width: 900px; margin: 0 auto; width: 100%; }
        .message { display: flex; gap: 16px; margin-bottom: 24px; }
        .avatar { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .avatar.user { background: #10a37f; }
        .avatar.bot { background: #0085CA; }
        .content { flex: 1; line-height: 1.6; white-space: pre-wrap; font-size: 14px; }
        .content strong { color: #0085CA; }
        .input-area { background: #1a1a2e; padding: 16px; border-top: 1px solid #4a4b5a; }
        .input-wrapper { max-width: 800px; margin: 0 auto; display: flex; gap: 12px; }
        textarea { flex: 1; background: #40414f; border: none; border-radius: 12px; padding: 12px 16px; color: white; font-family: inherit; resize: none; font-size: 14px; }
        button { background: #0085CA; border: none; border-radius: 12px; padding: 12px 24px; color: white; cursor: pointer; font-weight: 500; }
        .suggestions { max-width: 800px; margin: 12px auto 0; display: flex; gap: 8px; flex-wrap: wrap; }
        .suggestion { background: #2a2b32; padding: 6px 14px; border-radius: 20px; font-size: 12px; cursor: pointer; border: 1px solid #0085CA; }
        .suggestion:hover { background: #0085CA; }
        .footer { text-align: center; padding: 8px; font-size: 10px; color: #565869; }
        .typing span { display: inline-block; width: 8px; height: 8px; background: #8e8ea0; border-radius: 50%; animation: pulse 1.4s infinite; margin: 0 2px; }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
    </style>
</head>
<body>
<div class="header">
    <div class="logo">📡 KENNYSON OURAGAN <span class="badge">AGENT TÉLÉCOM</span></div>
    <div class="sub">Réseaux · Sécurité · 5G · IoT · Cloud</div>
</div>
<div class="chat-container" id="chat"></div>
<div class="input-area">
    <div class="input-wrapper">
        <textarea id="input" rows="1" placeholder="Posez votre question technique..."></textarea>
        <button id="send">Envoyer</button>
    </div>
    <div class="suggestions">
        <div class="suggestion" data-q="J'ai 200 ms de latence, c'est grave ?">📊 Latence</div>
        <div class="suggestion" data-q="Comment améliorer mon Wi-Fi ?">📶 Wi-Fi</div>
        <div class="suggestion" data-q="Qu'est-ce que le 5G ?">📡 5G</div>
        <div class="suggestion" data-q="Comment sécuriser mon réseau ?">🔒 Sécurité</div>
        <div class="suggestion" data-q="C'est quoi un VPN ?">🔐 VPN</div>
    </div>
    <div class="footer">📡 Expert en télécommunications · API Groq · Solutions IA</div>
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
        addMessage("❌ Erreur. Vérifie que GROQ_API_KEY est configurée.", 'bot');
    }
}

document.getElementById('send').onclick = send;
input.onkeypress = (e) => { if(e.key === 'Enter') { e.preventDefault(); send(); } };
document.querySelectorAll('.suggestion').forEach(s => { s.onclick = () => { input.value = s.dataset.q; send(); }; });

addMessage('📡 **KENNYSON OURAGAN - AGENT TÉLÉCOM (API Groq)**\n\nBonjour ! Je suis votre expert en télécommunications, propulsé par **Groq Llama 3.3 70B**.\n\n**🔍 Ce que je peux faire :**\n• 📊 Analyser la latence réseau\n• 📶 Diagnostiquer les problèmes Wi-Fi\n• 📡 Expliquer le 5G, VPN, Sécurité\n• 🔒 Conseiller en cybersécurité\n\n**💡 Exemples :**\n• "J\'ai 150 ms de latence, c\'est normal ?"\n• "Comment améliorer mon Wi-Fi ?"\n• "Qu\'est-ce que le 5G ?"\n• "C\'est quoi un VPN ?"\n\n**Posez votre question technique !** 🔥', 'bot');
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
