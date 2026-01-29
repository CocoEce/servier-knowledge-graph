"""
Script de mapping des ontologies OWL vers CSV
Extrait les classes, leurs propriétés, relations hiérarchiques et individus associés

Usage:
    python mapping_ontologie.py
"""

import csv
import json
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import SKOS
from collections import defaultdict


def load_ontology(owl_file):
    """Charge une ontologie OWL avec rdflib"""
    print(f"Chargement de {Path(owl_file).name}...")
    g = Graph()
    g.parse(owl_file, format='xml')
    return g


def get_text_values(graph, subject, predicates):
    """
    Récupère les valeurs textuelles pour un sujet et une liste de prédicats
    Gère les variations de noms d'attributs
    """
    values = []
    for predicate in predicates:
        for obj in graph.objects(subject, predicate):
            values.append(str(obj))
    return values


def extract_id_from_uri(uri):
    """Extrait un ID lisible depuis l'URI"""
    uri_str = str(uri)
    # Essayer d'extraire la dernière partie après / ou #
    if '/' in uri_str:
        return uri_str.split('/')[-1]
    elif '#' in uri_str:
        return uri_str.split('#')[-1]
    return uri_str


def get_label(graph, subject):
    """Récupère le label avec plusieurs variantes possibles"""
    label_predicates = [
        RDFS.label,
        Namespace("http://www.w3.org/2004/02/skos/core#").prefLabel,
    ]
    labels = get_text_values(graph, subject, label_predicates)
    return labels[0] if labels else extract_id_from_uri(subject)


def get_definition(graph, subject):
    """Récupère la définition avec plusieurs variantes possibles"""
    definition_predicates = [
        RDFS.comment,
        Namespace("http://purl.org/dc/elements/1.1/").description,
        Namespace("http://www.w3.org/2004/02/skos/core#").definition,
    ]
    definitions = get_text_values(graph, subject, definition_predicates)
    # Filtrer les commentaires qui sont des attributs (contiennent ":")
    clean_definitions = [d for d in definitions if ':' not in d or len(d) > 100]
    return clean_definitions[0] if clean_definitions else ""


def get_synonyms(graph, subject):
    """Récupère les synonymes avec plusieurs variantes possibles"""
    synonym_predicates = [
        SKOS.altLabel,
        Namespace("http://www.w3.org/2004/02/skos/core#").hiddenLabel,
    ]
    synonyms = get_text_values(graph, subject, synonym_predicates)
    return synonyms


def get_attributes(graph, subject):
    """Récupère les attributs additionnels (commentaires avec format key: value)"""
    attributes = {}
    for comment in graph.objects(subject, RDFS.comment):
        comment_str = str(comment)
        # Si le commentaire contient ":" et est court, c'est probablement un attribut
        if ':' in comment_str and len(comment_str) < 100:
            parts = comment_str.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                attributes[key] = value
    return attributes


def get_parent(graph, subject):
    """Récupère la classe parente avec son URI et label"""
    parents = list(graph.objects(subject, RDFS.subClassOf))
    if parents:
        parent_uri = parents[0]
        parent_label = get_label(graph, parent_uri)
        return {
            'label': parent_label,
            'uri': str(parent_uri)
        }
    return None


def get_children(graph, subject):
    """Récupère les classes enfants avec leurs URIs"""
    children = []
    for child in graph.subjects(RDFS.subClassOf, subject):
        if (child, RDF.type, OWL.Class) in graph:
            child_label = get_label(graph, child)
            children.append({
                'label': child_label,
                'uri': str(child)
            })
    return children


def get_individuals(graph, class_uri):
    """Récupère les individus d'une classe avec leur label et définition"""
    individuals = []
    
    for individual in graph.subjects(RDF.type, class_uri):
        # Vérifier que c'est bien un individu nommé
        if (individual, RDF.type, OWL.NamedIndividual) in graph:
            ind_label = get_label(graph, individual)
            ind_def = get_definition(graph, individual)
            
            # Format: "Label (Definition)" ou juste "Label" si pas de définition
            if ind_def:
                individuals.append(f"{ind_label} ({ind_def})")
            else:
                individuals.append(ind_label)
    
    return individuals


def extract_classes_from_ontology(owl_file):
    """
    Extrait toutes les informations des classes d'une ontologie
    
    Returns:
        Liste de dictionnaires contenant les informations de chaque classe
    """
    graph = load_ontology(owl_file)
    
    classes_data = []
    
    # Récupérer toutes les classes
    for class_uri in graph.subjects(RDF.type, OWL.Class):
        class_id = extract_id_from_uri(class_uri)
        label = get_label(graph, class_uri)
        definition = get_definition(graph, class_uri)
        synonyms = get_synonyms(graph, class_uri)
        parent = get_parent(graph, class_uri)
        attributes = get_attributes(graph, class_uri)
        children = get_children(graph, class_uri)
        individuals = get_individuals(graph, class_uri)
        
        # Rich text = label + definition
        rich_text = f"{label}. {definition}" if definition else label
        
        # Formater pour le CSV (on gardera le parsing pour MongoDB)
        parent_str = f"{parent['label']}|{parent['uri']}" if parent else ""
        enfants_str = ';'.join([f"{c['label']}|{c['uri']}" for c in children])
        attributes_str = ', '.join([f"{k}: {v}" for k, v in attributes.items()]) if attributes else ""
        
        class_info = {
            'id': class_id,
            'uri': str(class_uri),
            'label': label,
            'definition': definition,
            'synonyms': ';'.join(synonyms),
            'parent': parent_str,
            'attributes': attributes_str,
            'enfants': enfants_str,
            'individus': ';'.join(individuals),
            'rich_text': rich_text
        }
        
        classes_data.append(class_info)
    
    print(f"  → {len(classes_data)} classes extraites")
    return classes_data


def save_to_csv(classes_data, output_file):
    """Sauvegarde les données des classes dans un fichier CSV"""
    if not classes_data:
        print(f"Aucune donnée à sauvegarder dans {Path(output_file).name}")
        return
    
    fieldnames = ['id', 'uri', 'label', 'definition', 'synonyms', 'parent', 
                  'attributes', 'enfants', 'individus', 'rich_text']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(classes_data)
    
    print(f"✓ CSV créé : {Path(output_file).name}")
    print(f"  → {len(classes_data)} lignes écrites")


def main():
    """Fonction principale"""
    # Chemins des fichiers
    data_dir = Path(__file__).parent.parent / "data" / "owl"
    csv_dir = Path(__file__).parent.parent / "data" / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    owl_a = data_dir / "ontologie_animaux_A.owl"
    owl_b = data_dir / "ontologie_animaux_B.owl"
    
    csv_a = csv_dir / "ontologie_animaux_A.csv"
    csv_b = csv_dir / "ontologie_animaux_B.csv"
    
    # Vérifier que les fichiers OWL existent
    if not owl_a.exists():
        print(f"Erreur : {owl_a} n'existe pas")
        return
    if not owl_b.exists():
        print(f"Erreur : {owl_b} n'existe pas")
        return
    
    print("="*60)
    print("Extraction des ontologies vers CSV")
    print("="*60)
    
    # Traiter l'ontologie A
    print("\n1. Ontologie A")
    classes_a = extract_classes_from_ontology(owl_a)
    save_to_csv(classes_a, csv_a)
    
    # Traiter l'ontologie B
    print("\n2. Ontologie B")
    classes_b = extract_classes_from_ontology(owl_b)
    save_to_csv(classes_b, csv_b)
    
    print("\n" + "="*60)
    print("✓ Conversion terminée avec succès !")
    print("="*60)


if __name__ == '__main__':
    main()
