import os
# Configuración para Windows - Alternativa
import sys
if sys.platform == 'win32':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
    os.environ['KIVY_GRAPHICS'] = 'opengl'
    os.environ['KIVY_WINDOW'] = 'sdl2'
else:
    os.environ['KIVY_GL_BACKEND'] = 'gl'

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime, timedelta
import sqlite3
import json

class DatabaseManager:
    def __init__(self):
        self.db_path = "zenith_mobile.db"
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT,
                start_time TEXT,
                end_time TEXT,
                date TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                theme TEXT DEFAULT 'Blue',
                notifications INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_activity(self, title, description, category, priority, start_time, end_time, date):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activities (title, description, category, priority, start_time, end_time, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, category, priority, start_time, end_time, date))
        conn.commit()
        conn.close()
    
    def get_activities(self, date=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if date:
            cursor.execute('SELECT * FROM activities WHERE date = ? ORDER BY start_time', (date,))
        else:
            cursor.execute('SELECT * FROM activities ORDER BY date, start_time')
        activities = cursor.fetchall()
        conn.close()
        return activities
    
    def update_activity_status(self, activity_id, completed):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE activities SET completed = ? WHERE id = ?', (completed, activity_id))
        conn.commit()
        conn.close()
    
    def delete_activity(self, activity_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM activities WHERE id = ?', (activity_id,))
        conn.commit()
        conn.close()

class DashboardScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"
        self.db = DatabaseManager()
        self.build_ui()
    
    def build_ui(self):
        main_layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
        
        # Header
        header = MDTopAppBar(
            title="Zenith - Dashboard",
            elevation=2,
            md_bg_color="#2196F3"
        )
        main_layout.add_widget(header)
        
        # Stats Cards
        stats_layout = MDGridLayout(cols=2, spacing=dp(15), size_hint_y=None, height=dp(120))
        
        # Today's tasks card
        today_card = MDCard(
            MDBoxLayout(
                MDLabel(
                    text="Tareas de Hoy",
                    theme_text_color="Primary",
                    font_style="H6",
                    halign="center"
                ),
                MDLabel(
                    text="0",
                    theme_text_color="Primary",
                    font_style="H3",
                    halign="center",
                    id="today_tasks_count"
                ),
                orientation="vertical",
                padding=dp(15),
                spacing=dp(5)
            ),
            elevation=3,
            radius=[10],
            md_bg_color="#E3F2FD"
        )
        
        # Completed tasks card
        completed_card = MDCard(
            MDBoxLayout(
                MDLabel(
                    text="Completadas",
                    theme_text_color="Primary",
                    font_style="H6",
                    halign="center"
                ),
                MDLabel(
                    text="0",
                    theme_text_color="Primary",
                    font_style="H3",
                    halign="center",
                    id="completed_tasks_count"
                ),
                orientation="vertical",
                padding=dp(15),
                spacing=dp(5)
            ),
            elevation=3,
            radius=[10],
            md_bg_color="#E8F5E8"
        )
        
        stats_layout.add_widget(today_card)
        stats_layout.add_widget(completed_card)
        main_layout.add_widget(stats_layout)
        
        # Today's activities section
        activities_label = MDLabel(
            text="Actividades de Hoy",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height=dp(40)
        )
        main_layout.add_widget(activities_label)
        
        # Activities list
        self.activities_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.activities_list)
        main_layout.add_widget(scroll)
        
        # Add activity button
        add_btn = MDRaisedButton(
            text="Agregar Actividad",
            md_bg_color="#2196F3",
            theme_text_color="Custom",
            text_color="white",
            size_hint_y=None,
            height=dp(50),
            on_release=self.show_add_activity_dialog
        )
        main_layout.add_widget(add_btn)
        
        self.add_widget(main_layout)
        Clock.schedule_once(self.load_data, 0.5)
    
    def load_data(self, dt):
        today = datetime.now().strftime("%Y-%m-%d")
        activities = self.db.get_activities(today)
        
        self.activities_list.clear_widgets()
        today_count = len(activities)
        completed_count = len([a for a in activities if a[8] == 1])  # completed column
        
        # Update stats
        today_label = self.ids.get("today_tasks_count")
        completed_label = self.ids.get("completed_tasks_count")
        
        for activity in activities:
            self.add_activity_item(activity)
    
    def add_activity_item(self, activity):
        item_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(70),
            padding=[dp(10), dp(5)]
        )
        
        # Checkbox
        checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            active=bool(activity[8]),  # completed status
            on_active=lambda x, active, aid=activity[0]: self.toggle_activity(aid, active)
        )
        
        # Activity info
        info_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2)
        )
        
        title_label = MDLabel(
            text=activity[1],  # title
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(25)
        )
        
        details_text = f"{activity[5]} - {activity[6]} | {activity[3]}"  # time range and category
        details_label = MDLabel(
            text=details_text,
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20)
        )
        
        info_layout.add_widget(title_label)
        info_layout.add_widget(details_label)
        
        # Delete button
        delete_btn = MDIconButton(
            icon="delete",
            theme_icon_color="Custom",
            icon_color="#F44336",
            on_release=lambda x, aid=activity[0]: self.delete_activity(aid)
        )
        
        item_layout.add_widget(checkbox)
        item_layout.add_widget(info_layout)
        item_layout.add_widget(delete_btn)
        
        card = MDCard(
            item_layout,
            elevation=2,
            radius=[5],
            size_hint_y=None,
            height=dp(80),
            md_bg_color="white" if not activity[8] else "#E8F5E8"
        )
        
        self.activities_list.add_widget(card)
    
    def toggle_activity(self, activity_id, completed):
        self.db.update_activity_status(activity_id, 1 if completed else 0)
        self.load_data(None)
    
    def delete_activity(self, activity_id):
        self.db.delete_activity(activity_id)
        self.load_data(None)
    
    def show_add_activity_dialog(self, instance):
        # Switch to activities screen
        self.manager.current = "activities"

class ActivitiesScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "activities"
        self.db = DatabaseManager()
        self.dialog = None
        self.build_ui()
    
    def build_ui(self):
        main_layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
        
        # Header
        header = MDTopAppBar(
            title="Gestionar Actividades",
            elevation=2,
            md_bg_color="#2196F3"
        )
        main_layout.add_widget(header)
        
        # Add activity button
        add_btn = MDRaisedButton(
            text="Nueva Actividad",
            md_bg_color="#4CAF50",
            theme_text_color="Custom",
            text_color="white",
            size_hint_y=None,
            height=dp(50),
            on_release=self.show_add_dialog
        )
        main_layout.add_widget(add_btn)
        
        # Activities list
        self.activities_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.activities_list)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        Clock.schedule_once(self.load_activities, 0.5)
    
    def load_activities(self, dt):
        activities = self.db.get_activities()
        self.activities_list.clear_widgets()
        
        for activity in activities:
            self.add_activity_card(activity)
    
    def add_activity_card(self, activity):
        card_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(15)
        )
        
        # Title and status
        title_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(30)
        )
        
        title = MDLabel(
            text=activity[1],
            theme_text_color="Primary",
            font_style="H6"
        )
        
        status_color = "#4CAF50" if activity[8] else "#FF9800"
        status_text = "Completada" if activity[8] else "Pendiente"
        
        status = MDLabel(
            text=status_text,
            theme_text_color="Custom",
            text_color=status_color,
            font_style="Caption",
            size_hint_x=None,
            width=dp(100)
        )
        
        title_layout.add_widget(title)
        title_layout.add_widget(status)
        
        # Description
        if activity[2]:  # description exists
            desc = MDLabel(
                text=activity[2],
                theme_text_color="Secondary",
                font_style="Body2",
                size_hint_y=None,
                height=dp(40)
            )
            card_layout.add_widget(desc)
        
        # Details
        details_text = f"📅 {activity[7]} | ⏰ {activity[5]} - {activity[6]} | 📂 {activity[3]} | 🔥 {activity[4]}"
        details = MDLabel(
            text=details_text,
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height=dp(25)
        )
        
        card_layout.add_widget(title_layout)
        card_layout.add_widget(details)
        
        card = MDCard(
            card_layout,
            elevation=3,
            radius=[10],
            size_hint_y=None,
            height=dp(120),
            md_bg_color="#E8F5E8" if activity[8] else "white"
        )
        
        self.activities_list.add_widget(card)
    
    def show_add_dialog(self, instance):
        if not self.dialog:
            content = MDBoxLayout(
                orientation="vertical",
                spacing=dp(15),
                size_hint_y=None,
                height=dp(400),
                padding=dp(20)
            )
            
            self.title_field = MDTextField(
                hint_text="Título de la actividad",
                required=True,
                helper_text="Campo requerido",
                helper_text_mode="on_error"
            )
            
            self.desc_field = MDTextField(
                hint_text="Descripción (opcional)",
                multiline=True,
                max_text_length=200
            )
            
            self.category_field = MDTextField(
                hint_text="Categoría",
                text="Trabajo"
            )
            
            self.priority_field = MDTextField(
                hint_text="Prioridad",
                text="Media"
            )
            
            self.date_field = MDTextField(
                hint_text="Fecha (YYYY-MM-DD)",
                text=datetime.now().strftime("%Y-%m-%d")
            )
            
            self.start_time_field = MDTextField(
                hint_text="Hora inicio (HH:MM)",
                text="09:00"
            )
            
            self.end_time_field = MDTextField(
                hint_text="Hora fin (HH:MM)",
                text="10:00"
            )
            
            content.add_widget(self.title_field)
            content.add_widget(self.desc_field)
            content.add_widget(self.category_field)
            content.add_widget(self.priority_field)
            content.add_widget(self.date_field)
            content.add_widget(self.start_time_field)
            content.add_widget(self.end_time_field)
            
            self.dialog = MDDialog(
                title="Nueva Actividad",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="CANCELAR",
                        theme_text_color="Custom",
                        text_color="#2196F3",
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="GUARDAR",
                        md_bg_color="#4CAF50",
                        theme_text_color="Custom",
                        text_color="white",
                        on_release=self.save_activity
                    ),
                ]
            )
        
        self.dialog.open()
    
    def save_activity(self, instance):
        if not self.title_field.text.strip():
            self.title_field.error = True
            return
        
        try:
            self.db.add_activity(
                self.title_field.text.strip(),
                self.desc_field.text.strip(),
                self.category_field.text.strip() or "General",
                self.priority_field.text.strip() or "Media",
                self.start_time_field.text.strip(),
                self.end_time_field.text.strip(),
                self.date_field.text.strip()
            )
            
            self.dialog.dismiss()
            self.load_activities(None)
            
            # Clear fields
            self.title_field.text = ""
            self.desc_field.text = ""
            
        except Exception as e:
            print(f"Error saving activity: {e}")

class ScheduleScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "schedule"
        self.db = DatabaseManager()
        self.current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        self.build_ui()
    
    def build_ui(self):
        main_layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
        
        # Header
        header = MDTopAppBar(
            title="Horario Semanal",
            elevation=2,
            md_bg_color="#2196F3"
        )
        main_layout.add_widget(header)
        
        # Week navigation
        week_nav = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(50)
        )
        
        prev_btn = MDIconButton(
            icon="chevron-left",
            on_release=self.prev_week
        )
        
        self.week_label = MDLabel(
            text="",
            theme_text_color="Primary",
            font_style="H6",
            halign="center"
        )
        
        next_btn = MDIconButton(
            icon="chevron-right",
            on_release=self.next_week
        )
        
        week_nav.add_widget(prev_btn)
        week_nav.add_widget(self.week_label)
        week_nav.add_widget(next_btn)
        
        main_layout.add_widget(week_nav)
        
        # Days of the week
        self.days_layout = MDBoxLayout(orientation="vertical", spacing=dp(10))
        scroll = MDScrollView()
        scroll.add_widget(self.days_layout)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        Clock.schedule_once(self.load_week_data, 0.5)
    
    def load_week_data(self, dt):
        self.update_week_label()
        self.load_week_activities()
    
    def update_week_label(self):
        start_date = self.current_week_start.strftime("%d/%m")
        end_date = (self.current_week_start + timedelta(days=6)).strftime("%d/%m/%Y")
        self.week_label.text = f"{start_date} - {end_date}"
    
    def load_week_activities(self):
        self.days_layout.clear_widgets()
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        for i, day_name in enumerate(days):
            day_date = self.current_week_start + timedelta(days=i)
            day_activities = self.db.get_activities(day_date.strftime("%Y-%m-%d"))
            
            # Day card
            day_card = MDCard(
                elevation=2,
                radius=[10],
                size_hint_y=None,
                height=dp(150),
                md_bg_color="white"
            )
            
            day_layout = MDBoxLayout(
                orientation="vertical",
                padding=dp(15),
                spacing=dp(5)
            )
            
            # Day header
            day_header = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(30)
            )
            
            day_title = MDLabel(
                text=f"{day_name} ({day_date.strftime('%d/%m')})",
                theme_text_color="Primary",
                font_style="Subtitle1"
            )
            
            activity_count = MDLabel(
                text=f"{len(day_activities)} actividades",
                theme_text_color="Secondary",
                font_style="Caption",
                size_hint_x=None,
                width=dp(100),
                halign="right"
            )
            
            day_header.add_widget(day_title)
            day_header.add_widget(activity_count)
            day_layout.add_widget(day_header)
            
            # Activities preview
            if day_activities:
                for activity in day_activities[:3]:  # Show first 3 activities
                    activity_text = f"• {activity[5]} - {activity[1]}"
                    if activity[8]:  # completed
                        activity_text += " ✓"
                    
                    activity_label = MDLabel(
                        text=activity_text,
                        theme_text_color="Secondary" if not activity[8] else "Custom",
                        text_color="#4CAF50" if activity[8] else None,
                        font_style="Caption",
                        size_hint_y=None,
                        height=dp(20)
                    )
                    day_layout.add_widget(activity_label)
                
                if len(day_activities) > 3:
                    more_label = MDLabel(
                        text=f"... y {len(day_activities) - 3} más",
                        theme_text_color="Secondary",
                        font_style="Caption",
                        size_hint_y=None,
                        height=dp(20)
                    )
                    day_layout.add_widget(more_label)
            else:
                empty_label = MDLabel(
                    text="No hay actividades programadas",
                    theme_text_color="Hint",
                    font_style="Caption",
                    italic=True,
                    size_hint_y=None,
                    height=dp(20)
                )
                day_layout.add_widget(empty_label)
            
            day_card.add_widget(day_layout)
            self.days_layout.add_widget(day_card)
    
    def prev_week(self, instance):
        self.current_week_start -= timedelta(days=7)
        self.load_week_data(None)
    
    def next_week(self, instance):
        self.current_week_start += timedelta(days=7)
        self.load_week_data(None)

class ProfileScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "profile"
        self.db = DatabaseManager()
        self.build_ui()
    
    def build_ui(self):
        main_layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
        
        # Header
        header = MDTopAppBar(
            title="Perfil y Configuración",
            elevation=2,
            md_bg_color="#2196F3"
        )
        main_layout.add_widget(header)
        
        # Profile info card
        profile_card = MDCard(
            elevation=3,
            radius=[15],
            size_hint_y=None,
            height=dp(150),
            md_bg_color="#E3F2FD"
        )
        
        profile_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(10)
        )
        
        welcome_label = MDLabel(
            text="¡Bienvenido a Zenith!",
            theme_text_color="Primary",
            font_style="H5",
            halign="center"
        )
        
        subtitle_label = MDLabel(
            text="Tu asistente personal para la gestión del tiempo",
            theme_text_color="Secondary",
            font_style="Body1",
            halign="center"
        )
        
        profile_layout.add_widget(welcome_label)
        profile_layout.add_widget(subtitle_label)
        profile_card.add_widget(profile_layout)
        main_layout.add_widget(profile_card)
        
        # Statistics card
        stats_card = MDCard(
            elevation=3,
            radius=[15],
            size_hint_y=None,
            height=dp(120),
            md_bg_color="white"
        )
        
        stats_layout = MDGridLayout(
            cols=3,
            padding=dp(20),
            spacing=dp(15)
        )
        
        # Total activities
        total_activities = len(self.db.get_activities())
        self.add_stat_item(stats_layout, str(total_activities), "Total\nActividades", "#2196F3")
        
        # Completed activities
        all_activities = self.db.get_activities()
        completed = len([a for a in all_activities if a[8] == 1])
        self.add_stat_item(stats_layout, str(completed), "Completadas", "#4CAF50")
        
        # Completion rate
        rate = f"{int((completed/total_activities)*100) if total_activities > 0 else 0}%"
        self.add_stat_item(stats_layout, rate, "Tasa de\nCompletado", "#FF9800")
        
        stats_card.add_widget(stats_layout)
        main_layout.add_widget(stats_card)
        
        # Settings section
        settings_label = MDLabel(
            text="Configuración",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(40)
        )
        main_layout.add_widget(settings_label)
        
        # Settings buttons
        settings_buttons = [
            ("Notificaciones", "bell", "#FF9800"),
            ("Tema", "palette", "#9C27B0"),
            ("Respaldo de Datos", "backup-restore", "#607D8B"),
            ("Acerca de", "information", "#2196F3")
        ]
        
        for text, icon, color in settings_buttons:
            btn = MDRaisedButton(
                text=f"  {text}",
                icon=icon,
                md_bg_color=color,
                theme_text_color="Custom",
                text_color="white",
                size_hint_y=None,
                height=dp(50),
                on_release=lambda x, t=text: self.handle_setting(t)
            )
            main_layout.add_widget(btn)
        
        self.add_widget(main_layout)
    
    def add_stat_item(self, layout, value, label, color):
        item_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(5)
        )
        
        value_label = MDLabel(
            text=value,
            theme_text_color="Custom",
            text_color=color,
            font_style="H4",
            halign="center",
            size_hint_y=None,
            height=dp(40)
        )
        
        desc_label = MDLabel(
            text=label,
            theme_text_color="Secondary",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        
        item_layout.add_widget(value_label)
        item_layout.add_widget(desc_label)
        layout.add_widget(item_layout)
    
    def handle_setting(self, setting_name):
        # Placeholder for settings functionality
        print(f"Setting selected: {setting_name}")

class ZenithMobileApp(MDApp):
    def build(self):
        self.title = "Zenith Mobile"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        # Screen manager
        sm = MDScreenManager()
        
        # Add screens
        sm.add_widget(DashboardScreen())
        sm.add_widget(ActivitiesScreen())
        sm.add_widget(ScheduleScreen())
        sm.add_widget(ProfileScreen())
        
        # Bottom navigation
        bottom_nav = MDBottomNavigation(
            selected_color_background="white",
            text_color_active="white"
        )
        
        # Dashboard tab
        dashboard_tab = MDBottomNavigationItem(
            name="dashboard",
            text="Inicio",
            icon="home"
        )
        dashboard_tab.add_widget(DashboardScreen())
        
        # Activities tab
        activities_tab = MDBottomNavigationItem(
            name="activities",
            text="Actividades",
            icon="clipboard-text"
        )
        activities_tab.add_widget(ActivitiesScreen())
        
        # Schedule tab
        schedule_tab = MDBottomNavigationItem(
            name="schedule",
            text="Horario",
            icon="calendar"
        )
        schedule_tab.add_widget(ScheduleScreen())
        
        # Profile tab
        profile_tab = MDBottomNavigationItem(
            name="profile",
            text="Perfil",
            icon="account"
        )
        profile_tab.add_widget(ProfileScreen())
        
        bottom_nav.add_widget(dashboard_tab)
        bottom_nav.add_widget(activities_tab)
        bottom_nav.add_widget(schedule_tab)
        bottom_nav.add_widget(profile_tab)
        
        return bottom_nav

if __name__ == "__main__":
    ZenithMobileApp().run()