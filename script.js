let currentUser = null;

// Form visibility toggling
function showLogin() {
    document.getElementById('signup-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('signup-form').style.display = 'block';
}

// Auth functions
async function signUp() {
    const userData = {
        fullName: document.getElementById('fullName').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phoneNumber').value,
        username: document.getElementById('signupUsername').value,
        password: document.getElementById('signupPassword').value
    };

    try {
        const response = await fetch('http://localhost:5000/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(userData)
        });

        if (response.status === 201) {
            showLogin();
            alert('Registration successful! Please login');
        } else {
            const errorData = await response.json();
            alert(`Registration failed: ${errorData.message}`);
        }
    } catch (error) {
        alert('Error connecting to server');
    }
}

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch('http://localhost:5000/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        if (response.ok) {
            document.getElementById('auth-forms').style.display = 'none';
            document.getElementById('todo-app').style.display = 'block';
            await loadTodos();
        } else {
            const errorData = await response.json();
            alert(`Login failed: ${errorData.message}`);
        }
    } catch (error) {
        alert('Error connecting to server');
    }
}

// Todo functions
async function loadTodos() {
    try {
        const response = await fetch('http://localhost:5000/todos', {
            credentials: 'include'
        });
        const todos = await response.json();
        
        const todoList = document.getElementById('todo-list');
        todoList.innerHTML = '';
        
        todos.forEach(todo => {
            const li = document.createElement('li');
            li.className = `todo-item ${todo.status === 'completed' ? 'completed' : ''}`;
            li.innerHTML = `
                <span>${todo.task}</span>
                <div>
                    <button onclick="toggleTodo(${todo.id})">Toggle</button>
                    <button onclick="deleteTodo(${todo.id})">Delete</button>
                </div>
            `;
            todoList.appendChild(li);
        });
    } catch (error) {
        alert('Error loading todos');
    }
}

async function addTodo() {
    const taskInput = document.getElementById('new-todo');
    if (!taskInput.value.trim()) return;

    try {
        const response = await fetch('http://localhost:5000/todos', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ task: taskInput.value }),
            credentials: 'include'
        });
        
        if (response.status === 201) {
            taskInput.value = '';
            await loadTodos();
        }
    } catch (error) {
        alert('Error adding todo');
    }
}

async function toggleTodo(todoId) {
    try {
        const todoItem = document.querySelector(`[onclick="toggleTodo(${todoId})"]`).parentElement.parentElement;
        const newStatus = todoItem.classList.contains('completed') ? 'pending' : 'completed';
        
        await fetch(`http://localhost:5000/todos/${todoId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                status: newStatus,
                task: todoItem.querySelector('span').textContent
            }),
            credentials: 'include'
        });
        
        await loadTodos();
    } catch (error) {
        alert('Error updating todo');
    }
}

async function deleteTodo(todoId) {
    try {
        await fetch(`http://localhost:5000/todos/${todoId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        await loadTodos();
    } catch (error) {
        alert('Error deleting todo');
    }
}