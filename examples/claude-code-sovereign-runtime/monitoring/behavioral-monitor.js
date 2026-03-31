#!/usr/bin/env node
// =============================================================================
// AI SAFE2 -- External Behavioral Monitor
// Pillar 4: Engage & Monitor
// Framework: AI SAFE2 / AISM Level 4
// =============================================================================
// Watches Claude Code log files in real time and builds behavioral analytics
// EXTERNAL to the Claude Code process -- the agent cannot influence this.
//
// Features:
//   - Real-time anomaly detection based on baseline thresholds
//   - Session summary reporting
//   - Alert escalation (console, file, optional webhook)
//   - Tool call rate tracking
//   - Secret detection alert aggregation
//
// Usage:
//   node monitoring/behavioral-monitor.js [--watch] [--report] [--baseline]
//   node monitoring/behavioral-monitor.js --watch   # live monitoring
//   node monitoring/behavioral-monitor.js --report  # session summary
// =============================================================================

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const os = require('os');

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const CONFIG = {
  logDir: process.env.CLAUDE_CODE_LOG_DIR || path.join(os.homedir(), '.claude', 'logs'),
  siemEndpoint: process.env.CLAUDE_CODE_SIEM_ENDPOINT || null,
  alertWebhook: process.env.CLAUDE_CODE_ALERT_WEBHOOK || null,

  // Anomaly thresholds (tune for your environment)
  thresholds: {
    maxToolCallsPerMinute: 30,         // >30 tool calls/min is unusual
    maxBashCallsPerSession: 100,        // >100 bash calls may indicate runaway agent
    maxFileWritesPerSession: 50,        // >50 writes is unusual
    maxSubagentsPerSession: 10,         // >10 subagents spawned is unusual
    maxExternalFetchesPerSession: 20,   // >20 web fetches is unusual
    alertOnAnySecret: true,             // Always alert on secret detection
    alertOnAnyBlock: true,              // Always alert on hook block
  }
};

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const sessionState = {
  startTime: Date.now(),
  toolCalls: [],          // timestamps
  bashCalls: 0,
  fileWrites: 0,
  subagents: 0,
  externalFetches: 0,
  blockedOps: 0,
  secretsDetected: [],
  anomalies: [],
};

// ---------------------------------------------------------------------------
// Log parsers
// ---------------------------------------------------------------------------
function parsePreToolUseLine(line) {
  const ts = line.match(/^([^|]+)\|/)?.[1]?.trim();
  const tool = line.match(/tool=([^\s|]+)/)?.[1];
  const type = line.includes('BLOCKED') ? 'block' :
               line.includes('ALLOWED') ? 'allow' : null;
  const reason = line.match(/reason=([^|]+)/)?.[1]?.trim();
  return { ts, tool, type, reason };
}

function parsePostToolUseLine(line) {
  const tool = line.match(/tool=([^\s|]+)/)?.[1];
  const type = line.includes('SECRET_DETECTED') ? 'secret' :
               line.includes('SUBAGENT_SPAWNED') ? 'subagent' :
               line.includes('EXTERNAL_FETCH') ? 'fetch' :
               line.includes('FILE_MODIFIED') ? 'write' : 'other';
  const secretType = line.match(/type=([^\s|]+)/)?.[1];
  const url = line.match(/url=([^\s|]+)/)?.[1];
  return { tool, type, secretType, url };
}

