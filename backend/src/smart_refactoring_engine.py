#!/usr/bin/env python3
"""
Smart Code Refactoring Engine - Advanced autonomous code improvements
"""

import ast
import re
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime


class SmartRefactoringEngine:
    """Advanced code refactoring for security and performance improvements"""

    def __init__(self):
        self.refactoring_log = []
        self.safe_mode = True

    async def analyze_and_refactor_code(
        self, file_path: str, refactor_type: str = "security"
    ) -> Dict[str, Any]:
        """Analyze code and apply intelligent refactoring"""

        if not os.path.exists(file_path):
            return {"error": "File not found", "refactors_applied": 0}

        try:
            with open(file_path, "r") as f:
                original_content = f.read()

            refactors = []

            if refactor_type == "security":
                refactors.extend(self._security_refactoring_patterns(original_content))
            elif refactor_type == "performance":
                refactors.extend(
                    self._performance_refactoring_patterns(original_content)
                )
            elif refactor_type == "maintainability":
                refactors.extend(
                    self._maintainability_refactoring_patterns(original_content)
                )
            else:
                # Apply all refactoring types
                refactors.extend(self._security_refactoring_patterns(original_content))
                refactors.extend(
                    self._performance_refactoring_patterns(original_content)
                )
                refactors.extend(
                    self._maintainability_refactoring_patterns(original_content)
                )

            # Apply refactoring patterns
            modified_content = original_content
            applied_refactors = []

            for refactor in refactors:
                if self._should_apply_refactor(refactor):
                    modified_content, applied = self._apply_refactor(
                        modified_content, refactor
                    )
                    if applied:
                        applied_refactors.append(refactor)

            # Write refactored code if changes were made
            if modified_content != original_content and not self.safe_mode:
                with open(file_path, "w") as f:
                    f.write(modified_content)

            return {
                "refactors_identified": len(refactors),
                "refactors_applied": len(applied_refactors),
                "applied_refactors": applied_refactors,
                "file_modified": modified_content != original_content,
                "safe_mode": self.safe_mode,
            }

        except Exception as e:
            return {"error": str(e), "refactors_applied": 0}

    def _security_refactoring_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Identify security-focused refactoring opportunities"""
        patterns = []

        # Input validation patterns
        if re.search(r"request\.(form|args|json)\[", content):
            patterns.append(
                {
                    "type": "input_validation",
                    "pattern": r"(\w+)\s*=\s*request\.(form|args|json)\[([^\]]+)\]",
                    "replacement": r'\1 = request.\2.get(\3, "")  # Security: safe input access',
                    "description": "Replace direct request parameter access with safe .get() method",
                    "severity": "medium",
                }
            )

        # Fix direct user input returns (XSS prevention)
        if re.search(r'return f".*\{[^}]+\}"', content):
            patterns.append(
                {
                    "type": "xss_prevention",
                    "pattern": r'return f"([^"]*\{[^}]+\}[^"]*)"',
                    "replacement": r'# Security: Consider using escape() for user input in responses\n    return f"\1"',
                    "description": "Add security comment for potential XSS in f-string returns",
                    "severity": "high",
                }
            )

        # SQL query improvements
        if re.search(r'f".*SELECT.*\{.*\}"', content, re.IGNORECASE):
            patterns.append(
                {
                    "type": "sql_parameterization",
                    "pattern": r'f"(SELECT.*\{[^}]+\}.*)"',
                    "replacement": r'# TODO: Use parameterized query instead of f-string\n    # cursor.execute("SELECT * FROM table WHERE id = %s", (user_id,))',
                    "description": "Flag SQL f-strings for parameterization",
                    "severity": "high",
                }
            )

        # Exception handling improvements
        if "except:" in content or "except Exception:" in content:
            patterns.append(
                {
                    "type": "exception_handling",
                    "pattern": r"except( Exception)?:\s*\n\s*pass",
                    "replacement": r'except\1 as e:\n    # TODO: Implement proper error handling\n    print(f"Error: {str(e)}")  # Security: log errors properly',
                    "description": "Improve exception handling with proper logging",
                    "severity": "medium",
                }
            )

        return patterns

    def _performance_refactoring_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Identify performance optimization opportunities"""
        patterns = []

        # List comprehension opportunities
        loop_pattern = r"(\w+)\s*=\s*\[\]\s*\n\s*for\s+(\w+)\s+in\s+([^:]+):\s*\n\s*\1\.append\(([^)]+)\)"
        if re.search(loop_pattern, content, re.MULTILINE):
            patterns.append(
                {
                    "type": "list_comprehension",
                    "pattern": loop_pattern,
                    "replacement": r"\1 = [\4 for \2 in \3]  # Performance: list comprehension",
                    "description": "Convert simple loops to list comprehensions",
                    "severity": "low",
                }
            )

        # String concatenation in loops
        if re.search(r"for.*:\s*\n\s*\w+\s*\+=\s*.*", content, re.MULTILINE):
            patterns.append(
                {
                    "type": "string_joining",
                    "pattern": None,  # Complex pattern, handle in apply method
                    "replacement": None,
                    "description": "Flag string concatenation in loops for join() optimization",
                    "severity": "medium",
                }
            )

        return patterns

    def _maintainability_refactoring_patterns(
        self, content: str
    ) -> List[Dict[str, Any]]:
        """Identify maintainability improvements"""
        patterns = []

        # Magic number elimination
        magic_numbers = re.findall(r"\b(?!0|1|2|10|100|1000)\d{3,}\b", content)
        if magic_numbers:
            patterns.append(
                {
                    "type": "magic_numbers",
                    "pattern": None,
                    "replacement": None,
                    "description": f"Replace magic numbers with named constants: {set(magic_numbers)}",
                    "severity": "low",
                }
            )

        # Long function detection (basic heuristic)
        functions = re.findall(
            r"def\s+(\w+).*?(?=\ndef|\nclass|\n$|\Z)", content, re.DOTALL
        )
        for func in functions:
            lines = func.count("\n")
            if lines > 20:  # Function longer than 20 lines
                patterns.append(
                    {
                        "type": "long_function",
                        "pattern": None,
                        "replacement": None,
                        "description": f"Consider breaking down long function (>{lines} lines)",
                        "severity": "low",
                    }
                )

        return patterns

    def _should_apply_refactor(self, refactor: Dict[str, Any]) -> bool:
        """Determine if a refactor should be applied automatically"""
        if self.safe_mode:
            # In safe mode, only apply low-risk refactors
            return refactor.get("severity") == "low"

        # In autonomous mode, apply all refactors (including high for testing)
        return refactor.get("severity") in ["low", "medium", "high"]

    def _apply_refactor(
        self, content: str, refactor: Dict[str, Any]
    ) -> Tuple[str, bool]:
        """Apply a specific refactor to the content"""
        if not refactor.get("pattern") or not refactor.get("replacement"):
            # Handle special cases that need custom logic
            return content, False

        try:
            # Apply regex replacement
            modified_content = re.sub(
                refactor["pattern"],
                refactor["replacement"],
                content,
                flags=re.MULTILINE,
            )

            applied = modified_content != content
            if applied:
                print(f"      ✅ Applied {refactor['type']}: {refactor['description']}")

            return modified_content, applied

        except Exception as e:
            print(f"      ❌ Failed to apply {refactor['type']}: {str(e)}")
            return content, False

    def generate_refactoring_report(self, file_path: str) -> Dict[str, Any]:
        """Generate a comprehensive refactoring analysis report"""

        if not os.path.exists(file_path):
            return {"error": "File not found"}

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Analyze code complexity
            complexity_metrics = self._analyze_complexity(content)

            # Identify all potential refactoring opportunities
            security_refactors = self._security_refactoring_patterns(content)
            performance_refactors = self._performance_refactoring_patterns(content)
            maintainability_refactors = self._maintainability_refactoring_patterns(
                content
            )

            return {
                "file": file_path,
                "complexity_metrics": complexity_metrics,
                "refactoring_opportunities": {
                    "security": len(security_refactors),
                    "performance": len(performance_refactors),
                    "maintainability": len(maintainability_refactors),
                    "total": len(security_refactors)
                    + len(performance_refactors)
                    + len(maintainability_refactors),
                },
                "detailed_analysis": {
                    "security_issues": security_refactors,
                    "performance_opportunities": performance_refactors,
                    "maintainability_improvements": maintainability_refactors,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"error": str(e)}

    def _analyze_complexity(self, content: str) -> Dict[str, Any]:
        """Analyze code complexity metrics"""
        try:
            # Parse AST for more sophisticated analysis
            tree = ast.parse(content)

            metrics = {
                "lines_of_code": len(content.split("\n")),
                "function_count": len(
                    [
                        node
                        for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                    ]
                ),
                "class_count": len(
                    [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                ),
                "import_count": len(
                    [
                        node
                        for node in ast.walk(tree)
                        if isinstance(node, (ast.Import, ast.ImportFrom))
                    ]
                ),
                "complexity_score": self._calculate_cyclomatic_complexity(tree),
            }

            return metrics

        except SyntaxError:
            # Fallback to basic text analysis if AST parsing fails
            lines = content.split("\n")
            return {
                "lines_of_code": len(lines),
                "function_count": len(re.findall(r"^\s*def\s+", content, re.MULTILINE)),
                "class_count": len(re.findall(r"^\s*class\s+", content, re.MULTILINE)),
                "import_count": len(
                    re.findall(r"^\s*(import|from)\s+", content, re.MULTILINE)
                ),
                "complexity_score": "unknown",
            }

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate basic cyclomatic complexity"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1

        return complexity
