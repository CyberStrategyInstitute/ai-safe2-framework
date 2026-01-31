#!/usr/bin/env python3
"""
AI SAFE² Ishi Security Scanner v2.1
Scans Ishi desktop installations for security vulnerabilities

Supports: Windows, macOS, Linux
Usage:
    python ishi-scanner.py
    python ishi-scanner.py --path "C:\\Users\\user\\AppData\\Roaming\\ishi"
    python ishi-scanner.py --json > report.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Platform-specific imports
if sys.platform == 'win32':
    import winreg

# Color codes (Windows-compatible)
class Colors:
    if sys.platform == 'win32':
        # Use colorama on Windows if available
        try:
            import colorama
            colorama.init()
            RED = '\033[91m'
            YELLOW = '\033[93m'
            GREEN = '\033[92m'
            BLUE = '\033[94m'
            BOLD = '\033[1m'
            END = '\033[0m'
        except ImportError:
            # Fallback: no colors on Windows
            RED = YELLOW = GREEN = BLUE = BOLD = END = ''
    else:
        RED = '\033[91m'
        YELLOW = '\033[93m'
        GREEN = '\033[92m'
        BLUE = '\033[94m'
        BOLD = '\033[1m'
        END = '\033[0m'

class IshiScanner:
    def __init__(self, ishi_path: str = None):
        # Auto-detect Ishi path if not provided
        if ishi_path:
            self.path = Path(ishi_path)
        else:
            self.path = self._find_ishi_path()
        
        self.findings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        self.risk_score = 0
        
    def _find_ishi_path(self) -> Path:
        """Auto-detect Ishi installation path"""
        if sys.platform == 'win32':
            # Windows: %APPDATA%\ishi
            appdata = os.getenv('APPDATA')
            if appdata:
                return Path(appdata) / 'ishi'
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/ishi
            return Path.home() / 'Library' / 'Application Support' / 'ishi'
        else:
            # Linux: ~/.config/ishi
            return Path.home() / '.config' / 'ishi'
        
        return Path.home() / '.ishi'  # Fallback
    
    def scan(self) -> Dict:
        """Run all security checks"""
        print(f"{Colors.BOLD}AI SAFE² Ishi Security Scanner v2.1{Colors.END}")
        print(f"{'='*60}\n")
        print(f"Platform: {sys.platform}")
        print(f"Scanning: {self.path}\n")
        
        if not self.path.exists():
            print(f"{Colors.RED}ERROR: Ishi path not found: {self.path}{Colors.END}")
            print(f"\nTry specifying path manually:")
            print(f"  python ishi-scanner.py --path \"C:\\Users\\YourName\\AppData\\Roaming\\ishi\"")
            sys.exit(1)
        
        # Run all checks
        self._check_memory_protocol()
        self._check_permission_slider()
        self._check_ghost_file_config()
        self._check_token_tracking()
        self._check_credential_storage()
        self._check_file_permissions()
        self._check_logs_and_audit()
        self._check_undo_history()
        self._check_agenticflow_integration()
        self._check_openclaw_integration()
        
        # Calculate risk score
        self._calculate_risk_score()
        
        return self._generate_report()
    
    def _check_memory_protocol(self):
        """Check if AI SAFE² memory protocol is deployed"""
        print("[1/10] Checking AI SAFE² memory protocol...")
        
        memories_dir = self.path / 'memories'
        if not memories_dir.exists():
            self.findings['high'].append({
                'check': 'Memory Protocol',
                'issue': 'No memories directory found',
                'risk': 'Ishi has no persistent safety controls',
                'fix': f'Create: {memories_dir} and add ishi_memory.md'
            })
            return
        
        protocol_file = memories_dir / 'ishi_memory.md'
        if not protocol_file.exists():
            self.findings['high'].append({
                'check': 'Memory Protocol',
                'issue': 'AI SAFE² memory protocol not found',
                'risk': 'No persistent safety rules active',
                'fix': 'Download: https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/examples/ishi/ishi_memory.md'
            })
        else:
            # Check if it's the right version
            content = protocol_file.read_text(encoding='utf-8', errors='ignore')
            if 'Permission Slider' not in content or 'Token Budget' not in content:
                self.findings['medium'].append({
                    'check': 'Memory Protocol',
                    'issue': 'Outdated memory protocol detected',
                    'recommendation': 'Update to latest version (v2.1)'
                })
            else:
                self.findings['info'].append({
                    'check': 'Memory Protocol',
                    'status': 'AI SAFE² protocol active',
                    'version': '2.1'
                })
    
    def _check_permission_slider(self):
        """Check permission slider configuration"""
        print("[2/10] Checking permission slider...")
        
        config_file = self.path / 'config.json'
        if not config_file.exists():
            self.findings['medium'].append({
                'check': 'Permission Slider',
                'issue': 'No config file found',
                'recommendation': 'Run Ishi and configure permission slider'
            })
            return
        
        try:
            with open(config_file) as f:
                config = json.load(f)
            
            permission_level = config.get('permissions', {}).get('level', None)
            
            if permission_level is None:
                self.findings['medium'].append({
                    'check': 'Permission Slider',
                    'issue': 'Permission level not configured',
                    'fix': 'In Ishi: /config permissions'
                })
            elif permission_level == 3:
                self.findings['low'].append({
                    'check': 'Permission Slider',
                    'note': 'Running at Partner level (maximum autonomy)',
                    'recommendation': 'Consider Level 2 for better safety'
                })
            elif permission_level == 1:
                self.findings['info'].append({
                    'check': 'Permission Slider',
                    'status': 'Running at Intern level (maximum safety)',
                    'note': 'May be slower due to approval requirements'
                })
            else:
                self.findings['info'].append({
                    'check': 'Permission Slider',
                    'status': f'Level {permission_level} (Associate) - balanced'
                })
                
        except json.JSONDecodeError:
            self.findings['medium'].append({
                'check': 'Permission Slider',
                'issue': 'Config file corrupted',
                'fix': 'Reinstall Ishi or restore from backup'
            })
    
    def _check_ghost_file_config(self):
        """Check ghost file settings"""
        print("[3/10] Checking ghost file configuration...")
        
        config_file = self.path / 'config.json'
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                
                ghost_config = config.get('ghost_files', {})
                
                auto_commit = ghost_config.get('auto_commit', False)
                if auto_commit:
                    self.findings['critical'].append({
                        'check': 'Ghost Files',
                        'issue': 'Auto-commit enabled',
                        'risk': 'Files modified without preview/approval',
                        'fix': 'In Ishi: /config ghost_files → Disable auto-commit'
                    })
                
                preview_timeout = ghost_config.get('preview_timeout_seconds', 3600)
                if preview_timeout < 300:  # Less than 5 minutes
                    self.findings['medium'].append({
                        'check': 'Ghost Files',
                        'issue': f'Preview timeout very short ({preview_timeout}s)',
                        'recommendation': 'Increase to at least 300s (5 min)'
                    })
                
            except json.JSONDecodeError:
                pass
    
    def _check_token_tracking(self):
        """Check if token usage is being tracked"""
        print("[4/10] Checking token tracking...")
        
        token_file = self.path / 'token_usage.json'
        if not token_file.exists():
            self.findings['medium'].append({
                'check': 'Token Tracking',
                'issue': 'No token usage tracking found',
                'risk': 'May exceed free tier limits without warning',
                'recommendation': 'Enable token tracking in Ishi settings'
            })
        else:
            try:
                with open(token_file) as f:
                    usage = json.load(f)
                
                today = datetime.now().strftime('%Y-%m-%d')
                if usage.get('date') != today:
                    self.findings['low'].append({
                        'check': 'Token Tracking',
                        'note': 'Token usage file not updated today',
                        'recommendation': 'May need to reset daily counters'
                    })
                else:
                    # Check if approaching limits
                    for provider, data in usage.get('providers', {}).items():
                        percentage = data.get('percentage', 0)
                        if percentage > 90:
                            self.findings['high'].append({
                                'check': 'Token Tracking',
                                'issue': f'{provider} at {percentage}% of daily limit',
                                'recommendation': 'Switch providers or upgrade plan'
                            })
                        elif percentage > 75:
                            self.findings['medium'].append({
                                'check': 'Token Tracking',
                                'note': f'{provider} at {percentage}% of daily limit',
                                'recommendation': 'Monitor usage closely'
                            })
                    
                    if not usage.get('providers'):
                        self.findings['info'].append({
                            'check': 'Token Tracking',
                            'status': 'Active but no usage yet today'
                        })
                    else:
                        self.findings['info'].append({
                            'check': 'Token Tracking',
                            'status': 'Active and tracking usage'
                        })
                        
            except (json.JSONDecodeError, FileNotFoundError):
                self.findings['medium'].append({
                    'check': 'Token Tracking',
                    'issue': 'Token usage file corrupted',
                    'fix': 'Delete file and let Ishi recreate it'
                })
    
    def _check_credential_storage(self):
        """Check how credentials are stored"""
        print("[5/10] Checking credential storage...")
        
        # Check for plaintext credentials in config
        config_file = self.path / 'config.json'
        if config_file.exists():
            try:
                with open(config_file) as f:
                    content = f.read()
                
                # Look for API key patterns
                dangerous_patterns = [
                    ('sk-ant-', 'Anthropic API key'),
                    ('sk-', 'OpenAI API key'),
                    ('AIza', 'Google API key'),
                    ('"api_key":', 'API key field')
                ]
                
                for pattern, desc in dangerous_patterns:
                    if pattern in content and not '${' in content:
                        self.findings['high'].append({
                            'check': 'Credential Storage',
                            'issue': f'{desc} in plaintext config',
                            'risk': 'Credentials can be stolen if system compromised',
                            'fix': 'Use environment variables or system keychain'
                        })
                        
            except:
                pass
        
        # Check for encrypted credential store
        cred_file = self.path / 'credentials.json'
        if cred_file.exists():
            # Basic check if file looks encrypted
            try:
                with open(cred_file, 'rb') as f:
                    first_bytes = f.read(10)
                
                # If starts with '{' it's probably plaintext JSON
                if first_bytes.startswith(b'{'):
                    self.findings['critical'].append({
                        'check': 'Credential Storage',
                        'issue': 'Credentials stored in plaintext',
                        'risk': 'Complete credential exposure if stolen',
                        'fix': 'Enable encryption in Ishi settings'
                    })
                else:
                    self.findings['info'].append({
                        'check': 'Credential Storage',
                        'status': 'Credentials appear encrypted'
                    })
            except:
                pass
    
    def _check_file_permissions(self):
        """Check file/folder permissions"""
        print("[6/10] Checking file permissions...")
        
        if sys.platform != 'win32':
            # Unix-like systems
            import stat
            
            # Check Ishi directory permissions
            ishi_stat = self.path.stat()
            mode = oct(ishi_stat.st_mode)[-3:]
            
            if mode not in ['700', '755']:
                self.findings['medium'].append({
                    'check': 'File Permissions',
                    'issue': f'Ishi directory has permissions {mode}',
                    'recommendation': f'chmod 700 {self.path}',
                    'risk': 'Other users may access Ishi files'
                })
            
            # Check config file permissions
            config_file = self.path / 'config.json'
            if config_file.exists():
                config_stat = config_file.stat()
                config_mode = oct(config_stat.st_mode)[-3:]
                
                if config_mode != '600':
                    self.findings['high'].append({
                        'check': 'File Permissions',
                        'issue': f'Config file has permissions {config_mode}',
                        'fix': f'chmod 600 {config_file}',
                        'risk': 'Config may be readable by other users'
                    })
        else:
            # Windows: Check if folder is in user's AppData (which should be protected)
            if 'AppData' not in str(self.path):
                self.findings['medium'].append({
                    'check': 'File Permissions',
                    'note': 'Ishi not in AppData folder',
                    'recommendation': 'Consider reinstalling to standard location',
                    'info': 'AppData provides better user isolation'
                })
    
    def _check_logs_and_audit(self):
        """Check logging configuration"""
        print("[7/10] Checking logs and audit trail...")
        
        logs_dir = self.path / 'logs'
        if not logs_dir.exists():
            self.findings['medium'].append({
                'check': 'Logging',
                'issue': 'No logs directory found',
                'recommendation': 'Enable logging in Ishi settings'
            })
            return
        
        # Check for action log
        action_log = logs_dir / 'actions.jsonl'
        if not action_log.exists():
            self.findings['high'].append({
                'check': 'Logging',
                'issue': 'No action log found',
                'risk': 'No audit trail of Ishi operations',
                'fix': 'Enable action logging in settings'
            })
        else:
            # Check if log is recent
            import time
            last_modified = action_log.stat().st_mtime
            age_hours = (time.time() - last_modified) / 3600
            
            if age_hours > 168:  # 7 days
                self.findings['low'].append({
                    'check': 'Logging',
                    'note': f'Action log not updated in {int(age_hours/24)} days',
                    'info': 'May indicate Ishi not being used'
                })
            else:
                self.findings['info'].append({
                    'check': 'Logging',
                    'status': 'Action logging active'
                })
        
        # Check for violation log
        violation_log = self.path / 'violations.json'
        if violation_log.exists():
            try:
                with open(violation_log) as f:
                    violations = json.load(f)
                
                total = violations.get('total_violations', 0)
                if total > 10:
                    self.findings['medium'].append({
                        'check': 'Security Violations',
                        'issue': f'{total} safety rule violations detected',
                        'recommendation': 'Review violation log and adjust permissions',
                        'file': str(violation_log)
                    })
                elif total > 0:
                    self.findings['low'].append({
                        'check': 'Security Violations',
                        'note': f'{total} minor violations detected',
                        'info': 'Review to ensure settings are correct'
                    })
            except:
                pass
    
    def _check_undo_history(self):
        """Check undo/recovery capabilities"""
        print("[8/10] Checking undo history...")
        
        snapshots_dir = self.path / 'snapshots'
        trash_dir = self.path / 'trash'
        
        if not snapshots_dir.exists() and not trash_dir.exists():
            self.findings['medium'].append({
                'check': 'Undo History',
                'issue': 'No undo/recovery directories found',
                'risk': 'Cannot undo file operations',
                'recommendation': 'Enable undo in Ishi settings'
            })
        else:
            if snapshots_dir.exists():
                snapshot_count = len(list(snapshots_dir.glob('*.snapshot')))
                self.findings['info'].append({
                    'check': 'Undo History',
                    'status': f'{snapshot_count} snapshots available for undo'
                })
            
            if trash_dir.exists():
                trash_count = len(list(trash_dir.iterdir()))
                if trash_count > 100:
                    self.findings['low'].append({
                        'check': 'Undo History',
                        'note': f'{trash_count} items in trash',
                        'recommendation': 'Consider purging old items'
                    })
    
    def _check_agenticflow_integration(self):
        """Check AgenticFlow integration safety"""
        print("[9/10] Checking AgenticFlow integration...")
        
        config_file = self.path / 'config.json'
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                
                agenticflow = config.get('integrations', {}).get('agenticflow', {})
                
                if agenticflow.get('enabled', False):
                    # Check if workflow validation is enabled
                    if not agenticflow.get('validate_workflows', True):
                        self.findings['high'].append({
                            'check': 'AgenticFlow Integration',
                            'issue': 'Workflow validation disabled',
                            'risk': 'Dangerous workflows may execute unchecked',
                            'fix': 'Enable validate_workflows in config'
                        })
                    
                    # Check if auto-execute is disabled
                    if agenticflow.get('auto_execute', False):
                        self.findings['critical'].append({
                            'check': 'AgenticFlow Integration',
                            'issue': 'Auto-execute workflows enabled',
                            'risk': 'Workflows run without approval',
                            'fix': 'Disable auto_execute in config'
                        })
                    
                    self.findings['info'].append({
                        'check': 'AgenticFlow Integration',
                        'status': 'Enabled with safety checks'
                    })
                else:
                    self.findings['info'].append({
                        'check': 'AgenticFlow Integration',
                        'status': 'Not enabled'
                    })
                    
            except:
                pass
    
    def _check_openclaw_integration(self):
        """Check OpenClaw integration if present"""
        print("[10/10] Checking OpenClaw integration...")
        
        config_file = self.path / 'config.json'
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                
                openclaw = config.get('integrations', {}).get('openclaw', {})
                
                if openclaw.get('enabled', False):
                    # Check if delegation requires approval
                    if not openclaw.get('require_approval', True):
                        self.findings['high'].append({
                            'check': 'OpenClaw Integration',
                            'issue': 'Delegation without approval enabled',
                            'risk': 'Tasks sent to OpenClaw without user consent',
                            'fix': 'Enable require_approval in config'
                        })
                    
                    # Check if health checks are enabled
                    if not openclaw.get('health_check', True):
                        self.findings['medium'].append({
                            'check': 'OpenClaw Integration',
                            'issue': 'OpenClaw health checks disabled',
                            'recommendation': 'Enable to detect if OpenClaw is down'
                        })
                    
                    self.findings['info'].append({
                        'check': 'OpenClaw Integration',
                        'status': 'Enabled with delegation controls'
                    })
                else:
                    self.findings['info'].append({
                        'check': 'OpenClaw Integration',
                        'status': 'Not configured'
                    })
                    
            except:
                pass
    
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
            print("2. Deploy AI SAFE² memory protocol if missing")
            print("3. Enable token tracking to avoid free tier limits")
            print("4. Configure permission slider appropriately")
            print("5. Review all findings and implement recommendations")
            print()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'platform': sys.platform,
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
        description='AI SAFE² Ishi Security Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ishi-scanner.py
  python ishi-scanner.py --path "C:\\Users\\user\\AppData\\Roaming\\ishi"
  python ishi-scanner.py --json > report.json
  
For more information:
  https://github.com/CyberStrategyInstitute/ai-safe2-framework
        """
    )
    
    parser.add_argument(
        '--path',
        help='Path to Ishi directory (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output report as JSON'
    )
    
    parser.add_argument(
        '--output',
        help='Save report to file'
    )
    
    args = parser.parse_args()
    
    # Run scan
    scanner = IshiScanner(args.path)
    report = scanner.scan()
    
    # Handle output
    if args.json:
        print(json.dumps(report, indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            if args.json:
                json.dump(report, f, indent=2)
            else:
                f.write(f"AI SAFE² Ishi Security Scan Report\n")
                f.write(f"Generated: {report['timestamp']}\n")
                f.write(f"Platform: {report['platform']}\n")
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
