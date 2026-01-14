# -*- coding: utf-8 -*-
"""
Récupère les vraies données de PubChem via API REST
Focus sur les données médicales pour ML sur les synonymes
"""

import requests
import json
import time

def fetch_pubchem():
    """Récupère ~50 composés médicaux de PubChem avec focus sur les synonymes pour ML"""
    
    print("\n" + "="*70)
    print("🧪 RÉCUPÉRATION PUBCHEM - DONNÉES MÉDICALES POUR ML")
    print("="*70)
    
    # IDs de composés PubChem (molécules pharmaceutiques importantes)
    # Correspondance approximative avec ChEBI pour faciliter le matching ML
    # Aspirine, Paracétamol, Ibuprofène, Metformine, Atorvastatine, Amoxicilline,
    # Dopamine, Sérotonine, Adrénaline, Morphine, Codéine, Warfarine, Pénicilline G,
    # Tétracycline, Érythromycine, Fluoxétine, Paroxétine, Sertraline, Oméprazole,
    # Lansoprazole, Ranitidine, Simvastatine, Pravastatine, Amlodipine, Losartan,
    # Enalapril, Captopril, Salbutamol, Théophylline, Prednisolone, Dexaméthasone,
    # Hydrocortisone, Diazépam, Lorazépam, Alprazolam, Clonazépam, Phénytoïne,
    # Carbamazépine, Acide valproïque, Lamotrigine, Gabapentine, Topiramate,
    # Lithium, Halopéridol, Rispéridone, Olanzapine, Quétiapine, Clozapine,
    # Ciprofloxacine, Levofloxacine
    compound_cids = [
        2244, 1983, 3672, 4091, 60823, 33613,  # 6 premiers
        681, 5202, 5816, 5288826, 5284371, 54678486, 5904,  # Neurotransmetteurs + anticoagulant + antibio
        54675776, 12560, 3386, 43815, 68617, 4594, 3883,  # Antibiotiques + antidépresseurs
        3001055, 54687, 6323497, 3749, 5362124, 44093,  # IPP + statines + antihypertenseurs
        5362081, 2123, 5754, 5743, 5833, 2809,  # Antihypertenseurs + bronchodilatateurs + corticoïdes
        3016, 3958, 2118, 2789, 1775, 2554,  # Benzodiazépines + antiépileptiques
        3000, 3878, 3878, 135398737, 4763, 3272,  # Antiépileptiques + antipsychotiques
        3652, 5093, 5281033, 135409400, 2764, 2771  # Autres antipsychotiques + antibiotiques
    ]
    
    # Endpoint optimisé pour les propriétés spécifiques
    property_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularWeight,MolecularFormula,InChI,InChIKey/JSON"
    synonyms_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
    
    print(f"\n📊 Nombre de composés à récupérer : {len(compound_cids)}")
    print("\n🎯 OBJECTIF ML : Récupération de données pour matching de synonymes inter-sources")
    print("  ├─ Extraction des synonymes multiples par entité")
    print("  ├─ Propriétés chimiques pour validation croisée (InChI, SMILES)")
    print("  └─ Structure prête pour alignement avec ChEBI et Wikidata\n")
    
    # Structure de données pour export JSON
    medical_data = {
        "source": "PubChem",
        "fetch_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entities": len(compound_cids),
        "entities": []
    }
    
    successful_count = 0
    failed_count = 0
    
    for i, cid_num in enumerate(compound_cids, 1):
        try:
            # 1. Récupérer les propriétés principales
            prop_response = requests.get(property_url.format(cid=cid_num), timeout=10)
            
            if prop_response.status_code == 200:
                prop_data = prop_response.json()
                if "PropertyTable" in prop_data and "Properties" in prop_data["PropertyTable"] and len(prop_data["PropertyTable"]["Properties"]) > 0:
                    props = prop_data["PropertyTable"]["Properties"][0]
                    
                    cid_value = props.get("CID", cid_num)
                    mol_weight = props.get("MolecularWeight", "N/A")
                    mol_formula = props.get("MolecularFormula", "N/A")
                    inchi = props.get("InChI", "N/A")
                    inchi_key = props.get("InChIKey", "N/A")
                    
                    # 2. Récupérer les synonymes (appel API séparé)
                    synonyms = []
                    try:
                        syn_response = requests.get(synonyms_url.format(cid=cid_num), timeout=10)
                        if syn_response.status_code == 200:
                            syn_data = syn_response.json()
                            if "InformationList" in syn_data and "Information" in syn_data["InformationList"]:
                                for info in syn_data["InformationList"]["Information"]:
                                    if "Synonym" in info:
                                        synonyms = info["Synonym"][:20]  # Limiter à 20
                                        break
                    except Exception as e:
                        pass
                    
                    # Récupérer le nom principal (premier synonyme ou "Compound X")
                    name = synonyms[0] if synonyms else f"Compound {cid_value}"
                    
                    # URI PubChem
                    uri = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid_value}"
                    
                    # Structure de données pour ML
                    entity_data = {
                        "id": f"CID:{cid_value}",
                        "uri": uri,
                        "name": name,
                        "synonyms": synonyms,
                        "chemical_properties": {
                            "formula": mol_formula,
                            "mass": mol_weight,
                            "inchi_key": inchi_key,
                            "inchi": inchi
                        }
                    }
                    
                    medical_data["entities"].append(entity_data)
                    successful_count += 1
                    
                    # Affichage concis
                    print(f"[{i}/{len(compound_cids)}] ✅ CID:{cid_value}: {name}")
                    print(f"       Synonymes: {len(synonyms)} | Formule: {mol_formula}")
                    
                    # Petite pause pour respecter l'API
                    time.sleep(0.2)
                else:
                    failed_count += 1
                    print(f"[{i}/{len(compound_cids)}] ⚠️  CID {cid_num}: Pas de propriétés")
            else:
                failed_count += 1
                print(f"[{i}/{len(compound_cids)}] ⚠️  CID {cid_num}: Erreur {prop_response.status_code}")
                
        except Exception as e:
            failed_count += 1
            print(f"[{i}/{len(compound_cids)}] ❌ CID {cid_num}: {str(e)[:50]}")
    
    # Affichage du résultat structuré
    print(f"\n{'='*70}")
    print(f"📊 RÉSUMÉ DE LA RÉCUPÉRATION")
    print(f"{'='*70}")
    print(f"✅ Succès    : {successful_count}/{len(compound_cids)}")
    print(f"❌ Échecs    : {failed_count}/{len(compound_cids)}")
    print(f"\n📁 DONNÉES STRUCTURÉES POUR ML :")
    print(json.dumps(medical_data, indent=2, ensure_ascii=False))
    print(f"\n{'='*70}\n")
    
    return medical_data

if __name__ == "__main__":
    data = fetch_pubchem()
    
    # Sauvegarde automatique dans un fichier JSON
    output_file = "pubchem_medical_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Données sauvegardées dans: {output_file}")
