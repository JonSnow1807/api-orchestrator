"""
API Contract Testing System
Validates API contracts between consumers and providers
"""

from typing import Dict, List, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
import jsonschema

try:
    from deepdiff import DeepDiff

    HAS_DEEPDIFF = True
except ImportError:
    HAS_DEEPDIFF = False
    print(
        "Warning: deepdiff not installed. Contract comparison features will be limited."
    )

from src.database import Base


class ContractType:
    """Contract type enumeration"""

    CONSUMER_DRIVEN = "consumer_driven"
    PROVIDER_DRIVEN = "provider_driven"
    BILATERAL = "bilateral"


class APIContract(Base):
    """API Contract model"""

    __tablename__ = "api_contracts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))

    # Contract details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), default="1.0.0")
    contract_type = Column(String(50), default="bilateral")

    # Provider and Consumer
    provider_name = Column(String(255))
    consumer_name = Column(String(255))
    provider_version = Column(String(50))
    consumer_version = Column(String(50))

    # Contract specification
    request_schema = Column(JSON)  # JSON Schema for request
    response_schema = Column(JSON)  # JSON Schema for response
    headers_schema = Column(JSON)  # Expected headers
    status_codes = Column(JSON)  # Acceptable status codes

    # Validation rules
    validation_rules = Column(JSON)  # Custom validation rules
    breaking_changes_allowed = Column(Boolean, default=False)

    # Testing
    test_endpoints = Column(JSON)  # Endpoints to test
    mock_data = Column(JSON)  # Mock data for testing
    last_tested = Column(DateTime)
    last_test_status = Column(String(20))  # passed, failed, warning

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))


class ContractTest(Base):
    """Contract test execution results"""

    __tablename__ = "contract_tests"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("api_contracts.id"))

    # Test details
    test_name = Column(String(255))
    test_type = Column(String(50))  # request, response, integration
    endpoint = Column(String(500))

    # Test data
    request_data = Column(JSON)
    response_data = Column(JSON)

    # Results
    passed = Column(Boolean)
    errors = Column(JSON)
    warnings = Column(JSON)
    execution_time_ms = Column(Integer)

    # Metadata
    executed_at = Column(DateTime, default=datetime.utcnow)
    executed_by = Column(Integer, ForeignKey("users.id"))


