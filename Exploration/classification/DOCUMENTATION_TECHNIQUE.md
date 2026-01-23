# Documentation Technique - Modèle de Classification

## 🎯 Vue d'ensemble

Ce pipeline utilise un **modèle de classification supervisé** pour mapper les classes de l'ontologie B sur les classes de l'ontologie A. Contrairement à une approche par similarité sémantique pure, ce système entraîne réellement un classificateur qui apprend à reconnaître les catégories de l'ontologie A.

## 🏗️ Architecture du Modèle

### 1. Vectorisation des Attributs (Feature Engineering)

Chaque classe d'ontologie est représentée par ses attributs textuels :

- **Label** : Nom principal de la classe
- **Synonymes** (altLabel) : Noms alternatifs
- **Commentaires** : Descriptions détaillées
- **Informations taxonomiques** : Ordre, famille, espèce, etc.

Ces attributs sont concaténés puis vectorisés en **embeddings sémantiques** (vecteurs de 384 dimensions) via le modèle Sentence-BERT `all-MiniLM-L6-v2`.

### 2. Augmentation de Données

**Problème** : Avec une seule instance par classe dans l'ontologie A, un classificateur standard ne peut pas s'entraîner efficacement.

**Solution** : Augmentation de données en créant 5 variations de chaque classe :

1. Description complète (baseline)
2. Label + commentaires principaux
3. Label + synonymes
4. Label + premier synonyme
5. Label + première description
6. Label seul

Cela génère **5× exemples d'entraînement** par classe, améliorant la robustesse.

### 3. Classificateur

**Random Forest** (par défaut) :

- `n_estimators=200` : 200 arbres de décision
- `class_weight='balanced'` : Compense les déséquilibres de classes
- Retourne des probabilités calibrées via `predict_proba()`

**Avantages** :

- Robuste au surapprentissage avec peu de données
- Probabilités bien calibrées
- Capture les relations non-linéaires
- Gère bien les features de haute dimension

**Alternative** : Neural Network (MLP)

- 3 couches cachées (256, 128, 64 neurones)
- Activation ReLU
- Early stopping pour éviter l'overfitting

## 📊 Processus de Classification

### Phase 1 : Entraînement

```
Ontologie A (58 classes)
    ↓
Extraction des attributs
    ↓
Vectorisation (embeddings)
    ↓
Augmentation de données (×5)
    ↓
290 exemples d'entraînement
    ↓
Entraînement Random Forest
    ↓
Modèle entraîné
```

### Phase 2 : Prédiction

```
Classe B (ex: "TigerSpecies")
    ↓
Extraction des attributs
    ↓
Vectorisation (embedding)
    ↓
Prédiction par le modèle
    ↓
Probabilités pour chaque classe A
    ↓
Top-5 prédictions avec probabilités
```

## 🔢 Interprétation des Probabilités

Les probabilités retournées par `predict_proba()` représentent :

**Pour Random Forest** :

- Proportion d'arbres qui votent pour chaque classe
- Exemple : P(Tiger) = 0.85 → 85% des arbres ont classifié l'entrée comme "Tiger"

**Caractéristiques** :

- Somme des probabilités = 1.0
- Valeurs entre 0 et 1
- Plus calibrées que les scores de similarité cosinus

## 📈 Comparaison avec l'Approche par Similarité

| Aspect               | Similarité Sémantique   | Classification Supervisée   |
| -------------------- | ----------------------- | --------------------------- |
| **Approche**         | Calcul de distances     | Apprentissage de patterns   |
| **Entraînement**     | Non requis              | Requis sur ontologie A      |
| **Probabilités**     | Softmax sur similarités | predict_proba du modèle     |
| **Robustesse**       | Sensible aux variations | Plus robuste (augmentation) |
| **Interprétabilité** | Distance dans l'espace  | Vote d'arbres/neurones      |
| **Performance**      | Rapide                  | Plus lent (entraînement)    |

## 🎓 Avantages du Modèle Supervisé

1. **Apprentissage de patterns spécifiques** : Le modèle apprend les caractéristiques distinctives de chaque classe de A

2. **Robustesse aux variations** : Grâce à l'augmentation, le modèle gère mieux les descriptions incomplètes ou alternatives

3. **Probabilités calibrées** : Les probabilités reflètent la confiance réelle du modèle

4. **Extensibilité** : Facile d'ajouter de nouvelles classes en ré-entraînant

## ⚠️ Limitations

1. **Dépendance aux données** : Nécessite des exemples de qualité pour l'ontologie A

2. **Temps d'entraînement** : Requiert une phase d'entraînement (quelques secondes à minutes)

3. **Généralisaton limitée** : Peut mal performer sur des classes très différentes de A

4. **One-shot learning** : Avec une seule instance réelle par classe, l'augmentation est cruciale

## 🔧 Optimisation

### Améliorer les Performances

1. **Augmenter les variations** : Créer plus de 5 augmentations par classe
2. **Utiliser un meilleur embedding** : `all-mpnet-base-v2` (768 dimensions)
3. **Tuning des hyperparamètres** : Grid search sur Random Forest
4. **Ensembling** : Combiner Random Forest + Neural Network

### Adaptation à d'Autres Domaines

Le pipeline est générique et s'adapte à n'importe quelles ontologies :

- Domaine médical (maladies, médicaments)
- Domaine scientifique (concepts, théories)
- Taxonomies diverses

Il suffit de fournir les fichiers OWL avec la même structure.

## 📚 Exemple Concret

**Input** : Classe B "FastCheetah"

- Label: "Fast Cheetah"
- Synonyms: ["Cheetah", "Acinonyx jubatus", "Sprint Cat"]
- Description: "Speediest terrestrial animal..."

**Vectorisation** :

```
[0.12, -0.45, 0.89, ..., 0.34]  # 384 dimensions
```

**Prédiction du modèle** :

```
Cheetah:  0.92  (92%)  ✓ Best match
Tiger:    0.04  (4%)
Leopard:  0.02  (2%)
Lion:     0.01  (1%)
Cat:      0.01  (1%)
```

**Résultat** : Mapping vers "Cheetah" avec 92% de confiance

## 🚀 Performance

Sur les ontologies animales (58 classes A, 60 classes B) :

- **Temps d'entraînement** : ~5-10 secondes
- **Temps de prédiction** : ~0.1 seconde par classe
- **Précision attendue** : >85% pour les correspondances directes

## 📖 Références

- **Sentence-BERT** : [Reimers & Gurevych, 2019](https://arxiv.org/abs/1908.10084)
- **Random Forest** : [Breiman, 2001](https://link.springer.com/article/10.1023/A:1010933404324)
- **OWL Ontologies** : [W3C OWL 2](https://www.w3.org/TR/owl2-overview/)
