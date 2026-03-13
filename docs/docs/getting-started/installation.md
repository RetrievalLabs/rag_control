---
title: Installation
description: How to install and set up rag_control
---

# Installation

## Requirements

- **Python**: 3.10+
- **Package Manager**: pip, poetry or uv


## Install from PyPI

```bash
pip install rag_control==0.1.3
```

## Verify Installation

```python
import rag_control
print(rag_control.__version__)
```

Or check that the core module imports:

```bash
python -c "from rag_control.core.engine import RAGControl; print('Installation successful!')"
```

## Next Steps

1. **Quick Start**: Learn the basics with [Quick Start Guide](/getting-started/quick-start)
2. **Configuration**: Understand how to configure rag_control with [Configuration Guide](/getting-started/configuration)
3. **Core Concepts**: Dive deeper into [Core Concepts](/concepts/overview)

## Troubleshooting

### ModuleNotFoundError: No module named 'rag_control'

Ensure rag_control is installed:
```bash
pip list | grep rag_control
pip install rag_control
```

### Pydantic version conflicts

rag_control requires Pydantic v2. If you have conflicts:
```bash
pip install --upgrade pydantic
```

## Getting Help

- Open an [issue on GitHub](https://github.com/RetrievalLabs/rag_control/issues)
- Contact [RetrievalLabs support](mailto:support@retrievallabs.ai) at support@retrievallabs.ai
