"""
Multi-file OpenAPI Support
Handle OpenAPI 3.0 specifications split across multiple files with $ref resolution
"""

import json
import yaml
from typing import Dict, Any, List
from pathlib import Path
from copy import deepcopy


class OpenAPIRefResolver:
    """Resolve $ref references in multi-file OpenAPI specifications"""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.resolved_refs = {}  # Cache resolved references
        self.file_cache = {}  # Cache loaded files

    def resolve_spec(self, spec_path: str) -> Dict[str, Any]:
        """
        Resolve a complete OpenAPI specification with all $ref references

        Args:
            spec_path: Path to the main OpenAPI spec file

        Returns:
            Fully resolved OpenAPI specification
        """
        # Load main spec
        main_spec = self._load_file(spec_path)

        # Set base path from spec location
        self.base_path = Path(spec_path).parent

        # Resolve all references
        resolved_spec = self._resolve_references(main_spec, spec_path)

        return resolved_spec

    def _load_file(self, file_path: str) -> Dict[str, Any]:
        """Load a YAML or JSON file"""
        if file_path in self.file_cache:
            return deepcopy(self.file_cache[file_path])

        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = self.base_path / full_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            if full_path.suffix in [".yaml", ".yml"]:
                content = yaml.safe_load(f)
            elif full_path.suffix == ".json":
                content = json.load(f)
            else:
                # Try both
                try:
                    content = yaml.safe_load(f)
                except Exception:
                    content = json.load(f)

        self.file_cache[file_path] = content
        return deepcopy(content)

    def _resolve_references(
        self, obj: Any, current_file: str, visited: set = None
    ) -> Any:
        """Recursively resolve all $ref references in an object"""
        if visited is None:
            visited = set()

        if isinstance(obj, dict):
            if "$ref" in obj:
                # Resolve the reference
                ref_value = obj["$ref"]

                # Check for circular references
                if ref_value in visited:
                    print(f"Warning: Circular reference detected: {ref_value}")
                    return obj

                visited.add(ref_value)
                resolved = self._resolve_single_ref(ref_value, current_file)

                # Merge other properties with resolved reference
                if len(obj) > 1:
                    # If there are other properties besides $ref, merge them
                    other_props = {k: v for k, v in obj.items() if k != "$ref"}
                    if isinstance(resolved, dict):
                        resolved = {**resolved, **other_props}

                # Continue resolving in the resolved object
                return self._resolve_references(resolved, current_file, visited.copy())
            else:
                # Recursively resolve in all values
                return {
                    key: self._resolve_references(value, current_file, visited.copy())
                    for key, value in obj.items()
                }

        elif isinstance(obj, list):
            return [
                self._resolve_references(item, current_file, visited.copy())
                for item in obj
            ]

        else:
            return obj

    def _resolve_single_ref(self, ref: str, current_file: str) -> Any:
        """Resolve a single $ref reference"""
        # Check cache
        cache_key = f"{current_file}:{ref}"
        if cache_key in self.resolved_refs:
            return deepcopy(self.resolved_refs[cache_key])

        # Parse the reference
        if ref.startswith("#"):
            # Internal reference within the same file
            result = self._resolve_internal_ref(ref, current_file)
        elif ref.startswith("http://") or ref.startswith("https://"):
            # External HTTP reference
            result = self._resolve_http_ref(ref)
        else:
            # File reference (possibly with fragment)
            result = self._resolve_file_ref(ref, current_file)

        # Cache the result
        self.resolved_refs[cache_key] = result
        return deepcopy(result)

    def _resolve_internal_ref(self, ref: str, current_file: str) -> Any:
        """Resolve an internal reference within the same file"""
        # Remove the leading #
        json_pointer = ref[1:]

        # Load the current file
        content = self._load_file(current_file)

        # Navigate the JSON pointer
        return self._navigate_json_pointer(content, json_pointer)

    def _resolve_file_ref(self, ref: str, current_file: str) -> Any:
        """Resolve a reference to another file"""
        # Split file path and fragment
        if "#" in ref:
            file_path, fragment = ref.split("#", 1)
        else:
            file_path = ref
            fragment = ""

        # Resolve relative path
        if not Path(file_path).is_absolute():
            base_dir = Path(current_file).parent
            file_path = str(base_dir / file_path)

        # Load the referenced file
        content = self._load_file(file_path)

        # If there's a fragment, navigate to it
        if fragment:
            content = self._navigate_json_pointer(content, fragment)

        # Continue resolving references in the loaded content
        return self._resolve_references(content, file_path)

    def _resolve_http_ref(self, ref: str) -> Any:
        """Resolve an HTTP reference (not implemented for security reasons)"""
        print(f"Warning: HTTP references are not supported for security reasons: {ref}")
        return {"$ref": ref}

    def _navigate_json_pointer(self, obj: Any, pointer: str) -> Any:
        """Navigate a JSON pointer path in an object"""
        if not pointer or pointer == "/":
            return obj

        # Split the pointer into parts
        parts = pointer.strip("/").split("/")

        # Navigate through the object
        current = obj
        for part in parts:
            # Unescape JSON pointer tokens
            part = part.replace("~1", "/").replace("~0", "~")

            if isinstance(current, dict):
                if part not in current:
                    raise KeyError(f"Key '{part}' not found in object")
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    raise KeyError(f"Invalid array index: {part}")
            else:
                raise TypeError(f"Cannot navigate into {type(current)}")

        return current


