import os
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from docxtpl import DocxTemplate
from comparator import DiffResult

class ReportGenerator:
    def __init__(self, template_dir: str = 'templates'):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, diff: DiffResult, format: str, detail: str, output_file: str, custom_template: Optional[str] = None):
        if custom_template:
            template_path = custom_template
            # If custom template is absolute, use it directly, otherwise look in current dir
            if not os.path.isabs(template_path):
                template_path = os.path.abspath(template_path)
        else:
            ext = 'docx' if format == 'docx' else 'md.j2'
            template_name = f"{detail}.{ext}"
            template_path = os.path.join(self.template_dir, template_name)

        if format == 'docx' or template_path.endswith('.docx'):
            self._generate_docx(diff, template_path, output_file)
        else:
            self._generate_md(diff, template_path, output_file)

    def _generate_md(self, diff: DiffResult, template_path: str, output_file: str):
        # For Jinja2, we need the template name relative to the loader root if it's in the dir
        # Or we can just create a new env for the specific file directory
        
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
        
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        
        output = template.render(diff=diff)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
        else:
            print(output)

    def _generate_docx(self, diff: DiffResult, template_path: str, output_file: str):
        doc = DocxTemplate(template_path)
        context = {'diff': diff}
        doc.render(context)
        doc.save(output_file)
