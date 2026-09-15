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


def external(url, label, cls='', icon=True):
    return f'<a class="{E(cls)}" href="{E(url)}" target="_blank" rel="noopener noreferrer">{label}{EXTERNAL if icon else ""}<span class="sr-only"> (opens in a new tab)</span></a>'


def text_link(url, label):
    return f'<a class="text-link" href="{E(url)}">{E(label)}{ARROW}</a>'


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
    schema = {
        '@context': 'https://schema.org', '@type': 'Person', 'name': P['name'],
        'jobTitle': P['role'], 'affiliation': {'@type': 'CollegeOrUniversity', 'name': P['university']},
        'sameAs': [P['linkedin'], P['scholar'], P['orcid']],
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
    <div class="topbar"><span class="topbar-label"><span class="academic-site">Academic profile</span><span class="separator academic-site" aria-hidden="true">/</span><span>{'Blog' if post else E(title)}</span></span>{external(P['scholar'], 'Google Scholar')}</div>
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
    bio = ''.join(f'<p>{E(paragraph)}</p>' for paragraph in P['biography'])
    interests = ''.join(f'<li>{E(item)}</li>' for item in P['research_interests'])
    return f'''<header class="page-header home-header"><p class="eyebrow">{E(P['field'].upper())} / {E(P['university'].upper())}</p><h1>{E(P['name'])}</h1><p class="home-role">{E(P['home_role'])}<br>{E(P['location'])}</p></header>
<div class="home-grid"><div class="biography"><p class="opening">{E(P['tagline'])}</p>{bio}{text_link('/research/', 'Explore my research')}</div>
<aside class="appointment" aria-label="Current affiliation"><p class="small-label">Current affiliation</p><div><h2>{E(P['laboratory'])}</h2><p class="university">{E(P['university'])}</p></div><dl><dt>Department</dt><dd>{E(P['field'])}</dd><dt>Advisor</dt><dd>{E(P['advisor'])}</dd><dt>Graduate researcher since</dt><dd>{E(P['researcher_since'])}</dd></dl></aside></div>
<div class="interests"><p class="section-label">Research interests</p><ul class="interest-list">{interests}</ul></div>'''


def research():
    return header('02', 'Research', 'Flow, fiber orientation, and the manufacturing of polymer composites.') + f'''
<p class="research-intro">My work examines how nozzle geometry and incoming fiber alignment influence the structure of an extruded composite.</p>
<div class="section-heading"><h2>Research directions</h2><span class="meta">Additive manufacturing</span></div>
<article class="research-row"><span class="research-index" aria-hidden="true">01</span><div><h3>Controlling fiber alignment through nozzle design</h3><p>I investigate adjustable orifice gaps in fused filament fabrication. Numerical flow analysis connects changes in nozzle geometry with shear, extension, and fiber orientation in the extruded filament.</p>{text_link('/publications/#orifice-gap', 'Related publication')}<ul class="tags"><li>Nozzle geometry</li><li>CFD simulation</li><li>Extrusion flow</li></ul></div></article>
<article class="research-row"><span class="research-index" aria-hidden="true">02</span><div><h3>Understanding the role of inlet orientation</h3><p>I use flow visualization and tensor-based orientation modeling to examine how fibers entering a nozzle affect the alignment downstream. This work explores the transition between M-shaped and Gaussian-like orientation profiles.</p>{text_link('/publications/#inlet-orientation', 'Related publication')}<ul class="tags"><li>Fiber orientation</li><li>Flow visualization</li><li>Polymer composites</li></ul></div></article>
<div class="method-note"><p class="section-label">Methods</p><p>Computational fluid dynamics · Advani–Tucker orientation tensor modeling · Experimental flow visualization</p></div>'''


def publications():
    articles = {}
    for p in sorted(P['publications'], key=lambda item: int(item['year']), reverse=True):
        authors = ', '.join(f'<strong>{E(a)}</strong>' if a == P['name'] else E(a) for a in p['authors'])
        articles.setdefault(p['year'], []).append(f'''<article class="publication" id="{E(p['id'])}"><div class="pub-meta"><span class="pub-kind">Journal article</span><span>{E(p['date'])}</span></div><h2><a href="https://doi.org/{E(p['doi'])}" target="_blank" rel="noopener noreferrer">{E(p['title'])}<span class="sr-only"> (opens in a new tab)</span></a></h2><p class="authors">{authors}</p><p class="journal"><em>{E(p['journal'])}</em> <strong>{E(p['volume'])}</strong>, {E(p['location'])} ({p['year']})</p><p class="pub-summary">{E(p['summary'])}</p><div class="pub-links">{external('https://doi.org/' + p['doi'], 'Read paper', 'text-link')}<span class="doi">DOI: {E(p['doi'])}</span></div></article>''')
    groups = ''.join(f'<section class="pub-year" aria-label="Publications in {E(year)}"><h2 class="year-label">{E(year)}</h2><div>{"".join(items)}</div></section>' for year, items in articles.items())
    return header('03', 'Publications', 'Journal articles on flow and fiber alignment in additive manufacturing.') + f'''<div class="publication-toolbar"><p>Journal articles</p>{external(P['scholar'], 'View Google Scholar', 'text-link')}</div>{groups}'''


def education():
    items = []
    for d in P['education']:
        details = ''.join(f'<li>{E(line)}</li>' for line in d['details'])
        status_class = ' completed' if d['status'] == 'Completed' else ''
        items.append(f'''<article class="education-item"><div class="period">{E(d['period'])}<br><span class="status{status_class}">{E(d['status'])}</span></div><div><h2>{E(d['degree'])}</h2><p class="institution">{E(d['institution'])}</p><p class="location">{E(d['location'])}</p><ul class="degree-details">{details}</ul><p class="degree-dates">{E(d['dates'])}</p></div></article>''')
    return header('04', 'Education', 'Academic training in mechanical and aviation engineering.') + '<section aria-label="University education">' + ''.join(items) + '</section>'


def experience():
    sections = []
    for key, label in [('research_experience', 'Research appointments'), ('industry_experience', 'Industry experience')]:
        items = []
        for x in P[key]:
            team = f'<p class="team">{E(x["team"])}</p>' if x.get('team') else ''
            items.append(f'''<article class="experience-item"><div class="period">{E(x['period'])}</div><div><h3>{E(x['title'])}</h3><p class="institution">{E(x['institution'])}</p>{team}<p class="location">{E(x['location'])}</p><p class="description">{E(x['description'])}</p></div></article>''')
        sections.append(f'<section class="experience-section"><div class="section-heading"><h2>{label}</h2></div>{"".join(items)}</section>')
    return header('05', 'Experience', 'Research in fluid mechanics and manufacturing, with a background in aerospace engineering.') + ''.join(sections)


def contact():
    links = [
        (P['linkedin'], 'LinkedIn', 'Professional profile', 'in', ''),
        (P['scholar'], 'Google Scholar', 'Publications and citations', CAP, ''),
        (P['orcid'], 'ORCID', P['orcid_id'], 'iD', 'orcid-icon'),
        (P['researchgate'], 'ResearchGate', 'Research profile', 'RG', '')
    ]
    if P['email']:
        links.insert(0, ('mailto:' + P['email'], 'Email', P['email'], '@', ''))
    rows = []
    for url, title, subtitle, icon, cls in links:
        target = ' target="_blank" rel="noopener noreferrer"' if not url.startswith('mailto:') else ''
        accessible = '<span class="sr-only"> (opens in a new tab)</span>' if target else ''
        rows.append(f'<li><a href="{E(url)}"{target}><span class="profile-icon {cls}" aria-hidden="true">{icon}</span><span><span class="contact-title">{E(title)}</span><span class="contact-subtitle">{E(subtitle)}</span>{accessible}</span>{EXTERNAL}</a></li>')
    return header('07', 'Contact', 'Professional profiles and academic affiliation.') + f'''<div class="contact-layout"><ul class="contact-links">{"".join(rows)}</ul><aside class="contact-affiliation"><p class="section-label">Academic affiliation</p><h2>{E(P['university'])}</h2><p class="lab-name">{E(P['laboratory'])}<br>{E(P['department'])}</p><p>{E(P['location'])}</p><p>Advisor<br>{E(P['advisor'])}</p></aside></div>'''


def main():
    posts = load_posts(ROOT / 'posts')
    pages = [
        ('/', 'About', 'Quoc-Viet Le is a Ph.D. student at Chosun University researching computational fluid dynamics, fiber alignment, and additive manufacturing.', home()),
        ('/research/', 'Research', 'Research by Quoc-Viet Le on nozzle design, inlet fiber orientation, flow visualization, and polymer composite additive manufacturing.', research()),
        ('/publications/', 'Publications', 'Journal publications by Quoc-Viet Le in Physics of Fluids and the Journal of Mechanical Science and Technology.', publications()),
        ('/education/', 'Education', 'Education of Quoc-Viet Le: Ph.D. studies in Mechanical Engineering at Chosun University and a B.S. in Aviation Engineering at Hanoi University of Science and Technology.', education()),
        ('/experience/', 'Experience', 'Research and industry experience of Quoc-Viet Le, including Chosun University and Hanoi University of Science and Technology.', experience()),
        ('/blog/', 'Blog', 'Research notes and articles by Quoc-Viet Le.', index_content(posts, header, ARROW)),
        ('/contact/', 'Contact', 'Find Quoc-Viet Le on LinkedIn, Google Scholar, and ORCID. Heat Transfer Laboratory, Chosun University, Gwangju, South Korea.', contact())
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
