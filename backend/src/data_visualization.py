"""
Data Visualization Backend Module
Provides intelligent data visualization suggestions and transformations
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import re
from datetime import datetime
import statistics
from collections import Counter, defaultdict


class VisualizationType(Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    TABLE = "table"
    JSON_TREE = "json_tree"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"


class DataVisualizationEngine:
    """
    Intelligent data visualization engine with AI-powered suggestions
    """

    def __init__(self):
        self.type_patterns = {
            "time_series": r"(date|time|timestamp|created|updated|modified|year|month|day)",
            "categorical": r"(category|type|status|state|group|class|label|tag)",
            "numerical": r"(count|amount|price|value|score|rating|quantity|total|sum)",
            "percentage": r"(percent|ratio|rate|proportion)",
            "geographic": r"(country|city|region|location|latitude|longitude|geo)",
        }

    def analyze_data(self, data: Any) -> Dict[str, Any]:
        """
        Analyze data structure and content for visualization recommendations
        """
        if isinstance(data, dict):
            return self._analyze_dict(data)
        elif isinstance(data, list):
            return self._analyze_list(data)
        else:
            return {
                "data_type": "scalar",
                "recommended_viz": [VisualizationType.TABLE.value],
                "structure": "single_value",
            }

    def _analyze_dict(self, data: Dict) -> Dict[str, Any]:
        """Analyze dictionary data structure"""
        analysis = {
            "data_type": "object",
            "keys": list(data.keys()),
            "field_types": {},
            "recommended_viz": [],
            "insights": [],
        }

        # Analyze each field
        for key, value in data.items():
            field_type = self._detect_field_type(key, value)
            analysis["field_types"][key] = field_type

        # Recommend visualizations based on field types
        if any(ft == "numerical" for ft in analysis["field_types"].values()):
            analysis["recommended_viz"].append(VisualizationType.BAR.value)

        if any(ft == "categorical" for ft in analysis["field_types"].values()):
            analysis["recommended_viz"].append(VisualizationType.PIE.value)

        if len(data) <= 10:
            analysis["recommended_viz"].append(VisualizationType.TABLE.value)

        analysis["recommended_viz"].append(VisualizationType.JSON_TREE.value)

        return analysis

    def _analyze_list(self, data: List) -> Dict[str, Any]:
        """Analyze list data structure"""
        if not data:
            return {
                "data_type": "empty_array",
                "recommended_viz": [VisualizationType.TABLE.value],
                "structure": "empty",
            }

        analysis = {
            "data_type": "array",
            "length": len(data),
            "recommended_viz": [],
            "insights": [],
        }

        # Check if all items are objects with same structure
        if all(isinstance(item, dict) for item in data):
            # Get common keys
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())

            analysis["common_keys"] = list(all_keys)

            # Detect field types from first item
            if data[0]:
                field_types = {}
                for key in all_keys:
                    sample_value = next(
                        (item.get(key) for item in data if key in item), None
                    )
                    if sample_value is not None:
                        field_types[key] = self._detect_field_type(key, sample_value)
                analysis["field_types"] = field_types

                # Recommend visualizations
                has_time = any(ft == "time_series" for ft in field_types.values())
                has_numerical = any(ft == "numerical" for ft in field_types.values())
                has_categorical = any(
                    ft == "categorical" for ft in field_types.values()
                )

                if has_time and has_numerical:
                    analysis["recommended_viz"].extend(
                        [VisualizationType.LINE.value, VisualizationType.AREA.value]
                    )
                    analysis["insights"].append(
                        "Time series data detected - line or area chart recommended"
                    )

                if has_categorical and has_numerical:
                    analysis["recommended_viz"].extend(
                        [VisualizationType.BAR.value, VisualizationType.PIE.value]
                    )
                    analysis["insights"].append(
                        "Categorical data with values - bar or pie chart recommended"
                    )

                if has_numerical and len(all_keys) >= 2:
                    analysis["recommended_viz"].append(VisualizationType.SCATTER.value)
                    analysis["insights"].append(
                        "Multiple numerical fields - scatter plot available"
                    )

                if len(all_keys) >= 3 and has_numerical:
                    analysis["recommended_viz"].append(VisualizationType.RADAR.value)
                    analysis["insights"].append(
                        "Multi-dimensional data - radar chart available"
                    )

        # For simple arrays
        elif all(isinstance(item, (int, float)) for item in data):
            analysis["recommended_viz"].extend(
                [VisualizationType.LINE.value, VisualizationType.BAR.value]
            )
            analysis["insights"].append(
                "Numerical array - line or bar chart recommended"
            )

        # Always include table as an option
        analysis["recommended_viz"].append(VisualizationType.TABLE.value)

        return analysis

    def _detect_field_type(self, key: str, value: Any) -> str:
        """Detect the type of a field based on key name and value"""
        key_lower = key.lower()

        # Check key patterns
        for pattern_type, pattern in self.type_patterns.items():
            if re.search(pattern, key_lower):
                return pattern_type

        # Check value type
        if isinstance(value, (int, float)):
            return "numerical"
        elif isinstance(value, str):
            # Check if it's a date string
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                return "time_series"
            except Exception:
                pass

            # Check if it's a number string
            try:
                float(value)
                return "numerical"
            except Exception:
                return "categorical"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (list, dict)):
            return "complex"
        else:
            return "unknown"

    def transform_for_visualization(
        self,
        data: Any,
        viz_type: VisualizationType,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Transform data for specific visualization type
        """
        options = options or {}

        if viz_type == VisualizationType.LINE:
            return self._transform_for_line(data, options)
        elif viz_type == VisualizationType.BAR:
            return self._transform_for_bar(data, options)
        elif viz_type == VisualizationType.PIE:
            return self._transform_for_pie(data, options)
        elif viz_type == VisualizationType.SCATTER:
            return self._transform_for_scatter(data, options)
        elif viz_type == VisualizationType.RADAR:
            return self._transform_for_radar(data, options)
        elif viz_type == VisualizationType.AREA:
            return self._transform_for_area(data, options)
        elif viz_type == VisualizationType.TABLE:
            return self._transform_for_table(data, options)
        else:
            return {"data": data, "type": viz_type.value}

    def _transform_for_line(self, data: Any, options: Dict) -> Dict[str, Any]:
        """Transform data for line chart"""
        x_field = options.get("x_field", "x")
        y_field = options.get("y_field", "y")

        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # Extract x and y values
            chart_data = []
            for item in data:
                point = {}
                # Try to find x value
                if x_field in item:
                    point["x"] = item[x_field]
                else:
                    # Look for time-series field
                    for key in item:
                        if self._detect_field_type(key, item[key]) == "time_series":
                            point["x"] = item[key]
                            break
                    else:
                        point["x"] = len(chart_data)

                # Try to find y value
                if y_field in item:
                    point["y"] = item[y_field]
                else:
                    # Look for numerical field
                    for key in item:
                        if self._detect_field_type(key, item[key]) == "numerical":
                            point["y"] = item[key]
                            break

                if "y" in point:
                    chart_data.append(point)

            return {
                "type": "line",
                "data": chart_data,
                "xAxis": x_field,
                "yAxis": y_field,
            }
        elif isinstance(data, list) and all(
            isinstance(item, (int, float)) for item in data
        ):
            # Simple numerical array
            return {
                "type": "line",
                "data": [{"x": i, "y": val} for i, val in enumerate(data)],
                "xAxis": "index",
                "yAxis": "value",
            }

        return {"type": "line", "data": []}

    def _transform_for_bar(self, data: Any, options: Dict) -> Dict[str, Any]:
        """Transform data for bar chart"""
        category_field = options.get("category_field")
        value_field = options.get("value_field")

        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            chart_data = []

            for item in data:
                bar = {}

                # Find category
                if category_field and category_field in item:
                    bar["category"] = str(item[category_field])
                else:
                    # Look for categorical field
                    for key in item:
                        if self._detect_field_type(key, item[key]) == "categorical":
                            bar["category"] = str(item[key])
                            break
                    else:
                        bar["category"] = f"Item {len(chart_data) + 1}"

                # Find value
                if value_field and value_field in item:
                    bar["value"] = item[value_field]
                else:
                    # Look for numerical field
                    for key in item:
                        if self._detect_field_type(key, item[key]) == "numerical":
                            bar["value"] = item[key]
                            break

                if "value" in bar:
                    chart_data.append(bar)

            return {
                "type": "bar",
                "data": chart_data,
                "categoryAxis": category_field or "category",
                "valueAxis": value_field or "value",
            }

        return {"type": "bar", "data": []}

    def _transform_for_pie(self, data: Any, options: Dict) -> Dict[str, Any]:
        """Transform data for pie chart"""
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            chart_data = []

            for item in data:
                slice_data = {}

                # Find name/category
                for key in item:
                    if self._detect_field_type(key, item[key]) == "categorical":
                        slice_data["name"] = str(item[key])
                        break
                else:
                    slice_data["name"] = f"Slice {len(chart_data) + 1}"

                # Find value
                for key in item:
                    if self._detect_field_type(key, item[key]) == "numerical":
                        slice_data["value"] = item[key]
                        break

                if "value" in slice_data:
                    chart_data.append(slice_data)

            return {"type": "pie", "data": chart_data}
        elif isinstance(data, dict):
            # Convert dict to pie slices
            chart_data = []
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    chart_data.append({"name": key, "value": value})

            return {"type": "pie", "data": chart_data}

        return {"type": "pie", "data": []}

    def _transform_for_scatter(self, data: Any, options: Dict) -> Dict[str, Any]:
        """Transform data for scatter plot"""
        x_field = options.get("x_field")
        y_field = options.get("y_field")

        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            chart_data = []

            # Find numerical fields
            numerical_fields = []
            if data:
                for key in data[0]:
                    if self._detect_field_type(key, data[0][key]) == "numerical":
                        numerical_fields.append(key)

            if len(numerical_fields) >= 2:
                x_field = x_field or numerical_fields[0]
                y_field = y_field or numerical_fields[1]

                for item in data:
                    if x_field in item and y_field in item:
                        chart_data.append({"x": item[x_field], "y": item[y_field]})

            return {
                "type": "scatter",
                "data": chart_data,
                "xAxis": x_field,
                "yAxis": y_field,
            }

        return {"type": "scatter", "data": []}

    def _transform_for_radar(self, data: Any, options: Dict) -> Dict[str, Any]:
        """Transform data for radar chart"""
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # Find numerical fields
            numerical_fields = []
            if data:
                for key in data[0]:
                    if self._detect_field_type(key, data[0][key]) == "numerical":
                        numerical_fields.append(key)

            if numerical_fields:
                chart_data = []
                for item in data:
                    series = []
                    for field in numerical_fields:
                        series.append({"axis": field, "value": item.get(field, 0)})

                    # Find a name for the series
                    name = None
                    for key in item:
                        if self._detect_field_type(key, item[key]) == "categorical":
                            name = str(item[key])
                            break

                    chart_data.append(
                        {
                            "name": name or f"Series {len(chart_data) + 1}",
                            "data": series,
                        }
                    )

                return {"type": "radar", "data": chart_data, "axes": numerical_fields}
        elif isinstance(data, dict):
            # Single object radar
            series = []
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    series.append({"axis": key, "value": value})

            return {
                "type": "radar",
                "data": [{"name": "Values", "data": series}],
                "axes": [s["axis"] for s in series],
            }

        return {"type": "radar", "data": []}

    def _transform_for_area(self, data: Any, options: Dict) -> Dict[str, Any]:
        """Transform data for area chart (similar to line)"""
        result = self._transform_for_line(data, options)
        result["type"] = "area"
        return result

    def _transform_for_table(self, data: Any, options: Dict) -> Dict[str, Any]:
        """Transform data for table display"""
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # Extract columns
            columns = set()
            for item in data:
                columns.update(item.keys())

            return {"type": "table", "columns": list(columns), "rows": data}
        elif isinstance(data, dict):
            # Convert dict to table
            return {
                "type": "table",
                "columns": ["Key", "Value"],
                "rows": [{"Key": k, "Value": v} for k, v in data.items()],
            }
        elif isinstance(data, list):
            # Simple list
            return {
                "type": "table",
                "columns": ["Index", "Value"],
                "rows": [{"Index": i, "Value": v} for i, v in enumerate(data)],
            }

        return {"type": "table", "columns": ["Value"], "rows": [{"Value": data}]}

    def process_natural_language_query(self, data: Any, query: str) -> Dict[str, Any]:
        """
        Process natural language queries for data transformation
        Examples: "Group by category", "Sum amounts", "Average prices"
        """
        query_lower = query.lower()
        result = {"query": query, "success": False}

        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            result["error"] = "Data must be an array of objects for queries"
            return result

        # Group by operations
        if "group by" in query_lower:
            field = self._extract_field_from_query(query_lower, "group by")
            if field:
                grouped = defaultdict(list)
                for item in data:
                    if field in item:
                        grouped[item[field]].append(item)

                result["data"] = dict(grouped)
                result["success"] = True
                result["operation"] = f"Grouped by {field}"

        # Sum operations
        elif "sum" in query_lower:
            field = self._extract_field_from_query(query_lower, "sum")
            if field:
                total = sum(
                    item.get(field, 0)
                    for item in data
                    if isinstance(item.get(field), (int, float))
                )
                result["data"] = {"sum": total, "field": field}
                result["success"] = True
                result["operation"] = f"Sum of {field}"

        # Average operations
        elif "average" in query_lower or "avg" in query_lower or "mean" in query_lower:
            field = self._extract_field_from_query(query_lower, "average|avg|mean")
            if field:
                values = [
                    item.get(field, 0)
                    for item in data
                    if isinstance(item.get(field), (int, float))
                ]
                if values:
                    avg = statistics.mean(values)
                    result["data"] = {
                        "average": avg,
                        "field": field,
                        "count": len(values),
                    }
                    result["success"] = True
                    result["operation"] = f"Average of {field}"

        # Count operations
        elif "count" in query_lower:
            if "by" in query_lower:
                field = self._extract_field_from_query(query_lower, "count.*?by")
                if field:
                    counts = Counter(item.get(field) for item in data if field in item)
                    result["data"] = dict(counts)
                    result["success"] = True
                    result["operation"] = f"Count by {field}"
            else:
                result["data"] = {"count": len(data)}
                result["success"] = True
                result["operation"] = "Total count"

        # Filter operations
        elif "filter" in query_lower or "where" in query_lower:
            # Simple contains filter
            parts = re.split(r"filter|where", query_lower)
            if len(parts) > 1:
                condition = parts[1].strip()
                # Extract field and value
                match = re.search(r"(\w+)\s*(=|>|<|>=|<=|contains)\s*(.+)", condition)
                if match:
                    field, operator, value = match.groups()
                    value = value.strip().strip("\"'")

                    filtered = []
                    for item in data:
                        if field in item:
                            item_value = item[field]
                            if operator == "=" and str(item_value) == value:
                                filtered.append(item)
                            elif operator == "contains" and value in str(item_value):
                                filtered.append(item)
                            elif operator in [">", "<", ">=", "<="]:
                                try:
                                    if eval(f"{item_value} {operator} {float(value)}"):
                                        filtered.append(item)
                                except Exception:
                                    pass

                    result["data"] = filtered
                    result["success"] = True
                    result["operation"] = f"Filtered where {field} {operator} {value}"

        # Sort operations
        elif "sort" in query_lower or "order" in query_lower:
            field = self._extract_field_from_query(query_lower, "sort|order")
            if field:
                reverse = "desc" in query_lower
                sorted_data = sorted(
                    data, key=lambda x: x.get(field, ""), reverse=reverse
                )
                result["data"] = sorted_data
                result["success"] = True
                result[
                    "operation"
                ] = f"Sorted by {field} {'descending' if reverse else 'ascending'}"

        # Top N operations
        elif "top" in query_lower:
            match = re.search(r"top\s*(\d+)", query_lower)
            if match:
                n = int(match.group(1))
                # Check if there's a field to sort by
                field_match = re.search(r"by\s+(\w+)", query_lower)
                if field_match:
                    field = field_match.group(1)
                    sorted_data = sorted(
                        data, key=lambda x: x.get(field, 0), reverse=True
                    )
                    result["data"] = sorted_data[:n]
                    result["operation"] = f"Top {n} by {field}"
                else:
                    result["data"] = data[:n]
                    result["operation"] = f"First {n} items"
                result["success"] = True

        return result

    def _extract_field_from_query(self, query: str, after_word: str) -> Optional[str]:
        """Extract field name from natural language query"""
        pattern = f"{after_word}\\s+(\\w+)"
        match = re.search(pattern, query)
        if match:
            return match.group(1)
        return None

    def get_insights(self, data: Any) -> List[str]:
        """
        Generate insights about the data
        """
        insights = []

        if isinstance(data, list):
            insights.append(f"Dataset contains {len(data)} items")

            if all(isinstance(item, dict) for item in data):
                # Find numerical fields
                numerical_fields = []
                if data:
                    for key in data[0]:
                        if self._detect_field_type(key, data[0][key]) == "numerical":
                            numerical_fields.append(key)

                for field in numerical_fields:
                    values = [
                        item.get(field, 0)
                        for item in data
                        if isinstance(item.get(field), (int, float))
                    ]
                    if values:
                        insights.append(
                            f"{field}: min={min(values):.2f}, max={max(values):.2f}, avg={statistics.mean(values):.2f}"
                        )

                # Find categorical fields
                categorical_fields = []
                if data:
                    for key in data[0]:
                        if self._detect_field_type(key, data[0][key]) == "categorical":
                            categorical_fields.append(key)

                for field in categorical_fields:
                    unique_values = set(
                        item.get(field) for item in data if field in item
                    )
                    insights.append(f"{field}: {len(unique_values)} unique values")

        elif isinstance(data, dict):
            insights.append(f"Object with {len(data)} properties")
            numerical_count = sum(
                1 for v in data.values() if isinstance(v, (int, float))
            )
            if numerical_count:
                insights.append(f"Contains {numerical_count} numerical values")

        return insights
