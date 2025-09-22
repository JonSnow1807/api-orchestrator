#!/usr/bin/env python3
"""
Multi-Language Remediation Engine
Support for Python, JavaScript, Java, C#, Go autonomous fixes
"""

import re
import os
from typing import Dict, List, Any, Tuple


class MultiLanguageRemediationEngine:
    """Autonomous remediation across multiple programming languages"""

    def __init__(self):
        self.supported_languages = ["python", "javascript", "java", "csharp", "go"]
        self.safe_mode = True

    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension and content"""
        extension = os.path.splitext(file_path)[1].lower()

        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "javascript",  # TypeScript treated as JavaScript
            ".java": "java",
            ".cs": "csharp",
            ".go": "go",
        }

        return lang_map.get(extension, "unknown")

    async def apply_multilang_fixes(
        self, file_path: str, vulnerabilities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply language-specific security fixes"""

        if not os.path.exists(file_path):
            return {
                "fixes_applied": 0,
                "language": "unknown",
                "error": "File not found",
            }

        language = self.detect_language(file_path)

        if language == "unknown":
            return {
                "fixes_applied": 0,
                "language": "unknown",
                "error": "Unsupported language",
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            modified_content = original_content
            fixes_applied = 0

            if language == "python":
                modified_content, fixes = self._fix_python_vulnerabilities(
                    modified_content, vulnerabilities
                )
                fixes_applied += fixes
            elif language == "javascript":
                modified_content, fixes = self._fix_javascript_vulnerabilities(
                    modified_content, vulnerabilities
                )
                fixes_applied += fixes
            elif language == "java":
                modified_content, fixes = self._fix_java_vulnerabilities(
                    modified_content, vulnerabilities
                )
                fixes_applied += fixes
            elif language == "csharp":
                modified_content, fixes = self._fix_csharp_vulnerabilities(
                    modified_content, vulnerabilities
                )
                fixes_applied += fixes
            elif language == "go":
                modified_content, fixes = self._fix_go_vulnerabilities(
                    modified_content, vulnerabilities
                )
                fixes_applied += fixes

            # Write back if changes were made and safe mode is off
            if modified_content != original_content and not self.safe_mode:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)

            return {
                "fixes_applied": fixes_applied,
                "language": language,
                "file_modified": modified_content != original_content,
                "changes_preview": self._generate_diff_preview(
                    original_content, modified_content
                ),
            }

        except Exception as e:
            return {"fixes_applied": 0, "language": language, "error": str(e)}

    def _fix_python_vulnerabilities(
        self, content: str, vulnerabilities: List[Dict[str, Any]]
    ) -> Tuple[str, int]:
        """Fix Python-specific vulnerabilities"""
        fixes = 0
        modified = content

        # Fix hardcoded secrets
        if any("secret" in v.get("type", "").lower() for v in vulnerabilities):
            secret_patterns = [
                (
                    r'SECRET_KEY\s*=\s*["\']([^"\']+)["\']',
                    'SECRET_KEY = os.getenv("SECRET_KEY", "")  # Security fix',
                ),
                (
                    r'PASSWORD\s*=\s*["\']([^"\']+)["\']',
                    'PASSWORD = os.getenv("PASSWORD", "")  # Security fix',
                ),
                (
                    r'API_KEY\s*=\s*["\']([^"\']+)["\']',
                    'API_KEY = os.getenv("API_KEY", "")  # Security fix',
                ),
            ]

            for pattern, replacement in secret_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(
                        pattern, replacement, modified, flags=re.IGNORECASE
                    )
                    fixes += 1

            # Add os import if secrets were fixed
            if fixes > 0 and "import os" not in modified:
                modified = (
                    "import os  # Security fix: for environment variables\n" + modified
                )

        # Fix weak hash functions
        if any(
            "hash" in v.get("type", "").lower() or "md5" in v.get("issue", "").lower()
            for v in vulnerabilities
        ):
            if "hashlib.md5" in modified:
                modified = modified.replace(
                    "hashlib.md5", "hashlib.sha256  # Security fix: upgraded from MD5"
                )
                fixes += 1

        # Fix debug mode
        if any("debug" in v.get("type", "").lower() for v in vulnerabilities):
            if "debug=True" in modified:
                modified = modified.replace(
                    "debug=True", "debug=False  # Security fix: disabled debug mode"
                )
                fixes += 1

        # Fix SQL injection patterns
        if any("sql" in v.get("type", "").lower() for v in vulnerabilities):
            sql_patterns = [
                r'f".*SELECT.*\{[^}]+\}.*"',
                r'".*SELECT.*"\s*\+',
                r'".*SELECT.*"\s*%',
            ]
            for pattern in sql_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    lines = modified.split("\n")
                    for i, line in enumerate(lines):
                        if re.search(pattern, line, re.IGNORECASE):
                            lines.insert(
                                i,
                                "    # SECURITY WARNING: SQL injection risk - use parameterized queries",
                            )
                            fixes += 1
                            break
                    modified = "\n".join(lines)
                    break

        return modified, fixes

    def _fix_javascript_vulnerabilities(
        self, content: str, vulnerabilities: List[Dict[str, Any]]
    ) -> Tuple[str, int]:
        """Fix JavaScript/Node.js specific vulnerabilities"""
        fixes = 0
        modified = content

        # Fix hardcoded secrets
        if any("secret" in v.get("type", "").lower() for v in vulnerabilities):
            secret_patterns = [
                (
                    r'const\s+SECRET_KEY\s*=\s*["\']([^"\']+)["\']',
                    'const SECRET_KEY = process.env.SECRET_KEY || "";  // Security fix',
                ),
                (
                    r'const\s+API_KEY\s*=\s*["\']([^"\']+)["\']',
                    'const API_KEY = process.env.API_KEY || "";  // Security fix',
                ),
                (
                    r'let\s+PASSWORD\s*=\s*["\']([^"\']+)["\']',
                    'let PASSWORD = process.env.PASSWORD || "";  // Security fix',
                ),
            ]

            for pattern, replacement in secret_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(
                        pattern, replacement, modified, flags=re.IGNORECASE
                    )
                    fixes += 1

        # Fix SQL injection in template literals
        if any("sql" in v.get("type", "").lower() for v in vulnerabilities):
            sql_pattern = r"`.*SELECT.*\$\{[^}]+\}.*`"
            if re.search(sql_pattern, modified, re.IGNORECASE):
                lines = modified.split("\n")
                for i, line in enumerate(lines):
                    if re.search(sql_pattern, line, re.IGNORECASE):
                        lines.insert(
                            i,
                            "    // SECURITY WARNING: SQL injection risk - use parameterized queries",
                        )
                        fixes += 1
                        break
                modified = "\n".join(lines)

        # Fix eval usage
        if "eval(" in modified:
            modified = modified.replace(
                "eval(", "// SECURITY WARNING: eval() is dangerous\n    // eval("
            )
            fixes += 1

        # Fix HTTP server binding
        if "listen(3000, '0.0.0.0')" in modified:
            modified = modified.replace(
                "listen(3000, '0.0.0.0')",
                "listen(3000, 'localhost')  // Security fix: bind to localhost",
            )
            fixes += 1

        return modified, fixes

    def _fix_java_vulnerabilities(
        self, content: str, vulnerabilities: List[Dict[str, Any]]
    ) -> Tuple[str, int]:
        """Fix Java specific vulnerabilities"""
        fixes = 0
        modified = content

        # Fix hardcoded secrets
        if any("secret" in v.get("type", "").lower() for v in vulnerabilities):
            secret_patterns = [
                (
                    r'private\s+static\s+final\s+String\s+PASSWORD\s*=\s*"([^"]+)"',
                    'private static final String PASSWORD = System.getenv("PASSWORD");  // Security fix',
                ),
                (
                    r'private\s+static\s+final\s+String\s+API_KEY\s*=\s*"([^"]+)"',
                    'private static final String API_KEY = System.getenv("API_KEY");  // Security fix',
                ),
                (
                    r'String\s+SECRET_KEY\s*=\s*"([^"]+)"',
                    'String SECRET_KEY = System.getenv("SECRET_KEY");  // Security fix',
                ),
            ]

            for pattern, replacement in secret_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(
                        pattern, replacement, modified, flags=re.IGNORECASE
                    )
                    fixes += 1

        # Fix SQL injection in string concatenation
        if any("sql" in v.get("type", "").lower() for v in vulnerabilities):
            sql_pattern = r'".*SELECT.*"\s*\+\s*\w+'
            if re.search(sql_pattern, modified, re.IGNORECASE):
                lines = modified.split("\n")
                for i, line in enumerate(lines):
                    if re.search(sql_pattern, line, re.IGNORECASE):
                        lines.insert(
                            i,
                            "        // SECURITY WARNING: SQL injection risk - use PreparedStatement",
                        )
                        fixes += 1
                        break
                modified = "\n".join(lines)

        # Fix weak hash algorithms
        if 'MessageDigest.getInstance("MD5")' in modified:
            modified = modified.replace(
                'MessageDigest.getInstance("MD5")',
                'MessageDigest.getInstance("SHA-256")  // Security fix: upgraded from MD5',
            )
            fixes += 1

        return modified, fixes

    def _fix_csharp_vulnerabilities(
        self, content: str, vulnerabilities: List[Dict[str, Any]]
    ) -> Tuple[str, int]:
        """Fix C# specific vulnerabilities"""
        fixes = 0
        modified = content

        # Fix hardcoded secrets
        if any("secret" in v.get("type", "").lower() for v in vulnerabilities):
            secret_patterns = [
                (
                    r'private\s+static\s+readonly\s+string\s+PASSWORD\s*=\s*"([^"]+)"',
                    'private static readonly string PASSWORD = Environment.GetEnvironmentVariable("PASSWORD");  // Security fix',
                ),
                (
                    r'const\s+string\s+API_KEY\s*=\s*"([^"]+)"',
                    'private static readonly string API_KEY = Environment.GetEnvironmentVariable("API_KEY");  // Security fix',
                ),
            ]

            for pattern, replacement in secret_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(
                        pattern, replacement, modified, flags=re.IGNORECASE
                    )
                    fixes += 1

        # Fix SQL injection
        if any("sql" in v.get("type", "").lower() for v in vulnerabilities):
            sql_pattern = r'".*SELECT.*"\s*\+\s*\w+'
            if re.search(sql_pattern, modified, re.IGNORECASE):
                lines = modified.split("\n")
                for i, line in enumerate(lines):
                    if re.search(sql_pattern, line, re.IGNORECASE):
                        lines.insert(
                            i,
                            "            // SECURITY WARNING: SQL injection risk - use parameterized queries",
                        )
                        fixes += 1
                        break
                modified = "\n".join(lines)

        # Fix weak hash
        if "MD5.Create()" in modified:
            modified = modified.replace(
                "MD5.Create()", "SHA256.Create()  // Security fix: upgraded from MD5"
            )
            fixes += 1

        return modified, fixes

    def _fix_go_vulnerabilities(
        self, content: str, vulnerabilities: List[Dict[str, Any]]
    ) -> Tuple[str, int]:
        """Fix Go specific vulnerabilities"""
        fixes = 0
        modified = content

        # Fix hardcoded secrets
        if any("secret" in v.get("type", "").lower() for v in vulnerabilities):
            secret_patterns = [
                (
                    r'const\s+PASSWORD\s*=\s*"([^"]+)"',
                    'var PASSWORD = os.Getenv("PASSWORD")  // Security fix',
                ),
                (
                    r'const\s+API_KEY\s*=\s*"([^"]+)"',
                    'var API_KEY = os.Getenv("API_KEY")  // Security fix',
                ),
            ]

            for pattern, replacement in secret_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(
                        pattern, replacement, modified, flags=re.IGNORECASE
                    )
                    fixes += 1

            # Add os import if needed
            if fixes > 0 and 'import "os"' not in modified and '"os"' not in modified:
                if "import (" in modified:
                    modified = modified.replace(
                        "import (",
                        'import (\n\t"os"  // Security fix: for environment variables',
                    )
                else:
                    modified = (
                        'import "os"  // Security fix: for environment variables\n\n'
                        + modified
                    )

        # Fix SQL injection
        if any("sql" in v.get("type", "").lower() for v in vulnerabilities):
            sql_pattern = r'".*SELECT.*"\s*\+\s*\w+'
            if re.search(sql_pattern, modified, re.IGNORECASE):
                lines = modified.split("\n")
                for i, line in enumerate(lines):
                    if re.search(sql_pattern, line, re.IGNORECASE):
                        lines.insert(
                            i,
                            "\t// SECURITY WARNING: SQL injection risk - use prepared statements",
                        )
                        fixes += 1
                        break
                modified = "\n".join(lines)

        # Fix insecure HTTP server
        if 'http.ListenAndServe(":8080"' in modified:
            modified = modified.replace(
                'http.ListenAndServe(":8080"',
                'http.ListenAndServe("localhost:8080"  // Security fix: bind to localhost',
            )
            fixes += 1

        return modified, fixes

    def _generate_diff_preview(self, original: str, modified: str) -> List[str]:
        """Generate a preview of changes made"""
        if original == modified:
            return []

        # Simple diff - show first few changed lines
        original_lines = original.split("\n")
        modified_lines = modified.split("\n")

        changes = []
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
            if orig != mod:
                changes.append(f"Line {i+1}: {orig.strip()} → {mod.strip()}")
                if len(changes) >= 3:  # Limit preview
                    break

        return changes