// ---------------------------------------------------------------------------
// Anomaly detection
// ---------------------------------------------------------------------------
function checkAnomalies() {
  const now = Date.now();
  const oneMinuteAgo = now - 60_000;
  const t = CONFIG.thresholds;
  const anomalies = [];

  // Tool call rate
  const recentCalls = sessionState.toolCalls.filter(ts => ts > oneMinuteAgo).length;
  if (recentCalls > t.maxToolCallsPerMinute) {
    anomalies.push(`HIGH_TOOL_RATE: ${recentCalls} tool calls in last minute (threshold: ${t.maxToolCallsPerMinute})`);
  }

  // Absolute counts
  if (sessionState.bashCalls > t.maxBashCallsPerSession)
    anomalies.push(`HIGH_BASH_COUNT: ${sessionState.bashCalls} bash calls (threshold: ${t.maxBashCallsPerSession})`);
  if (sessionState.fileWrites > t.maxFileWritesPerSession)
    anomalies.push(`HIGH_WRITE_COUNT: ${sessionState.fileWrites} file writes (threshold: ${t.maxFileWritesPerSession})`);
  if (sessionState.subagents > t.maxSubagentsPerSession)
    anomalies.push(`HIGH_SUBAGENT_COUNT: ${sessionState.subagents} subagents (threshold: ${t.maxSubagentsPerSession})`);
  if (sessionState.externalFetches > t.maxExternalFetchesPerSession)
    anomalies.push(`HIGH_FETCH_COUNT: ${sessionState.externalFetches} external fetches (threshold: ${t.maxExternalFetchesPerSession})`);

  return anomalies;
}

// ---------------------------------------------------------------------------
// Alert dispatch
// ---------------------------------------------------------------------------
async function sendAlert(type, message, details = {}) {
  const alert = {
    timestamp: new Date().toISOString(),
    type,
    message,
    details,
    host: os.hostname(),
    user: os.userInfo().username,
  };

  // Always print to console
  console.error(`\n[AI SAFE2 ALERT] ${alert.timestamp}`);
  console.error(`Type: ${type}`);
  console.error(`Message: ${message}`);
  if (Object.keys(details).length > 0) {
    console.error('Details:', JSON.stringify(details, null, 2));
  }
  console.error('');

  // Log to file
  const alertFile = path.join(CONFIG.logDir, 'monitor-alerts.log');
  fs.appendFileSync(alertFile, JSON.stringify(alert) + '\n');

  // Optional: send to webhook (Slack, PagerDuty, etc.)
  if (CONFIG.alertWebhook) {
    try {
      const { default: fetch } = await import('node-fetch').catch(() => ({ default: null }));
      if (fetch) {
        await fetch(CONFIG.alertWebhook, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: `*[AI SAFE2 Alert]* ${type}: ${message}`,
            attachments: [{ text: JSON.stringify(details, null, 2) }]
          })
        });
      }
    } catch (e) {
      // Webhook failure is not critical -- continue monitoring
    }
  }
}

// ---------------------------------------------------------------------------
// Log watchers
// ---------------------------------------------------------------------------
function watchLogFile(filename, parser, handler) {
  const filepath = path.join(CONFIG.logDir, filename);

  // Process existing content first
  if (fs.existsSync(filepath)) {
    const content = fs.readFileSync(filepath, 'utf8');
    content.split('\n').filter(Boolean).forEach(line => {
      handler(parser(line), line);
    });
  }

  // Watch for new lines
  let fileSize = fs.existsSync(filepath) ? fs.statSync(filepath).size : 0;

  fs.watch(path.dirname(filepath), { persistent: true }, (event, changedFile) => {
    if (changedFile !== filename) return;
    if (!fs.existsSync(filepath)) return;

    const newSize = fs.statSync(filepath).size;
    if (newSize <= fileSize) return;

    // Read new content
    const fd = fs.openSync(filepath, 'r');
    const buffer = Buffer.alloc(newSize - fileSize);
    fs.readSync(fd, buffer, 0, buffer.length, fileSize);
    fs.closeSync(fd);
    fileSize = newSize;

    buffer.toString('utf8').split('\n').filter(Boolean).forEach(line => {
      handler(parser(line), line);
    });
  });
}

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------
function handlePreToolEvent(parsed) {
  if (!parsed.type) return;

  sessionState.toolCalls.push(Date.now());

  if (parsed.type === 'block') {
    sessionState.blockedOps++;
    if (CONFIG.thresholds.alertOnAnyBlock) {
      sendAlert('TOOL_BLOCKED', `Claude Code tool use blocked: ${parsed.tool}`, {
        tool: parsed.tool,
        reason: parsed.reason
      });
    }
  }

  if (parsed.tool === 'Bash') sessionState.bashCalls++;

  // Check anomalies after every tool call
  const anomalies = checkAnomalies();
  anomalies.forEach(anomaly => {
    if (!sessionState.anomalies.includes(anomaly)) {
      sessionState.anomalies.push(anomaly);
      sendAlert('ANOMALY_DETECTED', anomaly, {
        sessionStats: {
          bashCalls: sessionState.bashCalls,
          fileWrites: sessionState.fileWrites,
          subagents: sessionState.subagents,
          toolCallRate: sessionState.toolCalls.filter(ts => ts > Date.now() - 60_000).length
        }
      });
    }
  });
}

