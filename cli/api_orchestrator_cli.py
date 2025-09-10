#!/usr/bin/env python3
"""
API Orchestrator CLI - Command Line Interface for CI/CD Integration
Similar to Newman for Postman, but better!
"""

import click
import json
import sys
import os
import asyncio
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from tabulate import tabulate
from colorama import init, Fore, Style
import yaml

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.agents.test_runner_agent import TestRunnerAgent, TestCase, TestSuite, Assertion, AssertionType
from backend.src.postman_import import PostmanImporter

class CLIConfig:
    """CLI Configuration"""
    def __init__(self):
        self.api_url = os.getenv('API_ORCHESTRATOR_URL', 'http://localhost:8000')
        self.api_key = os.getenv('API_ORCHESTRATOR_KEY', '')
        self.output_format = 'text'
        self.verbose = False

# Global config
config = CLIConfig()

@click.group()
@click.option('--api-url', default=None, help='API Orchestrator server URL')
@click.option('--api-key', default=None, help='API key for authentication')
@click.option('--format', type=click.Choice(['text', 'json', 'junit', 'html']), default='text', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def cli(api_url, api_key, format, verbose):
    """API Orchestrator CLI - Test, Mock, and Generate APIs"""
    if api_url:
        config.api_url = api_url
    if api_key:
        config.api_key = api_key
    config.output_format = format
    config.verbose = verbose

@cli.command()
@click.argument('collection', type=click.Path(exists=True))
@click.option('--environment', '-e', type=click.Path(exists=True), help='Environment file')
@click.option('--folder', help='Run specific folder')
@click.option('--bail', is_flag=True, help='Stop on first failure')
@click.option('--parallel', is_flag=True, help='Run tests in parallel')
@click.option('--timeout', default=30000, help='Request timeout in ms')
@click.option('--delay', default=0, help='Delay between requests in ms')
@click.option('--iteration', default=1, help='Number of iterations')
def run(collection, environment, folder, bail, parallel, timeout, delay, iteration):
    """Run API tests from a collection"""
    click.echo(f"{Fore.CYAN}🚀 API Orchestrator Test Runner{Style.RESET_ALL}")
    
    # Load collection
    with open(collection, 'r') as f:
        collection_data = json.load(f)
    
    # Load environment if provided
    env_vars = {}
    if environment:
        with open(environment, 'r') as f:
            env_data = json.load(f)
            if 'values' in env_data:  # Postman format
                for var in env_data['values']:
                    if var.get('enabled', True):
                        env_vars[var['key']] = var['value']
            else:  # Simple key-value format
                env_vars = env_data
    
    # Create test runner
    runner = TestRunnerAgent()
    
    # Check if it's a Postman collection
    is_postman = 'info' in collection_data and 'item' in collection_data
    
    if is_postman:
        click.echo(f"{Fore.YELLOW}📦 Detected Postman Collection v{collection_data['info'].get('schema', '2.1')}{Style.RESET_ALL}")
        
        # Import Postman collection
        importer = PostmanImporter()
        result = importer.import_collection(collection_data)
        
        if not result['success']:
            click.echo(f"{Fore.RED}❌ Failed to import collection: {result.get('error')}{Style.RESET_ALL}")
            sys.exit(1)
        
        imported = result['collection']
        click.echo(f"{Fore.GREEN}✅ Imported {len(imported['requests'])} requests{Style.RESET_ALL}")
        
        # Convert to test cases
        tests = []
        for request in imported['requests']:
            # Filter by folder if specified
            if folder and request.get('folder') != folder:
                continue
            
            # Create test case
            test = runner.create_test_from_request(
                name=request['name'],
                url=request['url'],
                method=request['method'],
                headers=request.get('headers', {}),
                body=request.get('body'),
                assertions=request.get('assertions', [])
            )
            tests.append(test)
    else:
        # Native API Orchestrator format
        click.echo(f"{Fore.YELLOW}📦 API Orchestrator Collection{Style.RESET_ALL}")
        tests = []
        
        for test_def in collection_data.get('tests', []):
            test = runner.create_test_from_request(
                name=test_def['name'],
                url=test_def['url'],
                method=test_def.get('method', 'GET'),
                headers=test_def.get('headers', {}),
                body=test_def.get('body'),
                assertions=test_def.get('assertions', [])
            )
            tests.append(test)
    
    if not tests:
        click.echo(f"{Fore.YELLOW}⚠️ No tests to run{Style.RESET_ALL}")
        sys.exit(0)
    
    # Create test suite
    suite = TestSuite(name=collection_data.get('info', {}).get('name', 'Test Suite'), tests=tests)
    
    # Run tests for specified iterations
    all_results = []
    for i in range(iteration):
        if iteration > 1:
            click.echo(f"\n{Fore.CYAN}Iteration {i+1}/{iteration}{Style.RESET_ALL}")
        
        # Run the suite
        click.echo(f"\n{Fore.CYAN}Running {len(tests)} tests...{Style.RESET_ALL}\n")
        
        result = asyncio.run(suite.run(environment=env_vars, parallel=parallel))
        all_results.append(result)
        
        # Display results
        _display_results(result, config.output_format)
        
        # Stop on failure if bail is set
        if bail and result['failed'] > 0:
            click.echo(f"{Fore.RED}❌ Stopping due to test failure (--bail){Style.RESET_ALL}")
            sys.exit(1)
        
        # Delay between iterations
        if delay > 0 and i < iteration - 1:
            import time
            time.sleep(delay / 1000)
    
    # Exit with proper code
    total_failed = sum(r['failed'] for r in all_results)
    sys.exit(0 if total_failed == 0 else 1)

@cli.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--port', default=3000, help='Port for mock server')
@click.option('--delay', default=0, help='Response delay in ms')
@click.option('--chaos', is_flag=True, help='Enable chaos mode (random errors)')
def mock(spec_file, port, delay, chaos):
    """Start a mock server from OpenAPI spec"""
    click.echo(f"{Fore.CYAN}🎭 Starting Mock Server{Style.RESET_ALL}")
    
    # Load spec
    with open(spec_file, 'r') as f:
        if spec_file.endswith('.yaml') or spec_file.endswith('.yml'):
            spec = yaml.safe_load(f)
        else:
            spec = json.load(f)
    
    # Start mock server
    from backend.src.agents.mock_server_agent import MockServerAgent
    
    agent = MockServerAgent()
    server_info = asyncio.run(agent.create_mock_server(
        spec=spec,
        port=port,
        delay_ms=delay,
        chaos_mode=chaos
    ))
    
    click.echo(f"{Fore.GREEN}✅ Mock server running at http://localhost:{port}{Style.RESET_ALL}")
    click.echo(f"📋 Endpoints:")
    
    for endpoint in server_info.get('endpoints', []):
        click.echo(f"  • {endpoint['method']} {endpoint['path']}")
    
    click.echo(f"\n{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}")
    
    try:
        # Keep server running
        asyncio.run(asyncio.Event().wait())
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.RED}Stopping mock server...{Style.RESET_ALL}")

