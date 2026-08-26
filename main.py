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
                            bold:
