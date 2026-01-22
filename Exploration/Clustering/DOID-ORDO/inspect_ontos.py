import sys
from owlready2 import *

# Augmenter la limite de récursion pour les grosses ontologies
sys.setrecursionlimit(20000)

print("--- Chargement des Ontologies (Patience...) ---")

# 1. Chargement de DOID (Human Disease)
try:
    print("Chargement de DOID...")
    doid = get_ontology("doid.owl").load()
    print(f"✅ DOID chargé. ({len(list(doid.classes()))} classes)")
except Exception as e:
    print(f"❌ Erreur DOID : {e}")

# 2. Chargement de ORDO (Orphanet)
try:
    print("Chargement de ORDO...")
    ordo = get_ontology("ordo.owl").load()
    print(f"✅ ORDO chargé. ({len(list(ordo.classes()))} classes)")
except Exception as e:
    print(f"❌ Erreur ORDO : {e}")

print("\n" + "="*50)

# Fonction pour inspecter une classe en détail
def inspect_random_class(onto, name):
    print(f"🔍 Inspection d'une classe au hasard dans {name}")
    
    # On prend une classe qui a un label (on ignore les nœuds anonymes)
    classes = [c for c in onto.classes() if c.label]
    if not classes:
        print("Aucune classe avec label trouvée.")
        return

    # On prend la 100ème pour éviter les racines trop abstraites
    target = classes[min(100, len(classes)-1)]
    
    print(f"📌 URI : {target.iri}")
    print(f"🏷️  Label : {target.label}")
    
    # Inspection des propriétés (Commentaires, Définitions...)
    print("📝 Propriétés d'annotation (Description, Synonymes...) :")
    
    # Correction : On itère sur les propriétés d'annotation de l'ontologie
    # au lieu d'appeler get_properties() sur la classe elle-même.
    found_any = False
    
    # 1. Vérifier les commentaires standards RDFS
    if target.comment:
        print(f"   - rdfs:comment : {target.comment}")
        found_any = True

    # 2. Vérifier toutes les autres propriétés d'annotation
    for prop in onto.annotation_properties():
        try:
            # On récupère les valeurs de cette propriété pour notre classe cible
            vals = prop[target]
            if vals:
                # Affichage propre (nom de la propriété + valeur tronquée)
                val_str = str(vals)
                if len(val_str) > 100: val_str = val_str[:100] + "..."
                
                # Récupération du label de la propriété pour comprendre ce que c'est (ex: 'has_exact_synonym')
                prop_label = prop.label[0] if prop.label else prop.name
                
                print(f"   - {prop_label} ({prop.name}) : {val_str}")
                found_any = True
        except:
            continue
            
    if not found_any:
        print("   (Aucune annotation trouvée)")
            
    # Inspection de la hiérarchie (Parents)
    print("🌳 Parents (Is-a) :")
    for parent in target.is_a:
        if hasattr(parent, 'label') and parent.label:
            print(f"   - {parent.label[0]} ({parent.name})")
        else:
            print(f"   - {parent}")
    
    print("="*50 + "\n")

# Lancer l'inspection
if 'doid' in locals(): inspect_random_class(doid, "DOID")
if 'ordo' in locals(): inspect_random_class(ordo, "ORDO")