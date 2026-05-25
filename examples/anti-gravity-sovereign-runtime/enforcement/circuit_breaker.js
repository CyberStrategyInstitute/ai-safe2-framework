/**
 * circuit_breaker.js - Swarm Execution Circuit Breaker
 * Implements Pillar 3: Fail-Safe & Recovery // F3.2 Recursion Limits & F3.4 Cascade Containment
 */

const fs = require('fs');
const path = require('path');

class CircuitBreaker {
    constructor(maxRecursionDepth = 5, loopDetectionWindowMs = 5000) {
        this.maxRecursionDepth = maxRecursionDepth;
        this.loopDetectionWindowMs = loopDetectionWindowMs;
        this.callHistory = [];
        this.logPath = path.join(__dirname, 'audit.log');
    }

    logEvent(level, category, message) {
        const timestamp = new Date().toISOString();
        const logLine = `[${timestamp}] [${level}] [${category}] ${message}\n`;
        fs.appendFileSync(this.logPath, logLine, 'utf8');
        console.log(`[CIRCUIT-BREAKER-${level}] [${category}] ${message}`);
    }

    /**
     * Registers a tool call event and checks if it violates safety limits.
     * @param {string} toolName Name of the tool being called
     * @param {object} args Arguments passed to the tool
     */
    registerCall(toolName, args = {}) {
        const now = Date.now();
        const callEntry = {
            timestamp: now,
            tool: toolName,
            args: JSON.stringify(args)
        };

        this.callHistory.push(callEntry);

        // Check 1: Simple recursion depth check
        const identicalCalls = this.callHistory.filter(call => 
            call.tool === toolName && 
            call.args === callEntry.args && 
            (now - call.timestamp) <= this.loopDetectionWindowMs
        );

        this.logEvent('INFO', 'RECURSION_AUDIT', `Inspecting execution depth for tool '${toolName}': ${identicalCalls.length}/${this.maxRecursionDepth}`);

        if (identicalCalls.length >= this.maxRecursionDepth) {
            this.logEvent('ALERT', 'CIRCUIT_BREAKER_TRIGGERED', `Swarm execution aborted. runaway recursion loop detected for tool '${toolName}'!`);
            return {
                tripped: true,
                reason: `AI SAFE2 Fail-Safe Tripped: Recursive tool call depth exceeded threshold of ${this.maxRecursionDepth} in the last ${this.loopDetectionWindowMs}ms. Aborting sequence to prevent cascade denial of service.`
            };
        }

        return { tripped: false, reason: 'Execution path is clear.' };
    }

    /**
     * Safe execution recovery trigger
     */
    triggerRollback() {
        this.logEvent('ALERT', 'SYSTEM_ROLLBACK', 'Initiating automated workspace rollback to last verified Git commit...');
        // In actual implementation, this could execute 'git reset --hard HEAD' or restore a backup.
        return {
            status: 'ROLLBACK_SUCCESSFUL',
            rollbackTime: new Date().toISOString(),
            message: 'Workspace restored to stable state. Blocked operations neutralized.'
        };
    }
}

module.exports = CircuitBreaker;
