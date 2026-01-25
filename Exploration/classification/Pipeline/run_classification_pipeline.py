"""
Pipeline principal pour la classification d'ontologies
Exécute toutes les étapes: extraction, classification, génération de mapping
"""

import os
import sys
from pathlib import Path
import subprocess
from datetime import datetime


class ClassificationPipeline:
    """Classe pour orchestrer le pipeline de classification"""
    
    def __init__(self, base_dir: str):
        """
        Initialise le pipeline
        
        Args:
            base_dir: Répertoire de base contenant Data/ et Pipeline/
        """
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "Data"
        self.pipeline_dir = self.base_dir / "Pipeline"
        self.results_dir = self.base_dir / "Results"
        
        # Créer le dossier Results s'il n'existe pas
        self.results_dir.mkdir(exist_ok=True)
        
        # Chemins des fichiers
        self.onto_a_path = self.data_dir / "ontologie_animaux_A.owl"
        self.onto_b_path = self.data_dir / "ontologie_animaux_B.owl"
        
        # Timestamp pour les fichiers de sortie
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def print_header(self, title: str):
        """Affiche un en-tête formaté"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def run_step(self, step_name: str, command: list, cwd: str = None) -> bool:
        """
        Exécute une étape du pipeline
        
        Args:
            step_name: Nom de l'étape
            command: Commande à exécuter
            cwd: Répertoire de travail
            
        Returns:
            True si succès, False sinon
        """
        self.print_header(f"ÉTAPE: {step_name}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or str(self.pipeline_dir),
                capture_output=True,
                text=True,
                check=True
            )
            
            print(result.stdout)
            if result.stderr:
                print("Warnings/Errors:")
                print(result.stderr)
            
            print(f"✅ {step_name} - SUCCÈS")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ {step_name} - ÉCHEC")
            print(f"Code de sortie: {e.returncode}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            return False
    
    def step1_extract_classes(self) -> tuple:
        """
        Étape 1: Extraire les classes des deux ontologies
        
        Returns:
            Tuple (classes_a_path, classes_b_path)
        """
        classes_a_json = self.results_dir / f"classes_A_{self.timestamp}.json"
        classes_b_json = self.results_dir / f"classes_B_{self.timestamp}.json"
        
        # Extraction ontologie A
        success_a = self.run_step(
            "Extraction des classes de l'ontologie A",
            [
                sys.executable,
                str(self.pipeline_dir / "extract_classes.py"),
                str(self.onto_a_path),
                str(classes_a_json)
            ]
        )
        
        if not success_a:
            return None, None
        
        # Extraction ontologie B
        success_b = self.run_step(
            "Extraction des classes de l'ontologie B",
            [
                sys.executable,
                str(self.pipeline_dir / "extract_classes.py"),
                str(self.onto_b_path),
                str(classes_b_json)
            ]
        )
        
        if not success_b:
            return None, None
        
        return classes_a_json, classes_b_json
    
    def step2_classify(self, classes_a_json: Path, classes_b_json: Path) -> Path:
        """
        Étape 2: Classifier les classes de B sur A
        
        Args:
            classes_a_json: Chemin vers les classes A
            classes_b_json: Chemin vers les classes B
            
        Returns:
            Chemin vers les mappings générés
        """
        mappings_json = self.results_dir / f"mappings_{self.timestamp}.json"
        report_txt = self.results_dir / f"rapport_classification_{self.timestamp}.txt"
        
        success = self.run_step(
            "Classification des classes B → A",
            [
                sys.executable,
                str(self.pipeline_dir / "classify_ontologies.py"),
                str(classes_a_json),
                str(classes_b_json),
                str(mappings_json),
                str(report_txt)
            ]
        )
        
        if not success:
            return None
        
        return mappings_json
    
    def step3_generate_ontology(self, mappings_json: Path) -> Path:
        """
        Étape 3: Générer l'ontologie de mapping
        
        Args:
            mappings_json: Chemin vers les mappings
            
        Returns:
            Chemin vers l'ontologie générée
        """
        mapping_owl = self.results_dir / f"ontologie_mapping_{self.timestamp}.owl"
        
        # Note: Ce script nécessite une interaction utilisateur, on va le modifier
        # Pour l'instant, on va créer une version non-interactive
        
        print(self.print_header("Génération de l'ontologie de mapping"))
        
        try:
            # Import direct du module pour éviter subprocess avec input()
            sys.path.insert(0, str(self.pipeline_dir))
            from generate_mapping_ontology import MappingOntologyGenerator
            
            generator = MappingOntologyGenerator()
            mappings = generator.load_mappings(str(mappings_json))
            generator.create_ontology_structure()
            
            # Par défaut, inclure seulement le meilleur match pour simplifier
            print("Génération des mappings (meilleur match uniquement)...")
            generator.generate_mappings(mappings, include_all_ranks=False)
            
            generator.save_ontology(str(mapping_owl))
            
            # Générer les statistiques
            stats_path = str(mapping_owl).replace('.owl', '_statistics.json')
            generator.generate_statistics(mappings, stats_path)
            
            print("✅ Génération de l'ontologie - SUCCÈS")
            return mapping_owl
            
        except Exception as e:
            print(f"❌ Génération de l'ontologie - ÉCHEC: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def run(self):
        """Exécute le pipeline complet"""
        print("\n" + "🚀" * 40)
        print("  PIPELINE DE CLASSIFICATION D'ONTOLOGIES")
        print("🚀" * 40)
        
        print(f"\n📁 Répertoire de base: {self.base_dir}")
        print(f"📁 Résultats seront sauvegardés dans: {self.results_dir}")
        print(f"🕐 Timestamp: {self.timestamp}")
        
        # Vérifier que les ontologies existent
        if not self.onto_a_path.exists():
            print(f"❌ Erreur: {self.onto_a_path} n'existe pas")
            return False
        
        if not self.onto_b_path.exists():
            print(f"❌ Erreur: {self.onto_b_path} n'existe pas")
            return False
        
        # Étape 1: Extraction
        classes_a_json, classes_b_json = self.step1_extract_classes()
        if not classes_a_json or not classes_b_json:
            print("\n❌ Pipeline arrêté: échec de l'extraction")
            return False
        
        # Étape 2: Classification
        mappings_json = self.step2_classify(classes_a_json, classes_b_json)
        if not mappings_json:
            print("\n❌ Pipeline arrêté: échec de la classification")
            return False
        
        # Étape 3: Génération de l'ontologie
        mapping_owl = self.step3_generate_ontology(mappings_json)
        if not mapping_owl:
            print("\n❌ Pipeline arrêté: échec de la génération de l'ontologie")
            return False
        
        # Résumé final
        self.print_header("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
        
        print("📄 Fichiers générés:")
        print(f"   • Classes A: {classes_a_json.name}")
        print(f"   • Classes B: {classes_b_json.name}")
        print(f"   • Mappings JSON: {mappings_json.name}")
        print(f"   • Rapport: rapport_classification_{self.timestamp}.txt")
        print(f"   • CSV: mappings_{self.timestamp}.csv")
        print(f"   • Ontologie mapping: {mapping_owl.name}")
        print(f"   • Statistiques: {mapping_owl.stem}_statistics.json")
        
        print(f"\n📂 Tous les fichiers sont dans: {self.results_dir}")
        
        return True


def main():
    """Fonction principale"""
    # Déterminer le répertoire de base
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        # Par défaut, utiliser le répertoire parent du script
        script_dir = Path(__file__).parent.parent
        base_dir = script_dir
    
    # Créer et exécuter le pipeline
    pipeline = ClassificationPipeline(base_dir)
    success = pipeline.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
