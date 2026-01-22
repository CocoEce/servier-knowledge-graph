# -*- coding: utf-8 -*-
"""
Convertit les données JSON ChEBI en format TTL (Turtle) pour visualisation du graphe
"""

import json
from datetime import datetime

def json_to_ttl_chebi():
    """Convertit chebi_medical_data.json en chebi_medical_data.ttl"""
    
    print("\n" + "="*70)
    print("📄 CONVERSION ChEBI JSON → TTL")
    print("="*70)
    
    # Charger le fichier JSON
    try:
        with open("chebi_medical_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier chebi_medical_data.json introuvable!")
        print("   Exécutez d'abord: python fetch_chebi.py")
        return
    
    print(f"\n✅ Chargement de {data['total_entities']} entités ChEBI")
    
    # Créer le contenu TTL
    ttl_content = []
    
    # Préfixes RDF
    ttl_content.append("# ChEBI Medical Data - Knowledge Graph")
    ttl_content.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    ttl_content.append(f"# Source: ChEBI API")
    ttl_content.append(f"# Total entities: {data['total_entities']}")
    ttl_content.append("")
    ttl_content.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    ttl_content.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    ttl_content.append("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
    ttl_content.append("@prefix chebi: <http://purl.obolibrary.org/obo/chebi/> .")
    ttl_content.append("@prefix cheminf: <http://semanticscience.org/resource/> .")
    ttl_content.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    ttl_content.append("")
    
    # Générer les triplets pour chaque entité
    for entity in data['entities']:
        chebi_id = entity['id']
        name = entity['name']
        
        # URI ChEBI (format OBO)
        chebi_uri = f"chebi:{chebi_id.replace('CHEBI:', '')}"
        
        ttl_content.append(f"# {name} ({chebi_id})")
        ttl_content.append(f"{chebi_uri}")
        ttl_content.append(f"    rdf:type chebi:ChemicalEntity ;")
        ttl_content.append(f"    rdfs:label \"{escape_ttl(name)}\"@en ;")
        
        # Définition
        if entity.get('definition') and entity['definition'] != 'N/A':
            definition = entity['definition'].replace('\n', ' ').replace('"', '\\"')
            if len(definition) > 200:
                definition = definition[:200] + "..."
            ttl_content.append(f"    rdfs:comment \"{definition}\"@en ;")
        
        # Synonymes
        for synonym in entity['synonyms']:
            if synonym:
                ttl_content.append(f"    skos:altLabel \"{escape_ttl(synonym)}\"@en ;")
        
        # Propriétés chimiques
        chem_props = entity['chemical_properties']
        has_props = False
        
        if chem_props.get('formula') and chem_props['formula'] != 'N/A':
            if not has_props:
                has_props = True
            ttl_content.append(f"    cheminf:CHEMINF_000042 \"{escape_ttl(chem_props['formula'])}\" ;")
        
        if chem_props.get('mass') and chem_props['mass'] != 'N/A':
            ttl_content.append(f"    cheminf:CHEMINF_000338 \"{chem_props['mass']}\"^^xsd:decimal ;")
        
        if chem_props.get('inchi_key') and chem_props['inchi_key'] != 'N/A':
            ttl_content.append(f"    cheminf:CHEMINF_000059 \"{chem_props['inchi_key']}\" ;")
        
        if chem_props.get('inchi') and chem_props['inchi'] != 'N/A':
            ttl_content.append(f"    cheminf:CHEMINF_000113 \"{escape_ttl(chem_props['inchi'])}\" ;")
        
        if chem_props.get('smiles') and chem_props['smiles'] != 'N/A':
            ttl_content.append(f"    cheminf:CHEMINF_000018 \"{escape_ttl(chem_props['smiles'])}\" .")
        else:
            # Remplacer le dernier ; par .
            if ttl_content[-1].endswith(";"):
                ttl_content[-1] = ttl_content[-1][:-1] + "."
        
        ttl_content.append("")
    
    # Sauvegarder le fichier TTL
    output_file = "chebi_medical_data.ttl"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(ttl_content))
    
    print(f"\n✅ Conversion terminée!")
    print(f"📁 Fichier créé: {output_file}")
    print(f"📊 Triplets générés pour {len(data['entities'])} entités")
    print(f"\n{'='*70}\n")

def escape_ttl(text):
    """Échappe les caractères spéciaux pour TTL"""
    if not text:
        return ""
    return str(text).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', '')

if __name__ == "__main__":
    json_to_ttl_chebi()
