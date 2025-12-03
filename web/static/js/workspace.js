function loadHistory(){
  const list = document.getElementById('history');
  list.innerHTML = '';
  const items = JSON.parse(localStorage.getItem('queries') || '[]');
  items.forEach((q,i)=>{
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = q;
    a.onclick = () => { document.getElementById('query').value = q; return false; };
    li.appendChild(a);
    list.appendChild(li);
  });
}

async function runQuery() {
  const q = document.getElementById('query').value;
  const resultElem = document.getElementById('result');
  try {
    const resp = await fetch('/api/rag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    if (!resp.ok) {
      let errorMsg = `Error: ${resp.status} ${resp.statusText}`;
      try {
        const errorJson = await resp.json();
        if (errorJson && errorJson.error) {
          errorMsg += ` - ${errorJson.error}`;
        }
      } catch (e) {
        // ignore JSON parse errors
      }
      resultElem.textContent = errorMsg;
      return;
    }
    const json = await resp.json();
    resultElem.textContent = json.answer || JSON.stringify(json);
  } catch (err) {
    resultElem.textContent = `Network error: ${err.message}`;
  }
}

function saveQuery(){
  const q = document.getElementById('query').value;
  const items = JSON.parse(localStorage.getItem('queries') || '[]');
  items.push(q);
  localStorage.setItem('queries', JSON.stringify(items));
  loadHistory();
}

loadHistory();
