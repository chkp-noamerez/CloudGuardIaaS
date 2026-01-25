#!/usr/bin/env python3

import json
import os
from pathlib import Path
from urllib.parse import urlparse
import yaml

CP = 'Check Point'
DEFAULT_BUCKET = 'azure.templates'
DEFAULT_LAMBDA = 'azure.templates-lambda'
POOL_SIZE = 5
S3_URL = 'https://s3.console.aws.amazon.com/s3/buckets/{}?region=us-west-2&tab=objects'
SCRIPTS_DIR = 'scripts'
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'azure', 'templates'))
TEMPLATE_BODY = 'TemplateBody'
TEMPLATE_URL = 'TemplateURL'


class CFT:
    def __init__(self, template):
        if 'https://' in template:
            self.body = {TEMPLATE_URL: template}
            self.template = template
            self.content = None
            template_name = urlparse(template).path

        else:
            with open(template, 'r') as f:
                self.content = f.read()

            self.body = {TEMPLATE_BODY: self.content}
            self.template = load_dict_file(template)
            template_name = template

        self.template_name = os.path.basename(template_name)
        self.name = os.path.splitext(self.template_name)[0]
        self.path = os.path.dirname(template_name)[template_name.find(TEMPLATES_DIR) + len(TEMPLATES_DIR) + 1:]
        self.template_id = '-'.join([self.path, self.template_name])

    def __hash__(self):
        return hash(self.template_name)

    def __eq__(self, other):
        return isinstance(other, CFT) and self.template_name == other.template_name


def log(msg='', level=None):
    print(msg)


def load_dict(d):
    try:
        return yaml.load(d, Loader=yaml.BaseLoader)

    except yaml.YAMLError:
        return json.loads(d)

    except ValueError:
        raise Exception('Unknown dictionary format')


def load_dict_file(dict_file):
    if not os.path.isfile(dict_file):
        raise Exception(f'File {dict_file} was not found')

    _, ext = os.path.splitext(dict_file)
    with open(dict_file, 'r') as f:
        if ext in {'.yaml', '.yml'}:
            return yaml.load(f, Loader=yaml.BaseLoader)

        elif ext in {'.json', '.jsn'}:
            return json.load(f)

        else:
            raise Exception(f'Unknown dictionary format: {ext}')


def load_templates(templates):
    return [CFT(t) for t in templates]


def get_templates(path):
    templates = []
    for i in Path(path).rglob('*'):
        if str(i).endswith("mainTemplate.json") and "BUILD" in str(i):
            templates.append(str(i))

        if str(i).endswith("json") and "nestedtemplates" in str(i):
            templates.append(str(i))

    return templates


def load_all_templates(path=TEMPLATES_DIR):
    return load_templates(get_templates(path))
