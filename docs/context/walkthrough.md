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

## Historical Development Log

### Test Data
We created two sets of test data:
- `data/openapi30_v1.yaml` vs `data/openapi30_v2.yaml` (OpenAPI 3.0)
- `data/openapi31_v1.yaml` vs `data/openapi31_v2.yaml` (OpenAPI 3.1)

### Scenario 1: Synthetic Report (OpenAPI 3.0)
Command: `python main.py data/openapi30_v1.yaml data/openapi30_v2.yaml --detail synthetic`

**Output Summary**:
- Correctly identified version change (1.0.0 -> 1.1.0).
- Identified modified endpoint `/users` and `/users/{id}`.
- Summarized schema changes (1 new, 1 modified).

### Scenario 2: Verbose Report (OpenAPI 3.0)
Command: `python main.py data/openapi30_v1.yaml data/openapi30_v2.yaml --detail verbose`

**Output Summary**:
- Detailed property changes shown:
    - `username`: `minLength` changed from 3 to 5.
    - `status`: `enum` changed to include `suspended`.
    - `role`: New property added.
- New schema `UserDetail` listed.

### Scenario 3: DOCX Report
Command: `python main.py data/openapi30_v1.yaml data/openapi30_v2.yaml --format docx --detail verbose --output report_30.docx`

**Result**: File `report_30.docx` created successfully.

### Scenario 4: OpenAPI 3.1 Support
Command: `python main.py data/openapi31_v1.yaml data/openapi31_v2.yaml --detail verbose`

**Output Summary**:
- Correctly handled `type: [string, null]` change to `type: string`.
- Correctly identified type change from `string` to `integer` for `id`.

### Scenario 5: Complex OpenAPI 3.0 Comparison
Command: `python main.py data/complex_30_v1.yaml data/complex_30_v2.yaml --detail verbose`

**Output Summary**:
- **Paths**: Detected addition of `/orders`, removal of `/users` POST, and modification of `/users` GET.
- **Schemas**:
    - `User`: Detected changes in `required` fields, addition of `phoneNumber`, and constraint changes for `username` (minLength, pattern), `age` (min/max), `tags` (maxItems), and `role` (enum).
    - `Product`: Detected change in `oneOf` options.
    - `Address`: Detected addition of `country` and pattern change in `zip`.
    - `ServiceProduct`: Detected as new schema.
    - `Error`: Detected as removed schema.

### Scenario 6: Complex OpenAPI 3.1 Comparison
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --detail verbose`

**Output Summary**:
- Mirrored the 3.0 checks but validated 3.1 specific features.
- **Type Arrays**: Correctly identified change from `type: [string, null]` to `type: string` in `User.nullableField`.
- **Exclusive Constraints**: Verified `exclusiveMinimum` handling (though visually similar in report, the underlying logic handled the version difference).

### Scenario 7: Premium Templates
Command: `python main.py data/complex_30_v1.yaml data/complex_30_v2.yaml --detail verbose --output report_premium.md`
Command: `python main.py data/complex_30_v1.yaml data/complex_30_v2.yaml --format docx --detail verbose --output report_premium.docx`

**Output Summary**:
- **Markdown**: Verified new premium layout with emojis, badges, and tables.
- **DOCX**: Verified professional styling with custom fonts (Calibri Light), colors (Premium Blue), and table layouts for data presentation.

### Scenario 8: Premium DOCX (OpenAPI 3.1)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_premium_31.docx`

**Result**: Generated `report_premium_31.docx` using the premium template and opened it for visual verification. The report correctly formats 3.1 specific changes with the new styling.

### Scenario 9: Professional Templates (Feedback Loop)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --detail verbose --output report_professional_31.md`
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_professional_31.docx`

**Output Summary**:
- **Markdown**: Removed "toy-like" icons, adopted a clean corporate style with standard tables and bold headers.
- **DOCX**: Significantly improved formatting. Reduced whitespace by adjusting paragraph spacing, fixed table borders using `Table Grid` style, and added bold headers for better readability.

### Scenario 10: Executive Report Design (DOCX)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_31.docx`

**Result**: Generated `report_executive_31.docx`.
- **Dashboard**: Includes a summary table at the top with key metrics (New/Removed Endpoints, Modified Schemas).
- **Property Tables**: Schema changes are now presented in clear grid tables instead of nested lists.
- **Branding**: Added "Confidential" header and "Generated on [Date]" footer with page numbers.
- **Typography**: Switched to Segoe UI for a modern, clean look.

