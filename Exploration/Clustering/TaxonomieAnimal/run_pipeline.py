"""
Script Python pour exécuter tout le pipeline d'alignement.
Compatible Windows, Linux, macOS.
Usage: python run_pipeline.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n{'='*70}")
    print(f"📍 {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(
        [sys.executable, command],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Erreur lors de l'exécution de {command}")
        sys.exit(1)
    
    print(f"✅ {description} terminée\n")

def check_file_exists(filepath, description):
    """Vérifie qu'un fichier existe."""
    if not Path(filepath).exists():
        print(f"❌ Erreur : {description} introuvable : {filepath}")
        sys.exit(1)

def main():
    print("🚀 Lancement du Pipeline d'Alignement de Taxonomies Animales")
    print("="*70)
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / "Data"
    pipeline_dir = base_dir / "Pipeline"
    
    # Étape 0 : Génération des ontologies
    print("\n📦 ÉTAPE 0 : Génération des ontologies de test...")
    os.chdir(data_dir)
    run_command("generate_animal_ontologies.py", "Génération des ontologies")
    
    # Vérification
    check_file_exists(data_dir / "taxonomy_A.owl", "Taxonomy A")
    check_file_exists(data_dir / "taxonomy_B.owl", "Taxonomy B")
    
    # Changement de répertoire pour le pipeline
    os.chdir(pipeline_dir)
    
    # Étape 1 : Extraction des données
    run_command("prepare_data.py", "ÉTAPE 1 : Extraction des données")
    check_file_exists(pipeline_dir / "dataset_alignment.csv", "Dataset d'alignement")
    
    # Étape 2 : Vectorisation BERT
    run_command("compute_embedding.py", "ÉTAPE 2 : Vectorisation BERT")
    check_file_exists(pipeline_dir / "embeddings.npy", "Embeddings")
    check_file_exists(pipeline_dir / "metadata.csv", "Métadonnées")
    
    # Étape 3 : Clustering
    run_command("clustering.py", "ÉTAPE 3 : Clustering et alignement")
    check_file_exists(pipeline_dir / "animal_clusters.csv", "Clusters d'alignement")
    
    # Étape 4 : Génération de la méta-ontologie
    run_command("generate_meta_ontology.py", "ÉTAPE 4 : Génération de la méta-ontologie")
    check_file_exists(pipeline_dir / "meta_animal_taxonomy.owl", "Méta-ontologie")
    
    # Résumé final
    print("\n" + "="*70)
    print("✨ PIPELINE TERMINÉ AVEC SUCCÈS !")
    print("="*70)
    print("\n📊 Fichiers générés :")
    print(f"   ✓ {data_dir / 'taxonomy_A.owl'}")
    print(f"   ✓ {data_dir / 'taxonomy_B.owl'}")
    print(f"   ✓ {pipeline_dir / 'dataset_alignment.csv'}")
    print(f"   ✓ {pipeline_dir / 'embeddings.npy'}")
    print(f"   ✓ {pipeline_dir / 'metadata.csv'}")
    print(f"   ✓ {pipeline_dir / 'animal_clusters.csv'}")
    print(f"   ✓ {pipeline_dir / 'meta_animal_taxonomy.owl'}")
    print("\n🔍 Pour analyser les résultats :")
    print(f"   python -c \"import pandas as pd; df=pd.read_csv('{pipeline_dir / 'animal_clusters.csv'}'); print(df.head())\"")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        sys.exit(1)
