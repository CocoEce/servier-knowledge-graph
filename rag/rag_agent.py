import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from sparql_tools import SPARQLTools

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


class KnowledgeGraphRAG:
    """
    Agent RAG qui utilise des tools SPARQL pour interroger le knowledge graph
    d'ontologies alignées et Gemini pour générer des réponses en langage naturel.
    """
    
    def __init__(self, config_file="agent_configuration.json"):
        # Charger la configuration
        config_path = Path(__file__).parent / config_file
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.tools = SPARQLTools()
        model_name = self.config['agent']['model']
        self.model = genai.GenerativeModel(model_name)
        
        # Créer le mapping des tools depuis la configuration
        self.tool_mapping = {
            "get_all_classes": self.tools.get_all_classes,
            "search_concept": self.tools.search_concept,
            "get_concept_info": self.tools.get_concept_info,
            "find_equivalences": self.tools.find_equivalences,
            "get_relationships": self.tools.get_relationships,
            "get_graph_stats": self.tools.get_graph_stats,
            "search_by_parent": self.tools.search_by_parent
        }
    
    def select_tool(self, question):
        """Sélectionne le tool approprié basé sur les patterns de la configuration"""
        question_lower = question.lower()
        
        # Parcourir les patterns de questions et calculer les scores
        pattern_scores = []
        
        for pattern_name, pattern_config in self.config['question_patterns'].items():
            score = 0
            matches = 0
            
            for keyword in pattern_config['keywords']:
                if keyword in question_lower:
                    matches += 1
                    score += pattern_config.get('priority', 5)
            
            if matches > 0:
                pattern_scores.append((score, pattern_config['tool'], pattern_config['requires_concepts']))
        
        # Si on a des matches, prendre celui avec le meilleur score
        if pattern_scores:
            pattern_scores.sort(reverse=True)
            _, tool, required = pattern_scores[0]
            return tool, required
        
        # Par défaut, recherche
        return "search_concept", 1
    
    def extract_concepts(self, question):
        """Extrait les concepts mentionnés dans la question"""
        # Simple extraction basée sur des mots-clés
        words = question.split()
        concepts = []
        
        # Chercher les mots entre guillemets ou majuscules
        in_quotes = False
        current_concept = []
        
        for word in words:
            word_clean = word.strip('.,!?')
            
            # Gérer les guillemets
            if '"' in word or "'" in word:
                in_quotes = not in_quotes
                word_clean = word_clean.strip('"\'')
            
            # Capturer les mots en majuscule ou entre guillemets
            if in_quotes or (word_clean and word_clean[0].isupper() and len(word_clean) > 1):
                current_concept.append(word_clean)
            elif current_concept:
                concepts.append(' '.join(current_concept))
                current_concept = []
        
        if current_concept:
            concepts.append(' '.join(current_concept))
        
        return concepts if concepts else [question]
    
    def query(self, question):
        """Interroge le knowledge graph et génère une réponse"""
        print(f"\n🔍 Question: {question}")
        print("=" * 70)
        
        # Sélectionner le tool approprié
        tool_name, required_concepts = self.select_tool(question)
        print(f"📊 Tool sélectionné: {tool_name} (requiert {required_concepts} concept(s))")
        
        # Extraire les concepts
        concepts = self.extract_concepts(question)
        print(f"🎯 Concepts détectés: {concepts}")
        
        # Exécuter le tool approprié
        tool_func = self.tool_mapping[tool_name]
        
        try:
            if required_concepts == 2 and len(concepts) >= 2:
                sparql_results = tool_func(concepts[0], concepts[1])
            elif required_concepts == 1 and concepts:
                sparql_results = tool_func(concepts[0])
            else:
                sparql_results = tool_func()
            
            print(f"\n📋 Résultats SPARQL:")
            print(sparql_results[:500] + "..." if len(sparql_results) > 500 else sparql_results)
            
        except Exception as e:
            sparql_results = f"Erreur lors de l'exécution du tool: {str(e)}"
            print(f"\n❌ {sparql_results}")
        
        # Construire le prompt pour Gemini depuis la configuration
        system_prompt = self.config['prompts']['system_prompt']
        instructions = '\n- '.join(self.config['prompts']['instructions'])
        
        prompt = f"""{system_prompt}

Question de l'utilisateur: {question}

Données récupérées du knowledge graph:
{sparql_results}

Instructions:
- {instructions}

Réponse:"""
        
        # Générer la réponse avec Gemini
        print("\n🤖 Génération de la réponse...")
        response = self.model.generate_content(prompt)
        
        return response.text


def main():
    """Fonction de test"""
    rag = KnowledgeGraphRAG()
    
    print("\n" + "="*70)
    print("🧠 Knowledge Graph RAG - Système de Questions-Réponses")
    print("="*70)
    print("\nExemples de questions:")
    print("- Quelles sont les classes disponibles ?")
    print("- Donne-moi des informations sur Canis lupus")
    print("- Quel est le lien entre Canis lupus et Wolf ?")
    print("- Trouve les équivalents de Canis lupus")
    print("- Statistiques du knowledge graph")
    print("\nTapez 'quit' pour quitter\n")
    
    while True:
        question = input("\n💬 Votre question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Au revoir!")
            break
        
        if not question:
            continue
        
        try:
            answer = rag.query(question)
            print("\n" + "="*70)
            print("📝 Réponse:")
            print("="*70)
            print(answer)
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")


if __name__ == '__main__':
    main()
