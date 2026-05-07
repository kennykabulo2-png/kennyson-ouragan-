from flask import Flask, jsonify, render_template_string
import json

app = Flask(__name__)

# ==================== DONNEES ====================
AGENTS = [
    {"id": "AG-001", "nom": "KABULO Kenny", "grade": "Directeur", "salaire": 3000000},
    {"id": "AG-002", "nom": "MBEMBA Jeanne", "grade": "Chef Bureau", "salaire": 2100000},
    {"id": "AG-003", "nom": "TSHIBANDA Paul", "grade": "Agent", "salaire": 1300000},
]

SOCIETES = [
    {"nom": "Minière du Congo", "secteur": "Mines", "impot_du": 13500, "impot_paye": 3200, "statut": "Alerte"},
    {"nom": "Telecom Congo", "secteur": "Telco", "impot_du": 8400, "impot_paye": 7600, "statut": "Conforme"},
    {"nom": "BTP Congo", "secteur": "BTP", "impot_du": 3600, "impot_paye": 3100, "statut": "Modéré"},
    {"nom": "Commerce Intl", "secteur": "Commerce", "impot_du": 2400, "impot_paye": 500, "statut": "Alerte"},
]

LIVRES = [
    {"titre": "Le prix de la corruption", "auteur": "M. Nkolo", "categorie": "Anti-corruption"},
    {"titre": "Gestion des finances publiques", "auteur": "J. Tshibangu", "categorie": "Finances"},
    {"titre": "Manuel du citoyen congolais", "auteur": "Société civile", "categorie": "Droits citoyens"},
]

