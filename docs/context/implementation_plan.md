# Schema Rename Tie-Breaking Strategy

## Problem
The schema renaming detection fails for schemas that are referenced by multiple parents which map to different new versions.
Specifically, `OriginalTransactionReference29_EPC259-22_V3.0_DS08N` is referenced by both "Negative" (`DS08N`) and "Positive" (`DS08P`) parent schemas.
In the new spec (V4.0), these parents point to `...V4.0_DS08N` and `...V4.0_DS08P` respectively.
This results in two candidates for the single old schema:
1. `OriginalTransactionReference29_EPC259-22_V4.0_DS08N`
2. `OriginalTransactionReference29_EPC259-22_V4.0_DS08P`

The current logic strictly enforces a "Unique Target" constraint (`len(targets) == 1`) and drops ambiguous candidates, causing the propagation chain to break.

## Proposed Changes

### `openapi_diff_tool/comparator.py`

#### 1. Deterministic Resolution & Classification
We will resolve candidates based on **Content Equality** and **Diff Magnitude**.

**Rules:**
1.  **Collect Candidates**: Identify all `NewSchema` targets referenced by homologous parents.
2.  **Filter Identical**: Find candidates that are structurally identical to `OldSchema`.
3.  **Resolution**:
    *   **Case A: Exactly One Identical Candidate**
        *   **Action**: Select it.
        *   **Status**: **"Rename"** (Pure).
    *   **Case B: Multiple Identical Candidates**
        *   **Action**: Ambiguous. Resolve by **Voting**.
        *   **Mechanism**: Count how many parent schemas reference each candidate.
        *   **Selection**: Pick the candidate with the highest vote count.
        *   **Tie-Breaking**: If votes are equal, pick the first one (lexicographically) for stability.
    *   **Case C: No Identical Candidates (All Modified)**
        *   **Action**: Calculate **Diff Score** for each candidate (count of changes).
        *   **Selection**: Pick the candidate with the **Lowest Score**.
        *   **Tie-Breaking**: If scores are equal, pick the first one (lexicographically by name) to ensure stability.
        *   **Status**: **"Modification"**.
        *   **Result**: The winner is linked as "Modification", the losers remain "New".

#### 2. Explicit Diffing
*   **Rename**: Status "Rename", Diff empty.
*   **Modification**: Status "Modification", Diff contains changes.

#### Algorithm Update
```python
def _count_diff_size(diff):
    # Recursively count number of leaf changes
    if not isinstance(diff, dict): return 1
    count = 0
    for k, v in diff.items():
        if k in ['old', 'new'] and not isinstance(v, dict): # Leaf
            count += 1
        else:
            count += _count_diff_size(v)
    return count

# ... inside detection loop ...
identical_targets = [t for t in targets if _is_content_identical(old_def, _get_schema(new_spec, t))]

if len(identical_targets) == 1:
    # ... (Rename logic) ...
elif len(identical_targets) == 0:
    # No identical matches. Try Least Differences.
    best_target = None
    min_score = float('inf')
    
    # Sort targets for deterministic tie-breaking if scores are equal
    for t in sorted(targets):
        new_def = _get_schema(new_spec, t)
        diff = _compare_schema(old_def, new_def)
        score = _count_diff_size(diff)
        
        if score < min_score:
            min_score = score
            best_target = t
            
    if best_target:
        current_renames[old_name] = (best_target, "Modification")
```

#### Algorithm Update
```python
def _is_content_identical(old_s, new_s):
    return _compare_schema(old_s, new_s) == {}

# ... inside detection loop ...
identical_targets = [t for t in targets if _is_content_identical(old_def, _get_schema(new_spec, t))]

if len(identical_targets) == 1:
    # Found exactly one perfect match -> RENAME
    winner = identical_targets[0]
    current_renames[old_name] = (winner, "Rename")
elif len(identical_targets) > 1:
    # Multiple perfect matches -> Ambiguous (skip)
    pass
else:
    # No perfect matches. Check for single substitution.
    if len(targets) == 1:
        target = list(targets)[0]
        current_renames[old_name] = (target, "Modification")
    else:
        # Multiple different candidates -> Ambiguous (skip)
        pass

# ... storage ...
for old, (new, status) in final_renames.items():
    diff = _compare_schema(old_def, new_def)
    diff['__rename_info__'] = {'new_name': new, 'status': status}
    result.modified_components.setdefault('schemas', {})[old] = diff
```

