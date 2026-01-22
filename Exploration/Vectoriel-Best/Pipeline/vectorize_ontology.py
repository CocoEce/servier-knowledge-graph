"""
Script de vectorisation des ontologies et insertion dans MongoDB
Génère des embeddings BERT pour chaque classe et les stocke dans MongoDB

Usage:
    python vectorize_ontology.py <chemin_vers_csv>
    
Exemple:
    python vectorize_ontology.py ../Data/ontologie_animaux_A.csv
    python vectorize_ontology.py ../Data/ontologie_animaux_B.csv
"""

import csv
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from tqdm import tqdm


def load_model():
    """Charge le modèle BERT pour la génération d'embeddings"""
    print("Chargement du modèle sentence-transformers/all-MiniLM-L6-v2...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("✓ Modèle chargé")
    return model


def connect_mongodb():
    """Se connecte à MongoDB en utilisant l'URI du fichier .env"""
    load_dotenv()
    mongodb_uri = os.getenv('MONGODB_URI')
    
    if not mongodb_uri:
        raise ValueError("MONGODB_URI non trouvé dans le fichier .env")
    
    print("Connexion à MongoDB...")
    client = MongoClient(mongodb_uri)
    
    # Tester la connexion
    try:
        client.admin.command('ping')
        print("✓ Connecté à MongoDB")
    except Exception as e:
        raise Exception(f"Erreur de connexion à MongoDB: {e}")
    
    return client


def parse_document(doc):
    """Parse et transforme les champs du document pour MongoDB"""
    parsed_doc = {
        'id': doc['id'],
        'uri': doc['uri'],
        'label': doc['label'],
        'definition': doc['definition'],
        'rich_text': doc['rich_text']
    }
    
    # Parser les synonyms en liste
    if doc['synonyms']:
        parsed_doc['synonyms'] = [s.strip() for s in doc['synonyms'].split(';') if s.strip()]
    else:
        parsed_doc['synonyms'] = []
    
    # Parser les attributes en dictionnaire
    if doc['attributes']:
        attributes = {}
        for attr in doc['attributes'].split(','):
            if ':' in attr:
                key, value = attr.split(':', 1)
                attributes[key.strip()] = value.strip()
        parsed_doc['attributes'] = attributes
    else:
        parsed_doc['attributes'] = {}
    
    # Parser parent en dictionnaire {label, uri}
    if doc['parent']:
        parts = doc['parent'].split('|')
        if len(parts) == 2:
            parsed_doc['parent'] = {
                'label': parts[0],
                'uri': parts[1]
            }
        else:
            parsed_doc['parent'] = None
    else:
        parsed_doc['parent'] = None
    
    # Parser enfants en liste de dictionnaires [{label, uri}, ...]
    if doc['enfants']:
        enfants = []
        for enfant in doc['enfants'].split(';'):
            if '|' in enfant:
                parts = enfant.split('|')
                if len(parts) == 2:
                    enfants.append({
                        'label': parts[0],
                        'uri': parts[1]
                    })
        parsed_doc['enfants'] = enfants
    else:
        parsed_doc['enfants'] = []
    
    # Parser individus en liste
    if doc['individus']:
        parsed_doc['individus'] = [i.strip() for i in doc['individus'].split(';') if i.strip()]
    else:
        parsed_doc['individus'] = []
    
    return parsed_doc


def read_csv(csv_file):
    """Lit le fichier CSV et retourne la liste des documents"""
    print(f"Lecture du fichier {csv_file}...")
    
    documents = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parser le document pour avoir des structures propres
            parsed_doc = parse_document(row)
            documents.append(parsed_doc)
    
    print(f"✓ {len(documents)} lignes lues et parsées")
    return documents


def generate_embeddings(documents, model):
    """Génère les embeddings pour tous les documents"""
    print("Génération des embeddings...")
    
    # Extraire tous les rich_text
    rich_texts = [doc['rich_text'] for doc in documents]
    
    # Générer les embeddings en batch (plus rapide)
    embeddings = model.encode(rich_texts, show_progress_bar=True, convert_to_numpy=True)
    
    # Ajouter les embeddings aux documents
    for i, doc in enumerate(documents):
        doc['embedding'] = embeddings[i].tolist()  # Convertir numpy array en liste
    
    print(f"✓ {len(documents)} embeddings générés")
    return documents


def insert_to_mongodb(documents, client, clear_collection=True):
    """Insère les documents dans MongoDB"""
    db = client['Servier']
    collection = db['vector']
    
    # Vider la collection si demandé
    if clear_collection:
        print("Suppression des documents existants...")
        result = collection.delete_many({})
        print(f"✓ {result.deleted_count} documents supprimés")
    
    # Insérer les nouveaux documents
    print("Insertion des documents dans MongoDB...")
    result = collection.insert_many(documents)
    print(f"✓ {len(result.inserted_ids)} documents insérés")
    
    return len(result.inserted_ids)


def main():
    """Fonction principale"""
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python vectorize_ontology.py <chemin_vers_csv>")
        print("\nExemples:")
        print("  python vectorize_ontology.py ../Data/ontologie_animaux_A.csv")
        print("  python vectorize_ontology.py ../Data/ontologie_animaux_B.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Vérifier que le fichier existe
    if not Path(csv_file).exists():
        print(f"Erreur : Le fichier {csv_file} n'existe pas")
        sys.exit(1)
    
    print("="*60)
    print("Vectorisation de l'ontologie et insertion dans MongoDB")
    print("="*60)
    print(f"Fichier source : {csv_file}")
    print()
    
    try:
        # 1. Charger le modèle BERT
        model = load_model()
        print()
        
        # 2. Se connecter à MongoDB
        client = connect_mongodb()
        print()
        
        # 3. Lire le CSV
        documents = read_csv(csv_file)
        print()
        
        # 4. Générer les embeddings
        documents_with_embeddings = generate_embeddings(documents, model)
        print()
        
        # 5. Insérer dans MongoDB
        count = insert_to_mongodb(documents_with_embeddings, client, clear_collection=True)
        
        print()
        print("="*60)
        print("✓ Processus terminé avec succès !")
        print("="*60)
        print(f"Base de données : Servier")
        print(f"Collection : vector")
        print(f"Documents insérés : {count}")
        print(f"Dimension des embeddings : {len(documents_with_embeddings[0]['embedding'])}")
        
    except Exception as e:
        print(f"\n✗ Erreur : {e}")
        sys.exit(1)
    
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    main()
