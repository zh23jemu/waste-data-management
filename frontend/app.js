const formatJson = (value) => JSON.stringify(value, null, 2);

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({ ok: false, message: '响应不是有效 JSON。' }));
  if (!response.ok || data.ok === false) throw new Error(data.message || `请求失败：${response.status}`);
  return data;
}

function bindUpload(formId, outputId, endpoint) {
  document.getElementById(formId).addEventListener('submit', async (event) => {
    event.preventDefault();
    const output = document.getElementById(outputId);
    output.textContent = '处理中...';
    try {
      const formData = new FormData(event.target);
      const data = await requestJson(endpoint, { method: 'POST', body: formData });
      output.textContent = formatJson(data.data);
      if (formId === 'recognizeForm') loadHistory();
    } catch (error) {
      output.textContent = error.message;
    }
  });
}

async function loadConfig() {
  try {
    const search = await requestJson('/api/search?q=');
    const chips = document.getElementById('hotKeywords');
    chips.innerHTML = search.hot_keywords.map(word => `<span class="chip" data-keyword="${word}">${word}</span>`).join('');
    chips.querySelectorAll('.chip').forEach(chip => chip.addEventListener('click', () => {
      document.getElementById('searchInput').value = chip.dataset.keyword;
      doSearch();
    }));
  } catch (error) {
    console.warn(error.message);
  }
}

async function doSearch() {
  const output = document.getElementById('searchResult');
  const q = document.getElementById('searchInput').value.trim();
  output.textContent = '检索中...';
  try {
    const data = await requestJson(`/api/search?q=${encodeURIComponent(q)}`);
    output.textContent = data.data.length ? formatJson(data.data) : '未找到匹配条目，可换一个关键词。';
  } catch (error) {
    output.textContent = error.message;
  }
}

async function doChat() {
  const output = document.getElementById('chatResult');
  output.textContent = '正在调用 DeepSeek...';
  try {
    const question = document.getElementById('chatQuestion').value;
    const data = await requestJson('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }),
    });
    output.textContent = data.data.answer;
  } catch (error) {
    output.textContent = error.message;
  }
}

async function loadHistory() {
  const box = document.getElementById('historyList');
  box.textContent = '加载中...';
  try {
    const data = await requestJson('/api/history?page=1&page_size=10');
    if (!data.data.items.length) { box.textContent = '暂无历史记录。'; return; }
    box.innerHTML = data.data.items.map(item => `
      <article class="history-card">
        <strong>#${item.id} ${item.predicted_class}</strong>
        <div>置信度：${(item.confidence * 100).toFixed(2)}%</div>
        <div>时间：${item.created_at}</div>
        <button data-delete-id="${item.id}" class="secondary">删除</button>
      </article>
    `).join('');
    box.querySelectorAll('[data-delete-id]').forEach(button => button.addEventListener('click', async () => {
      await requestJson(`/api/history/${button.dataset.deleteId}`, { method: 'DELETE' });
      loadHistory();
    }));
  } catch (error) {
    box.textContent = error.message;
  }
}

async function clearHistory() { await requestJson('/api/history', { method: 'DELETE' }); loadHistory(); }

async function loadQuiz() {
  const box = document.getElementById('quizList');
  box.textContent = '抽题中...';
  try {
    const data = await requestJson('/api/quiz?count=10');
    box.innerHTML = data.data.map(item => `
      <article class="quiz-card" data-question-id="${item.id}">
        <strong>${item.question}</strong>
        <div class="quiz-options">${item.options.map(option => `<label><input type="radio" name="q-${item.id}" value="${option}">${option}</label>`).join('')}</div>
        <p>${item.explanation || ''}</p>
      </article>
    `).join('');
    document.getElementById('quizResult').textContent = `题库总量：${data.total_bank_size} 道。`;
  } catch (error) {
    box.textContent = error.message;
  }
}

async function submitQuiz() {
  const cards = [...document.querySelectorAll('.quiz-card')];
  const answers = cards.map(card => {
    const checked = card.querySelector('input[type="radio"]:checked');
    return { id: Number(card.dataset.questionId), answer: checked ? checked.value : '' };
  });
  try {
    const data = await requestJson('/api/quiz/submit', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers }),
    });
    document.getElementById('quizResult').textContent = formatJson(data.data);
  } catch (error) {
    document.getElementById('quizResult').textContent = error.message;
  }
}

bindUpload('recognizeForm', 'recognizeResult', '/api/recognize');
bindUpload('similarForm', 'similarResult', '/api/similar-search');
bindUpload('understandForm', 'understandResult', '/api/image-understanding');
document.getElementById('searchBtn').addEventListener('click', doSearch);
document.getElementById('chatBtn').addEventListener('click', doChat);
document.getElementById('loadHistoryBtn').addEventListener('click', loadHistory);
document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);
document.getElementById('loadQuizBtn').addEventListener('click', loadQuiz);
document.getElementById('submitQuizBtn').addEventListener('click', submitQuiz);
loadConfig();
loadHistory();
