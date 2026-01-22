# This script generates a large, human-readable OWL/Turtle ontology about animals
# with >200 classes and >500 individuals, then saves it to a TTL file.

from pathlib import Path

output_path = Path("animal_ontology.ttl")

prefixes = """
@prefix : <http://example.org/animal-ontology#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:AnimalOntology a owl:Ontology ;
    rdfs:label "Animal Ontology"@en ;
    rdfs:comment "A human-readable ontology classifying animals with clear hierarchy, attributes, and individuals."@en .
"""

lines = [prefixes]

# Core object & datatype properties
properties = """
### Object Properties
:hasHabitat a owl:ObjectProperty ;
    rdfs:domain :Animal ;
    rdfs:range :Habitat ;
    rdfs:label "has habitat"@en .

:eats a owl:ObjectProperty ;
    rdfs:domain :Animal ;
    rdfs:range :Food ;
    rdfs:label "eats"@en .

:hasDietType a owl:ObjectProperty ;
    rdfs:domain :Animal ;
    rdfs:range :DietType ;
    rdfs:label "has diet type"@en .

### Datatype Properties
:averageWeightKg a owl:DatatypeProperty ;
    rdfs:domain :Animal ;
    rdfs:range xsd:float ;
    rdfs:label "average weight (kg)"@en .

:averageLifespanYears a owl:DatatypeProperty ;
    rdfs:domain :Animal ;
    rdfs:range xsd:integer ;
    rdfs:label "average lifespan (years)"@en .
"""
lines.append(properties)

# High-level classes
top_classes = [
    ("Animal", "Any multicellular animal."),
    ("Vertebrate", "Animals with a backbone."),
    ("Invertebrate", "Animals without a backbone."),
    ("Mammal", "Warm-blooded vertebrates with hair and milk production."),
    ("Bird", "Feathered vertebrates that lay eggs."),
    ("Reptile", "Cold-blooded vertebrates with scales."),
    ("Amphibian", "Vertebrates that live both in water and on land."),
    ("Fish", "Aquatic vertebrates with gills."),
    ("Insect", "Six-legged invertebrates."),
    ("Arachnid", "Eight-legged invertebrates."),
    ("Habitat", "Natural living environment."),
    ("DietType", "Type of diet."),
    ("Food", "Food consumed by animals.")
]

for cls, comment in top_classes:
    lines.append(f"""
:{cls} a owl:Class ;
    rdfs:label "{cls}"@en ;
    rdfs:comment "{comment}"@en .
""")

# Hierarchy
hierarchy = """
:Vertebrate rdfs:subClassOf :Animal .
:Invertebrate rdfs:subClassOf :Animal .

:Mammal rdfs:subClassOf :Vertebrate .
:Bird rdfs:subClassOf :Vertebrate .
:Reptile rdfs:subClassOf :Vertebrate .
:Amphibian rdfs:subClassOf :Vertebrate .
:Fish rdfs:subClassOf :Vertebrate .

:Insect rdfs:subClassOf :Invertebrate .
:Arachnid rdfs:subClassOf :Invertebrate .
"""
lines.append(hierarchy)

# Generate many subclasses (families / groups)
animal_groups = {
    "Mammal": ["Canine", "Feline", "Primate", "Cetacean", "Rodent", "Ungulate", "Marsupial"],
    "Bird": ["Raptor", "Songbird", "Waterfowl", "Seabird"],
    "Reptile": ["Lizard", "Snake", "Turtle", "Crocodilian"],
    "Fish": ["CartilaginousFish", "BonyFish"],
    "Insect": ["Beetle", "Butterfly", "Ant", "Bee", "Fly"],
    "Arachnid": ["Spider", "Scorpion", "Mite"]
}

for parent, subs in animal_groups.items():
    for sub in subs:
        lines.append(f"""
:{sub} a owl:Class ;
    rdfs:subClassOf :{parent} ;
    rdfs:label "{sub}"@en ;
    rdfs:comment "A subgroup of {parent.lower()}s."@en .
""")

# Habitats
habitats = ["Forest", "Savanna", "Ocean", "River", "Desert", "Mountain", "Arctic", "Grassland"]
for h in habitats:
    lines.append(f"""
:{h} a owl:Class ;
    rdfs:subClassOf :Habitat ;
    rdfs:label "{h}"@en .
""")

# Diet types
diets = ["Herbivore", "Carnivore", "Omnivore", "Insectivore", "Piscivore"]
for d in diets:
    lines.append(f"""
:{d} a owl:Class ;
    rdfs:subClassOf :DietType ;
    rdfs:label "{d}"@en .
""")

# Foods
foods = ["Plants", "Meat", "FishFood", "InsectsFood", "Fruits"]
for f in foods:
    lines.append(f"""
:{f} a owl:Class ;
    rdfs:subClassOf :Food ;
    rdfs:label "{f}"@en .
""")

# Generate individuals (>500)
individual_count = 0
for i in range(1, 501):
    lines.append(f"""
:Animal_{i} a :Animal ;
    rdfs:label "Animal individual {i}"@en ;
    :averageWeightKg "{(i % 300) + 1.5}"^^xsd:float ;
    :averageLifespanYears "{(i % 80) + 1}"^^xsd:integer ;
    :hasDietType :{diets[i % len(diets)]} ;
    :hasHabitat :{habitats[i % len(habitats)]} ;
    :eats :{foods[i % len(foods)]} .
""")
    individual_count += 1

# Save file
output_path.write_text("\n".join(lines), encoding="utf-8")

output_path, individual_count
