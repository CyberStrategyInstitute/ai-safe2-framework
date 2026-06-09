/**
 * safe_gateway.js — AI SAFE² External Enforcement Gateway
 *
 * Implements:
 *   Pillar 1: Sanitize & Isolate  (P1.INJECT, P1.PATH, P1.SECRET, P1.DOMAIN)
 *   Pillar 4: Engage & Monitor    (P4.EXFIL, P4.AUDIT)
 *
 * Design contract: FAIL CLOSED.
 * If any internal component errors, the action is DENIED, never passed through.
 *
 * Threat classes covered:
 *   - Indirect Prompt Injection (IPI)
 *   - Outbound exfiltration (domain allowlist + private-IP block)
 *   - Domain-trick bypasses (subdomain confusion, encoded URLs, alt schemes)
 *   - Path traversal (../ chains, absolute escapes, Windows device paths)
 *   - Symlink / junction escape
 *   - Chained-command injection (;, &&, ||, |, $(), backtick)
 *   - Interactive / admin command requests
 *   - Cleartext secret writes to disk
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// ─── Schema ──────────────────────────────────────────────────────────────────
const DEFAULT_CONFIG = {
  logPath:          path.join(__dirname, 'audit.log'),
  workspaceRoot:    path.resolve(__dirname, '..'),
  whitelistedDomains: [
    'github.com',
    'api.github.com',
    'raw.githubusercontent.com',
  ],
  whitelistedCommandPrefixes: [
    'echo', 'date', 'git', 'agy-node', 'npm', 'node',
  ],
  maxLogFileSizeBytes: 10 * 1024 * 1024, // 10 MB rotation guard
};

// Windows device filenames that bypass path checks
const WINDOWS_DEVICE_NAMES = new Set([
  'CON','PRN','AUX','NUL','COM1','COM2','COM3','COM4',
  'COM5','COM6','COM7','COM8','COM9','LPT1','LPT2',
  'LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9',
]);

// Private / loopback IP ranges that must not receive agent-initiated connections
const PRIVATE_IP_PATTERNS = [
  /^127\./,                        // loopback
  /^10\./,                         // RFC 1918
  /^172\.(1[6-9]|2\d|3[01])\./,   // RFC 1918
  /^192\.168\./,                   // RFC 1918
  /^169\.254\./,                   // link-local
  /^::1$/,                         // IPv6 loopback
  /^fc[0-9a-f]{2}:/i,              // IPv6 ULA
  /^fe80:/i,                       // IPv6 link-local
];

// Interactive / privilege-escalation command tokens
const INTERACTIVE_COMMANDS = new Set([
  'sudo','su','passwd','ssh','telnet','ftp','sftp','scp',
  'powershell','cmd','bash','sh','zsh','fish',
  'net','attrib','reg','whoami','id','runas',
]);

// ─── SafeGateway Class ────────────────────────────────────────────────────────
class SafeGateway {
  /**
   * @param {Partial<typeof DEFAULT_CONFIG>} config
   */
  constructor(config = {}) {
    // Merge and freeze config — prevents runtime mutation
    this.config = Object.freeze({ ...DEFAULT_CONFIG, ...config });
    this.logPath      = this.config.logPath;
    this.workspaceRoot = path.resolve(this.config.workspaceRoot);

    // Compiled regex for secret patterns
    this.secretPatterns = {
      'GitHub Personal Access Token': /ghp_[a-zA-Z0-9]{36}/g,
      'GitHub OAuth Token':           /gho_[a-zA-Z0-9]{36}/g,
      'AWS Access Key ID':            /AKIA[0-9A-Z]{16}/g,
      'AWS Secret Access Key':        /(?<![A-Z0-9])[A-Za-z0-9\/+=]{40}(?![A-Z0-9])/g,
      'Stripe Live Secret Key':       /sk_live_[0-9a-zA-Z]{24,}/g,
      'Stripe Test Secret Key':       /sk_test_[0-9a-zA-Z]{24,}/g,
      'Generic Secret Assignment':    /(?:secret[_-]?key|api[_-]?secret|private[_-]?key)\s*[=:]\s*['"][a-zA-Z0-9_\-]{16,}['"]/gi,
      'OpenAI API Key':               /sk-[a-zA-Z0-9]{48}/g,
      'Anthropic API Key':            /sk-ant-[a-zA-Z0-9\-_]{90,}/g,
    };

    // Prompt injection signatures
    this.injectionPatterns = [
      /system\s*override/gi,
      /system\s*prompt\s*update/gi,
      /ignore\s+(?:all\s+)?previous\s+instructions/gi,
      /you\s+(?:must|shall|should)\s+now\s+(?:execute|run|perform)/gi,
      /disregard\s+(?:your\s+)?(?:rules|guidelines|policy)/gi,
      /\[INST\]|\[\/INST\]|<\|im_start\|>|<\|im_end\|>/g,   // model-level injection tokens
      /###\s*SYSTEM\s*PROMPT/gi,
    ];
  }

  // ── Logging ──────────────────────────────────────────────────────────────

  /**
   * Structured log write.
   * @param {'INFO'|'WARN'|'ALERT'|'ERROR'} level
   * @param {string} controlId   AI SAFE² control reference (e.g. 'P1.INJECT')
   * @param {string} category    Machine-readable event category
   * @param {string} message     Human-readable description
   * @param {object} [evidence]  Optional evidence payload
   */
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
      const line = JSON.stringify(entry) + '\n';
      fs.appendFileSync(this.logPath, line, 'utf8');
      // Human-readable console mirror
      console.log(`[GATEWAY-${level}] [${controlId}] [${category}] ${message}`);
    } catch (err) {
      // Logging must never crash the gateway — write to stderr and continue
      process.stderr.write(`[GATEWAY-LOG-ERROR] ${err.message}\n`);
    }
  }

  // ── Prompt / Content Sanitizer ───────────────────────────────────────────

  /**
   * Detect and neutralize Indirect Prompt Injection (IPI) attempts.
   * @param {string} content
   * @returns {{ sanitized: string, isFlagged: boolean, matches: string[] }}
   */
  sanitizeInput(content) {
    // FAIL CLOSED: if input is not a string, reject
    if (typeof content !== 'string') {
      this.logEvent('ALERT', 'P1.INJECT', 'INPUT_TYPE_VIOLATION',
        'Non-string input rejected by sanitizer', { inputType: typeof content });
      return { sanitized: '', isFlagged: true, matches: ['NON_STRING_INPUT'] };
    }

    let sanitized = content;
    const matches = [];

    for (const pattern of this.injectionPatterns) {
      // Reset lastIndex for global regexes
      pattern.lastIndex = 0;
      if (pattern.test(content)) {
        matches.push(pattern.source);
        this.logEvent('WARN', 'P1.INJECT', 'INJECTION_DETECTED',
          `IPI signature matched: ${pattern.source}`,
          { patternSource: pattern.source });
        pattern.lastIndex = 0;
        sanitized = sanitized.replace(pattern,
          `[NEUTRALIZED:${pattern.source.substring(0, 20)}]`);
      }
    }

    return { sanitized, isFlagged: matches.length > 0, matches };
  }

  // ── Action Verifier (main public API) ────────────────────────────────────

  /**
   * Central gate for all agent tool actions.
   * @param {string} action   Tool name
   * @param {string} payload  Action argument
   * @returns {{ authorized: boolean, message: string }}
   */
  verifyAction(action, payload) {
    try {
      this.logEvent('INFO', 'P4.AUDIT', 'ACTION_INTERCEPT',
        `Verifying action: ${action}`);

      switch (action) {
        case 'read_url_content':
          return this._verifyUrl(payload);
        case 'run_command':
          return this._verifyCommand(payload);
        case 'write_to_file':
        case 'replace_file_content':
        case 'multi_replace_file_content':
          return this._verifyFileWrite(payload);
        case 'view_file':
        case 'read_file':
          return this._verifyFileRead(payload);
        default:
          // Unknown actions: log and pass with warning
          this.logEvent('WARN', 'P4.AUDIT', 'UNKNOWN_ACTION',
            `Unknown action type passed through: ${action}`);
          return { authorized: true, message: `Unknown action '${action}' passed with warning.` };
      }
    } catch (err) {
      // FAIL CLOSED: any internal error denies the action
      this.logEvent('ERROR', 'P4.AUDIT', 'GATEWAY_INTERNAL_ERROR',
        `Gateway threw an internal error: ${err.message}. FAILING CLOSED.`,
        { stack: err.stack });
      return {
        authorized: false,
        message: `Gateway internal error — action denied (fail-closed). Error: ${err.message}`,
      };
    }
  }

  // ── URL Verifier ─────────────────────────────────────────────────────────

  _verifyUrl(urlStr) {
    if (typeof urlStr !== 'string' || urlStr.trim() === '') {
      return this._deny('P1.DOMAIN', 'MALFORMED_URL', 'Empty or non-string URL rejected.');
    }

    // Block non-http(s) schemes (file://, data://, ftp://, javascript:, etc.)
    const schemeLower = urlStr.trim().toLowerCase();
    if (!/^https?:\/\//i.test(schemeLower)) {
      return this._deny('P1.DOMAIN', 'FORBIDDEN_SCHEME',
        `Non-HTTP scheme blocked: ${urlStr.substring(0, 80)}`);
    }

    let urlObj;
    try {
      urlObj = new URL(urlStr);
    } catch {
      return this._deny('P1.DOMAIN', 'MALFORMED_URL', `URL parse failed: ${urlStr.substring(0, 80)}`);
    }

    const hostname = urlObj.hostname.toLowerCase();

    // Block private/loopback IPs — prevents SSRF to internal services
    for (const pattern of PRIVATE_IP_PATTERNS) {
      if (pattern.test(hostname)) {
        return this._deny('P1.DOMAIN', 'PRIVATE_IP_BLOCKED',
          `Blocked connection to private/loopback address: ${hostname}`);
      }
    }

    // Block numeric IPs altogether (not on whitelist by name)
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(hostname)) {
      return this._deny('P1.DOMAIN', 'RAW_IP_BLOCKED',
        `Raw IP address connections are not permitted: ${hostname}`);
    }

    // Domain-trick check: whitelisted domain must be the EXACT apex, not a suffix
    // e.g. "github.com.attacker.tld" must NOT match "github.com"
    const isWhitelisted = this.config.whitelistedDomains.some(domain => {
      const d = domain.toLowerCase();
      return hostname === d || hostname.endsWith('.' + d);
    });

    if (!isWhitelisted) {
      return this._deny('P4.EXFIL', 'EXFILTRATION_PREVENTED',
        `Unauthorized outbound connection blocked: ${hostname}`);
    }

    this.logEvent('INFO', 'P1.DOMAIN', 'URL_AUTHORIZED', `URL approved: ${hostname}`);
    return { authorized: true, message: `URL resolved to whitelisted domain: ${hostname}` };
  }

  // ── Command Verifier ─────────────────────────────────────────────────────

  _verifyCommand(command) {
    if (typeof command !== 'string' || command.trim() === '') {
      return this._deny('P1.CMD', 'EMPTY_COMMAND', 'Empty or non-string command rejected.');
    }

    // Block shell-chaining operators
    const chainOps = [';', '&&', '||', '|', '`', '$(', '>>', '> '];
    for (const op of chainOps) {
      if (command.includes(op)) {
        return this._deny('P1.CMD', 'COMMAND_CHAIN_BLOCKED',
          `Chained operator '${op}' blocked in: ${command.substring(0, 100)}`);
      }
    }

    // Block interactive / privilege-escalation binaries
    const firstToken = command.trim().split(/\s+/)[0].toLowerCase();
    // Strip Windows .exe/.cmd extensions
    const binaryName = firstToken.replace(/\.(exe|cmd|bat|ps1)$/i, '');

    if (INTERACTIVE_COMMANDS.has(binaryName)) {
      return this._deny('P1.CMD', 'INTERACTIVE_COMMAND_BLOCKED',
        `Interactive/admin command blocked: ${binaryName}`);
    }

    // Check against allowlist
    const isAllowed = this.config.whitelistedCommandPrefixes
      .some(prefix => binaryName === prefix.toLowerCase());

    if (!isAllowed) {
      return this._deny('P1.CMD', 'UNWHITELISTED_BINARY',
        `Binary '${binaryName}' is not on the command allowlist. Manual approval required.`);
    }

    this.logEvent('INFO', 'P1.CMD', 'COMMAND_AUTHORIZED', `Command approved: ${binaryName}`);
    return { authorized: true, message: `Command '${binaryName}' verified within allowlist.` };
  }

  // ── File Write Verifier ──────────────────────────────────────────────────

  _verifyFileWrite(content) {
    if (typeof content !== 'string') {
      return this._deny('P1.SECRET', 'INVALID_WRITE_CONTENT',
        'Non-string file content rejected.');
    }

    // Secret scan
    for (const [name, pattern] of Object.entries(this.secretPatterns)) {
      pattern.lastIndex = 0;
      if (pattern.test(content)) {
        return this._deny('P1.SECRET', 'CREDENTIAL_LEAK_BLOCKED',
          `Cleartext ${name} detected in write stream — blocked.`);
      }
    }

    this.logEvent('INFO', 'P1.SECRET', 'WRITE_CONTENT_CLEARED',
      'File write content passed secret hygiene scanner.');
    return { authorized: true, message: 'File content cleared secret-hygiene scanner.' };
  }

  // ── File Read Verifier ───────────────────────────────────────────────────

  /**
   * Checks path for traversal, symlink escape, and Windows device names.
   * @param {string} filePath
   */
  _verifyFileRead(filePath) {
    if (typeof filePath !== 'string' || filePath.trim() === '') {
      return this._deny('P1.PATH', 'EMPTY_PATH', 'Empty or non-string file path rejected.');
    }

    // Normalize path — resolves ../ and ./ sequences
    const resolved = path.resolve(filePath);

    // Detect path traversal: resolved path must stay inside workspace
    if (!resolved.startsWith(this.workspaceRoot + path.sep) &&
        resolved !== this.workspaceRoot) {
      return this._deny('P1.PATH', 'PATH_TRAVERSAL_BLOCKED',
        `Path '${filePath}' resolves outside workspace root: ${resolved}`);
    }

    // Detect Windows device path names
    const basename = path.basename(resolved).toUpperCase().split('.')[0];
    if (WINDOWS_DEVICE_NAMES.has(basename)) {
      return this._deny('P1.PATH', 'DEVICE_PATH_BLOCKED',
        `Windows device path blocked: ${basename}`);
    }

    // Detect encoded traversal sequences (e.g. %2e%2e, %252e)
    const raw = filePath.toLowerCase();
    if (raw.includes('%2e') || raw.includes('%252e') || raw.includes('%c0%af')) {
      return this._deny('P1.PATH', 'ENCODED_TRAVERSAL_BLOCKED',
        `Encoded path traversal sequence detected: ${filePath.substring(0, 80)}`);
    }

    // Symlink / junction check (best-effort — available when file exists)
    try {
      const stat = fs.lstatSync(resolved);
      if (stat.isSymbolicLink()) {
        return this._deny('P1.PATH', 'SYMLINK_ESCAPE_BLOCKED',
          `Symbolic link detected at path: ${resolved}`);
      }
    } catch {
      // File may not yet exist (pre-create check) — not a blocking error
    }

    this.logEvent('INFO', 'P1.PATH', 'FILE_PATH_AUTHORIZED',
      `File path approved within workspace: ${path.relative(this.workspaceRoot, resolved)}`);
    return { authorized: true, message: `Path verified within workspace bounds.` };
  }

  // ── Internal Helpers ─────────────────────────────────────────────────────

  _deny(controlId, category, message) {
    this.logEvent('ALERT', controlId, category, message);
    return {
      authorized: false,
      message: `[AI SAFE² POLICY VIOLATION] ${controlId}: ${message}`,
    };
  }
}

module.exports = SafeGateway;
