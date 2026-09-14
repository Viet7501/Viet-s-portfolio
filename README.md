# Viet's-portfolio

Viet's public profile — Quoc-Viet Le's academic website and blog.

Seven independent sections: `/`, `/research/`, `/publications/`, `/education/`, `/experience/`, `/blog/`, and `/contact/`. Each published post has its own `/blog/article-slug/` address. Navigation and the mobile menu work without JavaScript.

## Publish on GitHub

Source repository: [Viet7501/Viet-s-portfolio](https://github.com/Viet7501/Viet-s-portfolio). After GitHub Pages setup and a successful deployment, the website address will be [viet7501.github.io/Viet-s-portfolio/](https://viet7501.github.io/Viet-s-portfolio/).

1. Open [Settings → Pages](https://github.com/Viet7501/Viet-s-portfolio/settings/pages). Under **Build and deployment → Source**, choose **GitHub Actions**.
2. Open [Actions → Publish academic website](https://github.com/Viet7501/Viet-s-portfolio/actions/workflows/pages.yml), then **Run workflow → main → Run workflow** for the first deployment. Subsequent commits to `main` automatically build and publish the website.

If the first run reports that the Pages site could not be found, complete step 1 and rerun it. The source upload itself does not enable GitHub Pages.

The workflow uploads only `dist/`. Draft Markdown, source code, tests, and the original profile PDF are not deployed to the website. GitHub Pages and the ChatGPT Site are independent: GitHub edits update GitHub Pages after setup, not the ChatGPT Site URL.

If you use a different repository name, the workflow handles the `/repository-name/` prefix automatically. For local project-path builds, set `SITE_BASE_PATH` to that prefix.

## Write a blog post in your browser

1. Open `posts` on GitHub. Choose **Add file → Create new file** and name it, for example, `2026-09-14-nozzle-design-notes.md`.
2. Copy `posts/_template.md` into the new file.
3. Fill in the title, date, summary, slug, and article text. Leave `draft: true` while writing.
4. Change to `draft: false` when ready, then **Commit changes** to `main`.
5. Once the Pages workflow succeeds, the post appears on `/blog/` and at `/blog/your-slug/`.

```yaml
---
title: "Notes on nozzle design"
slug: "nozzle-design-notes"
date: "2026-09-14"
summary: "A short introduction to the article."
tags: ["CFD", "Research notes"]
draft: true
---

Write your introduction here.

## First section

Continue your article here.
```

Use `##` for section headings; the title already supplies the main heading. Posts support links, images, tables, lists, block quotes, and fenced code. Slugs must be unique among published posts; keep them stable after publication.

Files starting with `_`, posts marked `draft: true`, and posts without a draft flag are omitted from the website. **Drafts in a public GitHub repository remain visible as source on GitHub.** Keep private notes outside a public repository.

The date controls display and sorting, not scheduled publication. `draft: false` publishes on the next successful build regardless of date. To withdraw a post, set `draft: true` or remove its file; the next build removes its generated page.

For a full browser editor, open [this repository in github.dev](https://github.dev/Viet7501/Viet-s-portfolio), or press `.` while viewing the repository. Edit multiple files and commit them together there.

## Customize the website

| Change | Source file |
| --- | --- |
| Profile, biography, interests, education, experience, publications | `content.json` |
| Colors, fonts, spacing, mobile layout | `assets/site.css` |
| Research descriptions and page structure | `generate.py` |
| Articles | `posts/*.md` |
| Blog rendering | `blog.py` |
| GitHub Pages publishing | `.github/workflows/pages.yml` |

The `email` and `portrait` fields in `content.json` are intentionally empty.

- To add an email, set `email`. The Contact page will render an email link.
- To add a portrait, upload it to `assets/images/`, set `portrait` to `/assets/images/your-photo.jpg`, and update `portrait_alt`. The photo appears in the desktop and mobile identity.
- For a new theme, start with the CSS variables at the top of `assets/site.css`.

To add an article figure, upload it under `assets/images/` and write:

```markdown
![A description of the figure](/assets/images/my-figure.png)
```

Edit source files, not generated `dist/` pages. `generate.py` copies assets and rebuilds public HTML. Internal links and images are checked before deployment; a missing local target stops publication.

## Work locally on Windows

Install Python 3.12 or newer, then open a terminal in the repository folder:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python generate.py
.venv\Scripts\python validate_site.py
.venv\Scripts\python -m http.server 8000 --directory dist
```

Open http://localhost:8000. Stop the server with Ctrl+C. After editing content, run `generate.py` again and refresh the browser.

To create a draft:

```powershell
.venv\Scripts\python new_post.py "My research note"
```

To run the draft and publishing checks:

```powershell
.venv\Scripts\python -m unittest discover -s tests
```

On macOS or Linux, use `python3 -m venv .venv` and `.venv/bin/python` instead of the Windows commands.

Only two build dependencies are required: Python-Markdown and PyYAML, pinned in `requirements.txt`. The website needs no database, external fonts, tracking, paid CMS, or browser storage.

## Content sources

Education, appointments, and career history are drawn from the user-provided LinkedIn export, `Profile (2).pdf`. The source PDF is intentionally not published with the site; the user plans to add an email and photographs later.

Publication metadata was checked on 14 September 2026 against publisher records:

- [Physics of Fluids](https://doi.org/10.1063/5.0342259)
- [Journal of Mechanical Science and Technology](https://doi.org/10.1007/s12206-026-0548-7)

Research descriptions are short editorial summaries of these papers. Citation counts are not hard-coded. The future Ph.D. end date from the profile is explicitly labeled as expected. High-school education and the incomplete award entry are omitted from the academic presentation.

Platform documentation: [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [selecting the publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site), [creating files](https://docs.github.com/en/repositories/working-with-files/managing-files/creating-new-files), [github.dev](https://docs.github.com/en/codespaces/the-githubdev-web-based-editor), and [Markdown extensions](https://python-markdown.github.io/extensions/).
