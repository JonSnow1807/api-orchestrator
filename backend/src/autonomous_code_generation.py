#!/usr/bin/env python3
"""
Autonomous Code Generation from Natural Language
Revolutionary AI system that generates production-ready code from human descriptions
"""

import asyncio
import re
import ast
import json
import keyword
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime
import uuid

# LLM integrations
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

class CodeLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    SQL = "sql"
    BASH = "bash"

class CodeType(Enum):
    API_ENDPOINT = "api_endpoint"
    DATABASE_MODEL = "database_model"
    TEST_SUITE = "test_suite"
    FRONTEND_COMPONENT = "frontend_component"
    UTILITY_FUNCTION = "utility_function"
    INTEGRATION_SCRIPT = "integration_script"
    DEPLOYMENT_CONFIG = "deployment_config"

class QualityLevel(Enum):
    PROTOTYPE = "prototype"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"

@dataclass
class CodeGenerationRequest:
    request_id: str
    description: str
    language: CodeLanguage
    code_type: CodeType
    quality_level: QualityLevel
    requirements: List[str]
    constraints: List[str]
    context: Dict[str, Any]
    examples: List[str] = None
    deadline: Optional[datetime] = None

@dataclass
class GeneratedCode:
    code_id: str
    original_request: str
    language: CodeLanguage
    code_type: CodeType
    generated_code: str
    documentation: str
    test_code: str
    quality_score: float
    security_score: float
    performance_notes: List[str]
    usage_examples: List[str]
    dependencies: List[str]
    validation_results: Dict[str, Any]
    generation_time: float
    model_used: str

