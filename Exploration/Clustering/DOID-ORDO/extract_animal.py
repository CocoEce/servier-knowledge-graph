import gzip
import csv
import os
import sys

# Configuration
INPUT_FILE_GZ = 'mesh2024.nt.gz'
INPUT_FILE_NT = 'mesh2024.nt'
OUTPUT_FILE = 'mesh_animals.csv'

# Détection automatique du fichier : on cherche d'abord le .nt (décompressé), puis le .gz
if os.path.exists(INPUT_FILE_NT):
    input_path = INPUT_FILE_NT
    is_gzip = False
    print(f"📄 Fichier non-compressé trouvé : {input_path}")
elif os.path.exists(INPUT_FILE_GZ):
    input_path = INPUT_FILE_GZ
    is_gzip = True
    print(f"📦 Fichier compressé trouvé : {input_path}")
else:
    print(f"❌ Erreur : Aucun fichier trouvé ({INPUT_FILE_GZ} ou {INPUT_FILE_NT}).")
    print("👉 Assurez-vous d'être dans le bon dossier.")
    sys.exit(1)

print(f"Traitement de {input_path}...")

data_store = {}

def get_record(uri):
    if uri not in data_store:
        data_store[uri] = {'label': '', 'desc': '', 'tree_nums': [], 'is_animal': False}
    return data_store[uri]

count = 0

try:
    # Choix intelligent de la méthode d'ouverture
    opener = gzip.open if is_gzip else open
    
    with opener(input_path, 'rt', encoding='utf-8') as f:
        for line in f:
            count += 1
            if count % 2000000 == 0: print(f"Lignes lues : {count}...")

            parts = line.split(' ', 2)
            if len(parts) < 3: continue
            
            subject = parts[0]
            predicate = parts[1]
            obj = parts[2].rsplit(' .', 1)[0].replace('"', '')

            # 1. Filtrage sur la branche B (Organisms)
            if "treeNumber" in predicate:
                tree_code = obj.split('/')[-1].replace('>', '')
                # "B" pour Living Organisms
                if tree_code.startswith('B'):
                    record = get_record(subject)
                    record['is_animal'] = True
                    record['tree_nums'].append(tree_code)

            # 2. Label
            elif "label" in predicate and "@en" in obj:
                record = get_record(subject)
                record['label'] = obj
            
            # 3. Description
            elif "scopeNote" in predicate and "@en" in obj:
                record = get_record(subject)
                record['desc'] = obj

except gzip.BadGzipFile:
    print("\n❌ ERREUR CRITIQUE : Le fichier .gz est corrompu (c'est une page HTML).")
    print("👉 Solution : Supprimez le fichier 'mesh2024.nt.gz' et retéléchargez-le avec la commande ci-dessous.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Erreur inattendue : {e}")
    sys.exit(1)

print("Écriture du CSV...")
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['source', 'uri', 'label', 'rich_text']) 
    
    for uri, info in data_store.items():
        if info['is_animal'] and info['label']:
            # Construction du texte riche pour le MeSH
            rich_text = f"{info['label']}."
            if info['desc']: rich_text += f" Description: {info['desc']}"
            if info['tree_nums']: rich_text += f" Context: MeSH Category {info['tree_nums'][0]}"
            
            writer.writerow(["MESH", uri, info['label'], rich_text])

print(f"🎉 Terminé ! Fichier {OUTPUT_FILE} créé.")