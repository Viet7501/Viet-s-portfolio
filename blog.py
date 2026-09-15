"""Load owner-authored Markdown posts; never include draft source in public output."""
from dataclasses import dataclass
from datetime import date, datetime
from html import escape
import math
from pathlib import Path
import re

import markdown
import yaml


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    date: date
    summary: str
    tags: tuple[str, ...]
    html: str
    minutes: int

    @property
    def route(self):
        return f'/blog/{self.slug}/'

    @property
    def display_date(self):
        return f'{self.date.day} {self.date:%B %Y}'


def load_posts(directory: Path) -> list[Post]:
    posts = []
    slugs = set()
    for source in sorted(directory.glob('*.md')):
        if source.name.startswith('_'):
            continue
        text = source.read_text(encoding='utf-8-sig')
        parts = re.split(r'^---\s*$', text, maxsplit=2, flags=re.MULTILINE)
        if len(parts) != 3 or parts[0].strip():
            raise ValueError(f'{source.name}: start the post with YAML metadata between --- lines.')
        meta = yaml.safe_load(parts[1])
        if not isinstance(meta, dict):
            raise ValueError(f'{source.name}: metadata must contain named fields.')
        draft = meta.get('draft', True)
        if not isinstance(draft, bool):
            raise ValueError(f'{source.name}: draft must be true or false, without quotation marks.')
        if draft:
            continue
        for key in ('title', 'summary'):
            if not isinstance(meta.get(key), str) or not meta[key].strip():
                raise ValueError(f'{source.name}: a published post requires a nonempty {key}.')
        slug = meta.get('slug', source.stem)
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError(f'{source.name}: slug must contain lowercase letters, numbers, and single hyphens.')
        if slug in slugs:
            raise ValueError(f'{source.name}: duplicate published slug {slug!r}.')
        slugs.add(slug)
        try:
            published = meta['date']
            if isinstance(published, datetime):
                raise ValueError('Use a date without a time.')
            if not isinstance(published, date):
                published = date.fromisoformat(str(published))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'{source.name}: date must use YYYY-MM-DD.') from exc
        tags = meta.get('tags', [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
            raise ValueError(f'{source.name}: tags must be a list of text labels.')
        body = parts[2].strip()
        if not body:
            raise ValueError(f'{source.name}: add article text before publishing.')
        html = markdown.markdown(body, extensions=['extra', 'sane_lists'], output_format='html')
        if re.search(r'<h1\b', html, flags=re.IGNORECASE):
            raise ValueError(f'{source.name}: use ## for sections; the title already supplies the page heading.')
        minutes = max(1, math.ceil(len(re.findall(r'\S+', body)) / 220))
        posts.append(Post(slug, meta['title'].strip(), published, meta['summary'].strip(),
                          tuple(tags), html, minutes))
    return sorted(posts, key=lambda post: (post.date, post.slug), reverse=True)


def index_content(posts: list[Post], heading, arrow: str) -> str:
    intro = heading('06', 'Blog', 'Research notes, methods, and ideas from my work in engineering.')
    editor_button = '''<a class="blog-editor-button" href="/admin/" aria-label="Create a new blog post"><span aria-hidden="true">+</span> New post</a>'''
    if not posts:
        return intro + '''<section class="blog-empty" aria-label="No published articles"><p class="eyebrow">RESEARCH NOTEBOOK</p><h2>Notes from the research desk.</h2><p>Articles and research notes will appear here.</p></section>''' + editor_button
    rows = []
    for post in posts:
        tags = ''.join(f'<li>{escape(tag)}</li>' for tag in post.tags)
        rows.append(f'''<article class="blog-entry"><div class="blog-entry-meta"><time datetime="{post.date.isoformat()}">{escape(post.display_date)}</time><span>{post.minutes} min read</span></div><div><h2><a href="{post.route}">{escape(post.title)}</a></h2><p>{escape(post.summary)}</p><ul class="tags">{tags}</ul><a class="text-link" href="{post.route}">Read article {arrow}</a></div></article>''')
    return intro + '<section class="blog-list" aria-label="Published articles">' + ''.join(rows) + '</section>' + editor_button


def article_content(post: Post, author: str, arrow: str) -> str:
    tags = ''.join(f'<li>{escape(tag)}</li>' for tag in post.tags)
    return f'''<article class="blog-article"><a class="text-link back-link" href="/blog/">{arrow} All articles</a><header class="article-header"><div class="pub-meta"><span class="pub-kind">Research notebook</span><time datetime="{post.date.isoformat()}">{escape(post.display_date)}</time><span>{post.minutes} min read</span></div><h1>{escape(post.title)}</h1><p class="article-summary">{escape(post.summary)}</p><p class="article-author">{escape(author)}</p><ul class="tags">{tags}</ul></header><div class="prose">{post.html}</div></article>'''
