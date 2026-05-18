const categoryLabels = {
  recyclable: '可回收物',
  hazardous: '有害垃圾',
  kitchen: '厨余垃圾',
  other: '其他垃圾',
};

const formatPercent = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`;
const mediaUrl = (relativePath) => relativePath ? `/media/${String(relativePath).replace(/\\/g, '/')}` : '';

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({ ok: false, message: '响应不是有效 JSON。' }));
  if (!response.ok || data.ok === false) throw new Error(data.message || `请求失败：${response.status}`);
  return data;
}

function switchView(viewId) {
  const id = viewId || 'home';
  document.querySelectorAll('.view').forEach(view => view.classList.toggle('active', view.id === id));
  document.querySelectorAll('[data-view-link]').forEach(link => link.classList.toggle('active', link.dataset.viewLink === id));
  if (id === 'history') loadHistory();
  if (id === 'quiz' && !document.querySelector('.quiz-card')) loadQuiz();
  window.scrollTo({ top: 0, behavior: 'auto' });
  setTimeout(() => window.scrollTo({ top: 0, behavior: 'auto' }), 0);
}

function bindNavigation() {
  document.querySelectorAll('[data-view-link]').forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      const id = link.dataset.viewLink;
      history.replaceState(null, '', `#${id}`);
      switchView(id);
    });
  });
  switchView(location.hash ? location.hash.slice(1) : 'home');
}

function bindPreview(formId, previewId) {
  const input = document.querySelector(`#${formId} input[type="file"]`);
  const box = document.getElementById(previewId).closest('.image-preview');
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    document.getElementById(previewId).src = URL.createObjectURL(file);
    box.classList.add('has-image');
  });
}

function renderRecognition(result) {
  const probs = Object.entries(result.probabilities || {}).map(([name, value]) => `
    <div class="prob-item"><span>${categoryLabels[name] || name}</span><div class="bar"><span style="width:${Math.max(2, Number(value) * 100)}%"></span></div><strong>${formatPercent(value)}</strong></div>
  `).join('');
  return `
    <div class="metric-row">
      <div class="metric blue"><strong>${categoryLabels[result.predicted_class] || result.predicted_class}</strong><span>识别类别</span></div>
      <div class="metric green"><strong>${formatPercent(result.confidence)}</strong><span>置信度</span></div>
      <div class="metric cyan"><strong>#${result.history_id || '-'}</strong><span>历史编号</span></div>
    </div>
    <strong>分类依据</strong>
    <p>${result.rationale || '系统根据图像特征给出该分类结果。'}</p>
    <strong>类别概率</strong>
    <div class="prob-list">${probs}</div>
  `;
}

function bindRecognize() {
  document.getElementById('recognizeForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const output = document.getElementById('recognizeResult');
    output.textContent = '正在识别，请稍候...';
    try {
      const data = await requestJson('/api/recognize', { method: 'POST', body: new FormData(event.target) });
      output.innerHTML = renderRecognition(data.data);
      loadHistory();
    } catch (error) {
      output.textContent = error.message;
    }
  });
}

function renderSimilar(items) {
  if (!items.length) return '<div class="notice-box">未找到超过阈值的相似案例。</div>';
  return items.map(item => {
    const payload = item.payload || {};
    return `
      <article class="similar-card">
        <img src="${mediaUrl(payload.image_path)}" alt="${payload.filename || '相似图片'}">
        <div><strong>${payload.filename || '参考图片'}</strong><br>类别：${categoryLabels[payload.category] || payload.category || '-'}<br>相似度：${formatPercent(item.score)}</div>
      </article>
    `;
  }).join('');
}

function bindSimilar() {
  document.getElementById('similarForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const summary = document.getElementById('similarSummary');
    const output = document.getElementById('similarResult');
    summary.textContent = '正在提取特征并检索 Qdrant...';
    output.innerHTML = '';
    const start = performance.now();
    try {
      const data = await requestJson('/api/similar-search', { method: 'POST', body: new FormData(event.target) });
      const elapsed = Math.round(performance.now() - start);
      summary.textContent = `返回 ${data.data.length} 条相似案例，用时 ${elapsed} ms。`;
      output.innerHTML = renderSimilar(data.data);
    } catch (error) {
      summary.textContent = error.message;
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
    output.innerHTML = data.data.length ? data.data.map(item => `
      <article class="knowledge-card"><strong>${item.name}</strong><br>类别：${categoryLabels[item.category] || item.category}<br>${item.description}</article>
    `).join('') : '<article class="knowledge-card">未找到匹配条目，可换一个关键词。</article>';
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

function bindUnderstanding() {
  document.getElementById('understandForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const output = document.getElementById('understandResult');
    output.textContent = '正在调用星火图片理解...';
    try {
      const data = await requestJson('/api/image-understanding', { method: 'POST', body: new FormData(event.target) });
      output.textContent = data.data.answer;
    } catch (error) {
      output.textContent = error.message;
    }
  });
}

async function loadHistory() {
  const body = document.getElementById('historyList');
  body.innerHTML = '<tr><td colspan="6">加载中...</td></tr>';
  try {
    const data = await requestJson('/api/history?page=1&page_size=10');
    if (!data.data.items.length) { body.innerHTML = '<tr><td colspan="6">暂无历史记录。</td></tr>'; return; }
    body.innerHTML = data.data.items.map(item => `
      <tr>
        <td>${item.id}</td>
        <td><img class="thumb" src="${mediaUrl(item.image_path)}" alt="历史图片"></td>
        <td>${categoryLabels[item.predicted_class] || item.predicted_class}</td>
        <td>${formatPercent(item.confidence)}</td>
        <td>${item.created_at}</td>
        <td><button data-delete-id="${item.id}" class="gray">删除</button></td>
      </tr>
    `).join('');
    body.querySelectorAll('[data-delete-id]').forEach(button => button.addEventListener('click', async () => {
      await requestJson(`/api/history/${button.dataset.deleteId}`, { method: 'DELETE' });
      loadHistory();
    }));
  } catch (error) {
    body.innerHTML = `<tr><td colspan="6">${error.message}</td></tr>`;
  }
}

async function clearHistory() { await requestJson('/api/history', { method: 'DELETE' }); loadHistory(); }

async function loadQuiz() {
  const box = document.getElementById('quizList');
  box.textContent = '抽题中...';
  try {
    const data = await requestJson('/api/quiz?count=10');
    box.innerHTML = data.data.map((item, index) => `
      <article class="quiz-card" data-question-id="${item.id}">
        <strong>${index + 1}. ${item.question}</strong>
        <div class="quiz-options">${item.options.map(option => `<label><input type="radio" name="q-${item.id}" value="${option}">${option}</label>`).join('')}</div>
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
    document.getElementById('quizResult').textContent = `得分：${data.data.score}，答对 ${data.data.correct}/${data.data.total} 题。`;
  } catch (error) {
    document.getElementById('quizResult').textContent = error.message;
  }
}

bindNavigation();
bindPreview('recognizeForm', 'recognizePreview');
bindPreview('similarForm', 'similarPreview');
bindRecognize();
bindSimilar();
bindUnderstanding();
document.getElementById('searchBtn').addEventListener('click', doSearch);
document.getElementById('chatBtn').addEventListener('click', doChat);
document.getElementById('loadHistoryBtn').addEventListener('click', loadHistory);
document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);
document.getElementById('loadQuizBtn').addEventListener('click', loadQuiz);
document.getElementById('submitQuizBtn').addEventListener('click', submitQuiz);
loadConfig();
loadHistory();
