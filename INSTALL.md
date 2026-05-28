# Installation Guide

This guide covers installation for all 8 supported platforms. Pick your tool and follow the 2-minute setup.

---

## Quick Reference

| Platform | Install Time | Skill Support | Subagents | Slash Commands |
|----------|--------------|---------------|-----------|----------------|
| **Claude Code** | 2 min | ✅ Native | ✅ Parallel | ✅ |
| **Codex** | 2 min | ✅ Native | ⚠️ Sequential | ✅ |
| **OpenCode** | 3 min | ✅ Native | ⚠️ Sequential | ✅ |
| **Cursor** | 1 min | ⚠️ Rules | ❌ | ❌ |
| **Cline** | 1 min | ⚠️ Rules | ❌ | ❌ |
| **Windsurf** | 1 min | ⚠️ Rules | ❌ | ❌ |
| **GitHub Copilot** | 1 min | ⚠️ Rules | ❌ | ❌ |
| **Gemini CLI** | 2 min | ✅ Native | ✅ Parallel | ✅ |

---

## Prerequisites

All platforms require:
- **Python 3.10+** installed and in PATH
- **Git** for cloning the repository

Optional but recommended:
- **Virtual environment** (venv, conda, or virtualenv)
- **Jupyter** for running example notebooks

---

## Platform-Specific Installation

### Claude Code

**Best for**: Full feature set with parallel subagent dispatch and slash commands.

#### 1. Clone the repository

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
```

#### 2. Install Python dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install as editable package (optional, for development)
pip install -e .
```

#### 3. Link the plugin

```bash
# Linux/macOS
ln -s "$PWD/plugins/data-scientist" "$HOME/.claude/plugins/data-scientist"

# Windows (PowerShell as Administrator)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\plugins\data-scientist" -Target "$PWD\plugins\data-scientist"

# Windows (Command Prompt as Administrator)
mklink /D "%USERPROFILE%\.claude\plugins\data-scientist" "%CD%\plugins\data-scientist"
```

#### 4. Verify installation

```bash
# Start Claude Code and run:
/help

# You should see:
# - /ds-analyze
# - /ds-profile
# - /ds-plan
# - /ds-report
```

#### 5. Test with example data

```text
/ds-profile examples/manufacturing_yield/dataset.csv
```

---

### Codex

**Best for**: Sequential subagent workflows with slash commands.

#### 1. Clone and install dependencies

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
pip install -r requirements.txt
```

#### 2. Link the plugin

```bash
# Linux/macOS
ln -s "$PWD/plugins/data-scientist" "$HOME/.codex/plugins/data-scientist"

# Windows
mklink /D "%USERPROFILE%\.codex\plugins\data-scientist" "%CD%\plugins\data-scientist"
```

#### 3. Verify

```bash
# In Codex:
/skills

# Should list: data-scientist
```

---

### OpenCode

**Best for**: Lightweight integration with sequential workflows.

#### 1. Clone and install

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
pip install -r requirements.txt
```

#### 2. Copy plugin files

```bash
# Linux/macOS
cp -r plugins/data-scientist ~/.opencode/plugins/

# Windows
xcopy /E /I plugins\data-scientist %USERPROFILE%\.opencode\plugins\data-scientist
```

#### 3. Verify

```text
# In OpenCode, type:
Use the data-scientist skill on my dataset
```

---

### Cursor

**Best for**: Auto-activating rules on data files.

#### 1. Clone repository

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
pip install -r requirements.txt
```

#### 2. Copy rule file to your project

```bash
# From your project directory:
mkdir -p .cursor/rules
cp /path/to/data-scientist/plugins/data-scientist/.cursor/rules/data-scientist.mdc .cursor/rules/
```

#### 3. Verify

Open any `.csv`, `.xlsx`, or `.parquet` file in Cursor. The data-scientist rules should auto-activate.

**Manual activation**: Use Cursor's "Add Rule" command and select `data-scientist.mdc`.

---

### Cline

**Best for**: Manual rule loading in VS Code.

#### 1. Clone and install

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
pip install -r requirements.txt
```

#### 2. Copy rule file

```bash
# From your project directory:
mkdir -p .clinerules
cp /path/to/data-scientist/plugins/data-scientist/.clinerules/data-scientist.md .clinerules/
```

#### 3. Load the rule

In Cline's VS Code extension:
1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run: `Cline: Load Rules`
3. Select `data-scientist.md`

---

### Windsurf

**Best for**: Auto-activating rules in Windsurf IDE.

#### 1. Clone and install

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
pip install -r requirements.txt
```

#### 2. Copy rule file

```bash
# From your project directory:
mkdir -p .windsurf/rules
cp /path/to/data-scientist/plugins/data-scientist/.windsurf/rules/data-scientist.md .windsurf/rules/
```

#### 3. Verify

Open a data file (`.csv`, `.xlsx`, etc.). The rule should auto-activate.

---

### GitHub Copilot

**Best for**: Repository-wide context in GitHub Copilot Chat.

#### 1. Clone and install

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
pip install -r requirements.txt
```

