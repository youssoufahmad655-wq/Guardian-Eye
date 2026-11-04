# -*- coding: utf-8 -*-
import os
from datetime import datetime
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display


class EventPDFReport:
    """Generates a professional Arabic PDF report of security events."""

    def __init__(self, lang='ar'):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=12)
        self.pdf.set_margins(8, 8, 8)
        self.lang = lang

        # Find an Arabic-capable font
        candidates = [
            r'C:\Windows\Fonts\tahoma.ttf',
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\segoeui.ttf',
            r'C:\Windows\Fonts\DejaVuSans.ttf',
        ]
        font_path = next((p for p in candidates if os.path.exists(p)), None)
        if not font_path:
            raise FileNotFoundError("No Arabic font found in C:\\Windows\\Fonts")

        self.font_name = 'GuardianFont'
        self.pdf.add_font(self.font_name, '', font_path)

    def _ar(self, text):
        """Reshape Arabic text for proper RTL display."""
        if not text:
            return ''
        try:
            reshaped = arabic_reshaper.reshape(str(text))
            return get_display(reshaped)
        except Exception:
            return str(text)

    def _header(self, title):
        self.pdf.set_font(self.font_name, size=14)
        self.pdf.set_text_color(59, 130, 246)
        self.pdf.cell(0, 12, self._ar('GUARDIAN EYE'), align='C',
                      new_x='LMARGIN', new_y='NEXT')

        self.pdf.set_font(self.font_name, size=9)
        self.pdf.set_text_color(150, 150, 150)
        self.pdf.cell(0, 8, self._ar('AI-Powered Retail Security'), align='C',
                      new_x='LMARGIN', new_y='NEXT')

        self.pdf.ln(5)
        self.pdf.set_font(self.font_name, size=18)
        self.pdf.set_text_color(15, 23, 42)
        self.pdf.cell(0, 12, self._ar(title), align='C',
                      new_x='LMARGIN', new_y='NEXT')
        self.pdf.ln(8)

    def _stats_box(self, total, suspicious, normal, recurring):
        labels = {
            'ar': ('إجمالي الأحداث', 'مشبوهة', 'طبيعية', 'زوار متكررون'),
            'en': ('Total Events', 'Suspicious', 'Normal', 'Recurring'),
            'fr': ('Total', 'Suspects', 'Normaux', 'Récurrents'),
        }[self.lang]
        values = [total, suspicious, normal, recurring]
        colors = [(59,130,246), (239,68,68), (34,197,94), (245,158,11)]

        box_w = (self.pdf.w - 20) / 4
        start_x = 10
        y = self.pdf.get_y()

        for i, (label, val, color) in enumerate(zip(labels, values, colors)):
            x = start_x + i * box_w
            self.pdf.set_fill_color(*color)
            self.pdf.set_text_color(255, 255, 255)
            self.pdf.set_font(self.font_name, size=9)
            self.pdf.set_xy(x, y)
            self.pdf.cell(box_w - 2, 8, self._ar(label), align='C', fill=True)
            self.pdf.set_font(self.font_name, size=13)
            self.pdf.set_xy(x, y + 10)
            self.pdf.cell(box_w - 2, 11, str(val), align='C', fill=True)

        self.pdf.set_y(y + 22)
        self.pdf.set_text_color(0, 0, 0)

    def _table(self, events):
        titles = {
            'ar': 'سجل الأحداث التفصيلي',
            'en': 'Detailed Events Log',
            'fr': 'Journal détaillé des événements',
        }
        self.pdf.set_font(self.font_name, size=11)
        self.pdf.set_text_color(15, 23, 42)
        self.pdf.cell(0, 7, self._ar(titles[self.lang]),
                      new_x='LMARGIN', new_y='NEXT')
        self.pdf.ln(1)

        headers = {
            'ar': ['#', 'الوقت', 'الشخص', 'النوع', 'GPS', 'AI'],
            'en': ['#', 'Time', 'Track', 'Type', 'GPS', 'AI'],
            'fr': ['#', 'Heure', 'Piste', 'Type', 'GPS', 'IA'],
        }[self.lang]

        widths = [10, 32, 12, 28, 48, 24]

        # Header row
        self.pdf.set_fill_color(51, 65, 85)
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.set_font(self.font_name, size=9)
        for h, w in zip(headers, widths):
            self.pdf.cell(w, 7, self._ar(h), border=1, fill=True, align='C')
        self.pdf.ln()

        # Data rows
        self.pdf.set_font(self.font_name, size=7)
        self.pdf.set_text_color(30, 30, 30)

        for idx, e in enumerate(events):
            if self.pdf.get_y() > 280:
                self.pdf.add_page()

            fill = (idx % 2 == 0)
            self.pdf.set_fill_color(248, 250, 252) if fill else self.pdf.set_fill_color(255, 255, 255)

            reason = e.get('reason') or '-'
            if len(str(reason)) > 22:
                reason = str(reason)[:22] + '…'

            ai = e.get('qwen_verification')
            if ai:
                if 'مشبوه' in str(ai):
                    ai_text = 'مشبوه' if self.lang == 'ar' else 'Suspicious'
                elif 'طبيعي' in str(ai):
                    ai_text = 'طبيعي' if self.lang == 'ar' else 'Normal'
                else:
                    ai_text = str(ai)[:12]
            else:
                ai_text = '-'

            lat = e.get('gps_latitude')
            lon = e.get('gps_longitude')
            gps = f'{lat:.4f}, {lon:.4f}' if (lat and lon) else '-'

            created = e.get('created_at') or ''
            time_str = created[11:16] if len(created) >= 16 else str(created)[:10]

            row = [
                str(e.get('id', '')),
                time_str,
                '#' + str(e.get('track_id', '')),
                reason,
                gps,
                ai_text,
            ]

            for val, w in zip(row, widths):
                self.pdf.cell(w, 5, self._ar(val), border=1, fill=True, align='C')
            self.pdf.ln()

    def _footer(self):
        self.pdf.set_y(-10)
        self.pdf.set_font(self.font_name, size=7)
        self.pdf.set_text_color(120, 120, 120)
        date = datetime.now().strftime('%Y-%m-%d %H:%M')
        page = self.pdf.page_no()
        footer = f'{date}  |  Page {page}  |  Guardian Eye'
        self.pdf.cell(0, 6, self._ar(footer), align='C')

    def generate(self, events, output_path):
        total = len(events)
        suspicious = sum(1 for e in events if e.get('qwen_verification') and 'مشبوه' in str(e.get('qwen_verification')))
        normal = sum(1 for e in events if e.get('qwen_verification') and 'طبيعي' in str(e.get('qwen_verification')))
        recurring = sum(1 for e in events if e.get('is_recurring'))

        titles = {
            'ar': 'تقرير الأحداث الأمنية',
            'en': 'Security Events Report',
            'fr': 'Rapport des Événements de Sécurité',
        }

        self.pdf.add_page()
        self._header(titles[self.lang])
        self._stats_box(total, suspicious, normal, recurring)
        self._table(events)
        self._footer()
        self.pdf.output(output_path)
        return output_path
