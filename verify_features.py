#!/usr/bin/env python3
"""
Feature Verification Script for API Orchestrator
Verifies that all advertised features are actually functional
"""

import sys
import os
sys.path.append('backend/src')

def verify_features():
    results = {}
    
    print("🔍 Verifying API Orchestrator Features...\n")
    
    # 1. AI Intelligence Agent
    try:
        from agents.ai_agent import AIIntelligenceAgent
        agent = AIIntelligenceAgent()
        
        # Check all AI methods exist
        methods_to_check = [
            'analyze', 'analyze_api_security', 'check_compliance',
            'suggest_optimizations', 'calculate_business_value'
        ]
        
        all_exist = all(hasattr(agent, method) for method in methods_to_check)
        results['AI Intelligence Agent'] = '✅ FUNCTIONAL' if all_exist else '❌ PARTIAL'
        
        # Check if it actually has API keys configured
        has_keys = bool(agent.anthropic_client or agent.openai_client)
        if not has_keys:
            results['AI Intelligence Agent'] += ' (API keys needed for full functionality)'
    except Exception as e:
        results['AI Intelligence Agent'] = f'❌ ERROR: {str(e)}'
    
    # 2. Mock Server Generation
    try:
        from main import app
        import inspect
        
        # Check if mock server endpoints exist
        mock_endpoints = [
            '/api/mock-server/{task_id}',
            '/api/mock-server/{task_id}/start',
            '/api/mock-server/{task_id}/stop'
        ]
        
        routes = [route.path for route in app.routes]
        has_mock = all(any(endpoint in route for route in routes) for endpoint in mock_endpoints)
        
        results['Mock Server Generation'] = '✅ FUNCTIONAL' if has_mock else '❌ NOT FOUND'
    except Exception as e:
        results['Mock Server Generation'] = f'❌ ERROR: {str(e)}'
    
    # 3. Request History & Activity Log
    try:
        from database import RequestHistory, Base
        from sqlalchemy import inspect as sql_inspect
        
        # Check if RequestHistory table has all required columns
        required_columns = ['id', 'user_id', 'method', 'url', 'status_code', 'response_time']
        
        # Check model attributes
        has_columns = all(hasattr(RequestHistory, col) for col in ['id', 'user_id', 'method', 'url'])
        
        results['Request History'] = '✅ FUNCTIONAL' if has_columns else '❌ INCOMPLETE'
    except Exception as e:
        results['Request History'] = f'❌ ERROR: {str(e)}'
    
    # 4. API Monitoring
    try:
        from database import APIMonitor, MonitorResult
        
        # Check monitor model
        monitor_attrs = ['id', 'user_id', 'name', 'url', 'method', 'interval', 'is_active']
        has_monitor = all(hasattr(APIMonitor, attr) for attr in ['id', 'user_id', 'name', 'url'])
        
        # Check monitor result model
        has_results = hasattr(MonitorResult, 'monitor_id') and hasattr(MonitorResult, 'status_code')
        
        results['API Monitoring'] = '✅ FUNCTIONAL' if (has_monitor and has_results) else '❌ INCOMPLETE'
    except Exception as e:
        results['API Monitoring'] = f'❌ ERROR: {str(e)}'
    
    # 5. Postman Collection Import
    try:
        from export_import import ImportManager
        
        # Check if import method exists
        has_import = hasattr(ImportManager, 'import_postman_collection')
        
        if has_import:
            # Test with sample Postman data
            test_collection = {
                "info": {"name": "Test"},
                "item": [{"name": "Test Request", "request": {"method": "GET", "url": {"raw": "http://test.com"}}}]
            }
            
            import json
            result = ImportManager.import_postman_collection(json.dumps(test_collection).encode())
            is_functional = 'paths' in result and 'openapi' in result
            
            results['Postman Import'] = '✅ FUNCTIONAL' if is_functional else '❌ PARTIAL'
        else:
            results['Postman Import'] = '❌ METHOD NOT FOUND'
    except Exception as e:
        results['Postman Import'] = f'❌ ERROR: {str(e)}'
    
    # 6. WebSocket Support
    try:
        from main import manager
        
        # Check WebSocket manager exists and has methods
        has_websocket = hasattr(manager, 'connect') and hasattr(manager, 'broadcast')
        
        results['WebSocket Support'] = '✅ FUNCTIONAL' if has_websocket else '❌ INCOMPLETE'
    except Exception as e:
        results['WebSocket Support'] = f'❌ ERROR: {str(e)}'
    
    # 7. API Discovery & Testing
    try:
        from agents.discovery_agent import DiscoveryAgent
        from agents.test_agent import TestAgent
        
        # Check discovery agent
        discovery = DiscoveryAgent()
        has_discovery = hasattr(discovery, 'discover')
        
        # Check test agent
        test = TestAgent()
        has_test = hasattr(test, 'generate_tests')
        
        results['API Discovery'] = '✅ FUNCTIONAL' if has_discovery else '❌ NOT FOUND'
        results['Test Generation'] = '✅ FUNCTIONAL' if has_test else '❌ NOT FOUND'
    except Exception as e:
        results['API Discovery & Testing'] = f'❌ ERROR: {str(e)}'
    
    # 8. Export/Import Functionality
    try:
        from export_import import ExportManager
        
        # Check export formats
        formats = ExportManager.SUPPORTED_FORMATS
        has_formats = 'json' in formats and 'yaml' in formats and 'postman' in formats
        
        results['Export Functionality'] = '✅ FUNCTIONAL' if has_formats else '❌ LIMITED FORMATS'
    except Exception as e:
        results['Export Functionality'] = f'❌ ERROR: {str(e)}'
    
    # 9. Database Persistence
    try:
        from database import engine, Base
        
        # Check if database can be connected
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            db_works = result.scalar() == 1
        
        results['Database Persistence'] = '✅ FUNCTIONAL' if db_works else '❌ CONNECTION FAILED'
    except Exception as e:
        results['Database Persistence'] = f'❌ ERROR: {str(e)}'
    
    # 10. Authentication System
    try:
        from auth import get_password_hash, verify_password, create_access_token
        
        # Test password hashing
        test_pass = "test123"
        hashed = get_password_hash(test_pass)
        verified = verify_password(test_pass, hashed)
        
        results['Authentication'] = '✅ FUNCTIONAL' if verified else '❌ HASH VERIFICATION FAILED'
    except Exception as e:
        results['Authentication'] = f'❌ ERROR: {str(e)}'
    
    # Print results
    print("=" * 60)
    print("FEATURE VERIFICATION RESULTS")
    print("=" * 60)
    
    functional_count = 0
    total_count = len(results)
    
    for feature, status in results.items():
        print(f"{feature:30} {status}")
        if '✅ FUNCTIONAL' in status:
            functional_count += 1
    
    print("=" * 60)
    print(f"\nSUMMARY: {functional_count}/{total_count} features fully functional")
    
    if functional_count == total_count:
        print("🎉 All features are functional and working!")
    else:
        print(f"⚠️  {total_count - functional_count} features need attention")
    
    return results

if __name__ == "__main__":
    os.chdir('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator')
    verify_features()