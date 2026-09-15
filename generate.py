"""Render the academic profile and Markdown blog as independent static pages."""
from datetime import date
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote

from blog import article_content, index_content, load_posts

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
P = json.loads((ROOT / 'content.json').read_text())
BASE_PATH = os.environ.get('SITE_BASE_PATH', '').rstrip('/')
if BASE_PATH and (not re.fullmatch(r'(?:/[A-Za-z0-9._~-]+)+', BASE_PATH) or '..' in BASE_PATH.split('/')):
    raise ValueError('SITE_BASE_PATH must be a URL path such as /academic-profile, or empty.')
NAV = [('/', 'About'), ('/research/', 'Research'), ('/publications/', 'Publications'),
       ('/education/', 'Education'), ('/experience/', 'Experience'), ('/blog/', 'Blog'), ('/contact/', 'Contact')]
E = lambda value: escape(str(value), quote=True)
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
EXTERNAL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10"/></svg>'
MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M3 7h18M3 12h18M3 17h18"/></svg>'
CAP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m2 9 10-5 10 5-10 5L2 9Zm4 3v5c4 3 8 3 12 0v-5M22 9v7"/></svg>'
FAVICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#172f43"/><text x="32" y="43" text-anchor="middle" fill="white" font-family="Georgia,serif" font-size="34" letter-spacing="-3">QV</text></svg>'
INLINE_LINK_RE = re.compile(r'\[([^\]\n]+)\]\((https?://[^\s)]+)\)')


def external(url, label, cls='', icon=True):
    return f'<a class="{E(cls)}" href="{E(url)}" target="_blank" rel="noopener noreferrer">{label}{EXTERNAL if icon else ""}<span class="sr-only"> (opens in a new tab)</span></a>'


def text_link(url, label):
    return f'<a class="text-link" href="{E(url)}">{E(label)}{ARROW}</a>'


def optional_link(label, url):
    """Render plain text unless an optional URL is supplied."""
    if not url:
        return E(label)
    return (
        f'<a href="{E(url)}" target="_blank" rel="noopener noreferrer" '
        'style="color:inherit;text-decoration:underline;text-underline-offset:3px;">'
        f'{E(label)}<span class="sr-only"> (opens in a new tab)</span></a>'
    )


def inline_links(text):
    """Render safe [label](https://url) links while escaping all other text."""
    text = str(text)
    pieces = []
    last = 0
    for match in INLINE_LINK_RE.finditer(text):
        pieces.append(E(text[last:match.start()]))
        label, url = match.groups()
        pieces.append(
            f'<a href="{E(url)}" target="_blank" rel="noopener noreferrer">'
            f'{E(label)}<span class="sr-only"> (opens in a new tab)</span></a>'
        )
        last = match.end()
    pieces.append(E(text[last:]))
    return ''.join(pieces)


def nav(route):
    return '<ul class="nav-list">' + ''.join(
        f'<li><a href="{path}"' + (' aria-current="page"' if route == path or path == '/blog/' and route.startswith('/blog/') else '') +
        f'><span class="nav-number" aria-hidden="true">{i:02}</span>{label}</a></li>'
        for i, (path, label) in enumerate(NAV, 1)) + '</ul>'


def header(index, title, description):
    return f'<header class="page-header"><p class="eyebrow">{index} / {E(title.upper())}</p><h1>{E(title)}</h1><p class="lead">{E(description)}</p></header>'


