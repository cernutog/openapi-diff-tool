import zipfile
import xml.etree.ElementTree as ET
import sys

def inspect_docx(docx_path):
    print(f"Inspecting {docx_path}...")
    with zipfile.ZipFile(docx_path, 'r') as z:
        xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        
        # Namespaces
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # 1. Check Table Layout
        tables = tree.findall('.//w:tbl', ns)
        print(f"Found {len(tables)} tables.")
        for i, tbl in enumerate(tables):
            tblPr = tbl.find('w:tblPr', ns)
            tblLayout = tblPr.find('w:tblLayout', ns)
            if tblLayout is not None:
                type_val = tblLayout.get(f"{{{ns['w']}}}type")
                print(f"Table {i+1}: Layout Type = {type_val}")
            
            # Check Table Width (tblW)
            tblW = tblPr.find('w:tblW', ns)
            if tblW is not None:
                w_val = int(tblW.get(f"{{{ns['w']}}}w"))
                print(f"Table {i+1}: Preferred Width (tblW) = {w_val} (approx {w_val/1440:.2f} inches)")
            else:
                print(f"Table {i+1}: Preferred Width = AUTO/MISSING")
                
            # Check widths
            grid = tbl.find('w:tblGrid', ns)
            if grid:
                cols = grid.findall('w:gridCol', ns)
                total_width = sum(int(c.get(f"{{{ns['w']}}}w")) for c in cols)
                print(f"Table {i+1}: Total Width (twips) = {total_width} (approx {total_width/1440:.2f} inches)")

        # 2. Check for Empty Paragraphs in Tables
        # This is a heuristic: finding paragraphs with no text run or empty text
        # specifically inside table cells
        rows = tree.findall('.//w:tr', ns)
        empty_paras = 0
        for row in rows:
            cells = row.findall('w:tc', ns)
            for cell in cells:
                paras = cell.findall('w:p', ns)
                if len(paras) > 1:
                    # Check if any are empty
                    for p in paras:
                        runs = p.findall('w:r', ns)
                        text = "".join([t.text for r in runs for t in r.findall('w:t', ns) if t.text])
                        if not text.strip():
                            # print(f"Found empty paragraph in table cell!")
                            empty_paras += 1
        
        print(f"Total potentially unwanted empty paragraphs in tables: {empty_paras}")

if __name__ == "__main__":
    inspect_docx(sys.argv[1])
