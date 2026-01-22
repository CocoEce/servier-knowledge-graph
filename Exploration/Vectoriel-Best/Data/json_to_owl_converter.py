"""
Script de conversion d'ontologies JSON vers OWL/RDF
Convertit les ontologies animales au format JSON vers le format OWL-XML

Usage:
    python json_to_owl_converter.py <fichier_json> [fichier_owl_sortie]
    
Exemple:
    python json_to_owl_converter.py ontologie_animaux_A.json
    python json_to_owl_converter.py ontologie_animaux_A.json animal_ontology_A.owl
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from xml.dom import minidom


def create_owl_header(ontology_info):
    """Crée l'en-tête OWL avec les namespaces"""
    rdf = Element('rdf:RDF', {
        'xmlns': ontology_info['iri'] + '#',
        'xml:base': ontology_info['iri'],
        'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'xmlns:rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xmlns:owl': 'http://www.w3.org/2002/07/owl#',
        'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema#',
        'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
        'xmlns:skos': 'http://www.w3.org/2004/02/skos/core#'
    })
    
    # Déclaration de l'ontologie
    ontology = SubElement(rdf, 'owl:Ontology', {'rdf:about': ontology_info['iri']})
    
    # Métadonnées de l'ontologie
    version = SubElement(ontology, 'owl:versionInfo')
    version.text = ontology_info.get('version', '1.0')
    
    title = SubElement(ontology, 'dc:title')
    title.text = ontology_info.get('name', 'Animal Ontology')
    
    description = SubElement(ontology, 'dc:description')
    description.text = ontology_info.get('description', '')
    
    created = SubElement(ontology, 'dc:created')
    created.text = datetime.now().isoformat()
    
    return rdf


def add_class_to_owl(rdf, class_data, ontology_iri, id_to_uri):
    """Ajoute une classe OWL au document"""
    class_uri = class_data['uri']
    
    # Déclaration de la classe
    owl_class = SubElement(rdf, 'owl:Class', {'rdf:about': class_uri})
    
    # Label
    label = SubElement(owl_class, 'rdfs:label', {'xml:lang': 'en'})
    label.text = class_data['label']
    
    # Définition
    if 'definition' in class_data and class_data['definition']:
        definition = SubElement(owl_class, 'rdfs:comment', {'xml:lang': 'en'})
        definition.text = class_data['definition']
    
    # Classe parente (subClassOf)
    if class_data.get('parent'):
        # Trouver l'URI du parent à partir de son ID
        parent_id = class_data['parent']
        parent_uri = id_to_uri.get(parent_id, f"{ontology_iri}#{parent_id}")
        subclass = SubElement(owl_class, 'rdfs:subClassOf', {
            'rdf:resource': parent_uri
        })
    
    # Synonymes (comme skos:altLabel)
    if 'synonyms' in class_data and class_data['synonyms']:
        for synonym in class_data['synonyms']:
            alt_label = SubElement(owl_class, 'skos:altLabel', {'xml:lang': 'en'})
            alt_label.text = synonym
    
    # Attributs (comme annotations)
    if 'attributes' in class_data and class_data['attributes']:
        for attr_key, attr_value in class_data['attributes'].items():
            annotation = SubElement(owl_class, f'rdfs:comment')
            annotation.text = f"{attr_key}: {attr_value}"


def add_individual_to_owl(rdf, individual_data, ontology_iri, id_to_uri):
    """Ajoute un individu OWL au document"""
    individual_uri = individual_data['uri']
    
    # Déclaration de l'individu
    individual = SubElement(rdf, 'owl:NamedIndividual', {'rdf:about': individual_uri})
    
    # Type (rdf:type)
    class_id = individual_data['type']
    class_uri = id_to_uri.get(class_id, f"{ontology_iri}#{class_id}")
    rdf_type = SubElement(individual, 'rdf:type', {
        'rdf:resource': class_uri
    })
    
    # Label
    label = SubElement(individual, 'rdfs:label', {'xml:lang': 'en'})
    label.text = individual_data['label']
    
    # Définition/Description
    if 'definition' in individual_data and individual_data['definition']:
        comment = SubElement(individual, 'rdfs:comment', {'xml:lang': 'en'})
        comment.text = individual_data['definition']
    
    # Attributs
    if 'attributes' in individual_data and individual_data['attributes']:
        for attr_key, attr_value in individual_data['attributes'].items():
            annotation = SubElement(individual, 'rdfs:comment')
            annotation.text = f"{attr_key}: {attr_value}"


