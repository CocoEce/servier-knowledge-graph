import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from sys import path as sys_path
from rag_agent import MedicalKnowledgeGraphRAG

# Load environment variables from root .env
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(env_path)

# Add Tools directory to Python path
tools_dir = Path(__file__).resolve().parent.parent / 'Tools'
sys_path.insert(0, str(tools_dir))

# Configuration de la page
st.set_page_config(
    page_title="Knowledge Graph RAG",
    page_icon="🏥",
    layout="wide"
)

# Initialiser le RAG
@st.cache_resource
def get_rag():
    return MedicalKnowledgeGraphRAG()

rag = get_rag()

# Interface
st.title("🏥 Knowledge Graph RAG - PFE Servier")
st.markdown("""
Posez des questions sur le graphe de connaissances. Le système interroge GraphDB via SPARQL 
et génère une réponse avec Google Gemini.

**Sources de données:** WikiData | PubChem | ChEBI
""")

# Sidebar avec des exemples
with st.sidebar:
    st.header("💡 Questions d'exemple")
    
    examples = [
        "Quels composés chimiques sont disponibles?",
        "Quelles sont les relations entre entités?",
        "Combien de substances dans le graphe?",
        "Quels synonymes pour cette molécule?",
        "Quelles propriétés WikiData sont disponibles?",
    ]
    
    for example in examples:
        if st.button(example, key=example):
            st.session_state.question = example

# Zone de question
question = st.text_input(
    "Votre question:",
    value=st.session_state.get('question', ''),
    placeholder="Ex: Quels composés chimiques sont disponibles?"
)

if st.button("🔍 Rechercher", type="primary") or question:
    if question:
        with st.spinner("Recherche en cours..."):
            
            # Récupérer la réponse
            answer = rag.answer_question(question)
            
            # Afficher la réponse
            st.markdown("### 📝 Réponse")
            st.success(answer)
    else:
        st.warning("Veuillez poser une question")

# Footer
st.markdown("---")
st.caption("Powered by GraphDB (SPARQL) + Google Gemini | Repository: PFE-SERVIER")
