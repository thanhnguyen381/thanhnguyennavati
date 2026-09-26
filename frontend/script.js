/* ─────────────────────────────────────────
   AI CV Scorer v3 — script.js
   Mới: Hiển thị avatar ứng viên tự động
───────────────────────────────────────── */

const API_BASE = 'https://navati-app-ai-cv.onrender.com';

// ── DOM refs ──
const dropzone     = document.getElementById('dropzone');
const fileInput    = document.getElementById('cv-files');
const browseBtn    = document.getElementById('browse-btn');
const apiKeyInput  = document.getElementById('gemini-api-key');
const toggleKeyBtn = document.getElementById('toggle-key-btn');
const dzIdle       = document.getElementById('dz-idle');
const fileList     = document.getElementById('file-list');
const fileCountBar = document.getElementById('file-count-bar');
const fileCountTxt = document.getElementById('file-count-text');
const clearFiles   = document.getElementById('clear-files');
const addMoreBtn   = document.getElementById('add-more-btn');
const scoreBtn     = document.getElementById('score-btn');
const btnLabel     = document.getElementById('btn-label');
const btnSpin      = document.getElementById('btn-spin');
const formSection  = document.getElementById('form-section');
const loadSection  = document.getElementById('loading-section');
const resultSection= document.getElementById('result-section');
const loaderTitle  = document.getElementById('loader-title');
const loaderSub    = document.getElementById('loader-sub');
const rankBody     = document.getElementById('ranking-body');
const candidateCountEl = document.getElementById('candidate-count');
const exportBtn    = document.getElementById('export-btn');
const resetBtn     = document.getElementById('reset-btn');
const errorToast   = document.getElementById('error-toast');
const errorMsg     = document.getElementById('error-msg');
const errorListWrap= document.getElementById('error-list-wrap');
const errorListEl  = document.getElementById('error-list');

// ── Modal refs ──
const modalOverlay  = document.getElementById('modal-overlay');
const modalClose    = document.getElementById('modal-close');
const modalRing     = document.getElementById('modal-ring');
const modalScore    = document.getElementById('modal-score');
const modalName     = document.getElementById('modal-name');
const modalRankEl   = document.getElementById('modal-rank');
const modalInfoGrid = document.getElementById('modal-info-grid');
const mKyNangVal    = document.getElementById('m-ky-nang-val');
const mKyNangBar    = document.getElementById('m-ky-nang-bar');
const mKyNangNote   = document.getElementById('m-ky-nang-note');
const mKnVal        = document.getElementById('m-kn-val');
const mKnBar        = document.getElementById('m-kn-bar');
const mKnNote       = document.getElementById('m-kn-note');
const mHvVal        = document.getElementById('m-hv-val');
const mHvBar        = document.getElementById('m-hv-bar');
const mHvNote       = document.getElementById('m-hv-note');
const modalStrength = document.getElementById('modal-strength');
const modalWeakness = document.getElementById('modal-weakness');
const modalDeep     = document.getElementById('modal-deep');
const modalRecommend= document.getElementById('modal-recommend');

// ── State ──
let selectedFiles = [];
let allResults    = [];
let jdTitleGlobal = '';

// ─────────────────────────────────────────
// INIT & V4 API KEY
// ─────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  const savedKey = localStorage.getItem('gemini_api_key');
  if (savedKey) {
    apiKeyInput.value = savedKey;
  }
  renderHistoryList(); // Initialize history
});

toggleKeyBtn.addEventListener('click', () => {
  if (apiKeyInput.type === 'password') {
    apiKeyInput.type = 'text';
    toggleKeyBtn.textContent = '🙈';
  } else {
    apiKeyInput.type = 'password';
    toggleKeyBtn.textContent = '👁️';
  }
});

// ─────────────────────────────────────────
// V3 AVATAR HELPER
// ─────────────────────────────────────────

