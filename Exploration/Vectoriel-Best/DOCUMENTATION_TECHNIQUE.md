# Documentation Technique - Alignement Vectoriel Optimisé

## 🎯 Vue d'ensemble

Ce dossier représente l'approche **vectorielle optimisée** du projet - la base de la pipeline finale implémentée dans `pipeline/`. C'est une approche supervisée de matching sémantique qui utilise :

- **Vectorisation BERT** : Embeddings sémantiques des classes
- **MongoDB Vector Search** : Recherche vectorielle scalable
- **Matching hiérarchique** : Parcours la hiérarchie des classes
- **Seuils configurables** : Contrôle granulaire de la précision

**Approche** : Recherche vectorielle directe avec validation hiérarchique.

---

## 🏗️ Architecture Vectorielle

### 1. Concept Principal

Transformer le problème d'alignement en **recherche similarité dans un espace vectoriel** :

```
Classe A                    Classe B1
   ↓                           ↓
Vectorization            Vectorization
(BERT Embedding)         (BERT Embedding)
   ↓                           ↓
Vecteur 384D ← Recherche → Vecteur 384D
                Cosinus
                   ↓
            Similarité [0.0-1.0]
```

### 2. Avantages de l'Approche Vectorielle

| Avantage             | Détail                                      |
| -------------------- | ------------------------------------------- |
| **Sémantique riche** | Capture le sens profond, pas juste keywords |
| **Scalabilité**      | MongoDB gère millions de vecteurs           |
| **Flexibilité**      | Pas d'entraînement, pas de données requises |
| **Rapidité**         | Index vectoriel = recherche O(log n)        |
| **Contrôle**         | Seuils, TOP-K, stratégies configurables     |

---

## 📊 Pipeline Détaillé

### Phase 1 : Préparation des Données

**Conversion JSON → CSV** (optionnel)

```python
from json_to_owl_converter import convert_to_owl
# Convertit ontologies JSON en OWL pour standardisation
```

**Extraction des attributs** :

```csv
id,classe,label,parent,definition,proprietes,individus
A_001,Lion,Lion,Carnivore,Grand félin...,["quadrupède","carnivore"],[...]
B_042,Tiger,Tiger,BigCat,Grand carnivore...,["chasseur"],[...]
```

**Attributs vectorisés** :

- `label` : Nom principal
- `definition` : Description textuelle
- `proprietes` : Caractéristiques
- `parent` : Contexte hiérarchique

### Phase 2 : Vectorisation BERT

**`vectorize_ontology.py`** : Génère les embeddings

```python
from sentence_transformers import SentenceTransformer

# Modèle efficace (384 dimensions vs 768 pour BERT complet)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Encodage texte riche pour chaque classe
rich_text = f"{label} {definition} {properties}"
embedding = model.encode(rich_text)  # Vecteur 384D

# Insertion MongoDB
db.vectors.insert_one({
    'class_id': 'A_001',
    'ontology': 'A',
    'embedding': embedding,
    'metadata': {...}
})
```

**Configuration MongoDB Atlas** :

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "dimensions": 384,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```

### Phase 3 : Recherche Vectorielle Hiérarchique

**`semantic_matching.py`** : Trouve les alignements

```python
from pymongo import MongoClient

# Connexion MongoDB
client = MongoClient(MONGODB_URI)
db = client['knowledge_graph']

# Pour chaque classe A, chercher dans B
for class_a in ontology_a.classes:
    embedding_a = model.encode(class_a.rich_text)

    # Recherche vectorielle dans B
    results = db.vectors.aggregate([
        {
            "$search": {
                "cosmosSearch": {
                    "vector": embedding_a,
                    "k": 5  # Top-5
                },
                "returnBaseScore": true
            }
        },
        {
            "$project": {
                "class_id": 1,
                "score": { "$meta": "searchScore" }
            }
        }
    ])

    # Filtrer par seuil (0.85)
    alignments = [
        r for r in results
        if r['score'] > SIMILARITY_THRESHOLD
    ]
```

**Paramètres clés** :

- `k=5` : Retourner top 5 candidats
- `threshold=0.85` : Accepter scores > 0.85
- `metric='cosine'` : Similarité cosinus

### Phase 4 : Validation Hiérarchique

**Parcours hiérarchique** :

```python
# Si la classe A a des parents, chercher aussi dans ces contextes
parent_a = class_a.parent
while parent_a:
    parent_results = search_in_context(parent_a)
    alignments.extend(parent_results)
    parent_a = parent_a.parent

# Fusionner les résultats
# Score final = max(direct_match, parent_context_match)
```

**Rationale** :

- Un "Tiger" dans B qui descend de "BigCat" peut matcher avec "Lion" (dans "Carnivore")
- La hiérarchie aide à éliminer faux positifs

### Phase 5 : Fusion Intelligente

**`align_ontology.py`** : Crée l'ontologie fusionnée

```python
class OntologyMerger:
    def merge(self):
        # Pour chaque alignement
        for source, target, score in alignments:
            # Créer classe fusionnée
            merged_class = MergedClass(
                source_id=source,
                target_id=target,
                confidence=score,
                properties={...}
            )
            self.merged_ontology.add(merged_class)

        # Préserver la hiérarchie
        self.preserve_hierarchy()
        self.save_as_owl()
        self.save_as_json()
```

**Version Interactive** (validation manuelle) :

```python
# align_ontology_interactive.py
for alignment in alignments:
    print(f"Aligner {alignment.source} → {alignment.target}? (oui/non)")
    if input().lower() == 'oui':
        accept_alignment(alignment)
