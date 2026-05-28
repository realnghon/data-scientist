# Contributing to Data Scientist Plugin

Thank you for your interest in contributing! This guide will help you get started.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Making Changes](#making-changes)
6. [Testing](#testing)
7. [Code Style](#code-style)
8. [Submitting Changes](#submitting-changes)
9. [Review Process](#review-process)
10. [Areas for Contribution](#areas-for-contribution)

---

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

**Key principles**:
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Git**
- **pytest** for testing
- **One or more supported platforms** (Claude Code, Codex, Cursor, etc.)

### Quick Setup

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/data-scientist.git
cd data-scientist

# 3. Add upstream remote
git remote add upstream https://github.com/realnghon/data-scientist.git

# 4. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Install as editable package
pip install -e .

# 7. Run tests to verify setup
pytest tests/ -v
```

---

## Development Setup

### Recommended Tools

- **IDE**: VS Code, PyCharm, or any editor with Python support
- **Linter**: `ruff` or `flake8`
- **Formatter**: `black`
- **Type checker**: `pyright` or `mypy`

### VS Code Setup

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### Environment Variables

```bash
# Optional: for development
export DS_SKILL_DEBUG=1
export DS_SKILL_CACHE_DIR=.local/cache
```

---

## Project Structure

```
data_scientist/
├── plugins/data-scientist/
│   ├── .claude-plugin/        # Claude Code manifest
│   ├── .codex-plugin/         # Codex manifest
│   ├── .cursor/rules/         # Cursor rules
│   ├── .clinerules/           # Cline rules
│   ├── .windsurf/rules/       # Windsurf rules
│   ├── .github/               # GitHub Copilot instructions
│   ├── GEMINI.md              # Gemini CLI memory
│   ├── agents/                # 7 staged subagents
│   │   ├── ds-intake-agent.md
│   │   ├── ds-readiness-agent.md
│   │   ├── ds-shaping-agent.md
│   │   ├── ds-method-planner-agent.md
│   │   ├── ds-execution-agent.md
│   │   ├── ds-critic-agent.md
│   │   └── ds-report-agent.md
│   ├── commands/              # 4 slash commands
│   │   ├── ds-analyze.md
│   │   ├── ds-profile.md
│   │   ├── ds-plan.md
│   │   └── ds-report.md
│   └── skills/analysis-workflow/
│       ├── SKILL.md           # Main skill definition
│       ├── references/        # Method registry, playbooks, etc.
│       ├── scripts/           # Executable helpers
│       │   ├── profile_dataset.py
│       │   └── ds_skill/      # Python package
│       │       ├── __init__.py
│       │       ├── readiness.py
│       │       ├── spc.py
│       │       ├── correlation.py
│       │       ├── anomaly.py
│       │       ├── time_series.py
│       │       ├── bootstrap.py
│       │       ├── shaping.py
│       │       ├── ab_validator.py
│       │       ├── regression.py
│       │       ├── classification.py
│       │       ├── survival.py
│       │       ├── report_generator.py
│       │       ├── analysis_methods.py
│       │       ├── plotting.py
│       │       ├── caching.py
│       │       └── validation.py
│       └── assets/            # Templates
├── tests/                     # Test suite (176 tests)
├── examples/                  # Example datasets and notebooks
├── .local/                    # Git-ignored scratch space
├── requirements.txt           # Core dependencies
├── requirements-dev.txt       # Dev dependencies
├── pyproject.toml             # Package configuration
├── README.md
├── INSTALL.md
├── CHANGELOG.md
├── LICENSE
└── CONTRIBUTING.md (this file)
```

---

## Making Changes

### Branching Strategy

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/issue-123-description
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Weibull analysis to survival module
fix: correct FDR calculation in correlation ranking
docs: update method registry with new templates
test: add edge cases for readiness scoring
refactor: simplify bootstrap CI calculation
perf: optimize large dataset profiling
```

**Format**:
```
<type>: <short summary>

<optional body with details>

<optional footer with issue references>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding or updating tests
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `chore`: Maintenance tasks

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_readiness.py -v

# Run tests matching a pattern
pytest tests/ -k "correlation" -v

# Run with coverage
pytest tests/ --cov=ds_skill --cov-report=html

# Run fast tests only (skip slow integration tests)
pytest tests/ -m "not slow"
```

### Writing Tests

**Location**: `tests/test_<module_name>.py`

**Template**:
```python
import pytest
import pandas as pd
import numpy as np
from ds_skill.<module> import <function>

def test_<function>_<scenario>():
    """Test that <function> <expected behavior> when <condition>."""
    # Arrange
    data = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10]
    })
    
    # Act
    result = <function>(data, 'x', 'y')
    
    # Assert
    assert result['correlation'] > 0.9
    assert 'p_value' in result
```

**Guidelines**:
- One test per behavior
- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- Test edge cases (empty data, NaN, single row, etc.)
- Use fixtures for common test data (see `tests/conftest.py`)

### Test Coverage Goals

- **New features**: 100% coverage required
- **Bug fixes**: Add regression test
- **Refactoring**: Maintain existing coverage
- **Overall target**: >90%

---

## Code Style

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

```python
# Line length: 88 characters (Black default)
# Indentation: 4 spaces
# Quotes: Double quotes for strings, single for dict keys

# Good
def calculate_correlation(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    method: str = "pearson"
) -> dict:
    """Calculate correlation between two columns.
    
    Args:
        data: Input DataFrame
        x_col: Name of X column
        y_col: Name of Y column
        method: Correlation method (pearson, spearman, kendall)
    
    Returns:
        Dictionary with correlation, p_value, and method
    
    Raises:
        ValueError: If columns not found or method invalid
    """
    # Implementation
    pass
```

### Type Hints

Use type hints for all public functions:

```python
from typing import Optional, Union, List, Dict, Any
import pandas as pd
import numpy as np

def process_data(
    data: pd.DataFrame,
    columns: Optional[List[str]] = None,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """Process data with optional column selection."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: int, param2: str) -> bool:
    """Short one-line summary.
    
    Longer description if needed. Explain the purpose,
    not the implementation details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is negative
        TypeError: When param2 is not a string
    
    Example:
        >>> example_function(42, "test")
        True
    """
    pass
```

### Imports

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler

# Local
from ds_skill.validation import validate_dataframe
from ds_skill.caching import cached_computation
```

---

## Submitting Changes

### Before Submitting

**Checklist**:
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Code formatted: `black plugins/data-scientist/skills/analysis-workflow/scripts/ds_skill/`
- [ ] Type checks pass: `pyright` (if installed)
- [ ] Documentation updated (if adding features)
- [ ] CHANGELOG.md updated under "Unreleased"
- [ ] No merge conflicts with `main`

### Pull Request Process

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Reference related issues: "Fixes #123" or "Relates to #456"
   - Describe what changed and why
   - Include screenshots for UI changes
   - List any breaking changes

4. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix (non-breaking change which fixes an issue)
   - [ ] New feature (non-breaking change which adds functionality)
   - [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
   - [ ] Documentation update
   
   ## Testing
   - [ ] All tests pass
   - [ ] Added tests for new functionality
   - [ ] Tested on [platform names]
   
   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   
   ## Related Issues
   Fixes #123
   ```

---

## Review Process

### What to Expect

1. **Automated checks** run (tests, linting)
2. **Maintainer review** within 3-5 business days
3. **Feedback** may request changes
4. **Approval** and merge when ready

### Review Criteria

- **Correctness**: Does it work as intended?
- **Tests**: Are edge cases covered?
- **Style**: Follows project conventions?
- **Documentation**: Clear and complete?
- **Performance**: No unnecessary slowdowns?
- **Compatibility**: Works across platforms?

### Addressing Feedback

```bash
# Make requested changes
git add .
git commit -m "address review feedback: <description>"
git push origin feature/your-feature-name
```

---

## Areas for Contribution

### High-Priority

1. **Example datasets and notebooks**
   - Manufacturing yield analysis
   - A/B test validation
   - Time series anomaly detection
   - Add to `examples/` directory

2. **Platform testing**
   - Test on Codex, Cursor, OpenCode, etc.
   - Document platform-specific quirks
   - Add integration tests

3. **Performance optimization**
   - Large dataset handling (>1M rows)
   - Caching strategies
   - Memory profiling

4. **Documentation**
   - FAQ.md
   - Troubleshooting guide
   - Video tutorials
   - Blog posts

### Medium-Priority

5. **New analysis methods**
   - Add to `method-registry.md`
   - Implement in `ds_skill/`
   - Add tests
   - Update SKILL.md

6. **Golden templates**
   - Logistics, finance, web analytics domains
   - Add to `golden-templates.md`
   - Include example workflows

7. **Visualization enhancements**
   - Interactive charts (Plotly, Bokeh)
   - Dashboard templates
   - Export formats (PNG, SVG, PDF)

8. **Error handling**
   - Custom exception hierarchy
   - Better error messages
   - Recovery strategies

### Low-Priority

9. **Big data support**
   - Dask integration
   - Polars support
   - Streaming analysis

10. **MCP server wrapper**
    - Expose helpers as tools
    - API design
    - Documentation

11. **Internationalization**
    - Multi-language support
    - Localized error messages

---

## Contribution Ideas by Skill Level

### Beginner-Friendly

- Fix typos in documentation
- Add docstrings to undocumented functions
- Write tests for existing code
- Add examples to README
- Improve error messages

### Intermediate

- Add new chart types to `plotting.py`
- Implement new statistical methods
- Optimize slow functions
- Add platform integration tests
- Write tutorial notebooks

### Advanced

- Design new golden templates
- Implement parallel processing
- Add streaming data support
- Create MCP server wrapper
- Performance profiling and optimization

---

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/realnghon/data-scientist/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/realnghon/data-scientist/issues)
- **Chat**: Join our community (link TBD)

---

## Recognition

Contributors are recognized in:
- `README.md` Contributors section
- Release notes in `CHANGELOG.md`
- GitHub's contributor graph

Significant contributions may earn you:
- Maintainer status
- Decision-making input on roadmap
- Co-authorship on papers/blog posts

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Data Scientist Plugin! 🎉
