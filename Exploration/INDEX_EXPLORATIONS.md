# Exploration - Guide Complet des Approches d'Alignement d'Ontologies

## 📚 Vue d'Ensemble

Ce dossier **`Exploration/`** documente les différentes approches testées pour résoudre le problème d'alignement sémantique d'ontologies. Chaque sous-dossier représente une stratégie alternative pour aligner deux ontologies et créer un knowledge graph fusionné.

---

## 🗂️ Structure des Explorations

### 1️⃣ **`classification/`** - Approche Supervisée par Classification

**📄 Documentation** : [classification/DOCUMENTATION_TECHNIQUE.md](classification/DOCUMENTATION_TECHNIQUE.md)

**Concept** : Entraîner un classificateur (Random Forest) sur l'ontologie A pour prédire où chaque classe de B appartient dans A.

**Pipeline** :

```
Ontologie A (58 classes)
    ↓ [Extraction + Augmentation ×5]
290 exemples d'entraînement
    ↓ [Entraînement Random Forest]
Modèle Classification
    ↓ [Prédiction sur Ontologie B]
Alignements avec probabilités
```

**✅ Avantages** :

- Meilleure exactitude (précision très élevée)
- Probabilités bien calibrées
- Capture patterns du domaine

**❌ Inconvénients** :

- Nécessite ontologie A complète comme données d'entraînement
- Pas de hiérarchie préservée
- Plus lent à entraîner

**📊 Résultats** : Fichiers dans `Results/`

---

### 2️⃣ **`Clustering/`** - Approche Exploratoire par Clustering

**📄 Documentation** : [Clustering/DOCUMENTATION_TECHNIQUE.md](Clustering/DOCUMENTATION_TECHNIQUE.md)

**Concept** : Vectoriser tous les concepts et les grouper par similarité pour découvrir automatiquement les alignements.

**Pipeline** :

```
Ontologie A + Ontologie B
    ↓ [Vectorisation BERT]
Espace vectoriel N-D
    ↓ [Clustering Hiérarchique]
Groupes de concepts similaires
    ↓ [Génération Meta-Ontologie]
Alignements découverts automatiquement
```

**Cas d'usage** :

- **DOID-ORDO** : Maladies (DOID vs Orphanet)
- **TaxonomieAnimal** : Animaux (Taxonomie vs autre classement)

**✅ Avantages** :

