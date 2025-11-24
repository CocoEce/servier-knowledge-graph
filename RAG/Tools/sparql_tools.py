"""
SPARQL Tools - Requêtes SPARQL pour le graphe pharmaceutique
Chaque outil retourne un résultat SPARQL formaté

Sources de données:
- WikiData: Entités et propriétés générales des médicaments
- PubChem: Composés chimiques et leurs identifiants
- ChEBI: Structures chimiques et classifications
"""

import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root .env
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(env_path)

GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200")
REPOSITORY_NAME = os.getenv("GRAPHDB_REPOSITORY", "PFE-GraphDB")


class SPARQLTools:
    """Ensemble des outils SPARQL disponibles pour l'agent"""
    
    def __init__(self):
        self.graphdb_url = GRAPHDB_URL
        self.repository = REPOSITORY_NAME
    
    def query_sparql(self, sparql_query):
        """Exécute une requête SPARQL sur GraphDB"""
        try:
            response = requests.get(
                f"{self.graphdb_url}/repositories/{self.repository}",
                params={"query": sparql_query},
                headers={"Accept": "application/sparql-results+json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erreur SPARQL: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def format_results(self, results):
        """Formate les résultats SPARQL en texte lisible"""
        if "error" in results:
            return f"Erreur: {results['error']}"
        
        if not results.get('results', {}).get('bindings'):
            return "Aucune donnée trouvée."
        
        formatted = ""
        for binding in results['results']['bindings']:
            formatted += "- "
            for key, value in binding.items():
                formatted += f"{key}: {value['value']}, "
            formatted = formatted.rstrip(", ") + "\n"
        
        return formatted
    
    # ========== TOOLS DISPONIBLES ==========
    
    def get_all_patients(self):
        """Récupère tous les composés chimiques/molécules pharmaceutiques"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX ns1: <http://www.wikidata.org/prop/direct/>
        
        SELECT DISTINCT ?compound ?label ?altLabel ?formula WHERE {
            ?compound rdfs:label ?label .
            OPTIONAL { ?compound skos:altLabel ?altLabel }
            OPTIONAL { ?compound ns1:P274 ?formula }
        }
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_all_drugs(self):
        """Récupère tous les composés PubChem avec leurs identifiants"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX sso: <http://semanticscience.org/resource/>
        PREFIX ex: <http://example.org/>
        
        SELECT ?drug ?label ?pubchemId WHERE {
            ?drug a sso:ChemicalCompound ;
                  rdfs:label ?label ;
                  ex:id ?pubchemId .
        }
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_all_diseases(self):
        """Récupère toutes les entités chimiques ChEBI"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?entity ?label ?identifier WHERE {
            ?entity rdf:type ?class ;
                    rdfs:label ?label ;
                    dc:identifier ?identifier .
            FILTER(strstarts(str(?entity), 'http://purl.obolibrary.org/obo/CHEBI'))
        }
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_all_symptoms(self):
        """Récupère tous les prédicats/propriétés disponibles"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        SELECT DISTINCT ?predicate WHERE {
            ?s ?predicate ?o .
            FILTER (!strstarts(str(?predicate), 'http://www.w3.org/1999/02/22') &&
                    !strstarts(str(?predicate), 'http://www.w3.org/2000/01') &&
                    !strstarts(str(?predicate), 'http://www.w3.org/2002/07'))
        }
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def search_patient_by_name(self, name):
        """Cherche une molécule par son nom"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?compound ?label WHERE {{
            ?compound rdfs:label ?label .
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{name}")))
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def search_drug_by_name(self, name):
        """Cherche un composé PubChem par son label"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX sso: <http://semanticscience.org/resource/>
        
        SELECT ?drug ?label WHERE {{
            ?drug a sso:ChemicalCompound ;
                  rdfs:label ?label .
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{name}")))
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def search_disease_by_name(self, name):
        """Cherche une entité ChEBI par son nom"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        
        SELECT ?entity ?label ?identifier WHERE {{
            ?entity rdfs:label ?label ;
                    dc:identifier ?identifier .
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{name}")) &&
                    strstarts(str(?entity), 'http://purl.obolibrary.org/obo/CHEBI'))
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_treatments_for_disease(self, disease_name):
        """Récupère les propriétés/attributs de toutes les molécules"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ns1: <http://www.wikidata.org/prop/direct/>
        
        SELECT ?molecule ?label ?formula WHERE {{
            ?molecule rdfs:label ?label ;
                      ns1:P274 ?formula .
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_count_stats(self):
        """Récupère les statistiques globales du graphe"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT (COUNT(DISTINCT ?s) as ?totalEntities) 
               (COUNT(DISTINCT ?p) as ?totalPredicates) 
               (COUNT(*) as ?totalTriples) WHERE {
            ?s ?p ?o .
            FILTER (!strstarts(str(?s), 'http://www.w3.org/1999') && 
                    !strstarts(str(?s), 'http://www.w3.org/2000') &&
                    !strstarts(str(?s), 'http://www.w3.org/2001') &&
                    !strstarts(str(?s), 'http://www.w3.org/2002'))
        }
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    # ========== TOOLS GÉNÉRIQUES ==========
    
    def get_everything_about_entity(self, entity_name):
        """Récupère TOUT ce qu'on sait sur une entité (molécule, composé, etc)"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX ns1: <http://www.wikidata.org/prop/direct/>
        PREFIX ex: <http://example.org/>
        
        SELECT ?entity ?label ?altLabel ?formula ?identifier ?pubchemId ?property ?value WHERE {{
            ?entity rdfs:label ?label .
            OPTIONAL {{ ?entity skos:altLabel ?altLabel }}
            OPTIONAL {{ ?entity ns1:P274 ?formula }}
            OPTIONAL {{ ?entity dc:identifier ?identifier }}
            OPTIONAL {{ ?entity ex:id ?pubchemId }}
            OPTIONAL {{ ?entity ?property ?value }}
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{entity_name}")))
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def search_patient_complete_profile(self, patient_name):
        """Récupère le profil complet d'une molécule"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX ns1: <http://www.wikidata.org/prop/direct/>
        
        SELECT ?molecule ?label ?altLabel ?formula ?identifier WHERE {{
            ?molecule rdfs:label ?label .
            OPTIONAL {{ ?molecule skos:altLabel ?altLabel }}
            OPTIONAL {{ ?molecule ns1:P274 ?formula }}
            OPTIONAL {{ ?molecule dc:identifier ?identifier }}
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{patient_name}")))
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_diseases_and_treatments_for_patient(self, patient_name):
        """Récupère composés et leurs propriétés"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        SELECT DISTINCT ?compound ?label ?altLabel WHERE {{
            ?compound rdfs:label ?label .
            OPTIONAL {{ ?compound skos:altLabel ?altLabel }}
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{patient_name}")))
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_patients_with_disease(self, disease_name):
        """Récupère les entités liées"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?entity ?label WHERE {{
            ?entity rdfs:label ?label .
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{disease_name}")))
        }}
        LIMIT 50
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_patients_taking_drug(self, drug_name):
        """Récupère les entités contenant/ayant certaines propriétés"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?entity ?label WHERE {{
            ?entity rdfs:label ?label .
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{drug_name}")))
        }}
        LIMIT 50
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_all_relationships(self):
        """Récupère toutes les relations du graphe"""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        SELECT DISTINCT ?subject ?predicate ?object WHERE {
            ?subject ?predicate ?object .
            FILTER (!strstarts(str(?subject), 'http://www.w3.org/1999') && 
                    !strstarts(str(?subject), 'http://www.w3.org/2000') &&
                    !strstarts(str(?subject), 'http://www.w3.org/2001') &&
                    !strstarts(str(?subject), 'http://www.w3.org/2002'))
        }
        LIMIT 100
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def search_by_symptom(self, symptom_name):
        """Récupère les entités avec certaines propriétés/attributs"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?entity ?label WHERE {{
            ?entity rdfs:label ?label .
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{symptom_name}")))
        }}
        LIMIT 50
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_complete_disease_info(self, disease_name):
        """Récupère toutes les infos sur une molécule/composé"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX ns1: <http://www.wikidata.org/prop/direct/>
        PREFIX ex: <http://example.org/>
        
        SELECT ?entity ?label ?altLabel ?formula ?identifier ?pubchemId ?property ?value WHERE {{
            ?entity rdfs:label ?label .
            OPTIONAL {{ ?entity skos:altLabel ?altLabel }}
            OPTIONAL {{ ?entity ns1:P274 ?formula }}
            OPTIONAL {{ ?entity dc:identifier ?identifier }}
            OPTIONAL {{ ?entity ex:id ?pubchemId }}
            OPTIONAL {{ ?entity ?property ?value }}
            FILTER (CONTAINS(LCASE(STR(?label)), LCASE("{disease_name}")))
        }}
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def raw_sparql_query(self, sparql_query):
        """Exécute une requête SPARQL brute (pour les requêtes personnalisées)"""
        results = self.query_sparql(sparql_query)
        return self.format_results(results)
