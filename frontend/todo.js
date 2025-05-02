document.addEventListener('DOMContentLoaded', () => {
    const addTodoBtn = document.getElementById('addTodoBtn');
    const todoInput = document.getElementById('todoInput');
    const dueDate = document.getElementById('dueDate');
    const dueTime = document.getElementById('dueTime');
    const todoList = document.getElementById('todoList');

    let todos = JSON.parse(localStorage.getItem('todos')) || [];

    const saveTodos = () => {
        localStorage.setItem('todos', JSON.stringify(todos));
    };

    const createTodoElement = (todo, index) => {
        const todoElement = document.createElement('div');
        todoElement.className = `todo-item ${todo.completed ? 'completed' : ''}`;
        todoElement.innerHTML = `
            <div class="todo-content">
                <h4>${todo.text}</h4>
                <small>${todo.date || 'No date'} • ${todo.time || 'No time'}</small>
            </div>
            <div class="todo-actions">
                <i class="fas fa-check ${todo.completed ? 'text-success' : ''}"></i>
                <i class="far fa-bookmark ${todo.bookmarked ? 'text-warning' : ''}"></i>
                <i class="far fa-pen-to-square"></i>
                <i class="fas fa-trash"></i>
            </div>
        `;

        const deleteBtn = todoElement.querySelector('.fa-trash');
        const completeBtn = todoElement.querySelector('.fa-check');
        const bookmarkBtn = todoElement.querySelector('.fa-bookmark');
        const editBtn = todoElement.querySelector('.fa-pen-to-square');

        deleteBtn.addEventListener('click', () => {
            const isConfirmed = confirm('Are you sure you want to delete this todo?');
            if (isConfirmed) {
            todos.splice(index, 1);
            saveTodos();
            renderTodos();
        } 
    });

        completeBtn.addEventListener('click', () => {
            todos[index].completed = !todos[index].completed;
            saveTodos();
            renderTodos();
        });

        bookmarkBtn.addEventListener('click', () => {
            todos[index].bookmarked = !todos[index].bookmarked;
            saveTodos();
            renderTodos();
        });

        editBtn.addEventListener('click', () => {
            const newText = prompt('Edit your todo:', todos[index].text);
            if (newText !== null && newText.trim() !== '') {
                todos[index].text = newText.trim();
                saveTodos();
                renderTodos();
            }
        });

        return todoElement;
    };

    const renderTodos = () => {
        todoList.innerHTML = '';
        if (todos.length === 0) {
            todoList.innerHTML = `<div class="text-center p-3 text-muted">No todos yet. Add one above!</div>`;
            return;
        }

        const sortedTodos = [...todos].sort((a, b) => {
            if (a.bookmarked && !b.bookmarked) return -1;
            if (!a.bookmarked && b.bookmarked) return 1;
            if (a.completed && !b.completed) return 1;
            if (!a.completed && b.completed) return -1;
            return new Date(b.createdAt) - new Date(a.createdAt);
        });

        sortedTodos.forEach((todo, index) => {
            const originalIndex = todos.indexOf(todo);
            todoList.appendChild(createTodoElement(todo, originalIndex));
        });
    };

    addTodoBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const text = todoInput.value.trim();
        const date = dueDate.value;
        const time = dueTime.value;

        if (!text) {
            alert('Please enter a todo text!');
            return;
        }

        todos.push({
            text,
            date,
            time,
            completed: false,
            bookmarked: false,
            createdAt: new Date().toISOString()
        });

        saveTodos();
        renderTodos();

        todoInput.value = '';
        dueDate.value = '';
        dueTime.value = '';
        todoInput.focus();
    });

    todoInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addTodoBtn.click();
        }
    });

    renderTodos();
});