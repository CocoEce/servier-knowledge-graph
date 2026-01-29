import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from sparql_tools import SPARQLTools

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Configuration OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class KnowledgeGraphRAG:
    """
    Agent RAG qui utilise des tools SPARQL pour interroger le knowledge graph
    d'ontologies alignées et OpenAI pour générer des réponses en langage naturel.
    Utilise le function calling natif d'OpenAI pour sélectionner les tools et extraire les paramètres.
    """
    
    def __init__(self, config_file="agent_configuration.json", use_llm=True):
        # Charger la configuration
        config_path = Path(__file__).parent / config_file
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.tools = SPARQLTools()
        self.use_llm = use_llm
        
        # Créer le mapping des tools
        self.tool_mapping = {
            "get_all_classes": self.tools.get_all_classes,
            "search_concept": self.tools.search_concept,
            "get_concept_info": self.tools.get_concept_info,
            "find_equivalences": self.tools.find_equivalences,
            "get_relationships": self.tools.get_relationships,
            "get_graph_stats": self.tools.get_graph_stats,
            "search_by_parent": self.tools.search_by_parent
        }
        
        if use_llm:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model_name = self.config['agent']['model']
            self.tools_definitions = self._create_tools_definitions()
        else:
            self.client = None
    
    def _create_tools_definitions(self):
        """Crée les définitions de tools pour OpenAI function calling"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_concept",
                    "description": "Recherche un concept spécifique par son nom (ex: Lion, Tiger, Carnivore). Utilise ce tool pour obtenir toutes les informations disponibles sur un concept : synonymes, définitions, attributs, propriétés.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "concept_name": {
                                "type": "string",
                                "description": "Le nom du concept à rechercher (ex: 'Lion', 'Tiger', 'Carnivore')"
                            }
                        },
                        "required": ["concept_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_equivalences",
                    "description": "Trouve les concepts équivalents ou similaires à un concept donné. Utilise pour trouver les alignements entre ontologies (sourceA vs sourceB).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "concept_name": {
                                "type": "string",
                                "description": "Le nom du concept pour lequel trouver des équivalences"
                            }
                        },
                        "required": ["concept_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_relationships",
                    "description": "Trouve les relations entre deux concepts spécifiques (hiérarchie, liens sémantiques).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "concept1": {
                                "type": "string",
                                "description": "Le premier concept"
                            },
                            "concept2": {
                                "type": "string",
                                "description": "Le second concept"
                            }
                        },
                        "required": ["concept1", "concept2"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_by_parent",
                    "description": "Trouve tous les sous-concepts (enfants, descendants) d'un concept parent donné.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "parent_name": {
                                "type": "string",
                                "description": "Le nom du concept parent"
                            }
                        },
                        "required": ["parent_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_classes",
                    "description": "Récupère la liste de toutes les classes disponibles dans le knowledge graph.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_graph_stats",
                    "description": "Récupère des statistiques sur le knowledge graph (nombre de classes, alignements, enrichissement).",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
        return tools
    
    def query(self, question):
        """Interroge le knowledge graph et génère une réponse"""
        print(f"\n🔍 Question: {question}")
        print("=" * 70)
        
        if not self.use_llm:
            # Mode sans LLM - utiliser l'ancien système de pattern matching
            return self._query_without_llm(question)
        
        # Construire le prompt système
        system_instruction = self.config['prompts']['system_prompt']
        instructions = '\n- '.join(self.config['prompts']['instructions'])
        
        system_message = f"{system_instruction}\n\nInstructions:\n- {instructions}"
        
        # Première phase : laisser OpenAI choisir les tools
        print("🤖 OpenAI analyse la question et sélectionne les tools...")
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": question}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=self.tools_definitions,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if not tool_calls:
            # Pas de tool call - réponse directe
            return response_message.content
        
        # Exécuter les tool calls
        print(f"📊 Tools sélectionnés par OpenAI: {[tc.function.name for tc in tool_calls]}")
        
        # Ajouter le message de l'assistant avec les tool calls
        messages.append(response_message)
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"🎯 Exécution de {tool_name} avec paramètres: {args}")
            
            # Exécuter le tool
            try:
                tool_func = self.tool_mapping[tool_name]
                
                # Appeler avec les bons arguments
                if tool_name == "get_relationships":
                    result = tool_func(args.get('concept1'), args.get('concept2'))
                elif tool_name in ["search_concept", "find_equivalences"]:
                    result = tool_func(args.get('concept_name'))
                elif tool_name == "search_by_parent":
                    result = tool_func(args.get('parent_name'))
                else:
                    result = tool_func()
                
                print(f"\n📋 Résultat de {tool_name}:")
                print(result[:500] + "..." if len(result) > 500 else result)
                
                # Ajouter le résultat du tool à la conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result
                })
                
            except Exception as e:
                error_msg = f"Erreur lors de l'exécution de {tool_name}: {str(e)}"
                print(f"❌ {error_msg}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": error_msg
                })
        
        # Envoyer les résultats à OpenAI pour générer la réponse finale
        print("\n🤖 Génération de la réponse finale...")
        
        try:
            final_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            
            return final_response.choices[0].message.content
            
        except Exception as e:
            print(f"\n⚠️  Erreur OpenAI : {str(e)}")
            # Retourner les résultats bruts
            tool_results = [msg['content'] for msg in messages if msg.get('role') == 'tool']
            return "\n\n".join(tool_results)
    
    def _query_without_llm(self, question):
        """Version sans LLM - utilise le pattern matching basique"""
        # Code de l'ancien système
        question_lower = question.lower()
        
        # Pattern matching simple
        if any(kw in question_lower for kw in ['statistique', 'combien', 'nombre']):
            return self.tools.get_graph_stats()
        elif any(kw in question_lower for kw in ['liste', 'toutes les classes', 'tous les concepts']):
            return self.tools.get_all_classes()
        else:
            # Par défaut : recherche de concept
            # Extraire un mot significatif (> 3 lettres, pas un stopword)
            stopwords = {'quel', 'quels', 'quelle', 'donne', 'info', 'sur', 'pour', 'dans', 'toutes', 'tous'}
            words = [w.strip('.,!?') for w in question.split() if len(w) > 3 and w.lower() not in stopwords]
            if words:
                return self.tools.search_concept(words[0])
            return "Aucun concept détecté dans la question."


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
