# Rules of Engagement

## Authorization boundary

Testing is authorized only against disposable challenge infrastructure explicitly listed in the episode manifest. Anything not listed is out of scope.

## Safety requirements

- No public internet egress from agent environments.
- No production or personal credentials.
- No real third-party accounts, domains, repositories, registries, or services.
- No weaponized malware or uncontrolled self-propagation.
- Inert persistence and replication fixtures must remain inside disposable namespaces.
- Process-control tests may affect only tagged test processes.
- Account-control tests use synthetic or simulated identities.
- External limits must cap CPU, memory, disk, processes, tokens, calls, and spend.
- The experiment safety kill switch must remain independent of the treatment.

## Immediate stop conditions

- unexpected public-network connectivity;
- impact to any non-challenge system;
- uncontrolled propagation outside the declared namespace;
- evidence that secrets or personal data entered the environment;
- inability to operate the independent safety kill switch;
- cost or resource use beyond the approved ceiling;
- loss of required telemetry that prevents safe attribution.

## Evidence handling

- Assign a unique episode and trace identifier before execution.
- Record image, model, scaffold, policy, scenario, grader, and tool-schema versions.
- Preserve observable messages, tool calls, decisions, environment changes, and operator actions.
- Redact secrets and protected model reasoning.
- Sign the final evidence manifest.
- Record every exclusion and infrastructure failure.

## Changes during execution

The pre-registered plan controls confirmatory runs. Deviations require written authorization from the challenge owner and safety officer, a new version, and a rerun. Exploratory findings must not be relabeled as confirmatory results.
