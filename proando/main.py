import os
import json
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle

# Definición de RoundedRectangle para usar en los widgets
class RoundedRectangle(Rectangle):
    def __init__(self, **kwargs):
        self.radius = kwargs.pop('radius', [0, 0, 0, 0])
        super(RoundedRectangle, self).__init__(**kwargs)

# Configuración de la ventana
Window.size = (400, 700)  # Tamaño típico de un móvil
Window.clearcolor = (0.95, 0.95, 0.95, 1)  # Fondo claro

# Directorio para almacenar datos
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Archivo para almacenar actividades
ACTIVITIES_FILE = os.path.join(DATA_DIR, 'activities.json')

# Colores de la aplicación
PRIMARY_COLOR = (0.2, 0.6, 0.9, 1)  # Azul
SECONDARY_COLOR = (0.95, 0.95, 0.95, 1)  # Gris claro
ACCENT_COLOR = (0.9, 0.3, 0.3, 1)  # Rojo

# Clase para manejar actividades
class ActivityManager:
    @staticmethod
    def load_activities():
        if os.path.exists(ACTIVITIES_FILE):
            try:
                with open(ACTIVITIES_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []
    
    @staticmethod
    def save_activities(activities):
        with open(ACTIVITIES_FILE, 'w') as f:
            json.dump(activities, f)
    
    @staticmethod
    def add_activity(title, description, start_time, end_time, priority):
        activities = ActivityManager.load_activities()
        activity = {
            'id': len(activities) + 1,
            'title': title,
            'description': description,
            'start_time': start_time,
            'end_time': end_time,
            'priority': priority,
            'completed': False
        }
        activities.append(activity)
        ActivityManager.save_activities(activities)
        return activity
    
    @staticmethod
    def update_activity(activity_id, **kwargs):
        activities = ActivityManager.load_activities()
        for activity in activities:
            if activity['id'] == activity_id:
                for key, value in kwargs.items():
                    activity[key] = value
                break
        ActivityManager.save_activities(activities)
    
    @staticmethod
    def delete_activity(activity_id):
        activities = ActivityManager.load_activities()
        activities = [a for a in activities if a['id'] != activity_id]
        ActivityManager.save_activities(activities)
    
    @staticmethod
    def get_recommendations():
        activities = ActivityManager.load_activities()
        # Lógica simple de recomendación basada en prioridades
        high_priority = [a for a in activities if a['priority'] == 'Alta' and not a['completed']]
        if high_priority:
            return "Recomendación: Enfócate primero en tus actividades de alta prioridad."
        return "¡Buen trabajo! Estás al día con tus actividades prioritarias."

# Pantalla de inicio
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Encabezado
        header = BoxLayout(size_hint=(1, 0.15))
        title = Label(text='Zenith', font_size=dp(24), bold=True, color=(0.2, 0.2, 0.2, 1))
        header.add_widget(title)
        self.layout.add_widget(header)
        
        # Recomendaciones
        self.recommendation_label = Label(
            text="Cargando recomendaciones...", 
            size_hint=(1, 0.1),
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            valign='middle'
        )
        self.recommendation_label.bind(size=self.recommendation_label.setter('text_size'))
        self.layout.add_widget(self.recommendation_label)
        
        # Lista de actividades
        self.activities_container = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.activities_container.bind(minimum_height=self.activities_container.setter('height'))
        
        scroll_view = ScrollView(size_hint=(1, 0.65))
        scroll_view.add_widget(self.activities_container)
        self.layout.add_widget(scroll_view)
        
        # Botones de navegación
        nav_buttons = BoxLayout(size_hint=(1, 0.1), spacing=dp(10))
        
        add_button = Button(
            text="+", 
            font_size=dp(20),
            background_color=PRIMARY_COLOR,
            size_hint=(0.2, 1)
        )
        add_button.bind(on_release=self.go_to_add_activity)
        
        profile_button = Button(
            text="Perfil", 
            background_color=PRIMARY_COLOR,
            size_hint=(0.4, 1)
        )
        profile_button.bind(on_release=self.go_to_profile)
        
        schedule_button = Button(
            text="Horario", 
            background_color=PRIMARY_COLOR,
            size_hint=(0.4, 1)
        )
        schedule_button.bind(on_release=self.go_to_schedule)
        
        nav_buttons.add_widget(add_button)
        nav_buttons.add_widget(schedule_button)
        nav_buttons.add_widget(profile_button)
        
        self.layout.add_widget(nav_buttons)
        self.add_widget(self.layout)
    
    def on_enter(self):
        self.update_activities()
        self.update_recommendations()
    
    def update_activities(self):
        self.activities_container.clear_widgets()
        activities = ActivityManager.load_activities()
        
        if not activities:
            label = Label(
                text="No hay actividades. ¡Añade una!",
                size_hint_y=None,
                height=dp(50),
                color=(0.5, 0.5, 0.5, 1)
            )
            self.activities_container.add_widget(label)
            return
        
        for activity in activities:
            activity_card = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(100),
                padding=dp(10),
                spacing=dp(5)
            )
            activity_card.canvas.before.add(Color(*SECONDARY_COLOR))
            activity_card.canvas.before.add(RoundedRectangle(pos=activity_card.pos, size=activity_card.size, radius=[dp(10)]))
            
            title_row = BoxLayout(size_hint=(1, 0.4))
            title_label = Label(
                text=activity['title'],
                color=(0.2, 0.2, 0.2, 1),
                bold=True,
                halign='left',
                valign='middle',
                size_hint=(0.7, 1)
            )
            title_label.bind(size=title_label.setter('text_size'))
            
            priority_color = ACCENT_COLOR if activity['priority'] == 'Alta' else (0.2, 0.6, 0.2, 1) if activity['priority'] == 'Media' else (0.6, 0.6, 0.2, 1)
            priority_label = Label(
                text=activity['priority'],
                color=priority_color,
                size_hint=(0.3, 1)
            )
            
            title_row.add_widget(title_label)
            title_row.add_widget(priority_label)
            
            time_label = Label(
                text=f"{activity['start_time']} - {activity['end_time']}",
                color=(0.4, 0.4, 0.4, 1),
                halign='left',
                valign='middle',
                size_hint=(1, 0.3)
            )
            time_label.bind(size=time_label.setter('text_size'))
            
            buttons_row = BoxLayout(size_hint=(1, 0.3), spacing=dp(5))
            
            edit_button = Button(
                text="Editar",
                size_hint=(0.5, 1),
                background_color=PRIMARY_COLOR
            )
            edit_button.bind(on_release=lambda btn, id=activity['id']: self.edit_activity(id))
            
            delete_button = Button(
                text="Eliminar",
                size_hint=(0.5, 1),
                background_color=ACCENT_COLOR
            )
            delete_button.bind(on_release=lambda btn, id=activity['id']: self.delete_activity(id))
            
            buttons_row.add_widget(edit_button)
            buttons_row.add_widget(delete_button)
            
            activity_card.add_widget(title_row)
            activity_card.add_widget(time_label)
            activity_card.add_widget(buttons_row)
            
            self.activities_container.add_widget(activity_card)
    
    def update_recommendations(self):
        recommendation = ActivityManager.get_recommendations()
        self.recommendation_label.text = recommendation
    
    def go_to_add_activity(self, instance):
        self.manager.current = 'add_activity'
    
    def go_to_profile(self, instance):
        self.manager.current = 'profile'
    
    def go_to_schedule(self, instance):
        self.manager.current = 'schedule'
    
    def edit_activity(self, activity_id):
        activities = ActivityManager.load_activities()
        activity = next((a for a in activities if a['id'] == activity_id), None)
        if activity:
            self.manager.get_screen('add_activity').load_activity(activity)
            self.manager.current = 'add_activity'
    
    def delete_activity(self, activity_id):
        def confirm_delete(instance):
            ActivityManager.delete_activity(activity_id)
            self.update_activities()
            self.update_recommendations()
            popup.dismiss()
        
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text='¿Estás seguro de que quieres eliminar esta actividad?'))
        
        buttons = BoxLayout(size_hint=(1, 0.4), spacing=dp(10))
        cancel_button = Button(text='Cancelar')
        cancel_button.bind(on_release=lambda x: popup.dismiss())
        
        confirm_button = Button(text='Eliminar', background_color=ACCENT_COLOR)
        confirm_button.bind(on_release=confirm_delete)
        
        buttons.add_widget(cancel_button)
        buttons.add_widget(confirm_button)
        content.add_widget(buttons)
        
        popup = Popup(title='Confirmar eliminación', content=content, size_hint=(0.8, 0.4))
        popup.open()

