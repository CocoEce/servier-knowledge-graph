# -*- coding: utf-8 -*-
"""
Récupère les vraies données de ChEBI via API officielle 2.0
Focus sur les données médicales pour ML sur les synonymes
"""

import requests
import json
import time

def fetch_chebi():
    """Récupère ~50 molécules médicales de ChEBI avec focus sur les synonymes pour ML"""
    
    print("\n" + "="*70)
    print("⚗️  RÉCUPÉRATION ChEBI - DONNÉES MÉDICALES POUR ML")
    print("="*70)
    
    # IDs ChEBI de molécules pharmaceutiques et médicaments importants
    # Aspirine, Paracétamol, Ibuprofène, Metformine, Atorvastatine, Amoxicilline,
    # Insuline, Dopamine, Sérotonine, Adrénaline, Morphine, Codéine, Warfarine,
    # Héparine, Pénicilline, Céphalosporine, Tétracycline, Érythromycine,
    # Fluoxétine, Paroxétine, Sertraline, Oméprazole, Lansoprazole, Ranitidine,
    # Simvastatine, Pravastatine, Amlodipine, Losartan, Enalapril, Captopril,
    # Salbutamol, Théophylline, Prednisolone, Dexaméthasone, Hydrocortisone,
    # Diazépam, Lorazépam, Alprazolam, Clonazépam, Phénytoïne, Carbamazépine,
    # Acide valproïque, Lamotrigine, Gabapentine, Topiramate, Lithium, Halopéridol,
    # Rispéridone, Olanzapine, Quétiapine, Clozapine
    chebi_ids = [
        15365, 46195, 5855, 6801, 39548, 2676,  # 6 premiers
        145810, 18243, 28790, 33568, 17303, 16714, 10033,  # Molécules signalisation + anticoagulants
        24505, 17334, 23066, 27902, 42355,  # Antibiotiques
        5118, 7815, 9154, 7792, 6377, 8776,  # Antidépresseurs + IPP
        9303, 8461, 2618, 6541, 4784, 3704,  # Statines + antihypertenseurs
        2549, 28177, 8378, 41879, 5754,  # Bronchodilatateurs + corticoïdes
        5077, 6690, 2611, 3992, 8107, 3387,  # Benzodiazépines + antiépileptiques
        39867, 6445, 4903, 9635, 49713, 5613,  # Antiépileptiques + antipsychotiques
        135810, 7735, 8405, 3766  # Autres antipsychotiques
    ]
    
    base_url = "https://www.ebi.ac.uk/chebi/backend/api/public/compound"
    
    print(f"\n📊 Nombre de molécules à récupérer : {len(chebi_ids)}")
    print("\n🎯 OBJECTIF ML : Récupération de données pour matching de synonymes inter-sources")
    print("  ├─ Extraction des synonymes multiples par entité")
    print("  ├─ Propriétés chimiques pour validation croisée (InChI, SMILES)")
    print("  └─ Structure prête pour alignement avec PubChem et Wikidata\n")
    
    # Structure de données pour export JSON
    medical_data = {
        "source": "ChEBI",
        "fetch_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entities": len(chebi_ids),
        "entities": []
    }
    
    successful_count = 0
    failed_count = 0
    
    for i, chebi_id in enumerate(chebi_ids, 1):
        try:
            # Appel API ChEBI 2.0 officielle (avec trailing slash)
            url = f"{base_url}/{chebi_id}/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraction des propriétés (nouvelle structure API 2.0)
                chebi_id_full = data.get("chebi_accession", f"CHEBI:{chebi_id}")
                name = data.get("ascii_name", data.get("name", "N/A"))
                definition = data.get("definition", "N/A")
                
                # Chemical data (formule, masse)
                chemical_data = data.get("chemical_data", {})
                formula = chemical_data.get("formula", "N/A") if chemical_data else "N/A"
                mass = chemical_data.get("mass", "N/A") if chemical_data else "N/A"
                
                # Structure data (InChI, SMILES)
                default_structure = data.get("default_structure", {})
                inchi_key = default_structure.get("standard_inchi_key", "N/A") if default_structure else "N/A"
                inchi = default_structure.get("standard_inchi", "N/A") if default_structure else "N/A"
                smiles = default_structure.get("smiles", "N/A") if default_structure else "N/A"
                
                # Synonymes (extraire de names.SYNONYM)
                synonyms = []
                names_data = data.get("names", {})
                if "SYNONYM" in names_data and isinstance(names_data["SYNONYM"], list):
                    synonyms = [syn["name"] for syn in names_data["SYNONYM"] if "name" in syn]
                
                # URI ChEBI officiel
                uri = f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={chebi_id_full}"
                
                # Structure de données pour ML
                entity_data = {
                    "id": chebi_id_full,
                    "uri": uri,
                    "name": name,
                    "synonyms": synonyms,
                    "definition": definition,
                    "chemical_properties": {
                        "formula": formula,
                        "mass": mass,
                        "inchi_key": inchi_key,
                        "inchi": inchi,
                        "smiles": smiles
                    }
                }
                
                medical_data["entities"].append(entity_data)
                successful_count += 1
                
                # Affichage concis
                print(f"[{i}/{len(chebi_ids)}] ✅ {chebi_id_full}: {name}")
                print(f"       Synonymes: {len(synonyms)} | Formule: {formula}")
                
                # Petite pause pour respecter l'API
                time.sleep(0.2)
                
            else:
                failed_count += 1
                print(f"[{i}/{len(chebi_ids)}] ⚠️  ChEBI {chebi_id}: Erreur {response.status_code}")
                
        except Exception as e:
            failed_count += 1
            print(f"[{i}/{len(chebi_ids)}] ❌ ChEBI {chebi_id}: {str(e)[:50]}")
    
    # Affichage du résultat structuré
    print(f"\n{'='*70}")
    print(f"📊 RÉSUMÉ DE LA RÉCUPÉRATION")
    print(f"{'='*70}")
    print(f"✅ Succès    : {successful_count}/{len(chebi_ids)}")
    print(f"❌ Échecs    : {failed_count}/{len(chebi_ids)}")
    print(f"\n📁 DONNÉES STRUCTURÉES POUR ML :")
    print(json.dumps(medical_data, indent=2, ensure_ascii=False))
    print(f"\n{'='*70}\n")
    
    return medical_data

if __name__ == "__main__":
    data = fetch_chebi()
    
    # Sauvegarde automatique dans un fichier JSON
    output_file = "chebi_medical_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Données sauvegardées dans: {output_file}")