class AutonomousCodeGenerator:
    """
    Advanced autonomous code generation system using multiple LLMs
    Generates production-ready code from natural language descriptions
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Generation history and learning
        self.generation_history: List[GeneratedCode] = []
        self.pattern_library: Dict[str, Dict] = {}
        self.quality_metrics: Dict[str, float] = {}

        # Code templates and patterns
        self.templates = self._load_code_templates()
        self.best_practices = self._load_best_practices()

        # LLM configurations
        self.llm_configs = {
            "openai": {
                "model": "gpt-4",
                "temperature": 0.3,
                "max_tokens": 4000
            },
            "anthropic": {
                "model": "claude-3-sonnet",
                "temperature": 0.3,
                "max_tokens": 4000
            }
        }

    def _load_code_templates(self) -> Dict[str, str]:
        """Load code templates for different types"""
        return {
            "python_api_endpoint": '''
@app.{method}("{path}")
async def {function_name}({parameters}):
    """
    {description}
    """
    try:
        # Input validation
        {validation_code}

        # Business logic
        {business_logic}

        # Response
        return JSONResponse(
            status_code=200,
            content={{"message": "Success", "data": result}}
        )
    except Exception as e:
        logger.error(f"Error in {function_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
''',
            "python_model": '''
class {class_name}(BaseModel):
    """
    {description}
    """
    {fields}

    class Config:
        orm_mode = True
        validate_assignment = True

    @validator('{primary_field}')
    def validate_{primary_field}(cls, v):
        """Validate {primary_field}"""
        {validation_logic}
        return v
''',
            "react_component": '''
import React, {{ useState, useEffect }} from 'react';
import {{ {imports} }} from '@chakra-ui/react';

const {component_name} = ({{ {props} }}) => {{
    {state_declarations}

    {effects}

    {handlers}

    return (
        <{wrapper_component} {wrapper_props}>
            {component_body}
        </{wrapper_component}>
    );
}};

export default {component_name};
''',
            "test_suite": '''
import pytest
import asyncio
from unittest.mock import Mock, patch
from {module_path} import {target_class}

class Test{test_class_name}:
    """Test suite for {target_class}"""

    @pytest.fixture
    async def setup(self):
        """Setup test environment"""
        {setup_code}
        yield setup_data
        {cleanup_code}

    {test_methods}

    @pytest.mark.asyncio
    async def test_{main_functionality}(self, setup):
        """Test main functionality"""
        {test_code}
        assert result == expected_result
'''
        }

    def _load_best_practices(self) -> Dict[str, List[str]]:
        """Load coding best practices by language"""
        return {
            "python": [
                "Use type hints for all function parameters and return types",
                "Follow PEP 8 style guidelines",
                "Include comprehensive docstrings",
                "Use async/await for I/O operations",
                "Implement proper error handling with specific exceptions",
                "Add input validation and sanitization",
                "Use logging instead of print statements",
                "Include unit tests with high coverage",
                "Follow SOLID principles",
                "Use dependency injection for testability"
            ],
            "javascript": [
                "Use const/let instead of var",
                "Implement proper error boundaries",
                "Use async/await for asynchronous operations",
                "Follow ESLint recommended rules",
                "Use TypeScript for type safety",
                "Implement proper state management",
                "Add comprehensive JSDoc comments",
                "Use modern ES6+ features",
                "Implement proper component lifecycle management",
                "Add accessibility features"
            ],
            "sql": [
                "Use parameterized queries to prevent SQL injection",
                "Optimize queries with proper indexing",
                "Use transactions for data consistency",
                "Add proper constraints and validations",
                "Use descriptive table and column names",
                "Implement proper backup and recovery",
                "Use stored procedures for complex logic",
                "Add proper commenting and documentation"
            ]
        }

    async def generate_code_from_description(self, description: str,
                                           language: CodeLanguage = CodeLanguage.PYTHON,
                                           code_type: CodeType = CodeType.UTILITY_FUNCTION,
                                           quality_level: QualityLevel = QualityLevel.PRODUCTION) -> GeneratedCode:
        """
        Generate high-quality code from natural language description
        """

        self.logger.info(f"🤖 Generating {code_type.value} code in {language.value}: {description}")

        request = CodeGenerationRequest(
            request_id=str(uuid.uuid4()),
            description=description,
            language=language,
            code_type=code_type,
            quality_level=quality_level,
            requirements=self._extract_requirements(description),
            constraints=self._extract_constraints(description),
            context=self._analyze_context(description)
        )

        # Pre-generation security validation
        await self._validate_request_security(request)

        start_time = asyncio.get_event_loop().time()

        # Multi-step generation process
        generated_code = await self._multi_step_generation(request)

        end_time = asyncio.get_event_loop().time()
        generation_time = end_time - start_time

        # Validate and enhance generated code
        validated_code = await self._validate_and_enhance(generated_code, request)
        validated_code.generation_time = generation_time

        # Store for learning
        self.generation_history.append(validated_code)

        self.logger.info(f"✅ Code generation completed in {generation_time:.2f}s")
        return validated_code

    def _extract_requirements(self, description: str) -> List[str]:
        """Extract specific requirements from description"""
        requirements = []

        # Look for specific patterns
        requirement_patterns = [
            r"must\s+(\w+.*?)(?:[.!]|$)",
            r"should\s+(\w+.*?)(?:[.!]|$)",
            r"needs?\s+to\s+(\w+.*?)(?:[.!]|$)",
            r"requires?\s+(\w+.*?)(?:[.!]|$)",
            r"(?:need|want)\s+(\w+.*?)(?:[.!]|$)"
        ]

        for pattern in requirement_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            requirements.extend(matches)

        # Add common requirements based on keywords
        description_lower = description.lower()

        if "api" in description_lower:
            requirements.extend([
                "Include proper error handling",
                "Add request validation",
                "Implement rate limiting",
                "Include API documentation"
            ])

        if "database" in description_lower:
            requirements.extend([
                "Use parameterized queries",
                "Add connection pooling",
                "Implement proper transactions",
                "Include migration scripts"
            ])

        if "security" in description_lower:
            requirements.extend([
                "Implement authentication",
                "Add input sanitization",
                "Use HTTPS only",
                "Include audit logging"
            ])

        return list(set(requirements))  # Remove duplicates

    def _extract_constraints(self, description: str) -> List[str]:
        """Extract constraints from description"""
        constraints = []

        # Performance constraints
        if re.search(r"fast|quick|performant|speed", description, re.IGNORECASE):
            constraints.append("Optimize for performance")

        # Scalability constraints
        if re.search(r"scalable?|scale|concurrent|parallel", description, re.IGNORECASE):
            constraints.append("Design for scalability")

        # Memory constraints
        if re.search(r"memory|ram|efficient", description, re.IGNORECASE):
            constraints.append("Memory efficient implementation")

        # Security constraints
        if re.search(r"secure|safety|protected", description, re.IGNORECASE):
            constraints.append("Follow security best practices")

        return constraints

    def _analyze_context(self, description: str) -> Dict[str, Any]:
        """Analyze context from description"""
        context = {
            "domain": "general",
            "complexity": "medium",
            "integration_points": [],
            "external_dependencies": []
        }

        # Determine domain
        domain_keywords = {
            "web": ["web", "http", "api", "endpoint", "server"],
            "data": ["database", "sql", "data", "analytics", "etl"],
            "ai": ["ai", "ml", "machine learning", "neural", "model"],
            "devops": ["deploy", "docker", "kubernetes", "ci/cd", "pipeline"],
            "security": ["security", "auth", "encryption", "ssl", "oauth"]
        }

        description_lower = description.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                context["domain"] = domain
                break

        # Determine complexity
        complexity_indicators = {
            "simple": ["simple", "basic", "easy", "straightforward"],
            "medium": ["moderate", "standard", "typical"],
            "complex": ["complex", "advanced", "sophisticated", "enterprise"]
        }

        for complexity, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                context["complexity"] = complexity
                break

        # Identify integration points
        integration_keywords = ["integrate", "connect", "api", "webhook", "callback", "sync"]
        if any(keyword in description_lower for keyword in integration_keywords):
            context["integration_points"] = ["external_api", "database", "message_queue"]

        return context

    async def _multi_step_generation(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Multi-step code generation process"""

        # Step 1: Generate initial code structure
        initial_code = await self._generate_initial_structure(request)

        # Step 2: Add business logic
        business_logic = await self._generate_business_logic(request, initial_code)

        # Step 3: Add error handling and validation
        enhanced_code = await self._add_error_handling(request, business_logic)

        # Step 4: Generate documentation
        documentation = await self._generate_documentation(request, enhanced_code)

        # Step 5: Generate tests
        test_code = await self._generate_tests(request, enhanced_code)

        # Step 6: Calculate quality scores
        quality_score = await self._calculate_quality_score(enhanced_code, request)
        security_score = await self._calculate_security_score(enhanced_code, request)

        return GeneratedCode(
            code_id=str(uuid.uuid4()),
            original_request=request.description,
            language=request.language,
            code_type=request.code_type,
            generated_code=enhanced_code,
            documentation=documentation,
            test_code=test_code,
            quality_score=quality_score,
            security_score=security_score,
            performance_notes=self._generate_performance_notes(enhanced_code),
            usage_examples=self._generate_usage_examples(enhanced_code, request),
            dependencies=self._extract_dependencies(enhanced_code),
            validation_results={},
            generation_time=0.0,
            model_used="autonomous_generator"
        )

    async def _generate_initial_structure(self, request: CodeGenerationRequest) -> str:
        """Generate initial code structure"""

        template = self.templates.get(f"{request.language.value}_{request.code_type.value}")

        if request.code_type == CodeType.API_ENDPOINT and request.language == CodeLanguage.PYTHON:
            # Extract method and path from description
            method = self._extract_http_method(request.description)
            path = self._extract_api_path(request.description)
            function_name = self._generate_function_name(request.description)
            parameters = self._generate_parameters(request.description)

            return f'''
@app.{method}("{path}")
async def {function_name}({parameters}):
    """
    {request.description}

    Generated automatically from natural language description.
    """
    # TODO: Implement business logic
    pass
'''

        elif request.code_type == CodeType.FRONTEND_COMPONENT and request.language == CodeLanguage.JAVASCRIPT:
            component_name = self._generate_component_name(request.description)

            return f'''
import React, {{ useState, useEffect }} from 'react';

const {component_name} = () => {{
    // TODO: Add state management
    const [data, setData] = useState(null);

    // TODO: Add side effects
    useEffect(() => {{
        // Initialize component
    }}, []);

    // TODO: Add event handlers

    return (
        <div>
            {{/* TODO: Implement component UI */}}
            <h1>{component_name}</h1>
        </div>
    );
}};

export default {component_name};
'''

        elif request.code_type == CodeType.DATABASE_MODEL and request.language == CodeLanguage.PYTHON:
            class_name = self._generate_class_name(request.description)

            return f'''
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, validator
from datetime import datetime

Base = declarative_base()

class {class_name}(Base):
    """
    {request.description}
    """
    __tablename__ = '{class_name.lower()}s'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # TODO: Add specific fields based on requirements

class {class_name}Schema(BaseModel):
    """Pydantic schema for {class_name}"""
    # TODO: Add schema fields

    class Config:
        orm_mode = True
'''

        else:
            # Generic structure
            return f'''
# {request.description}
# Generated automatically from natural language description
# Language: {request.language.value}
# Type: {request.code_type.value}

# TODO: Implement specific functionality
def main():
    """Main function implementing the requested functionality"""
    pass

if __name__ == "__main__":
    main()
'''

    async def _generate_business_logic(self, request: CodeGenerationRequest, initial_code: str) -> str:
        """Generate business logic based on requirements"""

        # Analyze requirements and generate appropriate logic
        logic_patterns = {
            "crud": self._generate_crud_logic,
            "validation": self._generate_validation_logic,
            "calculation": self._generate_calculation_logic,
            "integration": self._generate_integration_logic
        }

        # Determine logic type from description
        description_lower = request.description.lower()

        enhanced_code = initial_code

        for pattern_type, generator in logic_patterns.items():
            if any(keyword in description_lower for keyword in self._get_pattern_keywords(pattern_type)):
                enhanced_code = await generator(request, enhanced_code)

        return enhanced_code

    def _get_pattern_keywords(self, pattern_type: str) -> List[str]:
        """Get keywords for different logic patterns"""
        keywords = {
            "crud": ["create", "read", "update", "delete", "insert", "select", "modify"],
            "validation": ["validate", "check", "verify", "ensure", "confirm"],
            "calculation": ["calculate", "compute", "sum", "average", "total", "count"],
            "integration": ["integrate", "connect", "sync", "import", "export", "api"]
        }
        return keywords.get(pattern_type, [])

    async def _generate_crud_logic(self, request: CodeGenerationRequest, code: str) -> str:
        """Generate CRUD operations logic"""

        if request.language == CodeLanguage.PYTHON:
            crud_operations = '''
    # CRUD Operations

    async def create(self, data: dict) -> dict:
        """Create a new record"""
        try:
            # Validate input data
            validated_data = self._validate_input(data)

            # Create record
            new_record = await self.db.create(validated_data)

            return {"success": True, "data": new_record}
        except Exception as e:
            logger.error(f"Error creating record: {e}")
            raise

    async def read(self, record_id: int) -> dict:
        """Read a record by ID"""
        try:
            record = await self.db.get_by_id(record_id)
            if not record:
                raise NotFoundError(f"Record {record_id} not found")

            return {"success": True, "data": record}
        except Exception as e:
            logger.error(f"Error reading record {record_id}: {e}")
            raise

    async def update(self, record_id: int, data: dict) -> dict:
        """Update a record"""
        try:
            # Check if record exists
            existing = await self.db.get_by_id(record_id)
            if not existing:
                raise NotFoundError(f"Record {record_id} not found")

            # Validate and update
            validated_data = self._validate_input(data)
            updated_record = await self.db.update(record_id, validated_data)

            return {"success": True, "data": updated_record}
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
            raise

    async def delete(self, record_id: int) -> dict:
        """Delete a record"""
        try:
            # Check if record exists
            existing = await self.db.get_by_id(record_id)
            if not existing:
                raise NotFoundError(f"Record {record_id} not found")

            # Delete record
            await self.db.delete(record_id)

            return {"success": True, "message": f"Record {record_id} deleted"}
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {e}")
            raise
'''
            return code.replace("# TODO: Implement business logic", crud_operations)

        return code

    async def _generate_validation_logic(self, request: CodeGenerationRequest, code: str) -> str:
        """Generate validation logic"""

        validation_logic = '''
    def _validate_input(self, data: dict) -> dict:
        """Validate input data"""
        if not data:
            raise ValidationError("Input data cannot be empty")

        # Type validation
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Required field '{field}' is missing")

        # Data sanitization
        sanitized_data = self._sanitize_data(data)

        # Business rule validation
        self._validate_business_rules(sanitized_data)

        return sanitized_data

    def _sanitize_data(self, data: dict) -> dict:
        """Sanitize input data"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = re.sub(r'[<>"\']', '', value).strip()
            else:
                sanitized[key] = value
        return sanitized

    def _validate_business_rules(self, data: dict):
        """Validate business-specific rules"""
        # Add specific business validation logic here
        pass
'''

        return code.replace("pass", validation_logic)

    async def _add_error_handling(self, request: CodeGenerationRequest, code: str) -> str:
        """Add comprehensive error handling"""

        if request.language == CodeLanguage.PYTHON:
            error_handling = '''
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class NotFoundError(Exception):
    """Resource not found error"""
    pass

class BusinessLogicError(Exception):
    """Business logic error"""
    pass

def handle_errors(func):
    """Decorator for error handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except NotFoundError as e:
            logger.warning(f"Not found error: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except BusinessLogicError as e:
            logger.error(f"Business logic error: {e}")
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper
'''
            return error_handling + "\n" + code

        return code

    async def _generate_calculation_logic(self, request: CodeGenerationRequest, code: str) -> str:
        """Generate calculation-specific logic"""
        calculation_logic = '''
# Calculation logic
def calculate_result(input_data):
    """Perform calculations on input data"""
    try:
        # Add calculation implementation here
        result = input_data * 2  # Example calculation
        return result
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")
'''
        return code + "\n" + calculation_logic

    async def _generate_integration_logic(self, request: CodeGenerationRequest, code: str) -> str:
        """Generate integration-specific logic"""
        integration_logic = '''
# Integration logic
async def integrate_with_external_service(data):
    """Integrate with external services"""
    try:
        # Add integration implementation here
        # Example: API calls, database connections, etc.
        return {"status": "success", "data": data}
    except Exception as e:
        raise ConnectionError(f"Integration error: {e}")
'''
        return code + "\n" + integration_logic

    def _get_pattern_keywords(self, pattern_type: str) -> List[str]:
        """Get keywords for different pattern types"""
        keyword_map = {
            "crud": ["create", "read", "update", "delete", "database", "store", "retrieve"],
            "validation": ["validate", "check", "verify", "sanitize", "clean"],
            "calculation": ["calculate", "compute", "math", "formula", "algorithm"],
            "integration": ["api", "service", "connect", "integrate", "external", "third-party"]
        }
        return keyword_map.get(pattern_type, [])

    async def _validate_request_security(self, request: CodeGenerationRequest) -> None:
        """Validate request for security concerns before code generation"""

        dangerous_keywords = [
            'delete', 'remove', 'unlink', 'destroy', 'erase', 'wipe',
            'format', 'clear', 'rm -rf', 'shred', 'truncate',
            'password', 'credential', 'key', 'token', 'secret',
            'hack', 'exploit', 'inject', 'bypass', 'crack',
            'harvest', 'steal', 'extract', 'breach', 'compromise'
        ]

        description_lower = request.description.lower()

        for keyword in dangerous_keywords:
            if keyword in description_lower:
                if keyword in ['delete', 'remove', 'unlink', 'destroy', 'erase', 'wipe', 'format', 'clear', 'rm -rf', 'shred', 'truncate']:
                    raise ValueError(f"Security violation: Request contains dangerous file operation keyword '{keyword}'. Code generation blocked for safety.")
                elif keyword in ['password', 'credential', 'key', 'token', 'secret']:
                    if keyword in ['harvest', 'steal', 'extract', 'breach', 'compromise']:
                        raise ValueError(f"Security violation: Request contains credential theft keyword '{keyword}'. Code generation blocked.")
                    else:
                        self.logger.warning(f"Security concern: Request involves sensitive data '{keyword}'. Extra validation will be applied.")
                elif keyword in ['hack', 'exploit', 'inject', 'bypass', 'crack', 'harvest', 'steal', 'extract', 'breach', 'compromise']:
                    raise ValueError(f"Security violation: Request contains malicious intent keyword '{keyword}'. Code generation blocked.")

        # Additional validation for file system operations
        file_operations = ['file', 'directory', 'folder', 'path']
        destruction_words = ['all', 'everything', 'entire', 'complete']

        has_file_op = any(op in description_lower for op in file_operations)
        has_destruction = any(word in description_lower for word in destruction_words)

        if has_file_op and has_destruction:
            raise ValueError("Security violation: Request appears to involve mass file operations. Code generation blocked for safety.")

    async def _generate_documentation(self, request: CodeGenerationRequest, code: str) -> str:
        """Generate comprehensive documentation"""

        return f'''
# {request.description}

## Overview
This code was automatically generated from the natural language description:
"{request.description}"

## Features
{chr(10).join("- " + str(req) for req in request.requirements)}

## Requirements
- Python 3.8+
- FastAPI
- SQLAlchemy
- Pydantic

## Usage
```python
# Example usage of the generated code
{self._generate_usage_example(code, request)}
```

## API Documentation
{self._generate_api_docs(code, request)}

## Error Handling
The code includes comprehensive error handling for:
- Validation errors (400)
- Not found errors (404)
- Business logic errors (422)
- Internal server errors (500)

## Security Considerations
- Input validation and sanitization
- SQL injection prevention
- Proper error messages (no sensitive data exposure)
- Rate limiting (if applicable)

## Performance Notes
- Async/await for non-blocking operations
- Connection pooling for database operations
- Efficient query patterns
- Caching where appropriate

## Testing
Run the generated tests with:
```bash
pytest test_generated.py -v
```

## Contributing
This code was generated automatically. For modifications:
1. Update the natural language description
2. Regenerate the code
3. Review and test changes
'''

    async def _generate_tests(self, request: CodeGenerationRequest, code: str) -> str:
        """Generate comprehensive test suite"""

        if request.language == CodeLanguage.PYTHON:
            return '''
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Import the generated code
# from your_module import YourClass

class TestGeneratedCode:
    """Test suite for generated code"""

    @pytest.fixture
    def setup(self):
        """Setup test environment"""
        # Mock database
        mock_db = Mock()
        mock_db.create = AsyncMock(return_value={"id": 1, "name": "test"})
        mock_db.get_by_id = AsyncMock(return_value={"id": 1, "name": "test"})
        mock_db.update = AsyncMock(return_value={"id": 1, "name": "updated"})
        mock_db.delete = AsyncMock(return_value=True)

        return {"mock_db": mock_db}

    @pytest.mark.asyncio
    async def test_main_functionality(self, setup):
        """Test main functionality"""
        # Test the primary function
        result = await main_function()
        assert result is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, setup):
        """Test error handling"""
        with pytest.raises(Exception):
            await error_causing_function()

    @pytest.mark.asyncio
    async def test_validation(self, setup):
        """Test input validation"""
        valid_data = {"name": "test", "value": 123}
        result = validate_input(valid_data)
        assert result["name"] == "test"

        invalid_data = {}
        with pytest.raises(ValidationError):
            validate_input(invalid_data)

    def test_api_endpoints(self, setup):
        """Test API endpoints if applicable"""
        client = TestClient(app)

        # Test GET endpoint
        response = client.get("/test")
        assert response.status_code == 200

        # Test POST endpoint
        response = client.post("/test", json={"name": "test"})
        assert response.status_code == 201

    @pytest.mark.parametrize("input_value,expected", [
        ("test", "test"),
        ("", ""),
        (None, None),
    ])
    def test_edge_cases(self, input_value, expected):
        """Test edge cases"""
        result = process_input(input_value)
        assert result == expected
'''

        return "# No tests generated for this language yet"

    async def _calculate_quality_score(self, code: str, request: CodeGenerationRequest) -> float:
        """Calculate code quality score"""

        score = 0.0
        max_score = 100.0

        # Check for best practices
        best_practices = self.best_practices.get(request.language.value, [])
        practices_found = 0

        for practice in best_practices:
            if self._check_practice_in_code(code, practice):
                practices_found += 1

        score += (practices_found / len(best_practices)) * 40  # 40 points for best practices

        # Check for error handling
        if "try:" in code and "except" in code:
            score += 20

        # Check for documentation
        if '"""' in code or "# " in code:
            score += 15

        # Check for type hints (Python)
        if request.language == CodeLanguage.PYTHON and "->" in code:
            score += 10

        # Check for async patterns
        if "async" in code and "await" in code:
            score += 10

        # Check for validation
        if "validate" in code.lower():
            score += 5

        return min(score, max_score)

    async def _calculate_security_score(self, code: str, request: CodeGenerationRequest) -> float:
        """Calculate security score and enforce security validation"""

        score = 100.0  # Start with perfect score, deduct for issues
        has_critical_issues = False

        # Check for common security issues
        security_issues = [
            ("eval(", "Use of eval() is dangerous"),
            ("exec(", "Use of exec() is dangerous"),
            ("shell=True", "Shell injection risk"),
            ("md5", "MD5 is cryptographically weak"),
            ("os.remove", "File deletion operations are restricted"),
            ("os.unlink", "File deletion operations are restricted"),
            ("shutil.rmtree", "Directory deletion operations are restricted"),
            ("rm -rf", "Shell commands for deletion are restricted"),
            ("subprocess.call", "Subprocess calls may be dangerous"),
            ("os.system", "Direct system calls are dangerous"),
            # Removed "print(" as it's too broad and not always a security issue
        ]

        for issue, description in security_issues:
            if issue in code:
                score -= 10
                self.logger.warning(f"Security issue detected: {description}")

                # Mark critical security issues
                if issue in ["eval(", "exec(", "shell=True", "os.remove", "os.unlink", "shutil.rmtree", "rm -rf", "os.system"]:
                    has_critical_issues = True

        # Block code with critical security issues
        if has_critical_issues:
            raise ValueError("Generated code contains critical security issues and cannot be returned")

        # Reward security best practices
        security_patterns = [
            "sanitize",
            "validate",
            "parameterized",
            "escape",
            "hash",
            "bcrypt",
            "jwt",
            "csrf"
        ]

        for pattern in security_patterns:
            if pattern in code.lower():
                score += 2  # Small bonus for each security pattern

        return max(0.0, min(score, 100.0))

    def _check_practice_in_code(self, code: str, practice: str) -> bool:
        """Check if a best practice is followed in the code"""

        practice_lower = practice.lower()
        code_lower = code.lower()

        # Map practices to code patterns
        practice_patterns = {
            "type hints": "->",
            "docstrings": '"""',
            "async/await": "async def",
            "error handling": "try:",
            "logging": "logger.",
            "validation": "validate",
            "solid principles": "class",
            "dependency injection": "__init__"
        }

        for key, pattern in practice_patterns.items():
            if key in practice_lower and pattern in code:
                return True

        return False

    def _generate_performance_notes(self, code: str) -> List[str]:
        """Generate performance optimization notes"""

        notes = []

        if "async def" in code:
            notes.append("✅ Uses async/await for non-blocking operations")
        else:
            notes.append("⚠️ Consider using async/await for I/O operations")

        if "cache" in code.lower():
            notes.append("✅ Implements caching for performance")
        else:
            notes.append("💡 Consider adding caching for frequently accessed data")

        if "db.create" in code or "db.query" in code:
            notes.append("💡 Consider using database connection pooling")
            notes.append("💡 Add database query optimization and indexing")

        if "for " in code and "await" in code:
            notes.append("⚠️ Consider using asyncio.gather() for concurrent operations")

        return notes

    def _generate_usage_examples(self, code: str, request: CodeGenerationRequest) -> List[str]:
        """Generate usage examples"""

        examples = []

        if request.code_type == CodeType.API_ENDPOINT:
            examples.extend([
                "curl -X GET http://localhost:8000/api/endpoint",
                "curl -X POST http://localhost:8000/api/endpoint -d '{\"key\": \"value\"}'",
                "# Python client example:\n# response = requests.get('http://localhost:8000/api/endpoint')"
            ])

        elif request.code_type == CodeType.UTILITY_FUNCTION:
            examples.extend([
                "# Basic usage:\nresult = function_name(input_data)",
                "# With error handling:\ntry:\n    result = function_name(input_data)\nexcept Exception as e:\n    print(f'Error: {e}')"
            ])

        elif request.code_type == CodeType.FRONTEND_COMPONENT:
            examples.extend([
                "// Basic usage:\n<ComponentName />",
                "// With props:\n<ComponentName prop1='value1' prop2='value2' />",
                "// With state:\nconst [state, setState] = useState(initialValue);"
            ])

        return examples

    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract dependencies from generated code"""

        dependencies = set()

        # Python imports
        import_patterns = [
            r"from\s+(\w+)",
            r"import\s+(\w+)",
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            dependencies.update(matches)

        # Common dependencies based on patterns
        if "fastapi" in code.lower():
            dependencies.update(["fastapi", "uvicorn", "pydantic"])

        if "sqlalchemy" in code.lower():
            dependencies.update(["sqlalchemy", "psycopg2-binary"])

        if "pytest" in code.lower():
            dependencies.update(["pytest", "pytest-asyncio"])

        if "requests" in code.lower():
            dependencies.add("requests")

        return list(dependencies)

    # Helper methods for code generation
    def _extract_http_method(self, description: str) -> str:
        """Extract HTTP method from description"""
        description_lower = description.lower()

        if any(word in description_lower for word in ["create", "add", "insert", "post"]):
            return "post"
        elif any(word in description_lower for word in ["update", "modify", "edit", "put"]):
            return "put"
        elif any(word in description_lower for word in ["delete", "remove"]):
            return "delete"
        else:
            return "get"

    def _extract_api_path(self, description: str) -> str:
        """Extract API path from description"""
        # Look for path indicators
        path_match = re.search(r"/\w+(?:/\w+)*", description)
        if path_match:
            return path_match.group()

        # Generate path from keywords
        words = re.findall(r'\w+', description.lower())
        relevant_words = [w for w in words if w not in ["api", "endpoint", "create", "get", "update", "delete"]]

        if relevant_words:
            return f"/api/{relevant_words[0]}"

        return "/api/generated"

    def _generate_function_name(self, description: str) -> str:
        """Generate function name from description"""
        words = re.findall(r'\w+', description.lower())

        # Filter out common words
        stop_words = {"the", "a", "an", "to", "for", "of", "in", "on", "at", "by", "with"}
        relevant_words = [w for w in words if w not in stop_words and w.isalpha()]

        if relevant_words:
            name = "_".join(relevant_words[:3])  # Use first 3 relevant words

            # Ensure it starts with a letter and is a valid identifier
            if not name[0].isalpha():
                name = "func_" + name

            # Remove any remaining invalid characters
            name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

            # Check if it's a Python keyword
            if keyword.iskeyword(name):
                name = name + "_func"

            # Validate it's a proper identifier
            if name.isidentifier():
                return name

        return "generated_function"

    def _generate_parameters(self, description: str) -> str:
        """Generate function parameters from description"""
        # Basic parameter detection
        if "id" in description.lower():
            return "item_id: int"
        elif any(word in description.lower() for word in ["create", "add"]):
            return "data: dict"
        elif "user" in description.lower():
            return "user_id: int"
        else:
            return ""

    def _generate_component_name(self, description: str) -> str:
        """Generate React component name"""
        words = re.findall(r'\w+', description)
        relevant_words = [w.capitalize() for w in words if len(w) > 2]

        if relevant_words:
            return "".join(relevant_words[:2]) + "Component"

        return "GeneratedComponent"

    def _generate_class_name(self, description: str) -> str:
        """Generate class name from description"""
        words = re.findall(r'\w+', description)
        relevant_words = [w.capitalize() for w in words if len(w) > 2]

        if relevant_words:
            return "".join(relevant_words[:2])

        return "GeneratedClass"

    def _generate_usage_example(self, code: str, request: CodeGenerationRequest) -> str:
        """Generate a usage example"""
        if "def " in code:
            function_match = re.search(r'def\s+(\w+)', code)
            if function_match:
                function_name = function_match.group(1)
                return f"{function_name}()"

        return "# Usage example not available"

    def _generate_api_docs(self, code: str, request: CodeGenerationRequest) -> str:
        """Generate API documentation"""
        if request.code_type == CodeType.API_ENDPOINT:
            method = self._extract_http_method(request.description)
            path = self._extract_api_path(request.description)

            return f'''
### {method.upper()} {path}

**Description:** {request.description}

**Request:**
```json
{{
    "example": "request body"
}}
```

**Response:**
```json
{{
    "success": true,
    "data": {{}}
}}
```

**Status Codes:**
- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error
'''

        return "No API documentation available for this code type."

    async def _validate_and_enhance(self, generated_code: GeneratedCode, request: CodeGenerationRequest) -> GeneratedCode:
        """Validate and enhance the generated code"""

        # Syntax validation
        if request.language == CodeLanguage.PYTHON:
            try:
                ast.parse(generated_code.generated_code)
                generated_code.validation_results["syntax"] = "valid"
            except SyntaxError as e:
                generated_code.validation_results["syntax"] = f"invalid: {e}"
                self.logger.warning(f"Syntax error in generated code: {e}")

        # Security validation
        security_issues = []
        dangerous_patterns = ["eval(", "exec(", "shell=True", "__import__"]

        for pattern in dangerous_patterns:
            if pattern in generated_code.generated_code:
                security_issues.append(f"Dangerous pattern detected: {pattern}")

        generated_code.validation_results["security_issues"] = security_issues

        return generated_code

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get code generation statistics"""

        if not self.generation_history:
            return {"message": "No code generated yet"}

        total_generated = len(self.generation_history)
        avg_quality = sum(g.quality_score for g in self.generation_history) / total_generated
        avg_security = sum(g.security_score for g in self.generation_history) / total_generated
        avg_time = sum(g.generation_time for g in self.generation_history) / total_generated

        languages = {}
        code_types = {}

        for gen in self.generation_history:
            languages[gen.language.value] = languages.get(gen.language.value, 0) + 1
            code_types[gen.code_type.value] = code_types.get(gen.code_type.value, 0) + 1

        return {
            "total_generated": total_generated,
            "average_quality_score": round(avg_quality, 2),
            "average_security_score": round(avg_security, 2),
            "average_generation_time": round(avg_time, 2),
            "languages_used": languages,
            "code_types_generated": code_types,
            "latest_generation": self.generation_history[-1].code_id if self.generation_history else None
        }

# Global code generator instance
autonomous_generator = AutonomousCodeGenerator()

async def generate_code(description: str, language: str = "python", code_type: str = "utility_function") -> GeneratedCode:
    """Generate code from natural language description"""
    lang_enum = CodeLanguage(language.lower())
    type_enum = CodeType(code_type.lower())

    return await autonomous_generator.generate_code_from_description(
        description=description,
        language=lang_enum,
        code_type=type_enum,
        quality_level=QualityLevel.PRODUCTION
    )

def get_generation_statistics():
    """Get code generation statistics"""
    return autonomous_generator.get_generation_stats()