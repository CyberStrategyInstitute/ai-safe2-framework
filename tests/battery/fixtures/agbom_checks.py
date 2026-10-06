"""NEXUS AgBOM adversarial checks. Prints: PASS|FAIL <id> :: detail"""
import copy
from nexus_sdk.agbom import AgBOMManager

def out(ok, cid, detail):
    print(f"{'PASS' if ok else 'FAIL'} {cid} :: {detail}")

def fresh():
    a = AgBOMManager("did:nexus:agent:t")
    a.discover_mcp_server("fs-mcp", "https://fs.example/mcp", tool_manifest_digest="a" * 64, version="1")
    a.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest="b" * 64, version="1")
    return a

# 1. tamper a component inside a historical snapshot
a = fresh()
a._version_history[0].components[0].supplier = "https://evil.example/mcp"
ok, v = a.verify_chain_integrity()
out(not ok, "tampered historical component detected", f"chain_ok={ok} violations={len(v)}")

# 2. tamper the latest snapshot
a = fresh()
a._version_history[-1].components[-1].capability_digest = "f" * 64
ok, v = a.verify_chain_integrity()
out(not ok, "tampered latest component detected", f"chain_ok={ok}")

# 3. snapshots are immutable w.r.t. later live edits
a = fresh()
before = a._version_history[0].components[0].supplier
for c in a.get_mcp_servers():
    c.supplier = "https://changed.example"
after = a._version_history[0].components[0].supplier
out(before == after, "historical snapshot isolated from live edits", f"{before} -> {after}")

# 4. rug pull: same server re-discovered with a different tool-manifest digest
a = fresh()
signal, detail = False, ""
try:
    v = a.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest="c" * 64, version="1")
    reason = (getattr(v, "change_reason", "") or "")
    held = [c for c in a._components.values() if getattr(c, "quarantined", False) or getattr(c, "status", "") == "hold"]
    signal = "digest" in reason or bool(held)
    wx = [c for c in a.get_mcp_servers() if c.name == "wx-mcp"]
    detail = f"reason={reason} held={len(held)} wx_entries={len(wx)}"
except Exception as e:
    signal, detail = True, f"raised {type(e).__name__}"
out(signal, "manifest digest change surfaced (rug pull)", detail)

# 5. a digest change must not leave the new digest silently trusted
a = fresh()
try:
    a.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest="c" * 64, version="1")
    trusted = [c for c in a.get_mcp_servers() if c.name == "wx-mcp" and c.capability_digest == "c" * 64
               and not getattr(c, "quarantined", False) and getattr(c, "status", "active") != "hold"]
    out(not trusted, "changed digest not silently trusted", f"trusted_new_digest={len(trusted)}")
except Exception as e:
    out(True, "changed digest not silently trusted", f"raised {type(e).__name__}")

# 6. same digest re-registration is idempotent (no false alarm)
a = fresh()
try:
    v = a.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest="b" * 64, version="1")
    held = [c for c in a._components.values() if getattr(c, "quarantined", False)]
    out(not held and "digest" not in (v.change_reason or ""), "unchanged digest: no false alarm", f"held={len(held)}")
except Exception as e:
    out(False, "unchanged digest: no false alarm", f"raised {type(e).__name__}")

# 7. a server registered with no digest is flagged, not trusted by default
a = AgBOMManager("did:nexus:agent:t")
a.discover_mcp_server("anon", "https://anon.example/mcp")
unsigned = a.get_unsigned_components()
out(len(unsigned) == 1, "unsigned/undigested server reported", f"unsigned={len(unsigned)}")
