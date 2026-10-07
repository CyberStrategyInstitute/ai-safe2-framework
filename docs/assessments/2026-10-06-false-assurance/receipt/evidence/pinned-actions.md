# Action pinning in workflows changed by this PR

## .github/workflows/ci.yml
```
  50:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
  53:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
  112:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
  115:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
  132:        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7
  146:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
  149:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
  182:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
  185:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
  204:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
  207:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
  235:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
  238:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
  268:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
```
Unpinned (not a 40-char SHA): 0

## .github/workflows/opa.yml
```
  39:        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
```
Unpinned (not a 40-char SHA): 0

Downloaded binaries in these workflows are checked against release sha256 (OPA 0.65.0, 1.4.2).
