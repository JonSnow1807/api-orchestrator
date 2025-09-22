"""
Comprehensive Static Analysis Suite
Multiple static analysis tools integration for code quality
"""

import subprocess
import json
import logging
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import ast
import sys


@dataclass
class StaticAnalysisConfig:
    """Configuration for static analysis tools"""

    target_directory: str = "src"
    include_patterns: List[str] = field(
        default_factory=lambda: ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
    )
    exclude_patterns: List[str] = field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/dist/**",
        ]
    )

    # Tool configurations
    enable_pylint: bool = True
    enable_flake8: bool = True
    enable_mypy: bool = True
    enable_bandit: bool = True  # Security analysis
    enable_black: bool = True  # Code formatting check
    enable_isort: bool = True  # Import sorting check
    enable_prospector: bool = True  # Meta tool
    enable_semgrep: bool = True  # Pattern-based analysis
    enable_vulture: bool = True  # Dead code detection

    # Severity thresholds
    min_pylint_score: float = 8.0
    max_complexity: int = 10
    max_security_issues: int = 0
    max_high_priority_issues: int = 5


@dataclass
class AnalysisResult:
    """Results from static analysis"""

    tool_name: str
    exit_code: int
    stdout: str
    stderr: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class StaticAnalysisRunner:
    """Run comprehensive static analysis"""

    def __init__(self, config: StaticAnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.results: List[AnalysisResult] = []

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def run_all_analyses(self) -> Dict[str, Any]:
        """Run all configured static analysis tools"""
        self.logger.info("Starting comprehensive static analysis")

        # Python-specific tools
        if self.config.enable_pylint:
            await self._run_pylint()

        if self.config.enable_flake8:
            await self._run_flake8()

        if self.config.enable_mypy:
            await self._run_mypy()

        if self.config.enable_bandit:
            await self._run_bandit()

        if self.config.enable_black:
            await self._run_black_check()

        if self.config.enable_isort:
            await self._run_isort_check()

        if self.config.enable_prospector:
            await self._run_prospector()

        if self.config.enable_semgrep:
            await self._run_semgrep()

        if self.config.enable_vulture:
            await self._run_vulture()

        # Custom analyses
        await self._run_custom_ast_analysis()
        await self._run_dependency_analysis()

        # Generate comprehensive report
        return self._generate_comprehensive_report()

    async def _run_pylint(self) -> None:
        """Run Pylint analysis"""
        try:
            cmd = [
                "pylint",
                self.config.target_directory,
                "--output-format=json",
                "--reports=y",
                "--score=y",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="pylint",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Parse JSON output for issues
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    analysis_result.issues = issues

                    # Extract metrics
                    score_line = [
                        line
                        for line in result.stderr.split("\n")
                        if "Your code has been rated at" in line
                    ]
                    if score_line:
                        score = float(score_line[0].split()[6].split("/")[0])
                        analysis_result.metrics["pylint_score"] = score

                except json.JSONDecodeError:
                    self.logger.warning("Could not parse Pylint JSON output")

            self.results.append(analysis_result)
            self.logger.info(f"✅ Pylint analysis completed")

        except FileNotFoundError:
            self.logger.warning(
                "⚠️ Pylint not found - install with: pip install pylint"
            )
        except Exception as e:
            self.logger.error(f"❌ Pylint analysis failed: {e}")

    async def _run_flake8(self) -> None:
        """Run Flake8 analysis"""
        try:
            cmd = [
                "flake8",
                self.config.target_directory,
                "--format=json",
                "--max-complexity=10",
                "--max-line-length=88",
                "--extend-ignore=E203,W503",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="flake8",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Parse output for issues
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    analysis_result.issues = data
                except json.JSONDecodeError:
                    # Parse line-by-line format
                    issues = []
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            parts = line.split(":")
                            if len(parts) >= 4:
                                issues.append(
                                    {
                                        "file": parts[0],
                                        "line": int(parts[1]),
                                        "column": int(parts[2]),
                                        "message": ":".join(parts[3:]).strip(),
                                    }
                                )
                    analysis_result.issues = issues

            self.results.append(analysis_result)
            self.logger.info(f"✅ Flake8 analysis completed")

        except FileNotFoundError:
            self.logger.warning(
                "⚠️ Flake8 not found - install with: pip install flake8"
            )
        except Exception as e:
            self.logger.error(f"❌ Flake8 analysis failed: {e}")

    async def _run_mypy(self) -> None:
        """Run MyPy type checking"""
        try:
            cmd = [
                "mypy",
                self.config.target_directory,
                "--ignore-missing-imports",
                "--show-error-codes",
                "--show-column-numbers",
                "--json-report",
                "mypy-report",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="mypy",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Parse MyPy output
            issues = []
            for line in result.stdout.split("\n"):
                if ":" in line and ("error:" in line or "warning:" in line):
                    parts = line.split(":")
                    if len(parts) >= 3:
                        issues.append(
                            {
                                "file": parts[0],
                                "line": parts[1],
                                "severity": "error" if "error:" in line else "warning",
                                "message": ":".join(parts[2:]).strip(),
                            }
                        )

            analysis_result.issues = issues
            self.results.append(analysis_result)
            self.logger.info(f"✅ MyPy analysis completed")

        except FileNotFoundError:
            self.logger.warning("⚠️ MyPy not found - install with: pip install mypy")
        except Exception as e:
            self.logger.error(f"❌ MyPy analysis failed: {e}")

    async def _run_bandit(self) -> None:
        """Run Bandit security analysis"""
        try:
            cmd = [
                "bandit",
                "-r",
                self.config.target_directory,
                "-f",
                "json",
                "-ll",  # Only show medium and high severity
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="bandit",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Parse Bandit JSON output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    analysis_result.issues = data.get("results", [])
                    analysis_result.metrics = {
                        "total_issues": len(data.get("results", [])),
                        "high_severity": len(
                            [
                                r
                                for r in data.get("results", [])
                                if r.get("issue_severity") == "HIGH"
                            ]
                        ),
                        "medium_severity": len(
                            [
                                r
                                for r in data.get("results", [])
                                if r.get("issue_severity") == "MEDIUM"
                            ]
                        ),
                    }
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse Bandit JSON output")

            self.results.append(analysis_result)
            self.logger.info(f"✅ Bandit security analysis completed")

        except FileNotFoundError:
            self.logger.warning(
                "⚠️ Bandit not found - install with: pip install bandit"
            )
        except Exception as e:
            self.logger.error(f"❌ Bandit analysis failed: {e}")

    async def _run_black_check(self) -> None:
        """Check code formatting with Black"""
        try:
            cmd = ["black", "--check", "--diff", self.config.target_directory]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="black",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Count files that need formatting
            if result.stdout:
                diff_count = result.stdout.count("+++")
                analysis_result.metrics["files_need_formatting"] = diff_count

            self.results.append(analysis_result)
            self.logger.info(f"✅ Black formatting check completed")

        except FileNotFoundError:
            self.logger.warning("⚠️ Black not found - install with: pip install black")
        except Exception as e:
            self.logger.error(f"❌ Black analysis failed: {e}")

    async def _run_isort_check(self) -> None:
        """Check import sorting with isort"""
        try:
            cmd = ["isort", "--check-only", "--diff", self.config.target_directory]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="isort",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Count files with import issues
            if result.stdout:
                fix_count = result.stdout.count("Fixing")
                analysis_result.metrics["files_need_import_sorting"] = fix_count

            self.results.append(analysis_result)
            self.logger.info(f"✅ isort import sorting check completed")

        except FileNotFoundError:
            self.logger.warning("⚠️ isort not found - install with: pip install isort")
        except Exception as e:
            self.logger.error(f"❌ isort analysis failed: {e}")

    async def _run_prospector(self) -> None:
        """Run Prospector meta-analysis tool"""
        try:
            cmd = ["prospector", self.config.target_directory, "--output-format=json"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="prospector",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Parse Prospector JSON output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    analysis_result.issues = data.get("messages", [])
                    analysis_result.metrics = {
                        "total_messages": len(data.get("messages", [])),
                        "errors": len(
                            [
                                m
                                for m in data.get("messages", [])
                                if m.get("severity") == "error"
                            ]
                        ),
                        "warnings": len(
                            [
                                m
                                for m in data.get("messages", [])
                                if m.get("severity") == "warning"
                            ]
                        ),
                    }
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse Prospector JSON output")

            self.results.append(analysis_result)
            self.logger.info(f"✅ Prospector analysis completed")

        except FileNotFoundError:
            self.logger.warning(
                "⚠️ Prospector not found - install with: pip install prospector"
            )
        except Exception as e:
            self.logger.error(f"❌ Prospector analysis failed: {e}")

    async def _run_semgrep(self) -> None:
        """Run Semgrep pattern-based analysis"""
        try:
            cmd = ["semgrep", "--config=auto", "--json", self.config.target_directory]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="semgrep",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Parse Semgrep JSON output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    analysis_result.issues = data.get("results", [])
                    analysis_result.metrics = {
                        "total_findings": len(data.get("results", [])),
                        "security_issues": len(
                            [
                                r
                                for r in data.get("results", [])
                                if "security"
                                in r.get("extra", {})
                                .get("metadata", {})
                                .get("category", "")
                                .lower()
                            ]
                        ),
                    }
                except json.JSONDecodeError:
                    self.logger.warning("Could not parse Semgrep JSON output")

            self.results.append(analysis_result)
            self.logger.info(f"✅ Semgrep analysis completed")

        except FileNotFoundError:
            self.logger.warning(
                "⚠️ Semgrep not found - install with: pip install semgrep"
            )
        except Exception as e:
            self.logger.error(f"❌ Semgrep analysis failed: {e}")

    async def _run_vulture(self) -> None:
        """Run Vulture dead code detection"""
        try:
            cmd = ["vulture", self.config.target_directory, "--min-confidence=80"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            analysis_result = AnalysisResult(
                tool_name="vulture",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

            # Parse Vulture output
            issues = []
            for line in result.stdout.split("\n"):
                if line.strip() and ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        issues.append(
                            {
                                "file": parts[0],
                                "line": parts[1],
                                "message": ":".join(parts[2:]).strip(),
                                "type": "dead_code",
                            }
                        )

            analysis_result.issues = issues
            analysis_result.metrics = {"dead_code_items": len(issues)}

            self.results.append(analysis_result)
            self.logger.info(f"✅ Vulture dead code analysis completed")

        except FileNotFoundError:
            self.logger.warning(
                "⚠️ Vulture not found - install with: pip install vulture"
            )
        except Exception as e:
            self.logger.error(f"❌ Vulture analysis failed: {e}")

    async def _run_custom_ast_analysis(self) -> None:
        """Run custom AST-based analysis"""
        try:
            issues = []
            metrics = {
                "total_functions": 0,
                "complex_functions": 0,
                "total_classes": 0,
                "total_lines": 0,
            }

            for py_file in Path(self.config.target_directory).rglob("*.py"):
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        source = f.read()
                        metrics["total_lines"] += len(source.split("\n"))

                    tree = ast.parse(source)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            metrics["total_functions"] += 1

                            # Check function complexity (simple metric)
                            complexity = self._calculate_complexity(node)
                            if complexity > self.config.max_complexity:
                                metrics["complex_functions"] += 1
                                issues.append(
                                    {
                                        "file": str(py_file),
                                        "line": node.lineno,
                                        "message": f"Function '{node.name}' has high complexity ({complexity})",
                                        "type": "complexity",
                                        "severity": "warning",
                                    }
                                )

                        elif isinstance(node, ast.ClassDef):
                            metrics["total_classes"] += 1

                except Exception as e:
                    self.logger.warning(f"Could not analyze {py_file}: {e}")

            analysis_result = AnalysisResult(
                tool_name="custom_ast",
                exit_code=0,
                stdout="",
                stderr="",
                issues=issues,
                metrics=metrics,
            )

            self.results.append(analysis_result)
            self.logger.info(f"✅ Custom AST analysis completed")

        except Exception as e:
            self.logger.error(f"❌ Custom AST analysis failed: {e}")

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    async def _run_dependency_analysis(self) -> None:
        """Analyze dependencies for security issues"""
        try:
            # Check for requirements.txt
            req_file = Path("requirements.txt")
            if not req_file.exists():
                return

            # Use safety to check for known vulnerabilities
            try:
                cmd = ["safety", "check", "--json"]
                result = subprocess.run(cmd, capture_output=True, text=True)

                analysis_result = AnalysisResult(
                    tool_name="safety",
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

                if result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        analysis_result.issues = data
                        analysis_result.metrics = {"vulnerable_packages": len(data)}
                    except json.JSONDecodeError:
                        pass

                self.results.append(analysis_result)
                self.logger.info(f"✅ Dependency security analysis completed")

            except FileNotFoundError:
                self.logger.warning(
                    "⚠️ Safety not found - install with: pip install safety"
                )

        except Exception as e:
            self.logger.error(f"❌ Dependency analysis failed: {e}")

    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        total_issues = sum(len(result.issues) for result in self.results)
        tools_run = len(self.results)

        # Categorize issues by severity
        critical_issues = []
        high_issues = []
        medium_issues = []
        low_issues = []

        for result in self.results:
            for issue in result.issues:
                severity = issue.get("severity", "medium").lower()
                if severity in ["critical", "error"]:
                    critical_issues.append(issue)
                elif severity in ["high", "warning"]:
                    high_issues.append(issue)
                elif severity in ["medium", "info"]:
                    medium_issues.append(issue)
                else:
                    low_issues.append(issue)

        # Calculate quality score
        quality_score = self._calculate_quality_score()

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "tools_run": tools_run,
                "total_issues": total_issues,
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues),
                "medium_issues": len(medium_issues),
                "low_issues": len(low_issues),
                "quality_score": quality_score,
                "overall_grade": self._get_grade(quality_score),
            },
            "tool_results": {
                result.tool_name: {
                    "exit_code": result.exit_code,
                    "issues_count": len(result.issues),
                    "metrics": result.metrics,
                }
                for result in self.results
            },
            "detailed_issues": {
                "critical": critical_issues[:10],  # Top 10 of each
                "high": high_issues[:10],
                "medium": medium_issues[:10],
                "low": low_issues[:10],
            },
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _calculate_quality_score(self) -> float:
        """Calculate overall code quality score (0-100)"""
        base_score = 100.0

        for result in self.results:
            tool_name = result.tool_name
            issue_count = len(result.issues)

            # Weight different tools differently
            if tool_name == "bandit":
                base_score -= issue_count * 10  # Security issues are critical
            elif tool_name == "pylint":
                if "pylint_score" in result.metrics:
                    pylint_score = result.metrics["pylint_score"]
                    base_score = min(
                        base_score, pylint_score * 10
                    )  # Pylint score is 0-10
            elif tool_name in ["flake8", "mypy"]:
                base_score -= issue_count * 2
            else:
                base_score -= issue_count * 1

        return max(0.0, min(100.0, base_score))

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Check specific tool results
        for result in self.results:
            if result.tool_name == "bandit" and len(result.issues) > 0:
                recommendations.append(
                    "🔐 Address security vulnerabilities identified by Bandit"
                )

            elif (
                result.tool_name == "pylint"
                and result.metrics.get("pylint_score", 10)
                < self.config.min_pylint_score
            ):
                recommendations.append(
                    f"📊 Improve Pylint score (target: {self.config.min_pylint_score})"
                )

            elif result.tool_name == "black" and result.exit_code != 0:
                recommendations.append("🎨 Format code with Black for consistency")

            elif result.tool_name == "mypy" and len(result.issues) > 0:
                recommendations.append("🏷️ Add type hints to improve code clarity")

            elif result.tool_name == "vulture" and len(result.issues) > 0:
                recommendations.append("🧹 Remove dead code identified by Vulture")

        # General recommendations
        recommendations.extend(
            [
                "📝 Set up pre-commit hooks for automated code quality checks",
                "🔄 Integrate static analysis into CI/CD pipeline",
                "📚 Establish coding standards and documentation",
                "🧪 Increase test coverage for better reliability",
            ]
        )

        return recommendations


async def main():
    """Run comprehensive static analysis"""
    config = StaticAnalysisConfig(
        target_directory="src",
        min_pylint_score=8.0,
        max_complexity=10,
        max_security_issues=0,
    )

    runner = StaticAnalysisRunner(config)

    try:
        report = await runner.run_all_analyses()

        # Save report
        with open("static_analysis_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Print summary
        print("\n" + "=" * 60)
        print("COMPREHENSIVE STATIC ANALYSIS REPORT")
        print("=" * 60)
        print(f"Overall Grade: {report['summary']['overall_grade']}")
        print(f"Quality Score: {report['summary']['quality_score']:.1f}/100")
        print(f"Total Issues: {report['summary']['total_issues']}")
        print(f"  Critical: {report['summary']['critical_issues']}")
        print(f"  High: {report['summary']['high_issues']}")
        print(f"  Medium: {report['summary']['medium_issues']}")

        print(f"\nTop Recommendations:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            print(f"  {i}. {rec}")

        print(f"\nDetailed report saved to: static_analysis_report.json")

        # Exit code based on quality
        if report["summary"]["quality_score"] >= 80:
            return 0
        elif report["summary"]["quality_score"] >= 60:
            return 1
        else:
            return 2

    except Exception as e:
        print(f"Static analysis failed: {e}")
        return 3


if __name__ == "__main__":
    import asyncio

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
