"""AI SAFE2 v3.1 Scanner rule modules."""

from .p1_sanitize import P1_RULES
from .p2_audit import P2_RULES
from .p3_failsafe import P3_RULES
from .p4_monitor import P4_RULES
from .p5_evolve import P5_RULES
from .cross_pillar import CP_RULES
from .mcp_profile import MCP_RULES

ALL_RULES = (
    P1_RULES
    + P2_RULES
    + P3_RULES
    + P4_RULES
    + P5_RULES
    + CP_RULES
    + MCP_RULES
)