def json_to_owl(json_file, owl_file=None):
    """
    Convertit un fichier JSON d'ontologie en fichier OWL
    
    Args:
        json_file: Chemin vers le fichier JSON d'entrée
        owl_file: Chemin vers le fichier OWL de sortie (optionnel)
    
    Returns:
        Chemin du fichier OWL créé
    """
    # Charger le JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Déterminer le nom du fichier de sortie
    if owl_file is None:
        input_path = Path(json_file)
        owl_file = input_path.parent / f"{input_path.stem}.owl"
    
    # Créer la structure OWL
    ontology_info = data['ontology']
    rdf = create_owl_header(ontology_info)
    ontology_iri = ontology_info['iri']
    
    # Créer un mapping id -> uri pour résoudre les références
    id_to_uri = {}
    for class_data in data.get('classes', []):
        id_to_uri[class_data['id']] = class_data['uri']
    
    # Ajouter les classes
    print(f"Ajout de {len(data.get('classes', []))} classes...")
    for class_data in data.get('classes', []):
        add_class_to_owl(rdf, class_data, ontology_iri, id_to_uri)
    
    # Ajouter les individus
    print(f"Ajout de {len(data.get('individuals', []))} individus...")
    for individual_data in data.get('individuals', []):
        add_individual_to_owl(rdf, individual_data, ontology_iri, id_to_uri)
    
    # Formater joliment le XML
    xml_string = tostring(rdf, encoding='unicode')
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
    
    # Écrire le fichier OWL
    with open(owl_file, 'wb') as f:
        f.write(pretty_xml)
    
    print(f"✓ Ontologie OWL créée: {owl_file}")
    print(f"  - Classes: {len(data.get('classes', []))}")
    print(f"  - Individus: {len(data.get('individuals', []))}")
    
    return owl_file


def convert_all_json_in_directory(directory='.'):
    """
    Convertit tous les fichiers JSON d'ontologie dans un répertoire
    
    Args:
        directory: Répertoire à scanner (par défaut: répertoire courant)
    """
    path = Path(directory)
    json_files = list(path.glob('ontologie_*.json'))
    
    if not json_files:
        print(f"Aucun fichier ontologie_*.json trouvé dans {directory}")
        return
    
    print(f"Conversion de {len(json_files)} fichier(s) JSON...\n")
    
    for json_file in json_files:
        print(f"Traitement de {json_file.name}...")
        try:
            json_to_owl(json_file)
            print()
        except Exception as e:
            print(f"✗ Erreur lors de la conversion de {json_file}: {e}\n")


def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Convertir un fichier spécifique:")
        print("    python json_to_owl_converter.py <fichier.json> [sortie.owl]")
        print("  Convertir tous les fichiers ontologie_*.json du répertoire courant:")
        print("    python json_to_owl_converter.py --all")
        print("\nExemples:")
        print("  python json_to_owl_converter.py ontologie_animaux_A.json")
        print("  python json_to_owl_converter.py ontologie_animaux_A.json custom_output.owl")
        print("  python json_to_owl_converter.py --all")
        sys.exit(1)
    
    if sys.argv[1] == '--all':
        convert_all_json_in_directory()
    else:
        json_file = sys.argv[1]
        owl_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not Path(json_file).exists():
            print(f"Erreur: Le fichier {json_file} n'existe pas")
            sys.exit(1)
        
        try:
            json_to_owl(json_file, owl_file)
        except Exception as e:
            print(f"Erreur lors de la conversion: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
