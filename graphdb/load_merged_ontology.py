#!/usr/bin/env python3
"""
Script pour charger l'ontologie fusionnée dans GraphDB
Nettoie et charge les données dans le named graph 'graph_merged'
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

GRAPH_URI = "http://pfe.ece.fr/graph_merged"


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


def load_ontology(session, repo_url, owl_file):
    """Charge l'ontologie fusionnée dans le graph."""
    print(f"\n📊 Chargement de l'ontologie fusionnée...")
    print(f"   Fichier: {owl_file.name}")
    
    if not owl_file.exists():
        print(f"✗ Fichier non trouvé: {owl_file}")
        print(f"   Chemin attendu: {owl_file}")
        print("\n⚠️  Assurez-vous d'avoir exécuté l'étape de fusion avant de lancer ce script")
        return False
    
    url = f"{repo_url}/statements"
    params = {'context': f"<{GRAPH_URI}>"}
    headers = {'Content-Type': 'application/rdf+xml'}
    
    with open(owl_file, 'rb') as f:
        data = f.read()
    
    print(f"   Taille: {len(data)} octets")
    
    response = session.post(url, params=params, headers=headers, data=data)
    
    if response.status_code in [200, 204]:
        print("✓ Ontologie fusionnée chargée avec succès")
        return True
    else:
        print(f"✗ Erreur lors du chargement: {response.status_code}")
        print(f"  Message: {response.text}")
        return False


def main():
    """Fonction principale."""
    print("=" * 70)
    print("CHARGEMENT DE L'ONTOLOGIE FUSIONNÉE DANS GRAPHDB")
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
        print("\n⚠️  Assurez-vous que GraphDB est démarré et accessible")
        sys.exit(1)
    
    # Nettoyer le graph
    if not clear_graph(session, repo_url):
        sys.exit(1)
    
    # Charger l'ontologie fusionnée
    merged_file = project_root / "alignement" / "merged" / "merged_ontology.owl"
    
    if load_ontology(session, repo_url, merged_file):
        print("\n" + "=" * 70)
        print("✅ ONTOLOGIE FUSIONNÉE CHARGÉE AVEC SUCCÈS!")
        print("=" * 70)
        print(f"Named Graph: {GRAPH_URI}")
        return 0
    else:
        print("\n" + "=" * 70)
        print("❌ ÉCHEC DU CHARGEMENT")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