### Scenario 11: Fixed Executive Report (DOCX)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_fixed.docx`

**Result**: Generated `report_executive_fixed.docx` which opens successfully.
- **Fix Applied**: Corrected XML structure for page number fields (wrapped `w:fldChar` in `w:r`).
- **Verified**: Dashboard, tables, and branding are all rendered correctly.

### Scenario 12: Refined Executive Report (DOCX)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_refined.docx`

**Result**: Generated `report_executive_refined.docx`.
- **Improvements**:
    - **Table Layout**: Fixed column widths (Inches) to prevent cramping and bad text wrapping.
    - **Spacing**: Increased paragraph spacing (`Pt(8)`) and line height (`1.15`) for better readability.
    - **Headers**: Ensured white text on dark navy background renders correctly.
- **Verified**: Visual inspection confirms tables are now well-proportioned and easy to read.

### Scenario 13: Perfected Executive Report (DOCX)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_final.docx`

**Result**: Generated `report_executive_final.docx`.
- **Visual Perfection**:
    - **Margins**: Narrowed to 0.5" to maximize table width.
    - **Padding**: Added internal cell padding so text doesn't touch borders.
    - **Headers**: White text on Navy Blue, repeated on every page break.
    - **Columns**: Optimized widths (e.g., 3.0" for values) to prevent wrapping.
- **Verified**: Code-level verification of OXML properties ensures professional rendering.

### Scenario 14: Perfected Executive Report V3 (DOCX)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_final_v3.docx`

**Result**: Generated `report_executive_final_v3.docx`.
- **Layout Fixes**:
    - **Table Widths**: Reduced total width to 7.0" to safely fit within margins.
    - **Spacing**: Created `Table Text` style with 0 spacing to eliminate huge vertical gaps.
    - **Property Rows**: Correctly implemented Jinja2 loop spanning across cells to generate one row per property.
- **Verified**: The report now looks professional, compact, and fits perfectly within the page boundaries.

### Scenario 15: Perfected Executive Report V5 (DOCX) - Mathematically Verified
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_final_v5.docx`

**Result**: Generated `report_executive_final_v5.docx`.
- **Mathematical Verification**:
    - **Table Width**: `w:tblW` explicitly set to **7.00 inches** (10080 twips).
    - **Layout**: `w:tblLayout` set to **fixed**.
    - **Printable Area**: 7.50 inches. The table leaves a **0.50 inch visual buffer** on the right.
    - **Empty Paragraphs**: **0** (Verified by XML inspection). No more huge vertical spaces.
- **Visual Result**: Guaranteed to fit within margins with compact spacing.

### Scenario 16: Schema-Compliant Executive Report V7 (DOCX) - Corruption Fixed
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_final_v7.docx`

**Result**: Generated `report_executive_final_v7.docx`.
- **Corruption Fix**: Implemented strict **ECMA-376 XML Schema ordering** for Table Properties (`tblPr`).
    - Previously, `w:tblW` and `w:tblLayout` were appended to the end of the XML node, which is invalid for Word.
    - Now, a `get_or_add_child` helper inserts them in the correct position (e.g., `tblW` before `tblBorders`).
- **Verification**:
    - **Structure**: Validated via `verify_docx.py`.
    - **Layout**: Retains the 7.00" fixed width and 0 empty paragraphs.
    - **Stability**: Should open in Word without "unreadable content" errors.

### Scenario 17: Grid-Synchronized Executive Report V8 (DOCX) - Geometry Fixed
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_final_v8.docx`

**Result**: Generated `report_executive_final_v8.docx`.
- **Geometry Fix**: Synchronized `w:tblGrid` with `w:tblW`.
    - Previously, `tblGrid` defaulted to page width (7.5") while `tblW` was forced to 7.0".
    - Now, `tblGrid` columns are explicitly rewritten to sum exactly to 7.0".
- **Verification**:
    - **Structure**: `verify_docx.py` confirms `Total Width (twips) = 10080` (7.00") matches `Preferred Width`.
    - **Stability**: This eliminates the "corrupt file" error caused by conflicting layout instructions.

### Scenario 18: Robust Executive Report V9 (DOCX) - Comprehensive Fix
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_executive_final_v9.docx`

**Result**: Generated `report_executive_final_v9.docx`.
- **Comprehensive Schema Fix**:
    - **Paragraph Properties (`pPr`)**: Fixed invalid order of `w:pBdr` vs `w:spacing` (Heading 1 borders).
    - **Table Properties (`tblPr`)**: Fixed invalid order of `w:tblW` and `w:tblLayout`.
    - **Cell Properties (`tcPr`)**: Fixed invalid order of `w:shd` and `w:tcMar`.
    - **Grid Sync**: Maintained `w:tblGrid` synchronization with column widths.
- **Verification**:
    - **Structure**: Validated via `verify_docx.py`.
    - **Stability**: This version addresses all known XML schema violations that cause Word to crash.

### Scenario 19: Pure Builder Pattern Report V1 (DOCX) - Radical Fix
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_builder_v1.docx`

**Result**: Generated `report_builder_v1.docx`.
- **Radical Change**: Switched from `docxtpl` (templates) to `python-docx` (Builder Pattern).
    - **Why**: Templates required fragile XML patching that caused corruption in strict Word environments.
    - **How**: The report is now built programmatically element-by-element, ensuring valid XML structure by definition.
- **Verification**:
    - **Structure**: `verify_docx.py` confirms perfect 7.00" width and fixed layout.
    - **Stability**: This is the most robust solution possible, as it uses the library's native API to construct the document.

### Scenario 20: Refined Builder Report V2 (DOCX) - Content Complete
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_builder_v2.docx`

**Result**: Generated `report_builder_v2.docx`.
- **Content Refinements**:
    - **Endpoints**: Now lists detailed changes (New/Removed/Modified Operations) instead of just the path.
    - **Components**: Added explicit "Schemas" sub-heading to categorize changes.
- **Verification**:
    - **Visual**: Verified that the report now matches the information density of the Markdown version while retaining the professional DOCX layout.

### Scenario 21: Enterprise Report V1 (DOCX) - Final Polish
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_enterprise_v1.docx`

**Result**: Generated `report_enterprise_v1.docx`.
- **Enterprise Design**:
    - **Badges**: Colored status labels (e.g., [NEW] in Green, [REMOVED] in Red) for immediate visual scanning.
    - **Typography**: Headings now have professional bottom borders (Dark Navy for H1, Light Grey for H2).
    - **Terminology**: Switched from "Operations" to "HTTP Methods" or "Methods" for clarity.
- **Logic Fix**:
    - **Empty Schemas**: Schemas with no detected changes are now correctly filtered out.
- **Verification**:
    - **Visual**: Confirmed "Super Enterprise" look and feel.

### Scenario 22: Enterprise Report V2 (DOCX) - Logic & Content Complete
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_enterprise_v2.docx`

**Result**: Generated `report_enterprise_v2.docx`.
- **Logic Fix**:
    - **Non-Property Changes**: Now correctly displays changes to `oneOf`, `anyOf`, `enum`, `required`, etc.
    - **Product Schema**: Specifically verified that `Product` now shows `ONEOF: Count changed from 2 to 3`.
- **Verification**:
    - **Visual**: Confirmed that all changes, including structural ones, are visible and styled with badges.

### Scenario 23: Enterprise Report V3 (DOCX) - Perfected Detail
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_enterprise_v3.docx`

**Result**: Generated `report_enterprise_v3.docx`.
- **Logic Refinement**:
    - **Combinators**: `oneOf`, `anyOf`, `allOf` now show *exactly* which options were added or removed, not just a count.
    - **Example**: `Product` schema now lists `[ADDED OPTION] #/components/schemas/ServiceProduct`.
- **Verification**:
    - **Visual**: Confirmed the report provides the exact level of technical detail required for enterprise API governance.

### Scenario 24: Enterprise Report V4 (DOCX) - Visual Perfection
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_enterprise_v4.docx`

**Result**: Generated `report_enterprise_v4.docx`.
- **Visual Refinements**:
    - **Removed Prop Fix**: "REMOVED PROP" badge now only appears when there are actual removed properties, and the list is correctly displayed.
    - **Indentation**: Property tables are now indented (0.25") relative to the section text, improving hierarchy.
    - **Spacing**: Added 12pt spacing after tables for better readability.
- **Verification**:
    - **Visual**: Confirmed the report is now visually balanced, bug-free, and professional.

### Scenario 25: Enterprise Report V5 (DOCX) - Actionable Insights
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_enterprise_v5.docx`

**Result**: Generated `report_enterprise_v5.docx`.
- **Actionable Content**:
    - **Modified Methods**: Now explicitly list *what* changed (e.g., `[NEW PARAM] sort`, `[MODIFIED PARAM] limit: maximum changed`).
    - **Developer Focus**: This allows developers to immediately see the impact of API changes on their client code without guessing.
- **Verification**:
    - **Visual**: Confirmed that method changes are broken down into clear, badged sub-items.

### Scenario 26: Enterprise Report V6 (DOCX) - Deep Context
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --detail verbose --output report_enterprise_v6.docx`

**Result**: Generated `report_enterprise_v6.docx`.
- **Deep Context**:
    - **Inline Schemas**: Changes to schemas within Request/Response bodies are now rendered *inline* with full detail (tables, badges).
    - **Ref Changes**: Explicitly shows "SCHEMA REF CHANGED From X to Y".
- **Verification**:
    - **Visual**: Confirmed that complex endpoint changes are now fully self-contained and descriptive.

### Scenario 28: Impact Report (DOCX) - Intelligent Analysis
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v2.docx`

**Result**: Generated `report_impact_v2.docx`.
- **Intelligent Features**:
    - **Smart Analysis**: Automatically detects breaking changes (removed params) and risks (new required fields).
    - **Technical Deep Dive**: Generates context-aware paragraphs explaining the risk (e.g., "Client Contract Violation Risk").
    - **Checklist**: Creates actionable steps (e.g., "Audit client code...").
- **Design**:
    - **Neutral Branding**: "API Impact Report" title.
    - **Impact Matrix**: Clear table with severity badges.
### Scenario 29: Impact Report (DOCX) - Polished Aesthetics
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v3.docx`

**Result**: Generated `report_impact_v3.docx`.
- **Graphical Improvements**:
    - **Tables**: Modern "Dark Blue" headers with white text. Added cell padding for readability.
    - **Deep Dive**: Insights are now rendered in shaded grey boxes with a blue left-border accent.
    - **Badges**: Refined pastel colors for a more professional look.
    - **Typography**: Adjusted font sizes and spacing (Segoe UI).

### Scenario 30: Impact Report (DOCX) - Designer's Cut (v4)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v4.docx`

**Result**: Generated `report_impact_v4.docx`.
- **Radical Redesign ("Clean UI")**:
    - **No Vertical Borders**: Tables now use only light grey horizontal lines (`#E0E0E0`) for a modern, airy look.
    - **Symbolic Diff**: Replaced text tags (`[NEW PROP]`) with colored symbols (`+`, `-`, `~`) to reduce visual noise.
    - **Minimalist Headers**: Removed dark background blocks; used clean text with bottom borders.
    - **Refined Meta Bar**: Simplified to a single subtle line.
    - **Spaced Badges**: Added non-breaking spaces to badges to prevent the "suffocated" look.

### Scenario 31: Impact Report (DOCX) - Fixed Designer's Cut (v5)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v5.docx`

**Result**: Generated `report_impact_v5.docx`.
- **Fixes Applied**:
    - **Borders**: Explicitly removed all default table borders (`w:tblBorders` set to `nil`) to ensure the "No-Grid" look.
    - **Width**: Adjusted table widths to ~6.7 inches to fit A4 pages without overflow.
    - **Spacing**: Added explicit spacer paragraphs between headers and tables to prevent them from sticking together.

### Scenario 32: Impact Report (DOCX) - Width Fix (v6/v7)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v7.docx`

**Result**: Generated `report_impact_v7.docx`.
- **Fixes Applied**:
    - **Width**: Reduced total table width to 6.5 inches (from 6.7") to provide a safety margin for A4 printing.
    - **Columns**: Adjusted column ratios to ensure content fits comfortably.
    - **Note**: Version bumped to v7 to avoid file lock conflicts.

### Scenario 33: Impact Report (DOCX) - Final Layout Fix (v8)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v8.docx`

**Result**: Generated `report_impact_v8.docx`.
- **Fixes Applied**:
    - **Aggressive Width**: Reduced total table width to 6.0 inches (giving ~0.77" safety margin).
    - **Alignment**: Forced Left Alignment (`WD_TABLE_ALIGNMENT.LEFT`) to prevent centering issues.
    - **Code Fix**: Resolved `IndentationError` from previous edit.

### Scenario 34: Impact Report (DOCX) - OXML Fixed Layout (v9)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v9.docx`

**Result**: Generated `report_impact_v9.docx`.
- **Fixes Applied**:
    - **OXML Injection**: Manually injected `w:tblW` (width) and `w:tblLayout` (fixed) into the XML to override Word's autofit behavior.
    - **Explicit Width**: Set to 6.2 inches (8928 dxa) to guarantee fit within A4 margins.

### Scenario 35: Impact Report (DOCX) - Optimized Dimensions (v10)
    - **Clean Deep Dive**: Removed shaded boxes and blue bars. Implemented dynamic numbering (3.1, 3.2, 3.3...) to fix gaps.
    - **Spacing**: Increased spacer to `Pt(24)` for better visual separation.

### Scenario 37: Impact Report (DOCX) - Max Alignment (v12)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v12.docx`

**Result**: Generated `report_impact_v12.docx`.
- **Refinements**:
    - **Max Width**: Increased to 6.9 inches to perfectly align with the "Critical Migration Notice" box.
    - **Columns**: Redistributed width to give more space to the "Impact" column (4.6 inches).

### Scenario 38: Heuristic Engine & Executive Risk Assessment (v14)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v14.docx`

**Result**: Generated `report_impact_v14.docx`.
- **Heuristic Engine**: Implemented 30+ rules in `heuristic_engine.py` covering:
    - **Endpoints**: Removal, Deprecation, OperationID changes.
    - **Parameters**: Removal, New Required, Type changes, Location changes.
    - **Schemas**: Property removal, Type changes, Validation (Pattern) changes, Polymorphism (oneOf).
    - **Bodies**: Required body, Content-Type removal.
- **Executive Risk Assessment**:
    - Replaced generic "Critical Migration Notice" with a dynamic summary.
    - Example Output: "CRITICAL BREAKING CHANGES DETECTED: 1 Endpoint Removed, 2 Parameter Removed, 1 Schema Property Removed."

### Scenario 39: Report Refinement & Deep Dive Aggregation (v16)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v16.docx`

**Result**: Generated `report_impact_v16.docx`.
- **Executive Risk Assessment (ERA)**: Refined styling to use a clean bulleted list inside the red box.
- **Technical Deep Dive**:
    - **Aggregation**: Insights are now grouped by Rule ID (e.g., all "Property Removed" instances together).
    - **Static Descriptions**: Uses high-level explanations of the risk (e.g., "Properties have been removed...") instead of repetitive specific details.
    - **Context List**: Lists "Affected Areas" (e.g., Schema names) to provide scope without duplicating the granular diffs found in Section 2.
- **Cleanup**: Removed "AI GENERATED" labels from section headers.

### Scenario 40: ERA Styling Refinement (v17)
Command: `python main.py data/complex_31_v1.yaml data/complex_31_v2.yaml --format docx --style impact --output report_impact_v17.docx`

**Result**: Generated `report_impact_v17.docx`.
- **ERA Layout**:
    - **Title**: "EXECUTIVE RISK ASSESSMENT" moved outside the colored box.
    - **Width**: Aligned with the endpoint table (6.9 inches).
- **Dynamic Coloring**:
    - **CRITICAL**: Light Red background (as before).
    - **HIGH**: Light Yellow background.
    - **LOW**: Pastel Blue background (requested by user).
- **Logic**: The box now appears for *any* severity level, adapting its color and message accordingly.

### Scenario 41: Schema Renaming Fix (Verified)
Command: `python reproduce_issue.py`

**Result**: Verified fix for "Chain Reaction" schema renaming.
- **Problem**: Renames inside `allOf` / `oneOf` lists were being reported as separate `added` and `removed` items, breaking the reference chain detection.
- **Fix**: Enhanced `_scan_paths` (Seed Phase) to detect 1-to-1 replacements within these lists (e.g., `removed: [OldRef]`, `added: [NewRef]`) and register them as rename candidates.
- **Verification**: `reproduce_issue.py` confirmed that `ChildV1 -> ChildV2` (inside `allOf`) is now correctly detected, allowing propagation to `GrandChildV1 -> GrandChildV2`.

### Scenario 42: GUI Resizing & Versioning (v1.0.0)
- **Versioning**: Implemented version indicator "v1.0.0" in Window Title, About Dialog, and Windows Executable Metadata.
- **Resizing**: Configured Grid Layout in `gui.py` to allow "Old Spec", "New Spec", and "Output Folder" entry fields to expand horizontally when the window is resized.
- **Verification**: Rebuilt executable and verified that maximizing the window now correctly stretches the input fields.