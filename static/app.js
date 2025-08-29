function pushMsg(role, text, images=[]) {
  const chatBox = document.getElementById('chatBox');
  const el = document.createElement('div');
  el.className = `msg ${role}`;

  if (images && images.length) {
    images.forEach(url => {
      const img = document.createElement('img');
      img.src = url;
      img.style.maxWidth = "250px";
      img.style.display = "block";
      img.style.marginBottom = "6px";
      el.appendChild(img);
    });
  }

  const span = document.createElement('div');
  span.textContent = text;
  el.appendChild(span);

  chatBox.appendChild(el);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;
  pushMsg('user', text);
  input.value = '';

  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text })
  });
  const data = await res.json();
  pushMsg('bot', (data.answer || '').trim(), data.images || []);
}
