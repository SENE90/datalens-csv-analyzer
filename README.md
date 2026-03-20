# DataLens — Analyseur CSV Automatique

Application Streamlit qui transforme n'importe quel CSV en rapport d'analyse complet.

## Fonctionnalités

- **Vue d'ensemble** : lignes, colonnes, valeurs manquantes, doublons
- **Statistiques descriptives** : moyenne, écart-type, percentiles, skewness, kurtosis
- **Visualisations** : histogrammes, boxplots, valeurs catégorielles
- **Corrélations** : matrice de Pearson interactive
- **Qualité des données** : manquants, doublons, outliers IQR
- **Rapport PDF** : export professionnel en 1 clic

## Lancement rapide

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Lancer l'application

```bash
streamlit run csv_analyzer_app.py
```

L'application s'ouvre automatiquement sur http://localhost:8501

## Déploiement gratuit (pour la vente)

### Option A — Streamlit Community Cloud (recommandé)
1. Créer un compte sur https://share.streamlit.io
2. Uploader le code sur GitHub
3. Connecter le repo → votre app est en ligne gratuitement

### Option B — Railway
1. Créer un compte sur https://railway.app
2. Déployer depuis GitHub
3. Ajouter un `Procfile` : `web: streamlit run csv_analyzer_app.py --server.port=$PORT`

## Vendre l'application

### Sur Gumroad (gratuit)
1. Créer un compte sur https://gumroad.com
2. Créer un produit : "DataLens — Analyseur CSV Pro"
3. Prix suggéré : 15€ – 30€ (ou 0€ pay-what-you-want pour démarrer)
4. Inclure : le code source + lien vers la démo en ligne

### Ce que vous vendez
- Le code source complet
- Un lien vers votre version hébergée (démo live)
- Un guide d'installation (ce README)

## Structure du projet

```
datalens/
├── csv_analyzer_app.py   # Application principale
├── requirements.txt      # Dépendances Python
└── README.md             # Ce fichier
```

## Stack technique

- Python 3.9+
- Streamlit (UI)
- Pandas (manipulation des données)
- Matplotlib (visualisations)
- Matplotlib PdfPages (export PDF)
