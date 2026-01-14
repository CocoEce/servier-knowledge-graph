# -*- coding: utf-8 -*-
"""
Récupère les vraies données de PubChem via API REST
"""

import requests
import json

def fetch_pubchem():
    """Récupère 5 composés chimiques de PubChem avec leurs propriétés"""
    
    print("\n" + "="*70)
    print("🧪 RÉCUPÉRATION PUBCHEM - 5 COMPOSÉS CHIMIQUES")
    print("="*70)
    
    # IDs de composés PubChem populaires (pour exemple)
    compound_cids = [2244, 1983, 3672, 4091, 60823]  # Aspirine, Paracétamol, Ibuprofène, Metformine, Atorvastatine
    
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid"
    
    compounds = []
    
    for i, cid_num in enumerate(compound_cids, 1):
        try:
            # Appel API PubChem
            url = f"{base_url}/{cid_num}/JSON"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                compound = data["PC_Compounds"][0]
                
                # Extraction des propriétés
                cid_value = compound["id"]["id"]["cid"]
                
                # Récupérer le nom (IUPAC name ou common name)
                name = None
                synonyms = []
                
                # Chercher dans atoms
                if "atoms" in compound and "name" in compound["atoms"]:
                    name = compound["atoms"]["name"]
                
                # Chercher dans props
                if "props" in compound and isinstance(compound["props"], list):
                    for prop in compound["props"]:
                        if isinstance(prop, dict) and "urn" in prop:
                            urn_label = prop.get("urn", {}).get("label", "")
                            
                            if urn_label == "IUPAC Name" and "value" in prop:
                                if "sval" in prop["value"] and isinstance(prop["value"]["sval"], list):
                                    for val in prop["value"]["sval"]:
                                        if isinstance(val, dict) and "sval" in val:
                                            name = val["sval"]
                                            break
                            
                            if urn_label == "Synonym" and "value" in prop:
                                if "sval" in prop["value"] and isinstance(prop["value"]["sval"], list):
                                    for val in prop["value"]["sval"]:
                                        if isinstance(val, dict) and "sval" in val:
                                            synonyms.append(val["sval"])
                
                # Récupérer la masse moléculaire
                molecular_weight = None
                if "props" in compound and isinstance(compound["props"], list):
                    for prop in compound["props"]:
                        if isinstance(prop, dict) and "urn" in prop:
                            urn_label = prop.get("urn", {}).get("label", "")
                            if urn_label == "Molecular Weight" and "value" in prop:
                                if "fval" in prop["value"] and isinstance(prop["value"]["fval"], list):
                                    for val in prop["value"]["fval"]:
                                        if isinstance(val, dict) and "fval" in val:
                                            molecular_weight = val["fval"]
                                            break
                
                print(f"\n{'─'*70}")
                print(f"📍 ENTITÉ {i}")
                print(f"{'─'*70}")
                
                # URI PubChem
                uri = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid_value}"
                print(f"\n🔗 URI PubChem : {uri}")
                print(f"📛 Label (IUPAC) : {name if name else 'N/A'}")
                print(f"🆔 CID : {cid_value}")
                if molecular_weight:
                    print(f"⚖️  Masse moléculaire : {molecular_weight} g/mol")
                if synonyms:
                    print(f"🏷️  Synonymes : {', '.join(synonyms[:3])}")
                
                # Triplets RDF correspondants
                print(f"\n📊 Triplets RDF :")
                print(f"  - ({uri}, rdf:type, \"ChemicalCompound\")")
                print(f"  - ({uri}, rdfs:label, \"{name if name else 'Compound ' + str(cid_value)}\")")
                print(f"  - ({uri}, :cid, {cid_value})")
                if molecular_weight:
                    print(f"  - ({uri}, :molecularWeight, {molecular_weight})")
                
            else:
                print(f"\n⚠️ Erreur pour CID {cid_num}: {response.status_code}")
                
        except Exception as e:
            print(f"\n❌ ERREUR pour CID {cid_num}: {e}")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    fetch_pubchem()
