const AUTH_API = 'http://localhost:5000/api/auth';
const TODO_API = 'http://localhost:5000/api/todos';

const signupForm = document.getElementById('signup-form');
const loginForm = document.getElementById('login-form');
const authForms = document.getElementById('auth-forms');
const todoApp = document.getElementById('todo-app');
const todoList = document.getElementById('todo-list');
const newTodoInput = document.getElementById('new-todo');
const dueDateInput = document.getElementById('due-date');
const dueTimeInput = document.getElementById('due-time');

// Initialize todos array from localStorage or empty array
let todos = JSON.parse(localStorage.getItem('todos')) || [];

function saveTodos() {
    localStorage.setItem('todos', JSON.stringify(todos));
}

function showLogin() {
    signupForm.style.display = 'none';
    loginForm.style.display = 'block';
}

function showRegister() {
    loginForm.style.display = 'none';
    signupForm.style.display = 'block';
}

async function signUp() {
    const payload = {
        fullName: document.getElementById('fullName').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phoneNumber').value,
        username: document.getElementById('signupUsername').value,
        password: document.getElementById('signupPassword').value,
    };

    try {
        const res = await fetch(`${AUTH_API}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        alert(data.message);
        if (res.status === 201) showLogin();
    } catch (error) {
        console.error('Signup error:', error);
        // If backend is not available, proceed with local storage
        alert('Signup successful (offline mode)');
        showLogin();
    }
}

async function login() {
    const payload = {
        username: document.getElementById('loginUsername').value,
        password: document.getElementById('loginPassword').value,
    };

    try {
        const res = await fetch(`${AUTH_API}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            authForms.style.display = 'none';
            todoApp.style.display = 'block';
            loadTodos();
        } else {
            alert(`Login failed: ${data.message}`);
        }
    } catch (error) {
        console.error('Login error:', error);
        // If backend is not available, proceed with local storage
        authForms.style.display = 'none';
        todoApp.style.display = 'block';
        loadTodos();
    }
}

async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        authForms.style.display = 'block';
        todoApp.style.display = 'none';
        todoList.innerHTML = '';
        showLogin();
    }
}

async function loadTodos() {
    try {
        const res = await fetch(TODO_API + '/', { 
            credentials: 'include' 
        });
        if (res.status === 401) {
            // Use local storage if not authenticated
            renderTodos();
            return;
        }
        const todosFromServer = await res.json();
        todos = todosFromServer;
        renderTodos();
    } catch (error) {
        console.error('Load todos error:', error);
        // Use local storage if backend is not available
        renderTodos();
    }
}

function renderTodos() {
    if (!todos.length) {
        todoList.innerHTML = '<li class="no-todos">No todos yet</li>';
        return;
    }
    todoList.innerHTML = todos.map((t, index) => `
        <li class="todo-item ${t.status === 'completed' ? 'completed' : ''}" data-id="${t.id || index}">
            <div class="todo-content">
                <h4>${t.task}</h4>
                <small>${t.date || 'No date'} • ${t.time || 'No time'}</small>
            </div>
            <div class="todo-actions">
                <i class="fas fa-check" title="Complete"></i>
                <i class="fas fa-pen-to-square" title="Edit"></i>
                <i class="fas fa-trash" title="Delete"></i>
            </div>
        </li>
    `).join('');
}

async function addTodo() {
    const task = newTodoInput.value.trim();
    const date = dueDateInput.value;
    const time = dueTimeInput.value;

    if (!task) {
        alert('Please enter a todo task!');
        return;
    }

    const newTodo = {
        id: Date.now(), // Use timestamp as ID for local storage
        task,
        date,
        time,
        status: 'pending'
    };

    try {
        const res = await fetch(TODO_API + '/', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newTodo)
        });

        if (res.status === 201) {
            const data = await res.json();
            todos.unshift(data); // Add to beginning of array
        }
    } catch (error) {
        console.error('Add todo error:', error);
        // If backend fails, add to local storage
        todos.unshift(newTodo);
    }

    // Clear inputs and update UI
    newTodoInput.value = '';
    dueDateInput.value = '';
    dueTimeInput.value = '';
    saveTodos();
    renderTodos();
    newTodoInput.focus();
}

todoList.addEventListener('click', async e => {
    const li = e.target.closest('li');
    if (!li) return;
    const id = li.dataset.id;
    const task = li.querySelector('h4').textContent;

    if (e.target.classList.contains('fa-check')) {
        const newStatus = li.classList.contains('completed') ? 'pending' : 'completed';
        try {
            await fetch(`${TODO_API}/${id}`, {
                method: 'PUT',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task, status: newStatus })
            });
        } catch (error) {
            console.error('Update todo error:', error);
        }
        // Update local storage regardless of backend status
        const todoIndex = todos.findIndex(t => (t.id || t.id === 0) ? t.id.toString() === id : false);
        if (todoIndex !== -1) {
            todos[todoIndex].status = newStatus;
            saveTodos();
        }
        renderTodos();
    }

    if (e.target.classList.contains('fa-pen-to-square')) {
        const newTask = prompt('Edit your todo:', task);
        if (newTask && newTask.trim() !== '') {
            try {
                await fetch(`${TODO_API}/${id}`, {
                    method: 'PUT',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        task: newTask.trim(), 
                        status: li.classList.contains('completed') ? 'completed' : 'pending' 
                    })
                });
            } catch (error) {
                console.error('Edit todo error:', error);
            }
            // Update local storage regardless of backend status
            const todoIndex = todos.findIndex(t => (t.id || t.id === 0) ? t.id.toString() === id : false);
            if (todoIndex !== -1) {
                todos[todoIndex].task = newTask.trim();
                saveTodos();
            }
            renderTodos();
        }
    }

    if (e.target.classList.contains('fa-trash')) {
        if (confirm(`Are you sure you want to delete "${task}"?`)) {
            try {
                await fetch(`${TODO_API}/${id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
            } catch (error) {
                console.error('Delete todo error:', error);
            }
            // Update local storage regardless of backend status
            todos = todos.filter(t => (t.id || t.id === 0) ? t.id.toString() !== id : false);
            saveTodos();
            renderTodos();
        }
    }
});

// Event Listeners
newTodoInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        addTodo();
    }
});

// Initialize the app
if (localStorage.getItem('isLoggedIn') === 'true') {
    authForms.style.display = 'none';
    todoApp.style.display = 'block';
    loadTodos();
}

window.showLogin = showLogin;
window.showRegister = showRegister;
window.signUp = signUp;
window.login = login;
window.addTodo = addTodo;
window.logout = logout;