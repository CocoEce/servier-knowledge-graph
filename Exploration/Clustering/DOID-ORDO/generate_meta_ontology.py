import pandas as pd
from owlready2 import *
import types

# Configuration
INPUT_CLUSTERS = "mixed_clusters.csv"
INPUT_ALL_CONCEPTS = "metadata.csv"
OUTPUT_OWL = "meta_ontology.owl"
META_IRI = "http://myproject.org/meta/"

print("🏗️  Chargement des clusters alignés...")
df = pd.read_csv(INPUT_CLUSTERS)
print(f"   -> {len(df)} concepts alignés à transformer en Meta-Classes.")

print("📚 Chargement de tous les concepts...")
all_concepts_df = pd.read_csv(INPUT_ALL_CONCEPTS)
print(f"   -> {len(all_concepts_df)} concepts au total (DOID + ORDO).")

# Création de l'ontologie vierge
onto = get_ontology(META_IRI)

with onto:
    # On définit les propriétés d'annotation pour stocker les liens vers les sources
    class hasSourceURI(AnnotationProperty):
        pass
    
    class hasOriginalLabel(AnnotationProperty):
        pass
    
    class hasSourceHierarchy(AnnotationProperty):
        """Indique la provenance d'une relation hiérarchique (DOID ou ORDO)"""
        pass

    # Classe racine de notre Meta-Ontologie
    class MetaDisease(Thing):
        label = "Disease (Meta Concept)"

    # Dictionnaire pour mémoriser les classes déjà créées (éviter les doublons)
    created_classes = {"MetaDisease": MetaDisease}
    
    def is_ancestor(potential_ancestor, potential_descendant):
        """Vérifie si potential_ancestor est un ancêtre de potential_descendant (évite les cycles)"""
        if potential_ancestor == potential_descendant:
            return True
        
        # Parcours des parents de potential_descendant
        if hasattr(potential_descendant, '__bases__'):
            for parent in potential_descendant.__bases__:
                if parent == potential_ancestor or is_ancestor(potential_ancestor, parent):
                    return True
        return False
    
    def get_or_create_meta_class(label, uri=None, parent_label=None, parent_uri=None):
        """Crée ou récupère une Meta-Class par son label"""
        safe_name = "Meta_" + "".join(x for x in label.title() if x.isalnum())
        
        if safe_name not in created_classes:
            # Création de la classe si elle n'existe pas (parent par défaut = MetaDisease)
            NewClass = types.new_class(safe_name, (MetaDisease,))
            NewClass.label = label
            if uri:
                NewClass.hasSourceURI.append(uri)
            created_classes[safe_name] = NewClass
        
        return created_classes[safe_name]
    
    count = 0
    
    for index, row in df.iterrows():
        try:
            # 1. Stratégie de Nommage (À remplacer par LLM plus tard)
            doid_lbls = str(row['doid_labels']).split(' | ')
            ordo_lbls = str(row['ordo_labels']).split(' | ')
            
            candidate_name = doid_lbls[0]  # Par défaut
            if len(ordo_lbls[0]) < len(candidate_name) and len(ordo_lbls[0]) > 3:
                candidate_name = ordo_lbls[0]
            
            class_name_safe = "Meta_" + "".join(x for x in candidate_name.title() if x.isalnum())
            
            # 2. Création de la Classe Meta avec multi-héritage
            # On commence avec MetaDisease comme parent par défaut
            parent_classes = set([MetaDisease])
            
            # Extraction des parents DOID
            doid_parent_labels = str(row.get('doid_parent_labels', '')).split('|')
            doid_parent_uris = str(row.get('doid_parent_uris', '')).split('|')
            
            for parent_label, parent_uri in zip(doid_parent_labels, doid_parent_uris):
                if parent_label and parent_label.strip():
                    parent_class = get_or_create_meta_class(parent_label.strip(), parent_uri.strip())
                    # Éviter les cycles : ne pas ajouter si c'est déjà un ancêtre
                    if parent_class != MetaDisease:
                        parent_classes.add(parent_class)
            
            # Extraction des parents ORDO
            ordo_parent_labels = str(row.get('ordo_parent_labels', '')).split('|')
            ordo_parent_uris = str(row.get('ordo_parent_uris', '')).split('|')
            
            for parent_label, parent_uri in zip(ordo_parent_labels, ordo_parent_uris):
                if parent_label and parent_label.strip():
                    parent_class = get_or_create_meta_class(parent_label.strip(), parent_uri.strip())
                    # Éviter les cycles
                    if parent_class != MetaDisease:
                        parent_classes.add(parent_class)
            
            # Si aucun parent spécifique, garder juste MetaDisease
            if len(parent_classes) == 1 and MetaDisease in parent_classes:
                final_parents = (MetaDisease,)
            else:
                # Retirer MetaDisease si on a d'autres parents (éviter la redondance)
                parent_classes.discard(MetaDisease)
                final_parents = tuple(parent_classes) if parent_classes else (MetaDisease,)
            
            # Vérifier qu'on ne crée pas la classe avec elle-même comme parent (cycle)
            if class_name_safe in created_classes:
                existing_class = created_classes[class_name_safe]
                # Ajouter les nouveaux parents via is_a plutôt que recréer
                for parent in final_parents:
                    if parent not in existing_class.is_a and not is_ancestor(existing_class, parent):
                        existing_class.is_a.append(parent)
                NewMetaClass = existing_class
            else:
                # Création de la classe avec tous ses parents (multi-héritage)
                NewMetaClass = types.new_class(class_name_safe, final_parents)
                NewMetaClass.label = candidate_name
                created_classes[class_name_safe] = NewMetaClass
            
            # 3. Ajout des Métadonnées avec provenance
            # Liens vers DOID avec annotation de provenance
            uris_doid = str(row['doid_uris']).split(' | ')
            for uri in uris_doid:
                if uri.strip():
                    NewMetaClass.seeAlso.append(uri)
                    NewMetaClass.hasSourceURI.append(uri)
            
            # Annotation de la hiérarchie DOID
            if any(doid_parent_labels):
                hierarchy_doid = f"DOID: {' → '.join([p for p in doid_parent_labels if p.strip()])}"
                NewMetaClass.hasSourceHierarchy.append(hierarchy_doid)
            
            # Liens vers ORDO avec annotation de provenance
            uris_ordo = str(row['ordo_uris']).split(' | ')
            for uri in uris_ordo:
                if uri.strip():
                    NewMetaClass.seeAlso.append(uri)
                    NewMetaClass.hasSourceURI.append(uri)
            
            # Annotation de la hiérarchie ORDO
            if any(ordo_parent_labels):
                hierarchy_ordo = f"ORDO: {' → '.join([p for p in ordo_parent_labels if p.strip()])}"
                NewMetaClass.hasSourceHierarchy.append(hierarchy_ordo)
                
            # On ajoute le contexte (définition) s'il existe
            if isinstance(row['context_sample'], str):
                NewMetaClass.comment.append(f"Context used for alignment: {row['context_sample'][:150]}...")

            count += 1
            
        except Exception as e:
            print(f"⚠️ Erreur sur la ligne {index} : {e}")
            continue
    
    print(f"✅ {count} Meta-Classes alignées créées.")
    
    # ============================================================
    # OPTION 2 : Ajouter tous les concepts non alignés (singletons)
    # ============================================================
    print("\n🔍 Ajout des concepts non alignés (singletons)...")
    
    # 1. Identifier les URIs déjà alignés
    aligned_uris = set()
    for index, row in df.iterrows():
        aligned_uris.update([u.strip() for u in str(row['doid_uris']).split(' | ') if u.strip()])
        aligned_uris.update([u.strip() for u in str(row['ordo_uris']).split(' | ') if u.strip()])
    
    print(f"   -> {len(aligned_uris)} concepts alignés identifiés.")
    
    # 2. Créer les classes pour les singletons
    singleton_count = 0
    for index, row in all_concepts_df.iterrows():
        if row['uri'] not in aligned_uris:
            try:
                label = str(row['label'])
                uri = str(row['uri'])
                source = str(row['source'])
                
                # Nom de classe sécurisé
                safe_name = "Meta_" + "".join(x for x in label.title() if x.isalnum())
                
                # Éviter les doublons (si le label existe déjà)
                if safe_name in created_classes:
                    safe_name = safe_name + "_" + source
                
                # Extraction des parents
                parent_labels = str(row.get('parent_labels', '')).split('|')
                parent_uris = str(row.get('parent_uris', '')).split('|')
                
                parent_classes = set()
                for parent_label, parent_uri in zip(parent_labels, parent_uris):
                    if parent_label and parent_label.strip():
                        parent_class = get_or_create_meta_class(parent_label.strip(), parent_uri.strip())
                        if parent_class != MetaDisease:
                            parent_classes.add(parent_class)
                
                # Parent par défaut
                final_parents = tuple(parent_classes) if parent_classes else (MetaDisease,)
                
                # Création de la classe singleton
                NewSingletonClass = types.new_class(safe_name, final_parents)
                NewSingletonClass.label = label
                NewSingletonClass.hasSourceURI.append(uri)
                
                # Annotation spéciale pour les singletons
                NewSingletonClass.comment.append(f"Source-only concept from {source} (not aligned)")
                
                # Hiérarchie source
                if any(parent_labels):
                    hierarchy = f"{source}: {' → '.join([p for p in parent_labels if p.strip()])}"
                    NewSingletonClass.hasSourceHierarchy.append(hierarchy)
                
                created_classes[safe_name] = NewSingletonClass
                singleton_count += 1
                
                if singleton_count % 5000 == 0:
                    print(f"   - {singleton_count} singletons traités...")
                
            except Exception as e:
                continue
    
    print(f"✅ {singleton_count} concepts singleton ajoutés.")
    print(f"📊 TOTAL : {count + singleton_count} Meta-Classes créées.")

print(f"💾 Sauvegarde dans {OUTPUT_OWL}...")
onto.save(file=OUTPUT_OWL, format="rdfxml")
print("🎉 PROJET TERMINÉ ! Tu as ton fichier OWL pivot complet.")