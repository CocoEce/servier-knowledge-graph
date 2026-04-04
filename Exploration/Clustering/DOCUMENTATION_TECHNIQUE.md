# Documentation Technique - Alignement par Clustering

## 🎯 Vue d'ensemble

Ce dossier explore une **approche alternative d'alignement** basée sur le **clustering sémantique**. Au lieu de classifier ou rechercher directement des correspondances, on vectorise toutes les classes et on les groupe par similarité sémantique pour découvrir automatiquement les associations.

**Approche** : Créer une "ontologie métaontologie" qui regroupe les concepts similaires des deux ontologies sources.

---

## 🏗️ Architecture du Clustering

### 1. Concept Fondamental

**Idée clé** : Les concepts similaires forment des clusters naturels dans l'espace vectoriel. En trouvant ces clusters, on découvre les alignements.

```
Ontologie A + Ontologie B
    ↓
Vectorisation tous les concepts
    ↓
Espace vectoriel N-dimensionnel
    ↓
Clustering hiérarchique (Agglomerative)
    ↓
Groupes de concepts similaires
    ↓
Création d'une "méta-ontologie" unifiée
```

### 2. Avantage Principal

**Détection entièrement automatique** : Pas besoin de :

- Données d'entraînement
- Labels de qualité
- Hiérarchie prédéfinie

Les alignements émergent naturellement des données.

---

## 📊 Pipeline Détaillé

### Phase 1 : Préparation des Données

**`prepare_data.py`** : Prépare les données à partir des ontologies

```python
# Extraction pour chaque classe
{
    "id": "class_001",
    "uri": "http://ontology#class_001",
    "label": "Tigre",
    "description": "Grand carnivore...",
    "rich_text": "Tigre grand carnivore..."  # Concat tous les attributs
}
```

**Rich_text** combine :

- Label principal
- Synonymes
- Commentaires
- Propriétés
- Domaine (médical, animal, etc.)

### Phase 2 : Extraction et Vectorisation

**`compute_embedding.py`** : Génère les embeddings

```python
from sentence_transformers import SentenceTransformer

# Modèle BERT rapide et efficace
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

# Encodage par batch
embeddings = model.encode(
    texts,
    batch_size=64,
    show_progress_bar=True
)
```

**Sortie** :

- `embeddings.npy` : Vecteurs (N × 384) en NumPy
- `metadata.csv` : Métadonnées associées

### Phase 3 : Clustering Hiérarchique

**`clustering.py`** : Regroupe les concepts par similarité

```python
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize

# Normalisation : Transforme distance Euclidienne → similarité cosinus
embeddings_norm = normalize(embeddings, norm='l2')

# Clustering hiérarchique
clusterer = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=0.50,  # Critère d'arrêt
    linkage='average',         # Moyenne des distances
    metric='euclidean'         # Distance euclidienne (équiv. cosinus sur normalisé)
)

clusters = clusterer.fit_predict(embeddings_norm)
```

**Paramètre clé** : `distance_threshold`

| Distance | Similarité Cosinus | Interprétation                     |
| -------- | ------------------ | ---------------------------------- |
| 0.30     | ~0.96              | **Très strict** - Quasi-duplicatas |
| 0.40     | ~0.92              | **Strict** - Synonymes directs     |
| 0.50     | ~0.87              | **Modéré** - Concepts très proches |
| 0.60     | ~0.82              | **Souple** - Concepts connexes     |
| 0.70     | ~0.76              | **Très souple** - Léger rapport    |

### Phase 4 : Génération de Méta-Ontologie

**`generate_meta_ontology.py`** : Crée une nouvelle ontologie

```python
# Pour chaque cluster trouvé
for cluster_id, members in clusters.items():
    # Créer une classe "virtuelle"
    meta_class = {
        "id": f"meta_{cluster_id}",
        "label": f"Group_{cluster_id}",
        "children": members,  # Classes du cluster
        "source_ontologies": ["A", "B", "A", ...]  # Origine
    }
```

**Résultat** : Ontologie "plate" qui lie concepts similaires

### Phase 5 : Analyse et Inspection

**`inspect_ontos.py`** : Inspecte les résultats

```python
# Vérifier la couverture
- Couverture Ontologie A : 95 / 100 classes
- Couverture Ontologie B : 87 / 100 classes
- Clusters uniques A/B : 45
- Clusters mixtes A+B : 38
```

---

## 🎯 Cas d'Usage Inclus

### 1. DOID-ORDO (Maladies)

**Problème** : Aligner deux ontologies de maladies

- **DOID** : Ontologie des maladies (généraliste)
- **ORDO** : Orphanet (maladies rares)

**Défi** : Terminologies différentes, hiérarchies incompatibles

**Résolution** : Clustering trouve associations automatiquement

### 2. TaxonomieAnimal (Animaux)

**Problème** : Aligner ontologies d'animaux

- **Ontologie A** : Taxonomie classique
- **Ontologie B** : Autre taxonomie

**Pipeline complet** :

```bash
python run_pipeline.py
```

**Étapes** :