class ContractValidator:
    """Validates API contracts"""

    @staticmethod
    def validate_request(request_data: Dict, contract: APIContract) -> Dict[str, Any]:
        """Validate request against contract"""

        errors = []
        warnings = []

        # Validate request schema
        if contract.request_schema:
            try:
                jsonschema.validate(request_data, contract.request_schema)
            except jsonschema.ValidationError as e:
                errors.append(f"Request schema validation failed: {e.message}")

        # Validate custom rules
        if contract.validation_rules:
            rule_results = ContractValidator._validate_custom_rules(
                request_data, contract.validation_rules.get("request", [])
            )
            errors.extend(rule_results["errors"])
            warnings.extend(rule_results["warnings"])

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def validate_response(
        response_data: Dict, status_code: int, headers: Dict, contract: APIContract
    ) -> Dict[str, Any]:
        """Validate response against contract"""

        errors = []
        warnings = []

        # Validate status code
        if contract.status_codes and status_code not in contract.status_codes:
            errors.append(f"Unexpected status code: {status_code}")

        # Validate response schema
        if contract.response_schema:
            try:
                jsonschema.validate(response_data, contract.response_schema)
            except jsonschema.ValidationError as e:
                errors.append(f"Response schema validation failed: {e.message}")

        # Validate headers
        if contract.headers_schema:
            header_errors = ContractValidator._validate_headers(
                headers, contract.headers_schema
            )
            errors.extend(header_errors)

        # Validate custom rules
        if contract.validation_rules:
            rule_results = ContractValidator._validate_custom_rules(
                response_data, contract.validation_rules.get("response", [])
            )
            errors.extend(rule_results["errors"])
            warnings.extend(rule_results["warnings"])

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def _validate_headers(headers: Dict, expected_headers: Dict) -> List[str]:
        """Validate headers against expectations"""

        errors = []

        for header_name, header_spec in expected_headers.items():
            if header_spec.get("required", False) and header_name not in headers:
                errors.append(f"Missing required header: {header_name}")

            if header_name in headers:
                header_value = headers[header_name]

                # Validate header value pattern
                if "pattern" in header_spec:
                    import re

                    if not re.match(header_spec["pattern"], header_value):
                        errors.append(
                            f"Header {header_name} doesn't match pattern: {header_spec['pattern']}"
                        )

                # Validate header value type
                if "type" in header_spec:
                    expected_type = header_spec["type"]
                    if expected_type == "integer":
                        try:
                            int(header_value)
                        except ValueError:
                            errors.append(f"Header {header_name} should be an integer")

        return errors

    @staticmethod
    def _validate_custom_rules(data: Any, rules: List[Dict]) -> Dict[str, List[str]]:
        """Validate custom business rules"""

        errors = []
        warnings = []

        for rule in rules:
            rule_type = rule.get("type")

            if rule_type == "required_field":
                field_path = rule.get("field")
                if not ContractValidator._get_nested_value(data, field_path):
                    errors.append(f"Required field missing: {field_path}")

            elif rule_type == "field_format":
                field_path = rule.get("field")
                format_pattern = rule.get("pattern")
                value = ContractValidator._get_nested_value(data, field_path)
                if value and format_pattern:
                    import re

                    if not re.match(format_pattern, str(value)):
                        errors.append(
                            f"Field {field_path} doesn't match format: {format_pattern}"
                        )

            elif rule_type == "business_rule":
                # Custom business logic validation
                rule_name = rule.get("name")
                if not ContractValidator._evaluate_business_rule(data, rule):
                    severity = rule.get("severity", "error")
                    message = f"Business rule failed: {rule_name}"

                    if severity == "warning":
                        warnings.append(message)
                    else:
                        errors.append(message)

        return {"errors": errors, "warnings": warnings}

    @staticmethod
    def _get_nested_value(data: Any, path: str) -> Any:
        """Get nested value from data using dot notation"""

        if not path:
            return data

        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None

        return current

    @staticmethod
    def _evaluate_business_rule(data: Any, rule: Dict) -> bool:
        """Evaluate a business rule"""

        rule_type = rule.get("condition")

        if rule_type == "field_comparison":
            field1 = ContractValidator._get_nested_value(data, rule.get("field1"))
            field2 = ContractValidator._get_nested_value(data, rule.get("field2"))
            operator = rule.get("operator")

            if operator == "equals":
                return field1 == field2
            elif operator == "greater_than":
                return field1 > field2
            elif operator == "less_than":
                return field1 < field2

        elif rule_type == "value_in_range":
            field = ContractValidator._get_nested_value(data, rule.get("field"))
            min_val = rule.get("min")
            max_val = rule.get("max")

            if field is not None:
                if min_val is not None and field < min_val:
                    return False
                if max_val is not None and field > max_val:
                    return False
                return True

        return True


