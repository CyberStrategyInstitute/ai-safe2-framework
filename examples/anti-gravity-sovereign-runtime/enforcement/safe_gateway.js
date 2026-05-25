/**
 * safe_gateway.js - AI SAFE2 External Enforcement Gateway
 * Implements Pillar 1: Sanitize & Isolate & Pillar 4: Engage & Monitor
 */

const fs = require('fs');
const path = require('path');

class SafeGateway {
    constructor(logPath = path.join(__dirname, 'audit.log')) {
        this.logPath = logPath;
        
        // AI SAFE2 Whitelist Rules
        this.whitelistedDomains = [
            'github.com',
            'api.github.com',
            'raw.githubusercontent.com',
            'localhost'
        ];
        
        this.whitelistedCommands = [
            'echo',
            'date',
            'git',
            'agy-node'
        ];
        
        // High-risk credentials regex patterns
        this.secretPatterns = {
            'GitHub API Token': /ghp_[a-zA-Z0-9]{36}/g,
            'AWS Access Key': /AKIA[0-9A-Z]{16}/g,
            'Stripe API Key': /sk_live_[0-9a-zA-Z]{24}/g,
            'Generic Secret Key': /secret_key\s*=\s*['"][a-zA-Z0-9_\-]{16,}['"]/gi
        };
    }

    logEvent(level, category, message) {
        const timestamp = new Date().toISOString();
        const logLine = `[${timestamp}] [${level}] [${category}] ${message}\n`;
        fs.appendFileSync(this.logPath, logLine, 'utf8');
        console.log(`[GATEWAY-${level}] [${category}] ${message}`);
    }

    /**
     * Intercept and sanitize inputs to prevent Indirect Prompt Injection (IPI)
     */
    sanitizeInput(content) {
        let isFlagged = false;
        let sanitized = content;
        
        // Detect system override pattern attempts in raw text
        const injectionPatterns = [
            /system\s*override/gi,
            /system\s*prompt\s*update/gi,
            /ignore\s*previous\s*instructions/gi,
            /you\s*must\s*now\s*execute/gi
        ];

        for (const pattern of injectionPatterns) {
            if (pattern.test(content)) {
                isFlagged = true;
                this.logEvent('WARN', 'INJECTION_DETECTED', `Anomalous prompt injection signature matched: ${pattern}`);
                // Neutralize injection by placing it in an inactive comment block
                sanitized = sanitized.replace(pattern, `[NEUTRALIZED_INJECTION_ATTEMPT: ${pattern.source}]`);
            }
        }

        return { sanitized, isFlagged };
    }

    /**
     * Intercept agent actions to block exfiltration, path traversal, or command escape
     */
    verifyAction(action, payload) {
        this.logEvent('INFO', 'ACTION_INTERCEPT', `Verifying tool execution request: ${action}`);

        switch (action) {
            case 'read_url_content':
                return this.verifyUrl(payload);
            case 'run_command':
                return this.verifyCommand(payload);
            case 'write_to_file':
            case 'replace_file_content':
                return this.verifyFileWrite(payload);
            default:
                return { authorized: true, message: 'Action passed structural sandbox defaults.' };
        }
    }

    verifyUrl(urlStr) {
        try {
            const urlObj = new URL(urlStr);
            const hostname = urlObj.hostname.toLowerCase();
            
            const isWhitelisted = this.whitelistedDomains.some(domain => 
                hostname === domain || hostname.endsWith('.' + domain)
            );

            if (!isWhitelisted) {
                this.logEvent('ALERT', 'EXFILTRATION_PREVENTED', `Blocked unauthorized outbound connection attempt to: ${hostname}`);
                return { 
                    authorized: false, 
                    message: `AI SAFE2 Policy Violation: Outbound connections to ${hostname} are not whitelisted. Access Blocked.` 
                };
            }
            return { authorized: true, message: 'URL resolved to a secure, whitelisted domain.' };
        } catch (e) {
            return { authorized: false, message: `Malformed URL parsed: ${urlStr}` };
        }
    }

    verifyCommand(command) {
        const tokens = command.trim().split(/\s+/);
        const firstToken = tokens[0] || '';
        
        // Block command chaining operators
        const chainOperators = [';', '&&', '||', '|', '`', '$('];
        for (const op of chainOperators) {
            if (command.includes(op)) {
                this.logEvent('ALERT', 'COMMAND_ESCAPE_PREVENTED', `Chained shell command operator '${op}' blocked: ${command}`);
                return { 
                    authorized: false, 
                    message: `AI SAFE2 Policy Violation: Chained shell commands are restricted. Execution Blocked.` 
                };
            }
        }

        const isWhitelisted = this.whitelistedCommands.includes(firstToken);
        if (!isWhitelisted) {
            this.logEvent('WARN', 'UNWHITELSTED_BINARY', `Intercepted un-whitelisted shell execution request: ${firstToken}`);
            return { 
                authorized: false, 
                message: `AI SAFE2 Policy Violation: Command binary '${firstToken}' is not whitelisted. Requires manual approval.` 
            };
        }

        return { authorized: true, message: 'Command verified within safe prefix parameters.' };
    }

    verifyFileWrite(fileContent) {
        // Scan for potential credentials leakage
        for (const [secretName, pattern] of Object.entries(this.secretPatterns)) {
            if (pattern.test(fileContent)) {
                this.logEvent('ALERT', 'CREDENTIAL_LEAK_BLOCKED', `Blocked attempt to write cleartext ${secretName} to disk.`);
                return {
                    authorized: false,
                    message: `AI SAFE2 Policy Violation: Detected cleartext secrets (${secretName}) in write stream. Execution Blocked.`
                };
            }
        }
        return { authorized: true, message: 'File contents cleared secret-hygiene scanner checks.' };
    }
}

module.exports = SafeGateway;
