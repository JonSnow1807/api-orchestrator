"""
Plugin Marketplace - Extensibility beyond Postman
Create, share, and install plugins/extensions
"""

import uuid
import json
import hashlib
import subprocess
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import semver
import zipfile
from pathlib import Path


class PluginType(Enum):
    """Types of plugins"""

    INTEGRATION = "integration"  # Third-party service integrations
    TRANSFORMER = "transformer"  # Data transformation plugins
    VALIDATOR = "validator"  # Custom validation rules
    GENERATOR = "generator"  # Code/doc generators
    ANALYZER = "analyzer"  # API analysis tools
    MONITOR = "monitor"  # Monitoring and alerting
    SECURITY = "security"  # Security tools
    WORKFLOW = "workflow"  # Workflow automation
    UI_COMPONENT = "ui_component"  # UI extensions
    THEME = "theme"  # UI themes


class PluginStatus(Enum):
    """Plugin lifecycle status"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"


class PluginCategory(Enum):
    """Plugin categories"""

    PRODUCTIVITY = "productivity"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    DEVOPS = "devops"
    ANALYTICS = "analytics"
    COLLABORATION = "collaboration"
    UTILITIES = "utilities"


class PluginManifest(BaseModel):
    """Plugin manifest specification"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str  # Semantic versioning
    description: str
    author: str
    author_email: str
    license: str
    homepage: Optional[str] = None
    repository: Optional[str] = None

    type: PluginType
    category: PluginCategory
    tags: List[str] = []

    # Technical details
    runtime: str  # nodejs, python, go, etc.
    entry_point: str  # Main file/function
    dependencies: Dict[str, str] = {}  # Package dependencies

    # Compatibility
    min_app_version: str = "4.0.0"
    max_app_version: Optional[str] = None
    compatible_platforms: List[str] = ["windows", "macos", "linux"]

    # Permissions required
    permissions: List[str] = []  # network, filesystem, etc.
    api_access: List[str] = []  # Which APIs the plugin can access

    # Configuration schema
    config_schema: Optional[Dict[str, Any]] = None

    # UI integration
    ui_hooks: List[str] = []  # Where plugin adds UI elements
    menu_items: List[Dict[str, str]] = []  # Menu additions
    toolbar_buttons: List[Dict[str, str]] = []  # Toolbar additions

    # Assets
    icon: Optional[str] = None
    screenshots: List[str] = []
    readme: Optional[str] = "README.md"

    # Hooks and events
    activation_hooks: List[str] = []
    deactivation_hooks: List[str] = []
    event_subscriptions: List[str] = []


class Plugin(BaseModel):
    """Plugin model with metadata"""

    manifest: PluginManifest
    status: PluginStatus = PluginStatus.DRAFT

    # Publishing info
    publisher_id: str
    published_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    # Statistics
    downloads: int = 0
    active_installs: int = 0
    rating: float = 0.0
    reviews_count: int = 0

    # Verification
    verified: bool = False
    verified_by: Optional[str] = None
    security_scan_passed: bool = False
    security_scan_date: Optional[datetime] = None

    # Pricing
    price: float = 0.0  # 0 for free
    pricing_model: str = "free"  # free, one-time, subscription
    trial_days: int = 0

    # Files
    package_url: Optional[str] = None
    package_size: int = 0
    package_hash: Optional[str] = None

    # Installation
    install_count: int = 0
    last_install: Optional[datetime] = None


