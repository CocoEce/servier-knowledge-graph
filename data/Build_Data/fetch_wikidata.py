# -*- coding: utf-8 -*-
"""
Récupère les vraies données de Wikidata via SPARQL
Focus sur les données médicales pour ML sur les synonymes
"""

from SPARQLWrapper import SPARQLWrapper, JSON
import json
import time

def fetch_wikidata():
    """Récupère ~50 entités médicales de Wikidata avec focus sur les synonymes pour ML"""
    
    print("\n" + "="*70)
    print("🌐 RÉCUPÉRATION WIKIDATA - DONNÉES MÉDICALES POUR ML")
    print("="*70)
    
    # Configuration de l'endpoint SPARQL
    user_agent = "Projet_PFE_Servier_ECE/1.0 (contact@ece.fr) python-sparqlwrapper"
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent=user_agent)
    
    print("\n🎯 OBJECTIF ML : Récupération de données pour matching de synonymes inter-sources")
    print("  ├─ Extraction des synonymes multiples par entité (altLabel)")
    print("  ├─ Propriétés chimiques pour validation croisée")
    print("  ├─ Diversité des types d'entités médicales")
    print("  └─ Structure prête pour alignement avec ChEBI et PubChem\n")
    
    # Requête SPARQL optimisée : récupération simple sans GROUP_CONCAT
    # Pour ~50 médicaments, on fait plusieurs petites requêtes
    query = """
    SELECT DISTINCT ?entity ?entityLabel ?description 
           ?formula ?mass ?inchiKey ?alias WHERE {
      # Liste de molécules pharmaceutiques vérifiées
      VALUES ?entity {
        wd:Q18216 wd:Q57055 wd:Q186126 wd:Q19484 wd:Q409649 
        wd:Q234960 wd:Q170304 wd:Q167934 wd:Q186242 wd:Q130424
        wd:Q190688 wd:Q165618 wd:Q79903 wd:Q81225 wd:Q407241
        wd:Q407008 wd:Q190294 wd:Q422248 wd:Q407431 wd:Q422438
        wd:Q415560 wd:Q407476 wd:Q155954 wd:Q419443 wd:Q190430
        wd:Q422202 wd:Q411368 wd:Q407451 wd:Q407592 wd:Q412851
        wd:Q409309 wd:Q408658 wd:Q410246 wd:Q421088 wd:Q422224
        wd:Q422186 wd:Q190107 wd:Q407631 wd:Q422586 wd:Q410076
        wd:Q415385 wd:Q421059 wd:Q27107351 wd:Q422604 wd:Q410074
        wd:Q421089 wd:Q191924 wd:Q410372 wd:Q419409 wd:Q27108063
      }
      
      # Labels
      ?entity rdfs:label ?entityLabel .
      FILTER(LANG(?entityLabel) = "en")
      
      # Description
      OPTIONAL { 
        ?entity schema:description ?description .
        FILTER(LANG(?description) = "en")
      }
      
      # Propriétés chimiques
      OPTIONAL { ?entity wdt:P274 ?formula . }
      OPTIONAL { ?entity wdt:P2067 ?mass . }
      OPTIONAL { ?entity wdt:P235 ?inchiKey . }
      
      # Synonymes (sans GROUP_CONCAT)
      OPTIONAL { 
        ?entity skos:altLabel ?alias .
        FILTER(LANG(?alias) = "en")
      }
    }
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(120)  # Augmenter le timeout à 120 secondes
    
    print(f"📊 Lancement de la requête SPARQL (LIMIT 50)...")
    
    # Structure de données pour export JSON
    medical_data = {
        "source": "Wikidata",
        "fetch_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "entities": []
    }
    
    try:
        results = sparql.query().convert()
        bindings = results["results"]["bindings"]
        
        print(f"✅ {len(bindings)} résultats bruts récupérés\n")
        
        # Grouper les résultats par entité pour agréger les synonymes
        entities_dict = {}
        
        for result in bindings:
            # URI et label
            uri = result["entity"]["value"]
            entity_id = uri.split("/")[-1]  # Extraire le Q-ID
            
            if entity_id not in entities_dict:
                label = result["entityLabel"]["value"]
                description = result.get("description", {}).get("value", "N/A")
                
                # Propriétés chimiques
                formula = result.get("formula", {}).get("value", "N/A")
                mass = result.get("mass", {}).get("value", "N/A")
                inchi_key = result.get("inchiKey", {}).get("value", "N/A")
                
                entities_dict[entity_id] = {
                    "id": entity_id,
                    "uri": uri,
                    "name": label,
                    "synonyms": [],
                    "description": description,
                    "chemical_properties": {
                        "formula": formula,
                        "mass": mass,
                        "inchi_key": inchi_key,
                        "inchi": "N/A",
                        "smiles": "N/A"
                    }
                }
            
            # Ajouter le synonyme si présent
            if "alias" in result:
                alias = result["alias"]["value"]
                if alias not in entities_dict[entity_id]["synonyms"]:
                    entities_dict[entity_id]["synonyms"].append(alias)
        
        # Convertir en liste
        entities_list = list(entities_dict.values())
        successful_count = len(entities_list)
        
        for i, entity_data in enumerate(entities_list, 1):
            medical_data["entities"].append(entity_data)
            
            # Affichage concis
            print(f"[{i}/{successful_count}] ✅ {entity_data['id']}: {entity_data['name']}")
            print(f"       Synonymes: {len(entity_data['synonyms'])} | Formule: {entity_data['chemical_properties']['formula']}")
        
        medical_data["total_entities"] = successful_count
        
        # Affichage du résultat structuré
        print(f"\n{'='*70}")
        print(f"📊 RÉSUMÉ DE LA RÉCUPÉRATION")
        print(f"{'='*70}")
        print(f"✅ Succès    : {successful_count}/{len(bindings)}")
        print(f"\n📁 DONNÉES STRUCTURÉES POUR ML :")
        print(json.dumps(medical_data, indent=2, ensure_ascii=False))
        print(f"\n{'='*70}\n")
        
        return medical_data
        
    except Exception as e:
        print(f"❌ ERREUR : {e}\n")
        return None

if __name__ == "__main__":
    data = fetch_wikidata()
    
    # Sauvegarde automatique dans un fichier JSON
    if data:
        output_file = "wikidata_medical_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Données sauvegardées dans: {output_file}")
