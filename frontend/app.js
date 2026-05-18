const { createApp } = Vue;

const labels = {
  recyclable: '可回收物',
  hazardous: '有害垃圾',
  kitchen: '厨余垃圾',
  other: '其他垃圾',
};

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({ ok: false, message: '响应不是有效 JSON。' }));
  if (!response.ok || data.ok === false) {
    throw new Error(data.message || `请求失败：${response.status}`);
  }
  return data;
}

const ModuleCard = {
  props: ['title', 'tone'],
  template: `
    <div class="module-card">
      <div class="module-title" :class="tone + '-bg'">{{ title }}</div>
      <slot></slot>
    </div>
  `,
};

const ImagePreview = {
  props: ['src', 'text'],
  template: `
    <div class="image-preview" :class="{ 'has-image': src }">
      <img v-if="src" :src="src" alt="图片预览">
      <span v-else>{{ text }}</span>
    </div>
  `,
};

createApp({
  components: { ModuleCard, ImagePreview },
  data() {
    return {
      currentView: 'home',
      navItems: [
        { id: 'home', label: '首页', icon: '总' },
        { id: 'recognize', label: '图像识别', icon: '识' },
        { id: 'similar', label: '相似检索', icon: '检' },
        { id: 'search', label: '分类知识', icon: '知' },
        { id: 'chat', label: '智能问答', icon: '问' },
      ],
      stats: [
        { label: '分类数量', value: '4', tone: 'blue' },
        { label: '参考图片', value: '8213', tone: 'green' },
        { label: '测试准确率', value: '98.30%', tone: 'cyan' },
      ],
      features: [
        { id: 'recognize', title: '图像识别', tag: 'ResNet50', icon: '识', desc: '上传图片后返回四分类结果、置信度和分类依据。', action: '上传识别', tone: 'blue' },
        { id: 'similar', title: '相似检索', tag: 'Qdrant', icon: '检', desc: '用图像特征检索相似案例，辅助解释分类结果。', action: '检索案例', tone: 'green' },
        { id: 'search', title: '分类知识', tag: '知识库', icon: '知', desc: '按物品名称查询分类类别和处理建议。', action: '查询知识', tone: 'green' },
        { id: 'chat', title: '智能问答', tag: 'DeepSeek', icon: '问', desc: '面向分类问题提供问答入口，未配置密钥时返回明确提示。', action: '提问', tone: 'cyan' },
        { id: 'understand', title: '图片理解', tag: '星火', icon: '图', desc: '预留多模态图片理解接口，用于复杂场景分析。', action: '图片分析', tone: 'cyan' },
        { id: 'history', title: '历史记录', tag: '史', desc: '保存识别记录，支持查看、删除和清空。', action: '查看记录', tone: 'gray' },
      ],
      recognizePreview: '',
      recognizeResult: null,
      recognizeError: '',
      recognizeLoading: false,
      similarPreview: '',
      similarResults: [],
      similarMessage: 'Qdrant 集合 waste_images 已包含 8213 条参考向量。',
      keyword: '',
      hotKeywords: [],
      searchResults: [],
      searchMessage: '输入关键词查看分类知识。',
      chatQuestion: '',
      chatAnswer: '需要配置 DEEPSEEK_API_KEY。',
      understandResult: '需要配置星火视觉接口参数。',
      historyItems: [],
      historyMessage: '暂无历史记录。',
      quizItems: [],
      quizAnswers: {},
      quizResult: '题库不少于 20 道。',
    };
  },
  mounted() {
    this.switchView(location.hash ? location.hash.slice(1) : 'home');
    this.loadConfig();
    this.loadHistory();
  },
  computed: {
    currentSectionMeta() {
      const titleMap = {
        home: ['工作台', '废弃物识别与数据管理'],
        recognize: ['模型推理', '图像识别'],
        similar: ['向量检索', '相似案例'],
        search: ['知识库', '分类知识检索'],
        chat: ['问答', '智能交流'],
        understand: ['视觉接口', '图片理解'],
        history: ['记录', '识别历史'],
        quiz: ['学习', '知识测试'],
      };
      const [eyebrow, title] = titleMap[this.currentView] || titleMap.home;
      return { eyebrow, title };
    },
  },
  methods: {
    switchView(id) {
      const allowedViews = new Set(['home', 'recognize', 'similar', 'search', 'chat', 'understand', 'history']);
      this.currentView = allowedViews.has(id) ? id : 'home';
      history.replaceState(null, '', `#${this.currentView}`);
      if (this.currentView === 'history') this.loadHistory();
      this.$nextTick(() => window.scrollTo({ top: 0, behavior: 'auto' }));
    },
    labelOf(name) {
      return labels[name] || name || '-';
    },
    percent(value) {
      return `${(Number(value || 0) * 100).toFixed(1)}%`;
    },
    mediaUrl(relativePath) {
      return relativePath ? `/media/${String(relativePath).replace(/\\/g, '/')}` : '';
    },
    previewFile(type, event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      if (type === 'recognize') this.recognizePreview = url;
      if (type === 'similar') this.similarPreview = url;
    },
    formDataFrom(refName) {
      const input = this.$refs[refName];
      const file = input && input.files && input.files[0];
      if (!file) throw new Error('请先选择图片文件。');
      const formData = new FormData();
      formData.append('image', file);
      return formData;
    },
    async recognize() {
      this.recognizeLoading = true;
      this.recognizeError = '';
      this.recognizeResult = null;
      try {
        const data = await requestJson('/api/recognize', { method: 'POST', body: this.formDataFrom('recognizeInput') });
        this.recognizeResult = data.data;
        this.loadHistory();
      } catch (error) {
        this.recognizeError = error.message;
      } finally {
        this.recognizeLoading = false;
      }
    },
    async searchSimilar() {
      this.similarResults = [];
      this.similarMessage = '正在提取特征并检索 Qdrant...';
      const start = performance.now();
      try {
        const data = await requestJson('/api/similar-search', { method: 'POST', body: this.formDataFrom('similarInput') });
        const elapsed = Math.round(performance.now() - start);
        this.similarResults = data.data;
        this.similarMessage = `返回 ${data.data.length} 条相似案例，用时 ${elapsed} ms。`;
      } catch (error) {
        this.similarMessage = error.message;
      }
    },
    async loadConfig() {
      try {
        const data = await requestJson('/api/search?q=');
        this.hotKeywords = data.hot_keywords || [];
      } catch (error) {
        console.warn(error.message);
      }
    },
    useKeyword(word) {
      this.keyword = word;
      this.doSearch();
    },
    async doSearch() {
      this.searchResults = [];
      this.searchMessage = '检索中...';
      try {
        const data = await requestJson(`/api/search?q=${encodeURIComponent(this.keyword)}`);
        this.searchResults = data.data;
        this.searchMessage = data.data.length ? '' : '未找到匹配条目，可换一个关键词。';
      } catch (error) {
        this.searchMessage = error.message;
      }
    },
    async askChat() {
      this.chatAnswer = '正在提交问题...';
      try {
        const data = await requestJson('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: this.chatQuestion }),
        });
        this.chatAnswer = data.data.answer;
      } catch (error) {
        this.chatAnswer = error.message;
      }
    },
    async understandImage() {
      this.understandResult = '正在分析图片...';
      try {
        const data = await requestJson('/api/image-understanding', { method: 'POST', body: this.formDataFrom('understandInput') });
        this.understandResult = data.data.answer;
      } catch (error) {
        this.understandResult = error.message;
      }
    },
    async loadHistory() {
      this.historyMessage = '加载中...';
      try {
        const data = await requestJson('/api/history?page=1&page_size=10');
        this.historyItems = data.data.items;
        this.historyMessage = this.historyItems.length ? '' : '暂无历史记录。';
      } catch (error) {
        this.historyItems = [];
        this.historyMessage = error.message;
      }
    },
    async deleteHistory(id) {
      await requestJson(`/api/history/${id}`, { method: 'DELETE' });
      this.loadHistory();
    },
    async clearHistory() {
      await requestJson('/api/history', { method: 'DELETE' });
      this.loadHistory();
    },
    async loadQuiz() {
      this.quizResult = '抽题中...';
      try {
        const data = await requestJson('/api/quiz?count=10');
        this.quizItems = data.data;
        this.quizAnswers = {};
        this.quizResult = `题库总量：${data.total_bank_size} 道。`;
      } catch (error) {
        this.quizResult = error.message;
      }
    },
    async submitQuiz() {
      const answers = this.quizItems.map(item => ({ id: item.id, answer: this.quizAnswers[item.id] || '' }));
      try {
        const data = await requestJson('/api/quiz/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers }),
        });
        this.quizResult = `得分：${data.data.score}，答对 ${data.data.correct}/${data.data.total} 题。`;
      } catch (error) {
        this.quizResult = error.message;
      }
    },
  },
}).mount('#app');
