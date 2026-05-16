from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>OYEBI fonctionne !</h1><p>Le serveur est actif.</p>"

@app.route('/dashboard')
def dashboard():
    return "<h1>Dashboard OYEBI</h1><p>Bienvenue sur le tableau de bord.</p>"

@app.route('/insights')
def insights():
    return "<h1>Insights OYEBI</h1><p>Analyse des données.</p>"

@app.route('/objectifs')
def objectifs():
    return "<h1>Objectifs 2025</h1><p>Suivi des cibles.</p>"

@app.route('/bibliotheque')
def bibliotheque():
    return "<h1>Bibliothèque citoyenne</h1><p>Livres et ressources.</p>"

@app.route('/apropos')
def apropos():
    return "<h1>À propos</h1><p>Concepteur: Kenny Kabulo Matanda</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
