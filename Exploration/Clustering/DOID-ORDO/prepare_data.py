import sys
import csv
from owlready2 import *

# Configuration
DOID_PATH = "doid.owl"
ORDO_PATH = "ordo.owl"
OUTPUT_CSV = "dataset_alignment.csv"

# Augmenter la récursion pour OWL (nécessaire pour les grosses ontologies)
sys.setrecursionlimit(20000)

data_rows = []

def get_definition(entity, onto):
    """
    Cherche la définition textuelle de manière robuste.
    Priorité : IAO_0000115 (Standard OBO) > rdfs:comment
    """
    # 1. Essayer la propriété standard OBO 'definition' ou 'IAO_0000115'
    props_to_check = ["IAO_0000115", "definition", "def"]
    
    for prop_name in props_to_check:
        try:
            prop = onto.search_one(iri=f"*{prop_name}")
            if prop:
                vals = prop[entity]
                if vals:
                    return str(vals[0])
        except:
            continue
    
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
        # On ignore les classes sans label ou obsolètes
        if not cls.label: continue
        
        # 1. Récupération des infos de base
        # On utilise une gestion d'erreur pour éviter les plantages sur des caractères bizarres
        try:
            label = str(cls.label[0])
            uri = str(cls.iri)
            definition = get_definition(cls, onto)
            synonyms = get_synonyms(cls, onto)
            
            # 2. Récupération du contexte (Parents directs avec URIs)
            parents = []
            parent_uris = []
            try:
                for p in cls.is_a:
                    if hasattr(p, 'label') and p.label and hasattr(p, 'iri'):
                        parents.append(str(p.label[0]))
                        parent_uris.append(str(p.iri))
            except: pass 
            
            # 3. Construction du "Rich Text"
            rich_text = f"{label}."
            if definition:
                rich_text += f" Definition: {definition}"
            
            if synonyms:
                syn_str = ", ".join(synonyms)
                rich_text += f" Synonyms: {syn_str}."
                
            if parents:
                parent_str = ", ".join(parents[:3])
                rich_text += f" Context: Subclass of {parent_str}."
                
            # Ajout à la liste avec informations hiérarchiques complètes
            data_rows.append({
                "source": source_name,
                "uri": uri,
                "label": label,
                "rich_text": rich_text,
                "parent_labels": "|".join(parents) if parents else "",
                "parent_uris": "|".join(parent_uris) if parent_uris else ""
            })
            
            count += 1
            if count % 1000 == 0:
                print(f"   - {count} classes traitées pour {source_name}")

        except Exception as e:
            # On ignore juste la classe qui pose problème pour ne pas arrêter le script
            continue

    print(f"✅ Terminé pour {source_name} : {count} classes extraites.")

# --- Exécution ---
print("🚀 Démarrage de l'extraction des données...")

# Vérification de l'existence des fichiers
import os
if not os.path.exists(DOID_PATH) or not os.path.exists(ORDO_PATH):
    print(f"❌ ERREUR : Les fichiers {DOID_PATH} ou {ORDO_PATH} sont introuvables.")
    print("Assurez-vous d'avoir téléchargé les fichiers .owl dans ce dossier.")
else:
    process_ontology(DOID_PATH, "DOID")
    process_ontology(ORDO_PATH, "ORDO")

    print(f"💾 Sauvegarde dans {OUTPUT_CSV}...")
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["source", "uri", "label", "rich_text", "parent_labels", "parent_uris"])
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"🎉 Terminé ! Dataset prêt avec {len(data_rows)} lignes.")
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture du CSV : {e}")