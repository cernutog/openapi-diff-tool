# OpenAPI Diff Tool

A powerful, GUI-based tool for comparing OpenAPI specifications (Swagger) and generating comprehensive reports (Synthesis, Analytical, Impact) in DOCX format.

![Application Icon](app_icon.png)

## Features

*   **Deep Comparison**: Analyzes changes in Paths, Endpoints, Schemas, Parameters, and more.
*   **Smart Rename Detection**: Identifies renamed schemas to avoid false positives (Added/Removed).
*   **Multiple Report Types**:
    *   **Synthesis Report**: High-level summary of changes.
    *   **Analytical Report**: Detailed breakdown of every modification.
    *   **Impact Report**: Focuses on breaking changes and implementation details.
*   **Corporate Templating**: Fully customizable DOCX templates with variable substitution.
*   **User-Friendly GUI**: Native Windows interface with drag-and-drop support (via file browsing).
*   **Standalone Executable**: No Python installation required for end-users.

## Installation

### For End Users
Simply download the latest release (`OpenAPIDiffTool.exe`) and run it.

### For Developers

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/openapi-diff-tool.git
    cd openapi-diff-tool
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python gui.py
    ```

## Usage

1.  **Select Specs**: Choose the Old and New OpenAPI YAML/JSON files.
2.  **Select Output**: Choose where to save the reports.
3.  **Configure**:
    *   Go to **File > Preferences** to set user variables (e.g., Company Name) and manage templates.
    *   Enable **Debug Mode** if you need detailed logs.
4.  **Generate**: Click **GENERATE REPORTS**.

## Building from Source

To create the standalone executable:

```bash
python build_exe.py
```

The output will be in the `dist/` folder.

## License

[MIT License](LICENSE)