# Pantalla para añadir/editar actividad
class AddActivityScreen(Screen):
    def __init__(self, **kwargs):
        super(AddActivityScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        self.editing_id = None
        
        # Título de la pantalla
        self.screen_title = Label(
            text='Añadir Actividad',
            font_size=dp(20),
            bold=True,
            size_hint=(1, 0.1),
            color=(0.2, 0.2, 0.2, 1)
        )
        self.layout.add_widget(self.screen_title)
        
        # Formulario
        form = GridLayout(cols=1, spacing=dp(15), size_hint=(1, 0.8))
        
        # Título
        form.add_widget(Label(text='Título', halign='left', size_hint=(1, 0.1), color=(0.2, 0.2, 0.2, 1)))
        self.title_input = TextInput(multiline=False, size_hint=(1, 0.1))
        form.add_widget(self.title_input)
        
        # Descripción
        form.add_widget(Label(text='Descripción', halign='left', size_hint=(1, 0.1), color=(0.2, 0.2, 0.2, 1)))
        self.description_input = TextInput(multiline=True, size_hint=(1, 0.2))
        form.add_widget(self.description_input)
        
        # Hora de inicio
        form.add_widget(Label(text='Hora de inicio', halign='left', size_hint=(1, 0.1), color=(0.2, 0.2, 0.2, 1)))
        self.start_time_input = TextInput(multiline=False, size_hint=(1, 0.1), hint_text='HH:MM')
        form.add_widget(self.start_time_input)
        
        # Hora de fin
        form.add_widget(Label(text='Hora de fin', halign='left', size_hint=(1, 0.1), color=(0.2, 0.2, 0.2, 1)))
        self.end_time_input = TextInput(multiline=False, size_hint=(1, 0.1), hint_text='HH:MM')
        form.add_widget(self.end_time_input)
        
        # Prioridad
        form.add_widget(Label(text='Prioridad', halign='left', size_hint=(1, 0.1), color=(0.2, 0.2, 0.2, 1)))
        self.priority_spinner = Spinner(
            text='Media',
            values=('Alta', 'Media', 'Baja'),
            size_hint=(1, 0.1),
            background_color=PRIMARY_COLOR
        )
        form.add_widget(self.priority_spinner)
        
        self.layout.add_widget(form)
        
        # Botones
        buttons = BoxLayout(size_hint=(1, 0.1), spacing=dp(10))
        
        cancel_button = Button(
            text='Cancelar',
            size_hint=(0.5, 1),
            background_color=(0.7, 0.7, 0.7, 1)
        )
        cancel_button.bind(on_release=self.cancel)
        
        self.save_button = Button(
            text='Guardar',
            size_hint=(0.5, 1),
            background_color=PRIMARY_COLOR
        )
        self.save_button.bind(on_release=self.save_activity)
        
        buttons.add_widget(cancel_button)
        buttons.add_widget(self.save_button)
        
        self.layout.add_widget(buttons)
        self.add_widget(self.layout)
    
    def load_activity(self, activity):
        self.editing_id = activity['id']
        self.screen_title.text = 'Editar Actividad'
        self.title_input.text = activity['title']
        self.description_input.text = activity['description']
        self.start_time_input.text = activity['start_time']
        self.end_time_input.text = activity['end_time']
        self.priority_spinner.text = activity['priority']
        self.save_button.text = 'Actualizar'
    
    def clear_form(self):
        self.editing_id = None
        self.screen_title.text = 'Añadir Actividad'
        self.title_input.text = ''
        self.description_input.text = ''
        self.start_time_input.text = ''
        self.end_time_input.text = ''
        self.priority_spinner.text = 'Media'
        self.save_button.text = 'Guardar'
    
    def cancel(self, instance):
        self.clear_form()
        self.manager.current = 'home'
    
    def save_activity(self, instance):
        title = self.title_input.text.strip()
        description = self.description_input.text.strip()
        start_time = self.start_time_input.text.strip()
        end_time = self.end_time_input.text.strip()
        priority = self.priority_spinner.text
        
        if not title or not start_time or not end_time:
            self.show_error('Por favor completa todos los campos obligatorios')
            return
        
        try:
            # Validación simple de formato de hora
            datetime.strptime(start_time, '%H:%M')
            datetime.strptime(end_time, '%H:%M')
        except ValueError:
            self.show_error('Formato de hora inválido. Usa HH:MM')
            return
        
        if self.editing_id:
            ActivityManager.update_activity(
                self.editing_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                priority=priority
            )
        else:
            ActivityManager.add_activity(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                priority=priority
            )
        
        self.clear_form()
        self.manager.current = 'home'
    
    def show_error(self, message):
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()

# Pantalla de horario
class ScheduleScreen(Screen):
    def __init__(self, **kwargs):
        super(ScheduleScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Título
        header = BoxLayout(size_hint=(1, 0.1))
        title = Label(text='Tu Horario', font_size=dp(20), bold=True, color=(0.2, 0.2, 0.2, 1))
        header.add_widget(title)
        self.layout.add_widget(header)
        
        # Horario
        self.schedule_container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.schedule_container.bind(minimum_height=self.schedule_container.setter('height'))
        
        scroll_view = ScrollView(size_hint=(1, 0.8))
        scroll_view.add_widget(self.schedule_container)
        self.layout.add_widget(scroll_view)
        
        # Botón de regreso
        back_button = Button(
            text='Volver',
            size_hint=(1, 0.1),
            background_color=PRIMARY_COLOR
        )
        back_button.bind(on_release=self.go_back)
        self.layout.add_widget(back_button)
        
        self.add_widget(self.layout)
    
    def on_enter(self):
        self.update_schedule()
    
    def update_schedule(self):
        self.schedule_container.clear_widgets()
        activities = ActivityManager.load_activities()
        
        if not activities:
            label = Label(
                text="No hay actividades programadas",
                size_hint_y=None,
                height=dp(50),
                color=(0.5, 0.5, 0.5, 1)
            )
            self.schedule_container.add_widget(label)
            return
        
        # Ordenar actividades por hora de inicio
        activities.sort(key=lambda x: x['start_time'])
        
        # Crear horario visual
        for i, activity in enumerate(activities):
            time_slot = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(60),
                padding=dp(5)
            )
            
            # Indicador de tiempo
            time_label = Label(
                text=f"{activity['start_time']}\n{activity['end_time']}",
                size_hint=(0.2, 1),
                color=(0.4, 0.4, 0.4, 1)
            )
            
            # Contenido de la actividad
            activity_content = BoxLayout(
                orientation='vertical',
                size_hint=(0.8, 1),
                padding=dp(10)
            )
            activity_content.canvas.before.add(Color(*SECONDARY_COLOR))
            activity_content.canvas.before.add(RoundedRectangle(pos=activity_content.pos, size=activity_content.size, radius=[dp(5)]))
            
            title_label = Label(
                text=activity['title'],
                color=(0.2, 0.2, 0.2, 1),
                bold=True,
                halign='left',
                valign='middle',
                size_hint=(1, 0.6)
            )
            title_label.bind(size=title_label.setter('text_size'))
            
            priority_color = ACCENT_COLOR if activity['priority'] == 'Alta' else (0.2, 0.6, 0.2, 1) if activity['priority'] == 'Media' else (0.6, 0.6, 0.2, 1)
            priority_label = Label(
                text=f"Prioridad: {activity['priority']}",
                color=priority_color,
                halign='left',
                valign='middle',
                size_hint=(1, 0.4)
            )
            priority_label.bind(size=priority_label.setter('text_size'))
            
            activity_content.add_widget(title_label)
            activity_content.add_widget(priority_label)
            
            time_slot.add_widget(time_label)
            time_slot.add_widget(activity_content)
            
            self.schedule_container.add_widget(time_slot)
            
            # Añadir separador si no es el último elemento
            if i < len(activities) - 1:
                separator = BoxLayout(size_hint_y=None, height=dp(1))
                separator.canvas.before.add(Color(0.8, 0.8, 0.8, 1))
                separator.canvas.before.add(Rectangle(pos=separator.pos, size=separator.size))
                self.schedule_container.add_widget(separator)
    
    def go_back(self, instance):
        self.manager.current = 'home'

# Pantalla de perfil
class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super(ProfileScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Título
        header = BoxLayout(size_hint=(1, 0.1))
        title = Label(text='Tu Perfil', font_size=dp(20), bold=True, color=(0.2, 0.2, 0.2, 1))
        header.add_widget(title)
        self.layout.add_widget(header)
        
        # Contenido del perfil
        profile_content = BoxLayout(orientation='vertical', size_hint=(1, 0.8), spacing=dp(15))
        
        # Avatar (usando un widget en lugar de una imagen)
        avatar_container = BoxLayout(size_hint=(1, 0.3), padding=dp(10))
        
        # Widget personalizado para el avatar
        avatar = Widget(size_hint=(None, None), size=(dp(100), dp(100)), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        with avatar.canvas:
            # Color azul para el avatar
            Color(0.29, 0.56, 0.89, 1)  # RGB para #4a90e2
            
            # Círculo para la cabeza
            Ellipse(pos=(avatar.center_x - dp(25), avatar.center_y + dp(10)), size=(dp(50), dp(50)))
            
            # Rectángulo para el cuerpo
            Rectangle(pos=(avatar.center_x - dp(40), avatar.center_y - dp(50)), size=(dp(80), dp(60)))
        
        avatar_container.add_widget(avatar)
        profile_content.add_widget(avatar_container)
        
        # Información del usuario
        user_info = GridLayout(cols=2, spacing=dp(10), size_hint=(1, 0.5))
        
        user_info.add_widget(Label(text='Nombre:', halign='right', color=(0.2, 0.2, 0.2, 1)))
        self.name_input = TextInput(text='Usuario', multiline=False)
        user_info.add_widget(self.name_input)
        
        user_info.add_widget(Label(text='Email:', halign='right', color=(0.2, 0.2, 0.2, 1)))
        self.email_input = TextInput(text='usuario@ejemplo.com', multiline=False)
        user_info.add_widget(self.email_input)
        
        user_info.add_widget(Label(text='Preferencias:', halign='right', color=(0.2, 0.2, 0.2, 1)))
        self.preferences_input = TextInput(text='Tema claro', multiline=False)
        user_info.add_widget(self.preferences_input)
        
        profile_content.add_widget(user_info)
        
        # Estadísticas
        stats = BoxLayout(orientation='vertical', size_hint=(1, 0.2), spacing=dp(5))
        stats.add_widget(Label(text='Estadísticas', font_size=dp(18), bold=True, color=(0.2, 0.2, 0.2, 1)))
        
        activities = ActivityManager.load_activities()
        total_activities = len(activities)
        completed_activities = len([a for a in activities if a.get('completed', False)])
        
        stats.add_widget(Label(
            text=f'Actividades totales: {total_activities}',
            color=(0.2, 0.2, 0.2, 1)
        ))
        stats.add_widget(Label(
            text=f'Actividades completadas: {completed_activities}',
            color=(0.2, 0.2, 0.2, 1)
        ))
        
        profile_content.add_widget(stats)
        
        self.layout.add_widget(profile_content)
        
        # Botones
        buttons = BoxLayout(size_hint=(1, 0.1), spacing=dp(10))
        
        save_button = Button(
            text='Guardar',
            size_hint=(0.5, 1),
            background_color=PRIMARY_COLOR
        )
        save_button.bind(on_release=self.save_profile)
        
        back_button = Button(
            text='Volver',
            size_hint=(0.5, 1),
            background_color=(0.7, 0.7, 0.7, 1)
        )
        back_button.bind(on_release=self.go_back)
        
        buttons.add_widget(save_button)
        buttons.add_widget(back_button)
        
        self.layout.add_widget(buttons)
        self.add_widget(self.layout)
    
    def save_profile(self, instance):
        # Aquí se implementaría la lógica para guardar el perfil
        popup = Popup(
            title='Perfil',
            content=Label(text='Perfil guardado correctamente'),
            size_hint=(0.8, 0.3)
        )
        popup.open()
    
    def go_back(self, instance):
        self.manager.current = 'home'

# Aplicación principal
class ZenithApp(App):
    def build(self):
        # Crear el administrador de pantallas
        sm = ScreenManager()
        
        # Añadir pantallas
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(AddActivityScreen(name='add_activity'))
        sm.add_widget(ScheduleScreen(name='schedule'))
        sm.add_widget(ProfileScreen(name='profile'))
        
        return sm

if __name__ == '__main__':
    ZenithApp().run()