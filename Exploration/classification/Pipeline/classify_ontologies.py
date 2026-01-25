"""
Script pour classifier les classes de l'ontologie B sur l'ontologie A
en entraînant un modèle de classification supervisé
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from typing import List, Dict, Tuple
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


class OntologyClassifier:
    """Classe pour classifier les classes d'une ontologie sur une autre avec un modèle entraîné"""
    
    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2', 
                 classifier_type: str = 'random_forest'):
        """
        Initialise le classificateur
        
        Args:
            embedding_model: Nom du modèle pour générer les embeddings des attributs
            classifier_type: Type de classificateur ('random_forest', 'neural_net')
        """
        print(f"Chargement du modèle d'embedding {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)
        print("✓ Modèle d'embedding chargé")
        
        self.classifier_type = classifier_type
        self.classifier = None
        self.label_encoder = LabelEncoder()
        
        self.classes_a = None
        self.classes_b = None
        self.X_train = None
        self.y_train = None
        
    def load_classes(self, classes_a_path: str, classes_b_path: str):
        """
        Charge les classes des deux ontologies depuis des fichiers JSON
        
        Args:
            classes_a_path: Chemin vers le JSON des classes de l'ontologie A
            classes_b_path: Chemin vers le JSON des classes de l'ontologie B
        """
        with open(classes_a_path, 'r', encoding='utf-8') as f:
            self.classes_a = json.load(f)
        
        with open(classes_b_path, 'r', encoding='utf-8') as f:
            self.classes_b = json.load(f)
        
        print(f"✓ Chargé {len(self.classes_a)} classes de l'ontologie A")
        print(f"✓ Chargé {len(self.classes_b)} classes de l'ontologie B")
    
    def _extract_features(self, class_info: Dict) -> np.ndarray:
        """
        Extrait les features d'une classe en vectorisant ses attributs
        
        Args:
            class_info: Dictionnaire contenant les informations de la classe
            
        Returns:
            Vecteur de features
        """
        # Créer une représentation textuelle complète de la classe
        text_representation = class_info['full_description']
        
        # Générer l'embedding
        embedding = self.embedding_model.encode(text_representation, show_progress_bar=False)
        
        return embedding
    
    def _augment_data(self, class_info: Dict, n_augmentations: int = 5) -> List[str]:
        """
        Augmente les données en créant des variations de la description
        
        Args:
            class_info: Information de la classe
            n_augmentations: Nombre de variations à créer
            
        Returns:
            Liste de descriptions variées
        """
        base_text = class_info['full_description']
        variations = [base_text]
        
        # Variation 1: Utiliser seulement le label et les commentaires
        if class_info['comments']:
            variations.append(f"{class_info['label']} {' '.join(class_info['comments'])}")
        
        # Variation 2: Utiliser seulement les synonymes
        if class_info['synonyms']:
            variations.append(f"{class_info['label']} {' '.join(class_info['synonyms'])}")
        
        # Variation 3: Mélanger label et quelques synonymes
        if len(class_info['synonyms']) >= 2:
            variations.append(f"{class_info['label']} {class_info['synonyms'][0]}")
        
        # Variation 4: Commentaires principaux
        if len(class_info['comments']) >= 1:
            variations.append(f"{class_info['label']} {class_info['comments'][0]}")
        
        # Variation 5: Label seul (pour tester la robustesse)
        variations.append(class_info['label'])
        
        return variations[:n_augmentations]
    
    def train_model(self, use_augmentation: bool = True):
        """
        Entraîne le modèle de classification sur les classes de A
        
        Args:
            use_augmentation: Si True, augmente les données d'entraînement
        """
        print(f"\n🔧 Entraînement du modèle de classification...")
        print(f"   Augmentation de données: {'OUI' if use_augmentation else 'NON'}")
        
        X_train_list = []
        y_train_list = []
        
        # Préparer les données d'entraînement
        for class_a in self.classes_a:
            class_name = class_a['name']
            
            if use_augmentation:
                # Créer plusieurs exemples par classe
                variations = self._augment_data(class_a, n_augmentations=5)
                for variation in variations:
                    embedding = self.embedding_model.encode(variation, show_progress_bar=False)
                    X_train_list.append(embedding)
                    y_train_list.append(class_name)
            else:
                # Un seul exemple par classe
                embedding = self._extract_features(class_a)
                X_train_list.append(embedding)
                y_train_list.append(class_name)
        
        self.X_train = np.array(X_train_list)
        self.y_train = np.array(y_train_list)
        
        # Encoder les labels
        self.y_train_encoded = self.label_encoder.fit_transform(self.y_train)
        
        print(f"   Données d'entraînement: {self.X_train.shape[0]} exemples, {self.X_train.shape[1]} features")
        print(f"   Nombre de classes: {len(self.label_encoder.classes_)}")
        
        # Créer et entraîner le classificateur
        if self.classifier_type == 'random_forest':
            self.classifier = RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            )
        elif self.classifier_type == 'neural_net':
            from sklearn.neural_network import MLPClassifier
            self.classifier = MLPClassifier(
                hidden_layer_sizes=(256, 128, 64),
                activation='relu',
                solver='adam',
                max_iter=500,
                random_state=42,
                early_stopping=True
            )
        
        print(f"   Classificateur: {self.classifier_type}")
        self.classifier.fit(self.X_train, self.y_train_encoded)
        
        # Évaluer avec validation croisée (si possible)
        if use_augmentation and len(self.classes_a) > 3:
            try:
                cv_scores = cross_val_score(
                    self.classifier, self.X_train, self.y_train_encoded, 
                    cv=min(3, len(self.classes_a)), 
                    scoring='accuracy'
                )
                print(f"   Score de validation croisée: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            except:
                pass
        
        print("✓ Modèle entraîné avec succès")
    
    def classify(self, top_k: int = 5) -> List[Dict]:
        """
        Classifie chaque classe de B sur les classes de A avec probabilités
        
        Args:
            top_k: Nombre de meilleures prédictions à retourner
            
        Returns:
            Liste de mappings avec probabilités
        """
        print(f"\nClassification des classes de B → A (top-{top_k})...")
        
        if self.classifier is None:
            raise ValueError("Le modèle n'est pas entraîné. Appelez train_model() d'abord.")
        
        mappings = []
        
        for class_b in self.classes_b:
            # Extraire les features de la classe B
            features = self._extract_features(class_b).reshape(1, -1)
            
            # Prédire les probabilités pour toutes les classes
            probabilities = self.classifier.predict_proba(features)[0]
            
            # Obtenir les top-k prédictions
            top_indices = np.argsort(probabilities)[-top_k:][::-1]
            
            top_matches = []
            for idx in top_indices:
                class_a_name = self.label_encoder.inverse_transform([idx])[0]
                
                # Trouver les informations complètes de cette classe
                class_a_info = next(c for c in self.classes_a if c['name'] == class_a_name)
                
                top_matches.append({
                    'class_a_name': class_a_info['name'],
                    'class_a_label': class_a_info['label'],
                    'class_a_iri': class_a_info['iri'],
                    'similarity_score': float(probabilities[idx]),  # On garde le nom pour compatibilité
                    'probability': float(probabilities[idx])
                })
            
            mapping = {
                'class_b_name': class_b['name'],
                'class_b_label': class_b['label'],
                'class_b_iri': class_b['iri'],
                'class_b_description': class_b['full_description'][:200],
                'top_matches': top_matches,
                'best_match': top_matches[0] if top_matches else None
            }
            
            mappings.append(mapping)
        
        print(f"✓ Classification terminée pour {len(mappings)} classes")
        return mappings
    
    def save_mappings(self, mappings: List[Dict], output_path: str):
        """
        Sauvegarde les mappings dans un fichier JSON
        
        Args:
            mappings: Liste des mappings
            output_path: Chemin du fichier de sortie
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Mappings sauvegardés dans {output_path}")
    
    def generate_report(self, mappings: List[Dict], output_path: str):
        """
        Génère un rapport détaillé de la classification
        
        Args:
            mappings: Liste des mappings
            output_path: Chemin du fichier de rapport
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT DE CLASSIFICATION - ONTOLOGIE B → ONTOLOGIE A\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Nombre de classes de B classifiées: {len(mappings)}\n")
            f.write(f"Type de modèle: {self.classifier_type}\n\n")
            
            # Statistiques générales
            avg_best_prob = np.mean([m['best_match']['probability'] for m in mappings])
            
            f.write(f"Probabilité moyenne du meilleur match: {avg_best_prob:.4f}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("DÉTAIL DES CLASSIFICATIONS\n")
            f.write("=" * 80 + "\n\n")
            
            for i, mapping in enumerate(mappings, 1):
                f.write(f"\n{i}. CLASSE B: {mapping['class_b_label']} ({mapping['class_b_name']})\n")
                f.write("-" * 80 + "\n")
                f.write(f"Description: {mapping['class_b_description']}\n\n")
                
                f.write("Top 5 correspondances prédites par le modèle:\n\n")
                
                for j, match in enumerate(mapping['top_matches'], 1):
                    f.write(f"  {j}. {match['class_a_label']} ({match['class_a_name']})\n")
                    f.write(f"     Probabilité: {match['probability']:.4f} ({match['probability']*100:.2f}%)\n\n")
                
                f.write("\n")
        
        print(f"✓ Rapport généré dans {output_path}")
    
    def export_to_csv(self, mappings: List[Dict], output_path: str):
        """
        Exporte les résultats dans un CSV pour analyse
        
        Args:
            mappings: Liste des mappings
            output_path: Chemin du fichier CSV
        """
        rows = []
        
        for mapping in mappings:
            best = mapping['best_match']
            rows.append({
                'classe_b_name': mapping['class_b_name'],
                'classe_b_label': mapping['class_b_label'],
                'classe_a_name': best['class_a_name'],
                'classe_a_label': best['class_a_label'],
                'probabilite': best['probability'],
                'probabilite_pct': best['probability'] * 100
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"✓ Résultats exportés dans {output_path}")


def main():
    """Fonction principale"""
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python classify_ontologies.py <classes_a.json> <classes_b.json> <output_mappings.json> <output_report.txt>")
        sys.exit(1)
    
    classes_a_path = sys.argv[1]
    classes_b_path = sys.argv[2]
    output_mappings = sys.argv[3]
    output_report = sys.argv[4]
    
    # Créer le classificateur
    classifier = OntologyClassifier(classifier_type='random_forest')
    
    # Charger les classes
    classifier.load_classes(classes_a_path, classes_b_path)
    
    # Entraîner le modèle sur les classes de A
    classifier.train_model(use_augmentation=True)
    
    # Classifier les classes de B
    mappings = classifier.classify(top_k=5)
    
    # Sauvegarder les résultats
    classifier.save_mappings(mappings, output_mappings)
    classifier.generate_report(mappings, output_report)
    
    # Exporter en CSV
    csv_path = output_mappings.replace('.json', '.csv')
    classifier.export_to_csv(mappings, csv_path)
    
    print("\n✅ Classification terminée avec succès!")


if __name__ == "__main__":
    main()
