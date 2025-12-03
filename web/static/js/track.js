function logEvent(name){
  fetch('/api/track', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({event:name, path:location.pathname})
  });
}

window.addEventListener('load', ()=>logEvent('page_load'));
