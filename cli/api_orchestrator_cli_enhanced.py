#!/usr/bin/env python3
"""
API Orchestrator CLI - Enhanced Newman-equivalent for CI/CD
The POSTMAN KILLER CLI with advanced features
"""

import click
import json
import sys
import os
import asyncio
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, List
from tabulate import tabulate
from colorama import init, Fore, Style
import yaml
import time
from datetime import datetime
import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import tempfile
import subprocess

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.agents.test_runner_agent import TestRunnerAgent, TestCase, TestSuite, Assertion, AssertionType
from backend.src.postman_import import PostmanImporter

class CLIConfig:
    """Enhanced CLI Configuration"""
    def __init__(self):
        self.api_url = os.getenv('API_ORCHESTRATOR_URL', 'http://localhost:8000')
        self.api_key = os.getenv('API_ORCHESTRATOR_KEY', '')
        self.output_format = 'text'
        self.verbose = False
        self.color = True
        self.insecure = False
        self.reporters = []
        self.working_dir = os.getcwd()
        self.global_vars = {}
        self.collection_vars = {}
        
# Global config
config = CLIConfig()

class DataFileIterator:
    """Handle data-driven testing with CSV/JSON files"""
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data = []
        self._load_data()
    
    def _load_data(self):
        """Load data from CSV or JSON file"""
        if self.data_file.endswith('.csv'):
            with open(self.data_file, 'r') as f:
                reader = csv.DictReader(f)
                self.data = list(reader)
        elif self.data_file.endswith('.json'):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
                if not isinstance(self.data, list):
                    self.data = [self.data]
        else:
            raise ValueError(f"Unsupported data file format: {self.data_file}")
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)

class ParallelRunner:
    """Run collections in parallel for better performance"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.results = []
    
    async def run_parallel(self, test_suites: List[TestSuite], environment: Dict = None):
        """Run multiple test suites in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for suite in test_suites:
                future = executor.submit(self._run_suite, suite, environment)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
        
        return self.results
    
    def _run_suite(self, suite: TestSuite, environment: Dict):
        """Run a single test suite"""
        return asyncio.run(suite.run(environment=environment))

class ReportGenerator:
    """Generate various report formats"""
    
    @staticmethod
    def generate_html_report(results: Dict, output_file: str):
        """Generate comprehensive HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>API Orchestrator Test Report</title>
    <meta charset="utf-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .metric {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .metric .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric.passed .value {{ color: #28a745; }}
        .metric.failed .value {{ color: #dc3545; }}
        .metric.warning .value {{ color: #ffc107; }}
        .tests {{
            padding: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        .status-passed {{ color: #28a745; }}
        .status-failed {{ color: #dc3545; }}
        .status-error {{ color: #ffc107; }}
        .chart {{
            padding: 30px;
            text-align: center;
        }}
        .timestamp {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Test Report</h1>
            <p>Generated by API Orchestrator CLI - The Postman Killer</p>
        </div>
        
        <div class="summary">
            <div class="metric passed">
                <div class="label">Passed</div>
                <div class="value">{results['passed']}</div>
            </div>
            <div class="metric failed">
                <div class="label">Failed</div>
                <div class="value">{results['failed']}</div>
            </div>
            <div class="metric warning">
                <div class="label">Errors</div>
                <div class="value">{results['errors']}</div>
            </div>
            <div class="metric">
                <div class="label">Pass Rate</div>
                <div class="value">{results['pass_rate']:.1f}%</div>
            </div>
            <div class="metric">
                <div class="label">Duration</div>
                <div class="value">{results['duration_ms']:.0f}ms</div>
            </div>
            <div class="metric">
                <div class="label">Avg Response</div>
                <div class="value">{results.get('avg_response_time', 0):.0f}ms</div>
            </div>
        </div>
        
        <div class="tests">
            <h2>Test Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Response Time</th>
                        <th>Assertions</th>
                        <th>Error</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for test in results.get('tests', []):
            status_class = f"status-{test['status']}"
            assertions = f"{test.get('assertions_passed', 0)}/{test.get('assertions_total', 0)}"
            html += f"""
                    <tr>
                        <td>{test['name']}</td>
                        <td class="{status_class}">{test['status'].upper()}</td>
                        <td>{test.get('response_time_ms', 0):.2f}ms</td>
                        <td>{assertions}</td>
                        <td>{test.get('error', '')}</td>
                    </tr>