class ContractComparator:
    """Compare contracts for breaking changes"""

    @staticmethod
    def compare_contracts(
        old_contract: APIContract, new_contract: APIContract
    ) -> Dict[str, Any]:
        """Compare two contracts and identify breaking changes"""

        breaking_changes = []
        non_breaking_changes = []

        if not HAS_DEEPDIFF:
            # Simple comparison without deepdiff
            if old_contract.request_schema != new_contract.request_schema:
                breaking_changes.append("Request schema changed")
            if old_contract.response_schema != new_contract.response_schema:
                breaking_changes.append("Response schema changed")
        else:
            # Compare request schemas
            if old_contract.request_schema and new_contract.request_schema:
                request_diff = DeepDiff(
                    old_contract.request_schema,
                    new_contract.request_schema,
                    ignore_order=True,
                )

                if request_diff:
                    # Check for breaking changes in request
                    if "dictionary_item_removed" in request_diff:
                        for item in request_diff["dictionary_item_removed"]:
                            if "required" in str(item):
                                breaking_changes.append(
                                    f"Required request field removed: {item}"
                                )

                    if "type_changes" in request_diff:
                        for path, change in request_diff["type_changes"].items():
                            breaking_changes.append(
                                f"Request field type changed: {path}"
                            )

        # Compare response schemas (only with DeepDiff)
        if (
            HAS_DEEPDIFF
            and old_contract.response_schema
            and new_contract.response_schema
        ):
            response_diff = DeepDiff(
                old_contract.response_schema,
                new_contract.response_schema,
                ignore_order=True,
            )

            if response_diff:
                # Check for breaking changes in response
                if "dictionary_item_removed" in response_diff:
                    for item in response_diff["dictionary_item_removed"]:
                        breaking_changes.append(f"Response field removed: {item}")

                if "dictionary_item_added" in response_diff:
                    for item in response_diff["dictionary_item_added"]:
                        non_breaking_changes.append(f"Response field added: {item}")

        # Compare status codes
        old_codes = set(old_contract.status_codes or [])
        new_codes = set(new_contract.status_codes or [])

        removed_codes = old_codes - new_codes
        if removed_codes:
            breaking_changes.append(f"Status codes removed: {removed_codes}")

        added_codes = new_codes - old_codes
        if added_codes:
            non_breaking_changes.append(f"Status codes added: {added_codes}")

        return {
            "has_breaking_changes": len(breaking_changes) > 0,
            "breaking_changes": breaking_changes,
            "non_breaking_changes": non_breaking_changes,
            "compatible": len(breaking_changes) == 0,
        }


class ContractTestRunner:
    """Execute contract tests"""

    @staticmethod
    async def run_contract_tests(
        contract: APIContract, endpoint_url: str, db: Session
    ) -> Dict[str, Any]:
        """Run all tests for a contract"""

        import httpx

        results = {
            "contract_id": contract.id,
            "contract_name": contract.name,
            "tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0},
        }

        # Run tests for each endpoint
        for endpoint in contract.test_endpoints or []:
            test_name = f"Test {endpoint['method']} {endpoint['path']}"

            # Prepare request
            request_data = endpoint.get("request_data", {})
            headers = endpoint.get("headers", {})

            # Validate request against contract
            request_validation = ContractValidator.validate_request(
                request_data, contract
            )

            if not request_validation["valid"]:
                results["tests"].append(
                    {
                        "name": test_name,
                        "passed": False,
                        "errors": request_validation["errors"],
                    }
                )
                results["summary"]["failed"] += 1
                continue

            # Execute request
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=endpoint["method"],
                        url=f"{endpoint_url}{endpoint['path']}",
                        json=request_data
                        if endpoint["method"] in ["POST", "PUT", "PATCH"]
                        else None,
                        headers=headers,
                    )

                    # Validate response
                    response_data = response.json() if response.text else {}
                    response_validation = ContractValidator.validate_response(
                        response_data,
                        response.status_code,
                        dict(response.headers),
                        contract,
                    )

                    # Store test result
                    test_result = ContractTest(
                        contract_id=contract.id,
                        test_name=test_name,
                        test_type="integration",
                        endpoint=endpoint["path"],
                        request_data=request_data,
                        response_data=response_data,
                        passed=response_validation["valid"],
                        errors=response_validation["errors"],
                        warnings=response_validation["warnings"],
                        execution_time_ms=int(response.elapsed.total_seconds() * 1000),
                    )

                    db.add(test_result)

                    results["tests"].append(
                        {
                            "name": test_name,
                            "passed": response_validation["valid"],
                            "errors": response_validation["errors"],
                            "warnings": response_validation["warnings"],
                        }
                    )

                    if response_validation["valid"]:
                        results["summary"]["passed"] += 1
                    else:
                        results["summary"]["failed"] += 1

                    if response_validation["warnings"]:
                        results["summary"]["warnings"] += len(
                            response_validation["warnings"]
                        )

            except Exception as e:
                results["tests"].append(
                    {
                        "name": test_name,
                        "passed": False,
                        "errors": [f"Test execution failed: {str(e)}"],
                    }
                )
                results["summary"]["failed"] += 1

            results["summary"]["total"] += 1

        # Update contract test status
        contract.last_tested = datetime.utcnow()
        contract.last_test_status = (
            "passed" if results["summary"]["failed"] == 0 else "failed"
        )

        db.commit()

        return results
