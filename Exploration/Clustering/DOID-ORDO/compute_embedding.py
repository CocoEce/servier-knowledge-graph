import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import time

# Configuration
INPUT_CSV = "dataset_alignment.csv"
OUTPUT_EMBEDDINGS = "embeddings.npy"
OUTPUT_METADATA = "metadata.csv" # On resauvegarde le CSV propre aligné avec les vecteurs
MODEL_NAME = "all-MiniLM-L6-v2"

print(f"🔄 Chargement des données depuis {INPUT_CSV}...")
df = pd.read_csv(INPUT_CSV)

# Petit nettoyage : on s'assure que le texte est bien du string
df['rich_text'] = df['rich_text'].astype(str)

print(f"📊 Dataset chargé : {len(df)} lignes.")
print(f"🧠 Chargement du modèle BERT ({MODEL_NAME})...")

# Chargement du modèle (téléchargement auto au premier lancement)
model = SentenceTransformer(MODEL_NAME)

print("🚀 Démarrage de la vectorisation (cela peut prendre quelques minutes)...")
start_time = time.time()

# Encodage (batch_size gère la mémoire, show_progress_bar affiche la barre)
embeddings = model.encode(
    df['rich_text'].tolist(), 
    batch_size=64, 
    show_progress_bar=True,
    convert_to_numpy=True
)

end_time = time.time()
print(f"✅ Vectorisation terminée en {end_time - start_time:.2f} secondes.")
print(f"📐 Forme des vecteurs : {embeddings.shape} (Lignes, Dimensions)")

# Sauvegarde
print("💾 Sauvegarde des fichiers...")
np.save(OUTPUT_EMBEDDINGS, embeddings)
df.to_csv(OUTPUT_METADATA, index=False)

print("🎉 Terminé ! Tu es prêt pour le Clustering.")