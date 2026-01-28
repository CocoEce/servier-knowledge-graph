#!/usr/bin/env python3
"""
Script de démonstration de la pipeline complète d'alignement d'ontologies
Orchestre toutes les étapes : mapping, vectorisation, matching, et fusion interactive

Usage:
    python demo.py [--skip-mapping] [--skip-vectorize] [--skip-matching]
    
Exemples:
    python demo.py                          # Exécute toute la pipeline
    python demo.py --skip-mapping           # Saute l'étape de mapping
    python demo.py --skip-vectorize         # Saute la vectorisation
"""

import sys
import argparse
from pathlib import Path
import subprocess
import time

# Ajouter le répertoire parent au path pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step_num, total_steps, description):
    """Affiche l'étape en cours"""
    print(f"\n{'*' * 80}")
    print(f"  ÉTAPE {step_num}/{total_steps}: {description}")
    print(f"{'*' * 80}\n")


def ask_continue(step_name):
    """Demande à l'utilisateur s'il veut continuer"""
    while True:
        response = input(f"\n➡️  Continuer vers l'étape suivante ({step_name}) ? [O/n] ").strip().lower()
        if response in ['', 'o', 'oui', 'y', 'yes']:
            return True
        elif response in ['n', 'non', 'no']:
            print("\n⚠️  Pipeline arrêtée par l'utilisateur")
            sys.exit(0)
        else:
            print("   Réponse invalide. Tapez 'O' pour continuer ou 'n' pour arrêter.")


def run_step(description, func, *args, **kwargs):
    """Exécute une étape et gère les erreurs"""
    print(f"🔄 {description}...")
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"✅ {description} terminé en {elapsed:.1f}s")
        return result
    except Exception as e:
        print(f"❌ Erreur lors de {description}: {e}")
        raise


def step_mapping():
    """Étape 1: Mapping OWL vers CSV"""
    print_step(1, 4, "MAPPING OWL → CSV")
    
    from pipeline.mapping_ontologie import main as mapping_main
    
    print("Conversion des ontologies OWL en CSV...")
    print("→ Extraction des classes, propriétés, relations hiérarchiques\n")
    
    mapping_main()
    
    # Vérifier que les CSV ont bien été créés
    csv_dir = project_root / "data" / "csv"
    csv_a = csv_dir / "ontologie_animaux_A.csv"
    csv_b = csv_dir / "ontologie_animaux_B.csv"
    
    if not csv_a.exists() or not csv_b.exists():
        raise FileNotFoundError("Les fichiers CSV n'ont pas été créés correctement")
    
    print(f"\n✓ Fichiers créés:")
    print(f"  • {csv_a.relative_to(project_root)}")
    print(f"  • {csv_b.relative_to(project_root)}")


def step_vectorize():
    """Étape 2: Vectorisation de l'ontologie B"""
    print_step(2, 4, "VECTORISATION DE L'ONTOLOGIE B")
    
    csv_dir = project_root / "data" / "csv"
    csv_b = csv_dir / "ontologie_animaux_B.csv"
    
    # Vérifier que le CSV existe
    if not csv_b.exists():
        raise FileNotFoundError("Le fichier CSV de l'ontologie B n'existe pas. Exécutez d'abord l'étape de mapping.")
    
    print("Génération des embeddings BERT et insertion dans MongoDB...")
    print("→ L'ontologie B servira de référence pour la recherche vectorielle\n")
    
    # Vectoriser ontologie B (référence)
    print("📊 Vectorisation de l'ontologie B...")
    subprocess.run([
        sys.executable,
        str(project_root / "pipeline" / "vectorize_ontology.py"),
        str(csv_b)
    ], cwd=str(project_root), check=True)
    
    print("\n✓ Ontologie B vectorisée et stockée dans MongoDB")


def step_matching():
    """Étape 3: Alignement sémantique"""
    print_step(3, 4, "ALIGNEMENT SÉMANTIQUE")
    
    csv_dir = project_root / "data" / "csv"
    csv_a = csv_dir / "ontologie_animaux_A.csv"
    
    if not csv_a.exists():
        raise FileNotFoundError("Le fichier CSV de l'ontologie A n'existe pas")
    
    print("Recherche des correspondances entre les ontologies...")
    print("→ Génération des embeddings de l'ontologie A à la volée")
    print("→ Recherche vectorielle dans MongoDB (ontologie B)\n")
    
    subprocess.run([
        sys.executable,
        str(project_root / "pipeline" / "semantic_matching.py"),
        str(csv_a)
    ], cwd=str(project_root), check=True)
    
    # Vérifier que le fichier de résultats a été créé
    results_file = project_root / "alignement" / "results" / "alignment_results.json"
    if not results_file.exists():
        raise FileNotFoundError("Le fichier de résultats d'alignement n'a pas été créé")
    
    print(f"\n✓ Résultats sauvegardés: {results_file.relative_to(project_root)}")


