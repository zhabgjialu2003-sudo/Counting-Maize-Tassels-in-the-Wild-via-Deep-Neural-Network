// Farmer-facing maize leaf screening. API values are rendered with textContent
// so model output and user notes can never be interpreted as HTML.
(function initialiseLeafHealthPage() {
  'use strict';

  const COPY = {
    en: {
      pageEyebrow: 'Farmer leaf screening', pageTitle: 'Check leaf health',
      pageIntro: 'Upload one clear, close-up maize leaf photo for an initial screening.',
      languageLabel: 'Language', backLink: '‹ Home',
      purposeTitle: 'Use the right photo',
      purposeText: 'Leaf Health needs a close-up of one affected leaf. Tassel Counting needs a wide maize-field photo.',
      purposeLink: 'Go to Tassel Counting',
      guideOneTitle: '1. Fill the frame', guideOneText: 'Keep one affected leaf large and in focus.',
      guideTwoTitle: '2. Use soft light', guideTwoText: 'Avoid deep shadows, glare and digital zoom.',
      guideThreeTitle: '3. Show the symptom', guideThreeText: 'Include both affected and nearby healthy tissue.',
      filePromptTitle: 'Take or choose a leaf photo', filePromptText: 'JPG or PNG · up to 10 MB',
      takePhotoText: 'Take photo', chooseGalleryText: 'Choose from gallery',
      fieldLabel: 'Field for optional Agronomist review', noField: 'No field selected',
      fieldHelp: 'A field is only required if you later ask an Agronomist to review the result.',
      cropStageLabel: 'Growth stage (optional)', cropPlaceholder: 'For example: before tasseling',
      weatherLabel: 'Recent weather (optional)', weatherPlaceholder: 'For example: humid with frequent rain',
      spreadLabel: 'How symptoms are spreading (optional)', spreadPlaceholder: 'For example: started on lower leaves three days ago',
      submit: 'Screen this leaf', preparing: 'Preparing your photo…', uploading: 'Uploading securely…',
      analysing: 'Looking carefully at the visible leaf signs…', retained: 'Your photo is still here. You can try again.',
      selected: 'Selected', resultEyebrow: 'Screening result', emptyResultTitle: 'Your result will appear here',
      emptyResultText: 'We will explain what the model noticed, how certain it is, and what you can safely do next.',
      possibleCondition: 'Possible condition', confidence: 'Model confidence', observation: 'What was noticed',
      nextSteps: 'Safe next steps', questions: 'Helpful field questions', technical: 'Technical details',
      noCondition: 'No reliable condition match', saved: 'This screening was saved to your private history.',
      notDiagnosis: 'This is an image-based screening, not a confirmed diagnosis. Do not apply chemicals based only on this result.',
      reviewEyebrow: 'Human review', reviewTitle: 'Ask an Agronomist',
      reviewIntro: 'You stay in control. Nothing is shared unless you choose to request a review.',
      reviewReasonLabel: 'What would you like help with? (optional)', reviewPlaceholder: 'Add a short note for the Agronomist',
      requestReview: 'Request Agronomist review', selectField: 'Select one of your fields before requesting a review.',
      reviewSending: 'Sending your request…', reviewRequested: 'Review requested. An assigned Agronomist can now see this check.',
      historyEyebrow: 'Follow-up', historyTitle: 'Recent leaf checks', refresh: 'Refresh', loadingHistory: 'Loading recent checks…',
      noHistory: 'No leaf checks yet.', historyError: 'Recent checks could not be loaded.',
      reviewed: 'Reviewed', inReview: 'In review', requested: 'Review requested', notRequested: 'Private · not shared',
      professionalNote: 'Agronomist note', navHome: 'Home', navHistory: 'History', navProfile: 'Account',
      fieldsUnavailable: 'Fields could not be loaded. Screening still works, but review requests need a field.',
      requestFailed: 'The review request could not be sent.', screenFailed: 'The screening could not be completed.',
      strongMatch: 'strong match', moderateMatch: 'moderate match', needsConfirmation: 'needs confirmation'
    },
    'zh-CN': {
      pageEyebrow: '农户叶片初步筛查', pageTitle: '检查玉米叶片健康',
      pageIntro: '上传一张清晰的玉米叶片近照，系统会先做初步筛查。',
      languageLabel: '语言', backLink: '‹ 返回首页',
      purposeTitle: '请使用合适的照片',
      purposeText: '叶片健康检查需要一片病变叶片的近照；玉米穗计数需要较宽的玉米田照片。',
      purposeLink: '前往玉米穗计数',
      guideOneTitle: '1. 让叶片占满画面', guideOneText: '只拍一片有症状的叶片，并保持对焦清楚。',
      guideTwoTitle: '2. 使用柔和光线', guideTwoText: '避免浓重阴影、反光和数码变焦。',
      guideThreeTitle: '3. 拍清病变位置', guideThreeText: '同时保留病变组织和附近健康组织。',
      filePromptTitle: '拍摄或选择叶片照片', filePromptText: 'JPG 或 PNG · 最大 10 MB',
      takePhotoText: '拍照', chooseGalleryText: '从相册选择',
      fieldLabel: '选择田块（申请农艺师复核时使用）', noField: '暂不选择田块',
      fieldHelp: '初步筛查不要求田块；只有申请农艺师复核时才必须选择。',
      cropStageLabel: '生育期（可不填）', cropPlaceholder: '例如：抽雄前',
      weatherLabel: '近期天气（可不填）', weatherPlaceholder: '例如：潮湿并经常下雨',
      spreadLabel: '症状如何扩散（可不填）', spreadPlaceholder: '例如：三天前从下部叶片开始',
      submit: '开始筛查这片叶子', preparing: '正在处理照片…', uploading: '正在安全上传…',
      analysing: '正在仔细查看叶片上的可见特征…', retained: '照片仍保留在当前页面，可以直接重试。',
      selected: '已选择', resultEyebrow: '筛查结果', emptyResultTitle: '结果会显示在这里',
      emptyResultText: '我们会说明模型看到了什么、把握程度，以及接下来可以安全做什么。',
      possibleCondition: '可能的情况', confidence: '模型置信度', observation: '观察到的特征',
      nextSteps: '安全的下一步', questions: '建议补充确认的问题', technical: '技术信息',
      noCondition: '暂时无法可靠匹配', saved: '本次筛查已保存到你的私人历史记录。',
      notDiagnosis: '这是根据图片进行的初步筛查，并非确诊结果。请勿仅凭本结果使用农药。',
      reviewEyebrow: '人工复核', reviewTitle: '请农艺师协助',
      reviewIntro: '是否分享由你决定。只有你主动申请后，分配给该田块的农艺师才能查看。',
      reviewReasonLabel: '你希望农艺师重点帮助什么？（可不填）', reviewPlaceholder: '给农艺师留一段简短说明',
      requestReview: '申请农艺师复核', selectField: '申请复核前，请先选择属于你的田块。',
      reviewSending: '正在发送申请…', reviewRequested: '复核申请已发送，负责该田块的农艺师现在可以查看。',
      historyEyebrow: '后续跟进', historyTitle: '最近的叶片检查', refresh: '刷新', loadingHistory: '正在加载最近记录…',
      noHistory: '还没有叶片检查记录。', historyError: '暂时无法加载最近记录。',
      reviewed: '已完成复核', inReview: '农艺师复核中', requested: '已申请复核', notRequested: '仅自己可见 · 未分享',
      professionalNote: '农艺师说明', navHome: '首页', navHistory: '历史', navProfile: '我的',
      fieldsUnavailable: '暂时无法加载田块。初步筛查仍可使用，但申请复核需要田块。',
      requestFailed: '暂时无法发送复核申请。', screenFailed: '本次筛查未能完成。',
      strongMatch: '较强匹配', moderateMatch: '中等匹配', needsConfirmation: '需要进一步确认'
    }
  };

  const state = { language: mobileLanguage(), prepared: null, previewUrl: null, latest: null, fields: [] };
  const byId = id => document.getElementById(id);
  const text = (id, value) => { const node = byId(id); if (node) node.textContent = value; };
  const copy = key => COPY[state.language][key] || COPY.en[key] || key;
  const make = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = String(content);
    return node;
  };
  const replaceChildren = (node, ...children) => { node.replaceChildren(...children.filter(Boolean)); };

  function setInterfaceLanguage(language) {
    state.language = language === 'zh-CN' ? 'zh-CN' : 'en';
    setMobileLanguage(state.language);
    document.documentElement.lang = state.language;
    byId('languageSelect').value = state.language;
    const simpleIds = [
      'pageEyebrow', 'pageTitle', 'pageIntro', 'languageLabel', 'backLink', 'purposeTitle', 'purposeText',
      'purposeLink', 'guideOneTitle', 'guideOneText', 'guideTwoTitle', 'guideTwoText', 'guideThreeTitle',
      'guideThreeText', 'filePromptTitle', 'filePromptText', 'takePhotoText', 'chooseGalleryText', 'fieldLabel', 'fieldHelp', 'cropStageLabel',
      'weatherLabel', 'spreadLabel', 'submitButton', 'resultEyebrow', 'emptyResultTitle', 'emptyResultText',
      'reviewEyebrow', 'reviewTitle', 'reviewIntro', 'reviewReasonLabel', 'requestReviewButton', 'historyEyebrow',
      'historyTitle', 'refreshHistory', 'navHome', 'navHistory', 'navProfile'
    ];
    const keyMap = { submitButton: 'submit', requestReviewButton: 'requestReview', refreshHistory: 'refresh' };
    simpleIds.forEach(id => text(id, copy(keyMap[id] || id)));
    byId('cropStage').placeholder = copy('cropPlaceholder');
    byId('recentWeather').placeholder = copy('weatherPlaceholder');
    byId('symptomSpread').placeholder = copy('spreadPlaceholder');
    byId('reviewReason').placeholder = copy('reviewPlaceholder');
    renderFieldOptions();
    if (state.latest) renderResult(state.latest);
    loadHistory();
  }

  function renderFieldOptions() {
    const select = byId('leafField');
    const selected = select.value;
    const options = [new Option(copy('noField'), '')];
    state.fields.forEach(field => options.push(new Option(field.name || `Field ${field.fieldId}`, field.fieldId)));
    replaceChildren(select, ...options);
    if ([...select.options].some(option => option.value === selected)) select.value = selected;
  }

  async function loadFields() {
    if (currentRole() !== 'Farmer') return;
    const response = await apiGet('/api/fields');
    if (!response.ok) {
      text('uploadState', copy('fieldsUnavailable'));
      return;
    }
    state.fields = Array.isArray(response.data.fields)
      ? response.data.fields.map(field => ({
          fieldId: field.field_id ?? field.fieldId,
          name: field.field_name ?? field.fieldName ?? `Field ${field.field_id ?? field.fieldId}`,
        }))
      : [];
    renderFieldOptions();
  }

  async function choosePhoto(file) {
    if (!file) return;
    text('uploadState', copy('preparing'));
    try {
      state.prepared = await prepareImageForUpload(file, { maxLongEdge: 2200, quality: 0.88 });
      if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
      state.previewUrl = URL.createObjectURL(state.prepared.file);
      const preview = byId('leafPreview');
      preview.src = state.previewUrl;
      preview.hidden = false;
      byId('filePrompt').hidden = true;
      byId('submitButton').disabled = false;
      text('sizeNote', `${copy('selected')}: ${formatFileSize(state.prepared.originalBytes)} → ${formatFileSize(state.prepared.preparedBytes)} · ${state.prepared.width}×${state.prepared.height}`);
      text('uploadState', '');
    } catch (error) {
      state.prepared = null;
      byId('submitButton').disabled = true;
      text('uploadState', error.message);
    }
  }

  function addListSection(parent, title, values) {
    if (!Array.isArray(values) || !values.length) return;
    const section = make('section', 'diagnosis-section');
    section.append(make('h3', '', title));
    const list = make('ul');
    values.forEach(value => {
      const message = typeof value === 'object' ? (value.message || value.display_name || value.code) : value;
      if (message) list.append(make('li', '', message));
    });
    section.append(list);
    parent.append(section);
  }

  function renderResult(result) {
    const root = byId('leafResult');
    root.className = 'diagnosis-panel diagnosis-result';
    const eyebrow = make('p', 'eyebrow', copy('resultEyebrow'));
    const headline = make('h2', '', result.headline || copy('noCondition'));
    const condition = result.possible_condition || {};
    const summary = make('div', 'leaf-result-summary');
    const conditionCard = make('div', 'leaf-result-metric');
    conditionCard.append(make('span', '', copy('possibleCondition')), make('strong', '', condition.display_name || copy('noCondition')));
    summary.append(conditionCard);
    const confidence = Number(result.technical && result.technical.confidence);
    if (Number.isFinite(confidence)) {
      const confidenceCard = make('div', 'leaf-result-metric');
      const bandKey = { strong_match: 'strongMatch', moderate_match: 'moderateMatch', needs_confirmation: 'needsConfirmation' }[condition.confidence_band] || 'needsConfirmation';
      confidenceCard.append(make('span', '', copy('confidence')), make('strong', '', `${Math.round(confidence * 100)}% · ${copy(bandKey)}`));
      summary.append(confidenceCard);
    }
    replaceChildren(root, eyebrow, headline, summary);
    addListSection(root, copy('observation'), result.observation);
    addListSection(root, copy('nextSteps'), result.next_steps);
    addListSection(root, copy('questions'), result.follow_up_questions);
    const safety = make('div', 'diagnosis-safety');
    safety.append(make('strong', '', copy('notDiagnosis')), make('p', '', result.safety_note || ''));
    root.append(safety);
    if (result.persistence && result.persistence.status === 'saved') root.append(make('p', 'leaf-saved-note', copy('saved')));

    const canRequest = currentRole() === 'Farmer' && result.diagnosis_id && result.persistence && result.persistence.status === 'saved';
    byId('reviewPanel').hidden = !canRequest;
    if (canRequest) {
      const recommended = result.review && result.review.recommended;
      byId('reviewPanel').classList.toggle('review-recommended', Boolean(recommended));
      byId('requestReviewButton').disabled = false;
      text('reviewState', '');
    }
  }

  async function submitScreening(event) {
    event.preventDefault();
    if (!state.prepared) return;
    const button = byId('submitButton');
    const progress = byId('diagnosisProgress');
    button.disabled = true;
    progress.hidden = false;
    text('uploadState', '');
    text('progressText', copy('uploading'));
    byId('progressBar').style.width = '4%';
    const details = {
      language: state.language,
      field_id: byId('leafField').value,
      crop_stage: byId('cropStage').value,
      recent_weather: byId('recentWeather').value,
      symptom_spread: byId('symptomSpread').value,
    };
    const response = await apiDiagnoseDiseaseWithProgress(state.prepared.file, details, percent => {
      byId('progressBar').style.width = `${Math.min(92, percent)}%`;
      text('progressText', percent >= 100 ? copy('analysing') : `${copy('uploading')} ${percent}%`);
    });
    byId('progressBar').style.width = response.ok ? '100%' : '0%';
    progress.hidden = response.ok;
    button.disabled = false;
    if (!response.ok) {
      text('uploadState', `${response.error || copy('screenFailed')} ${copy('retained')}`);
      return;
    }
    state.latest = response.data;
    renderResult(state.latest);
    await loadHistory();
    byId('leafResult').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function requestReview() {
    if (!state.latest || !state.latest.diagnosis_id) return;
    const fieldId = byId('leafField').value;
    if (!fieldId) {
      text('reviewState', copy('selectField'));
      byId('leafField').focus();
      return;
    }
    const button = byId('requestReviewButton');
    button.disabled = true;
    text('reviewState', copy('reviewSending'));
    const response = await apiRequestDiseaseReview(state.latest.diagnosis_id, Number(fieldId), byId('reviewReason').value.trim());
    if (!response.ok) {
      button.disabled = false;
      text('reviewState', response.error || copy('requestFailed'));
      return;
    }
    text('reviewState', copy('reviewRequested'));
    await loadHistory();
  }

  function reviewStatusText(status) {
    return copy({ reviewed: 'reviewed', in_review: 'inReview', requested: 'requested' }[status] || 'notRequested');
  }

  function renderHistory(records) {
    const root = byId('leafHistory');
    root.replaceChildren();
    if (!records.length) {
      root.append(make('p', 'info-text', copy('noHistory')));
      return;
    }
    records.slice(0, 8).forEach(record => {
      const article = make('article', 'leaf-history-item');
      const main = make('div');
      main.append(make('strong', '', record.condition_name || record.headline || copy('noCondition')));
      const date = record.created_at ? new Date(record.created_at).toLocaleString(state.language) : '';
      if (date) main.append(make('time', '', date));
      const status = make('span', `review-status review-status-${record.review_status || 'not_requested'}`, reviewStatusText(record.review_status));
      article.append(main, status);
      if (record.reviewer_note) {
        const note = make('p', 'leaf-review-note');
        note.append(make('b', '', `${copy('professionalNote')}: `), document.createTextNode(record.reviewer_note));
        article.append(note);
      }
      root.append(article);
    });
  }

  async function loadHistory() {
    if (currentRole() !== 'Farmer') {
      byId('historySection').hidden = true;
      return;
    }
    text('leafHistory', copy('loadingHistory'));
    const response = await apiGet('/api/agronomy/diagnoses');
    if (!response.ok) {
      text('leafHistory', copy('historyError'));
      return;
    }
    renderHistory(Array.isArray(response.data.records) ? response.data.records : []);
  }

  async function start() {
    if (!requireRole(['Farmer', 'Researcher', 'Agronomist', 'Admin'])) return;
    if (!await validateSession()) return;
    initNav();
    setActiveNav();
    setInterfaceLanguage(state.language);
    await loadFields();
    ['leafDesktopPhoto', 'leafCameraPhoto', 'leafGalleryPhoto'].forEach(id => {
      byId(id).addEventListener('change', async event => {
        const input = event.currentTarget;
        const file = input.files && input.files[0];
        if (!file) return;
        await choosePhoto(file);
        input.value = '';
      });
    });
    byId('leafForm').addEventListener('submit', submitScreening);
    byId('requestReviewButton').addEventListener('click', requestReview);
    byId('refreshHistory').addEventListener('click', loadHistory);
    byId('languageSelect').addEventListener('change', event => setInterfaceLanguage(event.target.value));
  }

  window.addEventListener('beforeunload', () => {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
  });
  document.addEventListener('DOMContentLoaded', start);
})();