class MultiFileOpenAPIManager:
    """Manage multi-file OpenAPI specifications"""

    def __init__(self):
        self.resolver = OpenAPIRefResolver()

    def bundle_spec(self, spec_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        Bundle a multi-file OpenAPI spec into a single file

        Args:
            spec_path: Path to the main OpenAPI spec file
            output_path: Optional path to save the bundled spec

        Returns:
            Bundled OpenAPI specification
        """
        # Resolve all references
        bundled = self.resolver.resolve_spec(spec_path)

        # Save if output path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                if output_path.endswith(".yaml") or output_path.endswith(".yml"):
                    yaml.dump(bundled, f, default_flow_style=False, sort_keys=False)
                else:
                    json.dump(bundled, f, indent=2)

        return bundled

    def validate_refs(self, spec_path: str) -> List[str]:
        """
        Validate all $ref references in a specification

        Args:
            spec_path: Path to the main OpenAPI spec file

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            # Try to resolve the spec
            self.resolver.resolve_spec(spec_path)
        except FileNotFoundError as e:
            errors.append(f"File not found: {e}")
        except KeyError as e:
            errors.append(f"Invalid reference: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def split_spec(self, spec_path: str, output_dir: str):
        """
        Split a single OpenAPI spec into multiple files

        Args:
            spec_path: Path to the OpenAPI spec file
            output_dir: Directory to save the split files
        """
        # Load the spec
        with open(spec_path, "r", encoding="utf-8") as f:
            if spec_path.endswith(".yaml") or spec_path.endswith(".yml"):
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split components into separate files
        if "components" in spec:
            components = spec["components"]

            # Schemas
            if "schemas" in components:
                schemas_dir = output_dir / "schemas"
                schemas_dir.mkdir(exist_ok=True)

                for schema_name, schema_def in components["schemas"].items():
                    schema_file = schemas_dir / f"{schema_name}.yaml"
                    with open(schema_file, "w") as f:
                        yaml.dump(schema_def, f, default_flow_style=False)

                    # Replace with $ref
                    components["schemas"][schema_name] = {
                        "$ref": f"./schemas/{schema_name}.yaml"
                    }

            # Parameters
            if "parameters" in components:
                params_dir = output_dir / "parameters"
                params_dir.mkdir(exist_ok=True)

                for param_name, param_def in components["parameters"].items():
                    param_file = params_dir / f"{param_name}.yaml"
                    with open(param_file, "w") as f:
                        yaml.dump(param_def, f, default_flow_style=False)

                    components["parameters"][param_name] = {
                        "$ref": f"./parameters/{param_name}.yaml"
                    }

            # Responses
            if "responses" in components:
                responses_dir = output_dir / "responses"
                responses_dir.mkdir(exist_ok=True)

                for response_name, response_def in components["responses"].items():
                    response_file = responses_dir / f"{response_name}.yaml"
                    with open(response_file, "w") as f:
                        yaml.dump(response_def, f, default_flow_style=False)

                    components["responses"][response_name] = {
                        "$ref": f"./responses/{response_name}.yaml"
                    }

        # Split paths into separate files
        if "paths" in spec:
            paths_dir = output_dir / "paths"
            paths_dir.mkdir(exist_ok=True)

            for path, path_def in spec["paths"].items():
                # Create safe filename from path
                safe_name = (
                    path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
                )
                path_file = paths_dir / f"{safe_name}.yaml"

                with open(path_file, "w") as f:
                    yaml.dump(path_def, f, default_flow_style=False)

                spec["paths"][path] = {"$ref": f"./paths/{safe_name}.yaml"}

        # Save the main spec file
        main_file = output_dir / "openapi.yaml"
        with open(main_file, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        print(f"Spec split into multiple files in {output_dir}")
        print(f"Main file: {main_file}")


# Example usage
if __name__ == "__main__":
    manager = MultiFileOpenAPIManager()

    # Bundle a multi-file spec
    bundled = manager.bundle_spec("api-spec/openapi.yaml", "bundled-spec.yaml")

    # Validate references
    errors = manager.validate_refs("api-spec/openapi.yaml")
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("All references valid!")

    # Split a single spec
    manager.split_spec("single-spec.yaml", "split-spec/")