"""
        
        html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="timestamp">
            Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
        
        with open(output_file, 'w') as f:
            f.write(html)
    
    @staticmethod
    def generate_json_report(results: Dict, output_file: str):
        """Generate JSON report for CI/CD integration"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": results['total_tests'],
                "passed": results['passed'],
                "failed": results['failed'],
                "errors": results['errors'],
                "pass_rate": results['pass_rate'],
                "duration_ms": results['duration_ms']
            },
            "tests": results['tests'],
            "environment": results.get('environment', {}),
            "collection": results.get('collection_info', {})
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    @staticmethod
    def generate_junit_xml(results: Dict, output_file: str):
        """Generate JUnit XML for CI/CD tools"""
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="API Orchestrator Tests" tests="{results['total_tests']}" failures="{results['failed']}" errors="{results['errors']}" time="{results['duration_ms']/1000:.3f}">
  <testsuite name="{results.get('name', 'API Tests')}" tests="{results['total_tests']}" failures="{results['failed']}" errors="{results['errors']}" time="{results['duration_ms']/1000:.3f}">
"""
        
        for test in results.get('tests', []):
            time = test.get('response_time_ms', 0) / 1000
            xml += f'    <testcase classname="APITest" name="{test["name"]}" time="{time:.3f}">\n'
            
            if test['status'] == 'failed':
                xml += f'      <failure message="Test failed" type="AssertionError">\n'
                xml += f'        {test.get("error", "Assertion failed")}\n'
                for assertion in test.get('assertion_results', []):
                    if not assertion.get('passed'):
                        xml += f'        - {assertion.get("description", assertion.get("type"))}: {assertion.get("error")}\n'
                xml += f'      </failure>\n'
            elif test['status'] == 'error':
                xml += f'      <error message="Test error" type="RuntimeError">{test.get("error", "")}</error>\n'
            
            # Add system output
            if test.get('console_output'):
                xml += f'      <system-out><![CDATA[{test["console_output"]}]]></system-out>\n'
            
            xml += '    </testcase>\n'
        
        xml += """  </testsuite>
