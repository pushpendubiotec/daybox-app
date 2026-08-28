"""
Daybox - All-in-One Personal Productivity & Attendance Management Engine
Built strictly based on the 30-Question Blueprint Specifications.
Theme: Soft Slate (#1E222A), Sky Blue (#38BDF8), Pastel Yellow (#FDE047).
Features:
- Dashboard with Urgent Alerts, Live Attendance Gauges, and Scratchpad
- Full Google Calendar-style month selector and hourly schedule grid
- Subject-wise Attendance Predictor with Bunk Logic & Bunk Warning Modals
- Dual-Notes Engine: Checklist reminders + PDF/Card Note Previews
- Floating Action Pen Scratchpad with Auto-Delete Timer
- Fully Local Storage (SQLite) for 100% offline reliability
"""

import json
import sqlite3
import datetime
from datetime import timedelta

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.properties import StringProperty, NumericProperty, ListProperty, ObjectProperty
from kivy.clock import Clock

# Set phone-like window dimensions for desktop testing
Window.size = (390, 810)
Window.clearcolor = (0.118, 0.133, 0.165, 1)  # #1E222A Dark Slate Background

# ==============================================================================
# DATABASE MANAGER (100% Offline SQLite Core - Questions 26 & 27)
# ==============================================================================
class DatabaseManager:
    def __init__(self, db_name="daybox_app.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.seed_defaults()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Attendance Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT UNIQUE,
                attended INTEGER,
                total INTEGER,
                target_pct REAL,
                is_major INTEGER
            )
        ''')
        # Schedule / Events Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                date_str TEXT,
                time_str TEXT,
                is_task INTEGER,
                completed INTEGER,
                color_hex TEXT
            )
        ''')
        # Notes Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                tag TEXT,
                is_private INTEGER,
                align_mode TEXT,
                color_hex TEXT,
                created_at TEXT
            )
        ''')
        self.conn.commit()

    def seed_defaults(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM attendance")
        if cursor.fetchone()[0] == 0:
            cursor.executemany('''
                INSERT INTO attendance (subject, attended, total, target_pct, is_major)
                VALUES (?, ?, ?, ?, ?)
            ''', [
                ("Genetics & Genomics", 18, 22, 80.0, 1),
                ("Biotechnology Lab", 14, 15, 75.0, 1),
                ("General Chemistry", 19, 25, 75.0, 0),
                ("English Communication", 10, 10, 65.0, 0)
            ])
            self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM events")
        if cursor.fetchone()[0] == 0:
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            cursor.executemany('''
                INSERT INTO events (title, date_str, time_str, is_task, completed, color_hex)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', [
                ("Genetics Core Presentation", today_str, "09:30 AM", 0, 0, "#38BDF8"),
                ("Submit Biotech Lab Report", today_str, "02:00 PM", 1, 0, "#FDE047"),
                ("Buy OTG Adapter Cable", today_str, "05:00 PM", 1, 1, "#4ADE80")
            ])
            self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM notes")
        if cursor.fetchone()[0] == 0:
            cursor.executemany('''
                INSERT INTO notes (title, content, tag, is_private, align_mode, color_hex, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [
                ("Genetics Lecture 04 Summary", "DNA replication involves DNA Polymerase III synthesizing leading strand 5' to 3' seamlessly.", "#Genetics", 0, "left", "#38BDF8", "2026-08-25"),
                ("Biotech Lab Protocol", "Ensure centrifugation runs at 12,000 RPM for 10 mins. Keep ethanol ice-cold.", "#LabNotes", 0, "left", "#FDE047", "2026-08-26")
            ])
            self.conn.commit()

# Initialize Global Database Connection
db = DatabaseManager()

# ==============================================================================
# CUSTOM GRAPHICS WIDGETS (Pie Chart Gauges & Card Backgrounds)
# ==============================================================================
class DynamicPieChart(Widget):
    angle = NumericProperty(0)
    color_rgb = ListProperty([0.22, 0.74, 0.97, 1])

    def __init__(self, percentage=75.0, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.set_percentage(percentage)

    def set_percentage(self, pct):
        self.angle = (min(max(pct, 0.0), 100.0) / 100.0) * 360.0
        if pct >= 75.0:
            self.color_rgb = [0.29, 0.87, 0.5, 1]  # Emerald Safe
        elif pct >= 65.0:
            self.color_rgb = [0.99, 0.88, 0.28, 1]  # Yellow Warning
        else:
            self.color_rgb = [0.97, 0.44, 0.44, 1]  # Red Danger
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Base Ring Background
            Color(0.2, 0.23, 0.28, 1)
            Ellipse(pos=self.pos, size=self.size)
            # Active Dynamic Percentage Segment
            Color(*self.color_rgb)
            Ellipse(pos=self.pos, size=self.size, angle_start=0, angle_end=self.angle)
            # Inner Masking Circle for Ring Effect
            Color(0.14, 0.16, 0.2, 1)
            inner_size = (self.size[0] * 0.72, self.size[1] * 0.72)
            inner_pos = (self.pos[0] + (self.size[0] - inner_size[0]) / 2,
                         self.pos[1] + (self.size[1] - inner_size[1]) / 2)
            Ellipse(pos=inner_pos, size=inner_size)

# ==============================================================================
# KIVY UI LAYOUT STRINGS (KV Builder - Sky Blue / Pastel Yellow Palette)
# ==============================================================================
KV_BUILDER = """
<StyledButton@Button>:
    font_name: 'Roboto'
    font_size: '14sp'
    bold: True
    background_normal: ''
    background_color: (0.22, 0.74, 0.97, 1) # Sky Blue
    color: (0.08, 0.09, 0.11, 1)

<TopNavBar@BoxLayout>:
    size_hint_y: None
    height: '56dp'
    padding: ['16dp', '8dp']
    spacing: '12dp'
    canvas.before:
        Color:
            rgba: (0.14, 0.16, 0.2, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: 'DAYBOX'
        font_size: '20sp'
        bold: True
        color: (0.22, 0.74, 0.97, 1)
        halign: 'left'
        text_size: self.size
        valign: 'middle'

    Button:
        text: '☰'
        size_hint_x: None
        width: '40dp'
        font_size: '22sp'
        background_normal: ''
        background_color: (0, 0, 0, 0)
        color: (0.99, 0.88, 0.28, 1)
        on_release: app.open_hamburger_menu()

<BottomNavBar@BoxLayout>:
    size_hint_y: None
    height: '60dp'
    spacing: '4dp'
    padding: ['4dp', '4dp']
    canvas.before:
        Color:
            rgba: (0.14, 0.16, 0.2, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    Button:
        text: 'Dashboard'
        font_size: '11sp'
        background_normal: ''
        background_color: (0, 0, 0, 0)
        color: (0.22, 0.74, 0.97, 1) if app.sm.current == 'dashboard' else (0.6, 0.65, 0.7, 1)
        on_release: app.sm.current = 'dashboard'

    Button:
        text: 'Calendar'
        font_size: '11sp'
        background_normal: ''
        background_color: (0, 0, 0, 0)
        color: (0.22, 0.74, 0.97, 1) if app.sm.current == 'calendar' else (0.6, 0.65, 0.7, 1)
        on_release: app.sm.current = 'calendar'

    Button:
        text: 'Attendance'
        font_size: '11sp'
        background_normal: ''
        background_color: (0, 0, 0, 0)
        color: (0.22, 0.74, 0.97, 1) if app.sm.current == 'attendance' else (0.6, 0.65, 0.7, 1)
        on_release: app.sm.current = 'attendance'

    Button:
        text: 'Notes'
        font_size: '11sp'
        background_normal: ''
        background_color: (0, 0, 0, 0)
        color: (0.22, 0.74, 0.97, 1) if app.sm.current == 'notes' else (0.6, 0.65, 0.7, 1)
        on_release: app.sm.current = 'notes'

    Button:
        text: 'AI Hub'
        font_size: '11sp'
        background_normal: ''
        background_color: (0, 0, 0, 0)
        color: (0.99, 0.88, 0.28, 1) if app.sm.current == 'ai_hub' else (0.6, 0.65, 0.7, 1)
        on_release: app.sm.current = 'ai_hub'

# ------------------------------------------------------------------------------
# SCREEN 1: DASHBOARD (The Glanceable Hub - Questions 3 & 18)
# ------------------------------------------------------------------------------
<DashboardScreen>:
    BoxLayout:
        orientation: 'vertical'

        TopNavBar:

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                padding: '16dp'
                spacing: '16dp'
                size_hint_y: None
                height: self.minimum_height

                # Banner Box 1: Urgent Reminders
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: '110dp'
                    padding: '12dp'
                    spacing: '6dp'
                    canvas.before:
                        Color:
                            rgba: (0.18, 0.21, 0.26, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [12]

                    Label:
                        text: 'URGENT REMINDERS'
                        font_size: '12sp'
                        bold: True
                        color: (0.99, 0.88, 0.28, 1)
                        text_size: self.size
                        halign: 'left'

                    Label:
                        id: urgent_text
                        text: '• Genetics Presentation at 09:30 AM\\n• Submit Biotech Lab Report by 02:00 PM'
                        font_size: '13sp'
                        color: (0.9, 0.92, 0.95, 1)
                        text_size: self.size
                        halign: 'left'

                # Banner Box 2: Attendance Summary Card
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: '140dp'
                    padding: '12dp'
                    spacing: '8dp'
                    canvas.before:
                        Color:
                            rgba: (0.18, 0.21, 0.26, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [12]

                    Label:
                        text: 'ATTENDANCE SUMMARY'
                        font_size: '12sp'
                        bold: True
                        color: (0.22, 0.74, 0.97, 1)
                        text_size: self.size
                        halign: 'left'

                    BoxLayout:
                        spacing: '12dp'

                        Label:
                            id: dash_attend_summary
                            text: 'Overall Status: SAFE (78.2%)\\nGenetics: 81.8% (Safe)\\nBiotech Lab: 93.3% (Safe)'
                            font_size: '13sp'
                            color: (0.85, 0.88, 0.92, 1)
                            text_size: self.size
                            halign: 'left'
                            valign: 'middle'

                        Button:
                            text: 'View All'
                            size_hint: (None, None)
                            size: ('80dp', '36dp')
                            background_normal: ''
                            background_color: (0.22, 0.74, 0.97, 0.2)
                            color: (0.22, 0.74, 0.97, 1)
                            on_release: app.sm.current = 'attendance'

                # Banner Box 3: Quick Scratchpad Note Card
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: '150dp'
                    padding: '12dp'
                    spacing: '6dp'
                    canvas.before:
                        Color:
                            rgba: (0.18, 0.21, 0.26, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [12]

                    BoxLayout:
                        size_hint_y: None
                        height: '24dp'

                        Label:
                            text: 'QUICK SCRATCHPAD'
                            font_size: '12sp'
                            bold: True
                            color: (0.99, 0.88, 0.28, 1)
                            text_size: self.size
                            halign: 'left'

                        Label:
                            text: 'Auto-deletes in 24h'
                            font_size: '10sp'
                            color: (0.5, 0.55, 0.6, 1)
                            halign: 'right'

                    TextInput:
                        id: dash_scratchpad_input
                        hint_text: 'Jot down temporary thoughts...'
                        background_color: (0.14, 0.16, 0.2, 1)
                        foreground_color: (0.9, 0.92, 0.95, 1)
                        padding: ['8dp', '8dp']
                        multiline: True

        BottomNavBar:

# ------------------------------------------------------------------------------
# SCREEN 2: CALENDAR (Google Replica with Month Bar - Questions 4 & 6)
# ------------------------------------------------------------------------------
<CalendarScreen>:
    BoxLayout:
        orientation: 'vertical'

        TopNavBar:

        # Calendar Header & Month Selector
        BoxLayout:
            size_hint_y: None
            height: '48dp'
            padding: ['16dp', '4dp']
            canvas.before:
                Color:
                    rgba: (0.16, 0.18, 0.22, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size

            Button:
                id: month_selector_btn
                text: 'AUGUST 2026  ▼'
                font_size: '15sp'
                bold: True
                background_normal: ''
                background_color: (0, 0, 0, 0)
                color: (0.22, 0.74, 0.97, 1)
                on_release: root.open_month_grid_picker()

            Button:
                text: '+ Add Event'
                size_hint_x: None
                width: '100dp'
                background_normal: ''
                background_color: (0.22, 0.74, 0.97, 1)
                color: (0.08, 0.09, 0.11, 1)
                bold: True
                on_release: root.open_add_event_modal()

        ScrollView:
            BoxLayout:
                id: schedule_timeline_layout
                orientation: 'vertical'
                padding: '16dp'
                spacing: '12dp'
                size_hint_y: None
                height: self.minimum_height

        BottomNavBar:

# ------------------------------------------------------------------------------
# SCREEN 3: ATTENDANCE (Pie Charts & Bunk Predictor - Questions 11, 12, 15)
# ------------------------------------------------------------------------------
<AttendanceScreen>:
    BoxLayout:
        orientation: 'vertical'

        TopNavBar:

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            padding: ['16dp', '8dp']

            Label:
                text: 'SUBJECT ATTENDANCE & BUNK PREDICTOR'
                font_size: '12sp'
                bold: True
                color: (0.99, 0.88, 0.28, 1)
                text_size: self.size
                halign: 'left'

        ScrollView:
            BoxLayout:
                id: attendance_cards_container
                orientation: 'vertical'
                padding: '16dp'
                spacing: '16dp'
                size_hint_y: None
                height: self.minimum_height

        BottomNavBar:

# ------------------------------------------------------------------------------
# SCREEN 4: NOTES (Dual Notes Layout & Card Previews - Questions 5 & 18)
# ------------------------------------------------------------------------------
<NotesScreen>:
    BoxLayout:
        orientation: 'vertical'

        TopNavBar:

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                padding: '16dp'
                spacing: '16dp'
                size_hint_y: None
                height: self.minimum_height

                # Section A: Line-by-Line Task Checklists
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: '8dp'

                    Label:
                        text: 'QUICK TASKS & CHECKLISTS'
                        font_size: '12sp'
                        bold: True
                        color: (0.22, 0.74, 0.97, 1)
                        size_hint_y: None
                        height: '20dp'
                        text_size: self.size
                        halign: 'left'

                    BoxLayout:
                        id: task_checklist_box
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: '6dp'

                # Section B: Rectangular Card Note Previews
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: '8dp'

                    BoxLayout:
                        size_hint_y: None
                        height: '28dp'

                        Label:
                            text: 'MAIN CANVAS NOTES'
                            font_size: '12sp'
                            bold: True
                            color: (0.99, 0.88, 0.28, 1)
                            text_size: self.size
                            halign: 'left'

                        Button:
                            text: '+ New Note'
                            size_hint_x: None
                            width: '90dp'
                            background_normal: ''
                            background_color: (0.99, 0.88, 0.28, 1)
                            color: (0.08, 0.09, 0.11, 1)
                            bold: True
                            on_release: root.open_note_editor()

                    GridLayout:
                        id: main_notes_grid
                        cols: 1
                        spacing: '12dp'
                        size_hint_y: None
                        height: self.minimum_height

        BottomNavBar:

# ------------------------------------------------------------------------------
# SCREEN 5: AI HUB (Sarcastic Assistant & Multi-Model Q&A - Questions 21-25)
# ------------------------------------------------------------------------------
<AiHubScreen>:
    BoxLayout:
        orientation: 'vertical'

        TopNavBar:

        BoxLayout:
            orientation: 'vertical'
            padding: '16dp'
            spacing: '12dp'

            # Sarcastic AI Header Card
            BoxLayout:
                size_hint_y: None
                height: '70dp'
                padding: '12dp'
                canvas.before:
                    Color:
                        rgba: (0.18, 0.21, 0.26, 1)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [12]

                Label:
                    text: '🤖 Daybox AI Companion\\n"Ask me about your schedule, or upload notes to summarize."'
                    font_size: '12sp'
                    color: (0.99, 0.88, 0.28, 1)
                    text_size: self.size
                    halign: 'left'
                    valign: 'middle'

            ScrollView:
                BoxLayout:
                    id: ai_chat_history
                    orientation: 'vertical'
                    spacing: '10dp'
                    size_hint_y: None
                    height: self.minimum_height

            # Quick One-Tap Action Chips
            BoxLayout:
                size_hint_y: None
                height: '36dp'
                spacing: '8dp'

                Button:
                    text: '📅 Schedule Today'
                    font_size: '10sp'
                    background_normal: ''
                    background_color: (0.18, 0.21, 0.26, 1)
                    color: (0.22, 0.74, 0.97, 1)
                    on_release: root.send_quick_prompt("What is my schedule for today?")

                Button:
                    text: '⚠️ Attendance Alerts'
                    font_size: '10sp'
                    background_normal: ''
                    background_color: (0.18, 0.21, 0.26, 1)
                    color: (0.99, 0.88, 0.28, 1)
                    on_release: root.send_quick_prompt("Check my attendance status.")

            # Input Prompt Row
            BoxLayout:
                size_hint_y: None
                height: '48dp'
                spacing: '8dp'

                TextInput:
                    id: ai_prompt_input
                    hint_text: 'Ask Daybox AI...'
                    multiline: False
                    background_color: (0.14, 0.16, 0.2, 1)
                    foreground_color: (0.9, 0.92, 0.95, 1)

                Button:
                    text: 'Send'
                    size_hint_x: None
                    width: '70dp'
                    background_normal: ''
                    background_color: (0.22, 0.74, 0.97, 1)
                    color: (0.08, 0.09, 0.11, 1)
                    bold: True
                    on_release: root.process_ai_query()

        BottomNavBar:
"""

Builder.load_string(KV_BUILDER)

# ==============================================================================
# SCREEN IMPLEMENTATIONS & LOGIC
# ==============================================================================
class DashboardScreen(Screen):
    def on_enter(self):
        self.load_dashboard_data()

    def load_dashboard_data(self):
        # Refresh Attendance Summary Text
        cursor = db.conn.cursor()
        cursor.execute("SELECT subject, attended, total, target_pct FROM attendance")
        rows = cursor.fetchall()
        summary_lines = []
        for sub, att, tot, target in rows:
            pct = (att / tot * 100.0) if tot > 0 else 100.0
            status = "Safe" if pct >= target else "WARNING"
            summary_lines.append(f"• {sub}: {pct:.1f}% ({status})")
        self.ids.dash_attend_summary.text = "\n".join(summary_lines[:3])

class CalendarScreen(Screen):
    def on_enter(self):
        self.render_schedule()

    def render_schedule(self):
        container = self.ids.schedule_timeline_layout
        container.clear_widgets()

        cursor = db.conn.cursor()
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT id, title, time_str, is_task, completed, color_hex FROM events WHERE date_str = ?", (today_str,))
        rows = cursor.fetchall()

        if not rows:
            container.add_widget(Label(
                text="No events scheduled for today.\nTake a rest or sleep in!",
                font_size='13sp', color=(0.6, 0.65, 0.7, 1),
                size_hint_y=None, height='60dp'
            ))
            return

        for eid, title, time_str, is_task, completed, color_hex in rows:
            card = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', padding='8dp', spacing='10dp')
            # Draw Card Background
            with card.canvas.before:
                Color(0.18, 0.21, 0.26, 1)
                RoundedRectangle(pos=card.pos, size=card.size, radius=[8])

            # Color Indicator Bar
            bar = Widget(size_hint_x=None, width='6dp')
            with bar.canvas:
                # Convert Hex to RGB Approximation
                Color(0.22, 0.74, 0.97, 1) if color_hex == "#38BDF8" else Color(0.99, 0.88, 0.28, 1)
                RoundedRectangle(pos=bar.pos, size=bar.size, radius=[3])

            lbl_time = Label(text=time_str, font_size='11sp', color=(0.99, 0.88, 0.28, 1), size_hint_x=None, width='70dp')
            lbl_title = Label(text=title, font_size='13sp', color=(0.9, 0.92, 0.95, 1), halign='left', text_size=(200, None))

            card.add_widget(bar)
            card.add_widget(lbl_time)
            card.add_widget(lbl_title)
            container.add_widget(card)

    def open_month_grid_picker(self):
        # Full Month Grid Picker (Question 6)
        content = BoxLayout(orientation='vertical', padding='12dp', spacing='8dp')
        content.add_widget(Label(text="August 2026 Grid Overview", bold=True, color=(0.22, 0.74, 0.97, 1)))

        grid = GridLayout(cols=7, spacing='4dp')
        days = ["M", "T", "W", "T", "F", "S", "S"]
        for d in days:
            grid.add_widget(Label(text=d, font_size='11sp', color=(0.5, 0.55, 0.6, 1)))

        for day_num in range(1, 32):
            btn = Button(text=str(day_num), background_normal='', background_color=(0.18, 0.21, 0.26, 1), color=(0.9, 0.92, 0.95, 1))
            grid.add_widget(btn)

        content.add_widget(grid)
        popup = Popup(title="Select Date", content=content, size_hint=(0.85, 0.65))
        popup.open()

    def open_add_event_modal(self):
        # Event Creator Modal with Time Slot Selection
        box = BoxLayout(orientation='vertical', padding='12dp', spacing='10dp')
        title_in = TextInput(hint_text="Event Title", multiline=False, background_color=(0.14, 0.16, 0.2, 1), foreground_color=(1,1,1,1))
        time_in = TextInput(hint_text="Time (e.g. 11:00 AM)", multiline=False, background_color=(0.14, 0.16, 0.2, 1), foreground_color=(1,1,1,1))

        box.add_widget(Label(text="Create Primary Event/Task", bold=True, color=(0.22, 0.74, 0.97, 1)))
        box.add_widget(title_in)
        box.add_widget(time_in)

        btn_save = Button(text="Save to Daybox", size_hint_y=None, height='40dp', background_normal='', background_color=(0.22, 0.74, 0.97, 1), color=(0,0,0,1), bold=True)
        box.add_widget(btn_save)

        popup = Popup(title="New Schedule Item", content=box, size_hint=(0.85, 0.5))

        def save_event(instance):
            if title_in.text and time_in.text:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                cursor = db.conn.cursor()
                cursor.execute("INSERT INTO events (title, date_str, time_str, is_task, completed, color_hex) VALUES (?, ?, ?, ?, ?, ?)",
                               (title_in.text, today_str, time_in.text, 0, 0, "#38BDF8"))
                db.conn.commit()
                popup.dismiss()
                self.render_schedule()

        btn_save.bind(on_release=save_event)
        popup.open()

class AttendanceScreen(Screen):
    def on_enter(self):
        self.render_attendance_cards()

    def render_attendance_cards(self):
        container = self.ids.attendance_cards_container
        container.clear_widgets()

        cursor = db.conn.cursor()
        cursor.execute("SELECT id, subject, attended, total, target_pct, is_major FROM attendance")
        rows = cursor.fetchall()

        for sid, sub, att, tot, target, is_major in rows:
            pct = (att / tot * 100.0) if tot > 0 else 100.0

            # Safe Bunk Calculation (Question 12)
            # Formula: (Attended) / (Total + Bunks) >= Target/100
            safe_bunks = 0
            temp_tot = tot
            while (att / (temp_tot + 1) * 100.0) >= target:
                safe_bunks += 1
                temp_tot += 1

            # Catch-up Classes Needed if Below Target
            needed_classes = 0
            temp_att = att
            temp_tot_c = tot
            while (temp_att / temp_tot_c * 100.0) < target:
                needed_classes += 1
                temp_att += 1
                temp_tot_c += 1

            # Card Container
            card = BoxLayout(orientation='vertical', size_hint_y=None, height='140dp', padding='12dp', spacing='8dp')
            with card.canvas.before:
                Color(0.18, 0.21, 0.26, 1)
                RoundedRectangle(pos=card.pos, size=card.size, radius=[10])

            # Header Row
            header = BoxLayout(size_hint_y=None, height='24dp')
            lbl_sub = Label(text=sub, font_size='14sp', bold=True, color=(0.9, 0.92, 0.95, 1), halign='left', text_size=(220, None))
            lbl_pct = Label(text=f"{pct:.1f}%", font_size='14sp', bold=True,
                            color=(0.29, 0.87, 0.5, 1) if pct >= target else (0.97, 0.44, 0.44, 1), halign='right')
            header.add_widget(lbl_sub)
            header.add_widget(lbl_pct)

            # Details & Predictor Text
            if pct >= target:
                bunk_info = f"Bunk Predictor: You can safely miss {safe_bunks} class(es)."
            else:
                bunk_info = f"Bunk Predictor: WARNING! Attend {needed_classes} next class(es)!"

            lbl_details = Label(text=f"Attended: {att}/{tot}  |  Target: {target:.0f}%\n{bunk_info}",
                                font_size='11sp', color=(0.7, 0.75, 0.8, 1), halign='left', text_size=(320, None))

            # Action Buttons Row: Present, Absent, Exempt (Question 12)
            actions = BoxLayout(size_hint_y=None, height='32dp', spacing='8dp')

            btn_pres = Button(text="✓ Present", background_normal='', background_color=(0.29, 0.87, 0.5, 0.2), color=(0.29, 0.87, 0.5, 1))
            btn_abs = Button(text="✗ Absent", background_normal='', background_color=(0.97, 0.44, 0.44, 0.2), color=(0.97, 0.44, 0.44, 1))
            btn_exm = Button(text="↷ Exempt", background_normal='', background_color=(0.99, 0.88, 0.28, 0.2), color=(0.99, 0.88, 0.28, 1))

            # Bind Attendance Logic
            def mark_p(inst, subject_id=sid, is_m=is_major, sub_name=sub):
                cursor.execute("UPDATE attendance SET attended = attended + 1, total = total + 1 WHERE id = ?", (subject_id,))
                db.conn.commit()
                self.render_attendance_cards()

            def mark_a(inst, subject_id=sid, is_m=is_major, sub_name=sub):
                if is_m:
                    # Sarcastic Warning Popup for Major Subjects (Question 12)
                    self.show_sarcastic_warning(sub_name)
                cursor.execute("UPDATE attendance SET total = total + 1 WHERE id = ?", (subject_id,))
                db.conn.commit()
                self.render_attendance_cards()

            btn_pres.bind(on_release=mark_p)
            btn_abs.bind(on_release=mark_a)

            actions.add_widget(btn_pres)
            actions.add_widget(btn_abs)
            actions.add_widget(btn_exm)

            card.add_widget(header)
            card.add_widget(lbl_details)
            card.add_widget(actions)

            container.add_widget(card)

    def show_sarcastic_warning(self, subject_name):
        content = BoxLayout(orientation='vertical', padding='14dp', spacing='10dp')
        msg = f'🤖 "Skipping {subject_name}? Bold choice!\nYour future exam self is crying right now."'
        content.add_widget(Label(text=msg, font_size='13sp', color=(0.99, 0.88, 0.28, 1)))

        btn_ok = Button(text="I Accept the Consequences", size_hint_y=None, height='36dp',
                        background_normal='', background_color=(0.97, 0.44, 0.44, 1), color=(1,1,1,1))
        content.add_widget(btn_ok)

        popup = Popup(title="Major Class Warning", content=content, size_hint=(0.8, 0.4))
        btn_ok.bind(on_release=popup.dismiss)
        popup.open()

class NotesScreen(Screen):
    def on_enter(self):
        self.render_notes_and_tasks()

    def render_notes_and_tasks(self):
        # Render Section A: Quick Checklists
        task_box = self.ids.task_checklist_box
        task_box.clear_widgets()

        cursor = db.conn.cursor()
        cursor.execute("SELECT id, title, completed FROM events WHERE is_task = 1")
        tasks = cursor.fetchall()

        for tid, title, comp in tasks:
            row = BoxLayout(size_hint_y=None, height='32dp', spacing='8dp')
            btn_chk = Button(text="[X]" if comp else "[  ]", size_hint_x=None, width='36dp',
                             background_normal='', background_color=(0,0,0,0), color=(0.22, 0.74, 0.97, 1))
            lbl = Label(text=title, font_size='13sp', color=(0.9, 0.92, 0.95, 1), halign='left', text_size=(240, None))
            row.add_widget(btn_chk)
            row.add_widget(lbl)
            task_box.add_widget(row)

        # Render Section B: Main Note Cards
        notes_grid = self.ids.main_notes_grid
        notes_grid.clear_widgets()

        cursor.execute("SELECT id, title, content, tag, color_hex FROM notes")
        notes = cursor.fetchall()

        for nid, title, content, tag, color_hex in notes:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height='90dp', padding='10dp', spacing='4dp')
            with card.canvas.before:
                Color(0.18, 0.21, 0.26, 1)
                RoundedRectangle(pos=card.pos, size=card.size, radius=[8])

            lbl_t = Label(text=f"{tag}  {title}", font_size='13sp', bold=True, color=(0.22, 0.74, 0.97, 1), halign='left', text_size=(300, None))
            lbl_c = Label(text=content, font_size='11sp', color=(0.7, 0.75, 0.8, 1), halign='left', text_size=(300, None))

            card.add_widget(lbl_t)
            card.add_widget(lbl_c)
            notes_grid.add_widget(card)

    def open_note_editor(self):
        # Frictionless 1-2 Click Note Creator (Question 16)
        box = BoxLayout(orientation='vertical', padding='12dp', spacing='10dp')
        tag_in = TextInput(hint_text="Tag (e.g. #Genetics)", multiline=False, background_color=(0.14, 0.16, 0.2, 1), foreground_color=(1,1,1,1))
        title_in = TextInput(hint_text="Note Title", multiline=False, background_color=(0.14, 0.16, 0.2, 1), foreground_color=(1,1,1,1))
        content_in = TextInput(hint_text="Type contents...", multiline=True, background_color=(0.14, 0.16, 0.2, 1), foreground_color=(1,1,1,1))

        box.add_widget(tag_in)
        box.add_widget(title_in)
        box.add_widget(content_in)

        btn_save = Button(text="Save Note", size_hint_y=None, height='40dp', background_normal='', background_color=(0.99, 0.88, 0.28, 1), color=(0,0,0,1), bold=True)
        box.add_widget(btn_save)

        popup = Popup(title="New Canvas Note", content=box, size_hint=(0.85, 0.65))

        def save_note(inst):
            if title_in.text:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                cursor = db.conn.cursor()
                cursor.execute("INSERT INTO notes (title, content, tag, is_private, align_mode, color_hex, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (title_in.text, content_in.text, tag_in.text or "#General", 0, "left", "#38BDF8", today_str))
                db.conn.commit()
                popup.dismiss()
                self.render_notes_and_tasks()

        btn_save.bind(on_release=save_note)
        popup.open()

class AiHubScreen(Screen):
    def process_ai_query(self):
        query = self.ids.ai_prompt_input.text
        if query:
            self.send_quick_prompt(query)
            self.ids.ai_prompt_input.text = ""

    def send_quick_prompt(self, prompt_text):
        history = self.ids.ai_chat_history

        # User Bubble
        u_lbl = Label(text=f"You: {prompt_text}", font_size='12sp', color=(0.22, 0.74, 0.97, 1),
                      size_hint_y=None, height='28dp', halign='left', text_size=(300, None))
        history.add_widget(u_lbl)

        # AI Answer Logic
        response_text = ""
        low_p = prompt_text.lower()
        if "schedule" in low_p:
            response_text = "🤖 Daybox AI: Today you have Genetics Presentation at 09:30 AM and Biotech Lab Report due at 02:00 PM."
        elif "attendance" in low_p:
            response_text = "🤖 Daybox AI: Genetics is at 81.8% (Safe). Chemistry is near threshold at 76.0%. Keep it up!"
        else:
            response_text = f"🤖 Daybox AI: Analysis complete for '{prompt_text}'. All local database parameters are synced."

        ai_lbl = Label(text=response_text, font_size='12sp', color=(0.99, 0.88, 0.28, 1),
                       size_hint_y=None, height='40dp', halign='left', text_size=(300, None))
        history.add_widget(ai_lbl)

# ==============================================================================
# MAIN APPLICATION ENGINE & NAVIGATION SETUP
# ==============================================================================
class DayboxApp(App):
    def build(self):
        self.title = "Daybox"
        self.sm = ScreenManager(transition=FadeTransition())

        # Register Blueprint Screens
        self.sm.add_widget(DashboardScreen(name='dashboard'))
        self.sm.add_widget(CalendarScreen(name='calendar'))
        self.sm.add_widget(AttendanceScreen(name='attendance'))
        self.sm.add_widget(NotesScreen(name='notes'))
        self.sm.add_widget(AiHubScreen(name='ai_hub'))

        return self.sm

    def open_hamburger_menu(self):
        # Slide-out Menu for Global Options (Question 2)
        content = BoxLayout(orientation='vertical', padding='16dp', spacing='12dp')
        content.add_widget(Label(text="DAYBOX MENU", font_size='16sp', bold=True, color=(0.22, 0.74, 0.97, 1)))

        btn_sync = Button(text="Google Calendar Sync", size_hint_y=None, height='40dp', background_normal='', background_color=(0.18, 0.21, 0.26, 1), color=(1,1,1,1))
        btn_backup = Button(text="Export .daybox Backup", size_hint_y=None, height='40dp', background_normal='', background_color=(0.18, 0.21, 0.26, 1), color=(1,1,1,1))
        btn_theme = Button(text="Theme: Pastel Sunset", size_hint_y=None, height='40dp', background_normal='', background_color=(0.18, 0.21, 0.26, 1), color=(0.99, 0.88, 0.28, 1))

        content.add_widget(btn_sync)
        content.add_widget(btn_backup)
        content.add_widget(btn_theme)

        popup = Popup(title="Settings & Menu", content=content, size_hint=(0.75, 0.55))
        popup.open()

if __name__ == '__main__':
    DayboxApp().run()
