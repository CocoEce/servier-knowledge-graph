import streamlit as st
import sys
from pathlib import Path
import json

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from rag_agent import KnowledgeGraphRAG

# Configuration de la page
st.set_page_config(
    page_title="Knowledge Graph RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialiser l'agent RAG
@st.cache_resource
def get_rag_agent(use_llm=True):
    return KnowledgeGraphRAG(use_llm=use_llm)

# Charger la configuration pour les questions de démo
@st.cache_data
def load_config():
    config_path = Path(__file__).parent / "agent_configuration.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .demo-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sparql-results {
        background-color: #f8f9fa;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        border-radius: 0.3rem;
        font-family: monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# En-tête
st.markdown('<div class="main-header">🧠 Knowledge Graph RAG</div>', unsafe_allow_html=True)
st.markdown("### Système de questions-réponses sur le knowledge graph d'ontologies alignées")

# Mode sans LLM (fallback si quota dépassé)
use_llm = st.sidebar.checkbox("🤖 Utiliser LLM (décocher si quota dépassé)", value=True, 
                               help="Si décochée, retourne les résultats SPARQL bruts sans génération de texte")

# Initialisation
rag = get_rag_agent(use_llm=use_llm)
config = load_config()

# Initialiser l'historique
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.header("🎯 Questions de démo")
    
    st.divider()
    
    for i, q in enumerate(config['demo_questions'], 1):
        if st.button(f"{i}. {q}", key=f"demo_{i}_{q}", use_container_width=True):
            st.session_state.current_question = q
    
    st.divider()
    
    if st.button("🗑️ Effacer l'historique", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# Zone principale
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Posez votre question")
    
    # Input de question
    if 'current_question' in st.session_state:
        question = st.text_input(
            "Votre question:",
            value=st.session_state.current_question,
            key="question_input"
        )
        del st.session_state.current_question
    else:
        question = st.text_input(
            "Votre question:",
            placeholder="Ex: Quel est le lien entre Canis lupus et Wolf ?",
            key="question_input"
        )
    
    if st.button("🔍 Envoyer", type="primary", use_container_width=True):
        if question:
            with st.spinner("Interrogation du knowledge graph..."):
                try:
                    # Obtenir la réponse
                    answer = rag.query(question)
                    
                    # Ajouter à l'historique
                    st.session_state.history.append({
                        'question': question,
                        'answer': answer
                    })
                    
                    # Afficher la réponse
                    st.success("Réponse générée !")
                    
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")
        else:
            st.warning("Veuillez entrer une question")
    
    # Afficher l'historique
    if st.session_state.history:
        st.divider()
        st.header("📜 Historique des questions")
        
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"❓ {item['question']}", expanded=(i == 0)):
                st.markdown("**Réponse :**")
                st.markdown(item['answer'])

with col2:
    st.header("ℹ️ Informations")
    
    st.markdown("""
    **Tools SPARQL disponibles :**
    - 🔍 Recherche de concepts
    - 🔗 Recherche d'équivalences
    - 📊 Relations entre concepts
    - 📈 Statistiques du graphe
    - 🌳 Hiérarchie des classes
    """)
    
    st.divider()
    
    st.markdown("""
    **Configuration :**
    - **Modèle LLM :** Gemini 1.5 Flash
    - **Graph URI :** `knowledge_graph`
    - **Repository :** PFE-GraphDB
    """)
    
    st.divider()
    
    st.markdown("""
    **Exemples de patterns :**
    - "Quel est le lien entre X et Y ?"
    - "Trouve les équivalents de X"
    - "Donne-moi des infos sur X"
    - "Statistiques du graphe"
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🧠 Knowledge Graph RAG | Pipeline d'alignement d'ontologies
</div>
""", unsafe_allow_html=True)
