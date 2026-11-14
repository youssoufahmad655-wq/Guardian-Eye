/* ============================================================
   Guardian Eye — Application JS
   Shared + Dashboard logic (all DOM access is guarded)
   ============================================================ */

// ---------- TOAST ----------
function showToast(msg, type) {
  var el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = 'toast ' + (type || 'success') + ' show';
  clearTimeout(el._t);
  el._t = setTimeout(function () { el.className = 'toast'; }, 3500);
}

function tt(key, fallback) {
  return (typeof t === 'function') ? t(key) : (fallback || key);
}

// ---------- SIDEBAR ----------
function toggleSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('sidebarOverlay');
  if (sb) sb.classList.toggle('open');
  if (ov) ov.classList.toggle('show', sb && sb.classList.contains('open'));
}
function closeSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('sidebarOverlay');
  if (sb) sb.classList.remove('open');
  if (ov) ov.classList.remove('show');
}

// ---------- VOLUME ----------
var currentVolume = 70;
function getVolume() {
  var s = localStorage.getItem('guardian_volume');
  if (s !== null) currentVolume = parseInt(s, 10);
  return currentVolume;
}
function setVolume(v) {
  v = Math.max(0, Math.min(100, v));
  currentVolume = v;
  localStorage.setItem('guardian_volume', String(v));
  var f = document.getElementById('volumeFill');
  var l = document.getElementById('volumeValue');
  var r = document.getElementById('volumeRange');
  if (f) f.style.width = v + '%';
  if (l) l.textContent = v + '%';
  if (r) { r.value = v; r.style.setProperty('--p', v + '%'); }
}
function changeVolume(d) {
  var n = getVolume() + d;
  setVolume(n);
  if (n > 0) playBeep(n / 100);
}
function playBeep(vol) {
  try {
    var c = new (window.AudioContext || window.webkitAudioContext)();
    var o = c.createOscillator();
    var g = c.createGain();
    o.connect(g); g.connect(c.destination);
    o.frequency.value = 880;
    g.gain.setValueAtTime(vol * 0.3, c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.01, c.currentTime + 0.12);
    o.start();
    o.stop(c.currentTime + 0.12);
  } catch (e) {}
}
function triggerTestAlert() {
  if (typeof showAlertNotification === 'function') showAlertNotification({ id: 9999, reason: 'TEST' });
  showToast('Test alert — ' + getVolume() + '%', 'success');
}

// ---------- SETTINGS MODAL ----------
function openSettings() {
  var m = document.getElementById('settingsModal');
  if (m) m.classList.add('show');
  refreshSavedLoc();
  var sb = document.getElementById('sidebar');
  if (sb && sb.classList.contains('open')) closeSidebar();
}
function closeSettings() {
  var m = document.getElementById('settingsModal');
  if (m) m.classList.remove('show');
}

function refreshSavedLoc() {
  var out = document.getElementById('savedLoc');
  var wrap = document.getElementById('savedLocWrap');
  var clr = document.getElementById('clearLocBtn');
  var input = document.getElementById('manualLoc');
  var saved = null;
  try { saved = JSON.parse(localStorage.getItem('manualLocation') || 'null'); } catch (e) {}
  if (saved && saved.lat != null && saved.lon != null) {
    if (out) out.textContent = '📌 ' + Number(saved.lat).toFixed(6) + ', ' + Number(saved.lon).toFixed(6);
    if (wrap) wrap.classList.add('has-loc');
    if (clr) clr.classList.remove('hidden');
    if (input && !input.value) input.value = Number(saved.lat).toFixed(6) + ',' + Number(saved.lon).toFixed(6);
  } else {
    if (out) out.textContent = tt('no_location', 'لم يُحدد موقع بعد');
    if (wrap) wrap.classList.remove('has-loc');
    if (clr) clr.classList.add('hidden');
  }
}

