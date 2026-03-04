# rag_control Documentation

This is the documentation site for rag_control, built with [Docusaurus 3](https://docusaurus.io/).

## Prerequisites

- Node.js 18+
- npm or yarn

## Installation

```bash
npm install
```

## Local Development

Start the development server:

```bash
npm start
```

The site will open at `http://localhost:3000`. Most changes will be reflected immediately without restarting.

## Build

Build the static site:

```bash
npm run build
```

The output will be in the `build/` directory.

## Deployment

The documentation is automatically deployed on changes to the main branch. To manually deploy:

```bash
npm run deploy
```

## Documentation Structure

```
docs/
├── docs/
│   ├── index.md                    # Home page
│   ├── getting-started/            # Getting started guides
│   ├── concepts/                   # Core concepts
│   ├── architecture/               # Architecture documentation
│   ├── observability/              # Audit, tracing, metrics
│   ├── api/                        # API reference
│   ├── specs/                      # Formal specifications
│   ├── development/                # Development guides
│   └── license.md
├── src/
│   ├── css/
│   │   └── custom.css             # Custom styling
│   └── pages/                      # Additional pages
├── sidebars.js                     # Navigation structure
├── docusaurus.config.js            # Configuration
└── package.json
```

## Adding Documentation

1. Create a markdown file in `docs/docs/`
2. Add metadata (frontmatter) at the top:

```yaml
---
title: Page Title
description: Short description for SEO
---
```

3. Update `sidebars.js` to include the new page
4. Test locally with `npm start`

## Writing Style

- Clear, concise language
- Explain the "why" not just the "what"
- Include code examples
- Link to related documentation
- Use markdown formatting

## Code Examples

Use code blocks with language specification:

````markdown
```python
from rag_control.core.engine import RAGControl

engine = RAGControl(...)
```
````

Supported languages: `python`, `javascript`, `yaml`, `bash`, `json`, `sql`, etc.

## Links

Internal documentation links:

```markdown
[Page Title](/docs/path/to/page)
[Concept](/docs/concepts/policies)
```

External links:

```markdown
[OpenAI](https://openai.com/)
```

## SEO

Each page should have:

- `title`: Page title (in frontmatter)
- `description`: Short description (in frontmatter)
- Proper heading hierarchy (h1, h2, h3)

## Customization

### Colors and Styling

Edit `src/css/custom.css` to customize:

- Primary color
- Code highlighting
- Fonts
- Spacing

### Navigation

Edit `docusaurus.config.js` to customize:

- Site title and tagline
- Navigation bar items
- Footer links
- Social links

### Sidebar

Edit `sidebars.js` to organize documentation structure.

## Troubleshooting

### Build Fails

```bash
# Clear cache
npm run clear

# Rebuild
npm run build
```

### Port Already in Use

```bash
# Use different port
npm start -- --port 3001
```

### Styling Issues

Check `src/css/custom.css` and `docusaurus.config.js` for style overrides.

## Contributing

See [Contributing Guide](/docs/development/contributing.md) for guidelines.

## Deployment URLs

- **Production**: https://rag-control-docs.retrievallabs.ai
- **Staging**: (configured in deployment pipeline)

## Support

For documentation issues or improvements:

1. Open an issue on [GitHub](https://github.com/RetrievalLabs/rag_control/issues)
2. Check existing issues for similar topics
3. Provide clear description and suggestions

## License

Documentation is licensed under the same RBRL license as the project.

See [LICENSE](../LICENSE) for full terms.