#### 2. Copy instructions file

```bash
# From your project directory:
mkdir -p .github
cp /path/to/data-scientist/plugins/data-scientist/.github/copilot-instructions.md .github/
```

#### 3. Verify

In GitHub Copilot Chat, ask:
```text
@workspace How do I analyze my manufacturing yield data?
```

Copilot should reference the data-scientist instructions.

---

### Gemini CLI

**Best for**: Full feature set with parallel subagents in Gemini.

#### 1. Clone and install

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist
pip install -r requirements.txt
```

#### 2. Copy GEMINI.md to your project

```bash
# From your project directory:
cp /path/to/data-scientist/plugins/data-scientist/GEMINI.md .
```

#### 3. Activate skill

```bash
# In Gemini CLI:
activate_skill data-scientist
```

#### 4. Verify

```text
# Should see skill loaded message
# Then try:
analyze my dataset.csv
```

---

## Post-Installation

### 1. Run the test suite

```bash
cd data-scientist
python -m pytest tests/ -v
```

Expected: **176 tests passed** (with some warnings, which are non-critical).

### 2. Try the profile script

```bash
python plugins/data-scientist/skills/analysis-workflow/scripts/profile_dataset.py examples/manufacturing_yield/dataset.csv
```

### 3. Explore examples

```bash
# Start Jupyter
jupyter notebook examples/

# Open:
# - manufacturing_yield_analysis.ipynb
# - ab_test_validation.ipynb
# - time_series_anomaly_detection.ipynb
```

---

## Troubleshooting

### Issue: "Module 'ds_skill' not found"

**Solution**:
```bash
# Ensure you're in the project root
cd data-scientist

# Install as editable package
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="$PWD/plugins/data-scientist/skills/analysis-workflow/scripts:$PYTHONPATH"
```

### Issue: "Command /ds-analyze not found" (Claude Code/Codex)

**Solution**:
1. Check symlink exists:
   ```bash
   ls -la ~/.claude/plugins/data-scientist
   ```
2. Restart Claude Code
3. Verify plugin.json is valid JSON:
   ```bash
   cat ~/.claude/plugins/data-scientist/.claude-plugin/plugin.json | python -m json.tool
   ```

### Issue: "Permission denied" when creating symlink (Windows)

**Solution**:
- Run PowerShell or Command Prompt **as Administrator**
- Or use Developer Mode in Windows Settings (allows symlinks without admin)

### Issue: Rules not auto-activating (Cursor/Windsurf)

**Solution**:
1. Check file glob patterns in the rule frontmatter
2. Manually load the rule via IDE command
3. Ensure `.cursor/rules/` or `.windsurf/rules/` directory exists

### Issue: Import errors for scipy/sklearn

**Solution**:
```bash
# Reinstall with exact versions
pip install -r requirements.txt --force-reinstall

# Or install dev dependencies
pip install -r requirements-dev.txt
```

### Issue: Tests fail on Windows

**Solution**:
- Some tests use Unix-style paths. This is a known issue.
- Core functionality works; test failures are cosmetic.
- Run: `pytest tests/ -k "not path"` to skip path-related tests.

---

## Updating

### Pull latest changes

```bash
cd data-scientist
git pull origin main
pip install -r requirements.txt --upgrade
```

### Reinstall plugin (if needed)

```bash
# Claude Code/Codex: symlink auto-updates
# Cursor/Cline/Windsurf: re-copy rule files
# GitHub Copilot: re-copy .github/copilot-instructions.md
```

---

## Uninstalling

### Claude Code

```bash
rm ~/.claude/plugins/data-scientist
```

### Codex

```bash
rm ~/.codex/plugins/data-scientist
```

### OpenCode

```bash
rm -rf ~/.opencode/plugins/data-scientist
```

### Cursor/Cline/Windsurf/GitHub Copilot

```bash
# Remove rule files from your project
rm .cursor/rules/data-scientist.mdc
rm .clinerules/data-scientist.md
rm .windsurf/rules/data-scientist.md
rm .github/copilot-instructions.md
```

### Gemini CLI

```bash
# Remove GEMINI.md from your project
rm GEMINI.md
```

---

## Next Steps

- Read [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Explore [examples/](examples/) for real-world workflows
- Check [CHANGELOG.md](CHANGELOG.md) for latest features
- Report issues at [GitHub Issues](https://github.com/realnghon/data-scientist/issues)

---

## Getting Help

- **Documentation**: [README.md](README.md)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/realnghon/data-scientist/issues)
- **Discussions**: [GitHub Discussions](https://github.com/realnghon/data-scientist/discussions)
