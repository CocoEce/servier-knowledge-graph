# Knowledge Graph - Alignement Sémantique d'Ontologies

## 🎯 But du Projet

Ce projet implémente une **pipeline complète et automatisée d'alignement sémantique d'ontologies** utilisant les embeddings BERT et la recherche vectorielle. L'objectif principal est de :

1. **Fusionner automatiquement deux ontologies** (Source A et Source B) en détectant les concepts équivalents
2. **Enrichir les données** en préservant la traçabilité des sources
3. **Interroger le knowledge graph fusionné** en langage naturel grâce à un système RAG avec agent IA

Le projet démontre une approche complète de l'alignement sémantique : du parsing des ontologies OWL/JSON, à la vectorisation intelligente, jusqu'à l'interaction en langage naturel via SPARQL.

---

## 📁 Organisation des Dossiers

### 📊 **`data/`** - Données Source
Contient les ontologies originales dans plusieurs formats :
- **`csv/`** : Versions CSV des ontologies (format tabulaire pour le traitement)
- **`json/`** : Versions JSON des ontologies (format intermédiaire)
- **`owl/`** : Versions OWL originales (format standard des ontologies sémantiques)

**Rôle :** Base de données source pour toute la pipeline. Les ontologies `ontologie_animaux_A` et `ontologie_animaux_B` servent de cas d'étude.

---

### 🔄 **`pipeline/`** - Cœur du Processus d'Alignement
Contient les scripts principaux orchestrant l'alignement sémantique :

- **`mapping_ontologie.py`** : Première étape - Extrait les classes, propriétés, relations hiérarchiques et individus des ontologies OWL et les convertit en CSV
  
- **`vectorize_ontology.py`** : Deuxième étape - Génère des embeddings BERT pour chaque classe et les stocke dans MongoDB Atlas Vector Search
  
- **`semantic_matching.py`** : Troisième étape - Effectue la recherche vectorielle hiérarchique pour trouver les correspondances entre les classes des deux ontologies (seuil de similarité : 0.85)

**Flux de données :** OWL → CSV → Embeddings MongoDB → Alignement sémantique

---

### 🔗 **`alignement/`** - Résultats et Scripts de Fusion
Contient les résultats et scripts de fusion des ontologies alignées :

- **`scripts/`**
  - `align_ontology.py` : Fusionne les ontologies alignées en une seule ontologie cohérente
  - `align_ontology_interactive.py` : Version interactive permettant la validation manuelle des alignements

- **`results/`** : Résultats bruts de l'alignement sémantique
  - `alignment_results.json` : Correspondances trouvées entre A et B avec scores de similarité

- **`merged/`** : Ontologies fusionnées finales
  - `merged_ontology.owl` : Format OWL standard
  - `merged_ontology.json` : Format JSON pour l'exploitation

---

### 🎮 **`demo/`** - Interface de Démonstration
Deux interfaces pour tester la pipeline complète :

- **`demo.py`** : Interface CLI interactif
  - Orchestre les étapes : mapping → vectorisation → matching → fusion interactive
  - Permet de sauter certaines étapes avec des flags (`--skip-mapping`, `--skip-vectorize`, `--skip-matching`)

- **`demo_gui.py`** : Interface graphique (GUI)
  - Version plus conviviale pour les utilisateurs non-techniques

---

### 🤖 **`rag/`** - Agent d'Interrogation en Langage Naturel
Système RAG (Retrieval Augmented Generation) pour interroger le knowledge graph fusionné :

- **`rag_agent.py`** : Agent principal utilisant OpenAI GPT
  - Reçoit des questions en langage naturel
  - Traduit automatiquement en requêtes SPARQL
  - Interroge le knowledge graph et génère des réponses intelligentes

- **`streamlit_app.py`** : Interface web interactive avec Streamlit
  - Dashboard visuel pour explorer et interroger le knowledge graph
  - Visualisation des réponses et des requêtes SPARQL exécutées

- **`sparql_tools.py`** : Utilitaires SPARQL
  - Gestion des requêtes SPARQL vers GraphDB
  - Outils pour formater et exécuter les requêtes

- **`agent_configuration.json`** : Configuration de l'agent IA
  - Définition des outils disponibles
  - Instructions et comportement de l'agent

---

### 📦 **`graphdb/`** - Chargement dans GraphDB
Scripts pour persister les ontologies dans GraphDB (triplestore RDF) :

- **`load_source_ontologies.py`** : Charge les ontologies sources A et B séparément
  - Crée les named graphs `graph_A` et `graph_B`
  - Utilisé pour explorer les sources avant fusion

- **`load_merged_ontology.py`** : Charge l'ontologie fusionnée finale
  - Crée le named graph `graph_merged`
  - Point d'accès pour le système RAG

**Rôle :** Transformation des fichiers RDF/OWL en triplestore interrogeable via SPARQL

---

### 🧪 **`Exploration/`** - Expériences et Prototypes
Archive des travaux préliminaires et expérimentations du projet :

- **`classification/`** : Expériences de classification d'ontologies
  - `run_classification_pipeline.py` : Pipeline de classification des classes
  - Résultats et statistiques générés

