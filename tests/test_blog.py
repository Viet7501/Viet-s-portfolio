from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import blog
import generate
from validate_site import validate


def post_text(slug='test-note', draft='false'):
    return f'''---
title: "A research note"
slug: "{slug}"
date: "2026-09-14"
summary: "A test of the publishing path."
tags: ["Methods"]
draft: {draft}
---

## Method

A paragraph with **emphasis** and a [profile link](/).

```python
print("test")
```

| Quantity | Value |
| --- | --- |
| Sample | 1 |
'''


class BlogTests(unittest.TestCase):
    def test_draft_and_template_never_enter_public_posts(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'draft.md').write_text(post_text(draft='true'))
            (directory / '_template.md').write_text(post_text())
            (directory / 'no-status.md').write_text(post_text().replace('draft: false\n', ''))
            self.assertEqual(blog.load_posts(directory), [])

    def test_markdown_tables_code_and_post_route(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'published.md').write_text(post_text())
            post = blog.load_posts(directory)[0]
            self.assertEqual(post.route, '/blog/test-note/')
            self.assertIn('<table>', post.html)
            self.assertIn('<strong>emphasis</strong>', post.html)
            self.assertIn('language-python', post.html)

    def test_unsafe_and_duplicate_slugs_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            first = directory / 'one.md'
            first.write_text(post_text('../escape'))
            with self.assertRaisesRegex(ValueError, 'slug must'):
                blog.load_posts(directory)
            first.write_text(post_text())
            (directory / 'two.md').write_text(post_text())
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                blog.load_posts(directory)

    def test_invalid_draft_flag_fails_instead_of_publishing(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'one.md').write_text(post_text(draft='"false"'))
            with self.assertRaisesRegex(ValueError, 'draft must'):
                blog.load_posts(directory)

    def test_root_and_project_routes_and_withdrawal(self):
        original_root = generate.ROOT
        for base_path in ('', '/academic-profile'):
            with self.subTest(base_path=base_path), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'posts').mkdir()
                shutil.copytree(original_root / 'assets', root / 'assets')
                source = root / 'posts' / 'published.md'
                source.write_text(post_text())
                output = root / 'dist'
                with patch.object(generate, 'ROOT', root), patch.object(generate, 'OUT', output), patch.object(generate, 'BASE_PATH', base_path), redirect_stdout(StringIO()):
                    generate.main()
                    self.assertEqual(validate(output, base_path), 9)
                    article = output / 'blog/test-note/index.html'
                    self.assertIn('BlogPosting', article.read_text())
                    self.assertIn('aria-current="page"', article.read_text())
                    self.assertFalse(any(output.rglob('*.md')))
                    source.write_text(post_text(draft='true'))
                    generate.main()
                    self.assertFalse(article.exists(), 'Withdrawn post remained reachable.')
                    self.assertEqual(validate(output, base_path), 8)


if __name__ == '__main__':
    unittest.main()
