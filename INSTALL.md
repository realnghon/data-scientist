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
| **Gemini CLI** | 2 min | ⚠️ Project memory | ❌ | ❌ |

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

#### Option A — Install from the marketplace (recommended)

In Claude Code, add this repo as a marketplace and install the plugin:

```text
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

That is all that is required to use the skill, agents, and `/ds-*` commands. To run the bundled Python helpers (`ds_skill`) and charts in your own analysis, also install the dependencies once:

```bash
pip install "pandas>=2,<3" "numpy>=1.24,<2" "scipy>=1.10,<2" "scikit-learn>=1.3,<2" "statsmodels>=0.14,<1"
pip install matplotlib seaborn   # for charts
pip install openpyxl pyarrow     # for Excel (.xlsx) / Parquet input — CSV/JSON need no extra
```

#### Option B — Local development (clone + editable install)

```bash
git clone https://github.com/realnghon/data-scientist.git
cd data-scientist

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the helper package + dev/chart dependencies, then point Claude Code at the local plugin
pip install -e ".[dev]"
```

```text
# In Claude Code, from the cloned repo:
/plugin marketplace add ./
/plugin install data-scientist@data-scientist
```

`pip install -e .` makes `import ds_skill` work anywhere with no `sys.path` setup.

#### Verify installation

```text
# In Claude Code:
/help            # should list /ds-analyze, /ds-profile, /ds-plan, /ds-report
/plugin          # data-scientist shows as enabled
```

#### Test with example data

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

**Best for**: Sequential workflow via project memory in Gemini CLI.

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

#### 3. Start Gemini CLI

```bash
# Gemini CLI auto-loads GEMINI.md as project memory when it starts.
# Use the shared 7-stage workflow sequentially in one thread.
```

#### 4. Verify

```text
# Confirm GEMINI.md is loaded as project memory.
# Then try:
analyze my dataset.csv
```

---

## Post-Installation

### 1. Verify the install (deterministic, no AI in the loop)

```bash
cd data-scientist
python plugins/data-scientist/skills/analysis-workflow/scripts/profile_dataset.py examples/manufacturing_yield/dataset.csv
python plugins/data-scientist/skills/analysis-workflow/scripts/run_full_workflow.py examples/manufacturing_yield/dataset.csv --target yield_pct --output .local/baseline
```

### 2. Explore examples

```bash
# Install chart + notebook dependencies
pip install -e ".[viz]"
pip install jupyter

# Open the worked example notebook
jupyter notebook examples/manufacturing_yield/analysis.ipynb
```

See [examples/README.md](examples/README.md) for all three datasets (manufacturing yield, A/B test, time series) and their baked-in ground truth.

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

# Or install with Excel/Parquet + chart extras
pip install -e ".[io,viz]"
```

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

- Explore [examples/](examples/) for real-world workflows
- Read the [README](README.md) for a full feature overview
- Report issues at [GitHub Issues](https://github.com/realnghon/data-scientist/issues)

---

## Getting Help

- **Documentation**: [README.md](README.md)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/realnghon/data-scientist/issues)
- **Discussions**: [GitHub Discussions](https://github.com/realnghon/data-scientist/discussions)
