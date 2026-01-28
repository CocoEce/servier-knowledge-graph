import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from sys import path as sys_path

# Load environment variables from root .env
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(env_path)

# Add Tools directory to Python path
tools_dir = Path(__file__).resolve().parent.parent / 'Tools'
sys_path.insert(0, str(tools_dir))

from sparql_tools import SPARQLTools

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurer Gemini
genai.configure(api_key=GEMINI_API_KEY)

class MedicalKnowledgeGraphRAG:
    """
    Agent RAG qui utilise des tools SPARQL pour interroger le graphe
    et Gemini pour générer des réponses.
    
    Sources de données:
    - WikiData: Entités générales, propriétés
    - PubChem: Composés chimiques
    - ChEBI: Structures chimiques, classifications
    """
    
    def __init__(self, config_file="agent_configuration.json"):
        # Charger la configuration
        config_path = Path(__file__).parent / config_file
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.tools = SPARQLTools()
        
        # Initialiser Gemini avec le modèle de la config
        model_name = self.config['agent']['model']
        self.model = genai.GenerativeModel(model_name)
        
        # Initialiser les tools
        self.tools_list = self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialise les tools en fonction de la configuration"""
        enabled_tools = self.config['tools']['enabled_tools']
        tool_descriptions = self.config['tools']['tool_descriptions']
        
        tools_dict = {}
        
        # Mapper les noms de tools aux fonctions - UNIQUEMENT les versions sans paramètre
        tool_mapping = {
            "get_all_patients": self.tools.get_all_patients,
            "get_all_drugs": self.tools.get_all_drugs,
            "get_all_diseases": self.tools.get_all_diseases,
            "get_all_symptoms": self.tools.get_all_symptoms,
            "get_all_relationships": self.tools.get_all_relationships,
            "get_count_stats": self.tools.get_count_stats,
        }
        
        for tool_name in enabled_tools:
            # Mapper les tools avec paramètres aux versions génériques sans paramètre
            mapped_tool = tool_name
            if tool_name.startswith("search_"):
                # search_patient_* → get_all_patients
                # search_disease_* → get_all_diseases
                # search_drug_* → get_all_drugs
                if "patient" in tool_name:
                    mapped_tool = "get_all_patients"
                elif "disease" in tool_name:
                    mapped_tool = "get_all_diseases"
                elif "drug" in tool_name:
                    mapped_tool = "get_all_drugs"
            elif "patient" in tool_name and tool_name not in tool_mapping:
                mapped_tool = "get_all_patients"
            elif "disease" in tool_name and tool_name not in tool_mapping:
                mapped_tool = "get_all_diseases"
            elif "drug" in tool_name and tool_name not in tool_mapping:
                mapped_tool = "get_all_drugs"
            elif "symptom" in tool_name and tool_name not in tool_mapping:
                mapped_tool = "get_all_symptoms"
            
            if mapped_tool in tool_mapping:
                tools_dict[tool_name] = {
                    "description": tool_descriptions.get(tool_name, ""),
                    "function": tool_mapping[mapped_tool]
                }
        
        return tools_dict
    
    def select_tools(self, question):
        """
        Sélectionne les tools à utiliser en fonction de la question
        Utilise les patterns de la configuration
        """
        question_lower = question.lower()
        patterns = self.config['tool_selection']['patterns']
        
        selected_tools = set()
        
        for pattern_name, pattern_config in patterns.items():
            keywords = pattern_config['keywords']
            # Vérifier si au moins un keyword est présent
            if any(keyword in question_lower for keyword in keywords):
                selected_tools.update(pattern_config['tools'])
        
        # Si aucun pattern ne correspond, utiliser les tools par défaut
        if not selected_tools:
            selected_tools = set(self.config['tools']['default_tools'] if 'default_tools' in self.config['tools'] else ["get_all_patients", "get_all_relationships"])
        
        return list(selected_tools)
    
    def execute_tools(self, tools_to_run, question):
        """Exécute les tools sélectionnés et retourne le contexte"""
        context_parts = []
        
        print(f"\n📊 Exécution des tools: {', '.join(tools_to_run)}")
        
        for tool_name in tools_to_run:
            if tool_name in self.tools_list:
                tool_func = self.tools_list[tool_name]['function']
                
                try:
                    # Tous les tools s'exécutent sans paramètre
                    # Ils retournent TOUS les résultats
                    result = tool_func()
                    
                    context_parts.append(f"--- {tool_name} ---\n{result}")
                except Exception as e:
                    context_parts.append(f"⚠️  Erreur avec {tool_name}: {str(e)}")
        
        context = "\n\n".join(context_parts)
        return context
    
    def answer_question(self, question):
        """Orchestre: sélection tools → exécution → génération réponse"""
        print(f"\n🤔 Question: {question}")
        
        # 1. Sélectionner les tools
        tools_to_run = self.select_tools(question)
        print(f"✅ Tools sélectionnés: {', '.join(tools_to_run)}")
        
        # 2. Exécuter les tools
        context = self.execute_tools(tools_to_run, question)
        
        # 3. Préparer le prompt pour Gemini
        system_prompt = self.config['prompts']['system_prompt']
        answer_instruction = self.config['prompts']['answer_instruction']
        context_prefix = self.config['prompts']['context_prefix']
        
        prompt = f"""{system_prompt}

{context_prefix}
{context}

Question: {question}

{answer_instruction}"""
        
        # 4. Appeler Gemini
        print("\n🚀 Appel de Gemini...")
        response = self.model.generate_content(prompt)
        
        return response.text


def main():
    """Interface en ligne de commande pour le RAG"""
    
    print("=" * 60)
    print("🏥 Knowledge Graph RAG - PFE Servier")
    print("=" * 60)
    print("\nCe système répond à vos questions en interrogeant")
    print("un graphe de connaissances via SPARQL.")
    print("Sources: WikiData, PubChem, ChEBI\n")
    
    rag = MedicalKnowledgeGraphRAG()
    
    # Questions d'exemple adaptées aux sources de données
    example_questions = [
        "Quels composés chimiques traitent le diabète?",
        "Quelles propriétés ont les molécules de WikiData?",
        "Combien de substances sont dans le graphe?",
        "Quels sont les synonymes chimiques disponibles?",
    ]
    
    print("Questions d'exemple:")
    for i, q in enumerate(example_questions, 1):
        print(f"  {i}. {q}")
    print()
    
    while True:
        question = input("💬 Votre question (ou 'quit' pour quitter): ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Au revoir!")
            break
        
        if not question:
            continue
        
        answer = rag.answer_question(question)
        
        print("\n" + "=" * 60)
        print("📝 RÉPONSE:")
        print("=" * 60)
        print(answer)
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
