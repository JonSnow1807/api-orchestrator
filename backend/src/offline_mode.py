"""
Offline-First Mode
Store collections in plain text files for Git-friendly version control
Competitive with Bruno's offline capabilities
"""

import os
import json
import yaml
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiofiles
import git

class StorageFormat(Enum):
    """Storage format for offline collections"""
    BRU = "bru"  # Bruno-compatible format
    JSON = "json"  # JSON format
    YAML = "yaml"  # YAML format
    HTTP = "http"  # .http file format (VS Code REST Client)
    MARKDOWN = "md"  # Markdown with embedded requests

@dataclass
class OfflineRequest:
    """Offline request representation"""
    id: str
    name: str
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[str] = None
    params: Optional[Dict[str, str]] = None
    auth: Optional[Dict[str, Any]] = None
    tests: Optional[List[str]] = None
    preRequestScript: Optional[str] = None
    postResponseScript: Optional[str] = None
    description: Optional[str] = None
    folder: Optional[str] = None
    
    def to_bru(self) -> str:
        """Convert to Bruno format (.bru file)"""
        lines = []
        
        # Meta section
        lines.append("meta {")
        lines.append(f"  name: {self.name}")
        lines.append(f"  type: http")
        lines.append(f"  seq: 1")
        lines.append("}")
        lines.append("")
        
        # Request section
        lines.append(f"{self.method.lower()} " + "{")
        lines.append(f"  url: {self.url}")
        
        # Headers
        if self.headers:
            lines.append("  headers {")
            for key, value in self.headers.items():
                lines.append(f"    {key}: {value}")
            lines.append("  }")
        
        # Body
        if self.body:
            lines.append("  body {")
            if isinstance(self.body, dict):
                lines.append("    mode: json")
                lines.append("    json: " + json.dumps(self.body))
            else:
                lines.append("    mode: raw")
                lines.append(f"    raw: {self.body}")
            lines.append("  }")
        
        # Auth
        if self.auth:
            lines.append("  auth {")
            for key, value in self.auth.items():
                lines.append(f"    {key}: {value}")
            lines.append("  }")
        
        lines.append("}")
        lines.append("")
        
        # Scripts
        if self.preRequestScript:
            lines.append("script:pre-request {")
            lines.append(self.preRequestScript)
            lines.append("}")
            lines.append("")
        
        if self.tests:
            lines.append("tests {")
            for test in self.tests:
                lines.append(f"  {test}")
            lines.append("}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_http(self) -> str:
        """Convert to .http file format"""
        lines = []
        
        # Comment with name and description
        if self.name:
            lines.append(f"### {self.name}")
        if self.description:
            lines.append(f"# {self.description}")
        
        # Request line
        lines.append(f"{self.method} {self.url}")
        
        # Headers
        if self.headers:
            for key, value in self.headers.items():
                lines.append(f"{key}: {value}")
        
        # Empty line before body
        if self.body:
            lines.append("")
            lines.append(self.body)
        
        lines.append("")
        lines.append("###")
        lines.append("")
        
        return "\n".join(lines)
    
    def to_markdown(self) -> str:
        """Convert to Markdown format"""
        lines = []
        
        # Title
        lines.append(f"## {self.name}")
        lines.append("")
        
        # Description
        if self.description:
            lines.append(self.description)
            lines.append("")
        
        # Request details
        lines.append("**Request:**")
        lines.append("```http")
        lines.append(f"{self.method} {self.url}")
        
        if self.headers:
            for key, value in self.headers.items():
                lines.append(f"{key}: {value}")
        
        if self.body:
            lines.append("")
            lines.append(self.body)
        
        lines.append("```")
        lines.append("")
        
        # Tests
        if self.tests:
            lines.append("**Tests:**")
            lines.append("```javascript")
            for test in self.tests:
                lines.append(test)
            lines.append("```")
            lines.append("")
        
        return "\n".join(lines)

@dataclass
class OfflineCollection:
    """Offline collection representation"""
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    requests: List[OfflineRequest] = None
    folders: List[Dict[str, Any]] = None
    environments: List[Dict[str, Any]] = None
    variables: Dict[str, Any] = None
    auth: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.requests is None:
            self.requests = []
        if self.folders is None:
            self.folders = []
        if self.environments is None:
            self.environments = []
        if self.variables is None:
            self.variables = {}

class OfflineManager:
    """Manage offline-first API collections"""
    
    def __init__(self, base_path: str = "./api-collections"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.git_enabled = self._check_git()
        self.sync_queue = []
        self.file_watchers = {}
        
    def _check_git(self) -> bool:
        """Check if Git is available and initialized"""
        try:
            self.repo = git.Repo(self.base_path)
            return True
        except:
            try:
                # Try to initialize git repo
                self.repo = git.Repo.init(self.base_path)
                return True
            except:
                return False
    
    async def save_collection(
        self,
        collection: OfflineCollection,
        format: StorageFormat = StorageFormat.BRU
    ) -> str:
        """Save collection to disk in specified format"""
        
        collection_path = self.base_path / collection.name.replace(" ", "_").lower()
        collection_path.mkdir(parents=True, exist_ok=True)
        
        if format == StorageFormat.BRU:
            return await self._save_as_bru(collection, collection_path)
        elif format == StorageFormat.JSON:
            return await self._save_as_json(collection, collection_path)
        elif format == StorageFormat.YAML:
            return await self._save_as_yaml(collection, collection_path)
        elif format == StorageFormat.HTTP:
            return await self._save_as_http(collection, collection_path)
        elif format == StorageFormat.MARKDOWN:
            return await self._save_as_markdown(collection, collection_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def _save_as_bru(self, collection: OfflineCollection, path: Path) -> str:
        """Save collection in Bruno format"""
        
        # Save collection metadata
        bruno_json = {
            "version": "1",
            "name": collection.name,
            "type": "collection",
            "ignore": ["node_modules", ".git"]
        }
        
        async with aiofiles.open(path / "bruno.json", "w") as f:
            await f.write(json.dumps(bruno_json, indent=2))
        
        # Save each request as .bru file
        for request in collection.requests:
            folder = path / (request.folder or "")
            folder.mkdir(parents=True, exist_ok=True)
            
            filename = f"{request.name.replace(' ', '_').lower()}.bru"
            filepath = folder / filename
            
            async with aiofiles.open(filepath, "w") as f:
                await f.write(request.to_bru())
        
        # Save environments
        if collection.environments:
            env_path = path / "environments"
            env_path.mkdir(exist_ok=True)
            
            for env in collection.environments:
                env_file = env_path / f"{env['name']}.bru"
                async with aiofiles.open(env_file, "w") as f:
                    await f.write(self._format_environment_bru(env))
        
        # Git commit if enabled
        if self.git_enabled:
            await self._git_commit(path, f"Save collection: {collection.name}")
        
        return str(path)
    
    async def _save_as_json(self, collection: OfflineCollection, path: Path) -> str:
        """Save collection as JSON"""
        
        collection_file = path / f"{collection.name}.json"
        
        data = {
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "version": collection.version,
            "requests": [asdict(r) for r in collection.requests],
            "folders": collection.folders,
            "environments": collection.environments,
            "variables": collection.variables,
            "auth": collection.auth
        }
        
        async with aiofiles.open(collection_file, "w") as f:
            await f.write(json.dumps(data, indent=2))
        
        if self.git_enabled:
            await self._git_commit(path, f"Save collection: {collection.name}")
        
        return str(collection_file)
    
    async def _save_as_yaml(self, collection: OfflineCollection, path: Path) -> str:
        """Save collection as YAML"""
        
        collection_file = path / f"{collection.name}.yaml"
        
        data = {
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "version": collection.version,
            "requests": [asdict(r) for r in collection.requests],
            "folders": collection.folders,
            "environments": collection.environments,
            "variables": collection.variables,
            "auth": collection.auth
        }
        
        async with aiofiles.open(collection_file, "w") as f:
            await f.write(yaml.dump(data, default_flow_style=False))
        
        if self.git_enabled:
            await self._git_commit(path, f"Save collection: {collection.name}")
        
        return str(collection_file)
    
    async def _save_as_http(self, collection: OfflineCollection, path: Path) -> str:
        """Save collection as .http files"""
        
        # Group requests by folder
        for request in collection.requests:
            folder = path / (request.folder or "")
            folder.mkdir(parents=True, exist_ok=True)
            
            filename = f"{request.name.replace(' ', '_').lower()}.http"
            filepath = folder / filename
            
            async with aiofiles.open(filepath, "w") as f:
                await f.write(request.to_http())
        
        # Save variables as .env file
        if collection.variables:
            env_file = path / ".env"
            async with aiofiles.open(env_file, "w") as f:
                for key, value in collection.variables.items():
                    await f.write(f"{key}={value}\n")
        
        if self.git_enabled:
            await self._git_commit(path, f"Save collection: {collection.name}")
        
        return str(path)
    
    async def _save_as_markdown(self, collection: OfflineCollection, path: Path) -> str:
        """Save collection as Markdown documentation"""
        
        readme_file = path / "README.md"
        
        lines = []
        lines.append(f"# {collection.name}")
        lines.append("")
        
        if collection.description:
            lines.append(collection.description)
            lines.append("")
        
        lines.append("## API Endpoints")
        lines.append("")
        
        # Group by folder
        folders = {}
        for request in collection.requests:
            folder = request.folder or "General"
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(request)
        
        for folder, requests in folders.items():
            lines.append(f"### {folder}")
            lines.append("")
            
            for request in requests:
                lines.append(request.to_markdown())
        
        async with aiofiles.open(readme_file, "w") as f:
            await f.write("\n".join(lines))
        
        if self.git_enabled:
            await self._git_commit(path, f"Update documentation: {collection.name}")
        
        return str(readme_file)
    
    async def load_collection(self, path: str) -> OfflineCollection:
        """Load collection from disk"""
        
        path = Path(path)
        
        # Detect format
        if (path / "bruno.json").exists():
            return await self._load_bru_collection(path)
        elif path.suffix == ".json":
            return await self._load_json_collection(path)
        elif path.suffix == ".yaml":
            return await self._load_yaml_collection(path)
        else:
            # Try to detect from files
            http_files = list(path.glob("**/*.http"))
            if http_files:
                return await self._load_http_collection(path)
            
        raise ValueError(f"Cannot detect collection format at {path}")
    
    async def _load_bru_collection(self, path: Path) -> OfflineCollection:
        """Load Bruno format collection"""
        
        # Load metadata
        async with aiofiles.open(path / "bruno.json", "r") as f:
            metadata = json.loads(await f.read())
        
        collection = OfflineCollection(
            id=hashlib.md5(str(path).encode()).hexdigest(),
            name=metadata["name"]
        )
        
        # Load requests
        for bru_file in path.glob("**/*.bru"):
            if "environments" in str(bru_file):
                continue
            
            async with aiofiles.open(bru_file, "r") as f:
                content = await f.read()
            
            request = self._parse_bru_request(content)
            request.folder = bru_file.parent.name if bru_file.parent != path else None
            collection.requests.append(request)
        
        # Load environments
        env_path = path / "environments"
        if env_path.exists():
            for env_file in env_path.glob("*.bru"):
                async with aiofiles.open(env_file, "r") as f:
                    content = await f.read()
                
                env = self._parse_bru_environment(content)
                collection.environments.append(env)
        
        return collection
    
    async def _load_json_collection(self, path: Path) -> OfflineCollection:
        """Load JSON format collection"""
        
        async with aiofiles.open(path, "r") as f:
            data = json.loads(await f.read())
        
        collection = OfflineCollection(
            id=data.get("id", hashlib.md5(str(path).encode()).hexdigest()),
            name=data["name"],
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            folders=data.get("folders", []),
            environments=data.get("environments", []),
            variables=data.get("variables", {}),
            auth=data.get("auth")
        )
        
        # Convert requests
        for req_data in data.get("requests", []):
            request = OfflineRequest(**req_data)
            collection.requests.append(request)
        
        return collection
    
    async def _load_yaml_collection(self, path: Path) -> OfflineCollection:
        """Load YAML format collection"""
        
        async with aiofiles.open(path, "r") as f:
            data = yaml.safe_load(await f.read())
        
        collection = OfflineCollection(
            id=data.get("id", hashlib.md5(str(path).encode()).hexdigest()),
            name=data["name"],
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            folders=data.get("folders", []),
            environments=data.get("environments", []),
            variables=data.get("variables", {}),
            auth=data.get("auth")
        )
        
        # Convert requests
        for req_data in data.get("requests", []):
            request = OfflineRequest(**req_data)
            collection.requests.append(request)
        
        return collection
    
    async def _load_http_collection(self, path: Path) -> OfflineCollection:
        """Load .http files as collection"""
        
        collection = OfflineCollection(
            id=hashlib.md5(str(path).encode()).hexdigest(),
            name=path.name
        )
        
        # Load .env file if exists
        env_file = path / ".env"
        if env_file.exists():
            async with aiofiles.open(env_file, "r") as f:
                for line in (await f.read()).split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        collection.variables[key.strip()] = value.strip()
        
        # Load all .http files
        for http_file in path.glob("**/*.http"):
            async with aiofiles.open(http_file, "r") as f:
                content = await f.read()
            
            requests = self._parse_http_file(content)
            for request in requests:
                request.folder = http_file.parent.name if http_file.parent != path else None
                collection.requests.append(request)
        
        return collection
    
    def _parse_bru_request(self, content: str) -> OfflineRequest:
        """Parse a .bru file into a request"""
        
        # Simple parser for Bruno format
        request = OfflineRequest(
            id=hashlib.md5(content.encode()).hexdigest()[:8],
            name="Unnamed Request",
            method="GET",
            url="",
            headers={}
        )
        
        # Parse sections
        lines = content.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("meta {"):
                current_section = "meta"
            elif line.startswith("get {") or line.startswith("post {") or line.startswith("put {"):
                request.method = line.split()[0].upper()
                current_section = "request"
            elif line.startswith("headers {"):
                current_section = "headers"
            elif line.startswith("body {"):
                current_section = "body"
            elif line.startswith("}"):
                current_section = None
            elif current_section and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if current_section == "meta" and key == "name":
                    request.name = value
                elif current_section == "request" and key == "url":
                    request.url = value
                elif current_section == "headers":
                    request.headers[key] = value
                elif current_section == "body" and key == "raw":
                    request.body = value
        
        return request
    
    def _parse_http_file(self, content: str) -> List[OfflineRequest]:
        """Parse .http file into requests"""
        
        requests = []
        sections = content.split("###")
        
        for section in sections:
            if not section.strip():
                continue
            
            lines = section.strip().split("\n")
            if not lines:
                continue
            
            # Parse request line
            first_line = lines[0].strip()
            if not any(method in first_line for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]):
                continue
            
            parts = first_line.split()
            if len(parts) < 2:
                continue
            
            method = parts[0]
            url = parts[1]
            
            # Parse headers and body
            headers = {}
            body = None
            body_start = -1
            
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "":
                    body_start = i + 1
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
            
            if body_start > 0 and body_start < len(lines):
                body = "\n".join(lines[body_start:])
            
            request = OfflineRequest(
                id=hashlib.md5(section.encode()).hexdigest()[:8],
                name=f"{method} {url}",
                method=method,
                url=url,
                headers=headers,
                body=body
            )
            
            requests.append(request)
        
        return requests
    
    def _parse_bru_environment(self, content: str) -> Dict[str, Any]:
        """Parse Bruno environment file"""
        
        env = {
            "name": "default",
            "variables": {}
        }
        
        # Simple parser
        for line in content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "name":
                    env["name"] = value
                else:
                    env["variables"][key] = value
        
        return env
    
    def _format_environment_bru(self, env: Dict[str, Any]) -> str:
        """Format environment as Bruno file"""
        
        lines = []
        lines.append("vars {")
        
        for key, value in env.get("variables", {}).items():
            lines.append(f"  {key}: {value}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    async def _git_commit(self, path: Path, message: str):
        """Commit changes to Git"""
        
        if not self.git_enabled:
            return
        
        try:
            # Add all files in path
            self.repo.index.add([str(path)])
            
            # Commit
            self.repo.index.commit(message)
        except Exception as e:
            print(f"Git commit failed: {e}")
    
    async def sync_with_server(self, server_url: str, auth_token: str):
        """Sync offline collections with server"""
        
        # Queue sync operation
        self.sync_queue.append({
            "server_url": server_url,
            "auth_token": auth_token,
            "timestamp": datetime.utcnow()
        })
        
        # Process sync queue
        await self._process_sync_queue()
    
    async def _process_sync_queue(self):
        """Process pending sync operations"""
        
        while self.sync_queue:
            sync_op = self.sync_queue.pop(0)
            
            try:
                # Sync logic here
                # This would upload/download collections to/from server
                pass
            except Exception as e:
                print(f"Sync failed: {e}")
                # Re-queue for retry
                self.sync_queue.append(sync_op)
    
    async def watch_for_changes(self, path: str, callback):
        """Watch collection files for changes"""
        
        import watchdog.observers
        import watchdog.events
        
        class Handler(watchdog.events.FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory:
                    asyncio.create_task(callback(event.src_path))
        
        observer = watchdog.observers.Observer()
        observer.schedule(Handler(), path, recursive=True)
        observer.start()
        
        self.file_watchers[path] = observer
    
    def export_to_postman(self, collection: OfflineCollection) -> Dict[str, Any]:
        """Export collection to Postman format"""
        
        postman_collection = {
            "info": {
                "_postman_id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [],
            "variable": []
        }
        
        # Convert requests
        for request in collection.requests:
            item = {
                "name": request.name,
                "request": {
                    "method": request.method,
                    "url": request.url,
                    "header": [
                        {"key": k, "value": v}
                        for k, v in request.headers.items()
                    ]
                }
            }
            
            if request.body:
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": request.body
                }
            
            postman_collection["item"].append(item)
        
        # Convert variables
        for key, value in collection.variables.items():
            postman_collection["variable"].append({
                "key": key,
                "value": value
            })
        
        return postman_collection
    
    def import_from_postman(self, postman_data: Dict[str, Any]) -> OfflineCollection:
        """Import Postman collection"""
        
        info = postman_data.get("info", {})
        
        collection = OfflineCollection(
            id=info.get("_postman_id", hashlib.md5(json.dumps(postman_data).encode()).hexdigest()),
            name=info.get("name", "Imported Collection"),
            description=info.get("description")
        )
        
        # Import items
        def process_items(items, folder=None):
            for item in items:
                if "item" in item:
                    # It's a folder
                    process_items(item["item"], item.get("name"))
                elif "request" in item:
                    # It's a request
                    req = item["request"]
                    
                    headers = {}
                    for header in req.get("header", []):
                        headers[header.get("key", "")] = header.get("value", "")
                    
                    body = None
                    if "body" in req:
                        if req["body"].get("mode") == "raw":
                            body = req["body"].get("raw")
                    
                    request = OfflineRequest(
                        id=hashlib.md5(json.dumps(item).encode()).hexdigest()[:8],
                        name=item.get("name", "Unnamed"),
                        method=req.get("method", "GET"),
                        url=req.get("url", {}).get("raw", "") if isinstance(req.get("url"), dict) else req.get("url", ""),
                        headers=headers,
                        body=body,
                        folder=folder
                    )
                    
                    collection.requests.append(request)
        
        process_items(postman_data.get("item", []))
        
        # Import variables
        for var in postman_data.get("variable", []):
            collection.variables[var.get("key", "")] = var.get("value", "")
        
        return collection

# Export for use
__all__ = ['OfflineManager', 'OfflineCollection', 'OfflineRequest', 'StorageFormat']