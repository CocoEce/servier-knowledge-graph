# 📊 Build_Data - Récupération de Données Médicales pour Knowledge Graph

## 🎯 Objectif du Projet

Ce répertoire contient trois scripts de collecte de données médicales depuis des sources d'ontologies majeures :
- **ChEBI** (Chemical Entities of Biological Interest)
- **PubChem** (Base de données chimique du NCBI)
- **Wikidata** (Base de connaissances collaborative)

### Vision Globale

L'objectif principal est de **construire un knowledge graph médical unifié** en :
1. Récupérant des données structurées sur des molécules pharmaceutiques, médicaments et composés médicaux
2. Préparant ces données pour un **système de Machine Learning** qui alignera automatiquement les synonymes entre sources
3. Fusionnant les trois ontologies en un graphe de connaissances cohérent et interrogeable

---

## 🧪 Les Trois Scripts

### 1. **fetch_chebi.py** - ChEBI API

```bash
python fetch_chebi.py
```

**Source** : [ChEBI](https://www.ebi.ac.uk/chebi/)  
**API** : REST API officielle 2.0  
**Nombre d'entités** : ~50 molécules pharmaceutiques

#### Données récupérées
- **Identifiants** : ChEBI ID, URI
- **Labels** : Nom principal (chebiAsciiName)
- **Synonymes** : Liste complète des synonymes (crucial pour ML)
- **Propriétés chimiques** :
  - Formule moléculaire
  - Masse moléculaire
  - InChI / InChI Key (identifiants chimiques standardisés)
  - SMILES (représentation structurelle)
- **Descriptions** : Définitions textuelles

#### Exemples de molécules
Aspirine, Paracétamol, Ibuprofène, Metformine, Atorvastatine, Amoxicilline, Dopamine, Sérotonine, Morphine, Codéine, Warfarine, Pénicilline, Fluoxétine, Oméprazole, Simvastatine, Diazépam, Phénytoïne, Halopéridol, etc.

#### Structure JSON retournée
```json
{
  "source": "ChEBI",
  "fetch_date": "2026-01-14 10:30:00",
  "total_entities": 50,
  "entities": [
    {
      "id": "CHEBI:15365",
      "uri": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15365",
      "name": "aspirin",
      "synonyms": ["acetylsalicylic acid", "2-acetoxybenzoic acid", "ASA", ...],
      "definition": "A member of the class of benzoic acids...",
      "chemical_properties": {
        "formula": "C9H8O4",
        "mass": "180.159",
        "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
      }
    }
  ]
}
```

---

### 2. **fetch_pubchem.py** - PubChem REST API

```bash
python fetch_pubchem.py
```

**Source** : [PubChem](https://pubchem.ncbi.nlm.nih.gov/)  
**API** : REST API (PUG REST)  
**Nombre d'entités** : ~50 composés chimiques

#### Données récupérées
- **Identifiants** : CID (Compound ID), URI
- **Labels** : Nom principal (premier synonyme)
- **Synonymes** : Liste étendue (jusqu'à 20 synonymes par composé)
- **Propriétés chimiques** :
  - Formule moléculaire
  - Masse moléculaire
  - InChI / InChI Key
  
#### Spécificités
- **Deux appels API par composé** :
  1. Endpoint `/property/` pour les propriétés chimiques
  2. Endpoint `/synonyms/` pour la liste complète des synonymes
- Pause de 0.2s entre les requêtes pour respecter les limites de l'API

#### Exemples de CIDs récupérés
- CID 2244 (Aspirine)
- CID 1983 (Paracétamol)
- CID 3672 (Ibuprofène)
- CID 4091 (Metformine)
- etc.

#### Structure JSON retournée
```json
{
  "source": "PubChem",
  "fetch_date": "2026-01-14 10:35:00",
  "total_entities": 50,
  "entities": [
    {
      "id": "CID:2244",
      "uri": "https://pubchem.ncbi.nlm.nih.gov/compound/2244",
      "name": "Aspirin",
      "synonyms": ["acetylsalicylic acid", "2-Acetoxybenzoic acid", "ASA", ...],
      "chemical_properties": {
        "formula": "C9H8O4",
        "mass": "180.16",
        "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)"
      }
    }
  ]
}
```

---

### 3. **fetch_wikidata.py** - Wikidata SPARQL

```bash
python fetch_wikidata.py
```

**Source** : [Wikidata](https://www.wikidata.org/)  
**API** : SPARQL Endpoint  
**Nombre d'entités** : 50 composés chimiques

#### Données récupérées
- **Identifiants** : Q-ID (Wikidata ID), URI
- **Labels** : Nom principal (rdfs:label)
- **Synonymes** : Tous les altLabel en anglais (regroupés)
- **Descriptions** : Description textuelle
- **Propriétés chimiques** :
  - P274 (formule chimique)
  - P2067 (masse moléculaire)
  - P233 (InChI)
  - P235 (InChI Key)
  - P2017 (SMILES)

#### Requête SPARQL
La requête utilise :
- `wdt:P31/wdt:P279*` pour récupérer les instances et sous-classes de composés chimiques
- `GROUP_CONCAT` pour agréger tous les synonymes en une seule ligne
- Filtre sur la présence d'au moins une propriété chimique (formule, InChI Key ou masse)

#### Structure JSON retournée
```json
{
  "source": "Wikidata",
  "fetch_date": "2026-01-14 10:40:00",
  "total_entities": 50,
  "entities": [
    {
      "id": "Q18216",
      "uri": "http://www.wikidata.org/entity/Q18216",
      "name": "aspirin",
      "synonyms": ["acetylsalicylic acid", "ASA", "2-acetoxybenzoic acid", ...],
      "description": "medication to reduce pain, fever and inflammation",
      "chemical_properties": {
        "formula": "C9H8O4",
        "mass": "180.158",
        "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
      }
    }
  ]
}
```

---

## 🤖 Préparation pour le Machine Learning

### Pourquoi ces données ?

Les trois scripts sont conçus pour **faciliter l'alignement automatique des entités** entre les sources grâce au ML :

#### 1. **Synonymes multiples**
- Chaque entité possède une **liste de synonymes** (parfois 10-20 par molécule)
- Ces synonymes permettront d'entraîner un modèle de **similarité sémantique** pour détecter les correspondances inter-sources
- Exemple : "aspirin" (ChEBI) ≈ "Aspirin" (PubChem) ≈ "aspirin" (Wikidata)

#### 2. **Propriétés chimiques pour validation**
- **InChI Key** : Identifiant chimique unique et standardisé
  - Si deux entités partagent le même InChI Key, c'est **la même molécule**
  - Utile pour créer des **ground truth** pour le modèle ML
- **Formule moléculaire** : Validation secondaire
- **Masse moléculaire** : Filtre de proximité

#### 3. **Structure JSON uniforme**
Toutes les sources retournent le même format :
```json
{
  "id": "...",
  "uri": "...",
  "name": "...",
  "synonyms": [...],
  "chemical_properties": {
    "formula": "...",
    "mass": "...",
    "inchi_key": "...",
    ...
  }
}
```

Cela facilite :
- Le **chargement dans un DataFrame pandas**
- L'entraînement de modèles de **NLP** (BERT, sentence transformers)
- La création d'un **graphe de connaissances fusionné**

---

## 📈 Pipeline ML Envisagé

### Étape 1 : Collecte des données
```bash
python fetch_chebi.py > chebi_data.json
python fetch_pubchem.py > pubchem_data.json
python fetch_wikidata.py > wikidata_data.json
```

### Étape 2 : Prétraitement
- Charger les 3 fichiers JSON
- Normaliser les synonymes (lowercase, suppression de la ponctuation)
- Créer des paires candidates basées sur :
  - Similarité de chaînes (Levenshtein, Jaro-Winkler)
  - Correspondance exacte des InChI Key (pour le ground truth)

### Étape 3 : Entraînement du modèle
- **Modèle suggéré** : Sentence Transformers (SBERT) fine-tuné
- **Données d'entraînement** :
  - Positives : Paires avec même InChI Key
  - Négatives : Paires avec InChI Key différents mais synonymes proches
- **Métrique** : Similarité cosinus des embeddings

### Étape 4 : Alignement automatique
- Pour chaque entité ChEBI :
  - Trouver les top-K candidats PubChem et Wikidata
  - Calculer un score de confiance
  - Valider avec les propriétés chimiques
  
### Étape 5 : Construction du graphe unifié
- Fusionner les entités alignées avec `owl:sameAs`
- Créer un graphe RDF avec GraphDB

---

## 🔧 Installation et Utilisation

### Prérequis

```bash
pip install requests SPARQLWrapper
```

### Exécution des scripts

1. **Récupérer les données ChEBI** :
```bash
cd /path/to/Build_Data
python fetch_chebi.py
```

2. **Récupérer les données PubChem** :
```bash
python fetch_pubchem.py
```

3. **Récupérer les données Wikidata** :
```bash
python fetch_wikidata.py
```

### Options de sauvegarde

Chaque script contient du code commenté pour sauvegarder en JSON :
```python
# Décommenter dans le script
with open("chebi_medical_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## 📊 Statistiques Attendues

| Source    | Entités | Synonymes moy. | Prop. chimiques |
|-----------|---------|----------------|-----------------|
| ChEBI     | ~50     | 8-15           | 5-6             |
| PubChem   | ~50     | 10-20          | 4-5             |
| Wikidata  | 50      | 5-12           | 3-5             |

**Total** : ~150 entités (avec chevauchements attendus de 60-80%)

---

## 🔗 Alignement Inter-Sources

### Stratégies de matching

1. **Exact Match sur InChI Key** (100% fiable)
   ```python
   if chebi_entity["inchi_key"] == pubchem_entity["inchi_key"]:
       owl:sameAs
   ```

2. **Similarité de synonymes** (ML)
   - Calculer la similarité entre tous les synonymes
   - Seuil de confiance : > 0.85

3. **Validation par propriétés**
   - Formule identique
   - Masse moléculaire proche (± 0.1 g/mol)

### Exemple d'alignement
```turtle
# ChEBI
chebi:15365 a chebi:ChemicalEntity ;
    rdfs:label "aspirin" ;
    skos:altLabel "acetylsalicylic acid" ;
    chebi:inchiKey "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" .

# PubChem
pubchem:2244 a pubchem:ChemicalCompound ;
    rdfs:label "Aspirin" ;
    skos:altLabel "acetylsalicylic acid" ;
    pubchem:inchiKey "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" .

# Wikidata
wd:Q18216 a wikibase:Item ;
    rdfs:label "aspirin" ;
    skos:altLabel "acetylsalicylic acid" ;
    wdt:P235 "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" .

# Alignement ML
chebi:15365 owl:sameAs pubchem:2244 .
chebi:15365 owl:sameAs wd:Q18216 .
pubchem:2244 owl:sameAs wd:Q18216 .
```

---

## 🚀 Prochaines Étapes

1. ✅ **Collecte de données** (scripts actuels)
2. 🔄 **Normalisation** : Script de nettoyage des synonymes
3. 🤖 **ML Pipeline** : Fine-tuning SBERT sur les données médicales
4. 🔗 **Entity Linking** : Génération automatique des triplets `owl:sameAs`
5. 📦 **GraphDB Integration** : Chargement du graphe unifié
6. 🔍 **RAG Agent** : Interrogation du graphe avec SPARQL

---

## �️ Conversion JSON → TTL

### Scripts de conversion

Pour visualiser vos graphes de connaissances, vous pouvez convertir les fichiers JSON en format TTL (Turtle) :

```bash
# Convertir les données ChEBI
python json_to_ttl_chebi.py
# → Génère: chebi_medical_data.ttl

# Convertir les données PubChem
python json_to_ttl_pubchem.py
# → Génère: pubchem_medical_data.ttl

# Convertir les données Wikidata
python json_to_ttl_wikidata.py
# → Génère: wikidata_medical_data.ttl
```

### Utilisation des fichiers TTL

Les fichiers TTL générés peuvent être utilisés avec :

1. **WebVOWL** (déjà dans votre projet `/Git/WebVOWL`)
   ```bash
   # Ouvrir WebVOWL localement
   # Puis charger un fichier .ttl via l'interface
   ```

2. **GraphDB** (pour requêtes SPARQL)
   ```bash
   # Importer dans GraphDB via l'interface web
   # Repository → Import → RDF → Upload
   ```

3. **Protégé** (éditeur d'ontologies)
   - Ouvrir Protégé
   - File → Open → Sélectionner le fichier .ttl

4. **Python RDFLib** (manipulation programmatique)
   ```python
   from rdflib import Graph
   
   g = Graph()
   g.parse("chebi_medical_data.ttl", format="turtle")
   print(f"Triplets: {len(g)}")
   
   # Requête SPARQL
   query = """
   SELECT ?entity ?label WHERE {
       ?entity rdfs:label ?label .
   } LIMIT 10
   """
   for row in g.query(query):
       print(row)
   ```

### Format des fichiers TTL

Les fichiers utilisent les vocabulaires standards :
- **ChEBI** : `chebi:`, `cheminf:` (Chemical Information Ontology)
- **PubChem** : `pubchem:`, `cheminf:`
- **Wikidata** : `wd:`, `wdt:`, `schema:`

Exemple de triplets :
```turtle
chebi:15365
    rdf:type chebi:ChemicalEntity ;
    rdfs:label "acetylsalicylic acid"@en ;
    skos:altLabel "Aspirin"@en ;
    cheminf:CHEMINF_000042 "C9H8O4" ;
    cheminf:CHEMINF_000059 "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" .
```

---

## �📚 Ressources

- [ChEBI API Documentation](https://www.ebi.ac.uk/chebi/webServices.do)
- [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest)
- [Wikidata SPARQL](https://query.wikidata.org/)
- [Sentence Transformers](https://www.sbert.net/)
- [GraphDB](https://graphdb.ontotext.com/)

---

## 🐛 Dépannage

### Erreur API ChEBI
```
⚠️ Erreur pour ChEBI XXXXX: 404
```
→ L'ID n'existe pas ou a été fusionné. Vérifier sur le site ChEBI.

### Timeout Wikidata
```
❌ ERREUR : HTTPError: 408
```
→ La requête SPARQL est trop longue. Réduire la LIMIT ou simplifier la requête.

### Pas de synonymes PubChem
```
Synonymes: 0
```
→ L'endpoint `/synonyms/` peut être temporairement indisponible. Réessayer plus tard.

---

## 📧 Contact

Pour toute question sur ce projet : Projet PFE Servier - ECE Paris

**Date de création** : Janvier 2026  
**Dernière mise à jour** : 14 janvier 2026
