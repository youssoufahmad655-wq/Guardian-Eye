const TRANSLATIONS = window.TRANSLATIONS = {
    ar: {
        title: "Guardian Eye — عين الحارس",
        total_events: "إجمالي الأحداث", events_count: "حدث",
        last_24h: "آخر 24 ساعة",
        unique_tracks: "أشخاص فريدون",
        last_event: "آخر حدث",
        map: "الخريطة",
        events_log: "سجل الأحداث",
        id: "#", time: "الوقت", track: "الشخص", gps: "GPS",
        distance: "المسافة", type: "النوع", evidence: "الدليل", ai_check: "تحقق AI",
        refresh: "تحديث", clear: "مسح الكل", logout: "خروج",
        stats: "إحصائيات", upload: "رفع فيديو", report: "تقرير CSV",
        set_location: "تعيين الموقع", location_placeholder: "36.7538,3.0588",
        watch: "مشاهدة", verify: "تحقق AI", verifying: "جاري...",
        upload_title: "رفع فيديو للتحليل",
        upload_drop: "اسحب وأفلت الفيديو هنا أو انقر للاختيار",
        upload_selected: "تم اختيار:", upload_start: "بدء التحليل", upload_cancel: "إلغاء",
        upload_processing: "جاري معالجة الفيديو...",
        upload_done: "اكتملت المعالجة! الأحداث:", upload_failed: "فشل الرفع:",
        no_events: "لا توجد أحداث", loading: "جاري التحميل...",
        new_alert: "🚨 تنبيه: سلوك مشبوه!",
        no_ai: "لم يتم التحقق بعد",
        clear_confirm: "مسح كل الأحداث؟",
        lang_ar: "العربية", lang_en: "English", lang_fr: "Français",
        verdict_suspicious: "مشبوه", verdict_normal: "طبيعي", select_video: "اختر فيديو",
        stats_title: "📊 الإحصائيات",
        back_dashboard: "لوحة التحكم",
        chart_hourly: "⏰ الأحداث حسب الساعة",
        chart_reasons: "⚠️ توزيع أنواع السلوك",
        chart_tracks: "👤 أكثر 5 أشخاص",
        refresh_now: "تحديث الآن",
        events_unit: "حدث",
        behavior_types: "أنواع السلوك",
        recurring_visitors: "زوار متكررون",
        chart_summary: "📈 ملخص",
        chart_hint: "يتم تحديث الإحصائيات عند كل زيارة.",
        pdf_report: "تقرير PDF",
        subscribe: "اشتراك"
    },
    en: {
        title: "Guardian Eye — Dashboard",
        total_events: "Total Events", events_count: "events", last_24h: "Last 24h",
        unique_tracks: "Unique Tracks", last_event: "Last Event",
        map: "Map", events_log: "Events Log",
        id: "#", time: "Time", track: "Track", gps: "GPS",
        distance: "Distance", type: "Type", evidence: "Evidence", ai_check: "AI Check",
        refresh: "Refresh", clear: "Clear All", logout: "Logout",
        stats: "Stats", upload: "Upload Video", report: "CSV Report",
        set_location: "Set Location", location_placeholder: "36.7538,3.0588",
        watch: "Watch", verify: "AI Check", verifying: "Working...",
        upload_title: "Upload Video for Analysis",
        upload_drop: "Drag & drop video here or click to browse",
        upload_selected: "Selected:", upload_start: "Start Analysis", upload_cancel: "Cancel",
        upload_processing: "Processing video...",
        upload_done: "Analysis complete! Events:", upload_failed: "Upload failed:",
        no_events: "No events", loading: "Loading...",
        new_alert: "🚨 Alert: Suspicious behavior!",
        no_ai: "Not verified yet",
        clear_confirm: "Clear all events?",
        lang_ar: "العربية", lang_en: "English", lang_fr: "Français",
        verdict_suspicious: "Suspicious", verdict_normal: "Normal", select_video: "Please select a video",
        stats_title: "📊 Statistics",
        back_dashboard: "Dashboard",
        chart_hourly: "⏰ Events by Hour",
        chart_reasons: "⚠️ Behavior Distribution",
        chart_tracks: "👤 Top 5 Suspicious Persons",
        refresh_now: "Refresh Now",
        events_unit: "events",
        behavior_types: "Behavior Types",
        recurring_visitors: "Recurring Visitors",
        chart_summary: "📈 Summary",
        chart_hint: "Statistics refresh on every visit.",
        subscribe: "Subscribe"
    },
    fr: {
        title: "Guardian Eye — Tableau de bord",
        total_events: "Total des événements", events_count: "événements", last_24h: "Dernières 24h",
        unique_tracks: "Personnes uniques", last_event: "Dernier événement",
        map: "Carte", events_log: "Journal des événements",
        id: "#", time: "Heure", track: "Piste", gps: "GPS",
        distance: "Distance", type: "Type", evidence: "Preuve", ai_check: "Vérif. IA",
        refresh: "Actualiser", clear: "Tout effacer", logout: "Déconnexion",
        stats: "Statistiques", upload: "Téléverser vidéo", report: "Rapport CSV",
        set_location: "Définir l'emplacement", location_placeholder: "36.7538,3.0588",
        watch: "Voir", verify: "Vérif. IA", verifying: "En cours...",
        upload_title: "Téléverser une vidéo pour analyse",
        upload_drop: "Glissez-déposez la vidéo ici ou cliquez",
        upload_selected: "Sélectionné :", upload_start: "Démarrer l'analyse", upload_cancel: "Annuler",
        upload_processing: "Traitement en cours...",
        upload_done: "Analyse terminée ! Événements :", upload_failed: "Échec :",
        no_events: "Aucun événement", loading: "Chargement...",
        new_alert: "🚨 Alerte : comportement suspect !",
        no_ai: "Pas encore vérifié",
        clear_confirm: "Effacer tous les événements ?",
        lang_ar: "العربية", lang_en: "English", lang_fr: "Français",
        verdict_suspicious: "Suspect", verdict_normal: "Normal", select_video: "Veuillez sélectionner une vidéo",
        stats_title: "📊 Statistiques",
        back_dashboard: "Tableau de bord",
        chart_hourly: "⏰ Événements par heure",
        chart_reasons: "⚠️ Répartition des comportements",
        chart_tracks: "👤 Top 5 personnes suspectes",
        refresh_now: "Actualiser",
        events_unit: "événements",
        behavior_types: "Types de comportement",
        recurring_visitors: "Visiteurs récurrents",
        chart_summary: "📈 Résumé",
        chart_hint: "Les statistiques sont actualisées à chaque visite.",
        subscribe: "S'abonner"
    }
};