def page(route, title, description, body, post=None):
    identity_visual = (f'<img class="portrait" src="{E(P["portrait"])}" alt="{E(P["portrait_alt"])}" width="96" height="112">'
                       if P['portrait'] else '<span class="monogram" aria-hidden="true">QV</span>')
    same_as = [P.get('linkedin'), P.get('scholar'), P.get('researchgate'), P.get('orcid')]
    same_as.extend(item.get('url') for item in P.get('additional_contacts', []) if isinstance(item, dict))
    affiliation = {'@type': 'CollegeOrUniversity', 'name': P['university']}
    if P.get('university_url'):
        affiliation['url'] = P['university_url']
    schema = {
        '@context': 'https://schema.org', '@type': 'Person', 'name': P['name'],
        'jobTitle': P['role'], 'affiliation': affiliation,
        'sameAs': [url for url in same_as if url],
        'knowsAbout': P['research_interests']
    }
    if P['email']:
        schema['email'] = P['email']
    if post:
        schema = {'@context': 'https://schema.org', '@type': 'BlogPosting',
                  'headline': post.title, 'description': post.summary,
                  'datePublished': post.date.isoformat(),
                  'author': {'@type': 'Person', 'name': P['name']},
                  'keywords': list(post.tags)}
    page_title = f'{title} | {P["name"]}' if route != '/' else f'{P["name"]} | Mechanical Engineering Researcher'
    document = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{E(page_title)}</title>
  <meta name="description" content="{E(description)}">
  <meta name="author" content="{E(P['name'])}">
  <meta name="theme-color" content="#172f43">
  <meta property="og:type" content="{'article' if post else 'website'}">
  <meta property="og:title" content="{E(page_title)}">
  <meta property="og:description" content="{E(description)}">
  <meta property="og:site_name" content="{E(P['name'])}">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{quote(FAVICON, safe='')}">
  <link rel="stylesheet" href="/assets/site.css">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False).replace('<', chr(92) + 'u003c')}</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<aside class="sidebar" aria-label="Profile and navigation">
  <a class="identity" href="/" aria-label="{E(P['name'])}, home">{identity_visual}<span class="identity-name">{E(P['name'])}</span><span class="identity-role">{E(P['short_role'])}</span></a>
  <p class="nav-caption">Academic profile</p>
  <nav aria-label="Main navigation">{nav(route)}</nav>
  <div class="sidebar-bottom"><p class="affiliation">{E(P['university'])}</p><p>{E(P['location'])}</p><div class="rail-links">{external(P['scholar'], 'Scholar', icon=False)}{external(P['orcid'], 'ORCID', icon=False)}{external(P['linkedin'], 'LinkedIn', icon=False)}</div></div>
</aside>
<header class="mobile-header"><a class="mobile-brand" href="/">{identity_visual}<span>{E(P['name'])}</span></a><details class="mobile-menu"><summary>Menu {MENU}</summary><nav aria-label="Mobile navigation">{nav(route)}</nav></details></header>
<div class="page">
  <div class="page-inner">
    <div class="topbar"><span class="topbar-label"><span class="academic-site">Academic profile</span><span class="separator academic-site" aria-hidden="true">/</span><span>{'Blog' if post else E(title)}</span></span><span style="display:flex;gap:18px;align-items:center;">{external(P['scholar'], 'Google Scholar')}<a href="/admin/" title="Edit website content">Edit site</a></span></div>
    <main id="main">{body}</main>
  </div>
  <footer class="site-footer"><div class="page-inner"><div class="footer-inner"><span>© {date.today().year} {E(P['name'])}</span>{external(P['orcid'], 'ORCID ' + E(P['orcid_id']), icon=False)}</div></div></footer>
