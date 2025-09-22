"""
Postman Collection Import Module
Supports importing Postman collections (v2.1) and environments
"""

import json
import uuid
from typing import Dict, List, Any
import re


class PostmanImporter:
    """Import Postman collections and environments"""

    def __init__(self):
        self.collection = None
        self.environment = None
        self.imported_items = []
        self.errors = []

    def import_collection(self, collection_json: str) -> Dict[str, Any]:
        """Import a Postman collection v2.1"""
        try:
            collection = (
                json.loads(collection_json)
                if isinstance(collection_json, str)
                else collection_json
            )

            # Validate collection format
            if "info" not in collection:
                raise ValueError("Invalid Postman collection format")

            self.collection = collection
            info = collection.get("info", {})

            result = {
                "name": info.get("name", "Imported Collection"),
                "description": info.get("description", ""),
                "version": info.get("schema", "v2.1.0"),
                "requests": [],
                "folders": [],
                "variables": [],
                "auth": None,
                "events": [],
            }

            # Import variables
            if "variable" in collection:
                result["variables"] = self._import_variables(collection["variable"])

            # Import auth
            if "auth" in collection:
                result["auth"] = self._import_auth(collection["auth"])

            # Import events (pre-request scripts, tests)
            if "event" in collection:
                result["events"] = self._import_events(collection["event"])

            # Import items (requests and folders)
            if "item" in collection:
                self._import_items(collection["item"], result)

            return {
                "success": True,
                "collection": result,
                "stats": {
                    "total_requests": len(result["requests"]),
                    "total_folders": len(result["folders"]),
                    "total_variables": len(result["variables"]),
                    "errors": len(self.errors),
                },
                "errors": self.errors,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "errors": self.errors}

    def import_environment(self, environment_json: str) -> Dict[str, Any]:
        """Import a Postman environment"""
        try:
            environment = (
                json.loads(environment_json)
                if isinstance(environment_json, str)
                else environment_json
            )

            result = {
                "name": environment.get("name", "Imported Environment"),
                "variables": {},
            }

            # Import values
            for var in environment.get("values", []):
                if var.get("enabled", True):
                    key = var.get("key", "")
                    value = var.get("value", "")
                    result["variables"][key] = value

            return {
                "success": True,
                "environment": result,
                "stats": {"total_variables": len(result["variables"])},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _import_items(self, items: List[Dict], result: Dict, parent_folder: str = None):
        """Recursively import items (requests and folders)"""
        for item in items:
            if "request" in item:
                # It's a request
                request = self._import_request(item)
                if parent_folder:
                    request["folder"] = parent_folder
                result["requests"].append(request)
            elif "item" in item:
                # It's a folder
                folder = {
                    "id": str(uuid.uuid4()),
                    "name": item.get("name", "Unnamed Folder"),
                    "description": item.get("description", ""),
                    "parent": parent_folder,
                }
                result["folders"].append(folder)

                # Recursively import items in this folder
                self._import_items(item["item"], result, folder["id"])

    def _import_request(self, item: Dict) -> Dict[str, Any]:
        """Import a single request"""
        request = item.get("request", {})

        # Handle string URL or URL object
        url = request.get("url", "")
        if isinstance(url, dict):
            url_str = self._build_url_from_object(url)
        else:
            url_str = str(url)

        # Import headers
        headers = {}
        for header in request.get("header", []):
            if not header.get("disabled", False):
                headers[header.get("key", "")] = header.get("value", "")

        # Import body
        body = None
        body_type = None
        if "body" in request:
            body_data = request["body"]
            body_type = body_data.get("mode", "raw")

            if body_type == "raw":
                body = body_data.get("raw", "")
            elif body_type == "urlencoded":
                body = self._convert_urlencoded(body_data.get("urlencoded", []))
            elif body_type == "formdata":
                body = self._convert_formdata(body_data.get("formdata", []))
            elif body_type == "file":
                body = {"file": body_data.get("file", {}).get("src", "")}
            elif body_type == "graphql":
                body = body_data.get("graphql", {})

        # Import auth
        auth = None
        if "auth" in request:
            auth = self._import_auth(request["auth"])

        # Import tests and pre-request scripts
        tests = []
        pre_request = None

        for event in item.get("event", []):
            if event.get("listen") == "test":
                test_script = "\n".join(event.get("script", {}).get("exec", []))
                tests.append(test_script)
            elif event.get("listen") == "prerequest":
                pre_request = "\n".join(event.get("script", {}).get("exec", []))

        return {
            "id": str(uuid.uuid4()),
            "name": item.get("name", "Unnamed Request"),
            "description": item.get("description", ""),
            "method": request.get("method", "GET"),
            "url": url_str,
            "headers": headers,
            "body": body,
            "body_type": body_type,
            "auth": auth,
            "tests": tests,
            "pre_request_script": pre_request,
            "variables": item.get("variable", []),
        }

    def _build_url_from_object(self, url_obj: Dict) -> str:
        """Build URL string from Postman URL object"""
        protocol = url_obj.get("protocol", "http")
        host = ".".join(url_obj.get("host", ["localhost"]))
        port = url_obj.get("port", "")
        path = "/".join(url_obj.get("path", []))

        url = f"{protocol}://{host}"
        if port:
            url += f":{port}"
        if path:
            url += f"/{path}"

        # Add query parameters
        query = url_obj.get("query", [])
        if query:
            params = []
            for q in query:
                if not q.get("disabled", False):
                    key = q.get("key", "")
                    value = q.get("value", "")
                    params.append(f"{key}={value}")
            if params:
                url += "?" + "&".join(params)

        return url

    def _import_variables(self, variables: List[Dict]) -> List[Dict]:
        """Import collection variables"""
        result = []
        for var in variables:
            result.append(
                {
                    "key": var.get("key", ""),
                    "value": var.get("value", ""),
                    "type": var.get("type", "string"),
                    "description": var.get("description", ""),
                }
            )
        return result

    def _import_auth(self, auth: Dict) -> Dict:
        """Import authentication settings"""
        auth_type = auth.get("type", "noauth")

        if auth_type == "bearer":
            return {
                "type": "bearer",
                "bearer_token": auth.get("bearer", [{}])[0].get("value", ""),
            }
        elif auth_type == "basic":
            basic = auth.get("basic", [])
            username = next(
                (item["value"] for item in basic if item.get("key") == "username"), ""
            )
            password = next(
                (item["value"] for item in basic if item.get("key") == "password"), ""
            )
            return {"type": "basic", "username": username, "password": password}
        elif auth_type == "apikey":
            apikey = auth.get("apikey", [])
            key = next(
                (item["value"] for item in apikey if item.get("key") == "key"), ""
            )
            value = next(
                (item["value"] for item in apikey if item.get("key") == "value"), ""
            )
            location = next(
                (item["value"] for item in apikey if item.get("key") == "in"), "header"
            )
            return {"type": "apikey", "key": key, "value": value, "location": location}
        elif auth_type == "oauth2":
            oauth2 = auth.get("oauth2", [])
            return {
                "type": "oauth2",
                "access_token": next(
                    (
                        item["value"]
                        for item in oauth2
                        if item.get("key") == "accessToken"
                    ),
                    "",
                ),
                "token_type": next(
                    (
                        item["value"]
                        for item in oauth2
                        if item.get("key") == "tokenType"
                    ),
                    "Bearer",
                ),
            }
        else:
            return {"type": "noauth"}

    def _import_events(self, events: List[Dict]) -> List[Dict]:
        """Import collection-level events"""
        result = []
        for event in events:
            script_lines = event.get("script", {}).get("exec", [])
            result.append(
                {"listen": event.get("listen", ""), "script": "\n".join(script_lines)}
            )
        return result

    def _convert_urlencoded(self, data: List[Dict]) -> Dict:
        """Convert URL encoded data to dictionary"""
        result = {}
        for item in data:
            if not item.get("disabled", False):
                result[item.get("key", "")] = item.get("value", "")
        return result

    def _convert_formdata(self, data: List[Dict]) -> Dict:
        """Convert form data to dictionary"""
        result = {}
        for item in data:
            if not item.get("disabled", False):
                key = item.get("key", "")
                if item.get("type") == "file":
                    result[key] = {"type": "file", "src": item.get("src", "")}
                else:
                    result[key] = item.get("value", "")
        return result

    def convert_to_internal_format(self, imported_collection: Dict) -> Dict:
        """Convert imported Postman collection to internal format"""
        # This converts to the format used by API Orchestrator
        internal = {
            "project": {
                "name": imported_collection["name"],
                "description": imported_collection["description"],
                "source_type": "postman_import",
            },
            "collections": [],
            "environments": [
                {
                    "name": "Default",
                    "variables": {
                        var["key"]: var["value"]
                        for var in imported_collection.get("variables", [])
                    },
                }
            ],
            "requests": [],
        }

        # Convert folders to collections
        folders_map = {}
        for folder in imported_collection.get("folders", []):
            collection = {
                "id": folder["id"],
                "name": folder["name"],
                "description": folder["description"],
                "requests": [],
            }
            folders_map[folder["id"]] = collection
            internal["collections"].append(collection)

        # Add a default collection if no folders
        if not internal["collections"]:
            default_collection = {
                "id": "default",
                "name": "Imported Requests",
                "description": "Requests imported from Postman",
                "requests": [],
            }
            internal["collections"].append(default_collection)
            folders_map["default"] = default_collection

        # Convert requests
        for request in imported_collection.get("requests", []):
            internal_request = {
                "id": request["id"],
                "name": request["name"],
                "description": request["description"],
                "method": request["method"],
                "url": request["url"],
                "headers": request["headers"],
                "body": request["body"],
                "auth": request["auth"],
                "assertions": self._convert_tests_to_assertions(
                    request.get("tests", [])
                ),
                "pre_request_script": request.get("pre_request_script"),
                "collection_id": request.get("folder", "default"),
            }

            internal["requests"].append(internal_request)

            # Add to appropriate collection
            collection_id = request.get("folder", "default")
            if collection_id in folders_map:
                folders_map[collection_id]["requests"].append(internal_request["id"])

        return internal

    def _convert_tests_to_assertions(self, test_scripts: List[str]) -> List[Dict]:
        """Convert Postman test scripts to assertions"""
        assertions = []

        for script in test_scripts:
            # Parse common Postman test patterns
            # Status code check
            status_match = re.search(r"pm\.response\.to\.have\.status\((\d+)\)", script)
            if status_match:
                assertions.append(
                    {
                        "type": "STATUS_CODE",
                        "expected": int(status_match.group(1)),
                        "operator": "equals",
                        "description": f"Status code should be {status_match.group(1)}",
                    }
                )

            # Response time check
            time_match = re.search(r"pm\.response\.responseTime.*?(\d+)", script)
            if time_match:
                assertions.append(
                    {
                        "type": "RESPONSE_TIME",
                        "expected": int(time_match.group(1)),
                        "operator": "less_than",
                        "description": f"Response time should be less than {time_match.group(1)}ms",
                    }
                )

            # Body contains check
            contains_match = re.findall(
                r'pm\.expect\(.*?responseBody.*?\)\.to\.include\(["\'](.+?)["\']\)',
                script,
            )
            for match in contains_match:
                assertions.append(
                    {
                        "type": "BODY_CONTAINS",
                        "expected": match,
                        "operator": "contains",
                        "description": f"Response body should contain '{match}'",
                    }
                )

            # JSON value check
            json_match = re.findall(
                r"pm\.expect\(jsonData\.(.+?)\)\.to\.eql\((.+?)\)", script
            )
            for path, value in json_match:
                assertions.append(
                    {
                        "type": "BODY_JSON_PATH",
                        "expected": {"path": f"$.{path}", "value": value},
                        "operator": "equals",
                        "description": f"JSON path {path} should equal {value}",
                    }
                )

            # Header exists
            header_match = re.findall(
                r'pm\.response\.to\.have\.header\(["\'](.+?)["\']\)', script
            )
            for header in header_match:
                assertions.append(
                    {
                        "type": "HEADER_EXISTS",
                        "expected": header,
                        "operator": "exists",
                        "description": f"Response should have header '{header}'",
                    }
                )

        # Add default assertions if none found
        if not assertions:
            assertions.append(
                {
                    "type": "STATUS_CODE",
                    "expected": 200,
                    "operator": "equals",
                    "description": "Status code should be 200",
                }
            )

        return assertions
