# Licensing by component

The repository uses different licenses for different material. Read
[COPYRIGHT](../COPYRIGHT), the [existing scope agreement](../LICENSE), and the
license applicable to the files being copied or distributed.

| Material | Current designation | License text |
| --- | --- | --- |
| NEXUS SDK and NEXUS implementation | Apache-2.0 | [NEXUS license](../NEXUS/LICENSE), [NOTICE](../NEXUS/NOTICE) |
| CLI, MCP server implementation, sovereign-runtime implementation examples | MIT, unless a file or subdirectory says otherwise | [MIT](../LICENSE-MIT) |
| Framework methodology, taxonomy content, and documentation | CC-BY-SA-4.0, subject to existing explicit designations | [CC BY-SA 4.0](../LICENSE-CC-BY-SA-4.0) |
| Framework-based skill guidance in SKILL.md | Framework/documentation designation; inspect file notices | [CC BY-SA 4.0](../LICENSE-CC-BY-SA-4.0) |
| Executable skill helpers | Applicable code license; preserve third-party terms | [MIT default](../LICENSE-MIT) |
| Developer Workflow standalone package | Its existing MIT designation | [Developer Workflow license](../developer-workflow/LICENSE) |

MCP implementation code and the framework content it serves have separate
license scopes. The MCP package's MIT metadata describes its implementation;
retain the framework license notice when distributing its taxonomy/profile
content. The canonical taxonomy already states its framework/docs and code
designations. Its bytes remain unchanged by this presentation fix.

Some sovereign-runtime READMEs explicitly designate MIT. Those notices remain
in place. Copying framework methodology into an example does not erase the
framework's license. Check existing notices when a distribution combines code,
documentation, and framework data.

## GitHub presentation

GitHub reports NOASSERTION for the root custom combined license on the checked
default branch. Standard root license texts let GitHub and downstream tools
discover the existing MIT, Apache-2.0, and CC-BY-SA-4.0 texts separately.
NEXUS retains its own complete Apache-2.0 text and NOTICE. Explicit badges
and this scope table explain which component uses which license.

GitHub's repository-level license field is not a per-directory license map.
The mixed repository cannot accurately be described as wholly Apache-2.0.
Detection and presentation must be checked again after a reviewed change
reaches the default branch; adding files in a draft PR does not establish
that GitHub has reclassified the repository.

Sources: [GitHub licensing documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository),
[GitHub multiple-license navigation](https://github.blog/changelog/2022-05-26-easily-discover-and-navigate-to-multiple-licenses-in-repositories/),
[Apache-2.0 terms](https://www.apache.org/licenses/LICENSE-2.0), and
[CC BY-SA 4.0 terms](https://creativecommons.org/licenses/by-sa/4.0/).