</testsuites>"""
        
        with open(output_file, 'w') as f:
            f.write(xml)

@click.group()
@click.option('--api-url', envvar='API_ORCHESTRATOR_URL', default='http://localhost:8000', help='API server URL')
@click.option('--api-key', envvar='API_ORCHESTRATOR_KEY', help='API key for authentication')
@click.option('--format', type=click.Choice(['text', 'json', 'junit', 'html']), default='text', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--no-color', is_flag=True, help='Disable colored output')
@click.option('--insecure', '-k', is_flag=True, help='Allow insecure SSL connections')
@click.option('--working-dir', '-w', type=click.Path(), help='Working directory')
@click.option('--global-var', '-g', multiple=True, help='Set global variable (key=value)')
def cli(api_url, api_key, format, verbose, no_color, insecure, working_dir, global_var):
    """
    API Orchestrator CLI - The POSTMAN KILLER
    
    Advanced API testing tool with CI/CD integration.
    Better than Newman, built for modern workflows.
    """
    config.api_url = api_url
    config.api_key = api_key
    config.output_format = format
    config.verbose = verbose
    config.color = not no_color
    config.insecure = insecure
    
    if working_dir:
        config.working_dir = working_dir
        os.chdir(working_dir)
    
    # Parse global variables
    for var in global_var:
        if '=' in var:
            key, value = var.split('=', 1)
            config.global_vars[key] = value

@cli.command()
@click.argument('collection', type=click.Path(exists=True))
@click.option('--environment', '-e', type=click.Path(exists=True), help='Environment file')
@click.option('--data', '-d', type=click.Path(exists=True), help='Data file for iterations (CSV/JSON)')
@click.option('--folder', help='Run specific folder')
@click.option('--bail', is_flag=True, help='Stop on first failure')
@click.option('--parallel', '-p', type=int, default=1, help='Number of parallel requests')
@click.option('--timeout', default=30000, help='Request timeout in ms')
@click.option('--delay-request', default=0, help='Delay between requests in ms')
@click.option('--iteration', '-n', default=1, help='Number of iterations')
@click.option('--reporters', '-r', multiple=True, help='Reporters: cli, json, html, junit')
@click.option('--reporter-json-export', type=click.Path(), help='Export path for JSON reporter')
@click.option('--reporter-html-export', type=click.Path(), help='Export path for HTML reporter')
@click.option('--reporter-junit-export', type=click.Path(), help='Export path for JUnit reporter')
@click.option('--suppress-exit-code', is_flag=True, help='Always exit with 0')
@click.option('--ignore-redirects', is_flag=True, help='Disable automatic redirect following')
@click.option('--ssl-client-cert', type=click.Path(exists=True), help='Client certificate file')
@click.option('--ssl-client-key', type=click.Path(exists=True), help='Client key file')
def run(collection, environment, data, folder, bail, parallel, timeout, delay_request, 
        iteration, reporters, reporter_json_export, reporter_html_export, 
        reporter_junit_export, suppress_exit_code, ignore_redirects, 
        ssl_client_cert, ssl_client_key):
    """
    Run API tests from a collection (Postman/OpenAPI/Native)
    
    Examples:
        
        # Run a Postman collection
        api-orchestrator run collection.json -e environment.json
        
        # Run with data file (data-driven testing)
        api-orchestrator run collection.json -d data.csv -n 10
        
        # Run in parallel with multiple reporters
        api-orchestrator run collection.json -p 5 -r cli -r html --reporter-html-export report.html
        
        # CI/CD integration with JUnit output
        api-orchestrator run collection.json -r junit --reporter-junit-export results.xml
    """
    
    start_time = time.time()
    
    # Print header
    if config.color:
        click.echo(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}🚀 API Orchestrator CLI - The POSTMAN KILLER{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    else:
        click.echo("="*60)
        click.echo("API Orchestrator CLI")
        click.echo("="*60 + "\n")
    
    # Load collection
    with open(collection, 'r') as f:
        if collection.endswith(('.yaml', '.yml')):
            collection_data = yaml.safe_load(f)
        else:
            collection_data = json.load(f)
    
    # Load environment
    env_vars = dict(config.global_vars)
    if environment:
        with open(environment, 'r') as f:
            env_data = json.load(f) if environment.endswith('.json') else yaml.safe_load(f)
            if 'values' in env_data:  # Postman format
                for var in env_data['values']:
                    if var.get('enabled', True):
                        env_vars[var['key']] = var['value']
            else:
                env_vars.update(env_data)
    
    # Load data file for iterations
    data_iterator = None
    if data:
        data_iterator = DataFileIterator(data)
        click.echo(f"📊 Loaded {len(data_iterator)} data sets from {data}\n")
    
    # Parse reporters
    if not reporters:
        reporters = ['cli']
    config.reporters = list(reporters)
    
    # Create test runner
    runner = TestRunnerAgent()
    
    # Detect collection type
    is_postman = 'info' in collection_data and 'item' in collection_data
    is_openapi = 'openapi' in collection_data or 'swagger' in collection_data
    
    if is_postman:
        click.echo(f"📦 Detected Postman Collection v{collection_data['info'].get('schema', '2.1')}")
        tests = _import_postman_collection(collection_data, runner, folder)
    elif is_openapi:
        click.echo(f"📦 Detected OpenAPI Specification")
        tests = _import_openapi_spec(collection_data, runner)
    else:
        click.echo(f"📦 API Orchestrator Native Collection")
        tests = _import_native_collection(collection_data, runner, folder)
    
    if not tests:
        click.echo(f"{Fore.YELLOW}⚠️ No tests to run{Style.RESET_ALL}")
        sys.exit(0)
    
    click.echo(f"📋 Found {len(tests)} tests to run")
    
    # Create test suite
    suite_name = collection_data.get('info', {}).get('name', 'Test Suite')
    suite = TestSuite(name=suite_name, tests=tests)
    
    # Run tests
    all_results = []
    
    # Handle data-driven testing
    if data_iterator:
        click.echo(f"\n{Fore.CYAN}Running with data iterations...{Style.RESET_ALL}")
        for idx, data_set in enumerate(data_iterator):
            click.echo(f"\n{Fore.BLUE}Data Set {idx + 1}/{len(data_iterator)}{Style.RESET_ALL}")
            # Merge data variables with environment
            test_env = {**env_vars, **data_set}
            result = _run_suite_with_options(suite, test_env, parallel, bail, delay_request)
            all_results.append(result)
            
            if bail and result['failed'] > 0:
                break
    else:
        # Run iterations
        for i in range(iteration):
            if iteration > 1:
                click.echo(f"\n{Fore.BLUE}Iteration {i + 1}/{iteration}{Style.RESET_ALL}")
            
            result = _run_suite_with_options(suite, env_vars, parallel, bail, delay_request)
            all_results.append(result)
            
            if bail and result['failed'] > 0:
                break
    
    # Aggregate results
    final_result = _aggregate_results(all_results, suite_name)
    final_result['duration_ms'] = (time.time() - start_time) * 1000
    
    # Generate reports
    _generate_reports(final_result, config.reporters, {
        'json': reporter_json_export,
        'html': reporter_html_export,
        'junit': reporter_junit_export
    })
    
    # Exit code
    exit_code = 0 if (final_result['failed'] == 0 and final_result['errors'] == 0) else 1
    if suppress_exit_code:
        exit_code = 0
    
    sys.exit(exit_code)

def _import_postman_collection(collection_data: Dict, runner: TestRunnerAgent, folder: str = None) -> List[TestCase]:
    """Import Postman collection"""
    importer = PostmanImporter()
    result = importer.import_collection(collection_data)
    
    if not result['success']:
        click.echo(f"{Fore.RED}❌ Failed to import: {result.get('error')}{Style.RESET_ALL}")
        sys.exit(1)
    
    tests = []
    for request in result['collection']['requests']:
        if folder and request.get('folder') != folder:
            continue
        
        test = runner.create_test_from_request(
            name=request['name'],
            url=request['url'],
            method=request['method'],
            headers=request.get('headers', {}),
            body=request.get('body'),
            assertions=request.get('assertions', [])
        )
        tests.append(test)
    
    return tests

def _import_openapi_spec(spec_data: Dict, runner: TestRunnerAgent) -> List[TestCase]:
    """Import OpenAPI specification"""
    tests = []
    
    servers = spec_data.get('servers', [{'url': 'http://localhost:8000'}])
    base_url = servers[0]['url']
    
    for path, methods in spec_data.get('paths', {}).items():
        for method, operation in methods.items():
            if method in ['get', 'post', 'put', 'delete', 'patch']:
                test = runner.create_test_from_request(
                    name=operation.get('summary', f"{method.upper()} {path}"),
                    url=f"{base_url}{path}",
                    method=method.upper(),
                    headers={'Content-Type': 'application/json'},
                    assertions=[
                        {"type": "STATUS_CODE", "expected": 200, "operator": "equals"}
                    ]
                )
                tests.append(test)
    
    return tests

def _import_native_collection(collection_data: Dict, runner: TestRunnerAgent, folder: str = None) -> List[TestCase]:
    """Import native API Orchestrator collection"""
    tests = []
    
    for test_def in collection_data.get('tests', []):
        if folder and test_def.get('folder') != folder:
            continue
        
        test = runner.create_test_from_request(
            name=test_def['name'],
            url=test_def['url'],
            method=test_def.get('method', 'GET'),
            headers=test_def.get('headers', {}),
            body=test_def.get('body'),
            assertions=test_def.get('assertions', [])
        )
        tests.append(test)
    
    return tests

def _run_suite_with_options(suite: TestSuite, environment: Dict, parallel: int, bail: bool, delay: int) -> Dict:
    """Run test suite with options"""
    if parallel > 1:
        # Run in parallel
        runner = ParallelRunner(max_workers=parallel)
        results = asyncio.run(runner.run_parallel([suite], environment))
        return results[0] if results else {}
    else:
        # Run sequentially
        return asyncio.run(suite.run(environment=environment))

def _aggregate_results(results: List[Dict], suite_name: str) -> Dict:
    """Aggregate multiple test results"""
    total_tests = sum(r['total_tests'] for r in results)
    passed = sum(r['passed'] for r in results)
    failed = sum(r['failed'] for r in results)
    errors = sum(r.get('errors', 0) for r in results)
    
    all_tests = []
    for r in results:
        all_tests.extend(r.get('tests', []))
    
    response_times = [t.get('response_time_ms', 0) for t in all_tests if t.get('response_time_ms')]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    return {
        'name': suite_name,
        'total_tests': total_tests,
        'passed': passed,
        'failed': failed,
        'errors': errors,
        'pass_rate': (passed / total_tests * 100) if total_tests > 0 else 0,
        'tests': all_tests,
        'avg_response_time': avg_response_time,
        'duration_ms': sum(r.get('duration_ms', 0) for r in results)
    }

def _generate_reports(results: Dict, reporters: List[str], export_paths: Dict):
    """Generate reports in specified formats"""
    
    # CLI reporter (always shown unless quiet)
    if 'cli' in reporters:
        _display_cli_results(results)
    
    # JSON reporter
    if 'json' in reporters:
        if export_paths.get('json'):
            ReportGenerator.generate_json_report(results, export_paths['json'])
            click.echo(f"📄 JSON report saved to: {export_paths['json']}")
        else:
            click.echo(json.dumps(results, indent=2))
    
    # HTML reporter
    if 'html' in reporters:
        if export_paths.get('html'):
            ReportGenerator.generate_html_report(results, export_paths['html'])
            click.echo(f"📄 HTML report saved to: {export_paths['html']}")
        else:
            # Generate to temp file and open
            temp_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
            ReportGenerator.generate_html_report(results, temp_file.name)
            click.echo(f"📄 HTML report: {temp_file.name}")
            subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', temp_file.name])
    
    # JUnit reporter
    if 'junit' in reporters:
        if export_paths.get('junit'):
            ReportGenerator.generate_junit_xml(results, export_paths['junit'])
            click.echo(f"📄 JUnit report saved to: {export_paths['junit']}")

def _display_cli_results(results: Dict):
    """Display results in CLI format"""
    # Summary
    total = results['total_tests']
    passed = results['passed']
    failed = results['failed']
    errors = results.get('errors', 0)
    
    if failed == 0 and errors == 0:
        status_color = Fore.GREEN if config.color else ''
        status_icon = "✅"
        status_text = "ALL TESTS PASSED"
    else:
        status_color = Fore.RED if config.color else ''
        status_icon = "❌"
        status_text = "TESTS FAILED"
    
    click.echo(f"\n{status_color}{'='*60}{Style.RESET_ALL if config.color else ''}")
    click.echo(f"{status_color}{status_icon} {status_text}{Style.RESET_ALL if config.color else ''}")
    click.echo(f"{status_color}{'='*60}{Style.RESET_ALL if config.color else ''}\n")
    
    # Metrics
    table_data = [
        ["Total Tests", total],
        ["Passed", f"{Fore.GREEN if config.color else ''}{passed}{Style.RESET_ALL if config.color else ''}"],
        ["Failed", f"{Fore.RED if config.color else ''}{failed}{Style.RESET_ALL if config.color else ''}"],
        ["Errors", f"{Fore.YELLOW if config.color else ''}{errors}{Style.RESET_ALL if config.color else ''}"],
        ["Pass Rate", f"{results['pass_rate']:.1f}%"],
        ["Avg Response", f"{results.get('avg_response_time', 0):.2f}ms"],
        ["Total Duration", f"{results['duration_ms']:.2f}ms"]
    ]
    
    click.echo(tabulate(table_data, tablefmt="simple"))
    
    # Detailed results if verbose
    if config.verbose and results.get('tests'):
        click.echo(f"\n{Fore.CYAN if config.color else ''}Test Details:{Style.RESET_ALL if config.color else ''}")
        
        test_table = []
        for test in results['tests']:
            status = test['status']
            if status == 'passed':
                status_str = f"{Fore.GREEN if config.color else ''}✅ PASS{Style.RESET_ALL if config.color else ''}"
            elif status == 'failed':
                status_str = f"{Fore.RED if config.color else ''}❌ FAIL{Style.RESET_ALL if config.color else ''}"
            else:
                status_str = f"{Fore.YELLOW if config.color else ''}⚠️ ERROR{Style.RESET_ALL if config.color else ''}"
            
            test_table.append([
                test['name'][:50],
                status_str,
                f"{test.get('response_time_ms', 0):.2f}ms",
                test.get('error', '')[:40]
            ])
        
        headers = ["Test", "Status", "Time", "Error"]
        click.echo(tabulate(test_table, headers=headers, tablefmt="simple"))

# Add more CLI commands for other features...

@cli.command()
@click.argument('url')
@click.option('--watch', '-w', is_flag=True, help='Watch for changes continuously')
@click.option('--interval', default=60, help='Check interval in seconds')
@click.option('--webhook', help='Webhook URL for notifications')
def monitor(url, watch, interval, webhook):
    """Monitor API endpoint health"""
    click.echo(f"{Fore.CYAN}🔍 Monitoring {url}{Style.RESET_ALL}")
    
    async def check_health():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10)
                status = "UP" if response.status_code < 400 else "DOWN"
                response_time = response.elapsed.total_seconds() * 1000
                
                if status == "UP":
                    click.echo(f"{Fore.GREEN}✅ {datetime.now()}: {status} - {response_time:.2f}ms{Style.RESET_ALL}")
                else:
                    click.echo(f"{Fore.RED}❌ {datetime.now()}: {status} - Status {response.status_code}{Style.RESET_ALL}")
                    
                    if webhook:
                        # Send webhook notification
                        await client.post(webhook, json={
                            "url": url,
                            "status": status,
                            "status_code": response.status_code,
                            "timestamp": datetime.now().isoformat()
                        })
                
                return status == "UP"
            except Exception as e:
                click.echo(f"{Fore.RED}❌ {datetime.now()}: ERROR - {str(e)}{Style.RESET_ALL}")
                return False
    
    if watch:
        click.echo(f"Monitoring every {interval} seconds. Press Ctrl+C to stop.\n")
        try:
            while True:
                asyncio.run(check_health())
                time.sleep(interval)
        except KeyboardInterrupt:
            click.echo(f"\n{Fore.YELLOW}Monitoring stopped{Style.RESET_ALL}")
    else:
        healthy = asyncio.run(check_health())
        sys.exit(0 if healthy else 1)

if __name__ == '__main__':
    cli()