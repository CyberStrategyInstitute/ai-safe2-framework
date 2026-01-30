#!/usr/bin/env python3
"""
AI SAFE² Moltbot Security Scanner v2.1
Audits Moltbot/Clawdbot installations for security vulnerabilities

Usage:
    python3 scanner.py --path ~/.clawdbot
    python3 scanner.py --path ~/.clawdbot --output report.txt
    python3 scanner.py --path ~/.clawdbot --json
"""

import os
import sys
import json
import argparse
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class MoltbotScanner:
    def __init__(self, clawdbot_path: str):
        self.path = Path(clawdbot_path).expanduser()
        self.findings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        self.risk_score = 0
        
    def scan(self) -> Dict:
        """Run all security checks"""
        print(f"{Colors.BOLD}AI SAFE² Moltbot Security Scanner v2.1{Colors.END}")
        print(f"{'='*60}\n")
        print(f"Scanning: {self.path}\n")
        
        if not self.path.exists():
            print(f"{Colors.RED}ERROR: Path not found: {self.path}{Colors.END}")
            sys.exit(1)
            
        # Run all checks
        self._check_network_exposure()
        self._check_file_permissions()
        self._check_configuration()
        self._check_tool_permissions()
        self._check_logging_config()
        self._check_secrets_management()
        self._check_authentication()
        self._check_audit_logs()
        self._check_memory_files()
        
        # Calculate risk score
        self._calculate_risk_score()
        
        return self._generate_report()
    
    def _check_network_exposure(self):
        """Check if gateway is exposed on public internet"""
        print("[1/9] Checking network exposure...")
        
        # Check for running clawdbot processes
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            if 'clawdbot gateway' in result.stdout or 'moltbot gateway' in result.stdout:
                # Check netstat for listening ports
                netstat = subprocess.run(
                    ['netstat', '-tuln'],
                    capture_output=True,
                    text=True
                )
                
                for line in netstat.stdout.split('\n'):
                    if '0.0.0.0:' in line and ('8080' in line or '18789' in line or '8888' in line):
                        self.findings['critical'].append({
                            'check': 'Network Exposure',
                            'issue': 'Gateway bound to 0.0.0.0 (public internet exposed)',
                            'detail': line.strip(),
                            'risk': 'Allows anyone on internet to access your bot',
                            'fix': 'Stop gateway and restart with: clawdbot gateway --bind 127.0.0.1'
                        })
                        
                if '127.0.0.1:' in netstat.stdout:
                    self.findings['info'].append({
                        'check': 'Network Exposure',
                        'status': 'Gateway correctly bound to localhost',
                        'detail': 'Only accessible via SSH tunnel or local machine'
                    })
                        
        except Exception as e:
            self.findings['info'].append({
                'check': 'Network Exposure',
                'note': f'Could not check running processes: {e}'
            })
    
    def _check_file_permissions(self):
        """Check file and directory permissions"""
        print("[2/9] Checking file permissions...")
        
        critical_files = [
            'clawdbot.json',
            'config.toml',
            'config.yaml',
            '.env'
        ]
        
        for file in critical_files:
            filepath = self.path / file
            if filepath.exists():
                stat = filepath.stat()
                mode = oct(stat.st_mode)[-3:]
                
                if mode != '600':
                    severity = 'high' if mode in ['644', '666'] else 'medium'
                    self.findings[severity].append({
                        'check': 'File Permissions',
                        'issue': f'{file} has overly permissive permissions ({mode})',
                        'risk': 'Secrets and configs may be readable by other users',
                        'fix': f'chmod 600 {filepath}'
                    })
        
        # Check directory permissions
        dir_stat = self.path.stat()
        dir_mode = oct(dir_stat.st_mode)[-3:]
        
        if dir_mode not in ['700', '750']:
            self.findings['medium'].append({
                'check': 'Directory Permissions',
                'issue': f'~/.clawdbot has permissions {dir_mode}',
                'risk': 'Directory contents may be listable by others',
                'fix': f'chmod 700 {self.path}'
            })
    
    def _check_configuration(self):
        """Check configuration files for security issues"""
        print("[3/9] Checking configuration...")
        
        config_files = ['clawdbot.json', 'config.toml', 'config.yaml']
        
        for config_file in config_files:
            config_path = self.path / config_file
            if config_path.exists():
                content = config_path.read_text()
                
                # Check for hardcoded secrets
                secret_patterns = [
                    ('sk-ant-', 'Anthropic API key'),
                    ('sk-', 'OpenAI API key'),
                    ('ghp_', 'GitHub token'),
                    ('xoxb-', 'Slack token'),
                    ('AKIA', 'AWS access key')
                ]
                
                for pattern, desc in secret_patterns:
                    if pattern in content:
                        self.findings['critical'].append({
                            'check': 'Configuration Security',
                            'issue': f'{desc} hardcoded in {config_file}',
                            'risk': 'Secrets stored in plaintext, vulnerable to theft',
                            'fix': 'Move to environment variables or OS keychain'
                        })
    
    def _check_tool_permissions(self):
        """Check which tools are enabled"""
        print("[4/9] Checking tool permissions...")
        
        # This is a simplified check - actual implementation would parse config
        config_path = self.path / 'clawdbot.json'
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                
                # Check for high-risk tools
                high_risk_tools = ['exec', 'process', 'browser', 'cron', 'gateway']
                
                if 'tools' in config:
                    enabled_tools = config.get('tools', {})
                    
                    for tool in high_risk_tools:
                        if enabled_tools.get(tool, {}).get('enabled', False):
                            self.findings['high'].append({
                                'check': 'Tool Permissions',
                                'issue': f'High-risk tool enabled: {tool}',
                                'risk': 'Tool can perform destructive or privileged operations',
                                'recommendation': 'Enable only if absolutely necessary, use sandbox mode'
                            })
                            
            except json.JSONDecodeError:
                self.findings['medium'].append({
                    'check': 'Tool Permissions',
                    'issue': 'Could not parse clawdbot.json',
                    'fix': 'Verify config file syntax'
                })
    
    def _check_logging_config(self):
        """Check logging configuration"""
        print("[5/9] Checking logging configuration...")
        
        config_path = self.path / 'clawdbot.json'
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                
                logging_config = config.get('logging', {})
                
                redact = logging_config.get('redactSensitive', 'off')
                if redact != 'all':
                    self.findings['high'].append({
                        'check': 'Logging Security',
                        'issue': f'Log redaction set to "{redact}" (should be "all")',
                        'risk': 'API keys and secrets will leak to log files',
                        'fix': 'Set "redactSensitive": "all" in clawdbot.json'
                    })
                else:
                    self.findings['info'].append({
                        'check': 'Logging Security',
                        'status': 'Log redaction properly configured'
                    })
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    def _check_secrets_management(self):
        """Check how secrets are managed"""
        print("[6/9] Checking secrets management...")
        
        # Check for .env files
        env_file = self.path / '.env'
        if env_file.exists():
            stat = env_file.stat()
            mode = oct(stat.st_mode)[-3:]
            
            if mode != '600':
                self.findings['critical'].append({
                    'check': 'Secrets Management',
                    'issue': f'.env file has permissions {mode}',
                    'risk': 'Environment secrets readable by other users',
                    'fix': f'chmod 600 {env_file}'
                })
            
            # Check for secrets in .env
            content = env_file.read_text()
            if any(key in content for key in ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
                self.findings['medium'].append({
                    'check': 'Secrets Management',
                    'issue': 'Secrets stored in .env file',
                    'recommendation': 'Consider using OS keychain or vault',
                    'info': 'Current approach is acceptable if .env has chmod 600'
                })
    
    def _check_authentication(self):
        """Check authentication configuration"""
        print("[7/9] Checking authentication...")
        
        config_path = self.path / 'clawdbot.json'
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                
                auth_config = config.get('authentication', {})
                
                if not auth_config:
                    self.findings['critical'].append({
                        'check': 'Authentication',
                        'issue': 'No authentication configured',
                        'risk': 'Anyone with network access can control bot',
                        'fix': 'Enable SSO, MFA, or at minimum password authentication'
                    })
                elif auth_config.get('mode') == 'password':
                    self.findings['medium'].append({
                        'check': 'Authentication',
                        'issue': 'Using password-only authentication',
                        'recommendation': 'Upgrade to SSO or MFA for better security'
                    })
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    def _check_audit_logs(self):
        """Check if audit logging is enabled and working"""
        print("[8/9] Checking audit logs...")
        
        logs_dir = self.path / 'logs'
        if not logs_dir.exists():
            self.findings['high'].append({
                'check': 'Audit Logging',
                'issue': 'No logs directory found',
                'risk': 'No audit trail of bot actions',
                'fix': 'Enable logging in configuration'
            })
            return
        
        # Check for recent logs
        audit_log = logs_dir / 'audit.log'
        gateway_log = logs_dir / 'gateway.log'
        
        if audit_log.exists():
            stat = audit_log.stat()
            age_days = (datetime.now().timestamp() - stat.st_mtime) / 86400
            
            if age_days > 7:
                self.findings['medium'].append({
                    'check': 'Audit Logging',
                    'issue': f'Audit log not updated in {int(age_days)} days',
                    'risk': 'Logging may be disabled or bot not running',
                    'fix': 'Verify logging is enabled and bot is operational'
                })
            else:
                self.findings['info'].append({
                    'check': 'Audit Logging',
                    'status': 'Audit logs active and recent'
                })
        else:
            self.findings['high'].append({
                'check': 'Audit Logging',
                'issue': 'No audit.log file found',
                'risk': 'Actions not being logged',
                'fix': 'Enable audit logging in configuration'
            })
    
    def _check_memory_files(self):
        """Check for AI SAFE² memory protocol"""
        print("[9/9] Checking AI SAFE² memory protocol...")
        
        memories_dir = self.path / 'memories'
        if memories_dir.exists():
            memory_files = list(memories_dir.glob('*.md'))
            
            aisafe2_found = False
            for mem_file in memory_files:
                content = mem_file.read_text()
                if 'AI SAFE²' in content or 'ABSOLUTE SAFETY RULES' in content:
                    aisafe2_found = True
                    self.findings['info'].append({
                        'check': 'AI SAFE² Protocol',
                        'status': f'Memory protocol found: {mem_file.name}',
                        'info': 'Bot has persistent safety controls active'
                    })
                    break
            
            if not aisafe2_found:
                self.findings['medium'].append({
                    'check': 'AI SAFE² Protocol',
                    'issue': 'No AI SAFE² memory protocol found',
                    'recommendation': 'Add moltbot_memory.md to memories/ directory',
                    'benefit': 'Embeds persistent safety controls in bot context',
                    'link': 'https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/examples/moltbot/moltbot_memory.md'
                })
        else:
            self.findings['info'].append({
                'check': 'AI SAFE² Protocol',
                'note': 'No memories directory found (may not be using this feature)'
            })
    
    def _calculate_risk_score(self):
        """Calculate overall risk score (0-100)"""
        weights = {
            'critical': 25,
            'high': 10,
            'medium': 5,
            'low': 2
        }
        
        score = 0
        for severity, weight in weights.items():
            score += len(self.findings[severity]) * weight
        
        # Cap at 100
        self.risk_score = min(score, 100)
    
    def _generate_report(self) -> Dict:
        """Generate final report"""
        print(f"\n{'='*60}")
        print(f"{Colors.BOLD}SCAN COMPLETE{Colors.END}\n")
        
        # Print findings by severity
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        severity_colors = {
            'critical': Colors.RED,
            'high': Colors.YELLOW,
            'medium': Colors.YELLOW,
            'low': Colors.BLUE,
            'info': Colors.GREEN
        }
        
        for severity in severity_order:
            findings = self.findings[severity]
            if not findings:
                continue
                
            color = severity_colors[severity]
            label = severity.upper()
            
            print(f"{color}{Colors.BOLD}{label} ({len(findings)}){Colors.END}")
            print(f"{color}{'─'*60}{Colors.END}\n")
            
            for i, finding in enumerate(findings, 1):
                if severity == 'info':
                    print(f"  ✓ {finding.get('check')}: {finding.get('status', finding.get('note', ''))}")
                else:
                    print(f"  [{i}] {finding.get('check')}")
                    print(f"      Issue: {finding.get('issue')}")
                    if 'risk' in finding:
                        print(f"      Risk: {finding['risk']}")
                    if 'fix' in finding:
                        print(f"      Fix: {finding['fix']}")
                    if 'recommendation' in finding:
                        print(f"      Recommendation: {finding['recommendation']}")
                print()
        
        # Risk score with color coding
        if self.risk_score >= 70:
            score_color = Colors.RED
            rating = "CRITICAL RISK"
        elif self.risk_score >= 40:
            score_color = Colors.YELLOW
            rating = "HIGH RISK"
        elif self.risk_score >= 20:
            score_color = Colors.YELLOW
            rating = "MEDIUM RISK"
        else:
            score_color = Colors.GREEN
            rating = "LOW RISK"
        
        print(f"{'='*60}")
        print(f"{Colors.BOLD}OVERALL RISK SCORE: {score_color}{self.risk_score}/100{Colors.END} {Colors.BOLD}({rating}){Colors.END}")
        print(f"{'='*60}\n")
        
        # Recommendations
        if self.risk_score > 0:
            print(f"{Colors.BOLD}NEXT STEPS:{Colors.END}\n")
            print("1. Fix CRITICAL and HIGH issues immediately")
            print("2. Review MEDIUM issues and remediate within 1 week")
            print("3. Run scanner again after fixes: python3 scanner.py --path ~/.clawdbot")
            print("4. Deploy AI SAFE² control gateway for continuous protection")
            print("5. Review hardening guide: https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/guides/moltbot-hardening.md")
            print()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'path': str(self.path),
            'risk_score': self.risk_score,
            'findings': self.findings,
            'summary': {
                'critical': len(self.findings['critical']),
                'high': len(self.findings['high']),
                'medium': len(self.findings['medium']),
                'low': len(self.findings['low'])
            }
        }

