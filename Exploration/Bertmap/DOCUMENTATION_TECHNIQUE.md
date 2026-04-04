# Documentation Technique - Alignement BERTMap

## 🎯 Vue d'ensemble

Ce dossier explore **BERTMap**, un outil d'alignement d'ontologies basé sur les transformers BERT. BERTMap est une approche directe d'alignement sémantique qui utilise les embeddings BERT pour identifier les correspondances entre classes de deux ontologies.

**Approche** : Alignement bilingue à partir des labels et descriptions, sans entraînement de classificateur.

---

## 🏗️ Architecture de BERTMap

### 1. Qu'est-ce que BERTMap ?

BERTMap (BERT-based Ontology Matching Pipeline) est une pipeline d'alignement développée par le projet DeepOnto. Elle combine :

- **Transformers BERT** : Pour générer des embeddings contextuels des labels
- **Recherche vectorielle** : Pour trouver les pairs sémantiquement proches
- **Heuristiques d'alignement** : Pour raffiner les résultats

### 2. Processus de BERTMap

```
Ontologie A (src)          Ontologie B (tgt)
    ↓                           ↓
Extraction des labels      Extraction des labels
    ↓                           ↓
Tokenization & BERT encoding
    ↓
Recherche par similarité cosinus
    ↓
Filtrage par seuil de confiance
    ↓
Alignements (mappings)
    ↓
Format TSV/RDF
```

### 3. Types d'Alignements

BERTMap produit 4 types d'alignements :

| Type            | Relation              | Signification                             |
| --------------- | --------------------- | ----------------------------------------- |
| **equivalence** | `owl:equivalentClass` | Classes identiques                        |
| **subsumption** | `rdfs:subClassOf`     | Une classe subsume l'autre                |
| **related**     | `skos:relatedMatch`   | Classes connexes (sémantiquement proches) |
| **close match** | `skos:closeMatch`     | Correspondances proches mais non exactes  |

---

## 📊 Processus Détaillé

### Phase 1 : Préparation

1. **Chargement des ontologies** (format OWL/RDF)

   ```python
   from deeponto.onto import Ontology
   src_onto = Ontology("source.owl")
   tgt_onto = Ontology("target.owl")
   ```

2. **Extraction des informations**
   - `rdfs:label` : Label principal
   - `rdfs:comment` : Descriptions
   - `skos:altLabel` : Labels alternatifs
   - Hiérarchie `rdfs:subClassOf`

### Phase 2 : Vectorisation

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('bert-base-uncased')

# Encodage des labels et descriptions
embeddings_src = model.encode(labels_source)
embeddings_tgt = model.encode(labels_target)
```

**Modèles BERT Disponibles** :

- `bert-base-uncased` : Généraliste (anglais)
- `distilbert-base-uncased` : Plus léger et rapide
- `all-MiniLM-L6-v2` : Compact et efficace

### Phase 3 : Alignement

```python
from deeponto.align.bertmap import BERTMapPipeline

config = BERTMapPipeline.load_bertmap_config()
bertmap = BERTMapPipeline(src_onto, tgt_onto, config)

