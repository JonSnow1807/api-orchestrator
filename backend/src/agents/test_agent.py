import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import textwrap

from src.core.orchestrator import AgentMessage, AgentType

class TestGeneratorAgent:
    """Agent responsible for generating test suites from API specifications"""
    
    def __init__(self):
        self.test_frameworks = {
            'pytest': self._generate_pytest,
            'unittest': self._generate_unittest,
            'jest': self._generate_jest,
            'mocha': self._generate_mocha,
            'postman': self._generate_postman_collection,
            'locust': self._generate_locust_tests
        }
        self.generated_tests = []
        
    async def create_tests(self, spec: Dict, options: Dict = None) -> List[Dict]:
        """Generate test suites from OpenAPI specification"""
        self.generated_tests = []
        
        # Default options
        test_options = {
            'frameworks': ['pytest', 'postman'],
            'include_negative': True,
            'include_edge_cases': True,
            'include_load_tests': False,
            'coverage_target': 100
        }
        
        if options:
            test_options.update(options)
        
        # Extract API info
        api_info = spec.get('info', {})
        servers = spec.get('servers', [{'url': 'http://localhost:8000'}])
        paths = spec.get('paths', {})
        schemas = spec.get('components', {}).get('schemas', {})
        
        print(f"📝 Generating tests for {len(paths)} endpoints...")
        
        # Generate tests for each framework
        for framework in test_options['frameworks']:
            if framework in self.test_frameworks:
                generator = self.test_frameworks[framework]
                tests = generator(spec, test_options)
                self.generated_tests.extend(tests)
                print(f"  ✓ Generated {framework} tests")
        
        # Generate load tests if requested
        if test_options.get('include_load_tests'):
            locust_tests = self._generate_locust_tests(spec, test_options)
            self.generated_tests.extend(locust_tests)
            print(f"  ✓ Generated Locust load tests")
        
        return self.generated_tests
    
    def _generate_pytest(self, spec: Dict, options: Dict) -> List[Dict]:
        """Generate pytest test suites"""
        tests = []
        base_url = spec.get('servers', [{'url': 'http://localhost:8000'}])[0]['url']
        paths = spec.get('paths', {})
        
        # Generate test file content
        test_content = self._generate_pytest_header(base_url)
        
        # Generate fixtures
        fixtures = self._generate_pytest_fixtures(spec)
        test_content += fixtures + "\n\n"
        
        # Generate test class for each tag/resource
        test_classes = {}
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                tags = operation.get('tags', ['Default'])
                tag = tags[0] if tags else 'Default'
                
                if tag not in test_classes:
                    test_classes[tag] = []
                
                # Generate positive test
                test_name = f"test_{method}_{self._sanitize_name(path)}"
                test_code = self._generate_pytest_test_method(
                    path, method, operation, base_url, positive=True
                )
                test_classes[tag].append((test_name, test_code))
                
                # Generate negative tests if requested
                if options.get('include_negative'):
                    neg_test_name = f"test_{method}_{self._sanitize_name(path)}_invalid"
                    neg_test_code = self._generate_pytest_test_method(
                        path, method, operation, base_url, positive=False
                    )
                    test_classes[tag].append((neg_test_name, neg_test_code))
        
        # Compile test classes
        for tag, test_methods in test_classes.items():
            class_content = f"class Test{tag}API:\n"
            class_content += '    """Test suite for ' + tag + ' endpoints"""\n\n'
            
            for test_name, test_code in test_methods:
                class_content += test_code + "\n"
            
            test_content += class_content + "\n"
        
        # Add integration tests
        if options.get('include_edge_cases'):
            test_content += self._generate_integration_tests(spec)
        
        tests.append({
            'framework': 'pytest',
            'filename': 'test_api_generated.py',
            'content': test_content,
            'type': 'unit_tests'
        })
        
        # Generate conftest.py with shared fixtures
        conftest_content = self._generate_conftest(spec)
        tests.append({
            'framework': 'pytest',
            'filename': 'conftest.py',
            'content': conftest_content,
            'type': 'fixtures'
        })
        
        return tests
    
    def _generate_pytest_header(self, base_url: str) -> str:
        """Generate pytest file header with imports"""
        return f'''"""
Auto-generated API tests
Generated by API Orchestrator
Timestamp: {datetime.now().isoformat()}
"""

import pytest
import requests
import json
from typing import Dict, Any
from datetime import datetime
import time

BASE_URL = "{base_url}"
HEADERS = {{"Content-Type": "application/json"}}

'''
    
    def _generate_pytest_fixtures(self, spec: Dict) -> str:
        """Generate pytest fixtures"""
        fixtures = '''@pytest.fixture
def client():
    """HTTP client for API requests"""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

@pytest.fixture
def auth_headers():
    """Authentication headers"""
    # TODO: Implement actual authentication
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def test_data():
    """Sample test data"""
    return {
        "name": "Test Item",
        "description": "Test Description",
        "value": 100,
        "active": True
    }
'''
        return fixtures
    
    def _generate_pytest_test_method(self, path: str, method: str, 
                                    operation: Dict, base_url: str, 
                                    positive: bool = True) -> str:
        """Generate individual test method"""
        method_upper = method.upper()
        test_name = f"test_{method}_{self._sanitize_name(path)}"
        if not positive:
            test_name += "_invalid"
        
        # Build the URL with path parameters
        url_template = f'"{base_url}{path}"'
        path_params = self._extract_path_params(path)
        
        if path_params:
            # Replace path parameters with test values
            for param in path_params:
                if positive:
                    url_template = url_template.replace(f"{{{param}}}", "test-id")
                else:
                    url_template = url_template.replace(f"{{{param}}}", "invalid-id")
        
        # Generate test body based on method
        if positive:
            test_code = f'''    def {test_name}(self, client):
        """Test {method_upper} {path} - positive case"""
        url = {url_template}
        '''
            
            if method_upper in ['POST', 'PUT', 'PATCH']:
                test_code += '''
        data = {
            "name": "Test",
            "value": 123
        }
        response = client.''' + method.lower() + '''(url, json=data)
        '''
            else:
                test_code += f'''
        response = client.{method.lower()}(url)
        '''
            
            # Add assertions
            if method_upper == 'DELETE':
                test_code += '''
        assert response.status_code in [204, 200]
'''
            elif method_upper == 'POST':
                test_code += '''
        assert response.status_code in [201, 200]
        assert response.json()
'''
            else:
                test_code += '''
        assert response.status_code == 200
        assert response.json()
'''
        else:
            # Negative test case
            test_code = f'''    def {test_name}(self, client):
        """Test {method_upper} {path} - negative case"""
        url = {url_template}
        '''
            
            if method_upper in ['POST', 'PUT', 'PATCH']:
                test_code += '''
        # Invalid data
        data = {"invalid_field": "invalid_value"}
        response = client.''' + method.lower() + '''(url, json=data)
        assert response.status_code == 400
'''
            else:
                test_code += '''
        # Invalid request
        response = client.''' + method.lower() + '''(url)
        assert response.status_code in [400, 404]
'''
        
        return test_code
    
    def _generate_integration_tests(self, spec: Dict) -> str:
        """Generate integration tests that test workflows"""
        return '''class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_crud_workflow(self, client):
        """Test complete CRUD workflow"""
        # Create
        create_response = client.post(f"{BASE_URL}/items", json={"name": "Test"})
        assert create_response.status_code in [201, 200]
        item_id = create_response.json().get("id")
        
        # Read
        get_response = client.get(f"{BASE_URL}/items/{item_id}")
        assert get_response.status_code == 200
        
        # Update
        update_response = client.put(f"{BASE_URL}/items/{item_id}", json={"name": "Updated"})
        assert update_response.status_code == 200
        
        # Delete
        delete_response = client.delete(f"{BASE_URL}/items/{item_id}")
        assert delete_response.status_code in [204, 200]
        
        # Verify deletion
        verify_response = client.get(f"{BASE_URL}/items/{item_id}")
        assert verify_response.status_code == 404
    
    def test_pagination(self, client):
        """Test pagination parameters"""
        response = client.get(f"{BASE_URL}/items", params={"limit": 10, "offset": 0})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "data" in data
    
    def test_filtering(self, client):
        """Test filtering capabilities"""
        response = client.get(f"{BASE_URL}/items", params={"status": "active"})
        assert response.status_code == 200
'''
    
    def _generate_conftest(self, spec: Dict) -> str:
        """Generate conftest.py with shared fixtures"""
        return '''"""
Shared pytest fixtures and configuration
"""

import pytest
import requests
from typing import Generator

@pytest.fixture(scope="session")
def api_client() -> Generator:
    """Session-scoped API client"""
    client = requests.Session()
    client.headers.update({"Content-Type": "application/json"})
    yield client
    client.close()

@pytest.fixture(scope="function")
def cleanup():
    """Cleanup fixture for test isolation"""
    created_ids = []
    yield created_ids
    # Cleanup created resources
    for resource_id in created_ids:
        try:
            requests.delete(f"http://localhost:8000/items/{resource_id}")
        except:
            pass

@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User"
    }

@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    start = time.time()
    yield
    duration = time.time() - start
    print(f"\\nTest duration: {duration:.3f}s")
'''
    
    def _generate_postman_collection(self, spec: Dict, options: Dict) -> List[Dict]:
        """Generate Postman collection from OpenAPI spec"""
        collection = {
            "info": {
                "name": spec.get('info', {}).get('title', 'API Collection'),
                "description": spec.get('info', {}).get('description', ''),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [],
            "variable": [
                {
                    "key": "baseUrl",
                    "value": spec.get('servers', [{'url': 'http://localhost:8000'}])[0]['url']
                }
            ]
        }
        
        # Group requests by tags
        folders = {}
        paths = spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                tags = operation.get('tags', ['Default'])
                tag = tags[0] if tags else 'Default'
                
                if tag not in folders:
                    folders[tag] = {
                        "name": tag,
                        "item": []
                    }
                
                # Create Postman request
                request = self._create_postman_request(path, method, operation)
                folders[tag]["item"].append(request)
        
        # Add folders to collection
        collection["item"] = list(folders.values())
        
        # Add test scripts
        collection["event"] = [
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "pm.test('Status code is successful', function () {",
                        "    pm.response.to.have.status(200);",
                        "});",
                        "",
                        "pm.test('Response time is less than 500ms', function () {",
                        "    pm.expect(pm.response.responseTime).to.be.below(500);",
                        "});"
                    ]
                }
            }
        ]
        
        return [{
            'framework': 'postman',
            'filename': 'api_collection.postman_collection.json',
            'content': json.dumps(collection, indent=2),
            'type': 'postman_collection'
        }]
    
    def _create_postman_request(self, path: str, method: str, operation: Dict) -> Dict:
        """Create a Postman request object"""
        request = {
            "name": operation.get('summary', f"{method.upper()} {path}"),
            "request": {
                "method": method.upper(),
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}" + path,
                    "host": ["{{baseUrl}}"],
                    "path": path.strip('/').split('/')
                }
            },
            "response": []
        }
        
        # Add description
        if operation.get('description'):
            request["request"]["description"] = operation['description']
        
        # Add headers
        request["request"]["header"].append({
            "key": "Content-Type",
            "value": "application/json"
        })
        
        # Add authentication if required
        if operation.get('security'):
            request["request"]["header"].append({
                "key": "Authorization",
                "value": "Bearer {{token}}"
            })
        
        # Add request body for POST/PUT/PATCH
        if method.upper() in ['POST', 'PUT', 'PATCH'] and operation.get('requestBody'):
            request["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(self._generate_sample_data(operation['requestBody']), indent=2),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
        
        # Add query parameters
        if operation.get('parameters'):
            query_params = []
            for param in operation['parameters']:
                if param.get('in') == 'query':
                    query_params.append({
                        "key": param['name'],
                        "value": self._get_sample_value(param.get('schema', {})),
                        "description": param.get('description', '')
                    })
            if query_params:
                request["request"]["url"]["query"] = query_params
        
        return request
    
    def _generate_locust_tests(self, spec: Dict, options: Dict) -> List[Dict]:
        """Generate Locust load testing scripts"""
        paths = spec.get('paths', {})
        base_url = spec.get('servers', [{'url': 'http://localhost:8000'}])[0]['url']
        
        locust_content = f'''"""
Locust load testing script
Auto-generated from OpenAPI specification
"""

from locust import HttpUser, task, between
import random
import json

class APIUser(HttpUser):
    wait_time = between(1, 3)
    host = "{base_url}"
    
    def on_start(self):
        """Setup method called when user starts"""
        # Perform authentication if needed
        self.headers = {{"Content-Type": "application/json"}}
        self.test_data = {{
            "name": f"LoadTest_{{random.randint(1, 10000)}}",
            "value": random.randint(1, 1000)
        }}
'''
        
        # Generate tasks for each endpoint
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                    task_name = f"{method}_{self._sanitize_name(path)}"
                    weight = 10 if method.upper() == 'GET' else 5  # GET requests more frequent
                    
                    locust_content += f'''
    @task({weight})
    def {task_name}(self):
        """Test {method.upper()} {path}"""
'''
                    
                    # Build the URL
                    url = path
                    path_params = self._extract_path_params(path)
                    if path_params:
                        for param in path_params:
                            url = url.replace(f"{{{param}}}", f"{{random.randint(1, 100)}}")
                        url = f'f"{url}"'
                    else:
                        url = f'"{url}"'
                    
                    # Generate request based on method
                    if method.upper() == 'GET':
                        locust_content += f'''        self.client.get({url}, headers=self.headers, name="{method.upper()} {path}")
'''
                    elif method.upper() == 'POST':
                        locust_content += f'''        self.client.post({url}, json=self.test_data, headers=self.headers, name="{method.upper()} {path}")
'''
                    elif method.upper() == 'PUT':
                        locust_content += f'''        self.client.put({url}, json=self.test_data, headers=self.headers, name="{method.upper()} {path}")
'''
                    elif method.upper() == 'DELETE':
                        locust_content += f'''        self.client.delete({url}, headers=self.headers, name="{method.upper()} {path}")
'''
        
        # Add performance monitoring tasks
        locust_content += '''
    @task(2)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/health", name="Health Check")
    
class AdminUser(HttpUser):
    """Simulates admin users with different behavior"""
    wait_time = between(5, 10)
    host = "''' + base_url + '''"
    
    @task
    def admin_operations(self):
        """Perform admin-specific operations"""
        # Add admin-specific tasks here
        pass
'''
        
        return [{
            'framework': 'locust',
            'filename': 'locustfile.py',
            'content': locust_content,
            'type': 'load_tests'
        }]
    
    def export_tests(self, output_dir: str):
        """Export generated tests to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for test in self.generated_tests:
            filename = test.get('filename', 'test.py')
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                f.write(test.get('content', ''))
            
            print(f"  ✓ Exported {test.get('framework')} tests to {filepath}")
        
        return len(self.generated_tests)
    
    def _generate_unittest(self, spec: Dict, options: Dict) -> List[Dict]:
        """Generate unittest test suites"""
        # Similar structure to pytest but using unittest framework
        tests = []
        base_url = spec.get('servers', [{'url': 'http://localhost:8000'}])[0]['url']
        paths = spec.get('paths', {})
        
        test_content = f'''"""
Auto-generated unittest test suite
Generated: {datetime.now().isoformat()}
"""

import unittest
import requests
import json
from typing import Dict, Any

BASE_URL = "{base_url}"

class APITestCase(unittest.TestCase):
    """Base test case for API testing"""
    
    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()
        cls.session.headers.update({{"Content-Type": "application/json"}})
    
    @classmethod
    def tearDownClass(cls):
        cls.session.close()
'''
        
        # Generate test methods
        for path, methods in paths.items():
            for method, operation in methods.items():
                test_method = self._generate_unittest_method(path, method, operation, base_url)
                test_content += test_method
        
        test_content += '''
if __name__ == '__main__':
    unittest.main()
'''
        
        tests.append({
            'framework': 'unittest',
            'filename': 'test_api_unittest.py',
            'content': test_content,
            'type': 'unit_tests'
        })
        
        return tests
    
    def _generate_unittest_method(self, path: str, method: str, 
                                 operation: Dict, base_url: str) -> str:
        """Generate unittest test method"""
        test_name = f"test_{method}_{self._sanitize_name(path)}"
        url = f'"{base_url}{path}"'
        
        return f'''
    def {test_name}(self):
        """Test {method.upper()} {path}"""
        response = self.session.{method.lower()}({url})
        self.assertIn(response.status_code, [200, 201, 204])
'''
    
    def _generate_jest(self, spec: Dict, options: Dict) -> List[Dict]:
        """Generate Jest test suites for JavaScript/TypeScript"""
        tests = []
        base_url = spec.get('servers', [{'url': 'http://localhost:8000'}])[0]['url']
        paths = spec.get('paths', {})
        
        test_content = f'''/**
 * Auto-generated Jest test suite
 * Generated: {datetime.now().isoformat()}
 */

const axios = require('axios');

const BASE_URL = '{base_url}';
const api = axios.create({{
  baseURL: BASE_URL,
  headers: {{ 'Content-Type': 'application/json' }}
}});

describe('API Tests', () => {{
'''
        
        # Group tests by tags
        test_suites = {}
        for path, methods in paths.items():
            for method, operation in methods.items():
                tags = operation.get('tags', ['Default'])
                tag = tags[0] if tags else 'Default'
                
                if tag not in test_suites:
                    test_suites[tag] = []
                
                test = self._generate_jest_test(path, method, operation)
                test_suites[tag].append(test)
        
        # Generate test suites
        for suite_name, suite_tests in test_suites.items():
            test_content += f'''
  describe('{suite_name} API', () => {{
'''
            for test in suite_tests:
                test_content += test
            test_content += '  });\n'
        
        test_content += '});\n'
        
        tests.append({
            'framework': 'jest',
            'filename': 'api.test.js',
            'content': test_content,
            'type': 'unit_tests'
        })
        
        return tests
    
    def _generate_jest_test(self, path: str, method: str, operation: Dict) -> str:
        """Generate individual Jest test"""
        test_name = f"{method.upper()} {path}"
        
        test_code = f'''
    test('{test_name}', async () => {{
      const response = await api.{method.lower()}('{path}');
      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
    }});
'''
        return test_code
    
    def _generate_mocha(self, spec: Dict, options: Dict) -> List[Dict]:
        """Generate Mocha test suites"""
        # Similar to Jest but with Mocha/Chai syntax
        tests = []
        base_url = spec.get('servers', [{'url': 'http://localhost:8000'}])[0]['url']
        
        test_content = f'''/**
 * Auto-generated Mocha test suite
 */

const chai = require('chai');
const chaiHttp = require('chai-http');
const expect = chai.expect;

chai.use(chaiHttp);

const BASE_URL = '{base_url}';

describe('API Tests', function() {{
  // Test implementation here
}});
'''
        
        tests.append({
            'framework': 'mocha',
            'filename': 'test.spec.js',
            'content': test_content,
            'type': 'unit_tests'
        })
        
        return tests
    
    def _sanitize_name(self, path: str) -> str:
        """Sanitize path to valid function name"""
        # Remove special characters and convert to snake_case
        name = re.sub(r'[{}/\-:]', '_', path)
        name = re.sub(r'_+', '_', name)
        return name.strip('_').lower()
    
    def _extract_path_params(self, path: str) -> List[str]:
        """Extract parameter names from path"""
        pattern = r'\{([^}]+)\}'
        return re.findall(pattern, path)
    
    def _generate_sample_data(self, request_body: Dict) -> Dict:
        """Generate sample data based on request body schema"""
        if not request_body:
            return {}
        
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        schema = json_content.get('schema', {})
        
        if schema.get('type') == 'object':
            sample = {}
            properties = schema.get('properties', {})
            for prop_name, prop_schema in properties.items():
                sample[prop_name] = self._get_sample_value(prop_schema)
            return sample
        
        return {"sample": "data"}
    
    def _get_sample_value(self, schema: Dict) -> Any:
        """Get sample value based on schema type"""
        schema_type = schema.get('type', 'string')
        
        if schema_type == 'string':
            if 'enum' in schema:
                return schema['enum'][0]
            elif schema.get('format') == 'date-time':
                return datetime.now().isoformat()
            elif schema.get('format') == 'email':
                return "test@example.com"
            elif schema.get('format') == 'uuid':
                return "123e4567-e89b-12d3-a456-426614174000"
            else:
                return "sample_string"
        elif schema_type == 'integer':
            return 123
        elif schema_type == 'number':
            return 123.45
        elif schema_type == 'boolean':
            return True
        elif schema_type == 'array':
            item_schema = schema.get('items', {})
            return [self._get_sample_value(item_schema)]
        elif schema_type == 'object':
            return self._generate_sample_data({'content': {'application/json': {'schema': schema}}})
        else:
            return None
    
    async def handle_message(self, message: AgentMessage):
        """Handle messages from other agents"""
        if message.action == "generate_specific_test":
            # Generate test for specific endpoint
            endpoint = message.payload.get("endpoint")
            framework = message.payload.get("framework", "pytest")
            # Implementation for specific test generation
            pass
        elif message.action == "update_test_coverage":
            # Update test coverage requirements
            coverage = message.payload.get("coverage_target")
            # Implementation for coverage updates
            pass
    
    def export_tests(self, output_dir: str = "./tests") -> Dict[str, str]:
        """Export all generated tests to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        for test in self.generated_tests:
            file_path = output_path / test['filename']
            file_path.write_text(test['content'])
            exported_files[test['framework']] = str(file_path)
            print(f"  ✓ Exported {test['framework']} tests to {file_path}")
        
        return exported_files
    
    def get_test_statistics(self) -> Dict:
        """Get statistics about generated tests"""
        stats = {
            'total_tests': len(self.generated_tests),
            'frameworks': {},
            'test_types': {}
        }
        
        for test in self.generated_tests:
            framework = test['framework']
            test_type = test['type']
            
            if framework not in stats['frameworks']:
                stats['frameworks'][framework] = 0
            stats['frameworks'][framework] += 1
            
            if test_type not in stats['test_types']:
                stats['test_types'][test_type] = 0
            stats['test_types'][test_type] += 1
        
        return stats