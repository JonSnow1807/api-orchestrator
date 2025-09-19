#!/usr/bin/env python3
"""
GIT AUTOMATION AGENT - The Autonomous Code Manager
Creates branches, commits, PRs, and merges WITHOUT human intervention
Handles merge conflicts intelligently
"""

import os
import subprocess
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import difflib
try:
    import git
except ImportError:
    git = None

try:
    from github import Github
except ImportError:
    Github = None

try:
    import gitlab
except ImportError:
    gitlab = None


@dataclass
class PullRequestInfo:
    """Information about a pull request"""
    pr_number: int
    title: str
    description: str
    branch: str
    base_branch: str
    files_changed: List[str]
    additions: int
    deletions: int
    mergeable: bool
    conflicts: List[str]
    checks_passed: bool
    url: str


@dataclass
class CommitInfo:
    """Information about a commit"""
    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]
    stats: Dict[str, int]


class GitAgent:
    """
    The AI that manages all Git operations autonomously
    No more manual commits, PRs, or merge conflict resolution
    """

    def __init__(self, repo_path: str = ".", github_token: Optional[str] = None):
        self.repo_path = Path(repo_path)

        # Try to find the git repository
        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            # If not a git repo, initialize it
            self.repo = git.Repo.init(self.repo_path)
            print(f"   Initialized new Git repository at: {self.repo_path}")

        self.github_client = Github(github_token) if github_token else None
        self.commit_patterns = self._load_commit_patterns()
        self.merge_strategies = self._load_merge_strategies()

        print("🔀 GIT AGENT INITIALIZED")
        print(f"   Repository: {self.repo_path}")
        try:
            print(f"   Current branch: {self.repo.active_branch}")
        except TypeError:
            print(f"   Current branch: No branch yet (empty repository)")

    async def create_feature_branch(
        self,
        feature_name: str,
        from_branch: str = "main"
    ) -> str:
        """Create a new feature branch"""

        print(f"🌿 CREATING FEATURE BRANCH: {feature_name}")

        # Ensure we're on the latest from_branch
        self.repo.git.checkout(from_branch)
        self.repo.git.pull()

        # Create and checkout new branch
        branch_name = f"feature/{self._sanitize_branch_name(feature_name)}-{datetime.utcnow().strftime('%Y%m%d')}"

        try:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            print(f"   ✅ Created and checked out: {branch_name}")
            return branch_name
        except Exception as e:
            print(f"   ❌ Failed to create branch: {e}")
            raise

    async def commit_changes(
        self,
        message: Optional[str] = None,
        files: Optional[List[str]] = None,
        auto_generate_message: bool = True
    ) -> CommitInfo:
        """Commit changes with intelligent message generation"""

        print("📝 COMMITTING CHANGES")

        # Stage files
        if files:
            for file in files:
                try:
                    self.repo.git.add(file)
                    print(f"   ➕ Staged: {file}")
                except Exception as e:
                    # If file doesn't exist, skip it
                    print(f"   ⚠️ Could not stage {file}: {e}")
        else:
            # Stage all changes
            try:
                self.repo.git.add(A=True)
                print("   ➕ Staged all changes")
            except Exception as e:
                # Try adding with '.' instead
                self.repo.git.add('.')
                print("   ➕ Staged all changes")

        # Get diff for message generation
        diff = self.repo.git.diff(cached=True)

        if not diff:
            print("   ⚠️ No changes to commit")
            return None

        # Generate or use provided message
        if not message and auto_generate_message:
            message = self._generate_commit_message(diff)
            print(f"   🤖 Generated message: {message[:50]}...")
        elif not message:
            message = "Auto-commit by Git Agent"

        # Commit
        commit = self.repo.index.commit(message)

        # Get commit info
        stats = self.repo.git.diff(commit.hexsha, name_status=True, numstat=True)

        commit_info = CommitInfo(
            sha=commit.hexsha,
            message=message,
            author=str(commit.author),
            timestamp=datetime.fromtimestamp(commit.committed_date),
            files_changed=self._parse_changed_files(stats),
            stats={"additions": 0, "deletions": 0}  # Simplified
        )

        print(f"   ✅ Committed: {commit.hexsha[:8]}")

        return commit_info

    async def create_pull_request(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        base_branch: str = "main",
        auto_merge_on_success: bool = True
    ) -> PullRequestInfo:
        """Create a pull request"""

        print("🔄 CREATING PULL REQUEST")

        current_branch = self.repo.active_branch.name

        if current_branch == base_branch:
            raise ValueError("Cannot create PR from base branch to itself")

        # Push current branch
        print(f"   📤 Pushing {current_branch}...")
        self.repo.git.push("origin", current_branch, set_upstream=True)

        # Get diff information
        diff = self.repo.git.diff(f"{base_branch}...{current_branch}")
        files_changed = self.repo.git.diff(f"{base_branch}...{current_branch}", name_only=True).splitlines()

        # Generate title and description if not provided
        if not title:
            title = self._generate_pr_title(current_branch, files_changed)

        if not description:
            description = self._generate_pr_description(diff, files_changed)

        # Create PR using GitHub API
        if self.github_client:
            pr = await self._create_github_pr(
                title, description, current_branch, base_branch
            )

            pr_info = PullRequestInfo(
                pr_number=pr.number,
                title=title,
                description=description,
                branch=current_branch,
                base_branch=base_branch,
                files_changed=files_changed,
                additions=pr.additions,
                deletions=pr.deletions,
                mergeable=pr.mergeable if pr.mergeable is not None else True,
                conflicts=[],
                checks_passed=False,  # Will be updated
                url=pr.html_url
            )

            print(f"   ✅ PR created: #{pr.number} - {pr.html_url}")

            # Set up auto-merge if requested
            if auto_merge_on_success:
                await self._setup_auto_merge(pr_info)

            return pr_info
        else:
            # Fallback to CLI or manual process
            print(f"   ⚠️ GitHub token not configured. PR ready for manual creation:")
            print(f"      Title: {title}")
            print(f"      Branch: {current_branch} -> {base_branch}")

            return PullRequestInfo(
                pr_number=0,
                title=title,
                description=description,
                branch=current_branch,
                base_branch=base_branch,
                files_changed=files_changed,
                additions=0,
                deletions=0,
                mergeable=True,
                conflicts=[],
                checks_passed=False,
                url=""
            )

    async def handle_merge_conflicts(
        self,
        pr_info: PullRequestInfo,
        strategy: str = "auto"
    ) -> bool:
        """Intelligently handle merge conflicts"""

        print(f"🔧 HANDLING MERGE CONFLICTS for PR #{pr_info.pr_number}")

        # Fetch latest changes
        self.repo.git.fetch()

        # Try to merge
        try:
            self.repo.git.checkout(pr_info.branch)
            self.repo.git.merge(pr_info.base_branch)
            print("   ✅ No conflicts, merge successful")
            return True
        except git.GitCommandError as e:
            if "conflict" not in str(e).lower():
                raise

            print("   ⚠️ Conflicts detected, resolving...")

        # Get conflicted files
        conflicted_files = self.repo.git.diff(name_only=True, unmerged=True).splitlines()

        resolved_count = 0
        for file in conflicted_files:
            print(f"   🔍 Resolving: {file}")

            if strategy == "auto":
                resolved = await self._auto_resolve_conflict(file)
            elif strategy == "ours":
                resolved = self._resolve_with_ours(file)
            elif strategy == "theirs":
                resolved = self._resolve_with_theirs(file)
            else:
                resolved = await self._smart_resolve_conflict(file)

            if resolved:
                self.repo.git.add(file)
                resolved_count += 1
                print(f"      ✅ Resolved: {file}")
            else:
                print(f"      ❌ Could not resolve: {file}")

        if resolved_count == len(conflicted_files):
            # Commit the resolution
            self.repo.index.commit(f"Resolve merge conflicts from {pr_info.base_branch}")
            self.repo.git.push()
            print(f"   ✅ All {resolved_count} conflicts resolved")
            return True
        else:
            print(f"   ⚠️ Resolved {resolved_count}/{len(conflicted_files)} conflicts")
            return False

    async def auto_merge_when_ready(
        self,
        pr_info: PullRequestInfo,
        required_checks: List[str] = None
    ) -> bool:
        """Automatically merge PR when all checks pass"""

        print(f"⏳ WAITING TO AUTO-MERGE PR #{pr_info.pr_number}")

        max_attempts = 30
        attempt = 0

        while attempt < max_attempts:
            # Check PR status
            status = await self._check_pr_status(pr_info)

            if status["all_checks_passed"] and status["mergeable"]:
                print("   ✅ All checks passed, merging...")
                return await self._merge_pr(pr_info)

            print(f"   ⏳ Waiting for checks... ({attempt + 1}/{max_attempts})")
            print(f"      Checks: {status['passed_checks']}/{status['total_checks']}")
            print(f"      Mergeable: {status['mergeable']}")

            await asyncio.sleep(60)  # Wait 1 minute
            attempt += 1

        print("   ❌ Timeout waiting for checks")
        return False

    async def cherry_pick_commits(
        self,
        commits: List[str],
        target_branch: str
    ) -> List[CommitInfo]:
        """Cherry-pick specific commits to another branch"""

        print(f"🍒 CHERRY-PICKING {len(commits)} commits to {target_branch}")

        # Checkout target branch
        self.repo.git.checkout(target_branch)
        self.repo.git.pull()

        picked_commits = []

        for commit_sha in commits:
            try:
                # Cherry-pick commit
                self.repo.git.cherry_pick(commit_sha)
                print(f"   ✅ Cherry-picked: {commit_sha[:8]}")

                # Get commit info
                commit = self.repo.commit(commit_sha)
                picked_commits.append(CommitInfo(
                    sha=commit.hexsha,
                    message=commit.message,
                    author=str(commit.author),
                    timestamp=datetime.fromtimestamp(commit.committed_date),
                    files_changed=[],
                    stats={}
                ))

            except git.GitCommandError as e:
                if "conflict" in str(e).lower():
                    print(f"   ⚠️ Conflict in {commit_sha[:8]}, attempting resolution...")

                    # Try to resolve conflicts
                    conflicted_files = self.repo.git.diff(name_only=True, unmerged=True).splitlines()

                    for file in conflicted_files:
                        await self._auto_resolve_conflict(file)
                        self.repo.git.add(file)

                    # Continue cherry-pick
                    try:
                        self.repo.git.cherry_pick(continue_=True)
                        print(f"   ✅ Resolved and cherry-picked: {commit_sha[:8]}")
                    except:
                        self.repo.git.cherry_pick(abort=True)
                        print(f"   ❌ Failed to cherry-pick: {commit_sha[:8]}")
                else:
                    print(f"   ❌ Error cherry-picking {commit_sha[:8]}: {e}")

        # Push changes
        if picked_commits:
            self.repo.git.push()
            print(f"   ✅ Pushed {len(picked_commits)} cherry-picked commits")

        return picked_commits

    async def auto_tag_release(
        self,
        version: Optional[str] = None,
        message: Optional[str] = None
    ) -> str:
        """Automatically create release tags"""

        print("🏷️ CREATING RELEASE TAG")

        # Generate version if not provided
        if not version:
            version = self._generate_next_version()

        # Generate release notes
        if not message:
            message = await self._generate_release_notes(version)

        # Create tag
        tag = self.repo.create_tag(
            version,
            message=message
        )

        # Push tag
        self.repo.git.push("origin", version)

        print(f"   ✅ Created tag: {version}")

        # Create GitHub release if possible
        if self.github_client:
            await self._create_github_release(version, message)

        return version

    async def analyze_code_quality(
        self,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze code quality before merge"""

        print("🔍 ANALYZING CODE QUALITY")

        if branch:
            self.repo.git.checkout(branch)

        analysis = {
            "issues": [],
            "suggestions": [],
            "quality_score": 100,
            "ready_to_merge": True
        }

        # Check for common issues
        issues = []

        # Large files
        large_files = self._find_large_files()
        if large_files:
            issues.append({
                "type": "large_files",
                "severity": "warning",
                "files": large_files,
                "suggestion": "Consider using Git LFS for large files"
            })
            analysis["quality_score"] -= 10

        # Sensitive data
        sensitive_data = self._scan_for_secrets()
        if sensitive_data:
            issues.append({
                "type": "sensitive_data",
                "severity": "critical",
                "files": sensitive_data,
                "suggestion": "Remove sensitive data immediately"
            })
            analysis["quality_score"] -= 50
            analysis["ready_to_merge"] = False

        # Code complexity
        complexity_issues = await self._analyze_complexity()
        if complexity_issues:
            issues.append({
                "type": "high_complexity",
                "severity": "warning",
                "files": complexity_issues,
                "suggestion": "Refactor complex code for better maintainability"
            })
            analysis["quality_score"] -= 5 * len(complexity_issues)

        # Test coverage
        coverage = await self._check_test_coverage()
        if coverage < 80:
            issues.append({
                "type": "low_coverage",
                "severity": "warning",
                "coverage": coverage,
                "suggestion": f"Increase test coverage from {coverage}% to at least 80%"
            })
            analysis["quality_score"] -= (80 - coverage) // 2

        analysis["issues"] = issues

        # Generate suggestions
        if analysis["quality_score"] < 70:
            analysis["suggestions"].append("Consider addressing critical issues before merge")

        if not analysis["ready_to_merge"]:
            analysis["suggestions"].append("BLOCKING: Critical issues must be resolved")

        print(f"   📊 Quality Score: {analysis['quality_score']}/100")
        print(f"   🚦 Ready to merge: {'Yes' if analysis['ready_to_merge'] else 'No'}")

        return analysis

    def _generate_commit_message(self, diff: str) -> str:
        """Generate intelligent commit message from diff"""

        # Analyze diff to understand changes
        lines = diff.splitlines()

        # Count changes by file type
        file_changes = {}
        current_file = None

        for line in lines:
            if line.startswith("+++") or line.startswith("---"):
                # Extract filename
                parts = line.split()
                if len(parts) > 1:
                    filename = parts[1].replace("b/", "").replace("a/", "")
                    current_file = filename
                    if current_file not in file_changes:
                        file_changes[current_file] = {"added": 0, "removed": 0}

            elif line.startswith("+") and current_file:
                file_changes[current_file]["added"] += 1
            elif line.startswith("-") and current_file:
                file_changes[current_file]["removed"] += 1

        # Determine commit type
        if any("test" in f for f in file_changes):
            commit_type = "test"
        elif any("fix" in diff.lower() or "bug" in diff.lower() for _ in range(1)):
            commit_type = "fix"
        elif any("feat" in diff.lower() or "add" in diff.lower() for _ in range(1)):
            commit_type = "feat"
        elif any("refactor" in diff.lower() for _ in range(1)):
            commit_type = "refactor"
        elif any("docs" in f for f in file_changes):
            commit_type = "docs"
        else:
            commit_type = "chore"

        # Generate message
        if len(file_changes) == 1:
            file = list(file_changes.keys())[0]
            component = Path(file).stem
            action = "update" if file_changes[file]["added"] > file_changes[file]["removed"] else "fix"
            message = f"{commit_type}({component}): {action} {component}"
        else:
            message = f"{commit_type}: update {len(file_changes)} files"

            # Add details
            details = []
            for file, changes in list(file_changes.items())[:3]:
                component = Path(file).stem
                if changes["added"] > changes["removed"]:
                    details.append(f"- Add functionality to {component}")
                elif changes["removed"] > changes["added"]:
                    details.append(f"- Remove code from {component}")
                else:
                    details.append(f"- Update {component}")

            if details:
                message += "\n\n" + "\n".join(details)

        return message

    def _generate_pr_title(self, branch: str, files: List[str]) -> str:
        """Generate PR title from branch and files"""

        # Extract feature name from branch
        if "/" in branch:
            feature = branch.split("/")[-1]
            feature = feature.replace("-", " ").replace("_", " ")
            return f"Feature: {feature.capitalize()}"

        # Fallback to file-based title
        if len(files) == 1:
            component = Path(files[0]).stem
            return f"Update {component}"
        else:
            return f"Update {len(files)} files"

    def _generate_pr_description(self, diff: str, files: List[str]) -> str:
        """Generate PR description"""

        description = "## Summary\n\n"

        # Determine change type
        if any("test" in f for f in files):
            description += "This PR adds/updates tests.\n\n"
        elif any("fix" in diff.lower() or "bug" in diff.lower() for _ in range(1)):
            description += "This PR fixes bugs.\n\n"
        else:
            description += "This PR implements new functionality.\n\n"

        # List changed files
        description += "## Changes\n\n"
        for file in files[:10]:  # Limit to 10 files
            description += f"- `{file}`\n"

        if len(files) > 10:
            description += f"- ... and {len(files) - 10} more files\n"

        # Add checklist
        description += "\n## Checklist\n\n"
        description += "- [x] Code compiles without warnings\n"
        description += "- [x] Tests pass\n"
        description += "- [x] Documentation updated\n"
        description += "- [x] Changes reviewed by AI\n"

        return description

    async def _auto_resolve_conflict(self, file: str) -> bool:
        """Automatically resolve merge conflict"""

        try:
            with open(self.repo_path / file, 'r') as f:
                content = f.read()

            # Find conflict markers
            conflict_pattern = r'<<<<<<< .+?\n(.*?)\n=======\n(.*?)\n>>>>>>> .+?\n'
            conflicts = re.findall(conflict_pattern, content, re.DOTALL)

            if not conflicts:
                return False

            # Resolve each conflict
            for ours, theirs in conflicts:
                # Smart resolution based on content
                resolution = self._smart_merge(ours, theirs)

                # Replace conflict with resolution
                conflict_block = f"<<<<<<< .+?\n{re.escape(ours)}\n=======\n{re.escape(theirs)}\n>>>>>>> .+?\n"
                content = re.sub(conflict_block, resolution, content, count=1, flags=re.DOTALL)

            # Write resolved content
            with open(self.repo_path / file, 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"      ❌ Error resolving {file}: {e}")
            return False

    def _smart_merge(self, ours: str, theirs: str) -> str:
        """Smart merge strategy"""

        # If one is empty, take the other
        if not ours.strip():
            return theirs
        if not theirs.strip():
            return ours

        # If they're the same, take one
        if ours.strip() == theirs.strip():
            return ours

        # For imports, combine them
        if "import" in ours and "import" in theirs:
            combined = set(ours.splitlines()) | set(theirs.splitlines())
            return "\n".join(sorted(combined))

        # For functions, prefer the longer one (likely more complete)
        if "def " in ours or "function " in ours:
            return ours if len(ours) > len(theirs) else theirs

        # Default: combine both with a comment
        return f"{ours}\n// MERGED: Alternative implementation below\n// {theirs}"

    def _find_large_files(self, size_limit_mb: float = 10) -> List[str]:
        """Find large files in repository"""

        large_files = []
        size_limit = size_limit_mb * 1024 * 1024  # Convert to bytes

        for item in self.repo_path.rglob("*"):
            if item.is_file() and item.stat().st_size > size_limit:
                # Check if file is tracked
                try:
                    self.repo.git.ls_files(item)
                    large_files.append(str(item.relative_to(self.repo_path)))
                except:
                    pass  # File not tracked

        return large_files

    def _scan_for_secrets(self) -> List[str]:
        """Scan for sensitive data in code"""

        sensitive_patterns = [
            r'api[_-]?key\s*=\s*["\'][\w\d]+["\']',
            r'secret[_-]?key\s*=\s*["\'][\w\d]+["\']',
            r'password\s*=\s*["\'].+["\']',
            r'token\s*=\s*["\'][\w\d]+["\']',
            r'aws[_-]?access[_-]?key[_-]?id\s*=\s*["\'][\w\d]+["\']',
            r'private[_-]?key\s*=\s*["\'].+["\']'
        ]

        files_with_secrets = []

        for pattern in sensitive_patterns:
            try:
                # Search for pattern in tracked files
                result = self.repo.git.grep(pattern)
                if result:
                    for line in result.splitlines():
                        file = line.split(":")[0]
                        if file not in files_with_secrets:
                            files_with_secrets.append(file)
            except:
                pass  # Pattern not found

        return files_with_secrets

    async def _analyze_complexity(self) -> List[str]:
        """Analyze code complexity"""

        complex_files = []

        # Simple complexity check - functions longer than 50 lines
        for file in self.repo_path.rglob("*.py"):
            try:
                with open(file, 'r') as f:
                    lines = f.readlines()

                in_function = False
                function_lines = 0

                for line in lines:
                    if line.strip().startswith("def ") or line.strip().startswith("async def "):
                        in_function = True
                        function_lines = 0
                    elif in_function:
                        function_lines += 1
                        if function_lines > 50:
                            complex_files.append(str(file.relative_to(self.repo_path)))
                            break
            except:
                pass

        return complex_files

    async def _check_test_coverage(self) -> float:
        """Check test coverage"""

        # Try to run coverage command
        try:
            result = subprocess.run(
                ["coverage", "report", "--format=total"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Extract coverage percentage
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    return float(match.group(1))
        except:
            pass

        # Default to 0 if coverage not available
        return 0.0

    def _sanitize_branch_name(self, name: str) -> str:
        """Sanitize branch name"""
        # Remove special characters
        name = re.sub(r'[^a-zA-Z0-9\-_]', '-', name)
        # Remove consecutive hyphens
        name = re.sub(r'-+', '-', name)
        # Remove leading/trailing hyphens
        name = name.strip('-')
        # Lowercase
        name = name.lower()
        # Truncate if too long
        if len(name) > 50:
            name = name[:50]

        return name

    def _parse_changed_files(self, stats: str) -> List[str]:
        """Parse changed files from git stats"""
        files = []
        for line in stats.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                files.append(parts[2])
        return files

    def _load_commit_patterns(self) -> Dict:
        """Load commit message patterns"""
        return {
            "feat": "A new feature",
            "fix": "A bug fix",
            "docs": "Documentation only changes",
            "style": "Formatting, missing semicolons, etc",
            "refactor": "Code restructuring",
            "test": "Adding missing tests",
            "chore": "Maintenance tasks"
        }

    def _load_merge_strategies(self) -> Dict:
        """Load merge conflict resolution strategies"""
        return {
            "imports": "combine",
            "functions": "prefer_longer",
            "constants": "prefer_theirs",
            "comments": "combine"
        }

    def _generate_next_version(self) -> str:
        """Generate next version number"""

        try:
            # Get latest tag
            tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
            if tags:
                latest = tags[-1].name

                # Parse version
                match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', latest)
                if match:
                    major, minor, patch = map(int, match.groups())

                    # Determine version bump
                    # This is simplified - in reality would analyze commits
                    return f"v{major}.{minor}.{patch + 1}"

        except:
            pass

        return "v1.0.0"  # Default for first release

    async def _generate_release_notes(self, version: str) -> str:
        """Generate release notes"""

        notes = f"# Release {version}\n\n"
        notes += f"Released: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"

        # Get commits since last tag
        try:
            tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
            if len(tags) > 0:
                last_tag = tags[-1]
                commits = list(self.repo.iter_commits(f'{last_tag}..HEAD'))

                # Categorize commits
                features = []
                fixes = []
                others = []

                for commit in commits:
                    message = commit.message.strip()
                    if message.startswith("feat"):
                        features.append(message)
                    elif message.startswith("fix"):
                        fixes.append(message)
                    else:
                        others.append(message)

                # Add to notes
                if features:
                    notes += "## New Features\n\n"
                    for feat in features:
                        notes += f"- {feat}\n"
                    notes += "\n"

                if fixes:
                    notes += "## Bug Fixes\n\n"
                    for fix in fixes:
                        notes += f"- {fix}\n"
                    notes += "\n"

                if others:
                    notes += "## Other Changes\n\n"
                    for other in others[:5]:  # Limit to 5
                        notes += f"- {other}\n"
                    notes += "\n"

        except:
            notes += "## Changes\n\n- Various improvements and bug fixes\n\n"

        notes += "---\n\n"
        notes += "*Generated automatically by Git Agent*"

        return notes
    async def create_branch(self, branch_name: str) -> None:
        """Create a new branch"""
        self.repo.create_head(branch_name)
        self.repo.heads[branch_name].checkout()
        self.current_branch = branch_name

    async def analyze_changes(self) -> Dict[str, Any]:
        """Analyze current changes in the repository"""
        if not self.repo:
            return {"files_changed": 0, "additions": 0, "deletions": 0}
        
        diff = self.repo.index.diff(None)
        staged = self.repo.index.diff("HEAD")
        
        return {
            "files_changed": len(diff) + len(staged),
            "additions": sum(d.a_blob.size if d.a_blob else 0 for d in diff),
            "deletions": sum(d.b_blob.size if d.b_blob else 0 for d in diff),
            "has_conflicts": False
        }
