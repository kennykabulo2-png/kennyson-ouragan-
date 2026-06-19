from flask import Flask, jsonify, request
import requests
import os
import json
import re
from datetime import datetime

app = Flask(__name__)

# ==================================================
# CONFIGURATION
# ==================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================================================
# BASE DE CONNAISSANCES TÉLÉCOM & INFORMATIQUE
# ==================================================
TELECOM_KNOWLEDGE = {
    "latence": {
        "definition": "Temps de transmission entre deux points d'un réseau",
        "seuil_normal": "moins de 50 ms",
        "seuil_acceptable": "50-100 ms",
        "seuil_critique": "plus de 150 ms",
        "causes": ["Congestion du réseau", "Distance géographique", "Interférences", "Mauvaise configuration"],
        "solutions": ["Configurer la QoS", "Utiliser la fibre optique", "Optimiser le routage", "Passer en filaire"]
    },
    "bande_passante": {
        "definition": "Capacité maximale de transmission de données",
        "unite": "bits par seconde (bps)",
        "causes_lenteur": ["Saturation du lien", "Matériel obsolète", "Interférences", "Nombre d'utilisateurs"],
        "solutions": ["Augmenter le débit", "Optimiser le trafic", "Passer à la fibre", "Utiliser la compression"]
    },
    "ipv4": {
        "definition": "Protocole Internet version 4",
        "format": "192.168.1.1",
        "problemes": ["Épuisement des adresses", "NAT nécessaire"],
        "solutions": ["Passer à IPv6", "Utiliser le NAT", "Subnetting"]
    },
    "ipv6": {
        "definition": "Protocole Internet version 6",
        "format": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "avantages": ["Adresses illimitées", "Sécurité intégrée", "Meilleure performance"]
    },
    "dns": {
        "definition": "Domain Name System - Traduit les noms de domaine en adresses IP",
        "problemes": ["Résolution lente", "Cache corrompu", "Attaque DNS"],
        "solutions": ["Utiliser un DNS rapide (1.1.1.1, 8.8.8.8)", "Vider le cache", "Configurer des DNS redondants"]
    },
    "firewall": {
        "definition": "Système de sécurité qui contrôle le trafic réseau",
        "types": ["Pare-feu matériel", "Pare-feu logiciel", "Pare-feu applicatif"],
        "fonctions": ["Filtrage de paquets", "Inspection dynamique", "Proxy"],
        "recommandations": ["Configurer les règles", "Mettre à jour régulièrement", "Journaliser les accès"]
    },
    "vpn": {
        "definition": "Virtual Private Network - Réseau privé virtuel",
        "protocoles": ["OpenVPN", "IPsec", "WireGuard", "L2TP"],
        "avantages": ["Confidentialité", "Sécurité", "Contournement des restrictions"],
        "recommandations": ["Choisir un protocole sécurisé", "Utiliser une authentification forte"]
    },
    "wifi": {
        "definition": "Technologie de réseau sans fil",
        "normes": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax (Wi-Fi 6)"],
        "problemes": ["Interférences", "Portée limitée", "Saturation du canal"],
        "solutions": ["Changer de canal", "Utiliser la bande 5 GHz", "Ajouter des répéteurs"]
    },
    "5g": {
        "definition": "Cinquième génération de réseau mobile",
        "debit": "Jusqu'à 10 Gbps",
        "latence": "Moins de 1 ms",
        "applications": ["IoT", "Véhicules autonomes", "Smart Cities", "Réalité augmentée"],
        "frequences": ["Bande basse (sub-1 GHz)", "Bande moyenne (1-6 GHz)", "Bande haute (mmWave)"]
    },
    "iot": {
        "definition": "Internet of Things - Objets connectés",
        "protocoles": ["MQTT", "CoAP", "HTTP", "AMQP"],
        "securite": ["Changer les mots de passe par défaut", "Mettre à jour les firmwares", "Isoler les dispositifs"],
        "applications": ["Maison connectée", "Ville intelligente", "Industrie 4.0"]
    },
    "cloud": {
        "definition": "Infrastructure de services informatiques à distance",
        "modeles": ["IaaS", "PaaS", "SaaS"],
        "fournisseurs": ["AWS", "Azure", "Google Cloud", "OVH"],
        "avantages": ["Scalabilité", "Disponibilité", "Coût à l'usage"]
    },
    "cybersecurite": {
        "definition": "Protection des systèmes informatiques contre les menaces",
        "menaces": ["Malware", "Phishing", "DDoS", "Ransomware", "Ingénierie sociale"],
        "bonnes_pratiques": ["Mots de passe forts", "Authentification multi-facteurs", "Mises à jour régulières", "Sauvegardes"],
        "normes": ["ISO 27001", "GDPR", "NIST"]
    }
}