# Sauvegarde avec seuil
bertmap.save_mappings("mappings.tsv", threshold=0.6)
```

**Paramètres clés** :

- **threshold** : Score minimum d'alignement (0.0 à 1.0)
- **top_k** : Nombre maximum d'alignements par classe
- **include_subsumption** : Activer les relations hiérarchiques

### Phase 4 : Résultats

Format de sortie TSV :

```
source_class     target_class     relation_type     confidence_score
MouseAnatomy:001 HumanAnatomy:042 equivalentClass   0.95
MouseAnatomy:005 HumanAnatomy:123 subsumption       0.87
```

---

## ✅ Avantages de BERTMap

| Avantage         | Détail                                       |
| ---------------- | -------------------------------------------- |
| **Rapide**       | Pas d'entraînement, inférence directe        |
| **Flexible**     | Fonctionne avec n'importe quelles ontologies |
| **Transférable** | Modèles BERT pré-entraînés sur corpus larges |
| **Multilingue**  | Versions BERT pour plusieurs langues         |
| **Hiérarchie**   | Préserve les relations subsumption           |

---

## ❌ Limitations

| Limitation                  | Détail                                                          |
| --------------------------- | --------------------------------------------------------------- |
| **Pas de contexte local**   | Alignement basé sur labels, ignore la hiérarchie                |
| **Dépendance linguistique** | Nécessite labels de qualité en langue commune                   |
| **Pas d'entraînement**      | Ne peut pas apprendre de patterns spécifiques au domaine        |
| **Coûteux en mémoire**      | Les gros transformers (BERT complet) consomment beaucoup de RAM |
| **Pas de validation**       | Alignements non vérifiés contre des références gold-standard    |

---

## 🔬 Cas d'Usage : Anatomy Dataset

Le dossier `anatomy-dataset/` teste BERTMap sur un cas d'usage classique :

- **Ontologie source** : Mouse (Souris) - Anatomie
- **Ontologie cible** : Human (Humain) - Anatomie
- **Challenge** : Trouver les structures anatomiques équivalentes

### Résultats Attendus

Les structures anatomiques mainmaliennes partagent des homologies :

```
Mouse:Liver        → Human:Liver        (équivalent)
Mouse:Kidney       → Human:Kidney       (équivalent)
Mouse:FrontalLobe → Human:FrontalLobe   (équivalent)
```

---

## 🚀 Comparaison avec d'autres Approches

| Approche               | Vitesse     | Exactitude           | Complexité | Données d'entraînement |
| ---------------------- | ----------- | -------------------- | ---------- | ---------------------- |
| **BERTMap** (ici)      | ⚡⚡ Rapide | ⭐⭐⭐ Bon           | Basse      | 0 (pré-entraîné)       |
| **Classification**     | ⚡ Moyen    | ⭐⭐⭐⭐ Excellent   | Moyenne    | Ontologie A complète   |
| **Clustering**         | ⚡⚡ Rapide | ⭐⭐⭐ Bon           | Basse      | Aucune                 |
| **Matching Vectoriel** | ⚡ Moyen    | ⭐⭐⭐⭐⭐ Excellent | Moyenne    | MongoDB + MongoDB      |

---

## 📝 Format de Sortie

### TSV (Tab-Separated Values)

```
source_id          target_id           relation            confidence
http://...#Mouse1  http://...#Human1   equivalentClass     0.94
```

### RDF/OWL

```xml
<rdf:Description rdf:about="http://alignment#map1">
  <oaei:hasSource rdf:resource="http://source#class1"/>
  <oaei:hasTarget rdf:resource="http://target#class2"/>
  <oaei:relation rdf:resource="http://owl#equivalentClass"/>
  <oaei:confidence>0.94</oaei:confidence>
</rdf:Description>
```

---

## 🔧 Installation et Dépendances

```bash
# Installation de DeepOnto
pip install deeponto

# Dépendances
# - torch / tensorflow
# - transformers
# - owlready2
# - rdflib
```

---

## 📚 Ressources Complémentaires

- **DeepOnto** : https://github.com/KRR-Oxford/DeepOnto
- **BERT** : Devlin et al. (2018)
- **BERTMap Paper** : DeepOnto documentation
- **Benchmark OAEI** : http://oaei.ontologymatching.org/

---

## 💡 Quand Utiliser BERTMap ?

✅ **Bon pour** :

- Alignement rapide pour première approximation
- Ontologies avec labels de qualité
- Cas multilingues (avec BERT multilingue)
- Peu d'expertise disponible

❌ **Mauvais pour** :

- Ontologies avec labels peu informatifs
- Domaines très spécialisés
- Besoin de haute précision
- Alignements complexes hiérarchiques
