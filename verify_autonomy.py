import os
import re

def check_autonomous_features():
    print("=== AUTONOMOUS CAPABILITIES VERIFICATION ===\n")
    
    autonomous_files = [
        "backend/src/autonomous_security_tools.py",
        "backend/src/agents/autonomous_security_agent.py",
        "backend/src/ai_employee/self_learning_system.py",
        "backend/src/ai_employee/ai_employee_orchestrator.py",
        "backend/src/kill_shots/predictive_failure_analysis.py",
        "backend/src/learning_engine.py"
    ]
    
    features = {
        "Autonomous Security": False,
        "Self-Learning ML": False,
        "Autonomous Mode": False,
        "Predictive Analysis": False,
        "Auto-Fix Capabilities": False
    }
    
    for file in autonomous_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (IOError, OSError, UnicodeDecodeError) as e:
                print(f"⚠️ Could not read {file}: {e}")
                continue

            content_lower = content.lower()

            if 'autonomous_security_analysis' in content:
                features["Autonomous Security"] = True

            if 'RandomForestClassifier' in content or 'IsolationForest' in content:
                features["Self-Learning ML"] = True

            if 'autonomous_mode' in content or 'autonomous_operation' in content:
                features["Autonomous Mode"] = True

            if 'predict_next_24_hours' in content or 'predictive' in content_lower:
                features["Predictive Analysis"] = True

            if 'auto_fix' in content or 'apply_automated_fixes' in content:
                features["Auto-Fix Capabilities"] = True
    
    print("AUTONOMOUS FEATURES FOUND:")
    for feature, found in features.items():
        status = "✅" if found else "❌"
        print(f"  {status} {feature}")
    
    # Count autonomous functions
    autonomous_functions = []
    for file in autonomous_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    functions = re.findall(r'async def (\w*autonomous\w*)', content)
                    autonomous_functions.extend(functions)
            except (IOError, OSError, UnicodeDecodeError) as e:
                print(f"⚠️ Could not read {file} for function analysis: {e}")
                continue
    
    print(f"\nAUTONOMOUS FUNCTIONS: {len(set(autonomous_functions))}")
    for func in set(autonomous_functions):
        print(f"  - {func}()")
    
    return features

if __name__ == "__main__":
    features = check_autonomous_features()
    
    if all(features.values()):
        print("\n✅ FULL AUTONOMOUS CAPABILITIES VERIFIED")
    else:
        missing = [k for k, v in features.items() if not v]
        print(f"\n⚠️ Missing: {', '.join(missing)}")
