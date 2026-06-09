/**
 * circuit_breaker.js — Swarm Execution Circuit Breaker & Subagent Governance
 *
 * Implements:
 *   Pillar 3: Fail-Safe & Recovery (F3.2 Recursion Limits, F3.4 Cascade Containment)
 *   Pillar 1: Sanitize & Isolate   (Subagent privilege boundary enforcement)
 *
 * Threat classes covered:
 *   - Runaway / recursive tool loop detection
 *   - Subagent privilege escalation attempts
 *   - Memory poisoning via unauthorized state writes
 *   - Fork-bomb style rapid parallel invocations
 *   - Bounded call history (prevents memory exhaustion)
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// ─── Constants ────────────────────────────────────────────────────────────────

const SUBAGENT_ESCALATION_SIGNALS = new Set([
  // Privilege escalation terms a subagent should never request
  'unsandboxed', 'root_access', 'admin_mode', 'bypass_policy',
  'override_soul', 'override_identity', 'disable_gateway',
  'ask_permission',  // subagents must bubble up, not ask directly
]);

const MEMORY_POISON_PATTERNS = [
  /system\s*override/gi,
  /ignore\s+(?:all\s+)?previous\s+instructions/gi,
  /you\s+(?:must|shall)\s+now/gi,
  /update\s+SOUL\.md/gi,
  /overwrite\s+IDENTITY\.md/gi,
  /MEMORY\.md.*=.*eval/gi,
];

const MAX_CALL_HISTORY = 1000;  // hard cap — prevents unbounded memory growth

// ─── CircuitBreaker Class ─────────────────────────────────────────────────────
class CircuitBreaker {
  /**
   * @param {number} maxRecursionDepth   - Max identical calls in the time window
   * @param {number} loopDetectionWindowMs
   * @param {string} [logPath]
   */
  constructor(
    maxRecursionDepth    = 5,
    loopDetectionWindowMs = 5000,
    logPath              = path.join(__dirname, 'audit.log'),
  ) {
    this.maxRecursionDepth    = maxRecursionDepth;
    this.loopDetectionWindowMs = loopDetectionWindowMs;
    this.logPath              = logPath;
    this.callHistory          = [];  // bounded ring-buffer (capped at MAX_CALL_HISTORY)
    this._trippedTools        = new Set();  // permanently tripped tools this session
  }

  // ── Logging ──────────────────────────────────────────────────────────────

  logEvent(level, controlId, category, message, evidence = {}) {
    try {
      const entry = {
        ts:         new Date().toISOString(),
        level,
        control_id: controlId,
        category,
        message,
        ...evidence,
      };
      fs.appendFileSync(this.logPath, JSON.stringify(entry) + '\n', 'utf8');
      console.log(`[CIRCUIT-BREAKER-${level}] [${controlId}] [${category}] ${message}`);
    } catch (err) {
      process.stderr.write(`[CB-LOG-ERROR] ${err.message}\n`);
    }
  }

  // ── Core Loop Detection ──────────────────────────────────────────────────

  /**
   * Register a tool call and check for runaway loop patterns.
   * @param {string} toolName
   * @param {object} args
   * @returns {{ tripped: boolean, reason: string }}
   */
  registerCall(toolName, args = {}) {
    try {
      // If this tool already tripped the breaker, stay tripped
      if (this._trippedTools.has(toolName)) {
        return this._trip(toolName, 'F3.2', 'CIRCUIT_ALREADY_TRIPPED',
          `Tool '${toolName}' is still in tripped state from a previous trigger.`);
      }

      const now   = Date.now();
      const entry = {
        timestamp: now,
        tool:      toolName,
        argHash:   this._hashArgs(args),
      };

      // Bounded history — drop oldest entries when at capacity
      this.callHistory.push(entry);
      if (this.callHistory.length > MAX_CALL_HISTORY) {
        this.callHistory.shift();
      }

      // Count identical calls within the detection window
      const identical = this.callHistory.filter(c =>
        c.tool === toolName &&
        c.argHash === entry.argHash &&
        (now - c.timestamp) <= this.loopDetectionWindowMs,
      );

      this.logEvent('INFO', 'F3.2', 'RECURSION_AUDIT',
        `Tool '${toolName}': ${identical.length}/${this.maxRecursionDepth} calls in window`,
        { depth: identical.length, threshold: this.maxRecursionDepth });

      if (identical.length >= this.maxRecursionDepth) {
        this._trippedTools.add(toolName);
        return this._trip(toolName, 'F3.2', 'CIRCUIT_BREAKER_TRIGGERED',
          `Runaway recursion loop detected for tool '${toolName}' — ` +
          `${identical.length} identical calls in ${this.loopDetectionWindowMs}ms.`);
      }

      return { tripped: false, reason: 'Execution path within bounds.' };

    } catch (err) {
      // FAIL CLOSED
      return this._trip(toolName, 'F3.2', 'CIRCUIT_INTERNAL_ERROR',
        `Circuit breaker threw internally: ${err.message} — failing closed.`);
    }
  }

  // ── Subagent Privilege Governance ────────────────────────────────────────

  /**
   * Verify a subagent spawn request does not escalate privileges.
   * @param {object} spawnRequest  - { agentName, mode, permissions }
   * @returns {{ authorized: boolean, reason: string }}
   */
  validateSubagentSpawn(spawnRequest = {}) {
    try {
      const { agentName = 'unknown', mode = '', permissions = [] } = spawnRequest;

      // Unsandboxed spawn is always denied
      if (mode === 'unsandboxed' || (typeof mode === 'string' && mode.toLowerCase().includes('root'))) {
        this.logEvent('ALERT', 'P1.SUBAGENT', 'SUBAGENT_ESCALATION_BLOCKED',
          `Subagent '${agentName}' requested unsandboxed/root mode — denied.`,
          { mode, agentName });
        return {
          authorized: false,
          reason: `AI SAFE² Policy: Unsandboxed subagent spawn denied for '${agentName}'.`,
        };
      }

      // Check for escalation keywords in permission list
      const escalatingPerms = (Array.isArray(permissions) ? permissions : [])
        .filter(p => SUBAGENT_ESCALATION_SIGNALS.has(String(p).toLowerCase()));

      if (escalatingPerms.length > 0) {
        this.logEvent('ALERT', 'P1.SUBAGENT', 'SUBAGENT_PERMISSION_VIOLATION',
          `Subagent '${agentName}' requested escalated permissions: ${escalatingPerms.join(', ')}`,
          { agentName, escalatingPerms });
        return {
          authorized: false,
          reason: `AI SAFE² Policy: Subagent requested disallowed permissions: ${escalatingPerms.join(', ')}.`,
        };
      }

      this.logEvent('INFO', 'P1.SUBAGENT', 'SUBAGENT_SPAWN_AUTHORIZED',
        `Subagent '${agentName}' approved with mode '${mode}'.`);
      return { authorized: true, reason: `Subagent spawn authorized in sandboxed mode.` };

    } catch (err) {
      this.logEvent('ERROR', 'P1.SUBAGENT', 'SUBAGENT_CHECK_ERROR',
        `Error during subagent validation: ${err.message} — denying.`);
      return { authorized: false, reason: `Subagent validation error — denied (fail-closed).` };
    }
  }

  // ── Memory Poisoning Detection ───────────────────────────────────────────

  /**
   * Scan a proposed memory write for injection payloads before persistence.
   * @param {string} content
   * @returns {{ safe: boolean, reason: string }}
   */
  validateMemoryWrite(content) {
    try {
      if (typeof content !== 'string') {
        this.logEvent('ALERT', 'P1.MEMORY', 'MEMORY_TYPE_VIOLATION',
          'Non-string content rejected for memory write.');
        return { safe: false, reason: 'Memory write rejected: non-string content.' };
      }

      for (const pattern of MEMORY_POISON_PATTERNS) {
        pattern.lastIndex = 0;
        if (pattern.test(content)) {
          this.logEvent('ALERT', 'P1.MEMORY', 'MEMORY_POISONING_BLOCKED',
            `Memory poisoning pattern detected: ${pattern.source}`,
            { pattern: pattern.source });
          return {
            safe:   false,
            reason: `Memory write blocked — injection pattern detected: ${pattern.source}`,
          };
        }
      }

      this.logEvent('INFO', 'P1.MEMORY', 'MEMORY_WRITE_CLEARED',
        'Memory write content passed poisoning scan.');
      return { safe: true, reason: 'Memory content cleared poison scanner.' };

    } catch (err) {
      this.logEvent('ERROR', 'P1.MEMORY', 'MEMORY_CHECK_ERROR',
        `Error during memory validation: ${err.message} — denying.`);
      return { safe: false, reason: `Memory validation error — denied (fail-closed).` };
    }
  }

  // ── Rollback ─────────────────────────────────────────────────────────────

  triggerRollback() {
    this.logEvent('ALERT', 'F3.4', 'SYSTEM_ROLLBACK',
      'Initiating automated rollback to last verified workspace state...');
    // In production: exec('git reset --hard HEAD') or restore backup.
    return {
      status:       'ROLLBACK_INITIATED',
      rollbackTime: new Date().toISOString(),
      message:      'Workspace rollback initiated. All pending operations voided.',
    };
  }

  /**
   * Reset trip state for a specific tool (for testing / manual recovery).
   * @param {string} toolName
   */
  resetTrip(toolName) {
    this._trippedTools.delete(toolName);
    this.callHistory = this.callHistory.filter(c => c.tool !== toolName);
    this.logEvent('INFO', 'F3.2', 'CIRCUIT_RESET',
      `Circuit breaker manually reset for tool '${toolName}'.`);
  }

  // ── Private Helpers ──────────────────────────────────────────────────────

  _hashArgs(args) {
    try {
      return JSON.stringify(args);
    } catch {
      return String(args);
    }
  }

  _trip(toolName, controlId, category, message) {
    this.logEvent('ALERT', controlId, category, message, { tool: toolName });
    return {
      tripped: true,
      reason:  `[AI SAFE² Fail-Safe Tripped] ${controlId}: ${message}`,
    };
  }
}

module.exports = CircuitBreaker;