let CURRENT_LANG = localStorage.getItem('guardian_lang') || 'ar';

function t(key) {
    return (TRANSLATIONS[CURRENT_LANG] && TRANSLATIONS[CURRENT_LANG][key]) || key;
}

function applyLanguage(lang) {
    CURRENT_LANG = lang;
    localStorage.setItem('guardian_lang', lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = (lang === 'ar') ? 'rtl' : 'ltr';

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
            el.placeholder = t(key);
        } else {
            el.textContent = t(key);
        }
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        el.title = t(el.dataset.i18nTitle);
    });

    // أعد رسم الجدول إذا كانت الدالة متاحة
    if (typeof renderTable === 'function' && typeof allEvents !== 'undefined') {
        renderTable();
    }
}

function initLanguage() {
    applyLanguage(CURRENT_LANG);
    const switcher = document.getElementById('langSwitcher');
    if (switcher) {
        switcher.value = CURRENT_LANG;
        switcher.addEventListener('change', (e) => applyLanguage(e.target.value));
    }
}

// تنبيه صوتي بـ Web Audio API (بدون ملف خارجي)
function playAlertSound() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.frequency.setValueAtTime(660, ctx.currentTime + 0.15);
        osc.frequency.setValueAtTime(880, ctx.currentTime + 0.30);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6);
        osc.start();
        osc.stop(ctx.currentTime + 0.6);
    } catch (e) { console.warn('Audio not available', e); }
}

async function requestNotificationPermission() {
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') {
        try { await Notification.requestPermission(); } catch (e) {}
    }
}

function showAlertNotification(event) {
    playAlertSound();

    // وميض الشاشة
    document.body.classList.add('flash-alert');
    setTimeout(() => document.body.classList.remove('flash-alert'), 1500);

    // إشعار المتصفح
    if (Notification.permission === 'granted') {
        try {
            new Notification(t('new_alert'), {
                body: `#${event.id} — ${event.reason || 'Suspicious'} — ${new Date(event.created_at || Date.now()).toLocaleTimeString()}`,
                tag: 'guardian-alert-' + event.id,
                requireInteraction: false,
            });
        } catch (e) { console.warn(e); }
    }
}
