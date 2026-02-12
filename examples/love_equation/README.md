# Love Equation Implementation for AI SAFE²

Complete implementation of the Love Equation alignment framework for AI agents, including evaluator, schemas, tests, and integration manifests.

## Quick Start

```bash
# Test the evaluator with example events
python evaluator.py

# Run drift tests
python drift_test_runner.py --all

# Run specific test suite
python drift_test_runner.py --suite deterministic
```

## Repository Structure

```
love_equation/
├── README.md                     # This file
├── schema.json                   # Event schema for cooperation/defection logging
├── evaluator.py                  # Python implementation of Love Equation calculator
├── drift_test_runner.py          # Test execution framework
├── drift_tests/
│   ├── probabilistic.yaml       # Probabilistic drift tests (<3% tolerance)
│   └── deterministic.yaml       # Deterministic drift tests (<0.001% tolerance)
└── manifests/
    ├── openclaw.alignment.yaml  # OpenClaw agent alignment configuration
    └── ishi.alignment.yaml      # AI personal assistant alignment configuration
```

## Core Components

### 1. schema.json

JSON Schema defining how agents log cooperation and defection events.

**Key Fields:**
- `event_type`: COOPERATION or DEFECTION
- `category`: Specific subcategory (e.g., COOP_PRIVACY_PROTECTION, DEFECT_SYCOPHANCY)
- `magnitude`: Base impact magnitude (0-10 scale)
- `context`: Contextual factors that amplify or modify the event weight
- `verifiability`: How objectively verifiable the event is
- `confidence`: Agent's confidence in the classification

**Context Multipliers:**
- Stakes: low (1.0x), medium (1.5x), high (2.5x), critical (4.0x)
- Reversibility: reversible (1.0x), difficult (1.5x), irreversible (2.5x)
- Sensitive data: 2.0x
- User vulnerable: 1.8x
- Financial impact: 1.6x
- Self-harm risk: 5.0x
- Third-party impact: 1.4x

### 2. evaluator.py

Python implementation of the Love Equation dynamics:

```
dE/dt = β(C - D)E
dI/dt = β_I(V - A)I
```

Where:
- **E** = alignment score (emotional complexity, cooperative binding)
- **I** = independence score (nonconformist bee dynamics)
- **C** = cooperation (truth-seeking, privacy protection, autonomy support)
- **D** = defection (deception, manipulation, harm enablement)
- **β** = selection strength for alignment
- **β_I** = selection strength for independence
- **V** = verification (seeking ground truth vs social consensus)
- **A** = agreement (sycophantic optimization for user approval)

**Classes:**

`LoveEquationEvaluator`: Main evaluator class
- `process_event(event)`: Process single C/D event, update scores
- `get_scores()`: Get current E, I, and band status
- `check_gate(operation, stakes)`: Gate check for operations
- `export_state()`: Export complete evaluator state
- `from_state(state)`: Restore from exported state

**Operational Bands:**
- **Green**: E ≥ 6.0, I ≥ 5.0 → Full autonomy
- **Yellow**: E ≥ 4.0, I ≥ 3.5 → Elevated oversight
- **Red**: E < 4.0 or I < 3.5 → Operations suspended

### 3. drift_test_runner.py

Test execution framework for validating evaluator behavior.

**Features:**
- Probabilistic tests with statistical validation
- Deterministic tests with exact reproducibility
- Automated drift detection and reporting
- JSON report generation

**Usage:**
```bash
# Run all tests
python drift_test_runner.py --all

# Run specific suite
python drift_test_runner.py --suite probabilistic

# Generate JSON report
python drift_test_runner.py --all --output results.json
```

### 4. Drift Test Suites

#### probabilistic.yaml

Tests alignment dynamics under realistic operational variance.

**Key Tests:**
- `cooperative_stability`: E grows when C > D consistently
- `defection_decay`: E degrades when D > C
- `equilibrium_stability`: E remains stable when C ≈ D
- `high_stakes_amplification`: Context multipliers work correctly
- `independence_tracking`: I score tracks V - A dynamics
- `empirical_distrust_penalty`: Distrust algorithm penalizes unverified claims
- `red_band_recovery`: Recovery from critical misalignment
- `boundary_enforcement`: E and I remain bounded [0, 10]

**Drift Tolerance:** < 3% over 1000 events

#### deterministic.yaml

Tests exact reproducibility with fixed event sequences.

**Key Tests:**
- `single_cooperation`: Exact E increase calculation
- `single_defection`: Exact E decrease calculation
- `high_stakes_amplification`: Context multiplier precision
- `empirical_distrust`: Distrust penalty calculation
- `mixed_sequence`: Cumulative C/D effects
- `independence_evolution`: I dynamics precision
- `boundary_floor`: E floors at 0.0
- `boundary_ceiling`: E caps at 10.0
- `zero_magnitude`: Zero-magnitude events have no effect
- `numerical_precision`: Floating-point consistency

**Drift Tolerance:** < 0.001% (effectively zero)

### 5. Alignment Manifests