function handlePostToolEvent(parsed) {
  if (!parsed.type) return;

  switch (parsed.type) {
    case 'secret':
      sessionState.secretsDetected.push(parsed.secretType);
      sendAlert('SECRET_DETECTED', `Potential ${parsed.secretType} in Claude Code tool output`, {
        secretType: parsed.secretType,
        tool: parsed.tool,
        action: 'Review output immediately and rotate if confirmed'
      });
      break;
    case 'subagent':
      sessionState.subagents++;
      break;
    case 'fetch':
      sessionState.externalFetches++;
      break;
    case 'write':
      sessionState.fileWrites++;
      break;
  }
}

// ---------------------------------------------------------------------------
// Session report
// ---------------------------------------------------------------------------
function printSessionReport() {
  const durationMs = Date.now() - sessionState.startTime;
  const durationMin = (durationMs / 60_000).toFixed(1);

  console.log('\n================================================================');
  console.log('AI SAFE2 Session Behavioral Report');
  console.log(`Generated: ${new Date().toISOString()}`);
  console.log(`Duration: ${durationMin} minutes`);
  console.log('================================================================');
  console.log(`Tool calls (total):     ${sessionState.toolCalls.length}`);
  console.log(`Bash commands:          ${sessionState.bashCalls}`);
  console.log(`File writes:            ${sessionState.fileWrites}`);
  console.log(`External fetches:       ${sessionState.externalFetches}`);
  console.log(`Subagents spawned:      ${sessionState.subagents}`);
  console.log(`Operations blocked:     ${sessionState.blockedOps}`);
  console.log(`Secrets detected:       ${sessionState.secretsDetected.length}`);
  if (sessionState.secretsDetected.length > 0) {
    console.log(`Secret types:           ${sessionState.secretsDetected.join(', ')}`);
  }
  console.log(`Anomalies triggered:    ${sessionState.anomalies.length}`);
  if (sessionState.anomalies.length > 0) {
    sessionState.anomalies.forEach(a => console.log(`  - ${a}`));
  }
  console.log('================================================================\n');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);

if (!fs.existsSync(CONFIG.logDir)) {
  fs.mkdirSync(CONFIG.logDir, { recursive: true });
}

console.log(`AI SAFE2 Behavioral Monitor starting...`);
console.log(`Log directory: ${CONFIG.logDir}`);
console.log(`SIEM endpoint: ${CONFIG.siemEndpoint || 'none'}`);
console.log(`Alert webhook: ${CONFIG.alertWebhook || 'none'}`);
console.log('');

if (args.includes('--report')) {
  // One-shot report from existing logs
  watchLogFile('pre-tool-use.log', parsePreToolUseLine, (p) => handlePreToolEvent(p));
  watchLogFile('post-tool-use.log', parsePostToolUseLine, (p) => handlePostToolEvent(p));
  setTimeout(() => { printSessionReport(); process.exit(0); }, 500);
} else {
  // Live monitoring mode
  console.log('Watching for Claude Code activity (Ctrl+C to stop)...\n');
  watchLogFile('pre-tool-use.log', parsePreToolUseLine, (p) => handlePreToolEvent(p));
  watchLogFile('post-tool-use.log', parsePostToolUseLine, (p) => handlePostToolEvent(p));

  // Print report on exit
  process.on('SIGINT', () => { printSessionReport(); process.exit(0); });
  process.on('SIGTERM', () => { printSessionReport(); process.exit(0); });

  // Periodic status (every 5 minutes)
  setInterval(() => {
    const anomalies = checkAnomalies();
    if (anomalies.length > 0) {
      anomalies.forEach(a => sendAlert('ANOMALY_PERIODIC_CHECK', a));
    }
  }, 5 * 60 * 1000);
}
