"""Classify every 'v3.0'-as-framework-version mention and every old-meaning MCP id."""
import re, subprocess, sys, json, collections
LABEL = re.compile(r"(AI SAFE2?|AI SAFE²|SAFE2|SAFE²|[Ff]ramework)[^\n]{0,12}v3\.0\b|\bv3\.0 (controls?|framework|compliance|skill|alignment|aligned|CP\.5|scanner|scan)\b", re.I)
OLD_MCP = re.compile(r"MCP-?(6|9|12|13)\b[^\n]{0,40}(context.tool isolation|swarm.?c2|failure taxonomy|network isolation|egress|schema temporal)|(context.tool isolation|swarm.?c2|failure taxonomy|schema temporal)[^\n]{0,30}MCP-?(6|9|12|13)\b", re.I)
out = subprocess.run(["git", "grep", "-nI", "-e", "v3.0", "-e", "MCP-", "--", ".", ":!docs/assessments", ":!tests/battery"], capture_output=True, text=True).stdout
rows = []
for line in out.splitlines():
    path, ln, text = line.split(":", 2)
    hit_label, hit_mcp = bool(LABEL.search(text)), bool(OLD_MCP.search(text))
    if not (hit_label or hit_mcp): continue
    t = text.strip()
    if re.search(r"controls-v3\.0\.json", t) and not re.search(r"(AI SAFE|SAFE2|SAFE²)[^\n]{0,12}v3\.0\b", t.replace("controls-v3.0.json","")): continue
    if path.startswith(("research/", "releases/")) or "CHANGELOG" in path or path in ("EVOLUTION.md", "MIGRATION.md", "guides/v3-release-overview.md"):
        cls = "HISTORICAL (dated record; keep)"
    elif re.search(r"GENESIS:SAFE2:v3\.0|Gateway v3\.0|Gateway v3\.0 component", t) or (path.startswith("gateway/") and re.search(r"Gateway[^\n]{0,4}v3\.0", t)):
        cls = "INTENTIONAL (component version or hash seed; keep)"
    elif re.search(r"\"MCP-\d+_[a-z_]+\"|MCP-\d+_[a-z_]+", t):
        cls = "INTENTIONAL (attestation file key, external contract; keep)"
    elif path.startswith("examples/mcp-security-toolkit/"):
        cls = "STALE DUPLICATE (pre-migration toolkit copy)"
    elif path.startswith(("examples/", "NEXUS/integrations/legacy-sovereign-runtimes/")):
        cls = "EXAMPLE RUNTIME PACKAGES"
    elif hit_mcp:
        cls = "SEMANTIC (old MCP numbering/meaning in shipped tooling)"
    else:
        cls = "CORE (shipped code, data, docs, CI templates)"
    rows.append({"class": cls, "path": path, "line": int(ln), "text": t[:200], "old_mcp": hit_mcp})
json.dump(rows, open(sys.argv[1], "w"), indent=1)
c = collections.Counter(r["class"] for r in rows)
for k, v in c.most_common(): print(f"{v:5}  {k}  ({len({r['path'] for r in rows if r['class']==k})} files)")
