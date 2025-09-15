#!/usr/bin/env python3
"""
Simplified API Orchestrator CLI for GitHub Actions
Newman-compatible test runner without backend dependencies
"""

import click
import json
import sys
import os
import asyncio
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
import time
from datetime import datetime
import yaml

class TestResult:
    def __init__(self, name: str, passed: bool, duration: float, error: str = None):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.error = error

class TestSuite:
    def __init__(self, name: str):
        self.name = name
        self.tests = []
        self.start_time = None
        self.end_time = None

    def add_test(self, test: TestResult):
        self.tests.append(test)

    def get_summary(self):
        total = len(self.tests)
        passed = sum(1 for t in self.tests if t.passed)
        failed = total - passed
        duration = sum(t.duration for t in self.tests)

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'duration': duration,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'avg_response_time': duration / total if total > 0 else 0
        }

class PostmanCollectionRunner:
    def __init__(self, collection_path: str, environment: str = None, reporters: List[str] = None):
        self.collection_path = collection_path
        self.environment = environment or {}
        self.reporters = reporters or ['cli']
        self.suite = TestSuite("API Test Suite")

    def load_collection(self):
        """Load Postman collection from file"""
        try:
            with open(self.collection_path, 'r') as f:
                if self.collection_path.endswith('.yaml') or self.collection_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            click.echo(f"Error loading collection: {e}", err=True)
            sys.exit(1)

    def execute_request(self, request: Dict[str, Any]) -> TestResult:
        """Execute a single HTTP request"""
        start_time = time.time()

        try:
            method = request.get('method', 'GET')
            url = request.get('url', '')
            headers = {}

            # Handle headers
            for header in request.get('header', []):
                if isinstance(header, dict):
                    headers[header.get('key', '')] = header.get('value', '')

            # Execute request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30
            )

            duration = (time.time() - start_time) * 1000  # Convert to ms

            # Basic success check
            if response.status_code < 400:
                return TestResult(f"{method} {url}", True, duration)
            else:
                return TestResult(f"{method} {url}", False, duration, f"HTTP {response.status_code}")

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(f"{method} {url}", False, duration, str(e))

    def run_tests(self, iterations: int = 1):
        """Run all tests in the collection"""
        collection = self.load_collection()

        click.echo(f"Running API Orchestrator Tests")
        click.echo(f"Collection: {collection.get('info', {}).get('name', 'Unknown')}")
        click.echo(f"Iterations: {iterations}")
        click.echo("-" * 50)

        for iteration in range(iterations):
            if iterations > 1:
                click.echo(f"\nIteration {iteration + 1}/{iterations}")

            # Process collection items
            for item in collection.get('item', []):
                if 'request' in item:
                    test_result = self.execute_request(item['request'])
                    self.suite.add_test(test_result)

                    # Print result
                    status = "✓" if test_result.passed else "✗"
                    color = "green" if test_result.passed else "red"
                    click.echo(f"  {status} {item.get('name', 'Unnamed Test')} ({test_result.duration:.0f}ms)", color=color)

                    if not test_result.passed and test_result.error:
                        click.echo(f"    Error: {test_result.error}", color="red")

        # Generate reports
        self.generate_reports()

    def generate_reports(self):
        """Generate test reports"""
        summary = self.suite.get_summary()

        # CLI Report
        if 'cli' in self.reporters:
            click.echo("\n" + "="*50)
            click.echo("TEST SUMMARY")
            click.echo("="*50)
            click.echo(f"Total: {summary['total']}")
            click.echo(f"Passed: {summary['passed']}")
            click.echo(f"Failed: {summary['failed']}")
            click.echo(f"Duration: {summary['duration']:.0f}ms")
            click.echo(f"Pass Rate: {summary['pass_rate']:.1f}%")
            click.echo(f"Average Response Time: {summary['avg_response_time']:.2f}ms")

        # JSON Report
        if 'json' in self.reporters:
            report = {
                'summary': summary,
                'tests': [
                    {
                        'name': test.name,
                        'passed': test.passed,
                        'duration': test.duration,
                        'error': test.error
                    }
                    for test in self.suite.tests
                ]
            }

            with open('test-results.json', 'w') as f:
                json.dump(report, f, indent=2)

        # JUnit Report
        if 'junit' in self.reporters:
            self.generate_junit_report()

    def generate_junit_report(self):
        """Generate JUnit XML report"""
        summary = self.suite.get_summary()

        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="{self.suite.name}" tests="{summary['total']}" failures="{summary['failed']}" time="{summary['duration']/1000:.3f}">
'''

        for test in self.suite.tests:
            xml_content += f'    <testcase name="{test.name}" time="{test.duration/1000:.3f}"'
            if test.passed:
                xml_content += '/>\n'
            else:
                xml_content += f'>\n      <failure message="{test.error or "Test failed"}"/>\n    </testcase>\n'

        xml_content += '  </testsuite>\n</testsuites>'

        with open('junit-report.xml', 'w') as f:
            f.write(xml_content)

@click.group()
def cli():
    """API Orchestrator CLI - The POSTMAN KILLER"""
    pass

@cli.command()
@click.argument('collection')
@click.option('--environment', '-e', default='production', help='Environment to use')
@click.option('--reporters', '-r', default='cli,json', help='Test reporters (json, junit, html, cli)')
@click.option('--bail', is_flag=True, help='Stop on first test failure')
@click.option('--timeout', default=30000, help='Request timeout in ms')
@click.option('--delay', default=0, help='Delay between requests in ms')
@click.option('--iterations', default=1, help='Number of iterations to run')
@click.option('--folder', help='Run specific folder from collection')
def test(collection, environment, reporters, bail, timeout, delay, iterations, folder):
    """Run API tests from a collection file"""

    print(f"🔍 Debug: Starting test command")
    print(f"🔍 Debug: Collection={collection}")
    print(f"🔍 Debug: Environment={environment}")
    print(f"🔍 Debug: Reporters={reporters}")
    print(f"🔍 Debug: Working directory: {os.getcwd()}")
    print(f"🔍 Debug: Collection exists: {os.path.exists(collection)}")

    # Validate collection file exists
    if not os.path.exists(collection):
        click.echo(f"Error: Collection file '{collection}' not found", err=True)
        print(f"🔍 Debug: Available files: {os.listdir('.')}")
        sys.exit(1)

    # Parse reporters
    reporter_list = [r.strip() for r in reporters.split(',')]

    # Create and run test runner
    runner = PostmanCollectionRunner(collection, environment, reporter_list)

    try:
        runner.run_tests(int(iterations))

        # Check if any tests failed
        summary = runner.suite.get_summary()
        if summary['failed'] > 0 and not os.getenv('FAIL_ON_ERROR', 'true').lower() == 'false':
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\nTest run interrupted", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error running tests: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()