- **`Clustering/`** : Essais de clustering sémantique
  - `DOID-ORDO/` : Expériences sur des ontologies médicales
  - `TaxonomieAnimal/` : Travaux spécifiques aux ontologies animales
  - `run_pipeline.py/sh` : Scripts d'exécution des pipelines de clustering

- **`Bertmap/`** : Expérimentations avec BertMap (outil d'alignement d'ontologies)
  - Tests sur des datasets anatomiques

- **`Vectoriel-Best/`** : Approches vectorielles optimisées
  - Pipeline améliorée de vectorisation

- **`TP-Explo/`** : Travaux pratiques et prototypes
  - `TP INSA Rouen/` : Travaux académiques
  - `TP Perso/` : Expériences personnelles avec les formats OWL et JSON

**Rôle :** Documentation des approches testées et base pour le choix de l'architecture finale

---

## ⚙️ Configuration et Installation

### 1. Environnement Python

```bash
# Créer un environnement conda
conda create -n pfe_env python=3.10
conda activate pfe_env

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Fichier `.env` (Variables d'Environnement)

Créer un fichier `.env` à la racine du projet :

```env
# MongoDB Atlas (pour la vectorisation avec recherche vectorielle)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# GraphDB (triplestore RDF pour persister les ontologies)
GRAPHDB_URL=http://localhost:7200
GRAPHDB_REPOSITORY=PFE-GraphDB
GRAPHDB_USERNAME=admin
GRAPHDB_PASSWORD=admin

# OpenAI (pour le RAG et l'agent IA)
OPENAI_API_KEY=sk-proj-...votre_clé_api...
```

### 3. Services Requis

- **GraphDB** : À lancer localement sur `http://localhost:7200`
  - Créer un repository nommé `PFE-GraphDB`
- **MongoDB Atlas** : Cluster cloud avec Vector Search activé
- **Clé OpenAI** : Pour accéder à l'API GPT

---

## 🚀 Guide d'Utilisation

### Étape 1 : Exécuter la Pipeline Complète

**Option A - Interface CLI Automatique :**
```bash
python demo/demo.py
```

**Option B - Interface GUI :**
```bash
python demo/demo_gui.py
```

Ces scripts orchestrent automatiquement :
1. Mapping OWL → CSV
2. Vectorisation dans MongoDB
3. Alignement sémantique
4. Fusion interactive des ontologies

### Étape 2 : Charger les Ontologies dans GraphDB

```bash
# Charger les sources A et B (avant fusion)
python graphdb/load_source_ontologies.py

# Charger l'ontologie fusionnée (après fusion)
python graphdb/load_merged_ontology.py
```

### Étape 3 : Interroger le Knowledge Graph

**Option A - Agent CLI :**
```bash
cd rag
python rag_agent.py
```

**Option B - Interface Web (Streamlit) :**
```bash
cd rag
streamlit run streamlit_app.py
```

Posez des questions en langage naturel :
```
> Quels sont les animaux carnivores ?
> Montrez-moi la hiérarchie des mammifères
> Quels sont les propriétés du lion ?
```

---

## 📊 Dépendances Clés

| Composant | Libraire | Usage |
|-----------|----------|-------|
| Ontologies OWL | `rdflib==7.0.0` | Parsing et manipulation des ontologies |
| Embeddings | `sentence-transformers==2.2.2` | Génération d'embeddings BERT |
| Vectorisation | `pymongo==4.5.0` | Stockage et recherche vectorielle |
| LLM | `openai==1.12.0` | Agent IA pour le RAG |
| Interface web | `streamlit==1.31.0` | Dashboard interactif |
| Traitement | `pandas==2.0.3`, `numpy==1.24.3` | Manipulation de données |

---

## 🔄 Flux de Données Complet

```
Data Sources (OWL)
       ↓
[pipeline/mapping_ontologie.py]        → CSV
       ↓
[pipeline/vectorize_ontology.py]       → MongoDB (embeddings)
       ↓
[pipeline/semantic_matching.py]        → Alignements JSON
       ↓
[alignement/scripts/align_ontology.py] → Ontologie fusionnée (OWL/JSON)
       ↓
[graphdb/load_merged_ontology.py]      → GraphDB (triplestore)
       ↓
[rag/rag_agent.py]                     → Agent IA + SPARQL
       ↓
User Query (Natural Language) → Answer (en langage naturel)
```

---

## 📝 Structure des Formats

### Format OWL (RDF/XML)
Structure hiérarchique des classes, propriétés et relations

### Format CSV (après mapping)
```
id, classe, label, parent, definition, proprietes, individus
```

### Format JSON (résultats d'alignement)
```json
{
  "alignments": [
    {
      "source": "ontologie_A_classe",
      "target": "ontologie_B_classe",
      "similarity_score": 0.92,
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
    }
  ]
}
```

---

## 🔐 Sécurité

- Les credentials MongoDB et GraphDB doivent être en `.env` (jamais commités)
- La clé OpenAI API doit rester confidentielle
- Utiliser des HTTPS pour les services en production

---

## 📚 Ressources Complémentaires

- Voir `Exploration/classification/DOCUMENTATION_TECHNIQUE.md` pour plus de détails techniques
- Voir `Exploration/Clustering/README.md` pour les approches de clustering
- Voir `Exploration/Bertmap/README.md` pour les expériences BertMap