```

---

## 🔢 Scoring et Similarité

### Similarité Cosinus

```
similarity(a, b) = (a · b) / (||a|| × ||b||)
```

Pour vecteurs normalisés L2 :

| Similarity | Interprétation                | Confiance  |
| ---------- | ----------------------------- | ---------- |
| 0.95+      | Très proche (quasi-synonymes) | ✅✅✅✅✅ |
| 0.90-0.95  | Proche (bons alignements)     | ✅✅✅✅   |
| 0.85-0.90  | Assez proche (acceptables)    | ✅✅✅     |
| 0.80-0.85  | Modérément proche             | ⚠️✅✅     |
| 0.75-0.80  | Faiblement proche             | ⚠️⚠️       |
| <0.75      | Peu rapport                   | ❌         |

**Seuil du projet** : 0.85 (bon équilibre Précision/Rappel)

---

## 📊 Formats des Résultats

### Alignments JSON

```json
{
  "alignments": [
    {
      "source": "ontologie_A_Lion",
      "target": "ontologie_B_Tiger",
      "similarity_score": 0.92,
      "confidence": 0.92,
      "source_label": "Lion",
      "target_label": "Tiger",
      "embedding_model": "all-MiniLM-L6-v2",
      "metadata": {
        "source_parent": "Carnivore",
        "target_parent": "BigCat"
      }
    },
    ...
  ]
}
```

### Ontologie Fusionnée (OWL)

```xml
<owl:Class rdf:about="http://example.org/merged#LionTiger">
  <rdfs:label>Lion-Tiger Merged</rdfs:label>
  <owl:sameAs rdf:resource="http://ontA#Lion"/>
  <owl:sameAs rdf:resource="http://ontB#Tiger"/>
  <dc:hasSimilarity rdf:datatype="http://www.w3.org/2001/XMLSchema#float">0.92</dc:hasSimilarity>
</owl:Class>
```

---

## ✅ Avantages de l'Approche Vectorielle

| Avantage               | Détail                                   |
| ---------------------- | ---------------------------------------- |
| **Sémantique riche**   | BERT capture contexte profond            |
| **Scalabilité**        | Millions de vecteurs via MongoDB         |
| **Pas d'entraînement** | Modèles BERT pré-entraînés               |
| **Flexibilité**        | Seuils et paramètres ajustables          |
| **Hiérarchie**         | Parcours hiérarchique preserve structure |
| **Vitesse**            | Recherche vectorielle indexée = O(log n) |

---

## ❌ Limitations

| Limitation             | Détail                                                |
| ---------------------- | ----------------------------------------------------- |
| **MongoDB requis**     | Nécessite cluster Atlas + Vector Search               |
| **Coût cloud**         | Subscriptions MongoDB Atlas                           |
| **Qualité labels**     | Dépend des descriptions disponibles                   |
| **One-to-many**        | Un concept peut avoir plusieurs matches               |
| **Pas d'entraînement** | Ne peut pas apprendre patterns domaine                |
| **Mémoire**            | Embeddings prennent espace (384×8 bytes = 3KB/classe) |

---

## 🚀 Flux Complet

```
Ontologies JSON
    ↓
json_to_owl_converter.py (optionnel)
    ↓
Ontologies OWL
    ↓
mapping_ontologies.py → CSV
    ↓
vectorize_ontology.py → MongoDB (embeddings)
    ↓
semantic_matching.py → Recherche vectorielle
    ↓
alignment_results.json
    ↓
align_ontology.py (ou .interactive)
    ↓
merged_ontology.{owl,json}
```

---

## 🔧 Configuration

### 1. Variables d'Environnement

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
VECTOR_SEARCH_INDEX=vector_search_index
SIMILARITY_THRESHOLD=0.85
TOP_K=5
```

### 2. Modèles BERT Disponibles

```python
# Rapide et léger (déjà utilisé)
SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

# Plus puissant mais lent
SentenceTransformer('all-mpnet-base-v2')  # 768 dimensions

# Multilingue
SentenceTransformer('distiluse-base-multilingual-cased-v2')
```

---

## 📈 Amélioration Future

1. **Fine-tuning BERT** : Entraîner sur domaine spécifique
2. **Ensemble methods** : Combiner plusieurs modèles BERT
3. **Graph-based refinement** : Utiliser structure graphe pour raffiner
4. **Active learning** : Incorporer feedback utilisateur
5. **Hybrid approaches** : Combiner vectoriel + BERTMap + Clustering

---

## 🎓 Quand Utiliser l'Approche Vectorielle ?

✅ **Idéal pour** :

- Alignement automatique d'ontologies générales
- Quand MongoDB Atlas est disponible
- Besoin de vitesse et scalabilité
- Descriptions/labels de bonne qualité
- Cas d'usage production

❌ **Éviter si** :

- Labels très pauvres
- Pas d'accès MongoDB
- Besoin précision extrême (>99%)
- Domaine très spécialisé/jargon

---

## 📚 Relation avec Pipeline Finale

Ce dossier **"Vectoriel-Best"** est la base de la pipeline finale (`/pipeline/`) :

| Composant     | Vectoriel-Best          | Pipeline Finale                        |
| ------------- | ----------------------- | -------------------------------------- |
| Vectorization | `vectorize_ontology.py` | `pipeline/vectorize_ontology.py`       |
| Matching      | `semantic_matching.py`  | `pipeline/semantic_matching.py`        |
| Fusion        | `align_ontology.py`     | `alignement/scripts/align_ontology.py` |
| Interaction   | ❌ Non                  | ✅ RAG + SPARQL                        |

**Améliorations dans la version finale** :

- Meilleure gestion des erreurs
- Support batch processing
- Intégration GraphDB
- Agent IA RAG complet