- Totalement automatique (0 données d'entraînement)
- Découverte de patterns cachés
- Très rapide

**❌ Inconvénients** :

- Hiérarchie perdue (ontologie résultante "plate")
- Sensible au seuil de distance
- Alignements N-to-N (pas 1-to-1)

**📊 Résultats** : Clusters identifiés, meta-ontologie générée

---

### 3️⃣ **`Bertmap/`** - Approche BERTMap

**📄 Documentation** : [Bertmap/DOCUMENTATION_TECHNIQUE.md](Bertmap/DOCUMENTATION_TECHNIQUE.md)

**Concept** : Utiliser l'outil BERTMap qui applique BERT directement sur les labels pour trouver correspondances sémantiques.

**Pipeline** :

```
Ontologies OWL
    ↓ [BERTMap Pipeline]
Extraction labels/descriptions
    ↓ [BERT Encoding]
Similarité cosinus
    ↓ [Seuillage]
Alignements (1-to-1 ou N-to-1)
```

**Cas d'usage** :

- **anatomy-dataset** : Anatomie souris vs humain

**✅ Avantages** :

- Rapide, pas d'entraînement
- Hiérarchie partiellement préservée
- Relations de subsumption supportées

**❌ Inconvénients** :

- Basé sur labels (ignorant descriptions profondes)
- Outil externe (DeepOnto)
- Moins flexible que vectoriel

**📊 Résultats** : Mappings TSV/RDF

---

### 4️⃣ **`Vectoriel-Best/`** - Approche Vectorielle Optimisée ⭐

**📄 Documentation** : [Vectoriel-Best/DOCUMENTATION_TECHNIQUE.md](Vectoriel-Best/DOCUMENTATION_TECHNIQUE.md)

**Concept** : Vectoriser sémantiquement et chercher via MongoDB Vector Search (approche retenue pour la pipeline finale).

**Pipeline** :

```
Ontologies JSON
    ↓ [Mapping → CSV]
Extraction attributs riches
    ↓ [BERT Embedding]
MongoDB Vector Search
    ↓ [Recherche Vectorielle Hiérarchique]
Alignements avec scores
    ↓ [Fusion Intelligente]
Ontologie Fusionnée (OWL/JSON)
```

**✅ Avantages** :

- Sémantique la plus riche (descriptions complètes)
- Scalabilité maximale (millions de vecteurs)
- Contrôle granulaire (seuils, TOP-K)
- Base de la pipeline finale

**❌ Inconvénients** :

- Nécessite MongoDB Atlas (coûteux)
- Configuration plus complexe
- Modèle BERT le plus rapide = moins précis

**📊 Résultats** : alignment_results.json, merged_ontology.\*

---

### 5️⃣ **`TP-Explo/`** - Travaux Pratiques et Prototypes

**Concept** : Expériences académiques et prototypes de test.

**Contenu** :

- **TP INSA Rouen** : Travaux académiques structurés
  - Formats OWL et JSON
  - Notebooks d'exploration
- **TP Perso** : Expériences personnelles
  - Tests de conversion
  - Gestion des synonymes

**Rôle** : Base exploratoire, non documentée formellement.

---

## 🎯 Comparaison des Approches

| Critère                  | Classification       | Clustering      | BERTMap            | Vectoriel-Best        |
| ------------------------ | -------------------- | --------------- | ------------------ | --------------------- |
| **Type**                 | Supervisé            | Non-supervisé   | Semi-supervisé     | Non-supervisé         |
| **Données entraînement** | Ontologie A complète | Aucune          | Aucune             | Aucune                |
| **Vectorisation**        | BERT                 | BERT            | BERT labels        | BERT rich_text        |
| **Matching**             | Probabilités classe  | Groupes         | Similarité directe | Recherche vectorielle |
| **Hiérarchie**           | ❌ Perdue            | ❌ Perdue       | ✅ Partiellement   | ✅ Validée            |
| **Vitesse**              | ⚡ Lente             | ⚡⚡ Rapide     | ⚡⚡ Rapide        | ⚡⚡ Rapide           |
| **Exactitude**           | ⭐⭐⭐⭐⭐           | ⭐⭐⭐          | ⭐⭐⭐             | ⭐⭐⭐⭐              |
| **Scalabilité**          | Moyenne              | Bonne           | Bonne              | Excellente            |
| **Infrastructure**       | CPU OK               | CPU OK          | CPU OK             | MongoDB Atlas         |
| **Complexity**           | Moyenne              | Basse           | Basse              | Moyenne               |
| **Production**           | ✅ Possible          | ⚠️ Exploratoire | ✅ Possible        | ✅✅ Recommandé       |

---

## 🚀 Flux de Décision : Quelle Approche Choisir ?

```
Avez-vous ontologie A complète et étiquetée ?
│
├─ OUI → Classification (⭐⭐⭐⭐⭐ exactitude, mais coûteux)
│
└─ NON →
    │
    ├─ Besoin vitesse maximale & découverte ?
    │  └─→ Clustering (⚡⚡ rapide, automatique)
    │
    ├─ Besoin hiérarchie préservée ?
    │  └─→ BERTMap (✅ conserve structure)
    │
    └─ Besoin exactitude & scalabilité ?
       └─→ Vectoriel-Best (⭐⭐⭐⭐ optimal)
```

---

## 📊 Résumé des Résultats

### Classification

- **Modèle** : Random Forest 200 arbres
- **Données entraînement** : 290 exemples (58 × 5 augmentation)
- **Résultats** : `classification/Results/`
  - Classes mappées : A → B
  - Probabilités : [0.0, 1.0]
  - Rapport détaillé

### Clustering

- **DOID-ORDO** : Maladies
  - Clusters découverts
  - Métadonnées d'alignement
- **TaxonomieAnimal** : Animaux
  - Structure de clustering
  - Analyse de couverture

### BERTMap

- **Anatomy** : Souris ↔ Humain
  - Mappings TSV
  - Alignements OWL
  - Relations subsumption

### Vectoriel-Best

- **Alignements JSON** : Scores de similarité
- **Ontologie fusionnée** : OWL + JSON
- **Validation hiérarchique** : Parents/enfants
- **Base pour pipeline finale** ✅

---

## 🔍 Recommandation Finale

**Pour la production** → **Vectoriel-Best** ⭐⭐⭐⭐⭐

**Raisons** :

1. Meilleur équilibre exactitude/scalabilité
2. Sémantique riche (descriptions complètes)
3. Base de la pipeline implémentée
4. MongoDB scalable pour millions de concepts
5. Intégrable avec RAG et GraphDB
6. Résultats reproductibles et explicables

**Autres approches comme alternatives** :

- **Classification** : Si benchmarks montrent besoin exceptionnelle précision
- **Clustering** : Pour exploration/découverte
- **BERTMap** : Alternative légère sans MongoDB

---

## 📚 Lectures Supplémentaires

Pour chaque approche, voir la documentation dédiée :

1. **Classification** → [classification/DOCUMENTATION_TECHNIQUE.md](classification/DOCUMENTATION_TECHNIQUE.md)
   - Modèles supervisés
   - Feature engineering
   - Augmentation de données

2. **Clustering** → [Clustering/DOCUMENTATION_TECHNIQUE.md](Clustering/DOCUMENTATION_TECHNIQUE.md)
   - Clustering hiérarchique
   - Seuillage de distance
   - Meta-ontologies

3. **BERTMap** → [Bertmap/DOCUMENTATION_TECHNIQUE.md](Bertmap/DOCUMENTATION_TECHNIQUE.md)
   - DeepOnto pipeline
   - Relations SKOS/OWL
   - Multilingue

4. **Vectoriel-Best** → [Vectoriel-Best/DOCUMENTATION_TECHNIQUE.md](Vectoriel-Best/DOCUMENTATION_TECHNIQUE.md)
   - Recherche vectorielle
   - MongoDB Atlas
   - Parcours hiérarchique

---

## 🔗 Intégration avec Pipeline Finale

La **pipeline finale** (voir `/pipeline/` et `/rag/`) est basée sur **Vectoriel-Best** :

```
Exploration/Vectoriel-Best/
  Pipeline/vectorize_ontology.py
  Pipeline/semantic_matching.py
  Result/merged_ontology.*
              ↓
         (Raffiné & Production)
              ↓
/pipeline/
  vectorize_ontology.py
  semantic_matching.py
  mapping_ontologie.py
              ↓
/alignement/
  scripts/align_ontology.py
              ↓
/rag/
  rag_agent.py
  streamlit_app.py
```

**Evolution** : De l'exploration vers l'implémentation production avec RAG et GraphDB.

---

## 📞 Questions Fréquentes

**Q: Laquelle est la meilleure ?**
A: Vectoriel-Best pour production, Classification si données d'entraînement disponibles.

**Q: Puis-je combiner plusieurs approches ?**
A: Oui ! Ensemble methods (vote) sur alignements des différentes approches.

**Q: Combien coûte MongoDB Atlas Vector Search ?**
A: ~$0.20 par million de requêtes + stockage documents.

**Q: Comment améliorer les résultats ?**
A: Fine-tuner BERT sur domaine spécifique, ajouter validation manuelle, utiliser descriptions plus riches.

**Q: Puis-je faire sans MongoDB ?**
A: Oui, utiliser BERTMap ou Clustering (moins scalable).
