# Brevet 2026 — Dashboard Contrôle Continu

Calcule les points de contrôle continu du DNB 2026 depuis Pronote (via [pronotepy](https://github.com/bain3/pronotepy)).

## Stack

- **API** : FastAPI (`api/index.py`), exposée en Vercel Function (runtime Python, auto-détecté via `requirements.txt`)
- **Front** : statique dans `public/`, servi par le CDN Vercel
- **Python** : 3.12 (épinglé dans `.python-version`)

## Déployer sur Vercel

1. Importer ce repo sur [vercel.com/new](https://vercel.com/new)
2. Aucune configuration requise : framework FastAPI auto-détecté, dépendances installées depuis `requirements.txt`, aucune variable d'environnement nécessaire (les identifiants Pronote sont saisis dans le formulaire, jamais stockés)
3. Deploy

## Dev local

```powershell
./start.ps1
# ou
pip install -r requirements.txt
python -m uvicorn api.index:app --reload
```

Ouvrir http://localhost:8000