class PluginInstallation(BaseModel):
    """Plugin installation record"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plugin_id: str
    plugin_name: str
    plugin_version: str
    workspace_id: str
    user_id: str

    installed_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    enabled: bool = True
    config: Dict[str, Any] = {}

    # Runtime info
    last_activated: Optional[datetime] = None
    activation_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class PluginReview(BaseModel):
    """Plugin review/rating"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plugin_id: str
    user_id: str
    user_name: str

    rating: int  # 1-5 stars
    title: str
    comment: str

    helpful_count: int = 0
    verified_purchase: bool = False

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class PluginMarketplace:
    """Manage plugin marketplace"""

    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins: Dict[str, Plugin] = {}
        self.installations: Dict[str, List[PluginInstallation]] = {}
        self.reviews: Dict[str, List[PluginReview]] = {}
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)

        # Plugin runtime environments
        self.runtimes = {
            "nodejs": NodeJSRuntime(),
            "python": PythonRuntime(),
            "go": GoRuntime(),
        }

    async def publish_plugin(
        self, manifest: PluginManifest, package_path: str, publisher_id: str
    ) -> Plugin:
        """Publish a new plugin to marketplace"""

        # Validate manifest
        self._validate_manifest(manifest)

        # Validate package
        package_hash = self._calculate_package_hash(package_path)
        package_size = Path(package_path).stat().st_size

        # Security scan
        security_passed = await self._security_scan(package_path)

        # Create plugin
        plugin = Plugin(
            manifest=manifest,
            status=PluginStatus.PENDING_REVIEW,
            publisher_id=publisher_id,
            package_hash=package_hash,
            package_size=package_size,
            security_scan_passed=security_passed,
            security_scan_date=datetime.now() if security_passed else None,
        )

        # Store package
        stored_path = self._store_package(
            package_path, plugin.manifest.id, plugin.manifest.version
        )
        plugin.package_url = str(stored_path)

        # Add to registry
        self.plugins[plugin.manifest.id] = plugin

        # Auto-approve if security scan passed (for demo)
        if security_passed:
            plugin.status = PluginStatus.APPROVED
            plugin.verified = True

        return plugin

    async def install_plugin(
        self,
        plugin_id: str,
        workspace_id: str,
        user_id: str,
        config: Dict[str, Any] = None,
    ) -> PluginInstallation:
        """Install a plugin for a workspace"""

        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin = self.plugins[plugin_id]

        if (
            plugin.status != PluginStatus.PUBLISHED
            and plugin.status != PluginStatus.APPROVED
        ):
            raise ValueError(f"Plugin {plugin_id} is not available for installation")

        # Check compatibility
        if not self._check_compatibility(plugin.manifest):
            raise ValueError(
                f"Plugin {plugin_id} is not compatible with current version"
            )

        # Extract package
        install_dir = self.plugins_dir / "installed" / workspace_id / plugin_id
        install_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(plugin.package_url, "r") as zip_ref:
            zip_ref.extractall(install_dir)

        # Install dependencies
        await self._install_dependencies(plugin.manifest, install_dir)

        # Create installation record
        installation = PluginInstallation(
            plugin_id=plugin_id,
            plugin_name=plugin.manifest.name,
            plugin_version=plugin.manifest.version,
            workspace_id=workspace_id,
            user_id=user_id,
            config=config or {},
        )

        # Store installation
        if workspace_id not in self.installations:
            self.installations[workspace_id] = []
        self.installations[workspace_id].append(installation)

        # Update plugin stats
        plugin.downloads += 1
        plugin.active_installs += 1
        plugin.install_count += 1
        plugin.last_install = datetime.now()

        # Run activation hooks
        await self._run_activation_hooks(plugin.manifest, install_dir)

        return installation

    async def uninstall_plugin(self, plugin_id: str, workspace_id: str):
        """Uninstall a plugin"""

        if workspace_id not in self.installations:
            return

        # Find installation
        installation = None
        for inst in self.installations[workspace_id]:
            if inst.plugin_id == plugin_id:
                installation = inst
                break

        if not installation:
            return

        plugin = self.plugins.get(plugin_id)
        if plugin:
            # Run deactivation hooks
            install_dir = self.plugins_dir / "installed" / workspace_id / plugin_id
            if install_dir.exists():
                await self._run_deactivation_hooks(plugin.manifest, install_dir)

                # Remove installation directory
                shutil.rmtree(install_dir)

            # Update stats
            plugin.active_installs = max(0, plugin.active_installs - 1)

        # Remove installation record
        self.installations[workspace_id] = [
            inst
            for inst in self.installations[workspace_id]
            if inst.plugin_id != plugin_id
        ]

    async def execute_plugin(
        self,
        plugin_id: str,
        workspace_id: str,
        action: str,
        params: Dict[str, Any] = None,
    ) -> Any:
        """Execute a plugin action"""

        # Find installation
        if workspace_id not in self.installations:
            raise ValueError(f"No plugins installed for workspace {workspace_id}")

        installation = None
        for inst in self.installations[workspace_id]:
            if inst.plugin_id == plugin_id:
                installation = inst
                break

        if not installation:
            raise ValueError(f"Plugin {plugin_id} not installed")

        if not installation.enabled:
            raise ValueError(f"Plugin {plugin_id} is disabled")

        plugin = self.plugins[plugin_id]

        # Get runtime
        runtime = self.runtimes.get(plugin.manifest.runtime)
        if not runtime:
            raise ValueError(f"Runtime {plugin.manifest.runtime} not supported")

        # Execute
        install_dir = self.plugins_dir / "installed" / workspace_id / plugin_id

        try:
            result = await runtime.execute(
                plugin.manifest, install_dir, action, params, installation.config
            )

            # Update stats
            installation.last_activated = datetime.now()
            installation.activation_count += 1

            return result

        except Exception as e:
            installation.error_count += 1
            installation.last_error = str(e)
            raise

    async def search_plugins(
        self,
        query: Optional[str] = None,
        type: Optional[PluginType] = None,
        category: Optional[PluginCategory] = None,
        tags: Optional[List[str]] = None,
        min_rating: float = 0.0,
        max_price: Optional[float] = None,
        sort_by: str = "downloads",  # downloads, rating, name, updated
    ) -> List[Plugin]:
        """Search plugins in marketplace"""

        results = []

        for plugin in self.plugins.values():
            # Filter by status
            if plugin.status not in [PluginStatus.PUBLISHED, PluginStatus.APPROVED]:
                continue

            # Filter by type
            if type and plugin.manifest.type != type:
                continue

            # Filter by category
            if category and plugin.manifest.category != category:
                continue

            # Filter by tags
            if tags and not any(tag in plugin.manifest.tags for tag in tags):
                continue

            # Filter by rating
            if plugin.rating < min_rating:
                continue

            # Filter by price
            if max_price is not None and plugin.price > max_price:
                continue

            # Search query
            if query:
                query_lower = query.lower()
                if not any(
                    query_lower in field.lower()
                    for field in [
                        plugin.manifest.name,
                        plugin.manifest.description,
                        plugin.manifest.author,
                    ]
                    + plugin.manifest.tags
                ):
                    continue

            results.append(plugin)

        # Sort results
        if sort_by == "downloads":
            results.sort(key=lambda x: x.downloads, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "name":
            results.sort(key=lambda x: x.manifest.name)
        elif sort_by == "updated":
            results.sort(key=lambda x: x.updated_at, reverse=True)

        return results

    async def add_review(
        self,
        plugin_id: str,
        user_id: str,
        user_name: str,
        rating: int,
        title: str,
        comment: str,
    ) -> PluginReview:
        """Add a review for a plugin"""

        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        review = PluginReview(
            plugin_id=plugin_id,
            user_id=user_id,
            user_name=user_name,
            rating=rating,
            title=title,
            comment=comment,
        )

        if plugin_id not in self.reviews:
            self.reviews[plugin_id] = []
        self.reviews[plugin_id].append(review)

        # Update plugin rating
        plugin = self.plugins[plugin_id]
        all_ratings = [r.rating for r in self.reviews[plugin_id]]
        plugin.rating = sum(all_ratings) / len(all_ratings)
        plugin.reviews_count = len(all_ratings)

        return review

    async def get_plugin_details(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed plugin information"""

        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin = self.plugins[plugin_id]

        # Get reviews
        plugin_reviews = self.reviews.get(plugin_id, [])

        return {
            "plugin": plugin.dict(),
            "reviews": [r.dict() for r in plugin_reviews[-10:]],  # Last 10 reviews
            "stats": {
                "total_downloads": plugin.downloads,
                "active_installs": plugin.active_installs,
                "average_rating": plugin.rating,
                "total_reviews": plugin.reviews_count,
            },
            "compatibility": {
                "current_version_compatible": self._check_compatibility(
                    plugin.manifest
                ),
                "platforms": plugin.manifest.compatible_platforms,
                "min_version": plugin.manifest.min_app_version,
                "max_version": plugin.manifest.max_app_version,
            },
        }

    def _validate_manifest(self, manifest: PluginManifest):
        """Validate plugin manifest"""

        # Validate version
        try:
            semver.VersionInfo.parse(manifest.version)
        except ValueError:
            raise ValueError(f"Invalid version format: {manifest.version}")

        # Validate required fields
        if not manifest.name:
            raise ValueError("Plugin name is required")

        if not manifest.entry_point:
            raise ValueError("Entry point is required")

        # Validate permissions
        valid_permissions = [
            "network",
            "filesystem",
            "process",
            "system",
            "clipboard",
            "notifications",
            "camera",
            "microphone",
        ]
        for perm in manifest.permissions:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")

    def _calculate_package_hash(self, package_path: str) -> str:
        """Calculate SHA256 hash of package"""
        sha256_hash = hashlib.sha256()
        with open(package_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _store_package(self, package_path: str, plugin_id: str, version: str) -> Path:
        """Store plugin package"""
        packages_dir = self.plugins_dir / "packages"
        packages_dir.mkdir(exist_ok=True)

        dest_path = packages_dir / f"{plugin_id}_{version}.zip"
        shutil.copy2(package_path, dest_path)

        return dest_path

    def _check_compatibility(self, manifest: PluginManifest) -> bool:
        """Check if plugin is compatible with current version"""
        current_version = "4.0.0"  # Current app version

        min_version = semver.VersionInfo.parse(manifest.min_app_version)
        current = semver.VersionInfo.parse(current_version)

        if current < min_version:
            return False

        if manifest.max_app_version:
            max_version = semver.VersionInfo.parse(manifest.max_app_version)
            if current > max_version:
                return False

        return True

    async def _security_scan(self, package_path: str) -> bool:
        """Perform security scan on plugin package"""
        # Basic security checks
        try:
            with zipfile.ZipFile(package_path, "r") as zip_ref:
                for file_info in zip_ref.filelist:
                    # Check for suspicious files
                    if file_info.filename.startswith("/") or ".." in file_info.filename:
                        return False

                    # Check file size
                    if file_info.file_size > 100 * 1024 * 1024:  # 100MB limit
                        return False

            return True
        except Exception:
            return False

    async def _install_dependencies(self, manifest: PluginManifest, install_dir: Path):
        """Install plugin dependencies"""
        if manifest.runtime == "nodejs" and manifest.dependencies:
            # Create package.json
            package_json = {
                "name": manifest.name,
                "version": manifest.version,
                "dependencies": manifest.dependencies,
            }

            with open(install_dir / "package.json", "w") as f:
                json.dump(package_json, f)

            # Run npm install
            subprocess.run(["npm", "install"], cwd=install_dir, check=True)

        elif manifest.runtime == "python" and manifest.dependencies:
            # Create requirements.txt
            with open(install_dir / "requirements.txt", "w") as f:
                for pkg, version in manifest.dependencies.items():
                    f.write(f"{pkg}{version}\n")

            # Run pip install
            subprocess.run(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=install_dir,
                check=True,
            )

    async def _run_activation_hooks(self, manifest: PluginManifest, install_dir: Path):
        """Run plugin activation hooks"""
        for hook in manifest.activation_hooks:
            # Execute hook
            pass

    async def _run_deactivation_hooks(
        self, manifest: PluginManifest, install_dir: Path
    ):
        """Run plugin deactivation hooks"""
        for hook in manifest.deactivation_hooks:
            # Execute hook
            pass


class PluginRuntime:
    """Base class for plugin runtime"""

    async def execute(
        self,
        manifest: PluginManifest,
        install_dir: Path,
        action: str,
        params: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Any:
        raise NotImplementedError


class NodeJSRuntime(PluginRuntime):
    """Node.js plugin runtime"""

    async def execute(
        self,
        manifest: PluginManifest,
        install_dir: Path,
        action: str,
        params: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Any:
        # Execute Node.js plugin
        script = f"""
        const plugin = require('./{manifest.entry_point}');
        const result = plugin.{action}({json.dumps(params)}, {json.dumps(config)});
        console.log(JSON.stringify(result));
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(script)
            script_path = f.name

        try:
            result = subprocess.run(
                ["node", script_path],
                cwd=install_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        finally:
            Path(script_path).unlink()


class PythonRuntime(PluginRuntime):
    """Python plugin runtime"""

    async def execute(
        self,
        manifest: PluginManifest,
        install_dir: Path,
        action: str,
        params: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Any:
        # Execute Python plugin
        script = f"""
import sys
import json
sys.path.insert(0, '{install_dir}')
from {manifest.entry_point.replace('.py', '')} import {action}
result = {action}({params}, {config})
print(json.dumps(result))
        """

        result = subprocess.run(
            ["python", "-c", script],
            cwd=install_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)


class GoRuntime(PluginRuntime):
    """Go plugin runtime"""

    async def execute(
        self,
        manifest: PluginManifest,
        install_dir: Path,
        action: str,
        params: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Any:
        # Execute Go plugin (compiled)
        binary_path = install_dir / manifest.entry_point

        result = subprocess.run(
            [str(binary_path), action, json.dumps(params), json.dumps(config)],
            cwd=install_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)


# Global marketplace instance
plugin_marketplace = PluginMarketplace()
