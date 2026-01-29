# Knowledge Graph - Alignement d'Ontologies

## 🎯 But du Projet

Ce projet implémente une pipeline complète d'alignement sémantique d'ontologies utilisant des embeddings BERT et la recherche vectorielle. L'objectif est de fusionner automatiquement deux ontologies (Source A et Source B) en détectant les concepts équivalents et en enrichissant les données. Un système RAG (Retrieval Augmented Generation) permet ensuite d'interroger le knowledge graph fusionné en langage naturel via des requêtes SPARQL dynamiques et un agent IA.

## 📁 Dossier Exploration

Le dossier `Exploration/` contient des expérimentations et tests préliminaires réalisés pendant le développement du projet. Il inclut des notebooks Jupyter pour la découverte des formats OWL/JSON, des scripts de conversion, et des travaux préparatoires sur l'alignement sémantique. Ce dossier sert d'archive des différentes approches testées avant la mise en place de la pipeline finale.

## ⚙️ Configuration

### 1. Fichier `.env`

Créer un fichier `.env` à la racine du projet avec :

```env
# MongoDB (pour la vectorisation)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# GraphDB
GRAPHDB_URL=http://localhost:7200
GRAPHDB_REPOSITORY=PFE-GraphDB

# OpenAI (pour le RAG)
OPENAI_API_KEY=sk-proj-...votre_clé...
```

### 2. Environnement Python

```bash
conda create -n pfe_env python=3.10
conda activate pfe_env
pip install -r requirements.txt
```

## 🚀 Lancement

### Pipeline de Démonstration

**Version CLI :**
```bash
python demo/demo.py
```

**Version GUI :**
```bash
python demo/demo_gui.py
```

### Système RAG

**Version CLI :**
```bash
cd rag
python rag_agent.py
```

**Version Streamlit (interface web) :**
```bash
cd rag
streamlit run streamlit_app.py
```

### Charger les Ontologies Sources dans GraphDB

Pour charger les ontologies sources A et B (AVANT alignement) :

```bash
python graphdb/load_source_ontologies.py
```

Pour charger l'ontologie fusionnée (APRÈS alignement) :

```bash
python graphdb/load_merged_ontology.py
```

---

**Note :** GraphDB doit être lancé sur http://localhost:7200 avec un repository nommé `PFE-GraphDB`.