// Palette màu cho avatar fallback (chung nhiều ứng viên)
const AVATAR_COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e',
  '#f97316', '#eab308', '#22c55e', '#14b8a6',
  '#0ea5e9', '#3b82f6'
];

function getAvatarColor(name) {
  let hash = 0;
  for (let i = 0; i < (name || '').length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  // Tên Việt: chữ đầu của phần đầu và phần cuối
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Trả về HTML của avatar:
 * - Nếu có base64 ảnh thật → dùng <img>
 * - Nếu không → tạo avatar chữ cái
 */
function makeAvatarHTML(avatarBase64, name, size = 44) {
  if (avatarBase64) {
    return `<img src="${avatarBase64}" class="avatar-img" width="${size}" height="${size}" alt="${name || 'avatar'}" loading="lazy">`;
  }
  const initials = getInitials(name);
  const color    = getAvatarColor(name);
  return `<div class="avatar-letter" style="width:${size}px;height:${size}px;background:${color};font-size:${Math.round(size*0.38)}px">${initials}</div>`;
}

// ─────────────────────────────────────────
// FILE UPLOAD
// ─────────────────────────────────────────
browseBtn.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('click', (e) => { if(e.target === dropzone || e.target.closest('.dz-idle')) fileInput.click(); });
fileInput.addEventListener('change', () => addFiles(Array.from(fileInput.files)));

dropzone.addEventListener('dragover',  e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('drag-over');
  addFiles(Array.from(e.dataTransfer.files).filter(f => f.name.match(/\.(pdf|docx)$/i)));
});

function addFiles(newFiles) {
  newFiles.forEach(f => {
    if (!selectedFiles.find(s => s.name === f.name && s.size === f.size)) {
      selectedFiles.push(f);
    }
  });
  renderFileList();
}

function renderFileList() {
  fileList.innerHTML = '';
  if (selectedFiles.length === 0) {
    dzIdle.style.display = 'flex';
    fileCountBar.style.display = 'none';
    return;
  }
  dzIdle.style.display = 'none';
  fileCountBar.style.display = 'flex';
  fileCountTxt.textContent = `${selectedFiles.length} file đã chọn`;

  selectedFiles.forEach((f, i) => {
    const li = document.createElement('li');
    li.className = 'file-item';
    const ext = f.name.split('.').pop().toUpperCase();
    const size = f.size < 1048576 ? `${(f.size/1024).toFixed(0)} KB` : `${(f.size/1048576).toFixed(1)} MB`;
    li.innerHTML = `
      <span class="file-icon">${ext === 'PDF' ? '📄' : '📝'}</span>
      <span class="file-name">${f.name}</span>
      <span class="file-size">${size}</span>
      <span class="file-remove" data-idx="${i}">✕</span>
    `;
    fileList.appendChild(li);
  });

  fileList.querySelectorAll('.file-remove').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      selectedFiles.splice(Number(btn.dataset.idx), 1);
      renderFileList();
    });
  });
}

clearFiles.addEventListener('click', () => {
  selectedFiles = [];
  fileInput.value = '';
  renderFileList();
});

addMoreBtn.addEventListener('click', () => {
  fileInput.click();
});

// ─────────────────────────────────────────
// LOADING MESSAGES
// ─────────────────────────────────────────
const loadingMessages = [
  ['🤖 AI đang phân tích hồ sơ...', 'Đang đọc và hiểu nội dung CV'],
  ['🔍 Đang đối chiếu với JD...', 'So sánh kỹ năng và kinh nghiệm'],
  ['📊 Đang chấm điểm từng tiêu chí...', 'Kỹ năng · Kinh nghiệm · Học vấn'],
  ['💡 AI đang viết nhận xét chuyên sâu...', 'Phân tích điểm mạnh và điểm yếu'],
  ['⏳ Đang xếp hạng ứng viên...', 'Gần xong, vui lòng chờ thêm chút'],
];
let msgIdx = 0, msgTimer = null;

