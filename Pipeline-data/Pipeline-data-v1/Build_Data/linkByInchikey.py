import json

# --- Configuration des fichiers ---
INPUT_FILES = {
    "pubchem": "pubchem_data.json",
    "chebi": "chebi_data.json",
    "wikidata": "wikidata_data.json"
}
OUTPUT_TTL = "knowledge_graph.ttl"

def get_inchikey(item):
    """
    Extrait l'InChIKey selon le format spécifique fourni.
    Chemin : item -> chemical_properties -> inchi_key
    """
    try:
        return item.get("chemical_properties", {}).get("inchi_key")
    except AttributeError:
        return None

def unify_data(files_map):
    """
    Regroupe les entités par InChIKey.
    """
    unified_index = {}

    for source_name, filepath in files_map.items():
        print(f"Chargement de {source_name}...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Fichier introuvable : {filepath}")
            continue

        for item in data:
            inchikey = get_inchikey(item)
            
            if not inchikey:
                continue
            
            # Normalisation (majuscule + strip)
            inchikey = inchikey.strip().upper()

            if inchikey not in unified_index:
                unified_index[inchikey] = []

            # On ajoute l'entité complète à la liste pour cet InChIKey
            # On ajoute aussi la source pour le traçage
            item["_source"] = source_name
            unified_index[inchikey].append(item)
            
    return unified_index

def escape_string(text):
    """Échappe les guillemets pour le format Turtle."""
    if not text: return ""
    return text.replace('"', '\\"')

def generate_ttl(unified_index, output_file):
    """
    Génère le graphe RDF au format Turtle (.ttl).
    """
    triples_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # 1. Écriture des Préfixes (En-tête)
        f.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
        f.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
        f.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
        f.write("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n")
        f.write("@prefix wdt: <http://www.wikidata.org/prop/direct/> .\n")
        f.write("@prefix schema: <http://schema.org/> .\n")
        f.write("\n")

        print("Génération du fichier TTL...")

        # 2. Parcours des groupes d'InChIKey
        for inchikey, entities in unified_index.items():
            
            # On récupère toutes les URIs associées à cet InChIKey
            uris = [e["uri"] for e in entities if "uri" in e]
            
            # S'il n'y a qu'une seule entité, pas de lien sameAs, mais on écrit quand même ses données
            # Si > 1 entité, on crée les liens d'équivalence
            
            # --- Stratégie : Tout lier au premier élément (Pivot) ---
            # Ou créer une clique (tout le monde sameAs tout le monde). 
            # Ici, on va déclarer les propriétés pour CHAQUE entité
            # et lier les entités entre elles si elles partagent l'InChIKey.
            
            for entity in entities:
                subject = f"<{entity['uri']}>"
                
                # A. Propriétés de base
                f.write(f"{subject} a schema:ChemicalSubstance .\n")
                
                # InChIKey
                f.write(f"{subject} wdt:P235 \"{inchikey}\" .\n")
                
                # Nom principal (rdfs:label)
                if "name" in entity and entity["name"]:
                    f.write(f"{subject} rdfs:label \"{escape_string(entity['name'])}\"@en .\n")
                
                # Synonymes (skos:altLabel)
                if "synonyms" in entity and isinstance(entity["synonyms"], list):
                    for syn in entity["synonyms"]:
                        f.write(f"{subject} skos:altLabel \"{escape_string(syn)}\"@en .\n")
                
                # B. Liens d'équivalence (Le cœur de votre demande)
                # On lie cette entité à TOUTES les autres entités partageant le même InChIKey
                for other_uri in uris:
                    if other_uri != entity["uri"]:
                        f.write(f"{subject} owl:sameAs <{other_uri}> .\n")
                        triples_count += 1
                
                f.write("\n") # Saut de ligne pour lisibilité

    print(f"Terminé ! Fichier '{output_file}' généré.")
    print(f"Environ {triples_count} liens d'équivalence (owl:sameAs) créés.")

# --- Exécution ---
if __name__ == "__main__":
    # 1. Unification en mémoire
    index_complet = unify_data(INPUT_FILES)
    
    # 2. Écriture du Graphe
    generate_ttl(index_complet, OUTPUT_TTL)