function clearManualLocation() {
  localStorage.removeItem('manualLocation');
  if (map && userMarker) { map.removeLayer(userMarker); userMarker = null; }
  var input = document.getElementById('manualLoc');
  if (input) input.value = '';
  refreshSavedLoc();
  showToast(tt('location_removed', 'تمت إزالة الموقع'), 'success');
}

// ---------- DATE ----------
function formatDate(i) {
  if (!i) return '-';
  try { return new Date(i).toLocaleString(); } catch (e) { return i; }
}

// ---------- MAP ----------
var map, markersLayer, allEvents = [], selectedFile = null, lastKnownEventId = 0, userMarker = null;

function initMap() {
  if (typeof L === 'undefined') return;
  map = L.map('map').setView([36.7538, 3.0588], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);

  try {
    var saved = JSON.parse(localStorage.getItem('manualLocation') || 'null');
    if (saved && saved.lat != null && saved.lon != null) {
      userMarker = L.circleMarker([saved.lat, saved.lon], {
        radius: 12, fillColor: '#10b981', color: '#fff', weight: 3, fillOpacity: 0.9
      }).addTo(map).bindPopup('<b>Location</b><br>' + saved.lat.toFixed(6) + ', ' + saved.lon.toFixed(6));
      map.setView([saved.lat, saved.lon], 14);
    }
  } catch (e) {}
}

function renderMap() {
  if (!markersLayer) return;
  markersLayer.clearLayers();
  var v = allEvents.filter(function (e) { return e.gps_latitude && e.gps_longitude; });
  var inf = document.getElementById('mapInfo');
  if (v.length === 0) { if (inf) inf.textContent = '-'; return; }
  if (inf) inf.textContent = v.length + ' pin';
  v.forEach(function (e) {
    var col = (e.qwen_verification && e.qwen_verification.indexOf('مشبوه') >= 0) ? '#ef4444' : '#f59e0b';
    var m = L.circleMarker([e.gps_latitude, e.gps_longitude], {
      radius: 7, fillColor: col, color: '#fff', weight: 2, fillOpacity: 0.85
    });
    m.bindPopup('#' + e.id + ' — Track ' + e.track_id + '<br>' + (e.reason || ''));
    m.eventId = e.id;
    markersLayer.addLayer(m);
  });
  try {
    map.fitBounds(L.latLngBounds(v.map(function (e) { return [e.gps_latitude, e.gps_longitude]; })),
      { padding: [30, 30], maxZoom: 17 });
  } catch (x) {}
}

function zoomTo(id) {
  var e = allEvents.find(function (x) { return x.id === id; });
  if (!e || !e.gps_latitude || !map) return;
  map.setView([e.gps_latitude, e.gps_longitude], 18);
  if (markersLayer) {
    markersLayer.eachLayer(function (m) { if (m.eventId === id) m.openPopup(); });
  }
}

