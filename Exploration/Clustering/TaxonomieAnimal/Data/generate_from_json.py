import json
import os
from owlready2 import *

DATA_DIR = os.path.dirname(__file__)

def json_to_owl(json_path, owl_path):
    """Convert JSON taxonomy to OWL format"""
    
    # Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create ontology
    onto = get_ontology(data['ontology_iri'])
    
    with onto:
        # Define annotation properties
        class definition(AnnotationProperty):
            pass
        
        class hasExactSynonym(AnnotationProperty):
            pass
        
        # Create classes from JSON
        created_classes = {}
        
        for class_data in data['classes']:
            class_name = class_data['name']
            label = class_data['label']
            defn = class_data.get('definition', '')
            synonyms = class_data.get('synonyms', [])
            parent_name = class_data.get('parent')
            
            # Create class with proper parent
            if parent_name and parent_name in created_classes:
                parent_class = created_classes[parent_name]
                new_class = type(class_name, (parent_class,), {})
            else:
                new_class = type(class_name, (Thing,), {})
            
            created_classes[class_name] = new_class
            
            # Add label
            new_class.label = label
            
            # Add definition as annotation property
            if defn:
                definition[new_class].append(defn)
            
            # Add synonyms as annotation properties
            for syn in synonyms:
                hasExactSynonym[new_class].append(syn)
    
    # Save OWL
    onto.save(owl_path)
    print(f"✅ Created {owl_path}")

if __name__ == "__main__":
    json_a = os.path.join(DATA_DIR, 'taxonomy_A.json')
    json_b = os.path.join(DATA_DIR, 'taxonomy_B.json')
    owl_a = os.path.join(DATA_DIR, 'taxonomy_A.owl')
    owl_b = os.path.join(DATA_DIR, 'taxonomy_B.owl')
    
    print("Converting JSONs to OWL...")
    json_to_owl(json_a, owl_a)
    json_to_owl(json_b, owl_b)
    print("Done!")
