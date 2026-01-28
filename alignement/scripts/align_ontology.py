#!/usr/bin/env python3
"""
Script de fusion d'ontologies alignées.
Crée une ontologie fusionnée à partir des résultats d'alignement sémantique,
en préservant la provenance des classes sources.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from rdflib.namespace import XSD

# ============================================================================
# PARAMÈTRES CONFIGURABLES
# ============================================================================

ALIGNMENT_FILE = "alignment_results.json"
OUTPUT_OWL = "merged_ontology.owl"
OUTPUT_JSON = "merged_ontology.json"

# Namespace pour l'ontologie fusionnée
MERGED_NS = "http://example.org/merged-animal-ontology/"

# ============================================================================


class OntologyMerger:
    """Classe pour fusionner deux ontologies alignées."""
    
    def __init__(self, alignment_path):
        """
        Initialise le merger.
        
        Args:
            alignment_path: Chemin vers le fichier alignment_results.json
        """
        self.alignment_path = Path(alignment_path)
        self.alignments = []
        self.metadata = {}
        self.merged_classes = {}
        self.class_hierarchy = defaultdict(list)
        
        # Création du graph RDF
        self.graph = Graph()
        self.merged = Namespace(MERGED_NS)
        self.graph.bind("merged", self.merged)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        
    def load_alignments(self):
        """Charge le fichier d'alignement."""
        print(f"📖 Chargement de {self.alignment_path.name}...")
        
        with open(self.alignment_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.metadata = data['metadata']
            self.alignments = data['alignments']
        
        print(f"✅ {len(self.alignments)} alignements chargés")
        
    def parse_individual_string(self, ind_str):
        """
        Parse une chaîne d'individu au format "Name (Description)".
        
        Args:
            ind_str: Chaîne de l'individu
            
        Returns:
            Dict avec name et description, ou None
        """
        match = re.match(r'^(.+?)\s*\((.+)\)$', ind_str.strip())
        if match:
            return {
                'name': match.group(1).strip(),
                'description': match.group(2).strip()
            }
        return None
    
    def merge_individuals(self, source_individuals, target_individus):
        """
        Fusionne les individus des deux sources.
        
        Args:
            source_individuals: Liste d'individus de la source A (format dict)
            target_individus: Liste d'individus de la source B (format string)
            
        Returns:
            Liste fusionnée avec provenance
        """
        merged = []
        
        # Individus de la source A
        for ind in source_individuals:
            merged.append({
                'name': ind['name'],
                'description': ind['description'],
                'source': 'A'
            })
        
        # Individus de la source B (parser les strings)
        for ind_str in target_individus:
            parsed = self.parse_individual_string(ind_str)
            if parsed:
                merged.append({
                    'name': parsed['name'],
                    'description': parsed['description'],
                    'source': 'B'
                })
        
        return merged
    
    def merge_synonyms(self, source_synonyms, target_synonyms):
        """Fusionne les listes de synonymes sans doublons."""
        all_synonyms = set(source_synonyms) | set(target_synonyms)
        return sorted(list(all_synonyms))
    
    def create_merged_classes(self):
        """Crée les classes fusionnées à partir des alignements."""
        print("🔄 Création des classes fusionnées...")
        
        for alignment in self.alignments:
            source = alignment['source_class']
            
            # Si pas de correspondance, on garde juste la source
            if not alignment['matches']:
                target = None
                best_score = 0.0
            else:
                target = alignment['matches'][0]['target_class']
                best_score = alignment['matches'][0]['similarity_score']
            
            # ID de la classe fusionnée (basé sur la source A)
            merged_id = source['id']
            
            # Création de la classe fusionnée
            merged_class = {
                'id': merged_id,
                'uri': str(self.merged[merged_id]),
                'label': source['label'],
                'similarity_score': best_score,
                
                # Provenance source A
                'source_A': {
                    'label': source['label'],
                    'uri': source['uri'],
                    'definition': source['definition']
                },
                
                # Provenance source B (si alignement trouvé)
                'source_B': {
                    'label': target['label'] if target else None,
                    'uri': target['uri'] if target else None,
                    'definition': target['definition'] if target else None
                } if target else None,
                
                # Données fusionnées
                'synonyms': self.merge_synonyms(
                    source['synonyms'],
                    target['synonyms'] if target else []
                ),
                'attributes': {
                    'source_A': source['attributes'],
                    'source_B': target['attributes'] if target else None
                },
                'individuals': self.merge_individuals(
                    source['individuals'],
                    target['individus'] if target else []
                ),
                
                # Hiérarchie (on garde celle de la source A comme référence)
                'parent': source['parent'],
                'children': source['children']
            }
            
            self.merged_classes[merged_id] = merged_class
            
            # Construction de la hiérarchie
            if source['parent']:
                parent_id = source['parent']['label']
                self.class_hierarchy[parent_id].append(merged_id)
        
        print(f"✅ {len(self.merged_classes)} classes fusionnées créées")
    
    def generate_owl(self):
        """Génère l'ontologie OWL fusionnée."""
        print("🔄 Génération de l'ontologie OWL...")
        
        # Déclaration de l'ontologie
        ontology_uri = URIRef(MERGED_NS)
        self.graph.add((ontology_uri, RDF.type, OWL.Ontology))
        self.graph.add((ontology_uri, RDFS.label, Literal("Merged Animal Ontology")))
        self.graph.add((ontology_uri, RDFS.comment, Literal(
            f"Ontologie fusionnée générée à partir de {self.metadata['source_ontology']}"
        )))
        
        # Création des classes
        for class_id, merged_class in self.merged_classes.items():
            class_uri = URIRef(merged_class['uri'])
            
            # Déclaration de la classe
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(merged_class['label'])))
            
            # Provenance source A
            self.graph.add((class_uri, self.merged['sourceA_label'], 
                           Literal(merged_class['source_A']['label'])))
            self.graph.add((class_uri, self.merged['sourceA_uri'], 
                           Literal(merged_class['source_A']['uri'])))
            self.graph.add((class_uri, self.merged['sourceA_definition'], 
                           Literal(merged_class['source_A']['definition'])))
            
            # Provenance source B (si existante)
            if merged_class['source_B']:
                self.graph.add((class_uri, self.merged['sourceB_label'], 
                               Literal(merged_class['source_B']['label'])))
                self.graph.add((class_uri, self.merged['sourceB_uri'], 
                               Literal(merged_class['source_B']['uri'])))
                self.graph.add((class_uri, self.merged['sourceB_definition'], 
                               Literal(merged_class['source_B']['definition'])))
                self.graph.add((class_uri, self.merged['similarity_score'], 
                               Literal(merged_class['similarity_score'], datatype=XSD.float)))
            
            # Synonymes
            for synonym in merged_class['synonyms']:
                self.graph.add((class_uri, self.merged['synonym'], Literal(synonym)))
            
            # Attributs source A
            if merged_class['attributes']['source_A']:
                self.graph.add((class_uri, self.merged['attributesA'], 
                               Literal(str(merged_class['attributes']['source_A']))))
            
            # Attributs source B
            if merged_class['attributes']['source_B']:
                self.graph.add((class_uri, self.merged['attributesB'], 
                               Literal(str(merged_class['attributes']['source_B']))))
            
            # Relation parent (subClassOf)
            if merged_class['parent']:
                parent_id = merged_class['parent']['label']
                if parent_id in self.merged_classes:
                    parent_uri = URIRef(self.merged_classes[parent_id]['uri'])
                    self.graph.add((class_uri, RDFS.subClassOf, parent_uri))
            
            # Individus
            for individual in merged_class['individuals']:
                ind_uri = URIRef(f"{merged_class['uri']}/{individual['name']}")
                self.graph.add((ind_uri, RDF.type, class_uri))
                self.graph.add((ind_uri, RDFS.label, Literal(individual['name'])))
                self.graph.add((ind_uri, RDFS.comment, Literal(individual['description'])))
                self.graph.add((ind_uri, self.merged['source'], Literal(individual['source'])))
        
        print(f"✅ {len(self.merged_classes)} classes OWL créées")
        print(f"✅ {len([1 for c in self.merged_classes.values() for _ in c['individuals']])} individus créés")
    
    def generate_json(self):
        """Génère la représentation JSON hiérarchique."""
        print("🔄 Génération de la structure JSON...")
        
        def build_tree(class_id):
            """Construit récursivement l'arbre hiérarchique."""
            merged_class = self.merged_classes[class_id]
            
            node = {
                'id': merged_class['id'],
                'uri': merged_class['uri'],
                'label': merged_class['label'],
                'similarity_score': merged_class['similarity_score'],
                'source_A': merged_class['source_A'],
                'source_B': merged_class['source_B'],
                'synonyms': merged_class['synonyms'],
                'attributes': merged_class['attributes'],
                'individuals': merged_class['individuals'],
                'children': []
            }
            
            # Ajout récursif des enfants
            if class_id in self.class_hierarchy:
                for child_id in self.class_hierarchy[class_id]:
                    node['children'].append(build_tree(child_id))
            
            return node
        
        # Trouve les racines (classes sans parent)
        root_classes = [
            class_id for class_id, merged_class in self.merged_classes.items()
            if not merged_class['parent']
        ]
        
        # Construction de l'arbre
        tree = {
            'metadata': {
                'source_ontology_A': self.metadata['source_ontology'],
                'total_classes': len(self.merged_classes),
                'total_individuals': sum(len(c['individuals']) for c in self.merged_classes.values()),
                'alignment_statistics': self.metadata['statistics']
            },
            'ontology': [build_tree(root_id) for root_id in root_classes]
        }
        
        return tree
    
    def save_outputs(self, output_dir):
        """Sauvegarde les fichiers OWL et JSON."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarde OWL
        owl_path = output_path / OUTPUT_OWL
        print(f"💾 Sauvegarde OWL : {owl_path}...")
        self.graph.serialize(destination=str(owl_path), format='xml')
        print(f"✅ OWL sauvegardé : {owl_path}")
        
        # Sauvegarde JSON
        json_path = output_path / OUTPUT_JSON
        print(f"💾 Sauvegarde JSON : {json_path}...")
        tree = self.generate_json()
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON sauvegardé : {json_path}")
        
        # Statistiques finales
        print("\n" + "=" * 70)
        print("📊 STATISTIQUES DE FUSION")
        print("=" * 70)
        print(f"Classes fusionnées : {len(self.merged_classes)}")
        print(f"Individus totaux : {sum(len(c['individuals']) for c in self.merged_classes.values())}")
        print(f"  - Source A : {sum(1 for c in self.merged_classes.values() for i in c['individuals'] if i['source'] == 'A')}")
        print(f"  - Source B : {sum(1 for c in self.merged_classes.values() for i in c['individuals'] if i['source'] == 'B')}")
        print(f"Classes avec alignement : {sum(1 for c in self.merged_classes.values() if c['source_B'])}")
        print(f"Classes sans alignement : {sum(1 for c in self.merged_classes.values() if not c['source_B'])}")
        print("=" * 70)


def main():
    """Point d'entrée du script."""
    print("=" * 70)
    print("🔀 FUSION D'ONTOLOGIES ALIGNÉES")
    print("=" * 70)
    
    # Chemins
    script_dir = Path(__file__).parent
    alignment_file = script_dir.parent / 'results' / ALIGNMENT_FILE
    
    if not alignment_file.exists():
        print(f"❌ Erreur : Fichier non trouvé : {alignment_file}")
        return 1
    
    # Initialisation et exécution
    merger = OntologyMerger(alignment_file)
    merger.load_alignments()
    merger.create_merged_classes()
    merger.generate_owl()
    
    # Sauvegarder dans alignement/merged/
    output_dir = script_dir.parent / 'merged'
    output_dir.mkdir(parents=True, exist_ok=True)
    merger.save_outputs(output_dir)
    
    print("\n✅ Fusion terminée avec succès!")
    return 0


if __name__ == "__main__":
    exit(main())
