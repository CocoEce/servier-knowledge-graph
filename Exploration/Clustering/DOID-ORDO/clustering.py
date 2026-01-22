import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize
import collections

# Configuration
EMBEDDINGS_FILE = "embeddings.npy"
METADATA_FILE = "metadata.csv"
OUTPUT_CLUSTERS = "mixed_clusters.csv" # Les alignements trouvés

# Seuil de distance (Plus il est bas, plus le clustering est strict)
# Pour des vecteurs normalisés (norme L2) :
# Distance 0.40 ~ Similarité Cosine 0.92 (Très strict)
# Distance 0.50 ~ Similarité Cosine 0.87 (Bon pour synonymes)
# Distance 0.60 ~ Similarité Cosine 0.82 (Accepte des variations plus larges)
DISTANCE_THRESHOLD = 0.50

print("🔄 Chargement des données...")
try:
    embeddings = np.load(EMBEDDINGS_FILE)
    df = pd.read_csv(METADATA_FILE)
except FileNotFoundError:
    print("❌ Erreur : Fichiers 'embeddings.npy' ou 'metadata.csv' introuvables.")
    exit()

print(f"📊 Données chargées : {len(df)} entités.")

# 1. Normalisation
# Crucial : Sur des vecteurs normalisés, la distance Euclidienne devient équivalente à la similarité Cosine.
print("📐 Normalisation des vecteurs...")
embeddings_norm = normalize(embeddings)

# 2. Clustering
print(f"🧩 Lancement du Clustering (Seuil={DISTANCE_THRESHOLD}, Linkage='average')...")
print("   (Cela peut prendre une minute pour ~30k éléments)")

# 'average' linkage est souvent plus stable que 'ward' pour grouper des synonymes sémantiques
clustering = AgglomerativeClustering(
    n_clusters=None,           # On laisse l'algo trouver le nombre de clusters
    distance_threshold=DISTANCE_THRESHOLD,
    metric='euclidean',
    linkage='average'
)

cluster_labels = clustering.fit_predict(embeddings_norm)
df['cluster_id'] = cluster_labels

# 3. Analyse des résultats
print("🔍 Analyse des clusters...")

# On compte la taille de chaque cluster
cluster_counts = collections.Counter(cluster_labels)

# On filtre pour ne garder que les clusters utiles (ceux qui contiennent au moins 2 éléments)
# (Les clusters de taille 1 sont des singletons qui n'ont matché avec rien)
interesting_clusters = [k for k, v in cluster_counts.items() if v > 1]
print(f"   -> {len(interesting_clusters)} groupes formés (taille > 1).")

# 4. Filtrage : On cherche les clusters MIXTES (Alignements)
# Un cluster "Mixte" contient au moins une entité DOID ET une entité ORDO.
mixed_clusters = []

print("🕵️  Recherche des alignements (DOID <-> ORDO)...")

# Pour optimiser, on groupe le dataframe par cluster_id
grouped = df[df['cluster_id'].isin(interesting_clusters)].groupby('cluster_id')

for cid, group in grouped:
    sources = group['source'].unique()
    
    # Si le cluster contient les deux sources, c'est un match !
    if 'DOID' in sources and 'ORDO' in sources:
        
        # On prépare une ligne de synthèse pour le CSV de sortie
        doid_rows = group[group['source'] == 'DOID']
        ordo_rows = group[group['source'] == 'ORDO']
        
        cluster_summary = {
            "cluster_id": cid,
            "size": len(group),
            "score_confiance": "High", # À affiner plus tard
            # On concatène les infos pour lecture humaine facile
            "doid_labels": " | ".join(doid_rows['label'].tolist()),
            "ordo_labels": " | ".join(ordo_rows['label'].tolist()),
            "doid_uris": " | ".join(doid_rows['uri'].tolist()),
            "ordo_uris": " | ".join(ordo_rows['uri'].tolist()),
            # Informations hiérarchiques pour multi-héritage (gestion des NaN)
            "doid_parent_labels": " | ".join(doid_rows['parent_labels'].fillna('').astype(str).tolist()),
            "ordo_parent_labels": " | ".join(ordo_rows['parent_labels'].fillna('').astype(str).tolist()),
            "doid_parent_uris": " | ".join(doid_rows['parent_uris'].fillna('').astype(str).tolist()),
            "ordo_parent_uris": " | ".join(ordo_rows['parent_uris'].fillna('').astype(str).tolist()),
            # On garde un exemple de texte riche pour l'étape LLM future
            "context_sample": doid_rows.iloc[0]['rich_text'][:200] + "..."
        }
        mixed_clusters.append(cluster_summary)

print(f"🎯 BINGO : {len(mixed_clusters)} alignements potentiels trouvés !")

# 5. Sauvegarde
if mixed_clusters:
    results_df = pd.DataFrame(mixed_clusters)
    # On trie par taille de cluster (les plus gros regroupements en premier ?)
    # Ou juste tel quel.
    results_df.to_csv(OUTPUT_CLUSTERS, index=False)
    print(f"💾 Résultats sauvegardés dans '{OUTPUT_CLUSTERS}'")
    print("   👉 Ouvre ce fichier pour voir les maladies que l'IA a jugées identiques.")
else:
    print("⚠️ Aucun cluster mixte trouvé. Essaie d'augmenter le DISTANCE_THRESHOLD (ex: 0.6).")