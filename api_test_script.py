import requests
import json

# プロジェクトを作成
project_data = {
    "name": "Test Project",
    "description": "テストプロジェクト"
}

try:
    response = requests.post("http://localhost:8000/projects", json=project_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 201:
        project = response.json()
        project_id = project["id"]
        print(f"\nプロジェクトが作成されました: {project_id}")
        
        # プロジェクト一覧を取得
        list_response = requests.get("http://localhost:8000/projects")
        print(f"\n一覧取得 Status Code: {list_response.status_code}")
        print(f"Projects: {json.dumps(list_response.json(), indent=2, ensure_ascii=False)}")
        
        # Todoを追加
        todo_data = {
            "title": "テストタスク",
            "description": "これはテストタスクです"
        }
        todo_response = requests.post(f"http://localhost:8000/projects/{project_id}/todos", json=todo_data)
        print(f"\nTodo追加 Status Code: {todo_response.status_code}")
        print(f"Todo Response: {json.dumps(todo_response.json(), indent=2, ensure_ascii=False)}")
        
except requests.exceptions.ConnectionError:
    print("サーバーに接続できませんでした。サーバーが起動しているか確認してください。")
except Exception as e:
    print(f"エラーが発生しました: {e}")