# ==================================================
# ANALYSE DE RÉSEAUX
# ==================================================
class NetworkAnalyzer:
    """Analyse les problèmes de réseau"""
    
    @staticmethod
    def diagnose_latency(ms):
        if ms < 50:
            return "✅ Excellente latence", "Le réseau est optimal"
        elif ms < 100:
            return "⚠️ Latence modérée", "Peut être améliorée"
        else:
            return "❌ Latence élevée", "Action nécessaire"
    
    @staticmethod
    def diagnose_bandwidth(mbps):
        if mbps >= 100:
            return "✅ Très bon débit", "Adapté à tous les usages"
        elif mbps >= 50:
            return "✅ Bon débit", "Adapté à la plupart des usages"
        elif mbps >= 10:
            return "⚠️ Débit moyen", "Peut être insuffisant pour du streaming"
        else:
            return "❌ Débit faible", "Besoin d'amélioration"
    
    @staticmethod
    def diagnose_wifi(signal_percent):
        if signal_percent >= 70:
            return "✅ Excellent signal", "Connexion stable"
        elif signal_percent >= 50:
            return "⚠️ Signal moyen", "Peut avoir des déconnexions"
        else:
            return "❌ Mauvais signal", "Connexion instable"

# ==================================================
# AGENT TÉLÉCOM
# ==================================================
class TelecomAgent:
    def __init__(self):
        self.knowledge = TELECOM_KNOWLEDGE
        self.conversation_history = []
    
    def identify_topic(self, question):
        """Identifie le sujet de la question"""
        q = question.lower()
        topics = []
        
        topic_keywords = {
            "latence": ["latence", "ping", "temps de réponse", "lent", "ralenti"],
            "bande_passante": ["bande passante", "débit", "vitesse", "lent", "mbps"],
            "ipv4": ["ipv4", "adresse ip", "192.168"],
            "ipv6": ["ipv6", "adresse ipv6"],
            "dns": ["dns", "domaine", "résolution"],
            "firewall": ["firewall", "pare-feu", "bloque"],
            "vpn": ["vpn", "réseau privé", "tunnel"],
            "wifi": ["wifi", "sans fil", "wireless"],
            "5g": ["5g", "réseau mobile", "5ème génération"],
            "iot": ["iot", "objet connecté", "capteur"],
            "cloud": ["cloud", "nuage", "stockage distant"],
            "cybersecurite": ["sécurité", "cyber", "hack", "virus", "malware", "ransomware"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in q for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def get_knowledge_context(self, topics):
        """Récupère les connaissances pour les sujets identifiés"""
        context = ""
        for topic in topics:
            if topic in self.knowledge:
                data = self.knowledge[topic]
                context += f"📡 **{topic.upper()}** : {data.get('definition', '')}\n"
                if 'causes' in data:
                    context += "Causes: " + ", ".join(data['causes']) + "\n"
                if 'solutions' in data:
                    context += "Solutions: " + ", ".join(data['solutions']) + "\n"
                if 'bonnes_pratiques' in data:
                    context += "Bonnes pratiques: " + ", ".join(data['bonnes_pratiques']) + "\n"
                context += "\n"
        return context
    
    def analyze_network(self, question):
        """Analyse les paramètres réseau mentionnés"""
        q = question.lower()
        analysis = ""
        
        # Détection de latence
        ms_match = re.search(r'(\d+)\s*(?:ms|ms de latence)', q)
        if ms_match:
            ms = int(ms_match.group(1))
            status, comment = NetworkAnalyzer.diagnose_latency(ms)
            analysis += f"🔍 **Latence :** {ms} ms - {status}\n   {comment}\n\n"
        
        # Détection de débit
        mbps_match = re.search(r'(\d+)\s*(?:mbps|mb/s|mbit)', q)
        if mbps_match:
            mbps = int(mbps_match.group(1))
            status, comment = NetworkAnalyzer.diagnose_bandwidth(mbps)
            analysis += f"🔍 **Débit :** {mbps} Mbps - {status}\n   {comment}\n\n"
        
        # Détection de signal Wi-Fi
        signal_match = re.search(r'(\d+)\s*%', q)
        if signal_match and 'wifi' in q:
            signal = int(signal_match.group(1))
            status, comment = NetworkAnalyzer.diagnose_wifi(signal)
            analysis += f"🔍 **Signal Wi-Fi :** {signal}% - {status}\n   {comment}\n\n"
        
        return analysis
    
    def get_solution(self, question):
        """Génère une solution complète"""
        topics = self.identify_topic(question)
        knowledge_context = self.get_knowledge_context(topics)
        network_analysis = self.analyze_network(question)
        
        if not topics and not network_analysis:
            return "📡 **Agent Télécom**\n\nJe suis spécialisé en télécommunications et informatique.\n\n**Voici ce que je peux faire :**\n• Diagnostiquer des problèmes réseau\n• Analyser la latence, le débit, le signal Wi-Fi\n• Recommander des solutions techniques\n• Expliquer les concepts (IPv4, IPv6, DNS, VPN, 5G, IoT, Cloud, Cybersécurité)\n• Aider à la sécurisation des systèmes\n\n**Exemples de questions :**\n• "J'ai 200 ms de latence, c'est grave ?"\n• "Comment améliorer mon Wi-Fi ?"\n• "Qu'est-ce que le 5G ?"\n• "Comment sécuriser mon réseau ?"\n\n**Posez votre question technique !**"
        
        return f"""
📡 **ANALYSE TÉLÉCOM & INFORMATIQUE**

{knowledge_context}

{network_analysis}

💡 **SOLUTION PROPOSÉE :**

{self.generate_recommendation(topics, question, network_analysis)}

📚 **SOURCES :** Base de connaissances Télécom & Informatique
"""
    
    def generate_recommendation(self, topics, question, analysis):
        """Génère une recommandation personnalisée"""
        if not topics:
            return "Analyse en cours... Veuillez préciser votre question technique."
        
        recommendations = []
        
        for topic in topics:
            if topic in self.knowledge:
                data = self.knowledge[topic]
                if 'solutions' in data:
                    recommendations.extend(data['solutions'])
                if 'bonnes_pratiques' in data:
                    recommendations.extend(data['bonnes_pratiques'])
        
        if recommendations:
            return "1. " + "\n2. ".join(recommendations[:5])
        
        return "Effectuez un diagnostic plus précis de votre infrastructure."

# ==================================================
# ROUTES API
# ==================================================
agent = TelecomAgent()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    reponse = agent.get_solution(question)
    return jsonify({"reponse": reponse})

# ==================================================
# FRONTEND
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
    <div class="sub">Réseaux · Sécurité · 5G · IoT · Cloud · Informatique</div>
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
        <div class="suggestion" data-q="Que signifie IPv6 ?">🌐 IPv6</div>
        <div class="suggestion" data-q="C'est quoi un VPN ?">🔐 VPN</div>
    </div>
    <div class="footer">📡 Expert en télécommunications et informatique · Diagnostic réseau · Solutions techniques</div>
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
        addMessage("❌ Erreur. Veuillez réessayer.", 'bot');
    }
}

