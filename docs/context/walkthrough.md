# Walkthrough - OpenAPI Diff Tool

## Recent Changes

### Corporate Template Support (Enhanced)
The tool now supports a robust template system for corporate branding.

**Features:**
*   **Multiple Templates**: Automatically detects specific templates for each report type:
    *   `template_synthetic.docx`
    *   `template_analytic.docx`
    *   `template_impact.docx`
    *   Fallback: `template.docx`
*   **Preferences GUI**:
    *   **Edit Variables**: Double-click to modify existing values.
    *   **Helper**: Dropdown to insert standard variables (e.g., `{{ date }}`) without typing.
*   **Enriched Variables**:
    *   `{{ user }}`: Current OS user.
    *   `{{ platform }}`: OS Platform.
    *   `{{ file_size_old }} / {{ file_size_new }}`: Spec file sizes.
    *   `{{ tool_version }}`: Tool version.

**How to Use:**
1.  Create your DOCX templates with placeholders (e.g., `{{ company_name }}`, `{{ date }}`).
2.  Name them `template_synthetic.docx`, etc., and place them in the tool's folder.
3.  Open the GUI, click **Preferences**, and define your static variables (e.g., `company_name` = "Acme Corp").
4.  Generate reports!

### Renaming & Template Management
Refined naming conventions and improved template accessibility.

**Changes:**
*   **Report Names**:
    *   `Synthetic` -> `Synthesis` (File: `report_synthesis.docx`)
    *   `Analytic` -> `Analytical` (File: `report_analytical.docx`)
*   **Template Names**:
    *   `template_synthetic.docx` -> `template_synthesis.docx`
    *   `template_analytic.docx` -> `template_analytical.docx`
*   **Preferences GUI**:
    *   Added **Templates Section**: Lists all supported templates.
    *   **Open Button**: Allows opening templates directly from the GUI (enabled only if file exists).

### Application Polish
*   **Icon**: Added a custom application icon (`app_icon.png`) featuring a modern "diff" design.
*   **GUI**: The main window now displays this icon in the title bar and taskbar.

### Deployment (Executable)
Created a build process to generate a standalone `.exe`.

*   **Resource Handling**: Updated `gui.py` to use `resource_path()` for finding assets (like the icon) whether running as a script or frozen exe.
*   **Build Script**: Created `build_exe.py` which:
    1.  Installs dependencies (`pyinstaller`, `pillow`).
    2.  Converts `app_icon.png` to `app_icon.ico`.
    3.  Runs `PyInstaller` to create a single-file executable (`dist/OpenAPIDiffTool.exe`).

### Verification Results
*   **Icon Loading**: Verified `gui.py` loads `app_icon.png` using `tk.PhotoImage`.
*   **Error Handling**: Verified try/except block prevents crash if icon is missing.
    - **Schema Renames**: Standardized to `**NewSchema** (was OldSchema)`.
    - **Headers**: Removed "Confidential" labels.
    - **Table Headers**: Added light grey background (`#F2F2F2`).
- **Impact Report**: Improved summary formatting (pluralization, removed 'x' counts).

### GUI Enhancements
- **Reordering**: Reports are now ordered: Synthetic -> Analytic -> Impact.
- **Preferences**: Added dialog for managing template variables.
