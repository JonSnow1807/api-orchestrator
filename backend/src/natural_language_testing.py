"""
Natural Language Test Generation
Allows users to create tests using plain English commands
Competitive with Postman's Postbot capabilities
"""

import re
from typing import Dict, Any, List, Optional


class NaturalLanguageTestGenerator:
    """Generate test code from natural language descriptions"""

    def __init__(self):
        self.test_patterns = {
            # Status code patterns
            r"status (?:code )?(?:is |should be |equals? )?(\d+)": self._generate_status_test,
            r"(?:response )?(?:is |should be )?(?:successful|ok|success)": lambda: "pm.response.to.have.status(200)",
            r"(?:response )?(?:is |should be )?(?:not found|404)": lambda: "pm.response.to.have.status(404)",
            r"(?:response )?(?:is |should be )?(?:unauthorized|401)": lambda: "pm.response.to.have.status(401)",
            r"(?:response )?(?:is |should be )?(?:forbidden|403)": lambda: "pm.response.to.have.status(403)",
            r"(?:response )?(?:is |should be )?(?:bad request|400)": lambda: "pm.response.to.have.status(400)",
            # Response time patterns
            r"response time (?:is |should be )?(?:less than |below |< )?(\d+)(?:ms)?": self._generate_response_time_test,
            r"(?:response )?(?:is |should be )?fast": lambda: "pm.expect(pm.response.responseTime).to.be.below(1000)",
            r"(?:response )?(?:is |should be )?slow": lambda: "pm.expect(pm.response.responseTime).to.be.above(2000)",
            # Header patterns
            r"(?:has |contains? |includes? )?header ['\"]?([^'\"]+)['\"]?": self._generate_header_exists_test,
            r"header ['\"]?([^'\"]+)['\"]? (?:is |equals? |contains? )['\"]?([^'\"]+)['\"]?": self._generate_header_value_test,
            r"content[- ]?type (?:is |equals? )['\"]?([^'\"]+)['\"]?": self._generate_content_type_test,
            # Body/JSON patterns
            r"(?:body |response )?(?:has |contains? |includes? )['\"]?([^'\"]+)['\"]? (?:field|property|key)": self._generate_property_exists_test,
            r"['\"]?([^'\"]+)['\"]? (?:field |property |key )?(?:is |equals? |should be )['\"]?([^'\"]+)['\"]?": self._generate_property_value_test,
            r"(?:body |response )?(?:is |should be )?(?:not )?empty": self._generate_empty_body_test,
            r"(?:body |response )?(?:is |should be )?(?:valid )?json": lambda: "pm.response.to.be.json",
            r"(?:body |response )?(?:contains? |includes? )['\"]?([^'\"]+)['\"]?": self._generate_body_contains_test,
            # Array patterns
            r"(?:array |list )?['\"]?([^'\"]+)['\"]? (?:has |contains? )?(\d+) (?:items?|elements?)": self._generate_array_length_test,
            r"(?:array |list )?['\"]?([^'\"]+)['\"]? (?:is |should be )?(?:not )?empty": self._generate_array_empty_test,
            # Schema validation
            r"(?:matches? |validates? against |follows? )?schema": self._generate_schema_validation,
            r"(?:has |contains? )?required fields?": self._generate_required_fields_test,
            # Authentication patterns
            r"(?:is |should be )?authenticated": lambda: "pm.expect(pm.response.headers.get('Authorization')).to.exist",
            r"(?:has |contains? )?(?:valid )?token": self._generate_token_test,
            # Email/URL validation
            r"['\"]?([^'\"]+)['\"]? (?:is |should be )?(?:valid )?email": self._generate_email_validation,
            r"['\"]?([^'\"]+)['\"]? (?:is |should be )?(?:valid )?url": self._generate_url_validation,
            # Date patterns
            r"['\"]?([^'\"]+)['\"]? (?:is |should be )?(?:valid )?date": self._generate_date_validation,
            r"['\"]?([^'\"]+)['\"]? (?:is |should be )?(?:in the )?future": self._generate_future_date_test,
            r"['\"]?([^'\"]+)['\"]? (?:is |should be )?(?:in the )?past": self._generate_past_date_test,
        }

        self.ai_suggestions = {
            "auth": [
                "Check if response has valid token",
                "Verify authorization header exists",
                "Test if user is authenticated",
            ],
            "crud": [
                "Check if item was created successfully",
                "Verify response contains new ID",
                "Test if all required fields are present",
            ],
            "error": [
                "Check if error message is descriptive",
                "Verify error code is present",
                "Test if status code matches error type",
            ],
            "performance": [
                "Response time is less than 500ms",
                "Check if response is cached",
                "Verify no unnecessary data in response",
            ],
        }

    def generate_test(
        self, natural_language: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate test code from natural language description

        Args:
            natural_language: Plain English test description
            context: Optional context with response data, headers, etc.

        Returns:
            Dict with generated test code and metadata
        """
        natural_language = natural_language.lower().strip()
        generated_tests = []
        test_descriptions = []

        # Try to match patterns
        for pattern, generator in self.test_patterns.items():
            match = re.search(pattern, natural_language, re.IGNORECASE)
            if match:
                if callable(generator):
                    if match.groups():
                        test_code = generator(*match.groups())
                    else:
                        test_code = generator()

                    if test_code:
                        generated_tests.append(test_code)
                        test_descriptions.append(
                            self._get_description_for_test(pattern, match)
                        )

        # If no patterns matched, try intelligent generation
        if not generated_tests and context:
            generated_tests = self._intelligent_test_generation(
                natural_language, context
            )
            test_descriptions = [f"AI-generated test for: {natural_language}"]

        # Combine all tests
        if generated_tests:
            test_script = self._format_test_script(generated_tests, test_descriptions)
            return {
                "success": True,
                "test_script": test_script,
                "test_count": len(generated_tests),
                "descriptions": test_descriptions,
                "language": "javascript",
                "framework": "postman",
            }

        # Fallback to suggestions
        return {
            "success": False,
            "message": "Could not generate test from description",
            "suggestions": self._get_suggestions(natural_language),
            "help": "Try being more specific, e.g., 'status code is 200' or 'response has user field'",
        }

    def _generate_status_test(self, status_code: str) -> str:
        """Generate status code test"""
        return f"pm.response.to.have.status({status_code})"

    def _generate_response_time_test(self, time_ms: str) -> str:
        """Generate response time test"""
        return f"pm.expect(pm.response.responseTime).to.be.below({time_ms})"

    def _generate_header_exists_test(self, header_name: str) -> str:
        """Generate header existence test"""
        return f"pm.response.to.have.header('{header_name}')"

    def _generate_header_value_test(self, header_name: str, header_value: str) -> str:
        """Generate header value test"""
        return f"pm.expect(pm.response.headers.get('{header_name}')).to.eql('{header_value}')"

    def _generate_content_type_test(self, content_type: str) -> str:
        """Generate content-type test"""
        if "json" in content_type:
            return "pm.response.to.have.header('Content-Type', 'application/json')"
        return f"pm.response.to.have.header('Content-Type', '{content_type}')"

    def _generate_property_exists_test(self, property_name: str) -> str:
        """Generate property existence test"""
        return f"pm.expect(pm.response.json()).to.have.property('{property_name}')"

    def _generate_property_value_test(
        self, property_name: str, expected_value: str
    ) -> str:
        """Generate property value test"""
        # Try to parse value type
        if expected_value.lower() in ["true", "false"]:
            return f"pm.expect(pm.response.json().{property_name}).to.eql({expected_value.lower()})"
        elif expected_value.isdigit():
            return f"pm.expect(pm.response.json().{property_name}).to.eql({expected_value})"
        else:
            return f"pm.expect(pm.response.json().{property_name}).to.eql('{expected_value}')"

    def _generate_empty_body_test(self) -> str:
        """Generate empty body test"""
        return "pm.expect(pm.response.text()).to.be.empty"

    def _generate_body_contains_test(self, text: str) -> str:
        """Generate body contains text test"""
        return f"pm.expect(pm.response.text()).to.include('{text}')"

    def _generate_array_length_test(self, array_name: str, length: str) -> str:
        """Generate array length test"""
        return f"pm.expect(pm.response.json().{array_name}).to.have.lengthOf({length})"

    def _generate_array_empty_test(self, array_name: str) -> str:
        """Generate array empty test"""
        return f"pm.expect(pm.response.json().{array_name}).to.be.empty"

    def _generate_schema_validation(self) -> str:
        """Generate schema validation test"""
        return """const schema = {
    type: 'object',
    required: ['id', 'name'],
    properties: {
        id: { type: 'number' },
        name: { type: 'string' }
    }
};
pm.response.to.have.jsonSchema(schema)"""

    def _generate_required_fields_test(self) -> str:
        """Generate required fields test"""
        return """const requiredFields = ['id', 'name', 'email'];
requiredFields.forEach(field => {
    pm.expect(pm.response.json()).to.have.property(field);
})"""

    def _generate_token_test(self) -> str:
        """Generate token validation test"""
        return """const jsonData = pm.response.json();
pm.expect(jsonData.token).to.exist;
pm.expect(jsonData.token).to.be.a('string');
pm.expect(jsonData.token.length).to.be.above(20)"""

    def _generate_email_validation(self, field_name: str) -> str:
        """Generate email validation test"""
        return f"""const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
pm.expect(pm.response.json().{field_name}).to.match(emailRegex)"""

    def _generate_url_validation(self, field_name: str) -> str:
        """Generate URL validation test"""
        return f"""const urlRegex = /^https?:\\/\\/.+/;
pm.expect(pm.response.json().{field_name}).to.match(urlRegex)"""

    def _generate_date_validation(self, field_name: str) -> str:
        """Generate date validation test"""
        return f"""const dateValue = pm.response.json().{field_name};
pm.expect(new Date(dateValue).toString()).to.not.equal('Invalid Date')"""

    def _generate_future_date_test(self, field_name: str) -> str:
        """Generate future date test"""
        return f"""const dateValue = new Date(pm.response.json().{field_name});
const now = new Date();
pm.expect(dateValue.getTime()).to.be.above(now.getTime())"""

    def _generate_past_date_test(self, field_name: str) -> str:
        """Generate past date test"""
        return f"""const dateValue = new Date(pm.response.json().{field_name});
const now = new Date();
pm.expect(dateValue.getTime()).to.be.below(now.getTime())"""

    def _intelligent_test_generation(
        self, description: str, context: Dict
    ) -> List[str]:
        """Generate tests using AI-like intelligence based on context"""
        tests = []

        # Analyze response data if available
        if "response" in context:
            response = context["response"]

            # Check for common patterns
            if isinstance(response, dict):
                # Look for ID fields
                if any(key in response for key in ["id", "ID", "_id", "uuid"]):
                    tests.append("pm.expect(pm.response.json()).to.have.property('id')")

                # Look for user data
                if any(key in response for key in ["user", "username", "email"]):
                    tests.append("pm.expect(pm.response.json().user).to.exist")

                # Look for arrays
                for key, value in response.items():
                    if isinstance(value, list):
                        tests.append(
                            f"pm.expect(pm.response.json().{key}).to.be.an('array')"
                        )
                    elif isinstance(value, dict):
                        tests.append(
                            f"pm.expect(pm.response.json().{key}).to.be.an('object')"
                        )

        # Add basic success test if nothing else
        if not tests:
            tests.append("pm.response.to.have.status(200)")
            tests.append("pm.response.to.be.json")

        return tests

    def _get_description_for_test(self, pattern: str, match) -> str:
        """Get human-readable description for generated test"""
        descriptions = {
            r"status": f"Check if status code is {match.group(1) if match.groups() else '200'}",
            r"response time": f"Verify response time is less than {match.group(1)}ms",
            r"header": f"Check header '{match.group(1) if match.groups() else 'header'}'",
            r"property": f"Verify property '{match.group(1) if match.groups() else 'property'}' exists",
            r"email": "Validate email format",
            r"url": "Validate URL format",
            r"date": "Validate date format",
            r"array": f"Check array '{match.group(1) if match.groups() else 'array'}' length",
            r"json": "Verify response is valid JSON",
            r"empty": "Check if response is empty",
            r"authenticated": "Verify authentication",
            r"token": "Validate token presence",
        }

        for key, desc in descriptions.items():
            if key in pattern:
                return desc

        return "Custom test assertion"

    def _format_test_script(self, tests: List[str], descriptions: List[str]) -> str:
        """Format multiple tests into a complete test script"""
        script = "// Auto-generated tests from natural language\n\n"

        for i, (test, desc) in enumerate(zip(tests, descriptions), 1):
            script += f"// Test {i}: {desc}\n"
            script += f"pm.test('{desc}', function() {{\n"

            # Indent multi-line tests
            if "\n" in test:
                indented = "\n".join(f"    {line}" for line in test.split("\n"))
                script += f"{indented}\n"
            else:
                script += f"    {test};\n"

            script += "});\n\n"

        return script.strip()

    def _get_suggestions(self, input_text: str) -> List[str]:
        """Get suggestions based on input text"""
        suggestions = []

        # Detect context and provide relevant suggestions
        if any(word in input_text for word in ["auth", "login", "token"]):
            suggestions.extend(self.ai_suggestions["auth"])
        elif any(word in input_text for word in ["create", "add", "post", "new"]):
            suggestions.extend(self.ai_suggestions["crud"])
        elif any(word in input_text for word in ["error", "fail", "invalid"]):
            suggestions.extend(self.ai_suggestions["error"])
        elif any(
            word in input_text for word in ["fast", "slow", "time", "performance"]
        ):
            suggestions.extend(self.ai_suggestions["performance"])
        else:
            # Generic suggestions
            suggestions = [
                "Check if status code is 200",
                "Verify response has required fields",
                "Test if response time is less than 1000ms",
                "Check if response is valid JSON",
                "Verify authentication header exists",
            ]

        return suggestions[:5]  # Return top 5 suggestions

    async def generate_from_response(
        self, response_data: Dict, selected_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate tests based on actual response data (inline testing)

        Args:
            response_data: The API response data
            selected_field: Optional field selected by user for focused testing

        Returns:
            Dict with generated tests
        """
        tests = []

        if selected_field:
            # Generate specific tests for selected field
            field_value = self._get_nested_value(response_data, selected_field)

            if field_value is not None:
                # Determine field type and generate appropriate tests
                if isinstance(field_value, bool):
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.be.a('boolean')"
                    )
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.eql({str(field_value).lower()})"
                    )
                elif isinstance(field_value, int) or isinstance(field_value, float):
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.be.a('number')"
                    )
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.eql({field_value})"
                    )
                elif isinstance(field_value, str):
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.be.a('string')"
                    )
                    if "@" in field_value:  # Likely email
                        tests.append(
                            f"pm.expect(pm.response.json().{selected_field}).to.match(/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/)"
                        )
                    elif field_value.startswith("http"):  # Likely URL
                        tests.append(
                            f"pm.expect(pm.response.json().{selected_field}).to.match(/^https?:\\/\\/.+/)"
                        )
                    else:
                        tests.append(
                            f"pm.expect(pm.response.json().{selected_field}).to.eql('{field_value}')"
                        )
                elif isinstance(field_value, list):
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.be.an('array')"
                    )
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.have.lengthOf({len(field_value)})"
                    )
                elif isinstance(field_value, dict):
                    tests.append(
                        f"pm.expect(pm.response.json().{selected_field}).to.be.an('object')"
                    )
                    for key in field_value.keys():
                        tests.append(
                            f"pm.expect(pm.response.json().{selected_field}).to.have.property('{key}')"
                        )
        else:
            # Generate comprehensive tests for entire response
            tests.extend(self._analyze_response_structure(response_data))

        # Format as complete test script
        if tests:
            descriptions = [
                f"Test for {selected_field}"
                if selected_field
                else "Comprehensive response test"
            ] * len(tests)
            test_script = self._format_test_script(tests, descriptions)

            return {
                "success": True,
                "test_script": test_script,
                "test_count": len(tests),
                "field_tested": selected_field,
                "auto_generated": True,
            }

        return {
            "success": False,
            "message": "Could not generate tests for the selected data",
        }

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot notation"""
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _analyze_response_structure(self, data: Any, prefix: str = "") -> List[str]:
        """Analyze response structure and generate comprehensive tests"""
        tests = []

        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{prefix}.{key}" if prefix else key
                tests.append(
                    f"pm.expect(pm.response.json(){('.' + prefix) if prefix else ''}).to.have.property('{key}')"
                )

                # Type checks
                if isinstance(value, bool):
                    tests.append(
                        f"pm.expect(pm.response.json().{field_path}).to.be.a('boolean')"
                    )
                elif isinstance(value, (int, float)):
                    tests.append(
                        f"pm.expect(pm.response.json().{field_path}).to.be.a('number')"
                    )
                elif isinstance(value, str):
                    tests.append(
                        f"pm.expect(pm.response.json().{field_path}).to.be.a('string')"
                    )
                elif isinstance(value, list):
                    tests.append(
                        f"pm.expect(pm.response.json().{field_path}).to.be.an('array')"
                    )
                elif isinstance(value, dict):
                    tests.append(
                        f"pm.expect(pm.response.json().{field_path}).to.be.an('object')"
                    )

        return tests[:20]  # Limit to 20 tests to avoid overwhelming


# Export for use
__all__ = ["NaturalLanguageTestGenerator"]
