import sys
import csv
from owlready2 import *

# Configuration
TAXONOMY_A_PATH = "../Data/taxonomy_A.owl"
TAXONOMY_B_PATH = "../Data/taxonomy_B.owl"
OUTPUT_CSV = "dataset_alignment.csv"

# Augmenter la récursion pour OWL
sys.setrecursionlimit(20000)

data_rows = []

def get_definition(entity, onto):
    """
    Cherche la définition textuelle de manière robuste.
    Priorité : definition > rdfs:comment
    """
    # 1. Essayer la propriété 'definition'
    try:
        prop = onto.search_one(iri="*definition")
        if prop:
            vals = prop[entity]
            if vals:
                return str(vals[0])
    except:
        pass
    
    # 2. Fallback sur le commentaire standard
    if entity.comment:
        return str(entity.comment[0])
        
    return ""

def get_synonyms(entity, onto):
    """Récupère les synonymes exacts."""
    syns = []
    try:
        prop = onto.search_one(iri="*hasExactSynonym")
        if prop:
            for val in prop[entity]:
                syns.append(str(val))
    except:
        pass
    return syns

def get_individuals(cls, onto):
    """Récupère les individus (instances) d'une classe."""
    individuals = []
    try:
        # Récupérer les instances directes de la classe
        for ind in cls.instances():
            if hasattr(ind, 'name'):
                individuals.append(str(ind.name))
    except:
        pass
    return individuals

def process_ontology(path, source_name):
    print(f"🔄 Traitement de {source_name}...")
    try:
        onto = get_ontology(path).load()
    except Exception as e:
        print(f"⚠️ Impossible de charger {path} : {e}")
        return

    count = 0
    # On itère sur toutes les classes
    for cls in onto.classes():
        # On ignore les classes sans label
        if not cls.label: 
            continue
        
        try:
            label = str(cls.label[0])
            uri = str(cls.iri)
            definition = get_definition(cls, onto)
            synonyms = get_synonyms(cls, onto)
            individuals = get_individuals(cls, onto)
            
            # Récupération du contexte (Parents directs avec URIs)
            parents = []
            parent_uris = []
            try:
                for p in cls.is_a:
                    if hasattr(p, 'label') and p.label and hasattr(p, 'iri'):
                        parents.append(str(p.label[0]))
                        parent_uris.append(str(p.iri))
            except: 
                pass 
            
            # Construction du "Rich Text"
            rich_text = f"{label}."
            if definition:
                rich_text += f" Definition: {definition}"
            
            if synonyms:
                syn_str = ", ".join(synonyms)
                rich_text += f" Synonyms: {syn_str}."
            
            if individuals:
                ind_str = ", ".join(individuals[:5])  # Max 5 individus
                rich_text += f" Examples: {ind_str}."
                
            if parents:
                parent_str = ", ".join(parents[:3])
                rich_text += f" Context: Subclass of {parent_str}."
                
            # Ajout à la liste avec informations hiérarchiques complètes
            data_rows.append({
                "source": source_name,
                "uri": uri,
                "label": label,
                "definition": definition,
                "synonyms": "|".join(synonyms) if synonyms else "",
                "parent_labels": "|".join(parents),
                "parent_uris": "|".join(parent_uris),
                "rich_text": rich_text
            })
            count += 1
            
        except Exception as e:
            # On skip silencieusement les entités problématiques
            continue
    
    print(f"   ✅ {count} concepts extraits depuis {source_name}")

# Traitement des deux ontologies
print("🚀 Extraction des données des ontologies animales...\n")
process_ontology(TAXONOMY_A_PATH, "TAXONOMY_A")
process_ontology(TAXONOMY_B_PATH, "TAXONOMY_B")

# Sauvegarde dans un CSV
print(f"\n💾 Sauvegarde dans {OUTPUT_CSV}...")
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ["source", "uri", "label", "definition", "synonyms", 
                  "parent_labels", "parent_uris", "rich_text"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data_rows)

print(f"✅ Terminé ! {len(data_rows)} concepts au total sauvegardés.")
print(f"   📊 Répartition : TAXONOMY_A vs TAXONOMY_B")
