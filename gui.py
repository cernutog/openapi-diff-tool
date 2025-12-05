import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import sys
import ctypes

# Enable High DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Add current directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comparator import load_yaml, compare_specs
from report_generator import ReportGenerator
from impact_generator import ImpactDocxGenerator
from analytic_generator import AnalyticDocxGenerator
from synthetic_generator import SyntheticDocxGenerator
from config_manager import ConfigManager

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class PreferencesDialog:
    def __init__(self, parent, config_manager):
        self.top = tk.Toplevel(parent)
        self.top.title("Preferences")
        self.top.geometry("600x500")
        self.config_manager = config_manager
        self._set_icon(self.top)
        
        # Main Frame
        main_frame = tk.Frame(self.top, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Static Variables Section ---
        lbl_static = tk.Label(main_frame, text="Static Variables (User Defined)", font=("Segoe UI", 10, "bold"))
        lbl_static.pack(anchor="w", pady=(0, 5))
        
        # Treeview
        columns = ('key', 'value')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=8)
        self.tree.heading('key', text='Variable Name')
        self.tree.heading('value', text='Value')
        self.tree.column('key', width=150)
        self.tree.column('value', width=350)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Bind double click to edit
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # Buttons Frame
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Button(btn_frame, text="Add Variable", command=self._add_var).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Edit Selected", command=self._edit_var).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Delete Selected", command=self._delete_var).pack(side=tk.LEFT)
        
        # --- Templates Section ---
        lbl_templates = tk.Label(main_frame, text="Templates (Auto-Detected)", font=("Segoe UI", 10, "bold"))
        lbl_templates.pack(anchor="w", pady=(10, 5))
        
        tpl_frame = tk.Frame(main_frame)
        tpl_frame.pack(fill="x", pady=(0, 10))
        
        self._add_template_row(tpl_frame, "Synthesis", os.path.join("templates", "template_synthesis.docx"))
        self._add_template_row(tpl_frame, "Analytical", os.path.join("templates", "template_analytical.docx"))
        self._add_template_row(tpl_frame, "Impact", os.path.join("templates", "template_impact.docx"))
        self._add_template_row(tpl_frame, "Fallback", os.path.join("templates", "template.docx"))

        # --- Debug Mode Section ---
        # Moved here from Add/Edit dialog
        self.debug_var = tk.BooleanVar(value=self.config_manager.get_debug_mode())
        ttk.Checkbutton(main_frame, text="Enable Debug Mode (Verbose Logging)", variable=self.debug_var, command=self._save_debug_mode).pack(anchor="w", pady=(10, 0))

        self._load_vars()

    def _set_icon(self, window):
        try:
            ico_path = resource_path("app_icon.ico")
            if os.path.exists(ico_path):
                window.iconbitmap(ico_path)
            else:
                png_path = resource_path("app_icon.png")
                if os.path.exists(png_path):
                    icon = tk.PhotoImage(file=png_path)
                    window.iconphoto(False, icon)
        except Exception:
            pass

    def _save_debug_mode(self):
        self.config_manager.set_debug_mode(self.debug_var.get())

    def _load_vars(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for k, v in self.config_manager.get_all_variables().items():
            self.tree.insert('', tk.END, values=(k, v))

    def _on_double_click(self, event):
        self._edit_var()

    def _add_var(self):
        self._open_edit_dialog("Add Variable")

    def _edit_var(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        key, value = item['values']
        self._open_edit_dialog("Edit Variable", key, value)

    def _open_edit_dialog(self, title, key="", value=""):
        dialog = tk.Toplevel(self.top)
        dialog.title(title)
        dialog.geometry("500x200")
        self._set_icon(dialog)
        
        tk.Label(dialog, text="Variable Name (without {{ }}):").pack(anchor="w", padx=10, pady=(10, 0))
        entry_key = ttk.Entry(dialog, width=50)
        entry_key.insert(0, key)
        entry_key.pack(padx=10, pady=(0, 10), fill="x")
        if key: entry_key.config(state='disabled')
        
        tk.Label(dialog, text="Value:").pack(anchor="w", padx=10, pady=0)
        
        # Value Frame for Entry + Button
        val_frame = tk.Frame(dialog)
        val_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        entry_value = ttk.Entry(val_frame)
        entry_value.pack(side=tk.LEFT, fill="x", expand=True)
        entry_value.insert(0, value)
        
        def open_helper():
            self._show_std_var_helper(dialog, entry_value)

        ttk.Button(val_frame, text="Insert Std Var...", command=open_helper).pack(side=tk.LEFT, padx=(5, 0))
        
        def save():
            k = entry_key.get().strip()
            v = entry_value.get().strip()
            if k:
                self.config_manager.set_variable(k, v)
                self._load_vars()
                dialog.destroy()
                
        ttk.Button(dialog, text="Save", command=save).pack(pady=10)

    def _show_std_var_helper(self, parent, target_entry):
        helper = tk.Toplevel(parent)
        helper.title("Standard Variables")
        helper.geometry("350x400")
        self._set_icon(helper)
        
        tk.Label(helper, text="Double-click to insert:", font=("Segoe UI", 9, "bold")).pack(pady=5)
        
        frame_list = tk.Frame(helper)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame_list)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        listbox = tk.Listbox(frame_list, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        listbox.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        standard_vars = [
            "{{ date }}", "{{ time }}", "{{ user }}", "{{ platform }}",
            "{{ original_spec }}", "{{ new_spec }}",
            "{{ file_size_old }}", "{{ file_size_new }}",
            "{{ tool_version }}"
        ]
        
        for v in standard_vars:
            listbox.insert(tk.END, v)

        def on_select(event):
            selection = listbox.curselection()
            if selection:
                val = listbox.get(selection[0])
                target_entry.insert(tk.END, val)
                helper.destroy()
        
        listbox.bind("<Double-1>", on_select)

    def _add_template_row(self, parent, label, filename):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=2)
        
        tk.Label(row, text=f"{label}: {filename}", width=40, anchor="w").pack(side=tk.LEFT)
        
        exists = os.path.exists(filename)
        state = "normal" if exists else "disabled"
        text = "Open" if exists else "Not Found"
        
        btn = ttk.Button(row, text=text, state=state, command=lambda: self._open_template(filename))
        btn.pack(side=tk.RIGHT)

    def _open_template(self, filename):
        if os.path.exists(filename):
            os.startfile(filename)
        else:
            messagebox.showerror("Error", f"Template file not found: {filename}")

    def _delete_var(self):
        selected = self.tree.selection()
        if not selected:
            return
        if messagebox.askyesno("Confirm", "Delete selected variable?"):
            for item_id in selected:
                key = self.tree.item(item_id)['values'][0]
                self.config_manager.delete_variable(key)
            self._load_vars()


VERSION = "1.0.0"

class OpenAPIDiffGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"OpenAPI Diff Tool v{VERSION}")
        self.root.geometry("600x600")
        
        # Set AppUserModelID (Critical for Windows Taskbar Icon)
        try:
            import ctypes
            myappid = f'cernutog.openapi_diff_tool.v{VERSION}' # Unique ID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        # Set Icon (Try .ico first for Windows native look, then .png)
        try:
            # Try loading .ico for window icon (better for title bar)
            ico_path = resource_path("app_icon.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
            
            # Also load .png for taskbar/other contexts if needed
            png_path = resource_path("app_icon.png")
            if os.path.exists(png_path):
                icon = tk.PhotoImage(file=png_path)
                self.root.iconphoto(False, icon)
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")
        
        self.config_manager = ConfigManager()
        
        # Variables
        self.old_spec_path = tk.StringVar()
        self.new_spec_path = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "reports"))
        
        self.gen_markdown = tk.BooleanVar(value=True)
        self.gen_impact = tk.BooleanVar(value=True)
        self.gen_analytic = tk.BooleanVar(value=True)
        
        self._init_menu()
        self._init_ui()

    def _init_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Preferences...", command=self._open_preferences)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _show_about(self):
        msg = (
            f"OpenAPI Diff Tool\n"
            f"Version {VERSION}\n\n"
            f"A powerful tool for comparing OpenAPI specifications.\n\n"
            f"Copyright (c) 2025 Giuseppe Cernuto"
        )
        messagebox.showinfo("About", msg)

    def _init_ui(self):
        # Padding options
        pad_opts = {'padx': 10, 'pady': 5}
        
        # 1. File Selection Frame
        frame_files = tk.LabelFrame(self.root, text="Spec Files", padx=10, pady=10)
        frame_files.pack(fill="x", **pad_opts)
        frame_files.columnconfigure(1, weight=1) # Make column 1 expandable
        
        # Old Spec
        tk.Label(frame_files, text="Old Spec (YAML):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_files, textvariable=self.old_spec_path).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame_files, text="Browse...", command=self._browse_old).grid(row=0, column=2)
        
        # New Spec
        tk.Label(frame_files, text="New Spec (YAML):").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame_files, textvariable=self.new_spec_path).grid(row=1, column=1, padx=5, sticky="ew")
        ttk.Button(frame_files, text="Browse...", command=self._browse_new).grid(row=1, column=2)

        # 2. Output Configuration
        frame_out = tk.LabelFrame(self.root, text="Output Configuration", padx=10, pady=10)
        frame_out.pack(fill="x", **pad_opts)
        frame_out.columnconfigure(1, weight=1) # Make column 1 expandable
        
        tk.Label(frame_out, text="Output Folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_out, textvariable=self.output_dir).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame_out, text="Browse...", command=self._browse_out).grid(row=0, column=2)
        ttk.Button(frame_out, text="Open Folder", command=self._open_output_folder).grid(row=0, column=3, padx=5)

        # 3. Report Types
        frame_types = tk.LabelFrame(self.root, text="Report Types", padx=10, pady=10)
        frame_types.pack(fill="x", **pad_opts)
        
        # Synthesis
        frame_md = tk.Frame(frame_types)
        frame_md.pack(fill="x", pady=2)
        ttk.Checkbutton(frame_md, text="Synthesis Report", variable=self.gen_markdown).pack(side="left")
        self.btn_open_md = ttk.Button(frame_md, text="Open", state="disabled", command=lambda: self._open_report("report_synthesis.docx"))
        self.btn_open_md.pack(side="right", padx=5)

        # Analytical
        frame_ana = tk.Frame(frame_types)
        frame_ana.pack(fill="x", pady=2)
        ttk.Checkbutton(frame_ana, text="Analytical Report", variable=self.gen_analytic).pack(side="left")
        self.btn_open_ana = ttk.Button(frame_ana, text="Open", state="disabled", command=lambda: self._open_report("report_analytical.docx"))
        self.btn_open_ana.pack(side="right", padx=5)

        # Impact
        frame_imp = tk.Frame(frame_types)
        frame_imp.pack(fill="x", pady=2)
        ttk.Checkbutton(frame_imp, text="Impact Report", variable=self.gen_impact).pack(side="left")
        self.btn_open_imp = ttk.Button(frame_imp, text="Open", state="disabled", command=lambda: self._open_report("report_impact.docx"))
        self.btn_open_imp.pack(side="right", padx=5)

        # 4. Action (Preferences moved to Menu)
        frame_actions = tk.Frame(self.root)
        frame_actions.pack(fill="x", padx=20, pady=10)
        
        self.btn_generate = ttk.Button(frame_actions, text="GENERATE REPORTS", command=self._start_generation)
        self.btn_generate.pack(fill="x", expand=True)
        
        # 5. Log Area
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, state='disabled')
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def _browse_old(self):
        f = filedialog.askopenfilename(filetypes=[("YAML Files", "*.yaml *.yml")])
        if f: self.old_spec_path.set(f)

    def _browse_new(self):
        f = filedialog.askopenfilename(filetypes=[("YAML Files", "*.yaml *.yml")])
        if f: self.new_spec_path.set(f)

    def _browse_out(self):
        d = filedialog.askdirectory()
        if d: self.output_dir.set(d)

    def _open_output_folder(self):
        path = self.output_dir.get()
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Error", "Output directory does not exist.")

    def _open_report(self, path):
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Error", f"File not found: {path}")

    def _open_preferences(self):
        PreferencesDialog(self.root, self.config_manager)

    def _log(self, msg):
        # Always log to UI as per user request
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def _start_generation(self):
        # Validation
        if not self.old_spec_path.get() or not self.new_spec_path.get():
            messagebox.showerror("Error", "Please select both Old and New spec files.")
            return
            
        if not (self.gen_markdown.get() or self.gen_impact.get() or self.gen_analytic.get()):
            messagebox.showerror("Error", "Please select at least one report type.")
            return

        # Disable button
        self.btn_generate.config(state='disabled', text="Generating...")
        self.btn_open_md.config(state='disabled')
        self.btn_open_imp.config(state='disabled')
        self.btn_open_ana.config(state='disabled')
        
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        # Run in thread
        threading.Thread(target=self._generate_process, daemon=True).start()

    def _generate_process(self):
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            self._log("Loading specs...")
            spec1 = load_yaml(self.old_spec_path.get())
            spec2 = load_yaml(self.new_spec_path.get())
            
            self._log("Comparing specs...")
            debug_mode = self.config_manager.get_debug_mode()
            diff = compare_specs(spec1, spec2, debug_mode=debug_mode)
            
            out_dir = self.output_dir.get()
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            
            # Load Variables
            variables = self.config_manager.get_variables()
            
            # Synthesis DOCX
            if self.gen_markdown.get():
                self._log("Generating Synthesis Report (DOCX)...")
                filename = f"report_synthesis_{timestamp}.docx"
                out_path = os.path.join(out_dir, filename)
                
                gen = SyntheticDocxGenerator(
                    spec1=spec1, 
                    spec2=spec2, 
                    diff=diff, 
                    old_path=self.old_spec_path.get(), 
                    new_path=self.new_spec_path.get(), 
                    variables=variables,
                    template_path=os.path.join("templates", "template_synthesis.docx")
                )
                gen.generate(out_path)
                self._log(f" -> Created: {filename}")
                self.root.after(0, lambda p=out_path: self._configure_open_btn(self.btn_open_md, p))

            # Analytic DOCX
            if self.gen_analytic.get():
                self._log("Generating Analytical Report (DOCX)...")
                filename = f"report_analytical_{timestamp}.docx"
                out_path = os.path.join(out_dir, filename)
                gen = AnalyticDocxGenerator(
                    spec1=spec1, 
                    spec2=spec2, 
                    diff=diff, 
                    old_path=self.old_spec_path.get(), 
                    new_path=self.new_spec_path.get(), 
                    variables=variables,
                    template_path=os.path.join("templates", "template_analytical.docx")
                )
                gen.generate(out_path)
                self._log(f" -> Created: {filename}")
                self.root.after(0, lambda p=out_path: self._configure_open_btn(self.btn_open_ana, p))

            # Impact DOCX
            if self.gen_impact.get():
                self._log("Generating Impact Report (DOCX)...")
                filename = f"report_impact_{timestamp}.docx"
                out_path = os.path.join(out_dir, filename)
                gen = ImpactDocxGenerator(
                    old_spec=spec1, 
                    new_spec=spec2, 
                    diff=diff, 
                    old_path=self.old_spec_path.get(), 
                    new_path=self.new_spec_path.get(), 
                    variables=variables,
                    template_path=os.path.join("templates", "template_impact.docx")
                )
                gen.generate(out_path)
                self._log(f" -> Created: {filename}")
                self.root.after(0, lambda p=out_path: self._configure_open_btn(self.btn_open_imp, p))

            self._log("\nSUCCESS! All reports generated.")
            messagebox.showinfo("Success", "Reports generated successfully!")

        except Exception as e:
            import traceback
            error_msg = f"ERROR: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self._log(error_msg)
            
            # Write to debug log file only if debug mode is enabled
            if self.config_manager.get_debug_mode():
                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                with open(os.path.join(log_dir, "gui_debug.log"), "w", encoding="utf-8") as f:
                    f.write(error_msg)
                
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}\n\nSee gui_debug.log for details.")
        finally:
            self.root.after(0, lambda: self.btn_generate.config(state='normal', text="GENERATE REPORTS"))

    def _configure_open_btn(self, btn, path):
        btn.config(state='normal', command=lambda: self._open_report(path))

if __name__ == "__main__":
    root = tk.Tk()
    app = OpenAPIDiffGUI(root)
    root.mainloop()
