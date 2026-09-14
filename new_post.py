"""Create a draft without overwriting existing files: python new_post.py 'My title'."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import unicodedata


def main():
    parser = argparse.ArgumentParser(description='Create a draft Markdown blog post.')
    parser.add_argument('title')
    parser.add_argument('--slug', help='Optional lowercase URL slug, e.g. nozzle-design-notes')
    args = parser.parse_args()
    normalized = unicodedata.normalize('NFKD', args.title).encode('ascii', 'ignore').decode()
    slug = args.slug or re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        parser.error('Provide --slug with lowercase letters, numbers, and single hyphens.')
    folder = Path(__file__).resolve().parent / 'posts'
    folder.mkdir(exist_ok=True)
    dest = folder / f'{date.today().isoformat()}-{slug}.md'
    content = f'''---
title: {json.dumps(args.title, ensure_ascii=False)}
slug: {json.dumps(slug)}
date: "{date.today().isoformat()}"
summary: "Write a short description."
tags: ["Research notes"]
draft: true
---

Write your introduction here.

## First section

'''
    try:
        with dest.open('x', encoding='utf-8') as stream:
            stream.write(content)
    except FileExistsError:
        parser.error(f'{dest.name} already exists; choose a different slug.')
    print(f'Created {dest.relative_to(folder.parent)}. Set draft: false when ready to publish.')


if __name__ == '__main__':
    main()