</div>
</body>
</html>'''
    if BASE_PATH:
        document = re.sub(r'''\b(href|src)=(['"])/(?!/)''',
                          lambda match: f'{match[1]}={match[2]}{BASE_PATH}/', document)
    return document


def home():
    bio = ''.join(f'<p>{inline_links(paragraph)}</p>' for paragraph in P['biography'])
    interests = ''.join(f'<li>{E(item)}</li>' for item in P['research_interests'])
    laboratory = optional_link(P['laboratory'], P.get('laboratory_url'))
    university = optional_link(P['university'], P.get('university_url'))
    department = optional_link(P['field'], P.get('department_url'))
    advisor = optional_link(P['advisor'], P.get('advisor_url'))
    return f'''<header class="page-header home-header"><p class="eyebrow">{E(P['field'].upper())} / {E(P['university'].upper())}</p><h1>{E(P['name'])}</h1><p class="home-role">{E(P['home_role'])}<br>{E(P['location'])}</p></header>
<div class="home-grid"><div class="biography"><p class="opening">{inline_links(P['tagline'])}</p>{bio}{text_link('/research/', 'Explore my research')}</div>
<aside class="appointment" aria-label="Current affiliation"><p class="small-label">Current affiliation</p><div><h2>{laboratory}</h2><p class="university">{university}</p></div><dl><dt>Department</dt><dd>{department}</dd><dt>Advisor</dt><dd>{advisor}</dd><dt>Graduate researcher since</dt><dd>{E(P['researcher_since'])}</dd></dl></aside></div>
<div class="interests"><p class="section-label">Research interests</p><ul class="interest-list">{interests}</ul></div>'''


def research():
    r = P['research_page']
    rows = []
    for index, item in enumerate(r['directions'], 1):
        tags = ''.join(f'<li>{E(tag)}</li>' for tag in item.get('tags', []))
        publication_id = item.get('publication_id', '').strip()
        related = ''
        if publication_id:
            related = text_link('/publications/#' + publication_id, item.get('link_label') or 'Related publication')
        rows.append(
            f'''<article class="research-row"><span class="research-index" aria-hidden="true">{index:02}</span><div><h3>{E(item['title'])}</h3><p>{E(item['description'])}</p>{related}<ul class="tags">{tags}</ul></div></article>'''
        )
    methods = ' · '.join(E(method) for method in r.get('methods', []))
    return header('02', 'Research', r['lead']) + f'''
<p class="research-intro">{E(r['intro'])}</p>
<div class="section-heading"><h2>{E(r['section_title'])}</h2><span class="meta">{E(r['section_meta'])}</span></div>
{"".join(rows)}
<div class="method-note"><p class="section-label">Methods</p><p>{methods}</p></div>'''


def publications():
    articles = {}
    for p in sorted(P['publications'], key=lambda item: int(item['year']), reverse=True):
        authors = ', '.join(f'<strong>{E(a)}</strong>' if a == P['name'] else E(a) for a in p['authors'])
        articles.setdefault(p['year'], []).append(f'''<article class="publication" id="{E(p['id'])}"><div class="pub-meta"><span class="pub-kind">Journal article</span><span>{E(p['date'])}</span></div><h2><a href="https://doi.org/{E(p['doi'])}" target="_blank" rel="noopener noreferrer">{E(p['title'])}<span class="sr-only"> (opens in a new tab)</span></a></h2><p class="authors">{authors}</p><p class="journal"><em>{E(p['journal'])}</em> <strong>{E(p['volume'])}</strong>, {E(p['location'])} ({p['year']})</p><p class="pub-summary">{E(p['summary'])}</p><div class="pub-links">{external('https://doi.org/' + p['doi'], 'Read paper', 'text-link')}<span class="doi">DOI: {E(p['doi'])}</span></div></article>''')
    groups = ''.join(f'<section class="pub-year" aria-label="Publications in {E(year)}"><h2 class="year-label">{E(year)}</h2><div>{"".join(items)}</div></section>' for year, items in articles.items())
    return header('03', 'Publications', P.get('publications_intro', 'Journal articles on flow and fiber alignment in additive manufacturing.')) + f'''<div class="publication-toolbar"><p>Journal articles</p>{external(P['scholar'], 'View Google Scholar', 'text-link')}</div>{groups}'''


def education():
    items = []
    for d in P['education']:
        details = ''.join(f'<li>{E(line)}</li>' for line in d['details'])
        status_class = ' completed' if d['status'] == 'Completed' else ''
        items.append(f'''<article class="education-item"><div class="period">{E(d['period'])}<br><span class="status{status_class}">{E(d['status'])}</span></div><div><h2>{E(d['degree'])}</h2><p class="institution">{E(d['institution'])}</p><p class="location">{E(d['location'])}</p><ul class="degree-details">{details}</ul><p class="degree-dates">{E(d['dates'])}</p></div></article>''')
    return header('04', 'Education', P.get('education_intro', 'Academic training in mechanical and aviation engineering.')) + '<section aria-label="University education">' + ''.join(items) + '</section>'


def experience():
    sections = []
    for key, label in [('research_experience', 'Research appointments'), ('industry_experience', 'Industry experience')]:
        items = []
        for x in P[key]:
            team = f'<p class="team">{E(x["team"])}</p>' if x.get('team') else ''
            items.append(f'''<article class="experience-item"><div class="period">{E(x['period'])}</div><div><h3>{E(x['title'])}</h3><p class="institution">{E(x['institution'])}</p>{team}<p class="location">{E(x['location'])}</p><p class="description">{E(x['description'])}</p></div></article>''')
        sections.append(f'<section class="experience-section"><div class="section-heading"><h2>{label}</h2></div>{"".join(items)}</section>')
    return header('05', 'Experience', P.get('experience_intro', 'Research in fluid mechanics and manufacturing, with a background in aerospace engineering.')) + ''.join(sections)


def contact():
    links = [
        (P['linkedin'], 'LinkedIn', 'Professional profile', 'in', ''),
        (P['scholar'], 'Google Scholar', 'Publications and citations', CAP, ''),
        (P['orcid'], 'ORCID', P['orcid_id'], 'iD', 'orcid-icon'),
        (P['researchgate'], 'ResearchGate', 'Research profile', 'RG', '')
    ]
    for item in P.get('additional_contacts', []):
        if not isinstance(item, dict) or not item.get('label') or not item.get('url'):
            continue
        icon = item.get('icon') or item['label'][:2].upper()
        links.append((item['url'], item['label'], item.get('subtitle', ''), icon, ''))
    if P['email']:
        links.insert(0, ('mailto:' + P['email'], 'Email', P['email'], '@', ''))
    rows = []
    for url, title, subtitle, icon, cls in links:
        target = ' target="_blank" rel="noopener noreferrer"' if not url.startswith('mailto:') else ''
        accessible = '<span class="sr-only"> (opens in a new tab)</span>' if target else ''
        rows.append(f'<li><a href="{E(url)}"{target}><span class="profile-icon {cls}" aria-hidden="true">{icon}</span><span><span class="contact-title">{E(title)}</span><span class="contact-subtitle">{E(subtitle)}</span>{accessible}</span>{EXTERNAL}</a></li>')
    university = optional_link(P['university'], P.get('university_url'))
    laboratory = optional_link(P['laboratory'], P.get('laboratory_url'))
    department = optional_link(P['department'], P.get('department_url'))
    advisor = optional_link(P['advisor'], P.get('advisor_url'))
    return header('07', 'Contact', P.get('contact_intro', 'Professional profiles and academic affiliation.')) + f'''<div class="contact-layout"><ul class="contact-links">{"".join(rows)}</ul><aside class="contact-affiliation"><p class="section-label">Academic affiliation</p><h2>{university}</h2><p class="lab-name">{laboratory}<br>{department}</p><p>{E(P['location'])}</p><p>Advisor<br>{advisor}</p></aside></div>'''


def main():
    posts = load_posts(ROOT / 'posts')
    pages = [
        ('/', 'About', f'{P["name"]} is a {P["role"]} at {P["university"]} researching computational fluid dynamics, fiber alignment, and additive manufacturing.', home()),
        ('/research/', 'Research', f'Research by {P["name"]} on nozzle design, inlet fiber orientation, flow visualization, and polymer composite additive manufacturing.', research()),
        ('/publications/', 'Publications', f'Journal publications by {P["name"]} on flow and fiber alignment in additive manufacturing.', publications()),
        ('/education/', 'Education', f'Education and academic training of {P["name"]}.', education()),
        ('/experience/', 'Experience', f'Research and industry experience of {P["name"]}.', experience()),
        ('/blog/', 'Blog', f'Research notes and articles by {P["name"]}.', index_content(posts, header, ARROW)),
        ('/contact/', 'Contact', f'Professional profiles and academic affiliation for {P["name"]}.', contact())
    ]
    rendered = {route: page(route, title, description, body) for route, title, description, body in pages}
    for post in posts:
        rendered[post.route] = page(post.route, post.title, post.summary,
                                   article_content(post, P['name'], ARROW), post=post)
    # Blog HTML is generated output; removing it prevents withdrawn posts from remaining live.
    if (OUT / 'blog').exists():
        shutil.rmtree(OUT / 'blog')
    shutil.copytree(ROOT / 'assets', OUT / 'assets', dirs_exist_ok=True)
    for route, document in rendered.items():
        dest = OUT / route.strip('/') / 'index.html'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(document, encoding='utf-8')
    missing = '<div class="not-found"><p class="eyebrow">404 / PAGE NOT FOUND</p><h1>This page is not here.</h1><p>The address may have changed. You can return to my profile or use the navigation to find a section.</p>' + text_link('/', 'Back to profile') + '</div>'
    (OUT / '404.html').write_text(page('/404/', 'Page not found', 'This page could not be found.', missing), encoding='utf-8')
    (OUT / '.nojekyll').write_text('', encoding='utf-8')
    print(f'Rendered {len(pages)} sections, {len(posts)} published blog posts, and a 404 page.')


if __name__ == '__main__':
    main()