function startLoadingMessages() {
  msgIdx = 0;
  updateMsg();
  msgTimer = setInterval(() => {
    msgIdx = (msgIdx + 1) % loadingMessages.length;
    updateMsg();
  }, 3500);
}

function updateMsg() {
  loaderTitle.style.opacity = '0';
  loaderSub.style.opacity   = '0';
  setTimeout(() => {
    loaderTitle.textContent = loadingMessages[msgIdx][0];
    loaderSub.textContent   = loadingMessages[msgIdx][1];
    loaderTitle.style.opacity = '1';
    loaderSub.style.opacity   = '1';
    loaderTitle.style.transition = 'opacity 0.4s';
    loaderSub.style.transition   = 'opacity 0.4s';
  }, 200);
}

function stopLoadingMessages() {
  clearInterval(msgTimer);
}

// ─────────────────────────────────────────
// SCORE — Main
// ─────────────────────────────────────────
scoreBtn.addEventListener('click', async () => {
  const jdText  = document.getElementById('jd-text').value.trim();
  const jdTitle = document.getElementById('jd-title').value.trim() || 'Vị trí tuyển dụng';
  const apiKey  = apiKeyInput.value.trim();

  if (!apiKey) { showError('Vui lòng nhập Google Gemini API Key!'); return; }
  if (!jdText) { showError('Vui lòng nhập Mô tả công việc (JD) trước!'); return; }
  if (selectedFiles.length === 0) { showError('Vui lòng tải lên ít nhất 1 file CV!'); return; }

  localStorage.setItem('gemini_api_key', apiKey);
  jdTitleGlobal = jdTitle;

  // Build FormData
  const fd = new FormData();
  fd.append('jd_text', jdText);
  selectedFiles.forEach(f => fd.append('cvs', f));

  // Show loading
  setLoading(true);
  startLoadingMessages();

  try {
    const res  = await fetch(`${API_BASE}/score`, { 
      method: 'POST', 
      headers: { 'X-Gemini-Key': apiKey },
      body: fd 
    });
    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Lỗi không xác định từ server');
    }

    allResults = data.results;
    saveToHistory(data, jdTitleGlobal); // Luu lich su
    renderResults(data);
    showSection('result');

  } catch (err) {
    showError(`Lỗi: ${err.message}`);
    showSection('form');
  } finally {
    stopLoadingMessages();
    setLoading(false);
  }
});

function setLoading(on) {
  scoreBtn.disabled = on;
  btnLabel.style.display = on ? 'none' : '';
  btnSpin.style.display  = on ? '' : 'none';
}

function showSection(which) {
  const historySection = document.getElementById('history-section');
  
  formSection.style.display    = which === 'form'   ? '' : 'none';
  if (historySection) historySection.style.display = which === 'form' ? '' : 'none';
  
  loadSection.style.display    = which === 'loading' ? '' : 'none';
  resultSection.style.display  = which === 'result'  ? '' : 'none';

  if (which === 'loading') {
    formSection.style.display = '';   // keep form visible above loader
    if (historySection) historySection.style.display = ''; 
    loadSection.style.display = '';
    resultSection.style.display = 'none';
  }
  if (which === 'result') {
    formSection.style.display = '';
    if (historySection) historySection.style.display = 'none';
    loadSection.style.display = 'none';
    resultSection.style.display = '';
  }
  if (which === 'form') {
    formSection.style.display = '';
    if (historySection) historySection.style.display = '';
    loadSection.style.display = 'none';
    resultSection.style.display = 'none';
  }
}

