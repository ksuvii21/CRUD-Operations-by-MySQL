import mysql.connector
import uuid

DB = {
    'host': 'localhost',
    'user': 'root',
    'password': 'k21ritikasuvi06@',
    'database': 'task_manager_db' 
}

class Task:
    def __init__(self, task_id, description, status="Pending"):
        self.id = task_id
        self.description = description
        self.status = status

    def __str__(self):
        return f"ID: {self.id} | Description: {self.description:<30} | Status: {self.status}"

class TaskManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self._connect()
        self._ensure_table_exists()

    def _connect(self):
        try:
            self.connection = mysql.connector.connect(**DB)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                print(f"Connected to MySQL database: {DB['database']}")
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            exit(1)

    def _close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed.")

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
            print("Ensured 'tasks' table exists.")
        except mysql.connector.Error as err:
            print(f"Error creating table: {err}")
            self._close()
            exit(1)

    def create_task(self):
        description = input("Enter task description: ")
        if not description.strip():
            print("Task description cannot be empty. Task not created.")
            return

        task_id = str(uuid.uuid4())
        insert_query = "INSERT INTO tasks (id, description, status) VALUES (%s, %s, %s)"
        try:
            self.cursor.execute(insert_query, (task_id, description, "Pending"))
            self.connection.commit()
            print(f"Task created successfully! (ID: {task_id[:8]})")
        except mysql.connector.Error as err:
            print(f"Error creating task: {err}")
            self.connection.rollback()

    def read_tasks(self):
        select_query = "SELECT id, description, status FROM tasks"
        try:
            self.cursor.execute(select_query)
            tasks_data = self.cursor.fetchall()

            if not tasks_data:
                print("No tasks available.")
                return

            print("\n--- Your Tasks ---")
            for row in tasks_data:
                task = Task(row[0], row[1], row[2])
                print(task)
            print("------------------")
        except mysql.connector.Error as err:
            print(f"Error reading tasks: {err}")

    def update_task(self):
        self.read_tasks()
        if not self._check_for_tasks():
            return

        task_id_prefix = input("Enter the *first 8 characters* of the ID of the task to update: ").strip()
        
        select_id_query = "SELECT id FROM tasks WHERE id LIKE %s"
        try:
            self.cursor.execute(select_id_query, (f"{task_id_prefix}%",))
            result = self.cursor.fetchone()
            if not result:
                print(f"Task with ID prefix '{task_id_prefix}' not found.")
                return
            full_task_id = result[0]
            
            select_single_task_query = "SELECT id, description, status FROM tasks WHERE id = %s"
            self.cursor.execute(select_single_task_query, (full_task_id,))
            current_task_data = self.cursor.fetchone()
            
            if current_task_data:
                current_task = Task(current_task_data[0], current_task_data[1], current_task_data[2])
                print(f"Found task: {current_task}")
                print("What would you like to update?")
                print("1. Description")
                print("2. Status")
                choice = input("Enter your choice (1 or 2): ")

                if choice == '1':
                    new_description = input("Enter new description: ")
                    if new_description.strip():
                        update_query = "UPDATE tasks SET description = %s WHERE id = %s"
                        self.cursor.execute(update_query, (new_description, full_task_id))
                        self.connection.commit()
                        print(f"Task ID {task_id_prefix} description updated successfully.")
                    else:
                        print("Description cannot be empty. Update cancelled.")
                elif choice == '2':
                    new_status = input("Enter new status (e.g., Pending, In Progress, Completed): ")
                    if new_status.strip():
                        update_query = "UPDATE tasks SET status = %s WHERE id = %s"
                        self.cursor.execute(update_query, (new_status, full_task_id))
                        self.connection.commit()
                        print(f"Task ID {task_id_prefix} status updated successfully.")
                    else:
                        print("Status cannot be empty. Update cancelled.")
                else:
                    print("Invalid choice for update. No changes made.")
            else:
                 print(f"Task with ID prefix '{task_id_prefix}' not found.")
        except mysql.connector.Error as err:
            print(f"Error updating task: {err}")
            self.connection.rollback()

    def delete_task(self):
        self.read_tasks()
        if not self._check_for_tasks():
            return

        task_id_prefix = input("Enter the *first 8 characters* of the ID of the task to delete: ").strip()
        
        select_id_query = "SELECT id FROM tasks WHERE id LIKE %s"
        try:
            self.cursor.execute(select_id_query, (f"{task_id_prefix}%",))
            result = self.cursor.fetchone()
            if not result:
                print(f"Task with ID prefix '{task_id_prefix}' not found.")
                return
            full_task_id = result[0]

            delete_query = "DELETE FROM tasks WHERE id = %s"
            self.cursor.execute(delete_query, (full_task_id,))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                print(f"Task with ID prefix '{task_id_prefix}' deleted successfully.")
            else:
                print(f"Task with ID prefix '{task_id_prefix}' not found (already deleted or incorrect ID).")
        except mysql.connector.Error as err:
            print(f"Error deleting task: {err}")
            self.connection.rollback()
            
    def _check_for_tasks(self):
        select_count_query = "SELECT COUNT(*) FROM tasks"
        try:
            self.cursor.execute(select_count_query)
            count = self.cursor.fetchone()[0]
            if count == 0:
                print("No tasks available to perform this operation.")
                return False
            return True
        except mysql.connector.Error as err:
            print(f"Error checking task count: {err}")
            return False

def main():
    manager = TaskManager()

    try:
        while True:
            print("\n--- Task Manager Menu (Using Python with MySQL) ---")
            print("1. Create Task")
            print("2. View Tasks")
            print("3. Update Task")
            print("4. Delete Task")
            print("5. Exit")
            choice = input("Enter your choice: ").strip()

            if choice == '1':
                manager.create_task()
            elif choice == '2':
                manager.read_tasks()
            elif choice == '3':
                manager.update_task()
            elif choice == '4':
                manager.delete_task()
            elif choice == '5':
                print("Exiting Task Manager. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
    finally:
        manager._close()

if __name__ == "__main__":
    main()
