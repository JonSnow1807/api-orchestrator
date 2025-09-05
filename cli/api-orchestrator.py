#!/usr/bin/env python3
"""
API Orchestrator CLI - Transform any codebase into production-ready APIs
"""

import click
import requests
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
import yaml
import asyncio
import websocket
from datetime import datetime

console = Console()

# Configuration
DEFAULT_API_URL = "http://localhost:8000"
CONFIG_FILE = Path.home() / ".api-orchestrator" / "config.json"

class APIOrchestratorCLI:
    def __init__(self):
        self.config = self.load_config()
        self.api_url = self.config.get("api_url", DEFAULT_API_URL)
        self.token = self.config.get("token")
        
    def load_config(self):
        """Load CLI configuration"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        """Save CLI configuration"""
        CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_headers(self):
        """Get API headers with authentication"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

cli_instance = APIOrchestratorCLI()

@click.group()
@click.version_option(version='1.0.0', prog_name='API Orchestrator')
def cli():
    """🚀 API Orchestrator - AI-Powered API Development Platform
    
    Transform any codebase into production-ready APIs with OpenAPI specs,
    comprehensive test suites, and instant mock servers.
    """
    pass

@cli.command()
@click.option('--email', prompt=True, help='Your email address')
@click.option('--password', prompt=True, hide_input=True, help='Your password')
@click.option('--api-url', default=DEFAULT_API_URL, help='API server URL')
def login(email, password, api_url):
    """🔐 Authenticate with API Orchestrator"""
    cli_instance.api_url = api_url
    
    with console.status("[bold green]Logging in..."):
        try:
            response = requests.post(
                f"{api_url}/auth/login",
                data={"username": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                cli_instance.token = data["access_token"]
                cli_instance.config["token"] = data["access_token"]
                cli_instance.config["api_url"] = api_url
                cli_instance.config["email"] = email
                cli_instance.save_config()
                
                console.print(f"[green]✅ Successfully logged in as {email}[/green]")
            else:
                console.print(f"[red]❌ Login failed: {response.json().get('detail', 'Unknown error')}[/red]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]❌ Connection error: {str(e)}[/red]")
            sys.exit(1)

@cli.command()
def logout():
    """🚪 Logout from API Orchestrator"""
    cli_instance.config = {}
    cli_instance.save_config()
    console.print("[green]✅ Successfully logged out[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--framework', default='auto', help='Framework (auto/fastapi/flask/express/django)')
@click.option('--output', '-o', default='./api-output', help='Output directory')
@click.option('--watch', '-w', is_flag=True, help='Watch for changes')
@click.option('--mock', is_flag=True, default=True, help='Generate mock server')
@click.option('--tests', is_flag=True, default=True, help='Generate tests')
@click.option('--ai', is_flag=True, default=True, help='Include AI analysis')
def scan(path, framework, output, watch, mock, tests, ai):
    """🔍 Scan codebase and generate API artifacts
    
    Example:
        api-orchestrator scan ./my-project
        api-orchestrator scan ./backend --framework fastapi -o ./output
    """
    if not cli_instance.token:
        console.print("[red]❌ Please login first: api-orchestrator login[/red]")
        sys.exit(1)
    
    # Display scan configuration
    config_table = Table(title="Scan Configuration", show_header=False)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("📁 Source Path", str(path))
    config_table.add_row("🔧 Framework", framework)
    config_table.add_row("📂 Output Directory", output)
    config_table.add_row("🤖 AI Analysis", "✅" if ai else "❌")
    config_table.add_row("🧪 Generate Tests", "✅" if tests else "❌")
    config_table.add_row("🎭 Mock Server", "✅" if mock else "❌")
    console.print(config_table)
    console.print()
    
    # Start orchestration
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Starting orchestration...", total=100)
        
        try:
            # Create orchestration request
            response = requests.post(
                f"{cli_instance.api_url}/api/orchestrate",
                json={
                    "source_path": str(path),
                    "framework": framework,
                    "include_tests": tests,
                    "include_mock": mock,
                    "include_ai_analysis": ai
                },
                headers=cli_instance.get_headers()
            )
            
            if response.status_code == 200:
                task_id = response.json()["task_id"]
                progress.update(task, description=f"[cyan]Task ID: {task_id}")
                
                # Monitor progress via polling (WebSocket would be better)
                while True:
                    status_response = requests.get(
                        f"{cli_instance.api_url}/api/tasks/{task_id}",
                        headers=cli_instance.get_headers()
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status", "unknown")
                        message = status_data.get("message", "Processing...")
                        
                        progress.update(
                            task, 
                            description=f"[cyan]{message}",
                            completed=status_data.get("progress", 0)
                        )
                        
                        if status == "completed":
                            progress.update(task, completed=100)
                            break
                        elif status == "failed":
                            console.print(f"[red]❌ Orchestration failed: {message}[/red]")
                            sys.exit(1)
                    
                    time.sleep(2)
                
                # Download artifacts
                console.print("\n[green]✅ Orchestration completed![/green]\n")
                download_artifacts(task_id, output)
                
                if watch:
                    console.print("[yellow]👀 Watching for changes... (Press Ctrl+C to stop)[/yellow]")
                    watch_directory(path, framework, output)
                    
            else:
                console.print(f"[red]❌ Failed to start orchestration: {response.json()}[/red]")
                sys.exit(1)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Orchestration cancelled[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            sys.exit(1)

def download_artifacts(task_id, output_dir):
    """Download generated artifacts"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    artifacts = [
        ("openapi.json", "OpenAPI Specification"),
        ("openapi.yaml", "OpenAPI YAML"),
        ("tests.zip", "Test Suite"),
        ("mock_server.zip", "Mock Server"),
        ("analysis.json", "AI Analysis Report")
    ]
    
    console.print("[bold]📥 Downloading artifacts:[/bold]")
    
    for filename, description in artifacts:
        try:
            response = requests.get(
                f"{cli_instance.api_url}/api/download/{task_id}/{filename}",
                headers=cli_instance.get_headers()
            )
            
            if response.status_code == 200:
                output_path = Path(output_dir) / filename
                
                if filename.endswith('.zip'):
                    output_path.write_bytes(response.content)
                else:
                    output_path.write_text(response.text)
                
                console.print(f"  ✅ {description} → {output_path}")
            else:
                console.print(f"  ⏭️  {description} (not available)")
        except Exception as e:
            console.print(f"  ❌ {description} (error: {str(e)})")

def watch_directory(path, framework, output):
    """Watch directory for changes and re-orchestrate"""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class ChangeHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if not event.is_directory:
                console.print(f"[yellow]🔄 Change detected: {event.src_path}[/yellow]")
                # Re-run orchestration
                # scan(path, framework, output, False, True, True, True)
    
    observer = Observer()
    observer.schedule(ChangeHandler(), path, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@cli.command()
@click.argument('task_id')
def status(task_id):
    """📊 Check orchestration task status"""
    try:
        response = requests.get(
            f"{cli_instance.api_url}/api/tasks/{task_id}",
            headers=cli_instance.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Create status panel
            status_color = {
                "completed": "green",
                "in_progress": "yellow",
                "failed": "red",
                "pending": "blue"
            }.get(data["status"], "white")
            
            panel = Panel(
                f"""
[bold]Task ID:[/bold] {data['id']}
[bold]Status:[/bold] [{status_color}]{data['status']}[/{status_color}]
[bold]Progress:[/bold] {data.get('progress', 0)}%
[bold]Message:[/bold] {data.get('message', 'N/A')}
[bold]Created:[/bold] {data.get('created_at', 'N/A')}
                """,
                title="Task Status",
                border_style=status_color
            )
            console.print(panel)
        else:
            console.print(f"[red]❌ Task not found[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

@cli.command()
def list():
    """📋 List all orchestration tasks"""
    try:
        response = requests.get(
            f"{cli_instance.api_url}/api/tasks",
            headers=cli_instance.get_headers()
        )
        
        if response.status_code == 200:
            tasks = response.json().get("tasks", [])
            
            if not tasks:
                console.print("[yellow]No tasks found[/yellow]")
                return
            
            table = Table(title="Orchestration Tasks")
            table.add_column("ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Progress")
            table.add_column("Created", style="dim")
            
            for task in tasks:
                status_emoji = {
                    "completed": "✅",
                    "in_progress": "🔄",
                    "failed": "❌",
                    "pending": "⏰"
                }.get(task["status"], "❓")
                
                table.add_row(
                    task["id"][:8],
                    f"{status_emoji} {task['status']}",
                    f"{task.get('progress', 0)}%",
                    task.get('created_at', 'N/A')[:19]
                )
            
            console.print(table)
        else:
            console.print(f"[red]❌ Failed to fetch tasks[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

@cli.command()
@click.option('--port', '-p', default=3000, help='Port for mock server')
@click.argument('spec_file', type=click.Path(exists=True))
def mock(spec_file, port):
    """🎭 Start a mock server from OpenAPI spec
    
    Example:
        api-orchestrator mock ./openapi.json --port 3000
    """
    console.print(f"[green]🎭 Starting mock server on port {port}...[/green]")
    console.print(f"[cyan]📄 Using spec: {spec_file}[/cyan]")
    
    # This would start a mock server locally
    # For now, we'll show the endpoints
    try:
        with open(spec_file, 'r') as f:
            if spec_file.endswith('.yaml') or spec_file.endswith('.yml'):
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)
        
        console.print(f"\n[bold]Available endpoints:[/bold]")
        for path, methods in spec.get('paths', {}).items():
            for method in methods:
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    console.print(f"  [{method.upper()}] http://localhost:{port}{path}")
        
        console.print(f"\n[green]✅ Mock server would be running at http://localhost:{port}[/green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        
        # In real implementation, this would start an actual mock server
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Mock server stopped[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

@cli.command()
def config():
    """⚙️  Show current configuration"""
    config_table = Table(title="API Orchestrator Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("API URL", cli_instance.config.get("api_url", "Not set"))
    config_table.add_row("Email", cli_instance.config.get("email", "Not logged in"))
    config_table.add_row("Token", "***" if cli_instance.token else "Not set")
    config_table.add_row("Config File", str(CONFIG_FILE))
    
    console.print(config_table)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def init(path):
    """🎯 Initialize API Orchestrator in your project
    
    Creates .api-orchestrator.yml configuration file
    """
    config_path = Path(path) / ".api-orchestrator.yml"
    
    if config_path.exists():
        if not click.confirm("Configuration already exists. Overwrite?"):
            return
    
    config = {
        "version": "1.0",
        "framework": "auto",
        "output": "./api-output",
        "options": {
            "include_tests": True,
            "include_mock": True,
            "include_ai_analysis": True
        },
        "ignore": [
            "node_modules",
            ".git",
            "__pycache__",
            "*.pyc",
            ".env"
        ]
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    console.print(f"[green]✅ Created {config_path}[/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Edit .api-orchestrator.yml to customize settings")
    console.print("2. Run: api-orchestrator scan .")

if __name__ == '__main__':
    cli()