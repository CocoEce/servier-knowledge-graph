#!/usr/bin/env python3
"""
Interface graphique pour la démonstration de la pipeline d'alignement d'ontologies
"""

import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import subprocess
import threading
import queue
import time

# Ajouter le répertoire parent au path pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DemoGUI(tk.Tk):
    """Interface graphique pour la démonstration."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Démonstration - Pipeline d'Alignement d'Ontologies")
        self.geometry("1400x800")
        self.configure(bg='#f5f5f5')
        
        # État des étapes
        self.step_status = {
            1: "pending",  # pending, running, success, error
            2: "pending",
            3: "pending",
            4: "pending",
            5: "pending"
        }
        
        # Queue pour les logs
        self.log_queue = queue.Queue()
        self.running = False
        
        # Configuration du style
        self.setup_style()
        
        # Créer l'interface
        self.setup_ui()
        
        # Démarrer la lecture de la queue
        self.process_log_queue()
    
    def setup_style(self):
        """Configure le style de l'interface."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs
        style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'), foreground='#2c3e50')
        style.configure('Step.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#2c3e50')
        style.configure('Status.TLabel', font=('Segoe UI', 10), foreground='#7f8c8d')
        
        # Boutons des étapes
        style.configure('Step.TButton', font=('Segoe UI', 11), padding=15)
        style.configure('RunAll.TButton', font=('Segoe UI', 14, 'bold'), padding=20)
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        # Container principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== PARTIE GAUCHE : CONTRÔLES =====
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Titre
        title = ttk.Label(left_frame, text="Pipeline d'Alignement", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Description
        desc = ttk.Label(left_frame, text="Système d'alignement sémantique d'ontologies\nutilisant BERT et recherche vectorielle",
                        justify=tk.CENTER, foreground='#7f8c8d')
        desc.pack(pady=(0, 30))
        
        # Bouton "Exécuter tout"
        self.run_all_btn = ttk.Button(left_frame, text="▶️ EXÉCUTER TOUTE LA PIPELINE",
                                      style='RunAll.TButton', command=self.run_all_steps)
        self.run_all_btn.pack(pady=(0, 30), fill=tk.X)
        
        # Séparateur
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 20))
        
        # Étapes individuelles
        steps_label = ttk.Label(left_frame, text="Étapes individuelles", style='Step.TLabel')
        steps_label.pack(pady=(0, 15))
        
        # Créer les boutons d'étapes
        self.step_frames = {}
        self.step_buttons = {}
        self.step_labels = {}
        
        steps = [
            (1, "Mapping OWL → CSV", "Extraction des classes et propriétés", "#3498db"),
            (2, "Vectorisation", "Génération des embeddings BERT", "#27ae60"),
            (3, "Alignement Sémantique", "Recherche de correspondances", "#e67e22"),
            (4, "Validation Interactive", "Fusion des ontologies", "#e74c3c"),
            (5, "Chargement GraphDB", "Import dans le knowledge graph", "#9b59b6")
        ]
        
        for step_num, title, desc, color in steps:
            frame = self.create_step_widget(left_frame, step_num, title, desc, color)
            frame.pack(pady=5, fill=tk.X)
            self.step_frames[step_num] = frame
        
        # ===== PARTIE DROITE : LOGS =====
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Titre logs
        logs_title = ttk.Label(right_frame, text="Logs d'exécution", style='Step.TLabel')
        logs_title.pack(pady=(0, 10))
        
        # Zone de texte pour les logs
        self.log_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, 
                                                   font=('Consolas', 10),
                                                   bg='#2c3e50', fg='#ecf0f1',
                                                   relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Boutons en bas des logs
        log_buttons = ttk.Frame(right_frame)
        log_buttons.pack(pady=(10, 0), fill=tk.X)
        
        ttk.Button(log_buttons, text="Effacer les logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons, text="Quitter", 
                  command=self.quit_app).pack(side=tk.RIGHT, padx=5)
    
    def create_step_widget(self, parent, step_num, title, desc, color):
        """Crée un widget pour une étape."""
        frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        
        # Conteneur interne avec padding
        inner = ttk.Frame(frame)
        inner.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # Ligne du haut : numéro + titre
        top_line = ttk.Frame(inner)
        top_line.pack(fill=tk.X, pady=(0, 5))
        
        num_label = tk.Label(top_line, text=f"  {step_num}  ", 
                            bg=color, fg='white', font=('Segoe UI', 12, 'bold'),
                            relief=tk.FLAT)
        num_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = ttk.Label(top_line, text=title, font=('Segoe UI', 11, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Description
        desc_label = ttk.Label(inner, text=desc, foreground='#7f8c8d')
        desc_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Bouton + statut
        bottom_line = ttk.Frame(inner)
        bottom_line.pack(fill=tk.X)
        
        btn = ttk.Button(bottom_line, text="▶️ Exécuter",
                        command=lambda: self.run_single_step(step_num))
        btn.pack(side=tk.LEFT)
        self.step_buttons[step_num] = btn
        
        status_label = ttk.Label(bottom_line, text="⏸️  En attente", style='Status.TLabel')
        status_label.pack(side=tk.RIGHT)
        self.step_labels[step_num] = status_label
        
        return frame
    
    def update_step_status(self, step_num, status):
        """Met à jour le statut d'une étape."""
        self.step_status[step_num] = status
        
        icons = {
            "pending": "⏸️  En attente",
            "running": "⏳  En cours...",
            "success": "✅  Terminé",
            "error": "❌  Erreur"
        }
        
        self.step_labels[step_num].config(text=icons.get(status, ""))
    
    def log(self, message, level="INFO"):
        """Ajoute un message aux logs."""
        colors = {
            "INFO": "#3498db",
            "SUCCESS": "#27ae60",
            "ERROR": "#e74c3c",
            "WARNING": "#f39c12"
        }
        
        timestamp = time.strftime("%H:%M:%S")
        self.log_queue.put((timestamp, level, message, colors.get(level, "#ecf0f1")))
    
    def process_log_queue(self):
        """Traite la queue de logs."""
        try:
            while True:
                timestamp, level, message, color = self.log_queue.get_nowait()
                
                # Insérer dans le widget
                self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                self.log_text.insert(tk.END, f"[{level}] ", "level")
                self.log_text.insert(tk.END, f"{message}\n")
                
                # Auto-scroll
                self.log_text.see(tk.END)
                
        except queue.Empty:
            pass
        
        # Rappeler cette fonction après 100ms
        self.after(100, self.process_log_queue)
    
    def clear_logs(self):
        """Efface les logs."""
        self.log_text.delete(1.0, tk.END)
    
    def run_single_step(self, step_num):
        """Exécute une seule étape."""
        if self.running:
            messagebox.showwarning("Attention", "Une étape est déjà en cours d'exécution")
            return
        
        thread = threading.Thread(target=self._execute_step, args=(step_num,))
        thread.daemon = True
        thread.start()
    
    def run_all_steps(self):
        """Exécute toutes les étapes."""
        if self.running:
            messagebox.showwarning("Attention", "Une étape est déjà en cours d'exécution")
            return
        
        thread = threading.Thread(target=self._execute_all_steps)
        thread.daemon = True
        thread.start()
    
    def _execute_all_steps(self):
        """Exécute toutes les étapes en séquence."""
        self.running = True
        self.run_all_btn.config(state=tk.DISABLED)
        
        self.log("="*80, "INFO")
        self.log("DÉBUT DE LA PIPELINE COMPLÈTE", "INFO")
        self.log("="*80, "INFO")
        
        for step_num in [1, 2, 3, 4, 5]:
            self._execute_step(step_num)
            
            if self.step_status[step_num] == "error":
                self.log("Arrêt de la pipeline suite à une erreur", "ERROR")
                break
            
            # Délai spécial après la vectorisation pour l'indexation MongoDB
            if step_num == 2:
                self.log("⏳ Attente de 60 secondes pour l'indexation MongoDB...", "WARNING")
                time.sleep(60)
                self.log("✓ Indexation terminée", "SUCCESS")
            else:
                # Petite pause entre les autres étapes
                time.sleep(1)
        
        self.log("="*80, "INFO")
        self.log("PIPELINE TERMINÉE", "SUCCESS")
        self.log("="*80, "INFO")
        
        self.running = False
        self.run_all_btn.config(state=tk.NORMAL)
    
    def _execute_step(self, step_num):
        """Exécute une étape spécifique."""
        self.running = True
        self.update_step_status(step_num, "running")
        self.step_buttons[step_num].config(state=tk.DISABLED)
        
        steps_config = {
            1: ("Étape 1: Mapping OWL → CSV", self._run_mapping),
            2: ("Étape 2: Vectorisation", self._run_vectorize),
            3: ("Étape 3: Alignement sémantique", self._run_matching),
            4: ("Étape 4: Validation interactive", self._run_interactive),
            5: ("Étape 5: Chargement GraphDB", self._run_graphdb_load)
        }
        
        step_name, step_func = steps_config[step_num]
        
        self.log("", "INFO")
        self.log("*"*80, "INFO")
        self.log(f"  {step_name}", "INFO")
        self.log("*"*80, "INFO")
        
        try:
            step_func()
            self.update_step_status(step_num, "success")
            self.log(f"✓ {step_name} terminée avec succès", "SUCCESS")
        except Exception as e:
            self.update_step_status(step_num, "error")
            self.log(f"✗ Erreur: {str(e)}", "ERROR")
        finally:
            self.step_buttons[step_num].config(state=tk.NORMAL)
            self.running = False
    
    def _run_command(self, cmd, cwd=None):
        """Exécute une commande et capture la sortie."""
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd or str(project_root),
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            self.log(line.rstrip(), "INFO")
        
        process.wait()
        
        if process.returncode != 0:
            raise Exception(f"Commande échouée avec le code {process.returncode}")
    
    def _run_mapping(self):
        """Exécute l'étape de mapping."""
        self._run_command([
            sys.executable,
            str(project_root / "pipeline" / "mapping_ontologie.py")
        ])
    
    def _run_vectorize(self):
        """Exécute l'étape de vectorisation."""
        csv_b = project_root / "data" / "csv" / "ontologie_animaux_B.csv"
        self._run_command([
            sys.executable,
            str(project_root / "pipeline" / "vectorize_ontology.py"),
            str(csv_b)
        ])
    
    def _run_matching(self):
        """Exécute l'étape de matching."""
        csv_a = project_root / "data" / "csv" / "ontologie_animaux_A.csv"
        self._run_command([
            sys.executable,
            str(project_root / "pipeline" / "semantic_matching.py"),
            str(csv_a)
        ])
    
    def _run_interactive(self):
        """Lance l'interface interactive."""
        self.log("Lancement de l'interface de validation...", "INFO")
        self._run_command([
            sys.executable,
            str(project_root / "alignement" / "scripts" / "align_ontology_interactive.py")
        ])
    
    def _run_graphdb_load(self):
        """Charge l'ontologie merged dans GraphDB."""
        merged_owl = project_root / "alignement" / "merged" / "merged_ontology.owl"
        
        if not merged_owl.exists():
            raise FileNotFoundError("Ontologie merged non trouvée. Exécutez d'abord l'étape 4.")
        
        self.log(f"Chargement de {merged_owl.name} dans GraphDB...", "INFO")
        self._run_command([
            sys.executable,
            str(project_root / "graphdb" / "load_merged_ontology.py")
        ])
        self.log("✓ Ontologie chargée - Repository: PFE-GraphDB", "SUCCESS")
    
    def quit_app(self):
        """Quitte l'application."""
        if self.running:
            if not messagebox.askyesno("Confirmation", 
                "Une étape est en cours. Voulez-vous vraiment quitter ?"):
                return
        
        self.quit()


def main():
    """Point d'entrée."""
    app = DemoGUI()
    app.mainloop()


if __name__ == '__main__':
    main()
