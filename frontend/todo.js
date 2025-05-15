document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:5000/api/todos/';
    const addBtn = document.getElementById('addTodoBtn');
    const input = document.getElementById('todoInput');
    const dueDate = document.getElementById('dueDate');
    const dueTime = document.getElementById('dueTime');
    const todoList = document.getElementById('todoList');
    let todos = [];
  
    const showMessage = (msg, isError = true) => {
      const d = document.createElement('div');
      d.className = `message ${isError ? 'error' : 'success'}`;
      d.innerHTML = `
        <span>${isError ? '⚠️' : '✓'} ${msg}</span>
        <button class="close-btn">&times;</button>
      `;
      document.body.prepend(d);
      d.querySelector('.close-btn').onclick = () => d.remove();
      setTimeout(() => d.remove(), 4000);
    };
  
    const request = async (method, endpoint = '', data = null) => {
      const cfg = {
        method, 
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: data ? JSON.stringify(data) : null
      };
      const res = await fetch(API_URL + endpoint, cfg);
      const json = await res.json();
      if (!res.ok) throw new Error(json.message || 'Request failed');
      return json;
    };
  
    const fetchTodos = async () => {
      try {
        todos = await request('GET');
        render();
      } catch (e) {
        showMessage(e.message);
      }
    };
  
    const createEl = todo => {
      const el = document.createElement('div');
      el.className = `todo-item ${todo.status === 'completed' ? 'completed' : ''}`;
      el.dataset.id = todo.id;
      el.innerHTML = `
        <div class="todo-content">
          <h4>${todo.task}</h4>
          <small>${todo.date || 'No date'} • ${todo.time || 'No time'}</small>
        </div>
        <div class="todo-actions">
          <button class="complete-btn">${todo.status === 'completed' ? 'Undo' : 'Done'}</button>
          <button class="edit-btn">Edit</button>
          <button class="del-btn">✕</button>
        </div>
      `;
      el.querySelector('.del-btn').onclick = async () => {
        const ok = confirm(`Delete "${todo.task}"?`);
        if (!ok) return;
        const backup = [...todos];
        todos = todos.filter(t => t.id !== todo.id); 
        render();
        try { 
          await request('DELETE', `${todo.id}`); 
          showMessage('Deleted', false); 
        } catch { 
          todos = backup; 
          render(); 
        }
      };
      el.querySelector('.complete-btn').onclick = async () => {
        const upd = { ...todo, status: todo.status === 'completed' ? 'pending' : 'completed' };
        try { 
          await request('PUT', `${todo.id}`, upd); 
          fetchTodos(); 
        } catch(e) { 
          showMessage(e.message); 
        }
      };
      el.querySelector('.edit-btn').onclick = async () => {
        const newTask = prompt('Task:', todo.task);
        if (!newTask) return;
        const upd = { task: newTask, status: todo.status };
        try { 
          await request('PUT', `${todo.id}`, upd); 
          fetchTodos(); 
        } catch(e) { 
          showMessage(e.message); 
        }
      };
      return el;
    };
  
    function render() {
      todoList.innerHTML = '';
      if (!todos.length) {
        todoList.innerHTML = `<p class="empty">All caught up!</p>`;
        return;
      }
      todos.forEach(t => todoList.appendChild(createEl(t)));
    }
  
    addBtn.onclick = async e => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) { 
        showMessage('Enter a task'); 
        return; 
      }
      try {
        await request('POST', '', { 
          task: text, 
          date: dueDate.value, 
          time: dueTime.value 
        });
        input.value = ''; 
        dueDate.value = ''; 
        dueTime.value = '';
        fetchTodos();
      } catch (e) {
        showMessage(e.message);
      }
    };
  
    fetchTodos();
    input.onkeypress = e => { 
      if (e.key === 'Enter') addBtn.click(); 
    };
});