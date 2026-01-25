# Pipeline de Classification d'Ontologies

Ce dossier contient un pipeline complet pour classifier les classes de l'ontologie B sur les classes de l'ontologie A en utilisant un modèle de classification supervisé.

## 📋 Description

Le pipeline effectue les étapes suivantes :

1. **Extraction des classes** : Parse les fichiers OWL et extrait toutes les classes avec leurs métadonnées (labels, commentaires, synonymes)
2. **Entraînement du modèle** : Entraîne un classificateur (Random Forest) sur les classes de l'ontologie A avec augmentation de données
3. **Classification** : Utilise le modèle entraîné pour classifier chaque classe de B et obtenir les probabilités de prédiction
4. **Génération de l'ontologie de mapping** : Crée une nouvelle ontologie OWL contenant les correspondances avec probabilités et niveaux de confiance

## 🎯 Approche

**Modèle de Classification Supervisé** :

- Les classes de l'ontologie A servent de catégories cibles
- Les attributs de chaque classe (labels, synonymes, descriptions) sont vectorisés en embeddings
- Un classificateur Random Forest est entraîné sur ces données avec augmentation
- Pour chaque classe de B, le modèle prédit les probabilités d'appartenance à chaque classe de A

## 🗂️ Structure

```
Pipeline/
├── extract_classes.py              # Extraction des classes depuis OWL
├── classify_ontologies.py          # Classification avec probabilités
├── generate_mapping_ontology.py    # Génération de l'ontologie de mapping
└── run_classification_pipeline.py  # Script principal
```

## 📦 Dépendances

Installez les dépendances nécessaires :

```bash
pip install owlready2 sentence-transformers scikit-learn pandas numpy
```

## 🚀 Utilisation

### Méthode 1: Pipeline complet (recommandé)

Exécutez le pipeline complet en une seule commande :

```bash
cd Exploration/classification
python Pipeline/run_classification_pipeline.py
```

Le pipeline créera automatiquement un dossier `Results/` avec tous les fichiers générés.

### Méthode 2: Étape par étape

#### Étape 1: Extraire les classes

```bash
python Pipeline/extract_classes.py Data/ontologie_animaux_A.owl Results/classes_A.json
python Pipeline/extract_classes.py Data/ontologie_animaux_B.owl Results/classes_B.json
```

#### Étape 2: Classifier

```bash
python Pipeline/classify_ontologies.py \
    Results/classes_A.json \
    Results/classes_B.json \
    Results/mappings.json \
    Results/rapport_classification.txt
```

#### Étape 3: Générer l'ontologie de mapping

```bash
python Pipeline/generate_mapping_ontology.py \
    Results/mappings.json \
    Results/ontologie_mapping.owl
```

## 📊 Fichiers générés

Le pipeline génère les fichiers suivants dans le dossier `Results/` :

- **`classes_A_[timestamp].json`** : Classes extraites de l'ontologie A
- **`classes_B_[timestamp].json`** : Classes extraites de l'ontologie B
- **`mappings_[timestamp].json`** : Résultats de classification avec probabilités
- **`mappings_[timestamp].csv`** : Version CSV pour analyse dans Excel
- **`rapport_classification_[timestamp].txt`** : Rapport détaillé avec toutes les correspondances
- **`ontologie_mapping_[timestamp].owl`** : Ontologie OWL de mapping
- **`ontologie_mapping_[timestamp]_statistics.json`** : Statistiques sur les mappings

## 📈 Interprétation des résultats

### Probabilités de classification

Chaque classe de B est classifiée vers les classes de A avec :

- **Probability** (0-1) : Probabilité réelle du modèle de classification (Random Forest predict_proba)
- **Confidence Level** :
  - `high` : probabilité ≥ 0.7
  - `medium` : 0.4 ≤ probabilité < 0.7
  - `low` : probabilité < 0.4

### Format des mappings

Chaque mapping contient :

```json
{
  "class_b_name": "NomClasseB",
  "class_b_label": "Label Classe B",
  "top_matches": [
    {
      "class_a_name": "NomClasseA",
      "class_a_label": "Label Classe A",
      "probability": 0.87
    }
  ]
}
```

## 🔧 Personnalisation

### Modifier le type de classificateur

Dans `classify_ontologies.py` :

```python
# Types disponibles:
# - 'random_forest' (défaut, robuste, probabilités calibrées)
# - 'neural_net' (plus flexible mais nécessite plus de données)
classifier = OntologyClassifier(classifier_type='random_forest')
```

### Modifier le modèle d'embedding

```python
classifier = OntologyClassifier(
    embedding_model='all-MiniLM-L6-v2',  # Modifier ici
    classifier_type='random_forest'
)
```

Modèles disponibles :

- `all-MiniLM-L6-v2` (défaut, rapide)
- `all-mpnet-base-v2` (plus précis)
- `paraphrase-multilingual-MiniLM-L12-v2` (multilingue)

### Désactiver l'augmentation de données

Dans la méthode `train_model()` :

```python
classifier.train_model(use_augmentation=False)  # Désactiver l'augmentation
```

### Nombre de correspondances (top-k)

Dans `classify_ontologies.py`, méthode `classify()` :

```python
mappings = classifier.classify(top_k=5)  # Modifier ici
```

### Inclure tous les rangs dans l'ontologie

Dans `generate_mapping_ontology.py` :

```python
generator.generate_mappings(mappings, include_all_ranks=True)  # True ou False
```

## 📝 Exemple de sortie

```
CLASSE B: Tiger Species (TigerSpecies)
--------------------------------------------------------------------------------
Top 5 correspondances prédites par le modèle:

  1. Tiger (Tiger)
     Probabilité: 0.8756 (87.56%)

  2. Cheetah (Cheetah)
     Probabilité: 0.0891 (8.91%)

  3. Leopard (Leopard)
     Probabilité: 0.0234 (2.34%)
```

## ⚠️ Notes importantes

1. Le premier lancement télécharge le modèle d'embedding (~80MB)
2. Le temps de traitement dépend du nombre de classes
3. Les résultats sont horodatés pour éviter l'écrasement
4. L'ontologie de mapping utilise le format RDF/XML

## 🐛 Dépannage

### Erreur: "No module named 'owlready2'"

```bash
pip install owlready2
```

### Erreur: "No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### L'ontologie ne se charge pas

Vérifiez que les chemins dans `Data/` sont corrects et que les fichiers OWL sont valides.

## 📚 Références

- [Owlready2](https://owlready2.readthedocs.io/)
- [Sentence-Transformers](https://www.sbert.net/)
- [OWL 2 Web Ontology Language](https://www.w3.org/TR/owl2-overview/)
