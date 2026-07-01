const API = "/api";

let sessionId = localStorage.getItem("ra_session") || "";

const messagesEl = document.getElementById("messages");
const composer = document.getElementById("composer");
const questionInput = document.getElementById("questionInput");
const fileInput = document.getElementById("fileInput");
const uploadZone = document.getElementById("uploadZone");
const sourceList = document.getElementById("sourceList");
const statLine = document.getElementById("statLine");
const clearBtn = document.getElementById("clearBtn");
const themeBtn = document.getElementById("themeBtn");
const keywordInput = document.getElementById("keywordInput");
const keywordBtn = document.getElementById("keywordBtn");
const keywordResults = document.getElementById("keywordResults");
const micBtn = document.getElementById("micBtn");

// ----------------------------------------------------------------- //
// Theme toggle (Feature 3)
// ----------------------------------------------------------------- //
function initTheme() {
  const saved = localStorage.getItem("ra_theme") || "dark";
  if (saved === "light") document.documentElement.setAttribute("data-theme", "light");
}
themeBtn.addEventListener("click", () => {
  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  if (isLight) {
    document.documentElement.removeAttribute("data-theme");
    localStorage.setItem("ra_theme", "dark");
  } else {
    document.documentElement.setAttribute("data-theme", "light");
    localStorage.setItem("ra_theme", "light");
  }
});
initTheme();

// ----------------------------------------------------------------- //
// Upload
// ----------------------------------------------------------------- //
//uploadZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) uploadFiles(fileInput.files);
});

["dragover", "dragleave", "drop"].forEach(evt => {
  uploadZone.addEventListener(evt, (e) => e.preventDefault());
});
uploadZone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files);
});

async function uploadFiles(fileList) {
  const formData = new FormData();
  for (const f of fileList) formData.append("files", f);

  statLine.textContent = "Uploading & indexing...";
  try {
    const res = await fetch(`${API}/upload`, { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    refreshSources();
  } catch (err) {
    statLine.textContent = err.message;
  }
}

async function refreshSources() {
  const res = await fetch(`${API}/sources`);
  const data = await res.json();
  sourceList.innerHTML = "";
  data.sources.forEach(src => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${src}</span>`;
    sourceList.appendChild(li);
  });
  statLine.textContent = `${data.total_chunks} chunks indexed across ${data.sources.length} document(s)`;
}
refreshSources();

// ----------------------------------------------------------------- //
// Chat
// ----------------------------------------------------------------- //
composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  addMessage("user", question);
  questionInput.value = "";

  const typingId = addTyping();

  const formData = new FormData();
  formData.append("question", question);
  formData.append("session_id", sessionId);

  try {
    const res = await fetch(`${API}/ask`, { method: "POST", body: formData });
    const data = await res.json();
    sessionId = data.session_id;
    localStorage.setItem("ra_session", sessionId);

    removeTyping(typingId);
    addMessage("assistant", data.answer, data.citations, question);
  } catch (err) {
    removeTyping(typingId);
    addMessage("assistant", "Something went wrong reaching the server.");
  }
});

function addMessage(role, text, citations = [], question = "") {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);

  if (role === "assistant" && citations && citations.length) {
    const citeWrap = document.createElement("div");
    citeWrap.className = "citations";
    citations.forEach(c => {
      const pill = document.createElement("span");
      pill.className = "citation-pill";
      pill.textContent = `${c.source} · p.${c.page}`;
      citeWrap.appendChild(pill);
    });
    bubble.appendChild(citeWrap);
  }

  if (role === "assistant" && question) {
    const actions = document.createElement("div");
    actions.className = "bubble-actions";
    const dlBtn = document.createElement("button");
    dlBtn.textContent = "Download PDF";
    dlBtn.onclick = () => downloadAnswer(question, text);
    actions.appendChild(dlBtn);
    bubble.appendChild(actions);
  }

  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addTyping() {
  const id = `typing-${Date.now()}`;
  const wrap = document.createElement("div");
  wrap.className = "msg assistant";
  wrap.id = id;
  wrap.innerHTML = `<div class="bubble typing-dots"><span></span><span></span><span></span></div>`;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ----------------------------------------------------------------- //
// Download answer as PDF (Feature 5)
// ----------------------------------------------------------------- //
async function downloadAnswer(question, answer) {
  const formData = new FormData();
  formData.append("question", question);
  formData.append("answer", answer);

  const res = await fetch(`${API}/download-answer`, { method: "POST", body: formData });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "answer.pdf";
  a.click();
  URL.revokeObjectURL(url);
}

// ----------------------------------------------------------------- //
// Keyword search (Feature 8)
// ----------------------------------------------------------------- //
keywordBtn.addEventListener("click", runKeywordSearch);
keywordInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runKeywordSearch();
});

async function runKeywordSearch() {
  const keyword = keywordInput.value.trim();
  if (!keyword) return;

  const formData = new FormData();
  formData.append("keyword", keyword);

  const res = await fetch(`${API}/search`, { method: "POST", body: formData });
  const data = await res.json();

  keywordResults.innerHTML = "";
  if (!data.results.length) {
    keywordResults.innerHTML = `<li>No matches found.</li>`;
    return;
  }
  data.results.forEach(r => {
    const li = document.createElement("li");
    li.innerHTML = `<b>${r.source}</b> · p.${r.page}<br>${r.text.slice(0, 110)}...`;
    keywordResults.appendChild(li);
  });
}

// ----------------------------------------------------------------- //
// Clear all data
// ----------------------------------------------------------------- //
clearBtn.addEventListener("click", async () => {
  if (!confirm("Clear all uploaded documents and chat history?")) return;
  await fetch(`${API}/clear`, { method: "POST" });
  sessionId = "";
  localStorage.removeItem("ra_session");
  sourceList.innerHTML = "";
  statLine.textContent = "0 chunks indexed";
  messagesEl.innerHTML = "";
  addMessage("assistant", "All data cleared. Upload new PDFs to get started.");
});

// ----------------------------------------------------------------- //
// Voice input (Feature 4)
// ----------------------------------------------------------------- //
let recognizing = false;
let recognition = null;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    questionInput.value = transcript;
  };
  recognition.onend = () => {
    recognizing = false;
    micBtn.classList.remove("listening");
  };
} else {
  micBtn.disabled = true;
  micBtn.title = "Voice input not supported in this browser";
}

micBtn.addEventListener("click", () => {
  if (!recognition) return;
  if (recognizing) {
    recognition.stop();
    return;
  }
  recognizing = true;
  micBtn.classList.add("listening");
  recognition.start();
});
