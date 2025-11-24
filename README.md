# Knowledge Graph RAG - PFE Servier

## 📋 Projet

Système de Retrieval-Augmented Generation (RAG) utilisant un graphe de connaissances pharmaceutiques. Le système interroge un graphe RDF (WikiData, PubChem, ChEBI) via SPARQL et génère des réponses contextuelles avec Google Gemini.

**Stack:** Python 3.10 • MongoDB Atlas • GraphDB 11.1.1 • Google Gemini API • Streamlit

---

## 🚀 Lancer le RAG

### Installation initiale

```bash
# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos credentials MongoDB et Gemini API Key

# Installer les dépendances
pip install -r requirements.txt
```

### Streamlit Web UI

```bash
streamlit run RAG/AI-AGENT/streamlit_app.py
```

Accédez à `http://localhost:8501` pour l'interface interactive.

### RAG en ligne de commande

```bash
python3 RAG/AI-AGENT/rag_agent.py
```

Interface conversationnelle pour poser des questions au graphe.

---

## 📊 Système Data

**⚠️ Prérequis :** GraphDB 11.1.1 doit être lancé localement (`http://localhost:7200`)

```
[Protégé] 
    ↓ export .ttl
[data/Sources/] (source_wikidata.ttl, source_pubchem.ttl, source_chebi.ttl)
    ↓ ttl_to_mongo.py
[MongoDB Atlas - Servier.GraphDB]
    ↓ mongo_to_graphdb.py
[GraphDB Local - PFE-GraphDB Repository]
    ↓ SPARQL Queries
[RAG Agent + Streamlit UI]
```

### Scripts d'ingestion (`data/Ingestion/`)

- **`ttl_to_mongo.py`** : Parse les fichiers `.ttl` avec RDFlib, convertit en JSON, ingère dans MongoDB (replace_one pour éviter les doublons)
- **`mongo_to_graphdb.py`** : Synchronise les triples MongoDB → GraphDB via SPARQL UPDATE (batch de 1000 triples)
- **`reset_graphdb.py`** : Vide complètement le repository GraphDB (utile pour les tests)

**Utilisation typique :**
```bash
python3 data/Ingestion/ttl_to_mongo.py        # Import .ttl → MongoDB
python3 data/Ingestion/mongo_to_graphdb.py    # MongoDB → GraphDB
python3 RAG/AI-AGENT/streamlit_app.py         # Lancer le RAG
```

---

## 📁 Structure du projet

```
servier-knowledge-graph/
├── .env                          # Variables d'environnement (MongoDB, GraphDB, Gemini)
├── requirements.txt              # Dépendances Python
├── README.md                     # Ce fichier
│
├── data/
│   ├── Sources/                  # Fichiers RDF Turtle (.ttl)
│   │   ├── source_wikidata.ttl
│   │   ├── source_pubchem.ttl
│   │   └── source_chebi.ttl
│   ├── Ingestion/                # Scripts d'ingestion de données
│   │   ├── ttl_to_mongo.py
│   │   ├── mongo_to_graphdb.py
│   │   ├── reset_graphdb.py
│   │   └── clear_mongo.py
│   └── Data_simulation/          # Chargement medical_ontology.owl
│       └── load_to_graphdb.py
│
├── RAG/
│   ├── AI-AGENT/                 # Agent RAG principal
│   │   ├── rag_agent.py          # Orchestration RAG
│   │   ├── streamlit_app.py      # Interface Web
│   │   └── agent_configuration.json
│   └── Tools/                    # Outils SPARQL
│       └── sparql_tools.py       # Requêtes SPARQL pour GraphDB
│
└── Exploration/                  # Notebooks de recherche (exploratoire)
```

---

## ✅ Conclusion

Ce système offre un pipeline complet : de l'ontologie Protégé au RAG interactif, avec MongoDB et GraphDB comme socle de données centralisé et fiable.
