import os
from deeponto.onto import Ontology
from deeponto.align.bertmap import BERTMapPipeline

# 1. Chemins vers vos fichiers (adaptez si nécessaire)
src_file = "mouse.owl"   # Ontologie source
tgt_file = "human.owl"   # Ontologie cible

# 2. Charger les ontologies
# DeepOnto utilise OwlReady2 en arrière-plan pour lire les fichiers OWL
print("Chargement des ontologies...")
src_onto = Ontology(src_file)
tgt_onto = Ontology(tgt_file)

# 3. Charger la configuration par défaut de BERTMap
# Nous utilisons la config par défaut qui est optimisée pour ce genre de tâche
config = BERTMapPipeline.load_bertmap_config()

# Optionnel : Si vous avez un bon GPU, ça ira vite. Sinon, ça peut être lent sur CPU.
# BERTMap va utiliser les labels (rdfs:label) pour trouver les synonymes.

# 4. Lancer l'alignement
print("Lancement de BERTMap... (Cela peut prendre du temps)")
bertmap = BERTMapPipeline(src_onto, tgt_onto, config)

# 5. Sauvegarder les résultats
output_file = "mappings_mouse_human.tsv"
bertmap.save_mappings(output_file, threshold=0.6) # On garde les mappings avec un score > 0.6

print(f"Alignement terminé ! Résultats sauvegardés dans {output_file}")