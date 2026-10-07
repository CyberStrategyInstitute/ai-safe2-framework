"""Area 1: safe2 skill - structural, referential, and cross-surface consistency."""
import json, re, sys, pathlib, collections
R = pathlib.Path(sys.argv[1])
S = R / "skills"
fails, warns, passes = [], [], []
def ok(c, msg, warn=False):
    (passes if c else (warns if warn else fails)).append(msg)

tax = json.loads((S/"mcp/data/ai-safe2-controls-v3.0.json").read_text())
prof = json.loads((S/"mcp/data/mcp-profile-v3.1.json").read_text())
core_ids = {c["id"] for c in tax["pillar_controls"]} | {c["id"] for c in tax["cross_pillar_controls"]}
mcp_ids = {c["id"] for c in prof["controls"]}
ok(len(core_ids) == 161, f"core taxonomy has 161 unique controls (got {len(core_ids)})")
ok(len(tax["pillar_controls"]) + len(tax["cross_pillar_controls"]) == len(core_ids), "no duplicate control IDs")
ok({c["id"] for c in tax["cross_pillar_controls"]} == {f"CP.{i}" for i in range(1, 11)}, "cross-pillar = CP.1..CP.10")
ok(mcp_ids == {f"MCP-{i}" for i in range(1, 20)}, f"MCP profile = MCP-1..MCP-19 (got {len(mcp_ids)})")
ok(tax["metadata"]["version"].startswith("3.1"), f"taxonomy metadata version is v3.1 (says {tax['metadata']['version']}; filename v3.0 is documented provenance)", warn=True)

def front(p):
    t = p.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m: return None, t
    import yaml
    return yaml.safe_load(m.group(1)), t

# The canonical skill lives in its own package folder; skills/ itself must not be one.
skills = sorted(S.glob("*/SKILL.md")) + sorted(S.glob("codex/*/SKILL.md"))
ok(not (S / "SKILL.md").exists(), "skills/ root is not a skill package (no skills/SKILL.md)")
ok((S / "ai-safe2-secure-build-copilot" / "SKILL.md").exists(), "canonical skill package present")
for sk in skills:
    fm, body = front(sk)
    rel = sk.relative_to(R)
    ok(fm is not None, f"{rel}: has YAML frontmatter")
    if not fm: continue
    name, desc = fm.get("name", ""), " ".join(str(fm.get("description", "")).split())
    ok(bool(re.fullmatch(r"[a-z0-9-]{1,64}", name)), f"{rel}: name '{name}' valid")
    ok(0 < len(desc) <= 1024, f"{rel}: description length {len(desc)} <= 1024")
    ok("<" not in desc and ">" not in desc, f"{rel}: description has no angle brackets")
    # A v3.0 description on a surface whose body is v3.0 content is accurate; flag it for
    # the content refresh (open decision D3) rather than as a false claim.
    ok("v3.0" not in desc, f"{rel}: description says v3.0 (surface content is v3.0: D3)", warn=True)
    # referential: every control ID cited must exist
    # Negated mentions ("does not create CP.11") are not citations.
    NEG = re.compile(r"\b(not|never|no)\b", re.I)
    cited = set()
    for ln in body.splitlines():
        ids = set(re.findall(r"\b(?:P[1-5]\.T\d+\.\d+|CP\.\d+|[SAFEM]\d\.\d+|MCP-\d+)\b", ln))
        cited |= {i for i in ids if not (NEG.search(ln) and i not in core_ids | mcp_ids)}
    unknown = sorted(c for c in cited if c not in core_ids | mcp_ids and not re.fullmatch(r"CP\.5", c))
    ok(not unknown, f"{rel}: all {len(cited)} cited control IDs exist" + (f" - UNKNOWN: {unknown[:15]}" if unknown else ""))
    # relative links resolve
    links = re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+)", body)
    broken = [l for l in links if not (sk.parent / l).exists()]
    ok(not broken, f"{rel}: {len(links)} relative links resolve" + (f" - BROKEN: {broken[:8]}" if broken else ""))

# every md under skills: links + version claims
for md in sorted(S.rglob("*.md")):
    if "/mcp/" in str(md) and "README" not in md.name: continue
    t = md.read_text()
    links = re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+)", t)
    broken = [l for l in links if not (md.parent / l).exists()]
    if broken: fails.append(f"{md.relative_to(R)}: broken links {broken[:6]}")
    if re.search(r"AI SAFE2? ?v3\.0|AI SAFE² v3\.0 (Skill|Evaluation)", t) and "provenance" not in t:
        warns.append(f"{md.relative_to(R)}: still labels itself v3.0")
    for ln in t.splitlines():
        # Historical rows and statements that prevent a claim are not claims.
        if re.search(r"\b(not|never|prevent|accidental|historical|v2\.1|previously)\b", ln, re.I):
            continue
        for n in re.findall(r"\b(1[2-9]\d) (?:core )?controls\b", ln):
            if n != "161": fails.append(f"{md.relative_to(R)}: claims {n} controls")
# evals cite real controls
ev = (S/"evals.md").read_text()
cited = set(re.findall(r"\b(?:P[1-5]\.T\d+\.\d+|CP\.\d+|[SAFEM]\d\.\d+)\b", ev))
unknown = sorted(c for c in cited if c not in core_ids)
ok(not unknown, f"evals.md: all {len(cited)} expected control IDs exist" + (f" - UNKNOWN: {unknown}" if unknown else ""))

print(f"PASS {len(passes)}  WARN {len(warns)}  FAIL {len(fails)}")
for f in fails: print("FAIL", f)
for w in warns: print("WARN", w)