// ─────────────────────────────────────────
// RENDER RESULTS TABLE
// ─────────────────────────────────────────
function scoreColor(s) {
  if (s >= 7.5) return 'score-high';
  if (s >= 5)   return 'score-medium';
  return 'score-low';
}
function badgeClass(s) {
  if (s >= 7.5) return 'badge-pass';
  if (s >= 5)   return 'badge-warn';
  return 'badge-fail';
}
function badgeLabel(s) {
  if (s >= 7.5) return '🌟 Xuất sắc';
  if (s >= 5)   return '🔶 Cân nhắc';
  return '❌ Không phù hợp';
}
function miniBarColor(s) {
  if (s >= 7.5) return '#22c55e';
  if (s >= 5)   return '#f59e0b';
  return '#ef4444';
}

function renderResults(data) {
  rankBody.innerHTML = '';
  candidateCountEl.textContent = `${data.total} ứng viên`;

  data.results.forEach((r, i) => {
    const info  = r.thong_tin_ung_vien || {};
    const tong  = parseFloat(r.tong_diem || 0);
    const kyNang  = parseFloat(r.ky_nang?.diem || 0);
    const kinhNghiem = parseFloat(r.kinh_nghiem?.diem || 0);
    const hocVan = parseFloat(r.hoc_van?.diem || 0);
    const avatarHTML = makeAvatarHTML(r.avatar_base64, info.ho_ten);

    const rankClass = i < 3 ? `rank-${i+1}` : '';
    const tr = document.createElement('tr');
    tr.className = rankClass;
    tr.innerHTML = `
      <td class="rank-num">${i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i+1}</td>
      <td>
        <div class="candidate-cell">
          <div class="avatar-wrap">${avatarHTML}</div>
          <div>
            <div class="candidate-name">${info.ho_ten || r._file || '—'}</div>
            <div class="candidate-sub">${info.vi_tri_ung_tuyen || jdTitleGlobal} · ${info.nam_sinh ? 'Sinh ' + info.nam_sinh : ''} ${info.so_dien_thoai || ''}</div>
          </div>
        </div>
      </td>
      <td>
        <div class="mini-bar-wrap"><div class="mini-bar" style="width:${kyNang*10}%;background:${miniBarColor(kyNang)}"></div></div>
        ${kyNang}/10
      </td>
      <td>
        <div class="mini-bar-wrap"><div class="mini-bar" style="width:${kinhNghiem*10}%;background:${miniBarColor(kinhNghiem)}"></div></div>
        ${kinhNghiem}/10
      </td>
      <td>
        <div class="mini-bar-wrap"><div class="mini-bar" style="width:${hocVan*10}%;background:${miniBarColor(hocVan)}"></div></div>
        ${hocVan}/10
      </td>
      <td><span class="score-cell ${scoreColor(tong)}">${tong}</span></td>
      <td><span class="rank-badge ${badgeClass(tong)}">${badgeLabel(tong)}</span></td>
      <td><button class="btn-detail" data-idx="${i}">🔍 Chi tiết</button></td>
    `;
    rankBody.appendChild(tr);
  });

  // Bind detail buttons
  rankBody.querySelectorAll('.btn-detail').forEach(btn => {
    btn.addEventListener('click', () => openModal(allResults[Number(btn.dataset.idx)]));
  });

  // Errors
  if (data.errors && data.errors.length > 0) {
    errorListWrap.style.display = '';
    errorListEl.innerHTML = data.errors.map(e =>
      `<li><strong>${e.file}</strong>: ${e.error}</li>`
    ).join('');
  } else {
    errorListWrap.style.display = 'none';
  }

  // Scroll to result
  setTimeout(() => resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// ─────────────────────────────────────────
// MODAL
// ─────────────────────────────────────────
function openModal(r) {
  const info = r.thong_tin_ung_vien || {};
  const tong = parseFloat(r.tong_diem || 0);

  modalScore.textContent = tong;
  modalName.textContent  = info.ho_ten || 'Ứng viên';
  modalRankEl.textContent = `${jdTitleGlobal} · ${badgeLabel(tong)}`;

  // ── V3: Cập nhật avatar trong modal ──
  const modalAvatarEl = document.getElementById('modal-avatar-wrap');
  if (modalAvatarEl) {
    modalAvatarEl.innerHTML = makeAvatarHTML(r.avatar_base64, info.ho_ten, 80);
  }

  // Ring animation
  const circumference = 264;
  const offset = circumference - (tong / 10) * circumference;
  setTimeout(() => {
    modalRing.style.strokeDashoffset = offset;
    if (tong >= 7.5)      modalRing.style.stroke = '#22c55e';
    else if (tong >= 5)   modalRing.style.stroke = '#f59e0b';
    else                  modalRing.style.stroke  = '#ef4444';
  }, 80);

  // Info grid
  const infoItems = [
    ['Năm sinh',  info.nam_sinh       || '—'],
    ['SĐT',       info.so_dien_thoai  || '—'],
    ['Email',     info.email          || '—'],
    ['Địa chỉ',  info.dia_chi        || '—'],
  ];
  modalInfoGrid.innerHTML = infoItems.map(([k,v]) =>
    `<div class="info-row"><span>${k}:</span> <span>${v}</span></div>`
  ).join('');

  // Scores + bars
  const setScore = (val, valEl, barEl, noteEl, note) => {
    valEl.textContent = `${val}/10`;
    barEl.style.width = `${val * 10}%`;
    if (noteEl) noteEl.textContent = note || '';
  };
  setScore(r.ky_nang?.diem||0,     mKyNangVal, mKyNangBar, mKyNangNote, r.ky_nang?.nhan_xet);
  setScore(r.kinh_nghiem?.diem||0, mKnVal,     mKnBar,     mKnNote,     r.kinh_nghiem?.nhan_xet);
  setScore(r.hoc_van?.diem||0,     mHvVal,     mHvBar,     mHvNote,     r.hoc_van?.nhan_xet);

  modalStrength.textContent = r.diem_manh    || '—';
  modalWeakness.textContent = r.diem_yeu     || '—';
  modalDeep.textContent     = r.danh_gia_chi_tiet || '—';
  modalRecommend.textContent= r.khuyen_nghi  || '—';

  modalOverlay.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', e => { if(e.target === modalOverlay) closeModal(); });
document.addEventListener('keydown', e => { if(e.key === 'Escape') closeModal(); });

function closeModal() {
  modalOverlay.style.display = 'none';
  document.body.style.overflow = '';
  // Reset ring
  modalRing.style.strokeDashoffset = '264';
  // Reset bars
  [mKyNangBar, mKnBar, mHvBar].forEach(b => b.style.width = '0');
}

// ─────────────────────────────────────────
// EXPORT EXCEL & PDF
// ─────────────────────────────────────────
exportBtn.addEventListener('click', async () => {
  if (!allResults.length) return;

  exportBtn.disabled = true;
  exportBtn.textContent = '⏳ Đang tạo file...';

  try {
    const res = await fetch(`${API_BASE}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results: allResults, jd_title: jdTitleGlobal })
    });

    if (!res.ok) throw new Error('Lỗi khi tạo Excel');

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `KetQua_ChamDiemCV_${jdTitleGlobal.replace(/\s+/g,'_')}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showError(err.message);
  } finally {
    exportBtn.disabled  = false;
    exportBtn.textContent = '📥 Xuất Excel';
  }
});

// PDF Export Logic
// PDF Export Logic
// PDF Export Logic (Sử dụng tính năng in mặc định của trình duyệt để đạt tỷ lệ thành công 100%)
const exportPdfBtn = document.getElementById('export-pdf-btn');
if (exportPdfBtn) {
  exportPdfBtn.addEventListener('click', () => {
    // Ẩn nút xuất PDF khi in
    exportPdfBtn.style.display = 'none';
    
    // Thêm CSS đặc biệt cho việc in (chỉ in modal, ẩn nền)
    const style = document.createElement('style');
    style.id = 'print-style';
    style.innerHTML = `
      @media print {
        body > *:not(.modal-overlay) {
          display: none !important;
        }
        .modal-overlay {
          position: absolute;
          top: 0;
          left: 0;
          background: none !important;
          align-items: flex-start;
          padding: 0;
        }
        .modal {
          box-shadow: none !important;
          border: none !important;
          width: 100% !important;
          max-width: 100% !important;
          max-height: none !important;
          overflow: visible !important;
          margin: 0 !important;
        }
        #modal-close, #export-pdf-btn {
          display: none !important;
        }
      }
    `;
    document.head.appendChild(style);

    // Kích hoạt hộp thoại in (Người dùng có thể chọn Save as PDF)
    setTimeout(() => {
      window.print();
      
      // Dọn dẹp sau khi in
      document.head.removeChild(style);
      exportPdfBtn.style.display = 'inline-block';
    }, 100);
  });
}

// ─────────────────────────────────────────
// HISTORY (LỊCH SỬ CHẤM ĐIỂM)
// ─────────────────────────────────────────
function saveToHistory(data, jdTitle) {
    let history = JSON.parse(localStorage.getItem('cv_scorer_history') || '[]');
    const newEntry = {
        id: Date.now(),
        date: new Date().toLocaleString('vi-VN'),
        jdTitle: jdTitle,
        total: data.total,
        results: data.results
    };
    history.unshift(newEntry);
    if(history.length > 10) history = history.slice(0, 10); // Keep last 10
    localStorage.setItem('cv_scorer_history', JSON.stringify(history));
    renderHistoryList();
}

function renderHistoryList() {
    const historyWrap = document.getElementById('history-list');
    if (!historyWrap) return;
    
    let history = JSON.parse(localStorage.getItem('cv_scorer_history') || '[]');
    if(history.length === 0) {
        historyWrap.innerHTML = '<p style="color: #64748b; font-size: 0.9rem;">Chưa có lịch sử chấm điểm.</p>';
        return;
    }
    
    historyWrap.innerHTML = history.map((h, i) => `
        <div class="history-item" style="padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: 0.2s;" onclick="loadHistoryItem(${i})">
            <div>
                <strong style="color: #1e293b; font-size: 0.95rem;">${h.jdTitle}</strong>
                <p style="margin: 3px 0 0; font-size: 0.8rem; color: #64748b;">${h.date} — ${h.total} ứng viên</p>
            </div>
            <span style="background: #e0e7ff; color: #4338ca; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Xem lại &rarr;</span>
        </div>
    `).join('');
}

window.loadHistoryItem = function(index) {
    let history = JSON.parse(localStorage.getItem('cv_scorer_history') || '[]');
    const item = history[index];
    if(item) {
        allResults = item.results;
        jdTitleGlobal = item.jdTitle;
        renderResults({ results: item.results, total: item.total, errors: [] });
        showSection('result');
    }
};

// ─────────────────────────────────────────
// RESET
// ─────────────────────────────────────────
resetBtn.addEventListener('click', () => {
  allResults    = [];
  selectedFiles = [];
  fileInput.value = '';
  renderFileList();
  rankBody.innerHTML = '';
  showSection('form');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ─────────────────────────────────────────
// TOAST
// ─────────────────────────────────────────
let toastTimer;
function showError(msg) {
  errorMsg.textContent = msg;
  errorToast.style.display = 'flex';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { errorToast.style.display = 'none'; }, 5000);
}

// ─────────────────────────────────────────
// LOADING section toggle (keep form visible)
// ─────────────────────────────────────────
// Override setLoading to show loader BELOW form
function startLoadingUI() {
  loadSection.style.display = '';
  resultSection.style.display = 'none';
  loadSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
function stopLoadingUI() {
  loadSection.style.display = 'none';
}

// Patch score click to show loader inline
document.getElementById('score-btn').addEventListener('click', () => {}, { once: false });
// (already handled above in scoreBtn listener)
