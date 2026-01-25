#!/usr/bin/env python3
"""
Script interactif de fusion d'ontologies alignées avec interface de sélection.
Permet de valider/rejeter les alignements avant la fusion via une interface graphique.
"""

import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from collections import defaultdict
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from rdflib.namespace import XSD


# ============================================================================
# PARAMÈTRES CONFIGURABLES
# ============================================================================

ALIGNMENT_FILE = "alignment_results.json"
OUTPUT_OWL = "merged_ontology.owl"
OUTPUT_JSON = "merged_ontology.json"

# Namespace pour l'ontologie fusionnée
MERGED_NS = "http://example.org/merged-animal-ontology/"

# ============================================================================

class AlignmentValidator(tk.Tk):
    """Interface graphique pour valider les alignements avant fusion."""
    
    def __init__(self, alignment_file):
        super().__init__()
        
        self.title("Validation des Alignements d'Ontologies")
        self.geometry("1200x650")
        self.configure(bg='#f5f5f5')
        
        # Configuration du style moderne
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs
        bg_color = '#f5f5f5'
        fg_color = '#2c3e50'
        accent_color = '#3498db'
        success_color = '#27ae60'
        hover_color = '#ecf0f1'
        
        # Configuration globale
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Segoe UI', 9))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#2c3e50')
        style.configure('Heading.TLabel', font=('Segoe UI', 11, 'bold'), foreground=fg_color)
        style.configure('Subheading.TLabel', font=('Segoe UI', 10), foreground='#7f8c8d')
        
        # Boutons
        style.configure('TButton', font=('Segoe UI', 10), padding=8)
        style.map('TButton',
                 background=[('active', hover_color)],
                 foreground=[('active', fg_color)])
        
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), padding=8)
        style.map('Accent.TButton',
                 background=[('active', '#2980b9')],
                 foreground=[('active', 'white')])
        
        # Treeview
        style.configure('Treeview', 
                       rowheight=28,
                       font=('Segoe UI', 9),
                       background='white',
                       fieldbackground='white',
                       foreground=fg_color,
                       borderwidth=0)
        style.configure('Treeview.Heading',
                       font=('Segoe UI', 10, 'bold'),
                       background='#34495e',
                       foreground='white')
        style.map('Treeview', background=[('selected', accent_color)], foreground=[('selected', 'white')])
        
        # LabelFrame
        style.configure('TLabelframe', background=bg_color, foreground=fg_color, font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color, font=('Segoe UI', 10, 'bold'))
        
        self.alignment_file = Path(alignment_file)
        self.alignments = []
        self.metadata = {}
        self.selected_alignments = set()
        self.current_sort_order = None
        self.filtered_indices = list()
        self.search_var = None
        self.min_score_var = None
        
        # Charger les alignements
        self.load_alignments()
        
        # Créer l'interface
        self.setup_ui()
        
    def load_alignments(self):
        """Charge le fichier d'alignement."""
        try:
            with open(self.alignment_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metadata = data['metadata']
                self.alignments = data['alignments']
            print(f"OK {len(self.alignments)} alignements charges")
        except FileNotFoundError:
            messagebox.showerror("Erreur", f"Fichier non trouve: {self.alignment_file}")
            self.destroy()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        
        # ===== HEADER AVEC TITRE =====
        header = ttk.Frame(self, relief=tk.FLAT)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        title_container = ttk.Frame(header)
        title_container.pack(fill=tk.X, padx=15, pady=10)
        
        title = ttk.Label(title_container, text="Validation des Alignements d'Ontologies", 
                         style='Title.TLabel')
        title.pack(side=tk.LEFT)
        
        self.count_label = ttk.Label(title_container, text="0 alignements selectionnes", 
                                    style='Subheading.TLabel', foreground='#e74c3c')
        self.count_label.pack(side=tk.RIGHT)
        
        # Séparateur
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15)
        
        # ===== CONTROLES =====
        controls_container = ttk.Frame(self)
        controls_container.pack(fill=tk.X, padx=15, pady=10)
        
        # Ligne 1: Sélection et Tri
        row1 = ttk.Frame(controls_container)
        row1.pack(fill=tk.X, pady=(0, 8))
        
        select_frame = ttk.LabelFrame(row1, text="Selection", padding=8)
        select_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X)
        
        ttk.Button(select_frame, text="Tous", 
                  command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(select_frame, text="Aucun", 
                  command=self.deselect_all).pack(side=tk.LEFT, padx=2)
        
        sort_frame = ttk.LabelFrame(row1, text="Tri par score", padding=8)
        sort_frame.pack(side=tk.LEFT, padx=0, fill=tk.X)
        
        ttk.Button(sort_frame, text="Asc", 
                  command=self.sort_by_score_asc).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="Desc", 
                  command=self.sort_by_score_desc).pack(side=tk.LEFT, padx=2)
        
        # Ligne 2: Filtres
        row2 = ttk.Frame(controls_container)
        row2.pack(fill=tk.X)
        
        filter_frame = ttk.LabelFrame(row2, text="Recherche & Filtres", padding=8)
        filter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        search_subframe = ttk.Frame(filter_frame)
        search_subframe.pack(fill=tk.X)
        
        ttk.Label(search_subframe, text="Classe:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_alignments)
        search_entry = ttk.Entry(search_subframe, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        ttk.Label(search_subframe, text="Score min:").pack(side=tk.LEFT, padx=(0, 5))
        self.min_score_var = tk.DoubleVar(value=0.0)
        self.min_score_var.trace("w", self.filter_alignments)
        score_spinbox = ttk.Spinbox(search_subframe, from_=0.0, to=1.0, increment=0.05, 
                                    textvariable=self.min_score_var, width=8)
        score_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(search_subframe, text="Reset", 
                  command=self.reset_filters).pack(side=tk.LEFT)
        
        # ===== TABLEAU PRINCIPAL =====
        table_container = ttk.Frame(self)
        table_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Treeview avec scrollbar
        tree_frame = ttk.Frame(table_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Colonnes du tableau
        columns = ("select", "source", "matches", "score", "source_def", "target_def")
        self.tree = ttk.Treeview(tree_frame, columns=columns, height=15,
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set, show="headings")
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configuration des colonnes
        self.tree.heading("select", text="Sel")
        self.tree.column("select", width=35, anchor=tk.CENTER)
        
        self.tree.heading("source", text="Classe Source (A)")
        self.tree.column("source", width=120, anchor=tk.W)
        
        self.tree.heading("matches", text="Correspondance (B)")
        self.tree.column("matches", width=120, anchor=tk.W)
        
        self.tree.heading("score", text="Score")
        self.tree.column("score", width=50, anchor=tk.CENTER)
        
        self.tree.heading("source_def", text="Definition Source")
        self.tree.column("source_def", width=200, anchor=tk.W)
        
        self.tree.heading("target_def", text="Definition Cible")
        self.tree.column("target_def", width=200, anchor=tk.W)
        
        # Pack du treeview
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        # Bind click pour sélection
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        # Séparateur
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15)
        
        # ===== FOOTER AVEC ACTIONS =====
        footer = ttk.Frame(self)
        footer.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Button(footer, text="Exporter", 
                  command=self.export_selection).pack(side=tk.LEFT, padx=3)
        ttk.Button(footer, text="Fusionner", style='Accent.TButton',
                  command=self.merge_and_process).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(footer, text="Quitter", 
                  command=self.quit).pack(side=tk.RIGHT, padx=3)
        
        # Remplir le tableau
        self.populate_tree()
    
    def populate_tree(self):
        """Remplit le tableau avec les alignements."""
        for idx, alignment in enumerate(self.alignments):
            source = alignment['source_class']
            
            if not alignment['matches']:
                target_label = "Pas de correspondance"
                score = 0.0
                target_def = ""
            else:
                target = alignment['matches'][0]
                target_label = target['target_class']['label']
                score = target['similarity_score']
                target_def = target['target_class']['definition'][:100] + "..."
            
            source_def = source['definition'][:100] + "..." if source['definition'] else ""
            
            values = (
                "O",
                source['label'],
                target_label,
                f"{score:.2f}",
                source_def,
                target_def
            )
            
            self.tree.insert("", "end", iid=str(idx), values=values)
            self.selected_alignments.add(idx)  # Tous sélectionnés par défaut
        
        self.update_count()
    
    def filter_alignments(self, *args):
        """Filtre les alignements selon la recherche et le score minimum."""
        search_term = self.search_var.get().lower()
        min_score = self.min_score_var.get()
        
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            source_label = values[1].lower()
            target_label = values[2].lower()
            score = float(values[3])
            
            # Filtres
            search_match = search_term in source_label or search_term in target_label
            score_match = score >= min_score
            
            if search_match and score_match:
                self.tree.item(item, tags="visible")
            else:
                self.tree.item(item, tags="hidden")
        
        # Appliquer le style
        self.tree.tag_configure("hidden", foreground="#cccccc")
        self.tree.tag_configure("visible", foreground="black")
    
    def reset_filters(self):
        """Réinitialise tous les filtres."""
        self.search_var.set("")
        self.min_score_var.set(0.0)
        self.current_sort_order = None
        self.populate_tree()
    
    def sort_by_score_asc(self):
        """Trie les alignements par score croissant."""
        if self.current_sort_order == 'asc':
            self.current_sort_order = None
            self.populate_tree()
        else:
            self.current_sort_order = 'asc'
            self._apply_sort()
    
    def sort_by_score_desc(self):
        """Trie les alignements par score décroissant."""
        if self.current_sort_order == 'desc':
            self.current_sort_order = None
            self.populate_tree()
        else:
            self.current_sort_order = 'desc'
            self._apply_sort()
    
    def _apply_sort(self):
        """Applique le tri actuel."""
        # Créer une liste avec les alignements et leurs scores
        indices_with_scores = []
        for idx, alignment in enumerate(self.alignments):
            if alignment['matches']:
                score = alignment['matches'][0]['similarity_score']
            else:
                score = 0.0
            indices_with_scores.append((idx, score, alignment))
        
        # Trier
        if self.current_sort_order == 'asc':
            indices_with_scores.sort(key=lambda x: x[1])
        elif self.current_sort_order == 'desc':
            indices_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Vider le tree et le remplir dans le nouvel ordre
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for sorted_idx, (original_idx, score, alignment) in enumerate(indices_with_scores):
            source = alignment['source_class']
            
            if not alignment['matches']:
                target_label = "Pas de correspondance"
                target_def = ""
            else:
                target = alignment['matches'][0]
                target_label = target['target_class']['label']
                target_def = target['target_class']['definition'][:100] + "..."
            
            source_def = source['definition'][:100] + "..." if source['definition'] else ""
            
            values = (
                "X" if original_idx in self.selected_alignments else "O",
                source['label'],
                target_label,
                f"{score:.2f}",
                source_def,
                target_def
            )
            
            self.tree.insert("", "end", iid=str(original_idx), values=values)
    
    def on_tree_click(self, event):
        """Gère les clics sur le tableau."""
        item = self.tree.identify("item", event.x, event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or column != "#1":
            return
        
        idx = int(item)
        
        # Toggle sélection
        if idx in self.selected_alignments:
            self.selected_alignments.remove(idx)
            self.tree.item(item, values=(
                "O",
                self.tree.item(item, "values")[1],
                self.tree.item(item, "values")[2],
                self.tree.item(item, "values")[3],
                self.tree.item(item, "values")[4],
                self.tree.item(item, "values")[5],
            ))
            self.tree.item(item, tags="deselected")
        else:
            self.selected_alignments.add(idx)
            self.tree.item(item, values=(
                "X",
                self.tree.item(item, "values")[1],
                self.tree.item(item, "values")[2],
                self.tree.item(item, "values")[3],
                self.tree.item(item, "values")[4],
                self.tree.item(item, "values")[5],
            ))
            self.tree.item(item, tags="selected")
        
        self.update_count()
    
    def update_count(self):
        """Met à jour le compteur de sélection."""
        count = len(self.selected_alignments)
        self.count_label.config(text=str(count))
    
    def select_all(self):
        """Sélectionne tous les alignements."""
        self.selected_alignments = set(range(len(self.alignments)))
        
        for idx in range(len(self.alignments)):
            item = str(idx)
            values = list(self.tree.item(item, "values"))
            values[0] = "X"
            self.tree.item(item, values=values, tags="selected")
        
        self.update_count()
    
    def deselect_all(self):
        """Désélectionne tous les alignements."""
        self.selected_alignments.clear()
        
        for idx in range(len(self.alignments)):
            item = str(idx)
            values = list(self.tree.item(item, "values"))
            values[0] = "O"
            self.tree.item(item, values=values, tags="deselected")
        
        self.update_count()
    
    def export_selection(self):
        """Exporte la sélection en JSON."""
        if not self.selected_alignments:
            messagebox.showwarning("Attention", "Aucun alignement selectionne!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        selected_data = {
            'metadata': self.metadata,
            'alignments': [self.alignments[idx] for idx in sorted(self.selected_alignments)]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(selected_data, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("Succes", f"Selection exportee: {Path(file_path).name}")
    
    def merge_and_process(self):
        """Lance la fusion avec les alignements sélectionnés."""
        if not self.selected_alignments:
            messagebox.showwarning("Attention", "Aucun alignement selectionne!")
            return
        
        if messagebox.askyesno("Confirmation", 
            f"Fusionner {len(self.selected_alignments)} alignements selectionnes?"):
            
            # Créer les données filtrées
            filtered_alignments = [self.alignments[idx] for idx in sorted(self.selected_alignments)]
            
            # Lancer la fusion
            merger = OntologyMerger(self.metadata, filtered_alignments)
            merger.create_merged_classes()
            merger.generate_owl()
            merger.save_outputs(self.alignment_file.parent)
            
            messagebox.showinfo("Succes", "Fusion terminez avec succes!")
            self.quit()


class OntologyMerger:
    """Classe pour fusionner deux ontologies alignées."""
    
    def __init__(self, metadata, alignments):
        """
        Initialise le merger.
        
        Args:
            metadata: Métadonnées de l'alignement
            alignments: Liste des alignements sélectionnés
        """
        self.metadata = metadata
        self.alignments = alignments
        self.merged_classes = {}
        self.class_hierarchy = defaultdict(list)
        
        # Création du graph RDF
        self.graph = Graph()
        self.merged = Namespace(MERGED_NS)
        self.graph.bind("merged", self.merged)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        
    def parse_individual_string(self, ind_str):
        """
        Parse une chaîne d'individu au format "Name (Description)".
        
        Args:
            ind_str: Chaîne de l'individu
            
        Returns:
            Dict avec name et description, ou None
        """
        match = re.match(r'^(.+?)\s*\((.+)\)$', ind_str.strip())
        if match:
            return {
                'name': match.group(1).strip(),
                'description': match.group(2).strip()
            }
        return None
    
    def merge_individuals(self, source_individuals, target_individus):
        """
        Fusionne les individus des deux sources.
        
        Args:
            source_individuals: Liste d'individus de la source A (format dict)
            target_individus: Liste d'individus de la source B (format string)
            
        Returns:
            Liste fusionnée avec provenance
        """
        merged = []
        
        # Individus de la source A
        for ind in source_individuals:
            merged.append({
                'name': ind['name'],
                'description': ind['description'],
                'source': 'A'
            })
        
        # Individus de la source B (parser les strings)
        for ind_str in target_individus:
            parsed = self.parse_individual_string(ind_str)
            if parsed:
                merged.append({
                    'name': parsed['name'],
                    'description': parsed['description'],
                    'source': 'B'
                })
        
        return merged
    
    def merge_synonyms(self, source_synonyms, target_synonyms):
        """Fusionne les listes de synonymes sans doublons."""
        all_synonyms = set(source_synonyms) | set(target_synonyms)
        return sorted(list(all_synonyms))
    
    def create_merged_classes(self):
        """Crée les classes fusionnées à partir des alignements."""
        print("[INFO] Creation des classes fusionnees...")
        
        for alignment in self.alignments:
            source = alignment['source_class']
            
            # Si pas de correspondance, on garde juste la source
            if not alignment['matches']:
                target = None
                best_score = 0.0
            else:
                target = alignment['matches'][0]['target_class']
                best_score = alignment['matches'][0]['similarity_score']
            
            # ID de la classe fusionnée (basé sur la source A)
            merged_id = source['id']
            
            # Création de la classe fusionnée
            merged_class = {
                'id': merged_id,
                'uri': str(self.merged[merged_id]),
                'label': source['label'],
                'similarity_score': best_score,
                
                # Provenance source A
                'source_A': {
                    'label': source['label'],
                    'uri': source['uri'],
                    'definition': source['definition']
                },
                
                # Provenance source B (si alignement trouvé)
                'source_B': {
                    'label': target['label'] if target else None,
                    'uri': target['uri'] if target else None,
                    'definition': target['definition'] if target else None
                } if target else None,
                
                # Données fusionnées
                'synonyms': self.merge_synonyms(
                    source['synonyms'],
                    target['synonyms'] if target else []
                ),
                'attributes': {
                    'source_A': source['attributes'],
                    'source_B': target['attributes'] if target else None
                },
                'individuals': self.merge_individuals(
                    source['individuals'],
                    target['individus'] if target else []
                ),
                
                # Hiérarchie (on garde celle de la source A comme référence)
                'parent': source['parent'],
                'children': source['children']
            }
            
            self.merged_classes[merged_id] = merged_class
            
            # Construction de la hiérarchie
            if source['parent']:
                parent_id = source['parent']['label']
                self.class_hierarchy[parent_id].append(merged_id)
        
        print(f"[OK] {len(self.merged_classes)} classes fusionnees creees")
     
    def generate_owl(self):
        """Génère l'ontologie OWL fusionnée."""
        print("[INFO] Generation de l'ontologie OWL...")
        
        # Déclaration de l'ontologie
        ontology_uri = URIRef(MERGED_NS)
        self.graph.add((ontology_uri, RDF.type, OWL.Ontology))
        self.graph.add((ontology_uri, RDFS.label, Literal("Merged Animal Ontology")))
        self.graph.add((ontology_uri, RDFS.comment, Literal(
            f"Ontologie fusionnée générée à partir de {self.metadata['source_ontology']}"
        )))
        
        # Création des classes
        for class_id, merged_class in self.merged_classes.items():
            class_uri = URIRef(merged_class['uri'])
            
            # Déclaration de la classe
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(merged_class['label'])))
            
            # Provenance source A
            self.graph.add((class_uri, self.merged['sourceA_label'], 
                           Literal(merged_class['source_A']['label'])))
            self.graph.add((class_uri, self.merged['sourceA_uri'], 
                           Literal(merged_class['source_A']['uri'])))
            self.graph.add((class_uri, self.merged['sourceA_definition'], 
                           Literal(merged_class['source_A']['definition'])))
            
            # Provenance source B (si existante)
            if merged_class['source_B']:
                self.graph.add((class_uri, self.merged['sourceB_label'], 
                               Literal(merged_class['source_B']['label'])))
                self.graph.add((class_uri, self.merged['sourceB_uri'], 
                               Literal(merged_class['source_B']['uri'])))
                self.graph.add((class_uri, self.merged['sourceB_definition'], 
                               Literal(merged_class['source_B']['definition'])))
                self.graph.add((class_uri, self.merged['similarity_score'], 
                               Literal(merged_class['similarity_score'], datatype=XSD.float)))
            
            # Synonymes
            for synonym in merged_class['synonyms']:
                self.graph.add((class_uri, self.merged['synonym'], Literal(synonym)))
            
            # Attributs source A
            if merged_class['attributes']['source_A']:
                self.graph.add((class_uri, self.merged['attributesA'], 
                               Literal(str(merged_class['attributes']['source_A']))))
            
            # Attributs source B
            if merged_class['attributes']['source_B']:
                self.graph.add((class_uri, self.merged['attributesB'], 
                               Literal(str(merged_class['attributes']['source_B']))))
            
            # Relation parent (subClassOf)
            if merged_class['parent']:
                parent_id = merged_class['parent']['label']
                if parent_id in self.merged_classes:
                    parent_uri = URIRef(self.merged_classes[parent_id]['uri'])
                    self.graph.add((class_uri, RDFS.subClassOf, parent_uri))
            
            # Individus
            for individual in merged_class['individuals']:
                ind_uri = URIRef(f"{merged_class['uri']}/{individual['name']}")
                self.graph.add((ind_uri, RDF.type, class_uri))
                self.graph.add((ind_uri, RDFS.label, Literal(individual['name'])))
                self.graph.add((ind_uri, RDFS.comment, Literal(individual['description'])))
                self.graph.add((ind_uri, self.merged['source'], Literal(individual['source'])))
        
        print(f"[OK] {len(self.merged_classes)} classes OWL creees")
        print(f"[OK] {len([1 for c in self.merged_classes.values() for _ in c['individuals']])} individus crees")
    
    def generate_json(self):
        """Génère la représentation JSON hiérarchique."""
        print("[INFO] Generation de la structure JSON...")
        
        def build_tree(class_id):
            """Construit récursivement l'arbre hiérarchique."""
            merged_class = self.merged_classes[class_id]
            
            node = {
                'id': merged_class['id'],
                'uri': merged_class['uri'],
                'label': merged_class['label'],
                'similarity_score': merged_class['similarity_score'],
                'source_A': merged_class['source_A'],
                'source_B': merged_class['source_B'],
                'synonyms': merged_class['synonyms'],
                'attributes': merged_class['attributes'],
                'individuals': merged_class['individuals'],
                'children': []
            }
            
            # Ajout récursif des enfants
            if class_id in self.class_hierarchy:
                for child_id in self.class_hierarchy[class_id]:
                    node['children'].append(build_tree(child_id))
            
            return node
        
        # Trouve les racines (classes sans parent)
        root_classes = [
            class_id for class_id, merged_class in self.merged_classes.items()
            if not merged_class['parent']
        ]
        
        # Construction de l'arbre
        tree = {
            'metadata': {
                'source_ontology_A': self.metadata['source_ontology'],
                'total_classes': len(self.merged_classes),
                'total_individuals': sum(len(c['individuals']) for c in self.merged_classes.values()),
                'alignment_statistics': self.metadata['statistics']
            },
            'ontology': [build_tree(root_id) for root_id in root_classes]
        }
        
        return tree
    
    def save_outputs(self, output_dir):
        """Sauvegarde les fichiers OWL et JSON."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarde OWL
        owl_path = output_path / OUTPUT_OWL
        print(f"[SAVE] Sauvegarde OWL : {owl_path}...")
        self.graph.serialize(destination=str(owl_path), format='xml')
        print(f"[OK] OWL sauvegarde : {owl_path}")
        
        # Sauvegarde JSON
        json_path = output_path / OUTPUT_JSON
        print(f"[SAVE] Sauvegarde JSON : {json_path}...")
        tree = self.generate_json()
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON sauvegarde : {json_path}")
        
        # Statistiques finales
        print("\n" + "=" * 70)
        print("[STATS] STATISTIQUES DE FUSION")
        print("=" * 70)
        print(f"Classes fusionnees : {len(self.merged_classes)}")
        print(f"Individus totaux : {sum(len(c['individuals']) for c in self.merged_classes.values())}")
        print(f"  - Source A : {sum(1 for c in self.merged_classes.values() for i in c['individuals'] if i['source'] == 'A')}")
        print(f"  - Source B : {sum(1 for c in self.merged_classes.values() for i in c['individuals'] if i['source'] == 'B')}")
        print(f"Classes avec alignement : {sum(1 for c in self.merged_classes.values() if c['source_B'])}")
        print(f"Classes sans alignement : {sum(1 for c in self.merged_classes.values() if not c['source_B'])}")
        print("=" * 70)
        

def main():
    """Point d'entrée du script."""
    print("=" * 70)
    print("[APP] VALIDATION INTERACTIVE DES ALIGNEMENTS D'ONTOLOGIES")
    print("=" * 70)
    
    # Chemins
    script_dir = Path(__file__).parent
    alignment_file = script_dir / ALIGNMENT_FILE
    
    if not alignment_file.exists():
        print(f"[ERROR] Fichier non trouve : {alignment_file}")
        return 1
    
    # Lancer l'interface
    app = AlignmentValidator(alignment_file)
    app.mainloop()
    
    return 0


if __name__ == "__main__":
    exit(main())
