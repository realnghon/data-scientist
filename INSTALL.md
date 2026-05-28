# Installing the Data Scientist Plugin

The plugin source lives at `plugins/data-scientist/` in this repo. Each supported tool reads it from a different conventional location, so install means either copying/symlinking that directory (or a single file inside it) into your tool's plugin path, or pointing your tool's config at the in-repo path.

## Supported platforms

| Platform        | Entrypoint inside the plugin                                   | Install style                                   |
|-----------------|----------------------------------------------------------------|-------------------------------------------------|
| Claude Code     | `.claude-plugin/plugin.json`                                   | Symlink or copy plugin dir into `~/.claude/plugins/` |
| Codex           | `.codex-plugin/plugin.json`                                    | Register plugin dir with Codex CLI / config     |
| Cursor          | `.cursor/rules/data-scientist.mdc`                             | Copy or symlink `.mdc` into project `.cursor/rules/` |
| OpenCode        | `.opencode/plugins/data-scientist.js`                          | Symlink or reference `.js` from OpenCode config |
| Cline           | `.clinerules/data-scientist.md`                                | Copy or symlink `.md` into project `.clinerules/` |
| Windsurf        | `.windsurf/rules/data-scientist.md`                            | Copy or symlink `.md` into project `.windsurf/rules/` |
| GitHub Copilot  | `.github/copilot-instructions.md`                              | Copy file into project `.github/`               |
| Gemini CLI      | `GEMINI.md`                                                    | Copy or symlink into project root as `GEMINI.md` |

Pick the section that matches your tool.