def step_interactive_alignment():
    """Étape 4: Validation interactive et fusion"""
    print_step(4, 4, "VALIDATION INTERACTIVE & FUSION")
    
    results_file = project_root / "alignement" / "results" / "alignment_results.json"
    
    if not results_file.exists():
        raise FileNotFoundError("Le fichier de résultats d'alignement n'existe pas. Exécutez d'abord l'étape de matching.")
    
    print("Lancement de l'interface graphique de validation...")
    print("→ Sélectionnez les alignements à conserver")
    print("→ Cliquez sur 'Fusionner' pour générer l'ontologie finale\n")
    
    subprocess.run([
        sys.executable,
        str(project_root / "alignement" / "scripts" / "align_ontology_interactive.py")
    ], cwd=str(project_root), check=True)
    
    # Vérifier si les fichiers fusionnés ont été créés
    merged_dir = project_root / "alignement" / "merged"
    merged_owl = merged_dir / "merged_ontology.owl"
    merged_json = merged_dir / "merged_ontology.json"
    
    if merged_owl.exists() and merged_json.exists():
        print(f"\n✓ Ontologie fusionnée créée:")
        print(f"  • {merged_owl.relative_to(project_root)}")
        print(f"  • {merged_json.relative_to(project_root)}")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Pipeline complète d'alignement d'ontologies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python demo.py                    # Exécute toute la pipeline
  python demo.py --skip-mapping     # Saute l'étape de mapping (CSV déjà créés)
  python demo.py --skip-vectorize   # Saute la vectorisation (MongoDB déjà rempli)
  python demo.py --skip-matching    # Saute le matching (résultats déjà générés)
        """
    )
    
    parser.add_argument('--skip-mapping', action='store_true',
                       help="Sauter l'étape de mapping OWL → CSV")
    parser.add_argument('--skip-vectorize', action='store_true',
                       help="Sauter l'étape de vectorisation")
    parser.add_argument('--skip-matching', action='store_true',
                       help="Sauter l'étape d'alignement sémantique")
    
    args = parser.parse_args()
    
    print_header("🚀 DÉMONSTRATION - PIPELINE D'ALIGNEMENT D'ONTOLOGIES")
    
    print("Cette démonstration va exécuter les étapes suivantes:")
    print("  1. Mapping des ontologies (OWL → CSV)")
    print("  2. Vectorisation des ontologies (embeddings BERT)")
    print("  3. Alignement sémantique (recherche vectorielle)")
    print("  4. Validation interactive et fusion")
    print("  5. Chargement dans GraphDB")
    
    input("\nAppuyez sur Entrée pour commencer...")
    
    try:
        # Étape 1: Mapping
        if not args.skip_mapping:
            run_step("Mapping OWL → CSV", step_mapping)
        else:
            print("\n⏭️  Étape 1 (Mapping) ignorée")
        
        # Demander confirmation pour continuer
        if not args.skip_vectorize or not args.skip_matching:
            ask_continue("Vectorisation")
        
        # Étape 2: Vectorisation
        if not args.skip_vectorize:
            run_step("Vectorisation", step_vectorize)
            
            # Attendre que MongoDB indexe les documents
            print("\n⏳ Attente de 60 secondes pour l'indexation MongoDB...")
            time.sleep(60)
            print("✓ Indexation terminée\n")
        else:
            print("\n⏭️  Étape 2 (Vectorisation) ignorée")
        
        # Demander confirmation pour continuer
        if not args.skip_matching:
            ask_continue("Alignement sémantique")
        
        # Étape 3: Matching
        if not args.skip_matching:
            run_step("Alignement sémantique", step_matching)
        else:
            print("\n⏭️  Étape 3 (Matching) ignoré")
        
        # Demander confirmation pour continuer
        ask_continue("Validation interactive")
        
        # Étape 4: Interface interactive (toujours exécutée)
        run_step("Interface interactive", step_interactive_alignment)
        
        # Demander confirmation pour charger dans GraphDB
        ask_continue("Chargement dans GraphDB")
        
        # Étape 5: Chargement dans GraphDB
        print_step(5, 5, "CHARGEMENT DANS GRAPHDB")
        
        merged_owl = project_root / "alignement" / "merged" / "merged_ontology.owl"
        
        if not merged_owl.exists():
            print("⚠️  Ontologie merged non trouvée. Étape de chargement ignorée.")
        else:
            print("Chargement de l'ontologie merged dans GraphDB...")
            print(f"→ Fichier: {merged_owl.relative_to(project_root)}\n")
            
            subprocess.run([
                sys.executable,
                str(project_root / "graphdb" / "load_merged_ontology.py")
            ], cwd=str(project_root), check=True)
            
            print("\n✓ Ontologie chargée dans GraphDB")
            print("  • Repository: PFE-GraphDB")
            print("  • Named graph: http://pfe.ece.fr/knowledge_graph")
        
        # Résumé final
        print_header("✅ DÉMONSTRATION TERMINÉE AVEC SUCCÈS")
        
        print("Tous les fichiers ont été générés:")
        print(f"  • CSV: {project_root / 'data' / 'csv'}")
        print(f"  • Résultats d'alignement: {project_root / 'alignement' / 'results'}")
        print(f"  • Ontologie fusionnée: {project_root / 'alignement' / 'merged'}")
        print(f"  • GraphDB: http://localhost:7200 (Repository: PFE-GraphDB)")
        
        print("\n🚀 Étapes suivantes suggérées:")
        print("  1. Visualiser l'ontologie merged dans GraphDB")
        print("  2. Tester le RAG avec: cd rag && streamlit run streamlit_app.py")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Démonstration interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
