import mysql.connector
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys 

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'k21ritikasuvi06@', 
    'database': 'task_manager_db'
}

class Task:
    
    def __init__(self, id, description, status="Pending"): 
        self.id = id
        self.description = description
        self.status = status

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'status': self.status
        }

class TaskManager:
   
    def __init__(self):
        self.connection = None
        self.cursor = None
        self._connect()
        self._ensure_table_exists()

    def _connect(self):
        
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
            
                self.cursor = self.connection.cursor(dictionary=True)
                print(f"[INFO] Backend connected to MySQL: '{DB_CONFIG['database']}'")
        except mysql.connector.Error as err:
            print(f"[CRITICAL ERROR] Backend failed to connect to MySQL: {err}")
            sys.exit(1)

    def _ensure_table_exists(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(36) PRIMARY KEY,
            description VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending'
        );
        """
        try:
            self.cursor.execute(create_table_query)
            self.connection.commit()
            print("[INFO] 'tasks' table ensured to exist.")
        except mysql.connector.Error as err:
            print(f"[CRITICAL ERROR] Backend failed to create 'tasks' table: {err}")
            self._close_resources()
            sys.exit(1)

    def _close_resources(self):
        
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[INFO] Backend MySQL connection closed.")

    def get_all_tasks(self):
        
        select_query = "SELECT id, description, status FROM tasks ORDER BY description ASC"
        try:
            self.cursor.execute(select_query)
            tasks_data = self.cursor.fetchall()
           
            return [Task(**row).to_dict() for row in tasks_data]
        except mysql.connector.Error as err:
            print(f"[ERROR] Backend failed to get tasks: {err}")
            return None

    def add_task(self, description):
       
        task_id = str(uuid.uuid4())
        insert_query = "INSERT INTO tasks (id, description, status) VALUES (%s, %s, %s)"
        try:
            self.cursor.execute(insert_query, (task_id, description, "Pending"))
            self.connection.commit()
           
            return Task(task_id, description, "Pending").to_dict()
        except mysql.connector.Error as err:
            print(f"[ERROR] Backend failed to add task: {err}")
            self.connection.rollback()
            return None

    def update_task_db(self, task_id, description=None, status=None):
      
        update_parts = []
        params = []
        if description is not None:
            update_parts.append("description = %s")
            params.append(description)
        if status is not None:
            update_parts.append("status = %s")
            params.append(status)

        if not update_parts:
            return False 

        update_query = f"UPDATE tasks SET {', '.join(update_parts)} WHERE id = %s"
        params.append(task_id)

        try:
            self.cursor.execute(update_query, tuple(params))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"[ERROR] Backend failed to update task: {err}")
            self.connection.rollback()
            return False

    def delete_task_db(self, task_id):
       
        delete_query = "DELETE FROM tasks WHERE id = %s"
        try:
            self.cursor.execute(delete_query, (task_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"[ERROR] Backend failed to delete task: {err}")
            self.connection.rollback()
            return False


task_manager = TaskManager()


@app.route('/tasks', methods=['GET'])
def get_tasks():
   
    tasks = task_manager.get_all_tasks()
    if tasks is not None:
        return jsonify(tasks), 200
    return jsonify({"error": "Failed to retrieve tasks"}), 500

@app.route('/tasks', methods=['POST'])
def create_task():
    
    data = request.get_json()
    description = data.get('description')

    if not description or not description.strip():
        return jsonify({"error": "Description is required"}), 400

    new_task = task_manager.add_task(description.strip())
    if new_task:
        return jsonify(new_task), 201 
    return jsonify({"error": "Failed to create task"}), 500

@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
   
    data = request.get_json()
    description = data.get('description')
    status = data.get('status')

    if not description and not status:
        return jsonify({"error": "At least description or status must be provided for update"}), 400
    
   
    if description is not None:
        description = description.strip()
    if status is not None:
        status = status.strip()

    updated = task_manager.update_task_db(task_id, description=description, status=status)
    if updated:
        
        return jsonify({"message": "Task updated successfully"}), 200
    return jsonify({"error": "Task not found or failed to update"}), 404 


@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):

    deleted = task_manager.delete_task_db(task_id)
    if deleted:
        return jsonify({"message": "Task deleted successfully"}), 200
    return jsonify({"error": "Task not found or failed to delete"}), 404 

if __name__ == '__main__':
   
    app.run(debug=True)
