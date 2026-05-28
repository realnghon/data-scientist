# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it via GitHub Security Advisories:

**[Report a vulnerability][report]**

[report]: https://github.com/realnghon/data-scientist/security/advisories/new

Do not open a public issue for security vulnerabilities. Private vulnerability reporting ensures the issue can be triaged and fixed before public disclosure.

## Scope

### In scope

Security vulnerabilities in the following components are in scope for this policy:

- **`ds_skill/` Python modules** — injection vulnerabilities via DataFrame columns, unsafe deserialization, path traversal, arbitrary code execution
- **OpenCode plugin loader** (`.opencode/plugins/data-scientist.js`) — code injection, privilege escalation, unsafe eval
- **Slash command handlers** — command injection, unsafe file operations

### Out of scope

The following are out of scope for this project's security policy:

- **Host platform execution of markdown prompts** — how Claude Code, Cursor, Codex, or other platforms parse and execute the skill's markdown content is the responsibility of those platforms. Report such issues to the respective platform vendors.
- **Denial of service via large datasets** — the plugin is designed for interactive analysis of reasonably-sized datasets. Resource exhaustion from intentionally malicious inputs is not considered a vulnerability.
- **Social engineering attacks** — vulnerabilities that require tricking a user into running malicious commands outside the plugin's control are out of scope.

## What you can expect

- **Acknowledgment**: We will acknowledge receipt of your report within 7 days.
- **Triage**: We will triage the report and provide an initial assessment (confirmed vulnerability, needs more information, or not a vulnerability) within 30 days.
- **Fix timeline**: For confirmed vulnerabilities, we will work on a fix and coordinate disclosure timing with you. Critical vulnerabilities will be prioritized.
- **Credit**: We will credit you in the security advisory unless you prefer to remain anonymous.

## Supported versions

During the alpha phase (v0.x), only the latest minor release receives security fixes. Once the project reaches v1.0, we will maintain security fixes for the current major version and the previous major version.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Disclosure timeline

We prefer coordinated disclosure:

1. You report the vulnerability privately via GitHub Security Advisories.
2. We confirm the issue and develop a fix.
3. We release a patched version and publish a security advisory.
4. You may publish your findings after the advisory is public.

If you plan to publish details before we have released a fix, please give us at least 90 days notice so we can coordinate a response.

## Security best practices for users

When using this plugin:

- **Review generated code** before executing it, especially code that reads or writes files, makes network requests, or executes shell commands.
- **Sanitize datasets** before analysis if they come from untrusted sources. The plugin assumes input data is not adversarial.
- **Keep dependencies updated** — run `pip install -U pandas numpy scipy scikit-learn statsmodels` periodically to get security patches in underlying libraries.
- **Use virtual environments** to isolate the plugin's dependencies from other projects.

## Contact

For non-security issues, please use [GitHub Issues][issues] or [GitHub Discussions][discussions].

[issues]: https://github.com/realnghon/data-scientist/issues
[discussions]: https://github.com/realnghon/data-scientist/discussions
