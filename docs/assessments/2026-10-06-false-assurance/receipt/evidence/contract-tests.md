# Contract tests at 21a8333

## Version: 0.65.0: opa check --strict + opa test NEXUS/opa
```
check: OK
data.nexus.aism_test.test_policy_loads_and_scores: PASS
data.nexus.aism_test.test_i1_authenticated_borders_holds_with_full_identity: PASS (640.972µs)
data.nexus.aism_test.test_i1_fails_without_did: PASS (395.346µs)
data.nexus.aism_test.test_memory_scope_downgrade_is_blocked: PASS
data.nexus.aism_test.test_empty_input_is_not_allowed: PASS
data.nexus.authz_test.test_declared_request_scope_cannot_downgrade_permanent_write: PASS
data.nexus.authz_test.test_most_restrictive_declaration_wins: PASS
data.nexus.authz_test.test_unknown_scope_label_fails_closed: PASS
data.nexus.authz_test.test_consistent_request_scope_needs_no_mandate: PASS
data.nexus.authz_test.test_valid_mandate_satisfies_durable_write: PASS
data.nexus.authz_test.test_denial_reports_its_reason: PASS
data.nexus.authz_test.test_ordinary_call_has_a_decision: PASS
data.nexus.authz_test.test_decision_defined_when_fields_missing: PASS
data.nexus.authz_test.test_undeclared_memory_write_needs_mandate: PASS (936.762µs)
data.nexus.authz_test.test_explicit_deny_blocks_allow: PASS
data.nexus.authz_test.test_approved_config_change_allowed: PASS
PASS: 16/16
```

## Version: 1.4.2: opa check --strict + opa test NEXUS/opa
```
check: OK
data.nexus.aism_test.test_policy_loads_and_scores: PASS
data.nexus.aism_test.test_i1_authenticated_borders_holds_with_full_identity: PASS (485.834µs)
data.nexus.aism_test.test_i1_fails_without_did: PASS (310.912µs)
data.nexus.aism_test.test_memory_scope_downgrade_is_blocked: PASS (832.842µs)
data.nexus.aism_test.test_empty_input_is_not_allowed: PASS (878.471µs)
data.nexus.authz_test.test_declared_request_scope_cannot_downgrade_permanent_write: PASS
data.nexus.authz_test.test_most_restrictive_declaration_wins: PASS
data.nexus.authz_test.test_unknown_scope_label_fails_closed: PASS
data.nexus.authz_test.test_consistent_request_scope_needs_no_mandate: PASS
data.nexus.authz_test.test_valid_mandate_satisfies_durable_write: PASS
data.nexus.authz_test.test_denial_reports_its_reason: PASS
data.nexus.authz_test.test_ordinary_call_has_a_decision: PASS
data.nexus.authz_test.test_decision_defined_when_fields_missing: PASS
data.nexus.authz_test.test_undeclared_memory_write_needs_mandate: PASS (573.064µs)
data.nexus.authz_test.test_explicit_deny_blocks_allow: PASS
data.nexus.authz_test.test_approved_config_change_allowed: PASS (806.419µs)
PASS: 16/16
```

## APay policy migration differential (main on OPA 0.65 vs branch on OPA 1.4.2)
```
inputs=873 identical=873 stricter=0 looser=0 base_decision_new=allow base_decision_old=allow
PASS apay rewrite never loosens a decision
```

## authz decision contract (OPA 1.4.2)
```
PASS evaluates on OPA 1.x :: yes
PASS baseline capability allowed :: allow=True
PASS durable memory write w/o mandate denied :: allow=False deny_reason='durable memory writes require a Memory Mandate'
PASS durable memory write with mandate allowed :: allow=True
PASS scope downgrade: PERMANENT zone + 'request' scope denied :: allow=False deny_reason='durable memory writes require a Memory Mandate'
PASS unrecognized scope 'Durable ' w/o mandate denied :: allow=False deny_reason='swarm_shared memory writes require a Memory Mandate'
PASS credential: tool from TASK_CONTEXT denied :: allow=False deny_reason='TASK_CONTEXT cannot access credential: tools'
PASS config_change ACT-2 w/o approval denied :: allow=False deny_reason='ConfigChange requires out-of-band approval for ACT-2+ agents'
PASS config_change ACT-2 with approval allowed :: allow=True
PASS revoked agent denied :: allow=False deny_reason='agent revoked or under hard brake'
PASS scope widening denied :: allow=False deny_reason='requested capabilities exceed parent VCC'
PASS delegation depth 5 denied :: allow=False deny_reason='delegation depth missing or above 4'
PASS missing delegation depth denied :: allow=False deny_reason='delegation depth missing or above 4'
PASS unknown compartment denied :: allow=False deny_reason='unrecognized context compartment'
PASS decision defined for every input :: undefined for 0/13
PASS deny_reason explains a denial :: 'TASK_CONTEXT cannot access credential: tools'
```