function setManualLocation() {
  var input = document.getElementById('manualLoc');
  if (!input) return;
  var val = input.value.trim();
  if (!val) { showToast(tt('enter_coords', 'أدخل الإحداثيات أولاً'), 'error'); return; }
  var lat = null, lon = null;

  var dmsRegex = /(\d+)\s*°\s*(\d+)\s*['′]\s*([\d.]+)\s*["″]?\s*([NSEW])/gi;
  var m, matches = [];
  while ((m = dmsRegex.exec(val)) !== null) matches.push(m);
  if (matches.length >= 2) {
    var coords = [];
    for (var i = 0; i < 2; i++) {
      var dec = parseFloat(matches[i][1]) + parseFloat(matches[i][2]) / 60 + parseFloat(matches[i][3]) / 3600;
      if (matches[i][4].toUpperCase() === 'S' || matches[i][4].toUpperCase() === 'W') dec = -dec;
      coords.push(dec);
    }
    for (var j = 0; j < 2; j++) {
      var d = matches[j][4].toUpperCase();
      if (d === 'N' || d === 'S') lat = coords[j];
      if (d === 'E' || d === 'W') lon = coords[j];
    }
    if (lat === null || lon === null) { lat = coords[0]; lon = coords[1]; }
  }

  if (lat === null || lon === null) {
    var parts = val.replace(/[،\s]+/g, ',').split(',').filter(function (x) { return x.trim() !== ''; });
    if (parts.length === 2) {
      var a = parseFloat(parts[0].trim());
      var b = parseFloat(parts[1].trim());
      if (!isNaN(a) && !isNaN(b)) { lat = a; lon = b; }
    }
  }

  if (lat === null || lon === null || isNaN(lat) || isNaN(lon)) {
    showToast(tt('bad_format', 'صيغة خاطئة. استخدم 36.7538,3.0588'), 'error');
    return;
  }
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
    showToast(tt('out_of_range', 'القيم خارج النطاق'), 'error');
    return;
  }

  localStorage.setItem('manualLocation', JSON.stringify({ lat: lat, lon: lon }));
  if (map && typeof L !== 'undefined') {
    if (userMarker) map.removeLayer(userMarker);
    userMarker = L.circleMarker([lat, lon], {
      radius: 12, fillColor: '#10b981', color: '#fff', weight: 3, fillOpacity: 0.9
    }).addTo(map).bindPopup('<b>' + tt('map', 'الموقع') + '</b><br>' + lat.toFixed(6) + ', ' + lon.toFixed(6)).openPopup();
    map.setView([lat, lon], 17);
  }
  refreshSavedLoc();
  showToast(lat.toFixed(6) + ', ' + lon.toFixed(6), 'success');
}

// ---------- EVENTS / TABLE ----------
function loadEvents() {
  fetch('/api/events?limit=100000')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      allEvents = d.events || [];
      if (allEvents.length > 0) {
        var n = allEvents[0];
        if (lastKnownEventId > 0 && n.id > lastKnownEventId) {
          var cnt = allEvents.filter(function (e) { return e.id > lastKnownEventId; }).length;
          if (cnt > 0) {
            if (typeof showAlertNotification === 'function') showAlertNotification(n);
            showToast(tt('new_alert', 'تنبيه: سلوك مشبوه!') + ' (+' + cnt + ')', 'error');
          }
        }
        lastKnownEventId = Math.max(lastKnownEventId, n.id);
      }
      var st = document.getElementById('statTotal');
      if (st) st.textContent = d.total;
      updateStats();
      renderTable();
      renderMap();
    })
    .catch(function (e) { console.error(e); });
}

function updateStats() {
  var now = Date.now();
  var h = allEvents.filter(function (e) {
    return e.created_at && (now - new Date(e.created_at).getTime()) < 86400000;
  });
  var a = document.getElementById('statLast24');
  if (a) a.textContent = h.length;
  var b = document.getElementById('statTracks');
  if (b) b.textContent = new Set(allEvents.map(function (e) { return e.track_id; })).size;
  var c2 = document.getElementById('statLast');
  if (c2 && allEvents.length > 0) c2.textContent = formatDate(allEvents[0].created_at);
}