document.getElementById('send').onclick = send;
input.onkeypress = (e) => { if(e.key === 'Enter') { e.preventDefault(); send(); } };
document.querySelectorAll('.suggestion').forEach(s => { s.onclick = () => { input.value = s.dataset.q; send(); }; });

addMessage('📡 **KENNYSON OURAGAN - AGENT TÉLÉCOM & INFORMATIQUE**\n\nBonjour ! Je suis votre expert en télécommunications.\n\n**🔍 Mes compétences :**\n• 📊 Analyse de réseau (latence, débit, signal)\n• 🔒 Cybersécurité (pare-feu, VPN, protection)\n• 📶 Technologies (5G, Wi-Fi, IoT)\n• 🌐 Protocoles (IPv4, IPv6, DNS, TCP/IP)\n• ☁️ Cloud Computing (IaaS, PaaS, SaaS)\n\n**💡 Posez-moi vos questions techniques :**\n• "J\'ai 150 ms de latence, c\'est normal ?"\n• "Comment configurer un VPN ?"\n• "Quelle est la différence entre IPv4 et IPv6 ?"\n• "Comment sécuriser mon réseau Wi-Fi ?"\n• "Qu\'est-ce que le 5G et à quoi ça sert ?"\n\nJe vous donne des diagnostics précis et des solutions concrètes ! 🔥', 'bot');
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
