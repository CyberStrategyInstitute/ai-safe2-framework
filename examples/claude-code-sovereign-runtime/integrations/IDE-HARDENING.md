# Claude Code in VS Code and Cursor -- AI SAFE2 Hardening Guide

Claude Code runs inside VS Code and Cursor as an extension. The security
controls from this framework apply in both environments, but the deployment
path differs slightly from standalone CLI use.

---

## VS Code

### Where settings are read

When Claude Code runs as a VS Code extension, it reads:

1. Global user settings: `~/.claude/settings.json`
2. Project-level settings: `.claude/settings.json` in the workspace root
3. Enterprise managed settings (if deployed)

The hooks path uses the same `~/.claude/hooks/` directory.

### Setup (same as CLI)

```bash
# Run the quickstart -- it installs hooks and settings globally
# These apply to both the CLI and VS Code extension
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use.sh ~/.claude/hooks/
cp hooks/post-tool-use.sh ~/.claude/hooks/
cp hooks/stop.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
cp .claude/settings.json ~/.claude/settings.json
```

### VS Code workspace settings

Add to your workspace `.vscode/settings.json`:

```json
{
  "terminal.integrated.env.linux": {
    "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
    "CLAUDE_CODE_LOG_DIR": "${env:HOME}/.claude/logs"
  },
  "terminal.integrated.env.osx": {
    "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
    "CLAUDE_CODE_LOG_DIR": "${env:HOME}/.claude/logs"
  },
  "terminal.integrated.env.windows": {
    "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
    "CLAUDE_CODE_LOG_DIR": "${env:USERPROFILE}\\.claude\\logs"
  }
}
```

### CVE-2025-52882 note for VS Code

This CVE (WebSocket accepting connections from arbitrary origins) specifically
affected the IDE integration. If you are on a version below 1.0.24, upgrade
immediately. The VS Code extension shares the same WebSocket auth logic
exposed in the leak.

---

## Cursor

Cursor embeds a forked version of VS Code and runs Claude Code for its AI
features. The same hooks apply.

### Setup for Cursor

```bash
# Cursor uses the same ~/.claude/ directory
# The quickstart setup covers Cursor automatically
bash QUICKSTART.md  # or run the steps manually
```

### Cursor-specific notes

Cursor's "Agent" mode is essentially Claude Code running with elevated
permissions. Apply the same managed settings to restrict what it can do:

```json
{
  "bypassPermissions": false,
  "permissions": {
    "deny": [
      "Bash(curl *|*sh)",
      "Bash(wget *|*sh)",
      "Bash(rm -rf /*)",
      "Bash(*base64 -d*|*sh*)"
    ]
  }
}
```

Cursor reads `.cursor/settings.json` in the project root in addition to
`~/.claude/settings.json`. Add a hardened copy there too:

```bash
mkdir -p .cursor
cp .claude/settings.json .cursor/settings.json
```

---

## JetBrains IDEs (IntelliJ, WebStorm, etc.)

Claude Code in JetBrains IDEs operates via a plugin that shells out to the
CLI. The CLI hooks apply here automatically if you have completed the quickstart
setup. No additional configuration is needed beyond the standard setup.

---

## Neovim / Emacs plugins

Claude Code plugins for Neovim and Emacs invoke the CLI directly. The same
hooks apply. Verify the shell profile containing `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`
is sourced before your editor starts.

---

## VS Code Devcontainers (Remote Development)

When using VS Code with devcontainers, Claude Code runs inside the container.
The hooks need to be installed inside the container, not on the host.

Use the provided `ci-cd/devcontainer.json` and `ci-cd/setup-claude-safe.sh`
to automate this during container creation.

Key point: the `.claude-safe/` directory in your project root is mounted into
the container and the setup script installs the hooks automatically on first
run.

---

## Remote SSH development

When developing over SSH, Claude Code may run on the remote host. You need the
hooks on the remote host, not just your local machine.

```bash
# On the remote host
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework /tmp/safe2
cd /tmp/safe2/examples/claude-code-sovereign-runtime
bash QUICKSTART.md
```

Or use Ansible/Terraform/Chef to deploy at scale -- see the managed settings
deployment scripts in `scripts/deploy-enterprise.sh`.

---

*Cyber Strategy Institute -- AI SAFE2 Framework*
