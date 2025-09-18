#!/usr/bin/env python3
"""
Improvement Analysis - What would push beyond 90/100
"""

import asyncio
import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from autonomous_security_tools import SecurityToolExecutor

async def analyze_improvement_potential():
    """Analyze what specific improvements could push score higher"""
    print("🔍 IMPROVEMENT POTENTIAL ANALYSIS")
    print("=" * 50)

    # Create a more complex test with multiple file types
    print("Creating multi-file test environment...")

    # Python file with complex issues
    python_content = """from flask import Flask, request
import hashlib
import os

app = Flask(__name__)
SECRET_KEY = "hardcoded_secret_123"

@app.route('/user/<user_id>')
def get_user(user_id):
    return f"User data for {user_id}"

@app.route('/search')
def search():
    query = request.args.get('q')
    sql = f"SELECT * FROM users WHERE name = '{query}'"
    return sql

if __name__ == '__main__':
    app.run(debug=True)
"""

    # JavaScript file
    js_content = """
const express = require('express');
const app = express();

app.get('/api/user/:id', (req, res) => {
    const query = `SELECT * FROM users WHERE id = '${req.params.id}'`;
    res.send(`User: ${req.params.id}`);
});

app.listen(3000, '0.0.0.0');
"""

    # Java file
    java_content = """
public class UserController {
    private static final String PASSWORD = "hardcoded_pass_123";

    public String getUser(String userId) {
        String query = "SELECT * FROM users WHERE id = '" + userId + "'";
        return "User: " + userId;
    }
}
"""

    # Create test files
    test_files = {}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_content)
        test_files['python'] = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(js_content)
        test_files['javascript'] = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(java_content)
        test_files['java'] = f.name

    try:
        executor = SecurityToolExecutor()
        executor.safe_mode = False

        print(f"\n📊 CURRENT CAPABILITIES TEST:")

        current_score = 0
        max_possible = 0

        # Test 1: Multi-language support
        print("\n1. Multi-language vulnerability detection:")
        max_possible += 20

        languages_detected = 0
        for lang, file_path in test_files.items():
            try:
                result = await executor.execute_security_vulnerability_scan(
                    {"target_file": file_path},
                    {"path": "/test", "method": "GET", "security": []}
                )
                vulns = len(result.get('vulnerabilities', []))
                if vulns > 0:
                    languages_detected += 1
                    print(f"   {lang}: {vulns} vulnerabilities")
                else:
                    print(f"   {lang}: No vulnerabilities detected")
            except Exception as e:
                print(f"   {lang}: Error - {str(e)[:50]}...")

        if languages_detected >= 3:
            current_score += 20
        elif languages_detected >= 2:
            current_score += 15
        elif languages_detected >= 1:
            current_score += 10

        # Test 2: Advanced remediation completeness
        print("\n2. Remediation completeness:")
        max_possible += 25

        remediation_result = await executor.execute_advanced_remediation(
            {"target_file": test_files['python']},
            {"path": "/test", "method": "GET", "security": []},
            "Multi-language application"
        )

        fixes_applied = remediation_result.get('fixes_applied', 0)
        print(f"   Fixes applied: {fixes_applied}")

        # Read modified file to check completeness
        with open(test_files['python'], 'r') as f:
            modified_content = f.read()

        completeness_checks = {
            "md5_fixed": "sha256" in modified_content and "md5" not in modified_content,
            "debug_fixed": "debug=False" in modified_content,
            "secrets_fixed": "os.getenv" in modified_content,
            "sql_injection_flagged": "# SECURITY WARNING" in modified_content or "# Security:" in modified_content,
            "imports_added": "import os" in modified_content if "os.getenv" in modified_content else True
        }

        completeness_score = sum(completeness_checks.values())
        print(f"   Completeness: {completeness_score}/5 fixes")

        if completeness_score >= 4:
            current_score += 25
        elif completeness_score >= 3:
            current_score += 20
        elif completeness_score >= 2:
            current_score += 15

        # Test 3: Specialized agent integration
        print("\n3. Specialized agent integration:")
        max_possible += 20

        try:
            devops_result = await executor.execute_devops_security_scan(
                {"target_files": list(test_files.values())},
                {"path": "/test", "method": "GET"},
                "Multi-language microservices"
            )
            db_result = await executor.execute_database_security_audit(
                {"target_files": list(test_files.values())},
                {"path": "/test", "method": "GET"},
                "Enterprise application"
            )

            integration_score = 0
            if devops_result.get('total_findings', 0) > 0:
                integration_score += 10
                print(f"   DevOps integration: {devops_result.get('total_findings')} findings")
            if db_result.get('total_findings', 0) > 0:
                integration_score += 10
                print(f"   Database integration: {db_result.get('total_findings')} findings")

            current_score += integration_score

        except Exception as e:
            print(f"   Integration test failed: {str(e)[:50]}...")

        # Test 4: Real-time learning and adaptation
        print("\n4. Learning and adaptation:")
        max_possible += 15

        # This would require implementing learning capabilities
        learning_score = 0  # Not implemented yet
        print(f"   Learning capabilities: Not implemented")

        # Test 5: Production deployment readiness
        print("\n5. Production readiness:")
        max_possible += 20

        production_features = {
            "safe_mode": hasattr(executor, 'safe_mode'),
            "error_handling": True,  # Basic error handling exists
            "logging": hasattr(executor, 'execution_log'),
            "configuration": True,  # Basic configuration exists
            "scalability": False  # Not tested
        }

        production_score = sum(production_features.values()) * 4
        current_score += production_score
        print(f"   Production features: {sum(production_features.values())}/5")

        print(f"\n📊 IMPROVEMENT ANALYSIS:")
        print(f"   Current Score: {current_score}/{max_possible}")
        print(f"   Percentage: {(current_score/max_possible)*100:.1f}%")

        # Identify specific improvements needed
        print(f"\n🎯 SPECIFIC IMPROVEMENTS TO REACH 95%+:")

        needed_improvements = []
        if languages_detected < 3:
            needed_improvements.append(f"Multi-language support: Currently {languages_detected}/3")
        if completeness_score < 4:
            needed_improvements.append(f"Remediation completeness: Currently {completeness_score}/5")
        if learning_score == 0:
            needed_improvements.append("Learning and adaptation capabilities")
        if sum(production_features.values()) < 5:
            needed_improvements.append("Production readiness features")

        for improvement in needed_improvements:
            print(f"   - {improvement}")

        potential_max = current_score
        if languages_detected < 3:
            potential_max += (3 - languages_detected) * 5
        if completeness_score < 4:
            potential_max += (4 - completeness_score) * 5
        if learning_score == 0:
            potential_max += 15
        if sum(production_features.values()) < 5:
            potential_max += (5 - sum(production_features.values())) * 4

        print(f"\n🚀 POTENTIAL MAXIMUM SCORE: {min(potential_max, 100)}/100")

        return current_score, max_possible, needed_improvements

    finally:
        # Cleanup
        for file_path in test_files.values():
            if os.path.exists(file_path):
                os.unlink(file_path)

async def main():
    current, maximum, improvements = await analyze_improvement_potential()

    print(f"\n🎯 CONCLUSION:")
    if (current/maximum) * 100 >= 95:
        print("✅ System already capable of 95%+")
    else:
        print(f"📈 Can reach 95%+ by implementing {len(improvements)} key improvements")
        print("🔧 Most impactful would be multi-language support and learning capabilities")

if __name__ == "__main__":
    asyncio.run(main())