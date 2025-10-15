TP INSA Rouen — Ontologie "famille"

But du TP
---------
Ce TP (exercice d'INSA Rouen) montre la création simple d'une ontologie OWL représentant des relations familiales (Personne, Sexe, Homme/Femme, Parent, Mère, Père, relations parent/enfant, frère/soeur, etc.) à l'aide de la bibliothèque Python Owlready2. Le notebook `owl.ipynb` contient le code qui crée les classes, instances et relations, effectue un raisonnement (avec HermiT/Pellet via Owlready2) et sauvegarde l'ontologie dans `famille.owl`.

Fichiers importants
-------------------
- `owl.ipynb` : notebook Python qui construit l'ontologie et produit `famille.owl`.
- `famille.owl` : fichier OWL (sérialisé) généré par le notebook (si vous exécutez le notebook). Il peut être importé dans un éditeur OWL comme WebProtégé ou Protégé Desktop.

Comment utiliser
----------------
1) Pré-requis local
- Python 3.8+ recommandé
- Installer les dépendances (par exemple dans un venv) :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install owlready2 networkx matplotlib
```

2) Exécuter le notebook
- Ouvrez `owl.ipynb` (Jupyter / VS Code) et exécutez les cellules. Le fichier `famille.owl` sera créé à la racine du dossier du notebook.

Importer `famille.owl` dans WebProtégé (https://webprotege.stanford.edu)
-------------------------------------------------------------------
Voici les étapes pour charger et visualiser l'ontologie dans WebProtégé :

1. Ouvrir WebProtégé
   - Allez sur https://webprotege.stanford.edu
   - Connectez-vous (ou créez un compte gratuit) si vous souhaitez sauvegarder le projet en ligne.

2. Créer un nouveau projet
   - Cliquez sur "Create project" (ou "New Project").
   - Donnez un nom (par ex. "TP INSA Rouen - Famille") et, si demandé, choisissez "OWL 2 DL" comme type.

3. Importer le fichier OWL
   - Après la création du projet, ouvrez-le.
   - Dans le menu latéral, cliquez sur l'icône d'engrenage / settings ou sur le menu principal du projet, puis choisissez "Import" -> "Upload ontology file" (ou similiaire selon la version).
   - Sélectionnez le fichier `famille.owl` depuis votre système local et validez l'import.
   - WebProtégé affichera ensuite les classes, propriétés et individus importés.

4. Visualiser l'ontologie
   - Utilisez l'onglet "Classes" pour voir la hiérarchie de classes (Personne, Homme, Femme, Parent...).
   - L'onglet "Object properties" et "Data properties" montre les propriétés définies (`aEnfant`, `aParent`, `sexe`, `nom`, ...).
   - L'onglet "Individuals" liste les instances (jacques, pierre, monique, ...).
   - Pour explorer les relations d'un individu, sélectionnez l'individu dans "Individuals" puis regardez ses assertions (relations) et annotations.

Conseils et points à vérifier
----------------------------
- Format du fichier : WebProtégé accepte les fichiers OWL RDF/XML, Turtle, OWL/XML, etc. Par défaut Owlready2 sauve en RDF/XML (`.owl`) — cela fonctionne avec WebProtégé.
- IRIs : WebProtégé affichera les IRIs. Si les noms sont longs, utilisez la colonne des labels ou changez l'affichage pour voir seulement les fragments.
- Raisonnement : WebProtégé offre l'intégration de reasoners côté serveur/onglet (selon la version). Si vous voulez retrouver les mêmes inférences que dans le notebook, effectuez le raisonnement localement avant d'importer (le notebook appelle `sync_reasoner()`), ou utilisez un reasoner dans WebProtégé si disponible.

Alternative : Visualiser localement avec le notebook
---------------------------------------------------
Le notebook contient aussi un petit script utilisant `networkx` et `matplotlib` pour visualiser les relations parent/enfant et frère/soeur. Si vous avez exécuté le notebook, lancez la cellule de visualisation pour obtenir un graphe simple.

Licence / crédits
------------------
Exercice pédagogique inspiré du TP d'INSA Rouen. Code et données dans ce dossier destinés à un usage pédagogique.

---
Fichier créé automatiquement par un assistant. Si vous voulez que j'ajoute des captures d'écran, exemples d'import détaillés ou une version anglaise, dites-le-moi.