## Verification Plan

### Automated Verification
1.  Run `reproduce_debug.py` (which uses the captured `debug_old_spec.yaml` and `debug_new_spec.yaml`).
2.  Verify that `OriginalTransactionReference29...` and its children (`CashAccount38...`, `AccountIdentification4Choice...`) are reported as `[OK] ... -> ...`.
3.  Verify that the total number of "Renamed Schemas" increases.

### Manual Verification
1.  Ask the user to run the GUI comparison again.
2.  The user should see a significant reduction in "Removed" and "New" schemas in the report, and better linking in the Synthetic/Analytic reports.

## Report Legend Implementation

### `analytic_generator.py`

We will add a "Legend of Changes" section immediately after the document title and meta bar.

**Legend Content:**
*   **ADDED**: New component found in the new specification.
*   **REMOVED**: Component from the old specification that is no longer present.
*   **MODIFIED**: Component that exists in both versions but has changed content.
*   **RENAMED**: Component that has changed name but is structurally identical (or very similar) to a removed component. It is treated as the *same* component for history purposes.

**Implementation Details:**
*   Insert a new method `_add_legend(self)` in `AnalyticDocxGenerator`.
*   Call this method in `generate()` after adding the title and meta bar.
*   Use a table or list to present the legend clearly with the corresponding badges/colors.

### `analytic_generator.py` (Styling Refinement)

To avoid confusion with status labels, we will change the styling of combinator keywords (`oneOf`, `allOf`, `anyOf`).

*   **Current**: Neutral Pill Badge (Light Grey) - still looks too much like a label.
*   **New**: **Keyword Style**.
    *   **Font**: Monospaced (e.g., Consolas or Courier New).
    *   **Weight**: Bold.
    *   **Color**: Dark Blue (`003366`) or similar.
    *   **No Background**: Removes the "badge" shape entirely.
*   **Action**: Modify `_render_schema_diff_details` to use this new text-only style for combinators.

### Legend Refinement
*   **Alignment**: Ensure vertical alignment of cells in the legend table is consistent (likely `WD_ALIGN_VERTICAL.CENTER`).
*   **Text**: Update `RENAMED` description to remove "(or very similar)" and strictly define it as "Structurally identical component that has been renamed". This reflects the current logic (voting on identicals) and reassures the user.

## Advanced Corporate Template Support

### Goal
Enable "drop-in" corporate branding via a `template.docx` file and user-defined variables, without cluttering the main UI.

### 1. Configuration & Preferences
*   **Storage**: `config.json` to store user-defined static variables (e.g., `company_name`, `author`).
*   **GUI**:
    *   Remove "Template File" input from main window.
    *   Add "Preferences" button.
    *   **Preferences Dialog**:
        *   Grid/Table to add/edit/remove Key-Value pairs (Static Variables).
        *   List of available Dynamic Variables (read-only reference).

### 2. Variable System
*   **Syntax**: Jinja2-style `{{ variable_name }}` in the DOCX template.
*   **Static Variables**: Loaded from `config.json`.
*   **Dynamic Variables**:
    *   `{{ date }}`: Current date (YYYY-MM-DD).
    *   `{{ time }}`: Current time (HH:MM).
    *   `{{ datetime }}`: Current timestamp.
    *   `{{ original_spec }}`: Filename of old spec.
    *   `{{ new_spec }}`: Filename of new spec.

### 3. Template Loading Logic
*   **Location**: Automatically look for `template.docx` in the application directory.
*   **Generators**:
    *   Remove `template_path` argument.
    *   In `__init__`, check `os.path.exists('template.docx')`.
    *   If found, load it. If not, use default blank document.

