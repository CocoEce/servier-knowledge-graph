#!/bin/bash

# Script de lancement complet du pipeline d'alignement
# Usage: ./run_pipeline.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Lancement du Pipeline d'Alignement de Taxonomies Animales"
echo "=============================================================="
echo ""

# Étape 0 : Génération des ontologies
echo "📦 ÉTAPE 0 : Génération des ontologies de test..."
cd Data
python generate_animal_ontologies.py
echo ""

# Vérification
if [ ! -f "taxonomy_A.owl" ] || [ ! -f "taxonomy_B.owl" ]; then
    echo "❌ Erreur : Les ontologies n'ont pas été générées correctement."
    exit 1
fi

cd ../Pipeline

# Étape 1 : Extraction des données
echo "📋 ÉTAPE 1 : Extraction des données..."
python prepare_data.py
echo ""

# Étape 2 : Vectorisation BERT
echo "🧠 ÉTAPE 2 : Vectorisation BERT..."
python compute_embedding.py
echo ""

# Étape 3 : Clustering
echo "🧩 ÉTAPE 3 : Clustering et alignement..."
python clustering.py
echo ""

# Étape 4 : Génération de la méta-ontologie
echo "🏗️  ÉTAPE 4 : Génération de la méta-ontologie..."
python generate_meta_ontology.py
echo ""

echo "=============================================================="
echo "✨ PIPELINE TERMINÉ AVEC SUCCÈS !"
echo ""
echo "📊 Fichiers générés :"
echo "   - Data/taxonomy_A.owl (Taxonomie A)"
echo "   - Data/taxonomy_B.owl (Taxonomie B)"
echo "   - Pipeline/dataset_alignment.csv (Données extraites)"
echo "   - Pipeline/embeddings.npy (Vecteurs BERT)"
echo "   - Pipeline/metadata.csv (Métadonnées)"
echo "   - Pipeline/animal_clusters.csv (Alignements trouvés)"
echo "   - Pipeline/meta_animal_taxonomy.owl (Méta-ontologie finale)"
echo ""
echo "🔍 Pour analyser les résultats :"
echo "   cat Pipeline/animal_clusters.csv"
echo ""
