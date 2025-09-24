"""
Simple GUI for GML to Neo4j Importer
Allows users to input Neo4j connection details and select GML file for import
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from gml_to_neo4j_importer import GMLToNeo4jImporter

class GMLImporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GML to Neo4j Importer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.neo4j_url = tk.StringVar(value="bolt://localhost:7687")
        self.neo4j_user = tk.StringVar(value="neo4j")
        self.neo4j_password = tk.StringVar(value="12345678")
        self.gml_file_path = tk.StringVar()
        self.clear_database = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="GML to Neo4j Importer", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Neo4j Connection Section
        connection_frame = ttk.LabelFrame(main_frame, text="Neo4j Connection", padding="10")
        connection_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        connection_frame.columnconfigure(1, weight=1)
        
        # Neo4j URL
        ttk.Label(connection_frame, text="Neo4j URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        url_entry = ttk.Entry(connection_frame, textvariable=self.neo4j_url, width=40)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Username
        ttk.Label(connection_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=2)
        user_entry = ttk.Entry(connection_frame, textvariable=self.neo4j_user, width=40)
        user_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Password
        ttk.Label(connection_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=2)
        password_entry = ttk.Entry(connection_frame, textvariable=self.neo4j_password, 
                                 show="*", width=40)
        password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # GML File Section
        file_frame = ttk.LabelFrame(main_frame, text="GML File", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # File selection
        ttk.Label(file_frame, text="GML File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        file_entry = ttk.Entry(file_frame, textvariable=self.gml_file_path, width=40)
        file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=2)
        
        browse_button = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_button.grid(row=0, column=2, padx=(0, 0), pady=2)
        
        # Options Section
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        clear_check = ttk.Checkbutton(options_frame, text="Clear existing database before import", 
                                    variable=self.clear_database)
        clear_check.grid(row=0, column=0, sticky=tk.W)
        
        # Buttons Section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.import_button = ttk.Button(button_frame, text="Import GML to Neo4j", 
                                       command=self.start_import, style="Accent.TButton")
        self.import_button.pack(side=tk.LEFT, padx=(0, 10))
        
        test_button = ttk.Button(button_frame, text="Test Connection", 
                               command=self.test_connection)
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_log_button = ttk.Button(button_frame, text="Clear Log", 
                                    command=self.clear_log)
        clear_log_button.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Import Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initial log message
        self.log("🔄 GML to Neo4j Importer ready. Select a GML file and configure your Neo4j connection.")
        
    def browse_file(self):
        """Open file browser to select GML file"""
        filename = filedialog.askopenfilename(
            title="Select GML File",
            filetypes=[
                ("GML files", "*.gml"),
                ("XML files", "*.xml"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.gml_file_path.set(filename)
            self.log(f"📁 Selected file: {filename}")
    
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def test_connection(self):
        """Test Neo4j connection"""
        self.log("🔍 Testing Neo4j connection...")
        
        try:
            from neo4j import GraphDatabase
            
            # Test connection
            driver = GraphDatabase.driver(
                self.neo4j_url.get(),
                auth=(self.neo4j_user.get(), self.neo4j_password.get())
            )
            
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            driver.close()
            self.log("✅ Neo4j connection successful!")
            messagebox.showinfo("Success", "Neo4j connection successful!")
            
        except Exception as e:
            error_msg = f"❌ Connection failed: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Connection Error", f"Failed to connect to Neo4j:\n{str(e)}")
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.neo4j_url.get().strip():
            messagebox.showerror("Validation Error", "Please enter Neo4j URL")
            return False
            
        if not self.neo4j_user.get().strip():
            messagebox.showerror("Validation Error", "Please enter Neo4j username")
            return False
            
        if not self.neo4j_password.get().strip():
            messagebox.showerror("Validation Error", "Please enter Neo4j password")
            return False
            
        if not self.gml_file_path.get().strip():
            messagebox.showerror("Validation Error", "Please select a GML file")
            return False
            
        return True
    
    def start_import(self):
        """Start the import process in a separate thread"""
        if not self.validate_inputs():
            return
            
        # Disable import button
        self.import_button.config(state='disabled')
        self.progress.start()
        
        # Start import in separate thread
        import_thread = threading.Thread(target=self.run_import)
        import_thread.daemon = True
        import_thread.start()
    
    def run_import(self):
        """Run the import process"""
        try:
            self.log("🚀 Starting GML import process...")
            
            # Create custom importer with GUI connection details
            class CustomGMLImporter(GMLToNeo4jImporter):
                def __init__(self, gml_file, uri, auth):
                    self.gml_file_path = gml_file
                    from neo4j import GraphDatabase
                    self.driver = GraphDatabase.driver(uri, auth=auth)
                    
                    # XML namespaces
                    self.namespaces = {
                        'gml': 'http://www.opengis.net/gml/3.2',
                        'un': 'http://www.opengis.net/citygml/utility-network/2.0',
                        'core': 'http://www.opengis.net/citygml/2.0',
                        'xlink': 'http://www.w3.org/1999/xlink'
                    }
                    
                    # Storage for parsed data
                    self.networks = []
                    self.feature_graphs = []
                    self.nodes = []
                    self.interior_links = []
                    self.connections = []
                    self.abstract_features = []
            
            # Create importer instance
            importer = CustomGMLImporter(
                self.gml_file_path.get(),
                self.neo4j_url.get(),
                (self.neo4j_user.get(), self.neo4j_password.get())
            )
            
            # Capture output
            output_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                # Run import
                importer.import_gml_to_neo4j(clear_existing=self.clear_database.get())
            
            # Get captured output
            output = output_buffer.getvalue()
            
            # Log the output
            for line in output.split('\n'):
                if line.strip():
                    self.root.after(0, lambda l=line: self.log(l))
            
            # Show success message
            self.root.after(0, self.import_success)
            
        except Exception as e:
            error_msg = f"❌ Import failed: {str(e)}"
            self.root.after(0, lambda: self.log(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Import Error", f"Import failed:\n{str(e)}"))
            
        finally:
            # Re-enable import button and stop progress
            self.root.after(0, self.import_finished)
    
    def import_success(self):
        """Handle successful import"""
        self.log("🎉 GML import completed successfully!")
        messagebox.showinfo("Success", 
                          "GML file has been successfully imported to Neo4j!\n\n"
                          "You can now view your data in Neo4j Browser or any Neo4j client.")
    
    def import_finished(self):
        """Handle import completion (success or failure)"""
        self.import_button.config(state='normal')
        self.progress.stop()

def main():
    """Run the GUI application"""
    root = tk.Tk()
    
    # Set app icon and style
    try:
        # Try to set a nice style
        style = ttk.Style()
        style.theme_use('clam')  # or 'alt', 'default', 'classic'
    except:
        pass
    
    app = GMLImporterGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main() 