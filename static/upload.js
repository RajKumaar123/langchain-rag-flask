async function fetchIndexed() {
  const res = await fetch('/api/indexed');
  const data = await res.json();
  const list = document.getElementById('indexedList');
  list.innerHTML = '';

  if (!data.documents || data.documents.length === 0) {
    list.innerHTML = '<em>No documents indexed yet.</em>';
    return;
  }

  data.documents.forEach(f => {
    const div = document.createElement('div');
    // show file name + chunks info (if available)
    div.textContent = `${f.file || f} ${f.chunks ? "(" + f.chunks + " chunks)" : ""}`;
    list.appendChild(div);
  });
}

async function uploadFiles() {
  const input = document.getElementById('fileInput');
  const status = document.getElementById('uploadStatus');
  if (!input.files.length) {
    status.textContent = "⚠ Please select files first.";
    return;
  }

  const formData = new FormData();
  for (let f of input.files) formData.append('files', f);

  status.textContent = "⏳ Uploading...";
  const res = await fetch('/api/upload', { method: 'POST', body: formData });
  const data = await res.json();

  // show upload results
  status.textContent = JSON.stringify(data.results, null, 2);

  // refresh document list
  fetchIndexed();
}

document.getElementById('uploadBtn')?.addEventListener('click', uploadFiles);

// load indexed docs on page load
fetchIndexed();
