TP Perso Victor — Expérimentations personnelles

Fichiers présents
-----------------
- `First test.ipynb` : notebook d'exploration (code de test et démonstration).
- `synonyms.csv` : fichier CSV utilisé pour les tests de mapping / enrichissement.

Description du notebook `First test.ipynb`
-----------------------------------------
Ce notebook est un TP inventé pour tester la détection et la gestion de synonymie entre deux "ontologies" (ou entre un petit vocabulaire local et des synonymes externes). Résumé des étapes et du flux de données :

Objectif
- Expérimenter l'enrichissement automatique d'un petit graphe RDF avec des synonymes externes et des candidats détectés automatiquement (TF-IDF + similarité cosinus), puis annoter ces candidats avec `skos:altLabel`.

Étapes principales
1. Visualisation
   - Définition d'une fonction `visualiser_ontologie(g, titre)` qui transforme un `rdflib.Graph` en un graphe `networkx` et affiche une visualisation simple (noeuds = sujets/objets, arêtes étiquetées par le prédicat).
2. Création d'une mini-ontologie
   - Construction d'un petit graphe RDF avec quelques molécules (`Aspirin`, `Paracetamol`, `Ibuprofen`) et ajout de labels RDFS.
3. Enrichissement avec synonymes externes
   - Lecture de `synonyms.csv` et ajout des labels supplémentaires (triples `RDFS.label`) pour les paires (molecule, synonym).
4. Détection automatique de synonymes candidats
   - Définition d'une liste `unknown_terms` (exemples lus dans la littérature : `ASA`, `Acetaminophen`, `Advil`, `Vitamin C`).
   - Calcul de TF-IDF sur les labels connus + termes inconnus et calcul des similarités cosinus pour proposer le meilleur candidat pour chaque terme inconnu.
5. Enrichissement automatique
   - Pour les candidats dont le score dépasse un seuil (0.3 dans le notebook), ajout d'un triple `SKOS.altLabel` liant le concept connu au candidat détecté.

Entrées / sorties
- Entrées : `synonyms.csv`, listes internes (`molecules`, `unknown_terms`).
- Sorties : graphe RDF enrichi affiché et visualisé. Le notebook ne sérialise pas obligatoirement le graphe sur disque, mais il est trivial d'ajouter `g.serialize('famille.owl', format='xml')` pour exporter en RDF/XML.

Paramètres et recommandations
- Seuil de similarité : 0.3 (arbitraire). Ajuster selon la qualité et la nature des données.
- Prétraitement recommandé : normaliser les labels (minuscules, supprimer ponctuation), tokenisation, suppression de stopwords avant TF-IDF.
- Alternatives : embeddings sémantiques (word2vec, SBERT) ou fuzzy matching pour gérer abréviations et acronymes (p.ex. `ASA` → `Aspirin`).

Suggestions d'améliorations
- Ajouter un export automatique du graphe final : pour pouvoir importer directement dans WebProtégé.
- Documenter les colonnes attendues dans `synonyms.csv` (par ex. `molecule,synonym`).
- Ajouter des tests unitaires basiques pour la fonction de détection (p.ex. cas où le meilleur score est en dessous du seuil).
