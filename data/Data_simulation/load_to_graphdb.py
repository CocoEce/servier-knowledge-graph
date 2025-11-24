import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le root du projet
env_path = Path(__file__).parents[2] / ".env"
load_dotenv(env_path)

# Configuration GraphDB
GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200")
REPOSITORY_NAME = "RAG-TEST"  # Nom du repository

def create_repository():
    """Crée un nouveau repository dans GraphDB"""
    config = {
        "id": REPOSITORY_NAME,
        "title": "Medical Knowledge Graph",
        "type": "memory",
        "params": {
            "ruleset": {
                "name": "rdfsplus"
            }
        }
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"{GRAPHDB_URL}/rest/repositories",
        json=config,
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Repository '{REPOSITORY_NAME}' créé avec succès!")
    elif response.status_code == 409:
        print(f"⚠️  Repository '{REPOSITORY_NAME}' existe déjà")
    else:
        print(f"❌ Erreur lors de la création du repository: {response.status_code}")
        print(response.text)

def load_ontology():
    """Charge le fichier OWL dans GraphDB"""
    owl_file = Path(__file__).parent / "medical_ontology.owl"
    
    if not owl_file.exists():
        print(f"❌ Fichier {owl_file} introuvable")
        return
    
    with open(owl_file, 'rb') as f:
        data = f.read()
    
    headers = {"Content-Type": "application/rdf+xml"}
    response = requests.post(
        f"{GRAPHDB_URL}/repositories/{REPOSITORY_NAME}/statements",
        data=data,
        headers=headers
    )
    
    if response.status_code in [200, 204]:
        print(f"✅ Ontologie chargée avec succès dans '{REPOSITORY_NAME}'!")
    else:
        print(f"❌ Erreur lors du chargement: {response.status_code}")
        print(response.text)

def verify_data():
    """Vérifie que les données sont bien chargées"""
    query = """
    SELECT (COUNT(*) as ?count) WHERE {
        ?s ?p ?o
    }
    """
    
    response = requests.get(
        f"{GRAPHDB_URL}/repositories/{REPOSITORY_NAME}",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        count = result['results']['bindings'][0]['count']['value']
        print(f"✅ {count} triplets RDF chargés dans le graphe!")
    else:
        print(f"❌ Erreur lors de la vérification: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Démarrage du chargement dans GraphDB...\n")
    
    print("📋 Instructions:")
    print("1. Allez sur http://localhost:7200")
    print("2. Cliquez sur 'Setup' → 'Repositories' → 'Create new repository'")
    print("3. Remplissez:")
    print(f"   - Repository ID: {REPOSITORY_NAME}")
    print("   - Ruleset: RDFS-Plus (Optimized)")
    print("4. Cliquez 'Create'")
    print("\nAppuyez sur Entrée une fois le repository créé...")
    input()
    
    # Charger l'ontologie
    load_ontology()
    
    # Vérifier
    verify_data()
    
    print("\n✨ Terminé! Vous pouvez maintenant interroger le graphe.")
