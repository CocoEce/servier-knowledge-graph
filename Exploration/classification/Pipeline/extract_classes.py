"""
Script pour extraire les classes d'une ontologie OWL
"""

from owlready2 import get_ontology
from typing import List, Dict
import json


class OntologyClassExtractor:
    """Classe pour extraire les informations des classes d'une ontologie"""
    
    def __init__(self, ontology_path: str):
        """
        Initialise l'extracteur avec le chemin de l'ontologie
        
        Args:
            ontology_path: Chemin vers le fichier OWL
        """
        self.ontology_path = ontology_path
        self.ontology = get_ontology(f"file://{ontology_path}").load()
        
    def extract_classes(self) -> List[Dict]:
        """
        Extrait toutes les classes de l'ontologie avec leurs métadonnées
        
        Returns:
            Liste de dictionnaires contenant les informations des classes
        """
        classes_info = []
        
        for cls in self.ontology.classes():
            class_info = self._extract_class_info(cls)
            if class_info:
                classes_info.append(class_info)
        
        return classes_info
    
    def _extract_class_info(self, cls) -> Dict:
        """
        Extrait les informations d'une classe spécifique
        
        Args:
            cls: Classe OWL
            
        Returns:
            Dictionnaire avec les informations de la classe
        """
        # Récupérer le label
        label = cls.label[0] if cls.label else cls.name
        
        # Récupérer les commentaires
        comments = []
        if hasattr(cls, 'comment'):
            comments = [str(c) for c in cls.comment] if cls.comment else []
        
        # Récupérer les synonymes (altLabel)
        synonyms = []
        if hasattr(cls, 'altLabel'):
            synonyms = [str(s) for s in cls.altLabel] if cls.altLabel else []
        
        # Récupérer les parents
        parents = []
        for parent in cls.is_a:
            if hasattr(parent, 'name'):
                parents.append(parent.name)
        
        # Créer une description textuelle complète
        description_parts = [label]
        if comments:
            description_parts.extend(comments)
        if synonyms:
            description_parts.extend(synonyms)
        
        full_description = " ".join(description_parts)
        
        return {
            'iri': cls.iri,
            'name': cls.name,
            'label': label,
            'comments': comments,
            'synonyms': synonyms,
            'parents': parents,
            'full_description': full_description
        }
    
    def save_to_json(self, classes_info: List[Dict], output_path: str):
        """
        Sauvegarde les informations des classes dans un fichier JSON
        
        Args:
            classes_info: Liste des informations des classes
            output_path: Chemin du fichier de sortie
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(classes_info, f, indent=2, ensure_ascii=False)
        
        print(f"✓ {len(classes_info)} classes extraites et sauvegardées dans {output_path}")


def main():
    """Fonction principale pour tester l'extraction"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python extract_classes.py <ontology_path> <output_json>")
        sys.exit(1)
    
    ontology_path = sys.argv[1]
    output_path = sys.argv[2]
    
    extractor = OntologyClassExtractor(ontology_path)
    classes_info = extractor.extract_classes()
    extractor.save_to_json(classes_info, output_path)
    
    # Afficher un aperçu
    print(f"\nAperçu des premières classes:")
    for cls in classes_info[:5]:
        print(f"  - {cls['label']} ({cls['name']})")


if __name__ == "__main__":
    main()
