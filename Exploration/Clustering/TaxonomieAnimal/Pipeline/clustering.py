import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize
import collections

# Configuration
EMBEDDINGS_FILE = "embeddings.npy"
METADATA_FILE = "metadata.csv"
OUTPUT_CLUSTERS = "animal_clusters.csv"  # Les alignements trouvés

# Seuil de distance (Plus il est bas, plus le clustering est strict)
# Pour des vecteurs normalisés (norme L2) :
# Distance 0.40 ~ Similarité Cosine 0.92 (Très strict)
# Distance 0.50 ~ Similarité Cosine 0.87 (Bon pour synonymes)
# Distance 0.60 ~ Similarité Cosine 0.82 (Accepte des variations plus larges)
# Distance 0.70 ~ Similarité Cosine 0.75 (Très permissif)
# Distance 0.80 ~ Similarité Cosine 0.64 (Ultra permissif)
DISTANCE_THRESHOLD = 0.80  # Très permissif pour matcher concepts similaires

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
# Un cluster "Mixte" contient au moins une entité TAXONOMY_A ET une entité TAXONOMY_B.
mixed_clusters = []

print("🕵️  Recherche des alignements (TAXONOMY_A <-> TAXONOMY_B)...")

# Pour optimiser, on groupe le dataframe par cluster_id
grouped = df[df['cluster_id'].isin(interesting_clusters)].groupby('cluster_id')

# Debug : voir la composition des premiers clusters
debug_clusters = 0
for cid, group in grouped:
    sources = group['source'].unique()
    
    # Debug info sur les premiers clusters
    if debug_clusters < 5:
        source_counts = dict(pd.Series(sources).value_counts())
        print(f"   Cluster {cid} : {source_counts} | Labels: {group['label'].tolist()[:3]}")
        debug_clusters += 1
    
    # Si le cluster contient les deux sources, c'est un match !
    if 'TAXONOMY_A' in sources and 'TAXONOMY_B' in sources:
        
        # On prépare une ligne de synthèse pour le CSV de sortie
        taxonomy_a_rows = group[group['source'] == 'TAXONOMY_A']
        taxonomy_b_rows = group[group['source'] == 'TAXONOMY_B']
        
        cluster_summary = {
            "cluster_id": cid,
            "size": len(group),
            "score_confiance": "High",  # À affiner plus tard
            # On concatène les infos pour lecture humaine facile
            "taxonomy_a_labels": " | ".join(taxonomy_a_rows['label'].tolist()),
            "taxonomy_b_labels": " | ".join(taxonomy_b_rows['label'].tolist()),
            "taxonomy_a_uris": " | ".join(taxonomy_a_rows['uri'].tolist()),
            "taxonomy_b_uris": " | ".join(taxonomy_b_rows['uri'].tolist()),
            # Informations hiérarchiques pour multi-héritage (gestion des NaN)
            "taxonomy_a_parent_labels": " | ".join(taxonomy_a_rows['parent_labels'].fillna('').astype(str).tolist()),
            "taxonomy_b_parent_labels": " | ".join(taxonomy_b_rows['parent_labels'].fillna('').astype(str).tolist()),
            "taxonomy_a_parent_uris": " | ".join(taxonomy_a_rows['parent_uris'].fillna('').astype(str).tolist()),
            "taxonomy_b_parent_uris": " | ".join(taxonomy_b_rows['parent_uris'].fillna('').astype(str).tolist()),
            # On garde un exemple de texte riche pour analyse future
            "context_sample": taxonomy_a_rows.iloc[0]['rich_text'][:200] + "..."
        }
        mixed_clusters.append(cluster_summary)

print(f"🎯 BINGO : {len(mixed_clusters)} alignements potentiels trouvés !")

# 5. Sauvegarde
if mixed_clusters:
    df_clusters = pd.DataFrame(mixed_clusters)
    df_clusters.to_csv(OUTPUT_CLUSTERS, index=False)
    print(f"💾 Résultats sauvegardés dans {OUTPUT_CLUSTERS}")
    
    # Petit aperçu
    print("\n📋 Aperçu des premiers alignements :")
    for i, row in df_clusters.head(5).iterrows():
        print(f"   Cluster {row['cluster_id']}: {row['taxonomy_a_labels']} <-> {row['taxonomy_b_labels']}")
else:
    print("⚠️ Aucun alignement trouvé. Essayez d'augmenter le DISTANCE_THRESHOLD.")

print("\n✨ Clustering terminé !")