# ==================== TEMPLATE HTML ====================
BASE_HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OYEBI · {title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #F4F6FA; color: #1E2A3A; }}
        .navbar {{ background: #003366; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }}
        .logo {{ color: white; font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }}
        .logo i {{ color: #FACC15; }}
        .nav-links a {{ color: white; text-decoration: none; margin-left: 1.5rem; font-weight: 500; }}
        .nav-links a:hover {{ color: #FACC15; }}
        .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }}
        .hero {{ background: white; border-radius: 1rem; padding: 2rem; text-align: center; margin-bottom: 2rem; border: 1px solid #E2E8F0; }}
        .hero h1 {{ font-size: 2rem; color: #003366; }}
        .card {{ background: white; border-radius: 1rem; padding: 1.2rem; margin-bottom: 1.5rem; border: 1px solid #E2E8F0; }}
        .card h3 {{ color: #003366; margin-bottom: 1rem; border-left: 3px solid #FACC15; padding-left: 0.7rem; }}
        .grid-4 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .kpi-card {{ background: white; border-radius: 1rem; padding: 1rem; text-align: center; border: 1px solid #E2E8F0; }}
        .kpi-value {{ font-size: 1.8rem; font-weight: 700; color: #003366; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
        th, td {{ padding: 0.6rem 0.2rem; text-align: left; border-bottom: 1px solid #E2E8F0; }}
        .badge-alert {{ background: #FEE2E2; color: #B91C1C; padding: 0.2rem 0.6rem; border-radius: 2rem; font-size: 0.7rem; }}
        .badge-conforme {{ background: #E0F2FE; color: #0369A1; }}
        .badge-modere {{ background: #FEF9C3; color: #854D0E; }}
        .footer {{ text-align: center; padding: 1.5rem; font-size: 0.7rem; color: #64748B; border-top: 1px solid #E2E8F0; margin-top: 2rem; }}
        @media (max-width: 768px) {{ .nav-links a {{ margin: 0 0.8rem; }} }}
    </style>
</head>
<body>
<div class="navbar">
    <div class="logo"><i class="fas fa-chart-line"></i> OYEBI</div>
    <div class="nav-links">
        <a href="/">Accueil</a>
        <a href="/dashboard">Dashboard</a>
        <a href="/insights">Insights</a>
        <a href="/objectifs">Objectifs</a>
        <a href="/bibliotheque">Bibliothèque</a>
    </div>
</div>
<div class="container">
    {content}
</div>
<footer class="footer">
    <p>OYEBI · Kinshasa, RDC</p>
</footer>
</body>
</html>
'''

def render_page(title, content):
    return BASE_HTML.format(title=title, content=content)

# ==================== PAGES ====================
ACCUEIL = '''
<div class="hero">
    <h1>OYEBI</h1>
    <p>La gouvernance transparente pour un Congo qui avance</p>
</div>
<div class="grid-4">
    <div class="card"><i class="fas fa-chart-line" style="font-size:2rem; color:#003366;"></i><h3>Données fiables</h3><p>Issues des bases officielles</p></div>
    <div class="card"><i class="fas fa-eye" style="font-size:2rem; color:#003366;"></i><h3>Transparence totale</h3><p>Visualisez les fonds publics</p></div>
    <div class="card"><i class="fas fa-shield-alt" style="font-size:2rem; color:#003366;"></i><h3>Sécurité avancée</h3><p>Accès agent certifié</p></div>
    <div class="card"><i class="fas fa-database" style="font-size:2rem; color:#003366;"></i><h3>Données ouvertes</h3><p>API publiques disponibles</p></div>
</div>
'''

DASHBOARD = '''
<div class="hero"><h1>Tableau de bord stratégique</h1><p>Indicateurs clés de la gouvernance</p></div>
<div class="grid-4" id="kpis"></div>
<div class="card"><h3>📈 Comparaison impôts (M$)</h3><canvas id="chart"></canvas></div>
<div class="card"><h3>👥 Agents de l'État</h3><div id="agentsTable"></div></div>
<div class="card"><h3>🏢 Sociétés</h3><div id="societesTable"></div></div>
<script>
    async function fetchData(url) { let r = await fetch(url); return r.json(); }
    async function load() {
        let agents = await fetchData('/api/agents');
        let societes = await fetchData('/api/societes');
        let stats = await fetchData('/api/stats');
        document.getElementById('kpis').innerHTML = `
            <div class="kpi-card"><div class="kpi-value">${stats.nb_agents}</div><div>Agents</div></div>
            <div class="kpi-card"><div class="kpi-value">${stats.nb_societes}</div><div>Sociétés</div></div>
            <div class="kpi-card"><div class="kpi-value">${(stats.masse_salariale/1e6).toFixed(1)}M</div><div>Masse salariale</div></div>
            <div class="kpi-card"><div class="kpi-value">${(stats.manque_fiscal/1e6).toFixed(0)}M</div><div>Manque à gagner</div></div>
        `;
        let agentsHtml = '<table>';
        agents.forEach(a => { agentsHtml += `<tr><td><strong>${a.nom}</strong><br><small>${a.grade}</small></td><td>${(a.salaire/1e6).toFixed(2)}M FC</td></td>`; });
        agentsHtml += '</table>';
        document.getElementById('agentsTable').innerHTML = agentsHtml;
        let societesHtml = '<table><thead><tr><th>Société</th><th>Impôt dû</th><th>Payé</th><th>Statut</th> </thead><tbody>';
        societes.forEach(s => {
            let badge = s.statut === 'Alerte' ? 'badge-alert' : (s.statut === 'Conforme' ? 'badge-conforme' : 'badge-modere');
            societesHtml += `<tr><td>${s.nom}</td><td>${s.impot_du}M$</td><td>${s.impot_paye}M$</td><td><span class="${badge}">${s.statut}</span></td>`;
        });
        societesHtml += '</tbody></table>';
        document.getElementById('societesTable').innerHTML = societesHtml;
        new Chart(document.getElementById('chart'), {
            type: 'bar', data: { labels: societes.map(s => s.nom), datasets: [{ label: 'Dû', data: societes.map(s => s.impot_du), backgroundColor: '#003366' }, { label: 'Payé', data: societes.map(s => s.impot_paye), backgroundColor: '#FACC15' }] }
        });
    }
    load();
</script>
'''

INSIGHTS = '''
<div class="hero"><h1>Insights nationaux</h1><p>Analyse des écarts fiscaux par secteur</p></div>
<div class="card"><h3>Mines</h3><div id="m"></div></div>
<div class="card"><h3>Télécoms</h3><div id="t"></div></div>
<div class="card"><h3>BTP</h3><div id="b"></div></div>
<div class="card"><h3>Répartition du manque fiscal</h3><canvas id="donut"></canvas></div>
<script>
    async function run() {
        let societes = await (await fetch('/api/societes')).json();
        let total = societes.reduce((s,c)=>s+(c.impot_du-c.impot_paye),0);
        let mines = societes.find(s=>s.nom==='Minière du Congo');
        let telecom = societes.find(s=>s.nom==='Telecom Congo');
        let btp = societes.find(s=>s.nom==='BTP Congo');
        let m = mines.impot_du - mines.impot_paye;
        let t = telecom.impot_du - telecom.impot_paye;
        let b = btp.impot_du - btp.impot_paye;
        document.getElementById('m').innerHTML = `Manque fiscal : ${m}M$ (${Math.round(m/total*100)}% du total)`;
        document.getElementById('t').innerHTML = `Manque fiscal : ${t}M$ (${Math.round(t/total*100)}%)`;
        document.getElementById('b').innerHTML = `Manque fiscal : ${b}M$ (${Math.round(b/total*100)}%)`;
        new Chart(document.getElementById('donut'), {
            type: 'doughnut',
            data: { labels: ['Mines','Télécoms','BTP','Commerce'], datasets: [{ data: societes.map(s=>s.impot_du-s.impot_paye), backgroundColor: ['#003366','#FACC15','#EF4444','#10B981'] }] }
        });
    }
    run();
</script>
'''

OBJECTIFS = '''
<div class="hero"><h1>Objectifs 2025</h1><p>Suivi des cibles de l'administration</p></div>
<div class="card"><h3>Impôts collectés</h3><div id="o1"></div><div class="progress-bar"><div id="b1" class="progress-fill"></div></div></div>
<div class="card"><h3>Agents formés</h3><div id="o2"></div><div class="progress-bar"><div id="b2" class="progress-fill"></div></div></div>
<script>
    async function load() {
        let stats = await (await fetch('/api/stats')).json();
        let obj1 = { objectif: 15000, realise: stats.manque_fiscal/1e6 };
        let obj2 = { objectif: 500, realise: 120 };
        document.getElementById('o1').innerHTML = `🎯 Objectif ${obj1.objectif}M$ | ✅ Réalisé ${obj1.realise}M$`;
        document.getElementById('o2').innerHTML = `🎯 Objectif ${obj2.objectif} agents | ✅ Réalisé ${obj2.realise} agents`;
        document.getElementById('b1').style.width = `${Math.min((obj1.realise/obj1.objectif)*100,100)}%`;
        document.getElementById('b2').style.width = `${Math.min((obj2.realise/obj2.objectif)*100,100)}%`;
    }
    load();
</script>
'''

BIBLIOTHEQUE = '''
<div class="hero"><h1>Bibliothèque citoyenne</h1><p>Lectures pour renforcer la gouvernance</p></div>
<div class="grid-4" id="booksGrid"></div>
<script>
    async function loadBooks() {
        let livres = await (await fetch('/api/livres')).json();
        let html = '';
        for (let l of livres) {
            html += `<div class="kpi-card"><i class="fas fa-book" style="font-size:1.5rem; color:#003366;"></i><h3>${l.titre}</h3><p>${l.auteur}</p><small>${l.categorie}</small></div>`;
        }
        document.getElementById('booksGrid').innerHTML = html;
    }
    loadBooks();
</script>
'''

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_page("Accueil", ACCUEIL)

@app.route('/dashboard')
def dashboard():
    return render_page("Dashboard", DASHBOARD)

@app.route('/insights')
def insights():
    return render_page("Insights", INSIGHTS)

@app.route('/objectifs')
def objectifs():
    return render_page("Objectifs", OBJECTIFS)

@app.route('/bibliotheque')
def bibliotheque():
    return render_page("Bibliothèque", BIBLIOTHEQUE)

# ==================== API ====================
@app.route('/api/agents')
def api_agents(): return jsonify(AGENTS)
@app.route('/api/societes')
def api_societes(): return jsonify(SOCIETES)
@app.route('/api/livres')
def api_livres(): return jsonify(LIVRES)
@app.route('/api/stats')
def api_stats():
    return jsonify({
        "nb_agents": len(AGENTS),
        "nb_societes": len(SOCIETES),
        "masse_salariale": sum(a['salaire'] for a in AGENTS),
        "manque_fiscal": sum(s['impot_du'] - s['impot_paye'] for s in SOCIETES) * 1_000_000
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