@cli.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--language', type=click.Choice(['python', 'javascript', 'typescript', 'go', 'java', 'csharp']), 
              default='python', help='Target language')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--package-name', help='Package name for generated code')
def generate(spec_file, language, output, package_name):
    """Generate SDK from OpenAPI spec"""
    click.echo(f"{Fore.CYAN}🔧 Generating {language.upper()} SDK{Style.RESET_ALL}")
    
    # Load spec
    with open(spec_file, 'r') as f:
        if spec_file.endswith('.yaml') or spec_file.endswith('.yml'):
            spec = yaml.safe_load(f)
        else:
            spec = json.load(f)
    
    # Generate SDK
    from backend.src.agents.code_generator_agent import CodeGeneratorAgent
    
    agent = CodeGeneratorAgent()
    result = agent.generate_sdk(
        spec=spec,
        language=language,
        package_name=package_name or 'api_client'
    )
    
    # Write output
    output_dir = Path(output or f'./{package_name or "api_client"}_{language}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for file_name, content in result['files'].items():
        file_path = output_dir / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        click.echo(f"  📄 Generated: {file_path}")
    
    click.echo(f"{Fore.GREEN}✅ SDK generated in {output_dir}{Style.RESET_ALL}")

@cli.command()
@click.argument('postman_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file')
def import_postman(postman_file, output):
    """Import Postman collection to API Orchestrator format"""
    click.echo(f"{Fore.CYAN}📥 Importing Postman Collection{Style.RESET_ALL}")
    
    # Load Postman collection
    with open(postman_file, 'r') as f:
        postman_data = json.load(f)
    
    # Import
    importer = PostmanImporter()
    result = importer.import_collection(postman_data)
    
    if not result['success']:
        click.echo(f"{Fore.RED}❌ Import failed: {result.get('error')}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Convert to internal format
    internal = importer.convert_to_internal_format(result['collection'])
    
    # Write output
    output_file = output or postman_file.replace('.json', '_imported.json')
    with open(output_file, 'w') as f:
        json.dump(internal, f, indent=2)
    
    click.echo(f"{Fore.GREEN}✅ Imported successfully{Style.RESET_ALL}")
    click.echo(f"  📊 {result['stats']['total_requests']} requests")
    click.echo(f"  📁 {result['stats']['total_folders']} folders")
    click.echo(f"  🔧 {result['stats']['total_variables']} variables")
    click.echo(f"  💾 Saved to: {output_file}")

@cli.command()
@click.argument('url')
@click.option('--method', '-X', default='GET', help='HTTP method')
@click.option('--header', '-H', multiple=True, help='Headers (can be used multiple times)')
@click.option('--data', '-d', help='Request body')
@click.option('--auth', help='Authentication (user:pass for basic)')
@click.option('--assert-status', type=int, help='Assert response status code')
@click.option('--assert-time', type=int, help='Assert response time (ms)')
@click.option('--assert-contains', help='Assert response contains text')
def test(url, method, header, data, auth, assert_status, assert_time, assert_contains):
    """Quick test a single API endpoint"""
    click.echo(f"{Fore.CYAN}🧪 Testing {method} {url}{Style.RESET_ALL}")
    
    # Parse headers
    headers = {}
    for h in header:
        if ':' in h:
            key, value = h.split(':', 1)
            headers[key.strip()] = value.strip()
    
    # Parse auth
    if auth and ':' in auth:
        username, password = auth.split(':', 1)
        import base64
        auth_header = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers['Authorization'] = f"Basic {auth_header}"
    
    # Create assertions
    assertions = []
    if assert_status:
        assertions.append({
            "type": "STATUS_CODE",
            "expected": assert_status,
            "operator": "equals"
        })
    if assert_time:
        assertions.append({
            "type": "RESPONSE_TIME",
            "expected": assert_time,
            "operator": "less_than"
        })
    if assert_contains:
        assertions.append({
            "type": "BODY_CONTAINS",
            "expected": assert_contains,
            "operator": "contains"
        })
    
    # Create and run test
    runner = TestRunnerAgent()
    test = runner.create_test_from_request(
        name="Quick Test",
        url=url,
        method=method,
        headers=headers,
        body=data,
        assertions=assertions or None
    )
    
    result = asyncio.run(runner.run_single_test(test))
    
    # Display result
    if result['status'] == 'passed':
        click.echo(f"{Fore.GREEN}✅ Test PASSED{Style.RESET_ALL}")
    else:
        click.echo(f"{Fore.RED}❌ Test FAILED{Style.RESET_ALL}")
    
    click.echo(f"  ⏱️ Response time: {result['response_time_ms']:.2f}ms")
    
    if 'response' in result:
        click.echo(f"  📊 Status: {result['response']['status_code']}")
        
        if config.verbose:
            click.echo(f"\n{Fore.CYAN}Response Headers:{Style.RESET_ALL}")
            for key, value in result['response']['headers'].items():
                click.echo(f"  {key}: {value}")
            
            click.echo(f"\n{Fore.CYAN}Response Body:{Style.RESET_ALL}")
            click.echo(result['response']['body'])
    
    # Show assertion results
    if result.get('assertions'):
        click.echo(f"\n{Fore.CYAN}Assertions:{Style.RESET_ALL}")
        for assertion in result['assertions']:
            icon = "✅" if assertion['passed'] else "❌"
            click.echo(f"  {icon} {assertion.get('description', assertion['type'])}")
            if not assertion['passed'] and assertion.get('error'):
                click.echo(f"     {Fore.RED}{assertion['error']}{Style.RESET_ALL}")
    
    sys.exit(0 if result['status'] == 'passed' else 1)

def _display_results(result: Dict[str, Any], format: str):
    """Display test results in specified format"""
    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'junit':
        # Generate JUnit XML format
        xml = _generate_junit_xml(result)
        click.echo(xml)
    elif format == 'html':
        # Generate HTML report
        html = _generate_html_report(result)
        click.echo(html)
    else:
        # Default text format
        # Summary
        total = result['total_tests']
        passed = result['passed']
        failed = result['failed']
        errors = result['errors']
        
        if failed == 0 and errors == 0:
            status_color = Fore.GREEN
            status_icon = "✅"
        else:
            status_color = Fore.RED
            status_icon = "❌"
        
        click.echo(f"\n{status_color}{status_icon} Test Results{Style.RESET_ALL}")
        click.echo(f"  Total:  {total}")
        click.echo(f"  Passed: {Fore.GREEN}{passed}{Style.RESET_ALL}")
        click.echo(f"  Failed: {Fore.RED}{failed}{Style.RESET_ALL}")
        click.echo(f"  Errors: {Fore.YELLOW}{errors}{Style.RESET_ALL}")
        click.echo(f"  Pass Rate: {result['pass_rate']:.1f}%")
        click.echo(f"  Duration: {result['duration_ms']:.2f}ms")
        
        # Individual test results
        if config.verbose:
            click.echo(f"\n{Fore.CYAN}Test Details:{Style.RESET_ALL}")
            
            table_data = []
            for test in result['tests']:
                status = test['status']
                if status == 'passed':
                    status_str = f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}"
                elif status == 'failed':
                    status_str = f"{Fore.RED}❌ FAIL{Style.RESET_ALL}"
                else:
                    status_str = f"{Fore.YELLOW}⚠️ ERROR{Style.RESET_ALL}"
                
                table_data.append([
                    test['name'][:40],
                    status_str,
                    f"{test.get('response_time_ms', 0):.2f}ms",
                    test.get('error', '')[:30]
                ])
            
            headers = ["Test", "Status", "Time", "Error"]
            click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

def _generate_junit_xml(result: Dict[str, Any]) -> str:
    """Generate JUnit XML format"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="{result['name']}" tests="{result['total_tests']}" failures="{result['failed']}" errors="{result['errors']}" time="{result['duration_ms']/1000:.3f}">
  <testsuite name="{result['name']}" tests="{result['total_tests']}" failures="{result['failed']}" errors="{result['errors']}" time="{result['duration_ms']/1000:.3f}">
"""
    
    for test in result['tests']:
        time = test.get('duration_ms', 0) / 1000
        xml += f'    <testcase name="{test["name"]}" time="{time:.3f}">\n'
        
        if test['status'] == 'failed':
            xml += f'      <failure message="Test failed">{test.get("error", "")}</failure>\n'
        elif test['status'] == 'error':
            xml += f'      <error message="Test error">{test.get("error", "")}</error>\n'
        
        xml += '    </testcase>\n'
    
    xml += """  </testsuite>
</testsuites>"""
    
    return xml

def _generate_html_report(result: Dict[str, Any]) -> str:
    """Generate HTML report"""
    # Simple HTML report template
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {result['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .error {{ color: orange; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Test Report: {result['name']}</h1>
    <div class="summary">
        <p><strong>Total Tests:</strong> {result['total_tests']}</p>
        <p><strong>Passed:</strong> <span class="passed">{result['passed']}</span></p>
        <p><strong>Failed:</strong> <span class="failed">{result['failed']}</span></p>
        <p><strong>Errors:</strong> <span class="error">{result['errors']}</span></p>
        <p><strong>Pass Rate:</strong> {result['pass_rate']:.1f}%</p>
        <p><strong>Duration:</strong> {result['duration_ms']:.2f}ms</p>
    </div>
    
    <h2>Test Details</h2>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Status</th>
            <th>Response Time</th>
            <th>Error</th>
        </tr>
"""
    
    for test in result['tests']:
        status_class = test['status']
        html += f"""        <tr>
            <td>{test['name']}</td>
            <td class="{status_class}">{test['status'].upper()}</td>
            <td>{test.get('response_time_ms', 0):.2f}ms</td>
            <td>{test.get('error', '')}</td>
        </tr>
"""
    
    html += """    </table>
</body>
</html>"""
    
    return html

if __name__ == '__main__':
    cli()