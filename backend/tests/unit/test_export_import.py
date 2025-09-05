"""
Unit tests for Export/Import functionality
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
import yaml
from pathlib import Path
from datetime import datetime

from src.export_import import ExportManager, ImportManager


class TestExportManager:
    """Test ExportManager class"""
    
    @pytest.fixture
    def export_manager(self):
        """Create ExportManager instance"""
        return ExportManager()
    
    @pytest.fixture
    def sample_project_data(self):
        """Create sample project data for export"""
        return {
            "project": {
                "id": 1,
                "name": "Test Project",
                "description": "Test Description",
                "source_type": "directory",
                "source_path": "/test/path",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            "apis": [
                {
                    "id": 1,
                    "path": "/users",
                    "method": "GET",
                    "handler_name": "list_users",
                    "description": "List all users"
                },
                {
                    "id": 2,
                    "path": "/users/{id}",
                    "method": "GET",
                    "handler_name": "get_user",
                    "description": "Get user by ID"
                }
            ],
            "specs": {
                "openapi": "3.0.0",
                "info": {
                    "title": "Test API",
                    "version": "1.0.0"
                },
                "paths": {}
            },
            "tests": [
                {
                    "id": 1,
                    "test_name": "test_list_users",
                    "test_type": "pytest",
                    "test_code": "def test_list_users():\n    pass"
                }
            ]
        }
    
    def test_export_to_json(self, export_manager, sample_project_data):
        """Test exporting project data to JSON"""
        # Execute
        json_output = export_manager.export_to_json(sample_project_data)
        
        # Assert
        assert isinstance(json_output, str)
        parsed = json.loads(json_output)
        assert parsed["project"]["name"] == "Test Project"
        assert len(parsed["apis"]) == 2
    
    def test_export_to_yaml(self, export_manager, sample_project_data):
        """Test exporting project data to YAML"""
        # Execute
        yaml_output = export_manager.export_to_yaml(sample_project_data)
        
        # Assert
        assert isinstance(yaml_output, str)
        assert "Test Project" in yaml_output
        assert "list_users" in yaml_output
    
    def test_export_to_file_json(self, export_manager, sample_project_data):
        """Test exporting to JSON file"""
        with patch('builtins.open', mock_open()) as mock_file:
            # Execute
            export_manager.export_to_file(
                data=sample_project_data,
                filepath="export.json",
                format="json"
            )
            
            # Assert
            mock_file.assert_called_once_with("export.json", "w")
            handle = mock_file()
            handle.write.assert_called()
    
    def test_export_to_file_yaml(self, export_manager, sample_project_data):
        """Test exporting to YAML file"""
        with patch('builtins.open', mock_open()) as mock_file:
            # Execute
            export_manager.export_to_file(
                data=sample_project_data,
                filepath="export.yaml",
                format="yaml"
            )
            
            # Assert
            mock_file.assert_called_once_with("export.yaml", "w")
    
    def test_export_minimal_data(self, export_manager):
        """Test exporting minimal project data"""
        minimal_data = {
            "project": {"name": "Minimal"},
            "apis": []
        }
        
        # Execute
        json_output = export_manager.export_to_json(minimal_data)
        
        # Assert
        parsed = json.loads(json_output)
        assert parsed["project"]["name"] == "Minimal"
        assert parsed["apis"] == []
    
    @patch('src.export_import.DatabaseManager')
    def test_export_from_database(self, mock_db_class, export_manager):
        """Test exporting project from database"""
        # Setup
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "DB Project"
        mock_project.to_dict.return_value = {"id": 1, "name": "DB Project"}
        
        mock_db.get_project.return_value = mock_project
        mock_db.get_project_apis.return_value = []
        mock_db.get_project_specs.return_value = None
        mock_db.get_project_tests.return_value = []
        
        # Execute
        result = export_manager.export_from_database(project_id=1)
        
        # Assert
        assert result["project"]["name"] == "DB Project"
        assert result["apis"] == []
    
    def test_create_export_archive(self, export_manager, sample_project_data):
        """Test creating export archive with all data"""
        with patch('builtins.open', mock_open()):
            with patch('os.makedirs'):
                with patch('shutil.make_archive') as mock_archive:
                    # Execute
                    archive_path = export_manager.create_archive(
                        project_data=sample_project_data,
                        output_dir="/tmp/export"
                    )
                    
                    # Assert
                    mock_archive.assert_called_once()
                    assert "export" in str(archive_path)


class TestImportManager:
    """Test ImportManager class"""
    
    @pytest.fixture
    def import_manager(self):
        """Create ImportManager instance"""
        return ImportManager()
    
    @pytest.fixture
    def sample_json_data(self):
        """Sample JSON data for import"""
        return json.dumps({
            "project": {
                "name": "Imported Project",
                "description": "Imported Description"
            },
            "apis": [
                {
                    "path": "/test",
                    "method": "GET",
                    "handler_name": "test_handler"
                }
            ]
        })
    
    def test_import_from_json(self, import_manager, sample_json_data):
        """Test importing from JSON string"""
        # Execute
        result = import_manager.import_from_json(sample_json_data)
        
        # Assert
        assert result["project"]["name"] == "Imported Project"
        assert len(result["apis"]) == 1
        assert result["apis"][0]["path"] == "/test"
    
    def test_import_from_yaml(self, import_manager):
        """Test importing from YAML string"""
        yaml_data = """
        project:
          name: YAML Project
          description: From YAML
        apis:
          - path: /yaml
            method: POST
            handler_name: yaml_handler
        """
        
        # Execute
        result = import_manager.import_from_yaml(yaml_data)
        
        # Assert
        assert result["project"]["name"] == "YAML Project"
        assert result["apis"][0]["method"] == "POST"
    
    def test_import_from_file_json(self, import_manager):
        """Test importing from JSON file"""
        json_content = '{"project": {"name": "File Project"}}'
        
        with patch('builtins.open', mock_open(read_data=json_content)):
            # Execute
            result = import_manager.import_from_file("project.json")
            
            # Assert
            assert result["project"]["name"] == "File Project"
    
    def test_import_from_file_yaml(self, import_manager):
        """Test importing from YAML file"""
        yaml_content = "project:\n  name: YAML File Project"
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            # Execute
            result = import_manager.import_from_file("project.yaml")
            
            # Assert
            assert result["project"]["name"] == "YAML File Project"
    
    def test_validate_import_data(self, import_manager):
        """Test validating import data structure"""
        # Valid data
        valid_data = {
            "project": {"name": "Valid"},
            "apis": []
        }
        assert import_manager.validate_data(valid_data) == True
        
        # Invalid data - missing project
        invalid_data = {"apis": []}
        assert import_manager.validate_data(invalid_data) == False
        
        # Invalid data - missing name
        invalid_data2 = {"project": {}, "apis": []}
        assert import_manager.validate_data(invalid_data2) == False
    
    @patch('src.export_import.DatabaseManager')
    def test_import_to_database(self, mock_db_class, import_manager):
        """Test importing data to database"""
        # Setup
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.create_project.return_value = mock_project
        
        import_data = {
            "project": {"name": "Import Test"},
            "apis": [
                {"path": "/test", "method": "GET"}
            ]
        }
        
        # Execute
        result = import_manager.import_to_database(
            data=import_data,
            user_id=1
        )
        
        # Assert
        assert result["project_id"] == 1
        assert result["status"] == "success"
        mock_db.create_project.assert_called_once()
    
    def test_merge_projects(self, import_manager):
        """Test merging imported data with existing project"""
        existing = {
            "project": {"name": "Existing"},
            "apis": [{"path": "/old", "method": "GET"}]
        }
        
        new_data = {
            "project": {"description": "New Description"},
            "apis": [{"path": "/new", "method": "POST"}]
        }
        
        # Execute
        merged = import_manager.merge_projects(existing, new_data)
        
        # Assert
        assert merged["project"]["name"] == "Existing"
        assert merged["project"]["description"] == "New Description"
        assert len(merged["apis"]) == 2
    
    def test_import_with_transformation(self, import_manager):
        """Test importing with data transformation"""
        # Data in old format
        old_format = {
            "projectName": "Old Format",
            "endpoints": [
                {"route": "/old", "verb": "GET"}
            ]
        }
        
        # Transform function
        def transform(data):
            return {
                "project": {"name": data["projectName"]},
                "apis": [
                    {"path": e["route"], "method": e["verb"]}
                    for e in data.get("endpoints", [])
                ]
            }
        
        # Execute
        result = import_manager.import_with_transform(
            data=old_format,
            transform_fn=transform
        )
        
        # Assert
        assert result["project"]["name"] == "Old Format"
        assert result["apis"][0]["path"] == "/old"
    
    def test_import_archive(self, import_manager):
        """Test importing from archive file"""
        with patch('zipfile.ZipFile') as mock_zip:
            with patch('builtins.open', mock_open()):
                # Setup mock zip file
                mock_zip_instance = MagicMock()
                mock_zip.return_value.__enter__.return_value = mock_zip_instance
                mock_zip_instance.namelist.return_value = ["project.json"]
                mock_zip_instance.read.return_value = b'{"project": {"name": "Archived"}}'
                
                # Execute
                result = import_manager.import_from_archive("export.zip")
                
                # Assert
                assert result["project"]["name"] == "Archived"


class TestExportImportIntegration:
    """Test export/import integration scenarios"""
    
    def test_round_trip_json(self):
        """Test exporting and re-importing via JSON"""
        export_mgr = ExportManager()
        import_mgr = ImportManager()
        
        # Original data
        original = {
            "project": {"name": "Round Trip", "description": "Test"},
            "apis": [{"path": "/test", "method": "GET"}]
        }
        
        # Export to JSON
        json_str = export_mgr.export_to_json(original)
        
        # Import back
        imported = import_mgr.import_from_json(json_str)
        
        # Assert data integrity
        assert imported["project"]["name"] == original["project"]["name"]
        assert len(imported["apis"]) == len(original["apis"])
    
    def test_round_trip_yaml(self):
        """Test exporting and re-importing via YAML"""
        export_mgr = ExportManager()
        import_mgr = ImportManager()
        
        # Original data
        original = {
            "project": {"name": "YAML Round Trip"},
            "apis": []
        }
        
        # Export to YAML
        yaml_str = export_mgr.export_to_yaml(original)
        
        # Import back
        imported = import_mgr.import_from_yaml(yaml_str)
        
        # Assert
        assert imported["project"]["name"] == original["project"]["name"]
    
    def test_export_import_with_special_chars(self):
        """Test handling special characters in export/import"""
        export_mgr = ExportManager()
        import_mgr = ImportManager()
        
        # Data with special characters
        data = {
            "project": {"name": "Test & <Special> \"Chars\""},
            "apis": [{"path": "/api?param=value&other=true"}]
        }
        
        # Export and import
        json_str = export_mgr.export_to_json(data)
        imported = import_mgr.import_from_json(json_str)
        
        # Assert special chars preserved
        assert imported["project"]["name"] == data["project"]["name"]
        assert imported["apis"][0]["path"] == data["apis"][0]["path"]