"""
Script pour générer une ontologie de mapping entre l'ontologie A et B
basée sur les résultats de classification
"""

import json
from datetime import datetime
from typing import List, Dict
from owlready2 import get_ontology, Thing, ObjectProperty, DataProperty


class MappingOntologyGenerator:
    """Classe pour générer une ontologie de mapping"""
    
    def __init__(self, base_iri: str = "http://example.org/animal-mapping"):
        """
        Initialise le générateur d'ontologie
        
        Args:
            base_iri: IRI de base pour l'ontologie de mapping
        """
        self.base_iri = base_iri
        self.onto = get_ontology(base_iri)
        
    def load_mappings(self, mappings_path: str) -> List[Dict]:
        """
        Charge les mappings depuis un fichier JSON
        
        Args:
            mappings_path: Chemin vers le fichier de mappings
            
        Returns:
            Liste des mappings
        """
        with open(mappings_path, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        print(f"✓ Chargé {len(mappings)} mappings")
        return mappings
    
    def create_ontology_structure(self):
        """
        Crée la structure de base de l'ontologie de mapping
        """
        with self.onto:
            # Classe de base pour les mappings
            class Mapping(Thing):
                """Classe représentant un mapping entre deux classes"""
                pass
            
            # Propriétés pour le mapping
            class hasSourceClass(ObjectProperty):
                """Pointe vers la classe source (ontologie B)"""
                pass
            
            class hasTargetClass(ObjectProperty):
                """Pointe vers la classe cible (ontologie A)"""
                pass
            
            class hasSourceIRI(DataProperty):
                """IRI de la classe source"""
                range = [str]
            
            class hasTargetIRI(DataProperty):
                """IRI de la classe cible"""
                range = [str]
            
            class hasSourceLabel(DataProperty):
                """Label de la classe source"""
                range = [str]
            
            class hasTargetLabel(DataProperty):
                """Label de la classe cible"""
                range = [str]
            
            class hasSimilarityScore(DataProperty):
                """Score de similarité entre les classes"""
                range = [float]
            
            class hasProbability(DataProperty):
                """Probabilité de classification"""
                range = [float]
            
            class hasConfidenceLevel(DataProperty):
                """Niveau de confiance (high, medium, low)"""
                range = [str]
            
            class hasRank(DataProperty):
                """Rang du mapping (1 = meilleur match)"""
                range = [int]
            
            # Sauvegarder les classes pour usage ultérieur
            self.Mapping = Mapping
            self.hasSourceIRI = hasSourceIRI
            self.hasTargetIRI = hasTargetIRI
            self.hasSourceLabel = hasSourceLabel
            self.hasTargetLabel = hasTargetLabel
            self.hasSimilarityScore = hasSimilarityScore
            self.hasProbability = hasProbability
            self.hasConfidenceLevel = hasConfidenceLevel
            self.hasRank = hasRank
        
        print("✓ Structure de l'ontologie créée")
    
    def _get_confidence_level(self, probability: float) -> str:
        """
        Détermine le niveau de confiance basé sur la probabilité
        
        Args:
            probability: Probabilité de classification
            
        Returns:
            Niveau de confiance
        """
        if probability >= 0.7:
            return "high"
        elif probability >= 0.4:
            return "medium"
        else:
            return "low"
    
    def generate_mappings(self, mappings: List[Dict], include_all_ranks: bool = True):
        """
        Génère les individus de mapping dans l'ontologie
        
        Args:
            mappings: Liste des mappings depuis la classification
            include_all_ranks: Si True, inclut tous les top-k matches, sinon seulement le meilleur
        """
        with self.onto:
            mapping_count = 0
            
            for mapping in mappings:
                class_b_name = mapping['class_b_name']
                
                # Déterminer quels matches inclure
                matches = mapping['top_matches'] if include_all_ranks else [mapping['best_match']]
                
                for rank, match in enumerate(matches, 1):
                    # Créer un nom unique pour le mapping
                    mapping_name = f"mapping_{class_b_name}_to_{match['class_a_name']}_rank{rank}"
                    
                    # Créer l'individu de mapping
                    mapping_individual = self.Mapping(mapping_name)
                    
                    # Ajouter les propriétés
                    mapping_individual.hasSourceIRI = [mapping['class_b_iri']]
                    mapping_individual.hasTargetIRI = [match['class_a_iri']]
                    mapping_individual.hasSourceLabel = [mapping['class_b_label']]
                    mapping_individual.hasTargetLabel = [match['class_a_label']]
                    mapping_individual.hasSimilarityScore = [match['similarity_score']]
                    mapping_individual.hasProbability = [match['probability']]
                    mapping_individual.hasRank = [rank]
                    mapping_individual.hasConfidenceLevel = [self._get_confidence_level(match['probability'])]
                    
                    # Ajouter un label descriptif
                    mapping_individual.label = [
                        f"{mapping['class_b_label']} → {match['class_a_label']} (p={match['probability']:.3f})"
                    ]
                    
                    # Ajouter un commentaire
                    mapping_individual.comment = [
                        f"Mapping rank {rank}: {mapping['class_b_label']} from ontology B is classified to "
                        f"{match['class_a_label']} from ontology A with a probability of {match['probability']:.4f} "
                        f"(similarity score: {match['similarity_score']:.4f})"
                    ]
                    
                    mapping_count += 1
        
        print(f"✓ Créé {mapping_count} individus de mapping")
    
    def save_ontology(self, output_path: str):
        """
        Sauvegarde l'ontologie de mapping
        
        Args:
            output_path: Chemin du fichier de sortie (.owl)
        """
        self.onto.save(file=output_path, format="rdfxml")
        print(f"✓ Ontologie de mapping sauvegardée dans {output_path}")
    
    def generate_statistics(self, mappings: List[Dict], output_path: str):
        """
        Génère des statistiques sur les mappings
        
        Args:
            mappings: Liste des mappings
            output_path: Chemin du fichier de statistiques
        """
        import numpy as np
        
        # Calculer les statistiques
        probabilities = [m['best_match']['probability'] for m in mappings]
        similarities = [m['best_match']['similarity_score'] for m in mappings]
        
        high_conf = sum(1 for p in probabilities if p >= 0.7)
        medium_conf = sum(1 for p in probabilities if 0.4 <= p < 0.7)
        low_conf = sum(1 for p in probabilities if p < 0.4)
        
        stats = {
            'total_mappings': len(mappings),
            'probability_stats': {
                'mean': float(np.mean(probabilities)),
                'median': float(np.median(probabilities)),
                'std': float(np.std(probabilities)),
                'min': float(np.min(probabilities)),
                'max': float(np.max(probabilities))
            },
            'similarity_stats': {
                'mean': float(np.mean(similarities)),
                'median': float(np.median(similarities)),
                'std': float(np.std(similarities)),
                'min': float(np.min(similarities)),
                'max': float(np.max(similarities))
            },
            'confidence_distribution': {
                'high': high_conf,
                'medium': medium_conf,
                'low': low_conf
            },
            'confidence_percentages': {
                'high': round(high_conf / len(mappings) * 100, 2),
                'medium': round(medium_conf / len(mappings) * 100, 2),
                'low': round(low_conf / len(mappings) * 100, 2)
            }
        }
        
        # Sauvegarder en JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Statistiques sauvegardées dans {output_path}")
        
        # Afficher un résumé
        print("\n📊 RÉSUMÉ DES STATISTIQUES:")
        print(f"   Total mappings: {stats['total_mappings']}")
        print(f"   Probabilité moyenne: {stats['probability_stats']['mean']:.4f}")
        print(f"   Confiance haute: {stats['confidence_distribution']['high']} ({stats['confidence_percentages']['high']}%)")
        print(f"   Confiance moyenne: {stats['confidence_distribution']['medium']} ({stats['confidence_percentages']['medium']}%)")
        print(f"   Confiance basse: {stats['confidence_distribution']['low']} ({stats['confidence_percentages']['low']}%)")


def main():
    """Fonction principale"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python generate_mapping_ontology.py <mappings.json> <output.owl>")
        sys.exit(1)
    
    mappings_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Créer le générateur
    generator = MappingOntologyGenerator()
    
    # Charger les mappings
    mappings = generator.load_mappings(mappings_path)
    
    # Créer la structure de l'ontologie
    generator.create_ontology_structure()
    
    # Générer les mappings (inclure tous les rangs ou seulement le meilleur)
    include_all = input("\nInclure tous les top-5 matches? (o/n) [o]: ").lower() != 'n'
    generator.generate_mappings(mappings, include_all_ranks=include_all)
    
    # Sauvegarder l'ontologie
    generator.save_ontology(output_path)
    
    # Générer les statistiques
    stats_path = output_path.replace('.owl', '_statistics.json')
    generator.generate_statistics(mappings, stats_path)
    
    print("\n✅ Ontologie de mapping générée avec succès!")


if __name__ == "__main__":
    main()
