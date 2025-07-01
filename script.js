console.log("script.js has loaded and is executing!");

const API_BASE_URL = 'http://127.0.0.1:5000'; 

const taskDescriptionInput = document.getElementById('taskDescription');
const createTaskBtn = document.getElementById('createTaskBtn');
const tasksContainer = document.getElementById('tasksContainer');
const noTasksMessage = document.getElementById('noTasksMessage');

const updateModalOverlay = document.getElementById('updateModalOverlay');
const closeUpdateModalBtn = document.getElementById('closeUpdateModalBtn');
const updateTaskIdInput = document.getElementById('updateTaskId');
const updateDescriptionInput = document.getElementById('updateDescription');
const updateStatusSelect = document.getElementById('updateStatus');
const submitUpdateBtn = document.getElementById('submitUpdateBtn');
const cancelUpdateBtn = document.getElementById('cancelUpdateBtn');

const messageBox = document.getElementById('messageBox');

function showMessage(message, type = 'info') {
    messageBox.textContent = message;
    messageBox.style.display = 'block';
    messageBox.className = 'rounded-lg p-4 mb-4 text-center';
    if (type === 'success') {
        messageBox.classList.add('msg-success');
    } else if (type === 'error') {
        messageBox.classList.add('msg-error');
    } else if (type === 'warn') {
        messageBox.classList.add('msg-warn');
    } else {
        messageBox.classList.add('msg-info');
    }
    
    messageBox.style.animation = 'none';
    void messageBox.offsetWidth;
    messageBox.style.animation = 'fadeInOut 3s forwards';
}

async function fetchTasks() {
    console.log("fetchTasks() function started.");
    noTasksMessage.textContent = "Fetching your tasks...";
    noTasksMessage.style.display = 'block';
    tasksContainer.innerHTML = '';

    try {
        console.log(`Attempting to fetch from: ${API_BASE_URL}/tasks`);
        const response = await fetch(`${API_BASE_URL}/tasks`);
        console.log("Fetch response received:", response);
        if (!response.ok) {
            const errorDetails = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(`HTTP error! Status: ${response.status}. Details: ${errorDetails.error}`);
        }
        const tasks = await response.json();

        if (tasks.length === 0) {
            noTasksMessage.textContent = "Your task list is sparkling clean! Add a new task above.";
            noTasksMessage.style.display = 'block';
            return;
        }
        noTasksMessage.style.display = 'none';

        tasks.forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.className = 'task-item';

            taskItem.innerHTML = `
                <div class="task-details">
                    <div class="task-id">ID: ${task.id.substring(0, 8)}</div>
                    <div class="task-description-display">${task.description}</div>
                    <div class="task-status-display">Status: <span class="font-semibold">${task.status}</span></div>
                </div>
                <div class="task-actions">
                    <button class="btn btn-update"
                        data-id="${task.id}"
                        data-description="${task.description}"
                        data-status="${task.status}">Edit</button>
                    <button class="btn btn-delete" data-id="${task.id}">Delete</button>
                </div>
            `;
            tasksContainer.appendChild(taskItem);
        });
        addEventListenersToButtons();
    } catch (error) {
        console.error('Error fetching tasks:', error);
        let errorMessage = "Failed to load tasks. Please ensure the backend server is running and accessible.";
        if (error.message.includes("HTTP error!")) {
            errorMessage = `Failed to load tasks: ${error.message}`;
        } else if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
             errorMessage = "Could not connect to the backend server. Is it running?";
        }
        noTasksMessage.textContent = errorMessage;
        showMessage(errorMessage, 'error');
    }
}

createTaskBtn.addEventListener('click', async () => {
    const description = taskDescriptionInput.value.trim();
    if (!description) {
        showMessage("Please enter a task description!", 'warn');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description: description })
        });

        if (response.ok) {
            const newTask = await response.json();
            showMessage(`Task "${newTask.description}" added successfully!`, 'success');
            taskDescriptionInput.value = '';
            fetchTasks();
        } else {
            const errorData = await response.json();
            showMessage(`Error adding task: ${errorData.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error creating task:', error);
        showMessage("Could not connect to the backend. Is the server running?", 'error');
    }
});

function setupUpdateForm(id, description, status) {
    updateTaskIdInput.value = id;
    updateDescriptionInput.value = description;
    updateStatusSelect.value = status;
    updateModalOverlay.classList.add('visible');
}

function hideUpdateModal() {
    updateModalOverlay.classList.remove('visible');
}

submitUpdateBtn.addEventListener('click', async () => {
    const id = updateTaskIdInput.value;
    const newDescription = updateDescriptionInput.value.trim();
    const newStatus = updateStatusSelect.value;

    if (!newDescription) {
        showMessage("Description cannot be empty for update!", 'warn');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description: newDescription, status: newStatus })
        });

        if (response.ok) {
            showMessage("Task updated successfully!", 'success');
            hideUpdateModal();
            fetchTasks();
        } else {
            const errorData = await response.json();
            showMessage(`Error updating task: ${errorData.error || response.statusText}`, 'error');
        }
    } catch (error) {
        console.error('Error updating task:', error);
        showMessage("Could not connect to backend to update task.", 'error');
    }
});

cancelUpdateBtn.addEventListener('click', () => {
    hideUpdateModal();
    showMessage("Task update cancelled.", 'info');
});

closeUpdateModalBtn.addEventListener('click', () => {
    hideUpdateModal();
    showMessage("Task update cancelled.", 'info');
});

updateModalOverlay.addEventListener('click', (event) => {
    if (event.target === updateModalOverlay) {
        hideUpdateModal();
        showMessage("Task update cancelled.", 'info');
    }
});

function addEventListenersToButtons() {
    document.querySelectorAll('.btn-update').forEach(button => {
        button.onclick = () => {
            setupUpdateForm(
                button.dataset.id,
                button.dataset.description,
                button.dataset.status
            );
        };
    });

    document.querySelectorAll('.btn-delete').forEach(button => {
        button.onclick = async () => {
            const taskId = button.dataset.id;
            const taskDescriptionElement = button.closest('.task-item').querySelector('.task-description-display');
            const taskDescription = taskDescriptionElement ? taskDescriptionElement.textContent : 'this task';

            if (confirm(`Are you sure you want to permanently delete "${taskDescription}" (ID: ${taskId.substring(0,8)})? This action cannot be undone.`)) {
                try {
                    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
                        method: 'DELETE'
                    });

                    if (response.ok) {
                        showMessage(`Task "${taskDescription}" deleted successfully!`, 'success');
                        fetchTasks();
                    } else {
                        const errorData = await response.json();
                        showMessage(`Error deleting task: ${errorData.error || response.statusText}`, 'error');
                    }
                } catch (error) {
                    console.error('Error deleting task:', error);
                    showMessage("Could not connect to backend to delete task.", 'error');
                }
            }
        };
    });
}

document.addEventListener('DOMContentLoaded', fetchTasks);

