from os import path
import jinja2

templates = ""


class Template(object):
    templates = object

    def __init__(self):
        pass

    def import_templates(self):
        modules_root_dir = path.join(path.dirname(path.abspath(__file__)), "modules")
        modules_template_dir = path.join(modules_root_dir, self.options['module_name'], 'templates')
        file_loader = jinja2.FileSystemLoader(modules_template_dir)
        self.templates = jinja2.Environment(loader=file_loader)