function renderTable() {
  var tb = document.getElementById('eventsBody');
  if (!tb) return;
  var inf = document.getElementById('tableInfo');
  if (inf) inf.textContent = allEvents.length + ' ' + tt('events_count', 'حدث');

  if (allEvents.length === 0) {
    tb.innerHTML = '<tr><td colspan="8"><div class="empty"><span class="empty-ico">🛡️</span>' +
      '<div class="empty-title">' + tt('no_events', 'لا توجد أحداث') + '</div>' +
      '<div class="muted">' + tt('empty_hint', 'ارفع فيديو لبدء التحليل') + '</div></div></td></tr>';
    return;
  }

  tb.innerHTML = allEvents.map(function (e) {
    var lat = e.gps_latitude ? e.gps_latitude.toFixed(5) : '-';
    var lon = e.gps_longitude ? e.gps_longitude.toFixed(5) : '-';
    var dist = e.gps_distance_m ? e.gps_distance_m.toFixed(1) + 'm' : '-';

    var clip = '<span class="muted">—</span>';
    if (e.clip_path) {
      var fn = e.clip_path.split(/[\\/]/).pop();
      clip = '<a href="/clips/' + encodeURIComponent(fn) + '" target="_blank" class="badge badge-info" onclick="event.stopPropagation()">🎬 ' +
        tt('watch', 'مشاهدة') + '</a>';
    }

    var ver;
    if (e.qwen_verification) {
      var raw = String(e.qwen_verification);
      var ft = raw.replace(/"/g, '&quot;');
      if (raw.indexOf('مشبوه') !== -1) {
        ver = '<span class="badge badge-alert" title="' + ft + '">🚨 ' + tt('verdict_suspicious', 'مشبوه') + '</span>';
      } else if (raw.indexOf('طبيعي') !== -1 || raw.indexOf('طبيعي'.replace('ي', 'ي')) !== -1) {
        ver = '<span class="badge badge-ok" title="' + ft + '">✅ ' + tt('verdict_normal', 'طبيعي') + '</span>';
      } else {
        ver = '<span class="badge badge-violet" title="' + ft + '">🤖 ' + raw.slice(0, 30) + '</span>';
      }
    } else {
      ver = '<button class="btn btn-violet" style="padding:4px 9px;font-size:10.5px" onclick="event.stopPropagation(); startVerify(' + e.id + ')" id="vbtn-' + e.id + '">🤖 ' +
        tt('verify', 'تحقق AI') + '</button>';
    }

    return '<tr onclick="zoomTo(' + e.id + ')">' +
      '<td class="mono">' + e.id + '</td>' +
      '<td>' + formatDate(e.created_at) + '</td>' +
      '<td><span class="badge badge-info">#' + e.track_id + '</span></td>' +
      '<td class="mono">' + lat + ', ' + lon + '</td>' +
      '<td>' + dist + '</td>' +
      '<td><span class="badge badge-alert">' + (e.reason || '-') + '</span></td>' +
      '<td>' + clip + '</td>' +
      '<td>' + ver + '</td>' +
      '</tr>';
  }).join('');
}

function startVerify(id) {
  var b = document.getElementById('vbtn-' + id);
  if (b) { b.disabled = true; b.textContent = '…'; }
  fetch('/api/verify/' + id, { method: 'POST' }).then(function () {
    var a = 0;
    var iv = setInterval(function () {
      a++;
      fetch('/api/events/' + id).then(function (r) { return r.json(); }).then(function (e) {
        if (e.qwen_verification) { clearInterval(iv); loadEvents(); }
        if (a >= 60) clearInterval(iv);
      });
    }, 5000);
  });
}

function clearAll() {
  if (!confirm(tt('clear_confirm', 'مسح كل الأحداث؟'))) return;
  fetch('/api/events', { method: 'DELETE' }).then(function () {
    lastKnownEventId = 0;
    showToast(tt('cleared', 'تم المسح'), 'success');
    loadEvents();
  });
}

// ---------- REFRESH ----------
function refreshData(ev) {
  if (ev) { ev.preventDefault(); ev.stopPropagation(); }
  var btn = document.getElementById('refreshBtn');
  var tbody = document.getElementById('eventsBody');
  var origHTML = btn ? btn.innerHTML : '';

  if (btn) { btn.disabled = true; btn.innerHTML = '⏳ ' + new Date().toLocaleTimeString(); }
  if (tbody && allEvents.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8"><div class="empty"><span class="empty-ico">⏳</span>' +
      '<div class="empty-title">' + tt('loading', 'جاري التحميل...') + '</div></div></td></tr>';
  }
  if (tbody) {
    tbody.style.transition = 'background .3s';
    tbody.style.background = 'rgba(16,185,129,.14)';
    setTimeout(function () { tbody.style.background = ''; }, 600);
  }
  showToast('🔄 ' + tt('refresh', 'تحديث'), 'info');

  var onStats = typeof loadStats === 'function';
  try { if (onStats) loadStats(); else loadEvents(); } catch (e) { console.error(e); }

  setTimeout(function () {
    if (btn) { btn.disabled = false; btn.innerHTML = origHTML; }
    showToast('✅ ' + (onStats ? tt('stats_updated', 'تم التحديث') : (allEvents.length + ' ' + tt('events_count', 'حدث'))), 'success');
  }, 2000);
}

// ---------- PDF ----------
function downloadPDF() {
  var btn = document.getElementById('pdfBtn');
  var origHTML = btn ? btn.innerHTML : '';
  if (btn) { btn.disabled = true; btn.innerHTML = '⏳ …'; }
  showToast('📄 ' + tt('generating_pdf', 'جاري إنشاء التقرير...'), 'info');

  var lang = (typeof CURRENT_LANG !== 'undefined') ? CURRENT_LANG : (localStorage.getItem('guardian_lang') || 'ar');
  fetch('/api/reports/pdf?lang=' + encodeURIComponent(lang))
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.blob();
    })
    .then(function (blob) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'guardian_eye_report_' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
      if (btn) { btn.disabled = false; btn.innerHTML = origHTML; }
      showToast('✅ ' + tt('pdf_done', 'تم تحميل التقرير'), 'success');
    })
    .catch(function (e) {
      if (btn) { btn.disabled = false; btn.innerHTML = origHTML; }
      showToast('❌ ' + tt('pdf_failed', 'فشل التقرير') + ': ' + e.message, 'error');
    });
}

