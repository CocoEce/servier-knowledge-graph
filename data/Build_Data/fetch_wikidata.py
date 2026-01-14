# -*- coding: utf-8 -*-
"""
Récupère les vraies données de Wikidata via SPARQL
"""

from SPARQLWrapper import SPARQLWrapper, JSON
import json

def fetch_wikidata():
    """Récupère 5 molécules de Wikidata avec leurs propriétés"""
    
    print("\n" + "="*70)
    print("🌐 RÉCUPÉRATION WIKIDATA - 5 MOLÉCULES PHARMACEUTIQUES")
    print("="*70)
    
    # Configuration de l'endpoint SPARQL
    user_agent = "Projet_PFE_Servier_ECE/1.0 (contact@ece.fr) python-sparqlwrapper"
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent=user_agent)
    
    # Requête SPARQL pour récupérer 5 molécules avec leurs propriétés
    query = """
    SELECT ?entity ?entityLabel ?description ?formula ?mass WHERE {
      # Sélectionner les molécules connues
      ?entity wdt:P31 wd:Q11173;  # Instance of: chemical compound
              rdfs:label ?entityLabel;
              schema:description ?description .
      
      FILTER(LANG(?entityLabel) = "en")
      FILTER(LANG(?description) = "en")
      
      # Récupérer formule et masse moléculaire (optionnels)
      OPTIONAL { ?entity wdt:P274 ?formula . }
      OPTIONAL { ?entity wdt:P2067 ?mass . }
    }
    LIMIT 5
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(60)
    
    try:
        results = sparql.query().convert()
        bindings = results["results"]["bindings"]
        
        print(f"\n✅ {len(bindings)} molécules récupérées\n")
        
        for i, result in enumerate(bindings, 1):
            print(f"\n{'─'*70}")
            print(f"📍 ENTITÉ {i}")
            print(f"{'─'*70}")
            
            # URI
            uri = result["entity"]["value"]
            label = result["entityLabel"]["value"]
            description = result["description"]["value"]
            
            print(f"\n🔗 URI Wikidata : {uri}")
            print(f"📛 Label : {label}")
            print(f"📝 Description : {description}")
            
            # Propriétés optionnelles
            if "formula" in result:
                formula = result["formula"]["value"]
                print(f"🧪 Formule chimique : {formula}")
            
            if "mass" in result:
                mass = result["mass"]["value"]
                print(f"⚖️  Masse moléculaire : {mass} g/mol")
            
            # Triplets RDF correspondants
            print(f"\n📊 Triplets RDF :")
            print(f"  - ({uri}, rdfs:label, \"{label}\"@en)")
            print(f"  - ({uri}, schema:description, \"{description}\"@en)")
            if "formula" in result:
                print(f"  - ({uri}, wdt:P274, \"{result['formula']['value']}\")")
            if "mass" in result:
                print(f"  - ({uri}, wdt:P2067, {result['mass']['value']})")
        
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        print(f"❌ ERREUR : {e}\n")

if __name__ == "__main__":
    fetch_wikidata()
