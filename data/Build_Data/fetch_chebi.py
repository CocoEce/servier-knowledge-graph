# -*- coding: utf-8 -*-
"""
Récupère les vraies données de ChEBI via API officielle 2.0
"""

import requests
import json

def fetch_chebi():
    """Récupère 5 molécules de ChEBI avec leurs propriétés scientifiques"""
    
    print("\n" + "="*70)
    print("⚗️  RÉCUPÉRATION ChEBI - 5 MOLÉCULES SCIENTIFIQUES")
    print("="*70)
    
    # IDs ChEBI populaires (molécules pharmaceutiques)
    # Aspirine, Paracétamol, Ibuprofène, Metformine, Atorvastatine
    chebi_ids = [15365, 46195, 5855, 6801, 39548]
    
    base_url = "https://www.ebi.ac.uk/chebi/backend/api/public/compound"
    
    for i, chebi_id in enumerate(chebi_ids, 1):
        try:
            # Appel API ChEBI 2.0 officielle
            url = f"{base_url}/{chebi_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraction des propriétés
                chebi_id_full = data.get("chebiId", f"CHEBI:{chebi_id}")
                name = data.get("chebiAsciiName", data.get("name", "N/A"))
                definition = data.get("definition", "N/A")
                formula = data.get("formula", "N/A")
                mass = data.get("mass", "N/A")
                inchi_key = data.get("inchiKey", "N/A")
                
                # URI ChEBI officiel
                uri = f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={chebi_id_full}"
                
                print(f"\n{'─'*70}")
                print(f"📍 ENTITÉ {i}")
                print(f"{'─'*70}")
                
                print(f"\n🔗 URI ChEBI : {uri}")
                print(f"📛 Nom : {name}")
                print(f"🆔 ChEBI ID : {chebi_id_full}")
                
                if definition and definition != "N/A":
                    print(f"📝 Définition : {definition[:100]}..." if len(definition) > 100 else f"📝 Définition : {definition}")
                
                if formula and formula != "N/A":
                    print(f"🧪 Formule chimique : {formula}")
                
                if mass and mass != "N/A":
                    print(f"⚖️  Masse moléculaire : {mass}")
                
                if inchi_key and inchi_key != "N/A":
                    print(f"🔬 InChI Key : {inchi_key[:40]}...")
                
                # Triplets RDF correspondants
                print(f"\n📊 Triplets RDF :")
                print(f"  - ({uri}, rdf:type, \"ChemicalEntity\")")
                print(f"  - ({uri}, rdfs:label, \"{name}\")")
                print(f"  - ({uri}, chebi:chebiId, \"{chebi_id_full}\")")
                if definition and definition != "N/A":
                    def_text = definition[:60] + "..." if len(definition) > 60 else definition
                    print(f"  - ({uri}, obo:IAO_0000115, \"{def_text}\")")
                if formula and formula != "N/A":
                    print(f"  - ({uri}, chebi:formula, \"{formula}\")")
                if mass and mass != "N/A":
                    print(f"  - ({uri}, chebi:mass, {mass})")
            else:
                print(f"\n⚠️ Erreur pour ChEBI {chebi_id}: {response.status_code}")
                
        except Exception as e:
            print(f"\n❌ ERREUR pour ChEBI {chebi_id}: {e}")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    fetch_chebi()
