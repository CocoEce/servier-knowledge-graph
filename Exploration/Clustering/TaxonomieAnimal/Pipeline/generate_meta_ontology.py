import pandas as pd
from owlready2 import *
import types

# Configuration
INPUT_CLUSTERS = "animal_clusters.csv"
INPUT_ALL_CONCEPTS = "metadata.csv"
OUTPUT_OWL = "meta_animal_taxonomy.owl"
META_IRI = "http://example.org/meta_taxonomy#"

print("🏗️  Chargement des clusters alignés...")
df = pd.read_csv(INPUT_CLUSTERS)
print(f"   -> {len(df)} concepts alignés à transformer en Meta-Classes.")

print("📚 Chargement de tous les concepts...")
all_concepts_df = pd.read_csv(INPUT_ALL_CONCEPTS)
print(f"   -> {len(all_concepts_df)} concepts au total (TAXONOMY_A + TAXONOMY_B).")

# Création de l'ontologie vierge
onto = get_ontology(META_IRI)

with onto:
    # On définit les propriétés d'annotation pour stocker les liens vers les sources
    class hasSourceURI(AnnotationProperty):
        pass
    
    class hasOriginalLabel(AnnotationProperty):
        pass
    
    class hasSourceHierarchy(AnnotationProperty):
        """Indique la provenance d'une relation hiérarchique (TAXONOMY_A ou TAXONOMY_B)"""
        pass

    # Classe racine de notre Meta-Ontologie
    class MetaAnimal(Thing):
        label = "Animal (Meta Concept)"

    # Dictionnaire pour mémoriser les classes déjà créées (éviter les doublons)
    created_classes = {"MetaAnimal": MetaAnimal}
    
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
            # Création de la classe si elle n'existe pas (parent par défaut = MetaAnimal)
            NewClass = types.new_class(safe_name, (MetaAnimal,))
            NewClass.label = label
            if uri:
                NewClass.hasSourceURI.append(uri)
            created_classes[safe_name] = NewClass
        
        return created_classes[safe_name]
    
    count = 0
    
    for index, row in df.iterrows():
        try:
            # 1. Stratégie de Nommage
            taxonomy_a_lbls = str(row['taxonomy_a_labels']).split(' | ')
            taxonomy_b_lbls = str(row['taxonomy_b_labels']).split(' | ')
            
            # On choisit le label le plus court et pertinent
            candidate_name = taxonomy_a_lbls[0]  # Par défaut
            if len(taxonomy_b_lbls[0]) < len(candidate_name) and len(taxonomy_b_lbls[0]) > 3:
                candidate_name = taxonomy_b_lbls[0]
            
            class_name_safe = "Meta_" + "".join(x for x in candidate_name.title() if x.isalnum())
            
            # 2. Création de la Classe Meta avec multi-héritage
            # On commence avec MetaAnimal comme parent par défaut
            parent_classes = set([MetaAnimal])
            
            # Extraction des parents TAXONOMY_A
            taxonomy_a_parent_labels = str(row.get('taxonomy_a_parent_labels', '')).split('|')
            taxonomy_a_parent_uris = str(row.get('taxonomy_a_parent_uris', '')).split('|')
            
            for parent_label, parent_uri in zip(taxonomy_a_parent_labels, taxonomy_a_parent_uris):
                if parent_label and parent_label.strip():
                    parent_class = get_or_create_meta_class(parent_label.strip(), parent_uri.strip())
                    # Éviter les cycles : ne pas ajouter si c'est déjà un ancêtre
                    if parent_class != MetaAnimal:
                        parent_classes.add(parent_class)
            
            # Extraction des parents TAXONOMY_B
            taxonomy_b_parent_labels = str(row.get('taxonomy_b_parent_labels', '')).split('|')
            taxonomy_b_parent_uris = str(row.get('taxonomy_b_parent_uris', '')).split('|')
            
            for parent_label, parent_uri in zip(taxonomy_b_parent_labels, taxonomy_b_parent_uris):
                if parent_label and parent_label.strip():
                    parent_class = get_or_create_meta_class(parent_label.strip(), parent_uri.strip())
                    # Éviter les cycles
                    if parent_class != MetaAnimal:
                        parent_classes.add(parent_class)
            
            # Si aucun parent spécifique, garder juste MetaAnimal
            if len(parent_classes) == 1 and MetaAnimal in parent_classes:
                final_parents = (MetaAnimal,)
            else:
                # Retirer MetaAnimal si on a d'autres parents (éviter la redondance)
                parent_classes.discard(MetaAnimal)
                final_parents = tuple(parent_classes) if parent_classes else (MetaAnimal,)
            
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
            # Liens vers TAXONOMY_A avec annotation de provenance
            uris_taxonomy_a = str(row['taxonomy_a_uris']).split(' | ')
            for uri in uris_taxonomy_a:
                if uri.strip():
                    NewMetaClass.seeAlso.append(uri)
                    NewMetaClass.hasSourceURI.append(uri)
            
            # Annotation de la hiérarchie TAXONOMY_A
            if any(taxonomy_a_parent_labels):
                hierarchy_a = f"TAXONOMY_A: {' → '.join([p for p in taxonomy_a_parent_labels if p.strip()])}"
                NewMetaClass.hasSourceHierarchy.append(hierarchy_a)
            
            # Liens vers TAXONOMY_B avec annotation de provenance
            uris_taxonomy_b = str(row['taxonomy_b_uris']).split(' | ')
            for uri in uris_taxonomy_b:
                if uri.strip():
                    NewMetaClass.seeAlso.append(uri)
                    NewMetaClass.hasSourceURI.append(uri)
            
            # Annotation de la hiérarchie TAXONOMY_B
            if any(taxonomy_b_parent_labels):
                hierarchy_b = f"TAXONOMY_B: {' → '.join([p for p in taxonomy_b_parent_labels if p.strip()])}"
                NewMetaClass.hasSourceHierarchy.append(hierarchy_b)
                
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
        aligned_uris.update([u.strip() for u in str(row['taxonomy_a_uris']).split(' | ') if u.strip()])
        aligned_uris.update([u.strip() for u in str(row['taxonomy_b_uris']).split(' | ') if u.strip()])
    
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
                        if parent_class != MetaAnimal:
                            parent_classes.add(parent_class)
                
                # Parent par défaut
                final_parents = tuple(parent_classes) if parent_classes else (MetaAnimal,)
                
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
                
                if singleton_count % 50 == 0:
                    print(f"   - {singleton_count} singletons traités...")
                
            except Exception as e:
                continue
    
    print(f"✅ {singleton_count} concepts singleton ajoutés.")
    print(f"📊 TOTAL : {count + singleton_count} Meta-Classes créées.")

print(f"💾 Sauvegarde dans {OUTPUT_OWL}...")
onto.save(file=OUTPUT_OWL, format="rdfxml")
print("🎉 TERMINÉ ! Meta-ontologie animale créée avec succès.")
