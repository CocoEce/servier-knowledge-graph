"""
SPARQL Tools - Requêtes SPARQL pour interroger le knowledge graph d'ontologies animales
Adaptées pour les propriétés custom du namespace merged:
"""

import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200")
REPOSITORY_NAME = os.getenv("GRAPHDB_REPOSITORY", "PFE-GraphDB")
GRAPH_URI = "http://pfe.ece.fr/knowledge_graph"


class SPARQLTools:
    """Ensemble des outils SPARQL disponibles pour l'agent RAG"""
    
    def __init__(self):
        self.graphdb_url = GRAPHDB_URL
        self.repository = REPOSITORY_NAME
        self.graph_uri = GRAPH_URI
    
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
                return {"error": f"Erreur SPARQL: {response.status_code}", "details": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    def format_results(self, results):
        """Formate les résultats SPARQL en texte lisible"""
        if "error" in results:
            return f"Erreur: {results['error']}"
        
        if not results.get('results', {}).get('bindings'):
            return "Aucune donnée trouvée dans le knowledge graph."
        
        bindings = results['results']['bindings']
        formatted_lines = []
        
        for binding in bindings:
            parts = []
            for key, value in binding.items():
                parts.append(f"{key}: {value['value']}")
            formatted_lines.append("- " + ", ".join(parts))
        
        return "\n".join(formatted_lines)
    
    def _format_concept_details(self, results):
        """Formate les détails d'un concept de manière structurée"""
        if "error" in results:
            return f"Erreur: {results['error']}"
        
        if not results.get('results', {}).get('bindings'):
            return "Aucune donnée trouvée dans le knowledge graph."
        
        bindings = results['results']['bindings']
        
        # Regrouper les informations par concept
        concepts_data = {}
        for binding in bindings:
            concept_uri = binding.get('concept', {}).get('value', 'N/A')
            
            if concept_uri not in concepts_data:
                concepts_data[concept_uri] = {
                    'label': binding.get('label', {}).get('value', 'N/A'),
                    'properties': []
                }
            
            # Ajouter TOUTES les propriétés sans filtrer
            if 'property' in binding and 'value' in binding:
                prop_full = binding['property']['value']
                val = binding['value']['value']
                
                # Extraire le nom court de la propriété
                prop_name = prop_full.split('/')[-1].split('#')[-1]
                
                # Ignorer seulement rdf:type et rdfs:label (déjà affiché)
                if prop_name not in ['type', 'label']:
                    concepts_data[concept_uri]['properties'].append((prop_name, val, prop_full))
        
        # Formater en texte
        formatted = []
        for uri, data in concepts_data.items():
            formatted.append(f"\n{'='*60}")
            formatted.append(f"=== {data['label']} ===")
            formatted.append(f"{'='*60}")
            formatted.append(f"URI: {uri}")
            
            if data['properties']:
                formatted.append(f"\n📋 Propriétés:")
                for prop_name, val, prop_full in data['properties']:
                    # Formater joliment le nom
                    display_name = prop_name.replace('_', ' ').title()
                    
                    # Si c'est une URI longue, afficher juste la fin
                    if len(val) > 100 and val.startswith('http'):
                        val_display = f".../{val.split('/')[-1]}"
                    else:
                        val_display = val
                    
                    formatted.append(f"  • {display_name}: {val_display}")
        
        return "\n".join(formatted) if formatted else "Aucune donnée trouvée."
    
    def _format_equivalences(self, results):
        """Formate les équivalences de manière lisible"""
        if "error" in results:
            return f"Erreur: {results['error']}"
        
        if not results.get('results', {}).get('bindings'):
            return "Aucune équivalence trouvée dans le knowledge graph."
        
        bindings = results['results']['bindings']
        formatted = []
        
        # Regrouper par concept
        concepts = {}
        for binding in bindings:
            label = binding.get('label', {}).get('value', 'N/A')
            
            if label not in concepts:
                concepts[label] = {
                    'synonyms': set(),
                    'source_A': binding.get('sourceA_label', {}).get('value'),
                    'source_B': binding.get('sourceB_label', {}).get('value'),
                    'similarity': binding.get('similarity', {}).get('value')
                }
            
            if 'synonym' in binding:
                concepts[label]['synonyms'].add(binding['synonym']['value'])
        
        for concept, data in concepts.items():
            formatted.append(f"\n{'='*60}")
            formatted.append(f"=== {concept} ===")
            formatted.append(f"{'='*60}")
            
            if data['source_A'] and data['source_B']:
                formatted.append(f"\n🔗 Alignement de sources:")
                formatted.append(f"  Source A: {data['source_A']}")
                formatted.append(f"  Source B: {data['source_B']}")
                if data['similarity']:
                    formatted.append(f"  Score de similarité: {float(data['similarity']):.4f}")
            
            if data['synonyms']:
                formatted.append(f"\n🏷️  Tous les synonymes (combinés des 2 sources):")
                for syn in sorted(data['synonyms']):
                    formatted.append(f"  • {syn}")
        
        return "\n".join(formatted) if formatted else "Aucune équivalence trouvée."
    
    # ========== TOOLS POUR INTERROGER LE KNOWLEDGE GRAPH ==========
    
    def get_all_classes(self):
        """Récupère toutes les classes de l'ontologie"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?class ?label
        FROM <{self.graph_uri}>
        WHERE {{
            ?class rdf:type owl:Class .
            OPTIONAL {{ ?class rdfs:label ?label }}
        }}
        LIMIT 100
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def search_concept(self, concept_name):
        """Recherche un concept spécifique et récupère TOUTES ses informations de manière dynamique"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?concept ?label ?property ?value
        FROM <{self.graph_uri}>
        WHERE {{
            ?concept rdf:type owl:Class .
            
            # Récupérer d'abord le label principal
            ?concept rdfs:label ?label .
            
            # Chercher le concept par son label OU par n'importe quelle propriété textuelle
            {{
                # Option 1: Match direct sur le label
                FILTER(REGEX(STR(?label), "^{concept_name}$", "i"))
            }} UNION {{
                # Option 2: Match sur n'importe quelle propriété textuelle du concept
                ?concept ?anyProp ?textValue .
                FILTER(isLiteral(?textValue))
                FILTER(REGEX(STR(?textValue), "^{concept_name}$", "i"))
            }}
            
            # Récupérer TOUTES les propriétés du concept trouvé
            OPTIONAL {{
                ?concept ?property ?value .
                FILTER(?property != rdf:type)
            }}
        }}
        LIMIT 500
        """
        results = self.query_sparql(query)
        return self._format_concept_details(results)
    
    def get_concept_info(self, concept_uri):
        """Récupère toutes les informations sur un concept spécifique"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT ?property ?value
        FROM <{self.graph_uri}>
        WHERE {{
            <{concept_uri}> ?property ?value .
        }}
        LIMIT 50
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def find_equivalences(self, concept_name):
        """Trouve les équivalences en cherchant les classes avec des sources A et B (concepts alignés)"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX merged: <http://example.org/merged-animal-ontology/>
        
        SELECT DISTINCT ?concept ?label ?synonym ?sourceA_label ?sourceB_label ?similarity
        FROM <{self.graph_uri}>
        WHERE {{
            ?concept rdfs:label ?label .
            FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{concept_name}")))
            
            OPTIONAL {{ ?concept merged:synonym ?synonym }}
            OPTIONAL {{ ?concept merged:sourceA_label ?sourceA_label }}
            OPTIONAL {{ ?concept merged:sourceB_label ?sourceB_label }}
            OPTIONAL {{ ?concept merged:similarity_score ?similarity }}
        }}
        LIMIT 50
        """
        results = self.query_sparql(query)
        return self._format_equivalences(results)
    
    def get_relationships(self, concept1_name, concept2_name):
        """Trouve les relations entre deux concepts (hiérarchiques ET sémantiques)"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX merged: <http://example.org/merged-animal-ontology/>
        
        SELECT DISTINCT ?concept1 ?label1 ?relation ?concept2 ?label2 ?relationType
        FROM <{self.graph_uri}>
        WHERE {{
            ?concept1 rdfs:label ?label1 .
            ?concept2 rdfs:label ?label2 .
            
            FILTER(CONTAINS(LCASE(?label1), LCASE("{concept1_name}")))
            FILTER(CONTAINS(LCASE(?label2), LCASE("{concept2_name}")))
            
            {{
                # Relations hiérarchiques
                ?concept1 rdfs:subClassOf ?concept2 .
                BIND("hiérarchique (subClassOf)" AS ?relationType)
                BIND(rdfs:subClassOf AS ?relation)
            }} UNION {{
                # Relations inversées
                ?concept2 rdfs:subClassOf ?concept1 .
                BIND("hiérarchique (superClassOf)" AS ?relationType)
                BIND(rdfs:subClassOf AS ?relation)
            }} UNION {{
                # Partage des mêmes propriétés merged (synonymes communs)
                ?concept1 merged:synonym ?commonSynonym .
                ?concept2 merged:synonym ?commonSynonym .
                BIND("sémantique (synonyme partagé)" AS ?relationType)
                BIND(merged:synonym AS ?relation)
            }}
        }}
        LIMIT 20
        """
        results = self.query_sparql(query)
        return self.format_results(results)
    
    def get_graph_stats(self):
        """Récupère des statistiques complètes sur le knowledge graph enrichi"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX merged: <http://example.org/merged-animal-ontology/>
        
        SELECT 
            (COUNT(DISTINCT ?class) as ?totalClasses)
            (COUNT(DISTINCT ?synonym) as ?totalSynonyms)
            (COUNT(DISTINCT ?alignedConcept) as ?totalAlignedConcepts)
            (COUNT(DISTINCT ?sourceA) as ?totalFromSourceA)
            (COUNT(DISTINCT ?sourceB) as ?totalFromSourceB)
            (AVG(?score) as ?avgSimilarityScore)
        FROM <{self.graph_uri}>
        WHERE {{
            {{
                ?class a owl:Class .
            }} UNION {{
                ?s merged:synonym ?synonym .
            }} UNION {{
                ?alignedConcept merged:sourceA_label ?sourceA .
                ?alignedConcept merged:sourceB_label ?sourceB .
                OPTIONAL {{ ?alignedConcept merged:similarity_score ?score }}
            }}
        }}
        """
        results = self.query_sparql(query)
        
        # Formater les stats de manière lisible
        if "error" in results:
            return f"Erreur: {results['error']}"
        
        if results.get('results', {}).get('bindings'):
            stats = results['results']['bindings'][0]
            formatted = []
            formatted.append("\n📊 Statistiques du Knowledge Graph Enrichi")
            formatted.append("="*50)
            
            total_classes = int(stats.get('totalClasses', {}).get('value', 0))
            total_synonyms = int(stats.get('totalSynonyms', {}).get('value', 0))
            aligned = int(stats.get('totalAlignedConcepts', {}).get('value', 0))
            from_a = int(stats.get('totalFromSourceA', {}).get('value', 0))
            from_b = int(stats.get('totalFromSourceB', {}).get('value', 0))
            avg_score = stats.get('avgSimilarityScore', {}).get('value')
            
            formatted.append(f"\n🏷️  Classes totales: {total_classes}")
            formatted.append(f"📝 Synonymes totaux: {total_synonyms}")
            formatted.append(f"🔗 Concepts alignés (sources A+B): {aligned}")
            formatted.append(f"   • Provenant de Source A: {from_a}")
            formatted.append(f"   • Provenant de Source B: {from_b}")
            
            if avg_score:
                formatted.append(f"\n⭐ Score moyen de similarité: {float(avg_score):.4f}")
            
            # Calculer l'enrichissement
            if aligned > 0:
                enrichment_rate = (aligned / total_classes) * 100 if total_classes > 0 else 0
                formatted.append(f"\n💡 Taux d'enrichissement: {enrichment_rate:.1f}%")
                formatted.append(f"   ({aligned} concepts enrichis sur {total_classes} au total)")
            
            return "\n".join(formatted)
        
        return "Aucune statistique disponible."
    
    def search_by_parent(self, parent_name):
        """Trouve tous les sous-concepts d'un concept parent"""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?child ?childLabel ?parent ?parentLabel
        FROM <{self.graph_uri}>
        WHERE {{
            ?parent rdfs:label ?parentLabel .
            FILTER(CONTAINS(LCASE(?parentLabel), LCASE("{parent_name}")))
            
            ?child rdfs:subClassOf ?parent .
            OPTIONAL {{ ?child rdfs:label ?childLabel }}
        }}
        LIMIT 20
        """
        results = self.query_sparql(query)
        return self.format_results(results)