def main():
    parser = argparse.ArgumentParser(
        description='AI SAFE² Moltbot Security Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scanner.py --path ~/.clawdbot
  python3 scanner.py --path ~/.clawdbot --output report.txt
  python3 scanner.py --path ~/.clawdbot --json > report.json
  
For more information:
  https://github.com/CyberStrategyInstitute/ai-safe2-framework
        """
    )
    
    parser.add_argument(
        '--path',
        required=True,
        help='Path to Clawdbot/Moltbot directory (e.g., ~/.clawdbot)'
    )
    
    parser.add_argument(
        '--output',
        help='Save report to file'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output report as JSON'
    )
    
    args = parser.parse_args()
    
    # Run scan
    scanner = MoltbotScanner(args.path)
    report = scanner.scan()
    
    # Handle output
    if args.json:
        print(json.dumps(report, indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            if args.json:
                json.dump(report, f, indent=2)
            else:
                # Write text report
                f.write(f"AI SAFE² Moltbot Security Scan Report\n")
                f.write(f"Generated: {report['timestamp']}\n")
                f.write(f"Path: {report['path']}\n")
                f.write(f"Risk Score: {report['risk_score']}/100\n\n")
                
                for severity in ['critical', 'high', 'medium', 'low']:
                    findings = report['findings'][severity]
                    if findings:
                        f.write(f"\n{severity.upper()} ({len(findings)}):\n")
                        f.write("="*60 + "\n")
                        for finding in findings:
                            f.write(f"\n{finding.get('check')}\n")
                            f.write(f"  Issue: {finding.get('issue')}\n")
                            if 'risk' in finding:
                                f.write(f"  Risk: {finding['risk']}\n")
                            if 'fix' in finding:
                                f.write(f"  Fix: {finding['fix']}\n")
        
        print(f"\nReport saved to: {args.output}")
    
    # Exit code based on risk
    if scanner.risk_score >= 70:
        sys.exit(2)  # Critical
    elif scanner.risk_score >= 40:
        sys.exit(1)  # High/Medium
    else:
        sys.exit(0)  # Low/Clean

if __name__ == '__main__':
    main()
