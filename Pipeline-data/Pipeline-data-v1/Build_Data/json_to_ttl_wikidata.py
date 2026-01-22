# -*- coding: utf-8 -*-
"""
Convertit les données JSON Wikidata en format TTL (Turtle) pour visualisation du graphe
"""

import json
from datetime import datetime

def json_to_ttl_wikidata():
    """Convertit wikidata_medical_data.json en wikidata_medical_data.ttl"""
    
    print("\n" + "="*70)
    print("📄 CONVERSION Wikidata JSON → TTL")
    print("="*70)
    
    # Charger le fichier JSON
    try:
        with open("wikidata_medical_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier wikidata_medical_data.json introuvable!")
        print("   Exécutez d'abord: python fetch_wikidata.py")
        return
    
    print(f"\n✅ Chargement de {data['total_entities']} entités Wikidata")
    
    # Créer le contenu TTL
    ttl_content = []
    
    # Préfixes RDF
    ttl_content.append("# Wikidata Medical Data - Knowledge Graph")
    ttl_content.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    ttl_content.append(f"# Source: Wikidata SPARQL")
    ttl_content.append(f"# Total entities: {data['total_entities']}")
    ttl_content.append("")
    ttl_content.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    ttl_content.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    ttl_content.append("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
    ttl_content.append("@prefix wd: <http://www.wikidata.org/entity/> .")
    ttl_content.append("@prefix wdt: <http://www.wikidata.org/prop/direct/> .")
    ttl_content.append("@prefix schema: <http://schema.org/> .")
    ttl_content.append("@prefix cheminf: <http://semanticscience.org/resource/> .")
    ttl_content.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    ttl_content.append("")
    
    # Générer les triplets pour chaque entité
    for entity in data['entities']:
        qid = entity['id']
        name = entity['name']
        
        # URI Wikidata
        wd_uri = f"wd:{qid}"
        
        ttl_content.append(f"# {name} ({qid})")
        ttl_content.append(f"{wd_uri}")
        ttl_content.append(f"    rdf:type schema:Thing ;")
        ttl_content.append(f"    rdfs:label \"{escape_ttl(name)}\"@en ;")
        
        # Description
        if entity.get('description') and entity['description'] != 'N/A':
            description = entity['description'].replace('\n', ' ').replace('"', '\\"')
            ttl_content.append(f"    schema:description \"{description}\"@en ;")
        
        # Synonymes
        for synonym in entity['synonyms']:
            if synonym:
                ttl_content.append(f"    skos:altLabel \"{escape_ttl(synonym)}\"@en ;")
        
        # Propriétés chimiques
        chem_props = entity['chemical_properties']
        
        if chem_props.get('formula') and chem_props['formula'] != 'N/A':
            ttl_content.append(f"    wdt:P274 \"{escape_ttl(chem_props['formula'])}\" ;")
        
        if chem_props.get('mass') and chem_props['mass'] != 'N/A':
            ttl_content.append(f"    wdt:P2067 \"{chem_props['mass']}\"^^xsd:decimal ;")
        
        if chem_props.get('inchi_key') and chem_props['inchi_key'] != 'N/A':
            ttl_content.append(f"    wdt:P235 \"{chem_props['inchi_key']}\" ;")
        
        if chem_props.get('inchi') and chem_props['inchi'] != 'N/A':
            ttl_content.append(f"    wdt:P233 \"{escape_ttl(chem_props['inchi'])}\" ;")
        
        if chem_props.get('smiles') and chem_props['smiles'] != 'N/A':
            ttl_content.append(f"    wdt:P2017 \"{escape_ttl(chem_props['smiles'])}\" .")
        else:
            # Remplacer le dernier ; par .
            if ttl_content[-1].endswith(";"):
                ttl_content[-1] = ttl_content[-1][:-1] + "."
        
        ttl_content.append("")
    
    # Sauvegarder le fichier TTL
    output_file = "wikidata_medical_data.ttl"
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
    json_to_ttl_wikidata()
