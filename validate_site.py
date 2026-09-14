"""Check generated pages, navigation targets, and local assets before publication."""
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.h1 = 0
        self.main = 0
        self.title = ''
        self.in_title = False
        self.in_json = False
        self.json_parts = []
        self.active = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        self.h1 += tag == 'h1'
        self.main += tag == 'main'
        if tag == 'title':
            self.in_title = True
        if tag == 'script':
            self.in_json = attrs.get('type') == 'application/ld+json'
        if attrs.get('aria-current') == 'page':
            self.active.append(attrs.get('href'))
        for key in ('href', 'src'):
            if key in attrs:
                self.references.append(attrs[key])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script':
            if self.in_json:
                json.loads(''.join(self.json_parts))
                self.json_parts = []
            self.in_json = False

    def handle_data(self, value):
        if self.in_title:
            self.title += value
        if self.in_json:
            self.json_parts.append(value)


def validate(root: Path, base_path: str = ''):
    root = root.resolve()
    pages = {}
    for path in root.rglob('*.html'):
        parsed = Page()
        parsed.feed(path.read_text(encoding='utf-8'))
        pages[path] = parsed
        if parsed.h1 != 1 or parsed.main != 1 or not parsed.title:
            raise ValueError(f'{path}: expected one main heading, a main landmark, and a title.')
        if len(set(parsed.ids)) != len(parsed.ids):
            raise ValueError(f'{path}: duplicate HTML IDs.')
        if path.name != '404.html' and (len(parsed.active) != 2 or parsed.active[0] != parsed.active[1]):
            raise ValueError(f'{path}: desktop and mobile navigation must agree.')
    if not pages:
        raise ValueError('Build the site before validating it.')
    if len({page.title for page in pages.values()}) != len(pages):
        raise ValueError('Each page must have a unique title.')
    for path, parsed in pages.items():
        for reference in parsed.references:
            ref = urlsplit(reference)
            if ref.scheme or ref.netloc:
                continue
            url_path = unquote(ref.path)
            if url_path.startswith('/'):
                if base_path:
                    if not url_path.startswith(base_path + '/'):
                        raise ValueError(f'{path}: {reference} is missing the site base path.')
                    url_path = url_path[len(base_path):]
                target = root / url_path.lstrip('/')
            else:
                target = path.parent / url_path if url_path else path
            target = target.resolve()
            if root not in target.parents and target != root:
                raise ValueError(f'{path}: {reference} leaves the public output.')
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                raise ValueError(f'{path}: missing local target {reference}.')
            if ref.fragment and target in pages and unquote(ref.fragment) not in pages[target].ids:
                raise ValueError(f'{path}: missing anchor {reference}.')
    for route in ('', 'research', 'publications', 'education', 'experience', 'blog', 'contact'):
        if not (root / route / 'index.html').is_file():
            raise ValueError(f'Missing section route: /{route}')
    return len(pages)


if __name__ == '__main__':
    count = validate(Path(__file__).resolve().parent / 'dist', os.environ.get('SITE_BASE_PATH', '').rstrip('/'))
    print(f'Validated {count} HTML pages, local links, assets, structured data, and navigation.')
