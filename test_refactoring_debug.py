#!/usr/bin/env python3
"""
Debug Smart Refactoring - Test refactoring patterns
"""

import asyncio
import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from smart_refactoring_engine import SmartRefactoringEngine

async def test_refactoring_debug():
    """Test refactoring patterns in isolation"""
    print("🔧 DEBUGGING SMART REFACTORING")
    print("=" * 40)

    # Simple test content with clear patterns
    test_content = """from flask import Flask, request

app = Flask(__name__)

@app.route('/test')
def test():
    query = request.args['query']  # Should be refactored
    return f"Hello {query}"  # Should be flagged for XSS

def process_data(items):
    result = ""
    for item in items:
        result += str(item) + " "
    return result

if __name__ == '__main__':
    app.run(debug=True)
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name

    print(f"📁 Created debug test file: {temp_file_path}")

    try:
        # Create refactoring engine
        engine = SmartRefactoringEngine()
        engine.safe_mode = False  # Enable all refactoring

        print("\n📋 Original content:")
        print(test_content)

        # Test security patterns
        print("\n🔍 Testing security patterns...")
        security_patterns = engine._security_refactoring_patterns(test_content)
        print(f"Found {len(security_patterns)} security patterns:")
        for i, pattern in enumerate(security_patterns):
            print(f"  {i+1}. {pattern['type']}: {pattern['description']} (severity: {pattern['severity']})")

        # Test performance patterns
        print("\n⚡ Testing performance patterns...")
        performance_patterns = engine._performance_refactoring_patterns(test_content)
        print(f"Found {len(performance_patterns)} performance patterns:")
        for i, pattern in enumerate(performance_patterns):
            print(f"  {i+1}. {pattern['type']}: {pattern['description']} (severity: {pattern['severity']})")

        # Apply refactoring
        print("\n🔧 Applying refactoring...")
        result = await engine.analyze_and_refactor_code(temp_file_path, "security")

        print(f"Refactoring result: {result}")

        # Read modified content
        with open(temp_file_path, 'r') as f:
            modified_content = f.read()

        print("\n📝 Modified content:")
        print(modified_content)

        # Check what changed
        if modified_content != test_content:
            print("✅ File was modified!")
        else:
            print("❌ No changes applied")

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print("🗑️ Cleaned up")

if __name__ == "__main__":
    asyncio.run(test_refactoring_debug())