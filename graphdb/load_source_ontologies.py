#!/usr/bin/env python3
"""
Script pour charger les ontologies sources (A et B) dans GraphDB
Nettoie et charge les données dans le named graph 'graph_origin'
"""

import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# Configuration
GRAPHDB_URL = os.getenv('GRAPHDB_URL')
GRAPHDB_REPOSITORY = os.getenv('GRAPHDB_REPOSITORY')
GRAPHDB_USERNAME = os.getenv('GRAPHDB_USERNAME')
GRAPHDB_PASSWORD = os.getenv('GRAPHDB_PASSWORD')

GRAPH_URI = "http://pfe.ece.fr/knowledge_graph"


def clear_graph(session, repo_url):
    """Supprime toutes les données du graph."""
    print(f"🗑️  Nettoyage du graph <{GRAPH_URI}>...")
    
    url = f"{repo_url}/statements"
    params = {'context': f"<{GRAPH_URI}>"}
    
    response = session.delete(url, params=params)
    
    if response.status_code in [200, 204]:
        print("✓ Graph nettoyé avec succès")
        return True
    else:
        print(f"✗ Erreur lors du nettoyage: {response.status_code}")
        print(f"  Message: {response.text}")
        return False


def load_ontology(session, repo_url, owl_file, ontology_name):
    """Charge une ontologie OWL dans le graph."""
    print(f"\n📊 Chargement de {ontology_name}...")
    print(f"   Fichier: {owl_file.name}")
    
    if not owl_file.exists():
        print(f"✗ Fichier non trouvé: {owl_file}")
        return False
    
    url = f"{repo_url}/statements"
    params = {'context': f"<{GRAPH_URI}>"}
    headers = {'Content-Type': 'application/rdf+xml'}
    
    with open(owl_file, 'rb') as f:
        data = f.read()
    
    response = session.post(url, params=params, headers=headers, data=data)
    
    if response.status_code in [200, 204]:
        print(f"✓ {ontology_name} chargée avec succès")
        return True
    else:
        print(f"✗ Erreur lors du chargement: {response.status_code}")
        print(f"  Message: {response.text}")
        return False


def get_triple_count(session, repo_url):
    """Récupère le nombre de triples dans le graph."""
    url = f"{repo_url}/statements"
    params = {'context': f"<{GRAPH_URI}>"}
    headers = {'Accept': 'application/sparql-results+json'}
    
    response = session.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        # Compter les lignes (approximatif)
        return len(response.text.splitlines())
    return 0


def main():
    """Fonction principale."""
    print("=" * 70)
    print("CHARGEMENT DES ONTOLOGIES SOURCES DANS GRAPHDB")
    print("=" * 70)
    print(f"GraphDB: {GRAPHDB_URL}")
    print(f"Repository: {GRAPHDB_REPOSITORY}")
    print(f"Named Graph: {GRAPH_URI}")
    print("=" * 70)
    
    # Vérifier les variables d'environnement
    if not all([GRAPHDB_URL, GRAPHDB_REPOSITORY, GRAPHDB_USERNAME, GRAPHDB_PASSWORD]):
        print("✗ Erreur: Variables d'environnement GraphDB manquantes dans .env")
        sys.exit(1)
    
    # Créer une session avec authentification
    session = requests.Session()
    session.auth = (GRAPHDB_USERNAME, GRAPHDB_PASSWORD)
    
    repo_url = f"{GRAPHDB_URL}/repositories/{GRAPHDB_REPOSITORY}"
    
    # Tester la connexion
    print("\n🔄 Test de connexion à GraphDB...")
    try:
        response = session.get(f"{GRAPHDB_URL}/repositories")
        if response.status_code != 200:
            print(f"✗ Impossible de se connecter à GraphDB: {response.status_code}")
            sys.exit(1)
        print("✓ Connexion établie")
    except Exception as e:
        print(f"✗ Erreur de connexion: {e}")
        sys.exit(1)
    
    # Nettoyer le graph
    if not clear_graph(session, repo_url):
        sys.exit(1)
    
    # Charger les ontologies
    data_dir = project_root / "data" / "owl"
    
    ontologies = [
        (data_dir / "ontologie_animaux_A.owl", "Ontologie A"),
        (data_dir / "ontologie_animaux_B.owl", "Ontologie B")
    ]
    
    success_count = 0
    for owl_file, name in ontologies:
        if load_ontology(session, repo_url, owl_file, name):
            success_count += 1
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print(f"Ontologies chargées: {success_count}/{len(ontologies)}")
    print(f"Named Graph: {GRAPH_URI}")
    
    if success_count == len(ontologies):
        print("\n✅ Toutes les ontologies ont été chargées avec succès!")
        return 0
    else:
        print("\n⚠️  Certaines ontologies n'ont pas pu être chargées")
        return 1


if __name__ == '__main__':
    sys.exit(main())