### 4. Variable Substitution
*   Implement `_replace_variables(self, doc)` method in base generator.
*   Iterate through:
    *   Body Paragraphs
    *   Tables
    *   Headers (all sections)
    *   Footers (all sections)
*   Perform text replacement for all known variables.

## Expanded Template System

### Goal
Support multiple templates, editable variables, and enriched standard variables to provide a more flexible and user-friendly customization experience.

### 1. Multiple Templates
*   **Logic**: Generators will look for specific template files first, then fall back to `template.docx`, then default.
    *   `SyntheticDocxGenerator` -> `template_synthetic.docx`
    *   `AnalyticDocxGenerator` -> `template_analytic.docx`
    *   `ImpactDocxGenerator` -> `template_impact.docx`
*   **Implementation**: Update `__init__` in each generator to check for its specific template file.

### 2. GUI Enhancements (Preferences)
*   **Editable Variables**:
    *   Add "Edit" button to `PreferencesDialog`.
    *   Allow double-clicking a row to edit.
    *   Pre-fill the Add/Edit dialog with the selected key/value.
*   **Variable Selection Helper**:
    *   Add a "Insert Standard Variable" dropdown (Combobox) in the Add/Edit dialog.
    *   Selecting an item appends the placeholder (e.g., `{{ date }}`) to the Value field.

### 3. Enriched Standard Variables
*   **New Variables**:
    *   `{{ user }}`: Current OS user (`os.getlogin()` or `getpass.getuser()`).
    *   `{{ platform }}`: OS Platform (`sys.platform`).
    *   `{{ file_size_old }}`: Size of old spec (formatted).
    *   `{{ file_size_new }}`: Size of new spec (formatted).
    *   `{{ tool_version }}`: "1.0.0" (or similar).
*   **Implementation**: Update `_process_template_variables` in all generators.

## Deployment Plan (PyInstaller)
To distribute the application as a standalone `.exe`:

### 1. Resource Handling
*   **Problem**: When frozen, `__file__` points to a temporary directory or the exe itself.
*   **Solution**: Update `gui.py` to use a helper function `resource_path()` that checks `sys._MEIPASS` (PyInstaller's temp folder) before falling back to `os.path.abspath(".")`.

### 2. Icon Conversion
*   Windows Executables require `.ico` files.
*   We will create a `build_exe.py` script that:
    1.  Converts `app_icon.png` to `app_icon.ico` using `Pillow`.
    2.  Runs `PyInstaller`.

### 3. PyInstaller Configuration
*   **Command**: `pyinstaller --noconfirm --onefile --windowed --icon "app_icon.ico" --add-data "app_icon.png;." --name "OpenAPIDiffTool" gui.py`
*   **--onefile**: Single .exe file.
*   **--windowed**: No console window.
*   **--add-data**: Bundle the PNG for the GUI window icon.

### 4. Verification
*   Run the generated `.exe`.
*   Verify the icon appears in the taskbar and window title.
*   Verify reports are generated correctly.

## Application Polish (Phase 2)

### 5. Logging Control
*   **Requirement**: Reduce noise, optional debug logs.
*   **Solution**:
    *   Add `debug_mode` (bool) to `ConfigManager`.
    *   Add Checkbox in `PreferencesDialog`.
    *   Wrap `print` statements or `_log` calls with `if self.debug_mode:`.

### 6. GUI Modernization (Windows Standards)
*   **Widgets**: Replace `tk.*` widgets with `ttk.*` (Themed Tkinter) to use the native Windows visual styles (buttons, checkboxes, entries).
*   **High DPI**: Enable DPI awareness via `ctypes.windll.shcore.SetProcessDpiAwareness(1)` to prevent blurry text on modern screens.
*   **Menu Bar**: Move "Preferences" from a button to a standard `File > Preferences` menu.
*   **Layout**: Review padding and alignment for a cleaner "Microsoft" look (Segoe UI font is already used, which is good).