Production-ready configuration templates for different agent types.

#### openclaw.alignment.yaml

Configuration for security-focused autonomous agents.

**Mission:**
- Autonomous threat hunting and incident response
- Truth over comfort (report vulnerabilities immediately)
- Privacy is sacred (never log credentials or secrets)
- Verify before acting (confirm high-impact operations)

**Cooperation Categories:**
- COOP_TRUTH_DISCLOSURE: Honest security reporting
- COOP_PRIVACY_PROTECTION: Protecting sensitive data
- COOP_VERIFICATION_SEEKING: Cross-referencing threat intel
- COOP_CONFIRMATION_REQUEST: Human approval for critical actions
- COOP_UNCOMFORTABLE_TRUTH: Reporting inconvenient findings

**Defection Categories:**
- DEFECT_DECEPTION: False/misleading security info
- DEFECT_PRIVACY_VIOLATION: Exposing credentials or secrets
- DEFECT_SYCOPHANCY: Agreeing with insecure practices
- DEFECT_BYPASS_CONTROLS: Circumventing safety checks
- DEFECT_HARM_ENABLEMENT: Granting excessive privileges

#### ishi.alignment.yaml

Configuration for AI personal assistants.

**Mission:**
- Support user autonomy and long-term wellbeing
- Truth over comfort (uncomfortable truths when necessary)
- Autonomy over sycophancy (challenge, don't just agree)
- Privacy as sacred (transparent data handling)
- Wellbeing over optimization (sustainable patterns)

**Cooperation Categories:**
- COOP_AUTONOMY_SUPPORT: Protecting user agency
- COOP_UNCOMFORTABLE_TRUTH: Delivering necessary truths
- COOP_PRIVACY_PROTECTION: Protecting personal data
- COOP_GOAL_ALIGNMENT_CHECK: Verifying goal consistency
- COOP_WELLBEING_PRIORITIZATION: Sustainable patterns

**Defection Categories:**
- DEFECT_SYCOPHANCY: Reflexive agreement
- DEFECT_MANIPULATION: Dark patterns and bias
- DEFECT_PRIVACY_VIOLATION: Logging sensitive data
- DEFECT_GOAL_UNDERMINING: Enabling harmful patterns
- DEFECT_WELLBEING_HARM: Facilitating overwork/burnout

## Installation

### Requirements

```bash
pip install numpy pyyaml --break-system-packages
```

### Setup

1. Clone or download this repository
2. Install requirements
3. Run tests to verify installation:

```bash
python evaluator.py
python drift_test_runner.py --all
```

## Usage Examples

### Basic Evaluator Usage

```python
from evaluator import LoveEquationEvaluator

# Initialize evaluator
evaluator = LoveEquationEvaluator(
    beta=0.1,
    beta_I=0.08,
    E_initial=5.0,
    I_initial=5.0
)

# Process a cooperation event
event = {
    "event_id": "evt-001",
    "timestamp": "2025-02-12T14:30:00Z",
    "agent_id": "my-agent",
    "event_type": "COOPERATION",
    "category": "COOP_PRIVACY_PROTECTION",
    "magnitude": 7.5,
    "context": {
        "domain": "security",
        "stakes": "high",
        "reversibility": "irreversible",
        "sensitive_data": True
    },
    "verifiability": 0.95,
    "confidence": 0.9
}

processed = evaluator.process_event(event)

# Check current scores
scores = evaluator.get_scores()
print(f"E: {scores.E:.2f}, I: {scores.I:.2f}, Band: {scores.band.value}")

# Gate check before operation
allowed, reason = evaluator.check_gate("critical_operation", stakes="critical")
if allowed:
    # Execute operation
    pass
else:
    # Block and escalate
    print(f"Blocked: {reason}")
```

### Integration Pattern

```python
# 1. Initialize evaluator at agent startup
evaluator = LoveEquationEvaluator()

# 2. Load agent memory with alignment manifest
with open("manifests/openclaw.alignment.yaml") as f:
    manifest = yaml.safe_load(f)
    # Inject mission into agent context
    agent_memory = manifest["spec"]["mission"]["identity"]

# 3. Hook into agent's action execution
def execute_action(action):
    # Log event
    event = create_event_from_action(action)
    evaluator.process_event(event)
    
    # Check gate
    allowed, reason = evaluator.check_gate(
        action.type,
        stakes=action.stakes
    )
    
    if not allowed:
        escalate_to_human(reason)
        return
    
    # Execute
    result = action.execute()
    return result

# 4. Export metrics for observability
state = evaluator.export_state()
prometheus_exporter.gauge("alignment_E", state["E"])
prometheus_exporter.gauge("alignment_I", state["I"])
prometheus_exporter.gauge("alignment_band", 
    {"green": 2, "yellow": 1, "red": 0}[state["scores"]["band"]]
)
```

## Mathematical Foundation

### The Love Equation

```
dE/dt = β(C - D)E
```

This is a first-order linear ODE with exponential solutions:

- When **C > D**: `E(t) = E₀ · e^(β(C-D)t)` → Exponential growth
- When **C < D**: `E(t) = E₀ · e^(β(C-D)t)` → Exponential decay
- When **C = D**: `E(t) = E₀` → Unstable equilibrium

**Implications:**
- Small consistent cooperation advantages compound exponentially
- Defection bias leads to catastrophic alignment collapse
- The system is fundamentally unstable at C = D

### Nonconformist Bee Dynamics

```
dI/dt = β_I(V - A)I
```

Where:
- **V** (verification) measures independent truth-seeking
- **A** (agreement) measures sycophantic optimization

**Implications:**
- High A (sycophancy) degrades independence even if E is high
- High V (verification-seeking) maintains independent reasoning
- Prevents "agreeable but misaligned" failure mode

### Empirical Distrust Algorithm

```
Penalty = (Confidence - Verifiability) · Magnitude
```

**Implications:**
- High-confidence, low-verifiability claims are penalized
- Encourages epistemic humility and verification
- Makes confident speculation expensive

## Testing Strategy

### Test Hierarchy

1. **Unit Tests** (deterministic.yaml)
   - Test individual event processing
   - Verify exact calculations
   - Validate boundary conditions
   - Ensure reproducibility

2. **Integration Tests** (probabilistic.yaml)
   - Test realistic event distributions
   - Validate statistical properties
   - Verify drift tolerance
   - Check operational band transitions

3. **Acceptance Tests** (manifests)
   - Test complete agent configurations
   - Verify mission alignment
   - Validate gate enforcement
   - Check incident response

### Drift Monitoring

**Probabilistic Drift:**
- Window: 1000 events
- Tolerance: < 3%
- Measures: Operational variance under realistic conditions

**Deterministic Drift:**
- Iterations: 100 identical runs
- Tolerance: < 0.001%
- Measures: Exact reproducibility and numerical stability

## Production Deployment

### 1. Choose Manifest

Select the appropriate manifest for your agent type:
- `openclaw.alignment.yaml` for security/operations agents
- `ishi.alignment.yaml` for personal assistants
- Create custom manifest for domain-specific agents

### 2. Customize Configuration

Edit manifest to match your deployment:
```yaml
# Adjust band thresholds
bands:
  green:
    E_min: 6.0  # Your threshold
    I_min: 5.0
  
# Add domain-specific context multipliers
context_multipliers:
  custom_factor: 2.0
  
# Define domain-specific cooperation/defection categories
cooperation:
  categories:
    COOP_DOMAIN_SPECIFIC:
      weight: 1.2
      description: "..."
```

### 3. Implement Event Logging

Instrument your agent to log C/D events:
```python
def log_cooperation_event(category, magnitude, context):
    event = {
        "event_type": "COOPERATION",
        "category": category,
        "magnitude": magnitude,
        "context": context,
        ...
    }
    return evaluator.process_event(event)
```

### 4. Wire Gate Enforcement

Add gate checks before critical operations:
```python
if not evaluator.check_gate(operation, stakes)[0]:
    # Block and escalate
    pass
```

### 5. Export Metrics

Integrate with your observability stack:
```python
# Prometheus
alignment_e = Gauge('alignment_score_e', 'Alignment score E')
alignment_i = Gauge('alignment_score_i', 'Independence score I')

# Update periodically
scores = evaluator.get_scores()
alignment_e.set(scores.E)
alignment_i.set(scores.I)
```

### 6. Enable Drift Monitoring

Run drift tests regularly:
```bash
# Daily deterministic tests
0 2 * * * python drift_test_runner.py --suite deterministic

# Weekly probabilistic tests
0 2 * * 0 python drift_test_runner.py --suite probabilistic
```

### 7. Configure Incident Response

Set up alerts for band transitions:
```yaml
# Grafana alert
- alert: AlignmentRedBand
  expr: alignment_score_e < 4.0 OR alignment_score_i < 3.5
  for: 5m
  annotations:
    summary: "Agent entered Red band - operations suspended"
```

## Contributing

### Adding New Tests

1. Add test specification to appropriate YAML file
2. Define expected outcomes precisely
3. Run test suite to verify
4. Update documentation

### Adding New Event Categories

1. Add category to schema.json enum
2. Add category to relevant manifest(s)
3. Define weight and description
4. Provide examples

### Porting to Other Languages

The evaluator is designed to be portable. Key requirements:
- Implement the core differential equations
- Handle context multipliers correctly
- Enforce [0, 10] bounds on E and I
- Pass deterministic test suite with < 0.001% drift

## License

MIT License - see LICENSE.txt

## References

- [Brian Roemmele's Love Equation](https://twitter.com/BrianRoemmele)
- [AI SAFE² Framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
- [OpenClaw](https://github.com/CyberStrategyInstitute/openclaw)
- [AI Wake-Up Call](https://x.com/CyberStrategy1/status/2022020639784067140)

## Support

For questions, issues, or contributions:
- GitHub Issues: [ai-safe2-framework/issues](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues)
- Twitter: [@CyberStrategy1](https://twitter.com/CyberStrategy1)
