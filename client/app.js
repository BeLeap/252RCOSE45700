const serverUrlInput = document.querySelector("#serverUrl");
const topKInput = document.querySelector("#topK");
const questionInput = document.querySelector("#question");
const sendButton = document.querySelector("#sendButton");
const stopButton = document.querySelector("#stopButton");
const transcriptEl = document.querySelector("#transcript");
const citationsEl = document.querySelector("#citations");
const statusBadge = document.querySelector("#statusBadge");
const timerEl = document.querySelector("#timer");
const healthButton = document.querySelector("#healthButton");

let controller = null;
let startTime = null;
let timerHandle = null;
let messages = [];
let pendingAssistantIndex = null;

function setStatus(text, variant = "warn") {
  statusBadge.textContent = text;
  statusBadge.classList.remove("badge-ok", "badge-warn", "badge-error");
  statusBadge.classList.add(`badge-${variant}`);
}

function startTimer() {
  startTime = performance.now();
  timerHandle = requestAnimationFrame(updateTimer);
}

function stopTimer() {
  if (timerHandle) {
    cancelAnimationFrame(timerHandle);
    timerHandle = null;
  }
}

function updateTimer() {
  if (!startTime) return;
  const elapsed = (performance.now() - startTime) / 1000;
  timerEl.textContent = `${elapsed.toFixed(1)}s`;
  timerHandle = requestAnimationFrame(updateTimer);
}

function clearResponse() {
  citationsEl.innerHTML = "";
}

function renderTranscript() {
  transcriptEl.innerHTML = "";
  messages.forEach((msg) => {
    const div = document.createElement("div");
    div.className = `message ${msg.role}`;
    div.innerHTML = `
      <div class="role">${msg.role}</div>
      <div class="content">${msg.content}</div>
    `;
    transcriptEl.appendChild(div);
  });
}

function renderCitations(citations) {
  citationsEl.innerHTML = "";
  citations.forEach((c, idx) => {
    const div = document.createElement("div");
    div.className = "citation";
    div.innerHTML = `
      <div class="meta">
        <span>#${idx + 1}</span>
        <span>source: ${c.source ?? "unknown"}</span>
        <span>chunk: ${c.chunk_id ?? "-"}</span>
        <span>page: ${c.page ?? "-"}</span>
        <span>score: ${c.score?.toFixed ? c.score.toFixed(4) : c.score ?? "-"}</span>
      </div>
      <div class="preview">${c.preview ?? ""}</div>
    `;
    citationsEl.appendChild(div);
  });
}

function parseSseChunk(buffer, onEvent) {
  const events = buffer.split("\n\n");
  const remainder = events.pop();

  for (const raw of events) {
    let event = "message";
    let data = "";
    raw.split("\n").forEach((line) => {
      if (line.startsWith("event:")) {
        event = line.replace("event:", "").trim();
      } else if (line.startsWith("data:")) {
        data += line.replace("data:", "").trim();
      }
    });
    if (data) {
      try {
        onEvent(event, JSON.parse(data));
      } catch (err) {
        console.error("Failed to parse SSE data", err, data);
      }
    }
  }

  return remainder;
}

async function sendQuery() {
  const serverUrl = serverUrlInput.value.trim();
  const topK = parseInt(topKInput.value, 10) || 5;
  const query = questionInput.value.trim();
  if (!serverUrl || !query) return;

  const historySnapshot = [...messages];
  messages.push({ role: "user", content: query });
  pendingAssistantIndex = messages.push({ role: "assistant", content: "" }) - 1;
  renderTranscript();

  controller = new AbortController();
  sendButton.disabled = true;
  setStatus("Streaming...", "ok");
  clearResponse();
  startTimer();

  try {
    const response = await fetch(`${serverUrl}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK, history: historySnapshot }),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      buffer = parseSseChunk(buffer, (event, payload) => {
        if (event === "citations") {
          renderCitations(payload.citations || []);
        } else if (event === "token") {
          if (pendingAssistantIndex != null) {
            messages[pendingAssistantIndex].content += payload.token ?? "";
            renderTranscript();
          }
        } else if (event === "done") {
          setStatus("Done", "ok");
        }
      });
    }
  } catch (err) {
    if (controller.signal.aborted) {
      setStatus("Stopped", "warn");
    } else {
      setStatus("Error", "error");
      if (pendingAssistantIndex != null) {
        messages[pendingAssistantIndex].content = `Error: ${err.message}`;
        renderTranscript();
      }
    }
  } finally {
    sendButton.disabled = false;
    stopTimer();
    controller = null;
    pendingAssistantIndex = null;
  }
}

function stopQuery() {
  if (controller) {
    controller.abort();
  }
}

async function checkHealth() {
  const serverUrl = serverUrlInput.value.trim();
  if (!serverUrl) return;
  try {
    const res = await fetch(`${serverUrl}/health`);
    const json = await res.json();
    const status = json.status === "ok" ? "ok" : "warn";
    setStatus(`Health: ${json.status}`, status);
  } catch (err) {
    setStatus("Health error", "error");
    console.error(err);
  }
}

sendButton.addEventListener("click", sendQuery);
stopButton.addEventListener("click", stopQuery);
healthButton.addEventListener("click", checkHealth);
questionInput.addEventListener("keydown", (e) => {
  if (e.metaKey && e.key === "Enter") {
    sendQuery();
  }
});

setStatus("Idle", "warn");
