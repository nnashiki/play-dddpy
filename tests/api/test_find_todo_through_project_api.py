"""Test cases for FindTodoThroughProject API endpoint compatibility using FastAPI TestClient."""

from uuid import uuid4

import pytest


class TestFindTodoThroughProjectAPI:
    """Test cases for GET /projects/{project_id}/todos/{todo_id} endpoint."""

    def test_find_todo_through_project_api_success(self, test_client):
        """Test successfully finding a todo through project API."""
        # 1. Create a project
        project_data = {
            "name": "API Test Project",
            "description": "Testing API compatibility"
        }
        
        create_response = test_client.post("/projects", json=project_data)
        assert create_response.status_code == 201
        project = create_response.json()
        project_id = project["id"]
        
        # 2. Add a todo to the project
        todo_data = {
            "title": "Test Todo for API",
            "description": "Testing todo retrieval"
        }
        
        add_todo_response = test_client.post(f"/projects/{project_id}/todos", json=todo_data)
        assert add_todo_response.status_code == 201
        todo = add_todo_response.json()
        todo_id = todo["id"]
        
        # 3. Find the todo through project (our target endpoint)
        find_response = test_client.get(f"/projects/{project_id}/todos/{todo_id}")
        
        # 4. Verify response
        assert find_response.status_code == 200
        found_todo = find_response.json()
        
        # Verify response structure
        expected_fields = ["id", "title", "description", "status", "dependencies", 
                          "created_at", "updated_at", "project_id"]
        for field in expected_fields:
            assert field in found_todo, f"Missing field: {field}"
        
        # Verify data matches
        assert found_todo["id"] == todo_id
        assert found_todo["title"] == todo_data["title"]
        assert found_todo["description"] == todo_data["description"]
        assert found_todo["status"] == "not_started"
        assert found_todo["project_id"] == project_id
        assert isinstance(found_todo["dependencies"], list)
        assert len(found_todo["dependencies"]) == 0

    def test_find_todo_through_project_todo_not_found(self, test_client):
        """Test API returns 404 when todo doesn't exist."""
        # 1. Create a project (using the same pattern as successful tests)
        project_data = {
            "name": "Test Project",
            "description": "Test"
        }
        create_response = test_client.post("/projects", json=project_data)
        assert create_response.status_code == 201
        project = create_response.json()
        project_id = project["id"]
        
        # 2. Try to find non-existent todo
        non_existent_todo_id = str(uuid4())
        find_response = test_client.get(f"/projects/{project_id}/todos/{non_existent_todo_id}")
        
        # 3. Verify 404 response
        assert find_response.status_code == 404
        error_response = find_response.json()
        assert "detail" in error_response

    def test_find_todo_through_project_project_not_found(self, test_client):
        """Test API returns 404 when project doesn't exist."""
        # 1. Try to find todo in non-existent project
        non_existent_project_id = str(uuid4())
        any_todo_id = str(uuid4())
        
        find_response = test_client.get(f"/projects/{non_existent_project_id}/todos/{any_todo_id}")
        
        # 2. Verify 404 response
        assert find_response.status_code == 404
        error_response = find_response.json()
        assert "detail" in error_response

    def test_find_todo_through_project_api_response_format_consistency(self, test_client):
        """Test that API response format is consistent with existing endpoints."""
        # 1. Create test data
        project_data = {"name": "Format Test Project", "description": "Testing format"}
        create_response = test_client.post("/projects", json=project_data)
        project = create_response.json()
        project_id = project["id"]
        
        todo_data = {"title": "Format Test Todo", "description": "Testing format"}
        add_todo_response = test_client.post(f"/projects/{project_id}/todos", json=todo_data)
        todo = add_todo_response.json()
        todo_id = todo["id"]
        
        # 2. Get todo through find endpoint (our target)
        find_response = test_client.get(f"/projects/{project_id}/todos/{todo_id}")
        found_todo = find_response.json()
        
        # 3. Compare with other todo endpoints for format consistency
        # Get todos list to compare format
        list_response = test_client.get(f"/projects/{project_id}/todos")
        assert list_response.status_code == 200
        todos_list = list_response.json()
        
        # Find our todo in the list
        list_todo = None
        for todo_in_list in todos_list:
            if todo_in_list["id"] == todo_id:
                list_todo = todo_in_list
                break
        
        assert list_todo is not None, "Todo not found in list"
        
        # 4. Verify format consistency between endpoints
        # Both should have the same fields
        assert set(found_todo.keys()) == set(list_todo.keys())
        
        # Both should have the same values for key fields
        assert found_todo["id"] == list_todo["id"]
        assert found_todo["title"] == list_todo["title"]
        assert found_todo["description"] == list_todo["description"]
        assert found_todo["status"] == list_todo["status"]
        assert found_todo["project_id"] == list_todo["project_id"]

    def test_find_todo_through_project_api_with_dependencies(self, test_client):
        """Test finding todo with dependencies works correctly."""
        # 1. Create project and multiple todos
        project_data = {"name": "Dependency Test Project"}
        create_response = test_client.post("/projects", json=project_data)
        project = create_response.json()
        project_id = project["id"]
        
        # Create dependency todo
        dep_todo_data = {"title": "Dependency Todo"}
        dep_response = test_client.post(f"/projects/{project_id}/todos", json=dep_todo_data)
        dep_todo = dep_response.json()
        dep_todo_id = dep_todo["id"]
        
        # Create main todo with dependency
        main_todo_data = {
            "title": "Main Todo",
            "dependencies": [dep_todo_id]
        }
        main_response = test_client.post(f"/projects/{project_id}/todos", json=main_todo_data)
        main_todo = main_response.json()
        main_todo_id = main_todo["id"]
        
        # 2. Find the main todo
        find_response = test_client.get(f"/projects/{project_id}/todos/{main_todo_id}")
        
        # 3. Verify dependencies are correctly returned
        assert find_response.status_code == 200
        found_todo = find_response.json()
        assert found_todo["dependencies"] == [dep_todo_id]

    def test_find_todo_through_project_api_error_handling(self, test_client):
        """Test API error handling for invalid input."""
        # Test invalid UUID format
        invalid_project_id = "invalid-uuid"
        invalid_todo_id = "invalid-uuid"
        
        find_response = test_client.get(f"/projects/{invalid_project_id}/todos/{invalid_todo_id}")
        
        # Should return 422 for validation error (invalid UUID format)
        assert find_response.status_code == 422
        error_response = find_response.json()
        assert "detail" in error_response
