#!/usr/bin/env python3
"""
Script d'alignement sémantique d'ontologies par recherche vectorielle.
Parcourt hiérarchiquement l'ontologie A et trouve les correspondances dans l'ontologie B
en utilisant MongoDB Atlas Vector Search.
"""

import sys
import csv
import json
from pathlib import Path
from collections import defaultdict, deque
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient

# ============================================================================
# PARAMÈTRES CONFIGURABLES
# ============================================================================

# Nombre de résultats à retourner pour chaque recherche
TOP_K = 5

# Seuil de similarité minimum (0.0 à 1.0)
# Les correspondances avec un score inférieur seront filtrées
SIMILARITY_THRESHOLD = 0.85

# Nom de l'index de recherche vectorielle dans MongoDB Atlas
VECTOR_SEARCH_INDEX = "vector_search_index"

# Modèle de sentence embedding
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ============================================================================


class OntologyMatcher:
    """Classe pour l'alignement sémantique d'ontologies."""
    
    def __init__(self, csv_path, top_k=TOP_K, threshold=SIMILARITY_THRESHOLD):
        """
        Initialise le matcher d'ontologies.
        
        Args:
            csv_path: Chemin vers le CSV de l'ontologie A
            top_k: Nombre de résultats à retourner
            threshold: Seuil de similarité minimum
        """
        self.csv_path = Path(csv_path)
        self.top_k = top_k
        self.threshold = threshold
        self.classes = {}
        self.hierarchy = defaultdict(list)
        self.root_classes = []
        
        # Chargement du modèle et connexion MongoDB
        print(f"🔄 Chargement du modèle {EMBEDDING_MODEL}...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ValueError("MONGODB_URI non trouvé dans .env")
        
        print("🔄 Connexion à MongoDB Atlas...")
        self.client = MongoClient(mongodb_uri)
        self.db = self.client['Servier']
        self.collection = self.db['vector']
        
    def parse_csv(self):
        """Parse le CSV et construit la structure hiérarchique."""
        print(f"📖 Lecture du fichier {self.csv_path.name}...")
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                class_id = row['id']
                
                # Parse parent (format: "label|uri")
                parent_info = None
                if row['parent']:
                    parts = row['parent'].split('|')
                    if len(parts) == 2:
                        parent_info = {'label': parts[0], 'uri': parts[1]}
                
                # Parse children (format: "label1|uri1;label2|uri2")
                children_info = []
                if row['enfants']:
                    for child_str in row['enfants'].split(';'):
                        parts = child_str.split('|')
                        if len(parts) == 2:
                            children_info.append({'label': parts[0], 'uri': parts[1]})
                
                # Parse synonyms
                synonyms = [s.strip() for s in row['synonyms'].split(';') if s.strip()]
                
                # Parse individuals
                individuals = []
                if row['individus']:
                    for ind_str in row['individus'].split(';'):
                        if '(' in ind_str and ')' in ind_str:
                            name = ind_str[:ind_str.index('(')].strip()
                            desc = ind_str[ind_str.index('(')+1:ind_str.rindex(')')].strip()
                            individuals.append({'name': name, 'description': desc})
                
                # Stockage de la classe
                self.classes[class_id] = {
                    'id': class_id,
                    'uri': row['uri'],
                    'label': row['label'],
                    'definition': row['definition'],
                    'synonyms': synonyms,
                    'parent': parent_info,
                    'children': children_info,
                    'attributes': row['attributes'],
                    'individuals': individuals,
                    'rich_text': row['rich_text']
                }
                
                # Construction de la hiérarchie
                if parent_info:
                    parent_id = parent_info['label']
                    self.hierarchy[parent_id].append(class_id)
                else:
                    self.root_classes.append(class_id)
        
        print(f"✅ {len(self.classes)} classes chargées, {len(self.root_classes)} classes racines")
        
    def search_matches(self, class_data):
        """
        Recherche des correspondances pour une classe via Vector Search.
        
        Args:
            class_data: Données de la classe à rechercher
            
        Returns:
            Liste des correspondances avec leurs scores
        """
        # Génération de l'embedding pour le rich_text
        embedding = self.model.encode(class_data['rich_text']).tolist()
        
        # Requête de recherche vectorielle sur MongoDB Atlas
        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_SEARCH_INDEX,
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": 100,
                    "limit": self.top_k
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "uri": 1,
                    "label": 1,
                    "definition": 1,
                    "synonyms": 1,
                    "parent": 1,
                    "enfants": 1,
                    "attributes": 1,
                    "individus": 1,
                    "rich_text": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        # Filtrage par seuil de similarité
        filtered_results = [
            r for r in results 
            if r['score'] >= self.threshold
        ]
        
        return filtered_results
    
    def traverse_hierarchy(self):
        """
        Parcourt l'ontologie de manière hiérarchique (top-down) et trouve les correspondances.
        
        Returns:
            Dictionnaire avec les résultats d'alignement
        """
        print(f"🔍 Recherche des correspondances (top_k={self.top_k}, seuil={self.threshold})...")
        
        results = {
            'metadata': {
                'source_ontology': str(self.csv_path),
                'top_k': self.top_k,
                'similarity_threshold': self.threshold,
                'total_classes': len(self.classes),
                'root_classes': len(self.root_classes)
            },
            'alignments': []
        }
        
        # Parcours en largeur (BFS) pour traverser hiérarchiquement
        queue = deque(self.root_classes)
        visited = set()
        processed = 0
        
        while queue:
            class_id = queue.popleft()
            
            if class_id in visited:
                continue
            visited.add(class_id)
            
            class_data = self.classes[class_id]
            
            # Recherche des correspondances
            matches = self.search_matches(class_data)
            
            # Ajout au résultat
            alignment_entry = {
                'source_class': {
                    'id': class_data['id'],
                    'uri': class_data['uri'],
                    'label': class_data['label'],
                    'definition': class_data['definition'],
                    'synonyms': class_data['synonyms'],
                    'parent': class_data['parent'],
                    'children': class_data['children'],
                    'attributes': class_data['attributes'],
                    'individuals': class_data['individuals']
                },
                'matches': [
                    {
                        'target_class': {
                            'id': match.get('id', ''),
                            'uri': match.get('uri', ''),
                            'label': match.get('label', ''),
                            'definition': match.get('definition', ''),
                            'synonyms': match.get('synonyms', []),
                            'parent': match.get('parent'),
                            'enfants': match.get('enfants', []),
                            'attributes': match.get('attributes', ''),
                            'individus': match.get('individus', [])
                        },
                        'similarity_score': match['score']
                    }
                    for match in matches
                ]
            }
            
            results['alignments'].append(alignment_entry)
            
            processed += 1
            if processed % 10 == 0:
                print(f"  ⏳ {processed}/{len(self.classes)} classes traitées...")
            
            # Ajout des enfants à la queue
            if class_id in self.hierarchy:
                for child_id in self.hierarchy[class_id]:
                    queue.append(child_id)
        
        print(f"✅ {processed} classes traitées")
        
        # Statistiques
        total_matches = sum(len(a['matches']) for a in results['alignments'])
        classes_with_matches = sum(1 for a in results['alignments'] if a['matches'])
        
        results['metadata']['statistics'] = {
            'classes_processed': processed,
            'total_matches_found': total_matches,
            'classes_with_matches': classes_with_matches,
            'classes_without_matches': processed - classes_with_matches,
            'average_matches_per_class': round(total_matches / processed, 2) if processed > 0 else 0
        }
        
        return results
    
    def save_results(self, results, output_dir):
        """
        Sauvegarde les résultats dans un fichier JSON.
        
        Args:
            results: Dictionnaire avec les résultats
            output_dir: Répertoire de sortie
        """
        output_path = Path(output_dir) / 'alignment_results.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"💾 Sauvegarde des résultats dans {output_path.name}...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Résultats sauvegardés : {output_path.name}")
        print(f"\n📊 Statistiques :")
        print(f"   • Classes traitées : {results['metadata']['statistics']['classes_processed']}")
        print(f"   • Correspondances trouvées : {results['metadata']['statistics']['total_matches_found']}")
        print(f"   • Classes avec correspondances : {results['metadata']['statistics']['classes_with_matches']}")
        print(f"   • Classes sans correspondances : {results['metadata']['statistics']['classes_without_matches']}")
        print(f"   • Moyenne par classe : {results['metadata']['statistics']['average_matches_per_class']}")


def main():
    """Point d'entrée du script."""
    if len(sys.argv) != 2:
        print("Usage: python semantic_matching.py <chemin_csv_ontologie_A>")
        print("\nExemple:")
        print("  python semantic_matching.py ../data/csv/ontologie_animaux_A.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    if not Path(csv_path).exists():
        print(f"❌ Erreur : Fichier non trouvé : {Path(csv_path).name}")
        sys.exit(1)
    
    print("=" * 70)
    print("🔍 ALIGNEMENT SÉMANTIQUE D'ONTOLOGIES")
    print("=" * 70)
    print(f"Paramètres : TOP_K={TOP_K}, SEUIL={SIMILARITY_THRESHOLD}")
    print("=" * 70)
    
    # Initialisation et exécution
    matcher = OntologyMatcher(csv_path)
    matcher.parse_csv()
    results = matcher.traverse_hierarchy()
    
    # Sauvegarde dans alignement/results/
    script_dir = Path(__file__).parent
    result_dir = script_dir.parent / 'alignement' / 'results'
    result_dir.mkdir(parents=True, exist_ok=True)
    matcher.save_results(results, result_dir)
    
    print("\n✅ Alignement terminé avec succès!")


if __name__ == "__main__":
    main()