// ---------- SUBSCRIBE ----------
async function subscribe() {
  var btn = document.getElementById('subscribeBtn');
  var orig = btn ? btn.innerHTML : '';
  if (btn) { btn.disabled = true; btn.innerHTML = '…'; }
  showToast(tt('redirecting', 'جاري التحويل...'), 'info');
  try {
    var resp = await fetch('/api/subscribe', { method: 'POST' });
    var data = await resp.json();
    if (data.checkout_url) { window.location.href = data.checkout_url; return; }
    if (btn) { btn.disabled = false; btn.innerHTML = orig; }
    showToast('❌ ' + (data.error || 'failed'), 'error');
  } catch (e) {
    if (btn) { btn.disabled = false; btn.innerHTML = orig; }
    showToast('❌ ' + e.message, 'error');
  }
}

// ---------- UPLOAD ----------
function openUploadModal() {
  var m = document.getElementById('uploadModal');
  if (m) m.classList.add('show');
  if (typeof requestNotificationPermission === 'function') requestNotificationPermission();
}
function closeUploadModal() {
  var m = document.getElementById('uploadModal');
  if (m) m.classList.remove('show');
  selectedFile = null;
  var f = document.getElementById('fileName'); if (f) { f.textContent = ''; f.classList.add('hidden'); }
  var s = document.getElementById('startUploadBtn'); if (s) s.disabled = true;
  var p = document.getElementById('progressBar'); if (p) p.classList.remove('show');
  var pf = document.getElementById('progressFill'); if (pf) pf.style.width = '0%';
  var fi = document.getElementById('fileInput'); if (fi) fi.value = '';
}
function handleFile(file) {
  if (!file.type.startsWith('video/')) { showToast(tt('select_video', 'اختر فيديو'), 'error'); return; }
  selectedFile = file;
  var f = document.getElementById('fileName');
  if (f) {
    f.textContent = '🎬 ' + tt('upload_selected', 'تم اختيار:') + ' ' + file.name +
      ' (' + (file.size / 1024 / 1024).toFixed(2) + ' MB)';
    f.classList.remove('hidden');
  }
  var s = document.getElementById('startUploadBtn');
  if (s) s.disabled = false;
}
function startUpload() {
  if (!selectedFile) return;
  var b = document.getElementById('startUploadBtn');
  var bar = document.getElementById('progressBar');
  var fill = document.getElementById('progressFill');
  if (b) b.disabled = true;
  if (bar) bar.classList.add('show');
  if (fill) fill.style.width = '20%';
  var fd = new FormData();
  fd.append('video', selectedFile);
  showToast(tt('upload_processing', 'جاري معالجة الفيديو...'), 'info');
  fetch('/api/detect', { method: 'POST', body: fd })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (fill) fill.style.width = '100%';
      if (d.error) {
        showToast(tt('upload_failed', 'فشل الرفع:') + ' ' + d.error, 'error');
        if (b) b.disabled = false;
      } else {
        var cnt = (d.suspicious_events || []).length;
        showToast('✅ ' + tt('upload_done', 'اكتملت المعالجة! الأحداث:') + ' ' + cnt, 'success');
        loadEvents();
        setTimeout(closeUploadModal, 1500);
      }
    })
    .catch(function (e) {
      showToast('❌ ' + e.message, 'error');
      if (b) b.disabled = false;
    });
}

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', function () {
  // sidebar
  var hb = document.getElementById('hamburger');
  if (hb) hb.addEventListener('click', toggleSidebar);
  var ov = document.getElementById('sidebarOverlay');
  if (ov) ov.addEventListener('click', closeSidebar);

  // language (i18n.js handles switcher binding via initLanguage)
  if (typeof initLanguage === 'function') {
    try { initLanguage(); } catch (e) { console.warn('initLanguage:', e); }
  }

  // map
  try { if (typeof L !== 'undefined') initMap(); } catch (e) { console.error('initMap:', e); }

  // volume
  try { setVolume(getVolume()); } catch (e) {}
  try { refreshSavedLoc(); } catch (e) {}
  try { if (typeof requestNotificationPermission === 'function') requestNotificationPermission(); } catch (e) {}

  // buttons (single binding — no inline double binding)
  var binds = {
    volUp: function () { changeVolume(10); },
    volDown: function () { changeVolume(-10); },
    testAlertBtn: triggerTestAlert,
    clearBtn: clearAll,
    uploadBtn: openUploadModal,
    cancelUpload: closeUploadModal,
    startUploadBtn: startUpload,
    setLocBtn: setManualLocation,
    openSettingsBtn: openSettings,
    closeSettingsBtn: closeSettings,
    clearLocBtn: clearManualLocation,
    testSoundBtn: function () {
      var v = getVolume();
      if (v <= 0) { showToast(tt('volume_zero', 'الصوت مكتوم'), 'error'); return; }
      playBeep(v / 100);
      showToast('🎵 ' + v + '%', 'success');
    }
  };
  Object.keys(binds).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('click', binds[id]);
  });

  // settings modal: backdrop + ESC
  var sm = document.getElementById('settingsModal');
  if (sm) sm.addEventListener('click', function (e) { if (e.target === sm) closeSettings(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeSettings();
  });

  // volume range slider (live update, beep only on release)
  var vr = document.getElementById('volumeRange');
  if (vr) {
    vr.style.setProperty('--p', getVolume() + '%');
    vr.addEventListener('input', function () { setVolume(parseInt(vr.value, 10)); });
    vr.addEventListener('change', function () { var n = parseInt(vr.value, 10); if (n > 0) playBeep(n / 100); });
  }

  // manual location enter key
  var ml = document.getElementById('manualLoc');
  if (ml) ml.addEventListener('keydown', function (e) { if (e.key === 'Enter') setManualLocation(); });

  // drop zone
  try {
    var dz = document.getElementById('dropZone');
    var fi = document.getElementById('fileInput');
    if (dz && fi) {
      dz.addEventListener('click', function () { fi.click(); });
      dz.addEventListener('dragover', function (e) { e.preventDefault(); dz.classList.add('dragover'); });
      dz.addEventListener('dragleave', function () { dz.classList.remove('dragover'); });
      dz.addEventListener('drop', function (e) {
        e.preventDefault();
        dz.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
      });
      fi.addEventListener('change', function (e) {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
      });
    }
  } catch (e) {}

  // close modal on backdrop click
  var um = document.getElementById('uploadModal');
  if (um) um.addEventListener('click', function (e) { if (e.target === um) closeUploadModal(); });

  // initial data load (dashboard only)
  if (document.getElementById('eventsBody')) {
    loadEvents();
    setInterval(loadEvents, 15000);
  }
});