1. `prepare_data.py` → prépare données
2. `extract_animal.py` → extraction spécifique animaux
3. `compute_embedding.py` → vectorise
4. `clustering.py` → cluster
5. `generate_meta_ontology.py` → génère résultats
6. `inspect_ontos.py` → analyse

**Output** :

- Clusters identifiés
- Statistiques d'alignement
- Fichiers de résultats

---

## ✅ Avantages du Clustering

| Avantage                    | Détail                                          |
| --------------------------- | ----------------------------------------------- |
| **Entièrement automatique** | Aucune donnée d'entraînement requise            |
| **Découverte de patterns**  | Révèle des groupements naturels                 |
| **Scalabilité**             | Fonctionne sur grandes ontologies               |
| **Pas de biais**            | Ne suppose rien sur la structure                |
| **Justification claire**    | Chaque alignement basé sur similarité mesurable |

---

## ❌ Limitations du Clustering

| Limitation                 | Détail                                                       |
| -------------------------- | ------------------------------------------------------------ |
| **Perte de hiérarchie**    | Ontologie résultante est "plate"                             |
| **Sensibilité aux seuils** | Petits changements de threshold = gros changements résultats |
| **Alignements N-to-N**     | Un concept peut être dans plusieurs clusters                 |
| **Qualité variable**       | Dépend fortement de la qualité des labels/descriptions       |
| **Pas de validation**      | Résultats non vérifiés vs. référence Gold-Standard           |

---

## 🔢 Interprétation des Distances

Sur vecteurs **normalisés L2**, la distance Euclidienne équivaut à la similarité cosinus :

```
Distance Euclidienne = √(2 × (1 - Similarité Cosinus))
```

**Exemples** :

```
Cosine Sim = 1.00 (identique)      → Distance ≈ 0.00
Cosine Sim = 0.95 (très proche)    → Distance ≈ 0.32
Cosine Sim = 0.90 (proche)         → Distance ≈ 0.45
Cosine Sim = 0.85 (assez proche)   → Distance ≈ 0.55
Cosine Sim = 0.80 (modérément)     → Distance ≈ 0.63
```

---

## 🔗 Types de Linkage (Agglomération)

Le clustering hiérarchique a plusieurs stratégies pour fusionner clusters :

| Linkage      | Formule           | Caractéristique                     |
| ------------ | ----------------- | ----------------------------------- |
| **single**   | `min(dist)`       | Chaîne - agrège rapidement          |
| **complete** | `max(dist)`       | Très restrictif - clusters compacts |
| **average**  | `mean(dist)`      | **Équilibré** (recommandé)          |
| **ward**     | Variance minimale | Clusters sphériques                 |

---

## 📊 Formats de Résultats

### Alignements (clusters)

```csv
cluster_id,source_id,target_id,source_ontology,target_ontology,distance
1,A_001,B_042,A,B,0.45
1,A_001,B_055,A,B,0.48
2,A_003,B_100,A,B,0.52
```

### Statistiques

```
Total clusters: 43
Clusters A uniquement: 15
Clusters B uniquement: 8
Clusters mixtes A+B: 20

Couverture A: 95/100 (95%)
Couverture B: 87/100 (87%)
```

---

## 🚀 Comparaison avec d'autres Approches

| Approche               | Supervision | Hiérarchie   | Vitesse     | Exactitude |
| ---------------------- | ----------- | ------------ | ----------- | ---------- |
| **Clustering** (ici)   | ❌ Aucune   | ❌ Perdue    | ⚡⚡ Rapide | ⭐⭐⭐     |
| **BERTMap**            | ❌ Aucune   | ✅ Préservée | ⚡⚡ Rapide | ⭐⭐⭐     |
| **Classification**     | ✅ Complète | ❌ Ignorée   | ⚡ Lent     | ⭐⭐⭐⭐⭐ |
| **Matching Vectoriel** | Partielle   | ❌ Ignorée   | ⚡ Lent     | ⭐⭐⭐⭐   |

---

## 🔧 Installation et Dépendances

```bash
pip install sentence-transformers scikit-learn pandas numpy
```

**Principales libraires** :

- `sentence-transformers` : BERT embeddings
- `scikit-learn` : Clustering
- `pandas` : Manipulation de données
- `numpy` : Calculs vectoriels

---

## 💡 Quand Utiliser le Clustering ?

✅ **Bon pour** :

- Découverte exploratoire d'alignements
- Ontologies sans données d'entraînement
- Nécessité d'automatisation complète
- Trouver des groupements cachés

❌ **Mauvais pour** :

- Besoin de préserver hiérarchie
- Alignements un-à-un strictement
- Haute précision requise
- Ontologies avec labels pauvres

---

## 📈 Amélioration Future

1. **Clustering hiérarchique amélioré** : Préserver les relations subsumption
2. **Validation vs. références** : Comparer avec alignements gold-standard
3. **Tuning des seuils** : Optimiser via grid-search
4. **Post-traitement** : Nettoyer clusters bruiteux
5. **Fusion avec autres approches** : Combiner clustering + classification