- [Claude Code](#claude-code)
- [Codex](#codex)
- [Cursor](#cursor)
- [OpenCode](#opencode)
- [Cline](#cline)
- [Windsurf](#windsurf)
- [GitHub Copilot](#github-copilot)
- [Gemini CLI](#gemini-cli)
- [Verifying install](#verifying-install)

---

## Claude Code

Claude Code discovers plugins under `~/.claude/plugins/<plugin-name>/`. The manifest is `plugins/data-scientist/.claude-plugin/plugin.json`.

### Option A — symlink (recommended for development)

Keeps the plugin live against this checkout, so edits show up immediately.

**macOS / Linux:**

```bash
mkdir -p ~/.claude/plugins
ln -s "$(pwd)/plugins/data-scientist" ~/.claude/plugins/data-scientist
```

**Windows (PowerShell, run as admin or with Developer Mode on):**

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\plugins" | Out-Null
New-Item -ItemType SymbolicLink `
  -Path "$HOME\.claude\plugins\data-scientist" `
  -Target "$PWD\plugins\data-scientist"
```

### Option B — copy

Use this if symlinks are inconvenient. You'll need to re-copy after upstream changes.

```bash
cp -R plugins/data-scientist ~/.claude/plugins/data-scientist
```

### Option C — marketplace (future)

Once this repo is registered with a Claude Code plugin marketplace, you'll be able to install via `/plugin install data-scientist`. The `marketplace.json` at the repo root is a scaffold toward that.

Restart Claude Code (or run `/plugin reload`) after installing.

---

## Codex

Codex reads its plugin manifest from `plugins/data-scientist/.codex-plugin/plugin.json`.

Install by registering the plugin directory with the Codex CLI. The exact command depends on your Codex version; the general pattern is to point Codex at the directory containing `.codex-plugin/plugin.json`:

```bash
# If your Codex CLI exposes a plugin install command, prefer that:
codex plugin install ./plugins/data-scientist
```

If your Codex distribution uses a config file (commonly `~/.codex/config.json` or similar), add the plugin path under the plugins list:

```json
{
  "plugins": [
    "/absolute/path/to/this/repo/plugins/data-scientist"
  ]
}
```

When in doubt, follow the standard Codex plugin install procedure pointing at `plugins/data-scientist/`.

---

## Cursor

Cursor uses project-scoped rule files under `.cursor/rules/`. The plugin ships a single `.mdc` rule that auto-activates when matching data file globs (CSV, Parquet, Excel, etc.).

### In a project where you want the rule active

```bash
mkdir -p .cursor/rules
cp /path/to/this/repo/plugins/data-scientist/.cursor/rules/data-scientist.mdc .cursor/rules/
```

Or, if you want the rule to track upstream:

```bash
mkdir -p .cursor/rules
ln -s /absolute/path/to/this/repo/plugins/data-scientist/.cursor/rules/data-scientist.mdc .cursor/rules/data-scientist.mdc
```

That's it — Cursor picks the rule up automatically the next time it opens the project. The rule self-activates when you open or paste a data file matching its globs; you can also invoke it explicitly by asking Cursor for "the data-scientist workflow".

### Global rules (optional)

If you want the rule available across every project, drop the same `.mdc` into your Cursor user-level rules directory (the location depends on your Cursor install — see Cursor's docs for "Global rules").

---

## OpenCode

OpenCode loads plugins from its config plugins list, typically at `~/.config/opencode/plugins/` or referenced from `~/.config/opencode/config.json`. The plugin entry is `plugins/data-scientist/.opencode/plugins/data-scientist.js`.

### Option A — symlink into the conventional plugins dir

```bash
mkdir -p ~/.config/opencode/plugins
ln -s "$(pwd)/plugins/data-scientist/.opencode/plugins/data-scientist.js" \
  ~/.config/opencode/plugins/data-scientist.js
```

### Option B — reference from config

Add the absolute path to your OpenCode config's plugins array:

```json
{
  "plugins": [
    "/absolute/path/to/this/repo/plugins/data-scientist/.opencode/plugins/data-scientist.js"
  ]
}
```

Restart OpenCode after installing.

---

## Cline

Cline reads project rules from a `.clinerules/` directory (one markdown file per rule) at the project root. The plugin ships `plugins/data-scientist/.clinerules/data-scientist.md` as the entrypoint.

### In a project where you want the rule active

**macOS / Linux:**

```bash
mkdir -p .clinerules
cp /path/to/this/repo/plugins/data-scientist/.clinerules/data-scientist.md .clinerules/
```

Or symlink to track upstream:

```bash
mkdir -p .clinerules
ln -s /absolute/path/to/this/repo/plugins/data-scientist/.clinerules/data-scientist.md .clinerules/data-scientist.md
```

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path ".clinerules" | Out-Null
Copy-Item "C:\path\to\this\repo\plugins\data-scientist\.clinerules\data-scientist.md" ".clinerules\"
```

Cline picks the rule up next time the project is opened. Other rules can sit alongside it in the same directory.

---

## Windsurf

Windsurf (Cascade) reads project rules from `.windsurf/rules/*.md` at the project root. The plugin ships `plugins/data-scientist/.windsurf/rules/data-scientist.md`, which uses a glob trigger so it auto-activates on common data files.

### In a project where you want the rule active

**macOS / Linux:**

```bash
mkdir -p .windsurf/rules
cp /path/to/this/repo/plugins/data-scientist/.windsurf/rules/data-scientist.md .windsurf/rules/
```

Or symlink:

```bash
mkdir -p .windsurf/rules
ln -s /absolute/path/to/this/repo/plugins/data-scientist/.windsurf/rules/data-scientist.md .windsurf/rules/data-scientist.md
```

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path ".windsurf\rules" | Out-Null
Copy-Item "C:\path\to\this\repo\plugins\data-scientist\.windsurf\rules\data-scientist.md" ".windsurf\rules\"
```

The rule self-activates when a matching data file is opened; you can also invoke it explicitly by asking Cascade for "the data-scientist workflow".

---

## GitHub Copilot

GitHub Copilot Chat and Copilot Workspace auto-discover `.github/copilot-instructions.md` at the repository root. The plugin ships its own copy at `plugins/data-scientist/.github/copilot-instructions.md` so it travels with the plugin; install means placing it at `.github/copilot-instructions.md` in your repo.

### In a project where you want Copilot to follow the workflow

**macOS / Linux:**

```bash
mkdir -p .github
cp /path/to/this/repo/plugins/data-scientist/.github/copilot-instructions.md .github/
```

If your repo already has a `.github/copilot-instructions.md`, append the plugin's content rather than overwriting.

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path ".github" | Out-Null
Copy-Item "C:\path\to\this\repo\plugins\data-scientist\.github\copilot-instructions.md" ".github\"
```

No restart required — GitHub Copilot picks up the file on the next chat turn.

---

## Gemini CLI

Gemini CLI auto-loads `GEMINI.md` from the project root as session memory at startup. The plugin ships `plugins/data-scientist/GEMINI.md` so it travels with the plugin; install means placing it at the repo root as `GEMINI.md`.

### In a project where you want Gemini to follow the workflow

**macOS / Linux:**

```bash
cp /path/to/this/repo/plugins/data-scientist/GEMINI.md ./GEMINI.md
```

Or symlink so it tracks upstream:

```bash
ln -s /absolute/path/to/this/repo/plugins/data-scientist/GEMINI.md ./GEMINI.md
```

**Windows (PowerShell):**

```powershell
Copy-Item "C:\path\to\this\repo\plugins\data-scientist\GEMINI.md" ".\GEMINI.md"
```

If your repo already has a `GEMINI.md`, append the plugin's content rather than overwriting. Start a fresh Gemini CLI session after installing so the memory file is loaded.

---

## Verifying install

- **Claude Code** — open Claude Code and run `/plugin` to list installed plugins; `data-scientist` should appear. Typing `/ds-` should auto-suggest `/ds-analyze`, `/ds-plan`, `/ds-profile`, `/ds-report`.
- **Codex** — list registered plugins with your Codex CLI (e.g. `codex plugin list`); the `data-scientist` skill and its commands should be available. Asking the assistant "what skills are available?" should mention `data-scientist`.
- **Cursor** — open a CSV/Parquet/Excel file in the project; Cursor's Composer should show that the `data-scientist` rule is active. Asking "Run the data-scientist workflow on this file" should follow the staged plan.
- **OpenCode** — start OpenCode and check the plugins list in the status output or via the in-app command; `data-scientist` should appear. Asking the assistant to run the data-scientist workflow should trigger the same skill.
- **Cline** — open the project in Cline and confirm `.clinerules/data-scientist.md` is listed among active rules. Asking Cline to analyse a CSV should make it reference the staged workflow and the report-standard three-tier framework.
- **Windsurf** — open a CSV/Parquet/Excel file in the project; Cascade should announce that the `data-scientist` rule is active. Asking for an analysis should follow the staged plan.
- **GitHub Copilot** — open a chat in the repo and ask "what workflow should I use for this CSV?". Copilot should reference the staged data-scientist workflow and the three-tier evidence framework defined in the instructions file.
- **Gemini CLI** — start a new session at the repo root; the startup banner should list `GEMINI.md` as loaded memory. Asking Gemini to analyse a dataset should walk the 7 stages sequentially.

If something is missing after install, double-check the path in your tool's plugin/rules directory and that the tool was restarted (or its plugin cache reloaded) after the install step.
