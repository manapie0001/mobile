from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy_garden.mapview import MapView, MapMarker, MapSource
from threading import Thread
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
import requests
import time

try:
    from plyer import gps
    GPS_AVAILABLE = True
except:
    GPS_AVAILABLE = False
    print("plyer.gps не найден, используется симуляция")

# Константы
KAZAN_LAT = 55.796127
KAZAN_LON = 49.106405
ZOOM = 12

# Кэш для адресов
address_cache = {}


def get_address(lat, lon):
    """Обратное геокодирование (координаты -> адрес) с помощью OSM Nominatim"""
    cache_key = f"{lat:.6f},{lon:.6f}"
    if cache_key in address_cache:
        return address_cache[cache_key]
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'MyNavigatorApp/1.0'}
        time.sleep(0.5)
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            address = data.get('display_name', f"{lat:.5f}, {lon:.5f}")
            if len(address) > 100:
                address = address[:97] + "..."
            address_cache[cache_key] = address
            return address
    except:
        pass
    address = f"{lat:.5f}, {lon:.5f}"
    address_cache[cache_key] = address
    return address


def search_address(query):
    """Поиск адреса по тексту с ограничением по Казани"""
    if not query or len(query) < 3:
        return []
    try:
        search_query = f"{query} Казань"
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={search_query}&limit=5&addressdetails=1&bounded=1&viewbox=48.5,56.0,50.0,55.5"
        headers = {'User-Agent': 'MyNavigatorApp/1.0'}
        time.sleep(0.5)
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data:
                display_name = item.get('display_name', '')
                if 'Казань' in display_name or 'Kazan' in display_name:
                    results.append({
                        'display_name': display_name,
                        'lat': float(item.get('lat', 0)),
                        'lon': float(item.get('lon', 0))
                    })
            return results
    except Exception as e:
        print(f"Ошибка поиска: {e}")
    return []


class GPSButton(Button):

    def __init__(self, on_gps_click=None, **kwargs):
        super().__init__(**kwargs)
        self.text = 'GPS'
        self.font_size = '14sp'
        self.size_hint = (None, None)
        self.size = (60, 60)
        self.color = (1, 1, 1, 1)
        self.on_gps_click = on_gps_click
        self.opacity = 0   # скрыта по умолчанию
        self.disabled = True
        self.bind(on_press=self.get_location)

        from kivy.graphics import Color, RoundedRectangle
        with self.canvas.before:
            self.bg_color = Color(0.2, 0.5, 0.8, 0.9)
            self.bg_shape = RoundedRectangle(size=self.size, pos=self.pos, radius=[30, 30, 30, 30])
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_shape.pos = self.pos
        self.bg_shape.size = self.size

    def get_location(self, instance):
        print("\n=== ОТЛАДКА GPS: нажата кнопка ===")
        if self.on_gps_click:
            self.on_gps_click(None, None, "Поиск GPS сигнала...", is_loading=True)
            if GPS_AVAILABLE:
                try:
                    gps.configure(on_location=self.on_location, on_status=self.on_status)
                    gps.start()
                    print("GPS: запущен поиск координат")
                except Exception as e:
                    print(f"GPS ошибка при старте: {e}")
                    self.simulate_gps()
            else:
                self.simulate_gps()

    def on_location(self, **kwargs):
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        print(f"GPS: получены координаты: lat={lat}, lon={lon}")
        if lat and lon and self.on_gps_click:
            address = get_address(lat, lon)
            self.on_gps_click(lat, lon, address, is_loading=False)
        else:
            print("GPS: координаты недействительны")
        gps.stop()

    def on_status(self, stype, status):
        print(f"GPS статус: {stype} - {status}")

    def simulate_gps(self):
        print("GPS: используется симуляция (центр Казани)")
        lat = KAZAN_LAT
        lon = KAZAN_LON
        address = get_address(lat, lon)
        if self.on_gps_click:
            self.on_gps_click(lat, lon, address, is_loading=False)

    def show(self):
        print("=== GPSButton.show() called ===")
        self.opacity = 1
        self.disabled = False
        self.background_color = (1, 0, 0, 1)  # красный фон для отладки
        print(f"   pos_hint={self.pos_hint}, size={self.size}")

    def hide(self):
        print("=== GPSButton.hide() called ===")
        self.opacity = 0
        self.disabled = True
        print(f"   opacity={self.opacity}, disabled={self.disabled}")


class AddressInputWithDropdown(BoxLayout):
    def __init__(self, hint_text="Введите адрес", on_select_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.on_select_callback = on_select_callback
        self.orientation = 'horizontal'
        self.spacing = 5
        self.size_hint_y = None
        self.height = 48

        # Контейнер для поля ввода + иконки GPS (внутри поля)
        self.text_container = FloatLayout(size_hint_x=0.75)
        self.text_input = TextInput(
            hint_text=hint_text,
            multiline=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.text_input.bind(text=self.on_text_change)
        self.text_container.add_widget(self.text_input)

        # Иконка GPS внутри поля (прижата к правому краю)
        self.gps_btn = Button(
            background_normal='marker.png',
            background_down='marker.png',
            border=(0, 0, 0, 0),
            size_hint=(None, None),
            size=(35, 35),
            pos_hint={'right': 1, 'center_y': 0.5}
        )
        self.gps_btn.bind(on_press=self.on_gps_press)
        self.text_container.add_widget(self.gps_btn)

        # Отступ для текста, чтобы не залезал под иконку
        self.text_input.bind(size=self._update_padding)
        self._update_padding()

        # Кнопка «Выбрать на карте» – справа от поля
        self.map_btn = Button(text='Выбрать на карте', size_hint_x=0.2)
        self.map_btn.bind(on_press=self.open_map_selector)

        self.add_widget(self.text_container)
        self.add_widget(self.map_btn)

        # Остальные атрибуты (выпадающий список, поиск)
        self.dropdown = None
        self.suggestions = []
        self.search_thread = None
        self.current_query = ""

    def _update_padding(self, *args):
        if hasattr(self, 'gps_btn'):
            right_padding = self.gps_btn.width + 10
            self.text_input.padding = [8, 8, right_padding, 8]

    def on_gps_press(self, instance):
        app = App.get_running_app()
        if hasattr(app.root, 'request_gps_for_input'):
            app.root.request_gps_for_input(self)

    def on_text_change(self, instance, value):
        self.current_query = value
        if self.search_thread and self.search_thread.is_alive():
            return
        self.close_dropdown()
        if len(value) >= 3:
            self.search_thread = Thread(target=self.perform_search, args=(value,), daemon=True)
            self.search_thread.start()

    def perform_search(self, query):
        results = search_address(query)
        Clock.schedule_once(lambda dt: self.update_dropdown(results), 0)

    def close_dropdown(self):
        if self.dropdown:
            self.dropdown.dismiss()
            self.dropdown = None

    def update_dropdown(self, results):
        self.close_dropdown()
        self.suggestions = results
        if not results or not self.text_input.focus:
            return
        self.dropdown = DropDown()
        for result in results:
            display_name = result['display_name']
            if len(display_name) > 60:
                display_name = display_name[:57] + "..."
            btn = Button(text=display_name, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn, r=result: self.select_address(r))
            self.dropdown.add_widget(btn)
        if self.dropdown.children:
            self.dropdown.open(self.text_input)

    def select_address(self, address_data):
        self.text_input.text = address_data['display_name']
        self.close_dropdown()
        if self.on_select_callback:
            self.on_select_callback(
                address_data['lat'],
                address_data['lon'],
                address_data['display_name']
            )

    def open_map_selector(self, instance):
        self.close_dropdown()
        popup = PointSelectorPopup()
        popup.on_point_selected = self.on_map_selected
        popup.open()

    def on_map_selected(self, lat, lon, address):
        self.text_input.text = address
        if self.on_select_callback:
            self.on_select_callback(lat, lon, address)


class PointSelectorPopup(Popup):
    on_point_selected = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_lat = None
        self.selected_lon = None
        self.marker = None
        self.title = "Выберите точку на карте (нажмите на карту)"
        self.size_hint = (0.9, 0.9)
        self.auto_dismiss = False

        self.touch_start_pos = None
        self.is_dragging = False

        layout = BoxLayout(orientation='vertical', spacing=5, padding=5)

        self.map_view = MapView(
            zoom=11,
            lat=KAZAN_LAT,
            lon=KAZAN_LON,
            double_tap_zoom=True,
            map_source=MapSource.from_provider('osm')
        )

        self.coord_label = Label(
            text="Нажмите на карту, чтобы выбрать место",
            size_hint_y=None,
            height=80,
            text_size=(self.width, None)
        )
        self.coord_label.bind(size=self.coord_label.setter('text_size'))

        btn_layout = BoxLayout(size_hint_y=None, height=80, spacing=10)
        confirm_btn = Button(text='Подтвердить')
        confirm_btn.bind(on_press=self.confirm)
        cancel_btn = Button(text='Отмена')
        cancel_btn.bind(on_press=lambda x: self.dismiss())

        btn_layout.add_widget(confirm_btn)
        btn_layout.add_widget(cancel_btn)

        layout.add_widget(self.map_view)
        layout.add_widget(self.coord_label)
        layout.add_widget(btn_layout)

        self.add_widget(layout)

        self.map_view.bind(on_touch_down=self._on_touch_down)
        self.map_view.bind(on_touch_move=self._on_touch_move)
        self.map_view.bind(on_touch_up=self._on_touch_up)

    def _on_touch_down(self, map_view, touch):
        if map_view.collide_point(*touch.pos):
            self.touch_start_pos = (touch.x, touch.y)
            self.is_dragging = False
        return False

    def _on_touch_move(self, map_view, touch):
        if self.touch_start_pos:
            dx = abs(touch.x - self.touch_start_pos[0])
            dy = abs(touch.y - self.touch_start_pos[1])
            if dx > 10 or dy > 10:
                self.is_dragging = True
        return False

    def _on_touch_up(self, map_view, touch):
        if (map_view.collide_point(*touch.pos) and
                not touch.is_double_tap and
                not self.is_dragging):
            lat, lon = self._get_coordinates_from_touch(touch)
            if lat is not None and lon is not None:
                self.selected_lat = lat
                self.selected_lon = lon
                self._update_marker_at_selected_location()
        self.touch_start_pos = None
        self.is_dragging = False
        return False

    def _update_marker_at_selected_location(self):
        if self.selected_lat is None or self.selected_lon is None:
            return
        if self.marker:
            self.map_view.remove_marker(self.marker)
        self.marker = MapMarker(lat=self.selected_lat, lon=self.selected_lon)
        self.map_view.add_marker(self.marker)

    def _get_coordinates_from_touch(self, touch):
        try:
            bbox = self.map_view.get_bbox()
            min_lat, min_lon, max_lat, max_lon = bbox
            widget_x, widget_y = self.map_view.pos
            widget_w, widget_h = self.map_view.size
            rel_x = touch.x - widget_x
            rel_y = touch.y - widget_y
            if 0 <= rel_x <= widget_w and 0 <= rel_y <= widget_h:
                norm_x = rel_x / widget_w
                norm_y = rel_y / widget_h
                lon = min_lon + (max_lon - min_lon) * norm_x
                lat = min_lat + (max_lat - min_lat) * norm_y
                return lat, lon
        except Exception as e:
            print(f"Ошибка получения координат: {e}")
        return None, None

    def confirm(self, instance):
        if self.selected_lat is not None and self.on_point_selected:
            address = get_address(self.selected_lat, self.selected_lon)
            self.on_point_selected(self.selected_lat, self.selected_lon, address)
        self.dismiss()


class MenuButton(Button):
    def __init__(self, on_clear_callback=None, on_exit_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = 'wing.png'
        self.background_down = 'wing.png'   # можно ту же картинку для нажатия
        self.size_hint = (None, None)
        self.size = (40, 40)
        self.border = (0, 0, 0, 0)           # убираем рамки
        self.on_clear_callback = on_clear_callback
        self.on_exit_callback = on_exit_callback
        self.bind(on_release=self.open_menu)

    def open_menu(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.size_hint_y = None
        content.bind(minimum_height=content.setter('height'))

        clear_btn = Button(text='Сброс', size_hint_y=None, height=30, font_size='14sp')
        clear_btn.bind(on_release=lambda btn: self.menu_action('clear'))
        exit_btn = Button(text='Выход', size_hint_y=None, height=30, font_size='14sp')
        exit_btn.bind(on_release=lambda btn: self.menu_action('exit'))

        content.add_widget(clear_btn)
        content.add_widget(exit_btn)

        popup = Popup(
            title='Меню',
            content=content,
            size_hint=(None, None),
            size=(140, 200),
            auto_dismiss=True,
            pos_hint={'top': 0.985, 'x': 0.05},
            background_color=(0.1, 0.1, 0.1, 0.8)
        )
        popup.open()

    def menu_action(self, action):
        if action == 'clear' and self.on_clear_callback:
            self.on_clear_callback()
        elif action == 'exit' and self.on_exit_callback:
            self.on_exit_callback()


class MainWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.start_lat = None
        self.start_lon = None
        self.finish_lat = None
        self.finish_lon = None
        self.start_marker = None
        self.finish_marker = None
        self.active_input = None

        # Панель ввода (вверху)
        input_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.95, None),
            height=100,
            spacing=5,
            padding=[8, 8, 8, 8],
            pos_hint={'top': 0.98, 'x': 0.04}
        )

        self.start_input = AddressInputWithDropdown(
            hint_text="Введите адрес старта",
            on_select_callback=self.set_start_point
        )

        self.finish_input = AddressInputWithDropdown(
            hint_text="Введите адрес назначения",
            on_select_callback=self.set_finish_point
        )

        input_panel.add_widget(self.start_input)
        input_panel.add_widget(self.finish_input)

        # Карта
        self.map_view = MapView(
            zoom=ZOOM,
            lat=KAZAN_LAT,
            lon=KAZAN_LON,
            double_tap_zoom=True,
            map_source=MapSource.from_provider('osm')
        )

        self.add_widget(self.map_view)
        self.add_widget(input_panel)

        # Кнопка меню
        self.menu_button = MenuButton(
            on_clear_callback=self.clear_all,
            on_exit_callback=self.exit_app
        )
        self.menu_button.pos_hint = {'x': 0.001, 'top': 0.99}
        self.add_widget(self.menu_button)

        # Кнопка построения маршрута
        self.route_button = Button(
            text='Построить маршрут',
            size_hint=(None, None),
            size=(280, 80),
            font_size='18sp',
            pos_hint={'right': 0.98, 'y': 0.04},
            background_color=(0.8, 0, 0, 0.8),
            color=(1, 1, 1, 1)
        )
        self.route_button.bind(on_press=self.show_route)
        self.route_button.opacity = 0
        self.route_button.disabled = True
        self.add_widget(self.route_button)

        # Статусная строка
        self.status_label = Label(
            text='',
            size_hint=(None, None),
            size=(300, 40),
            pos_hint={'center_x': 0.5, 'top': 0.9},
            color=(0, 1, 0, 1),
            font_size='14sp'
        )
        self.add_widget(self.status_label)

        # Кнопка для отладки GPS
        # self.debug_btn = Button(
        #     text='GPS',
        #     size_hint=(None, None),
        #     size=(100, 40),
        #     pos_hint={'right': 0.98, 'top': 0.85},
        #     background_color=(0.5, 0.5, 0.5, 0.7),
        #     font_size='10sp'
        # )
        # self.debug_btn.bind(on_press=self.test_gps)
        # self.add_widget(self.debug_btn)

    def request_gps_for_input(self, input_widget):
        self.active_input = input_widget
        self.show_status('Поиск GPS...')
        # Запускаем получение координат (симуляция или реальный GPS)
        self._start_gps()

    def _start_gps(self):
        # Используем существующую логику из GPSButton, но упрощённо
        if GPS_AVAILABLE:
            try:
                gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
                gps.start()
            except Exception as e:
                print(f"GPS ошибка: {e}")
                self._simulate_gps()
        else:
            self._simulate_gps()

    def on_gps_location(self, **kwargs):
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        if lat and lon:
            address = get_address(lat, lon)
            if self.active_input:
                self.active_input.text_input.text = address
                if self.active_input == self.start_input:
                    self.set_start_point(lat, lon, address)
                else:
                    self.set_finish_point(lat, lon, address)
                self.show_status(f'GPS: {address[:50]}...')
                self.active_input = None
            gps.stop()
        else:
            self.show_status('Не удалось определить координаты', is_error=True)

    def on_gps_status(self, stype, status):
        print(f"GPS статус: {stype} - {status}")

    def _simulate_gps(self):
        lat, lon = KAZAN_LAT, KAZAN_LON
        address = get_address(lat, lon)
        if self.active_input:
            self.active_input.text_input.text = address
            if self.active_input == self.start_input:
                self.set_start_point(lat, lon, address)
            else:
                self.set_finish_point(lat, lon, address)
            self.show_status(f'GPS симуляция: {address[:50]}...')
            self.active_input = None
        else:
            self.show_status('Не выбрано поле для GPS', is_error=True)

    def exit_app(self):
        App.get_running_app().stop()

    def show_status(self, message, is_error=False):
        self.status_label.text = message
        self.status_label.color = (1, 0, 0, 1) if is_error else (0, 1, 0, 1)
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', ''), 3)

    def set_start_point(self, lat, lon, address):
        self.start_lat = lat
        self.start_lon = lon
        self.start_address = address
        self.start_input.text_input.text = address
        self._update_markers()
        self._check_and_show_route_button()
        self._center_map_on_points()
        self.show_status(f'Старт: {address[:50]}...')

    def set_finish_point(self, lat, lon, address):
        self.finish_lat = lat
        self.finish_lon = lon
        self.finish_address = address
        self.finish_input.text_input.text = address
        self._update_markers()
        self._check_and_show_route_button()
        self._center_map_on_points()
        self.show_status(f'Финиш: {address[:50]}...')

    def _check_and_show_route_button(self):
        if self.start_lat and self.finish_lat:
            self.route_button.opacity = 1
            self.route_button.disabled = False
        else:
            self.route_button.opacity = 0
            self.route_button.disabled = True

    def _update_markers(self):
        if hasattr(self, 'start_marker') and self.start_marker:
            self.map_view.remove_marker(self.start_marker)
        if hasattr(self, 'finish_marker') and self.finish_marker:
            self.map_view.remove_marker(self.finish_marker)
        if self.start_lat and self.start_lon:
            self.start_marker = MapMarker(lat=self.start_lat, lon=self.start_lon)
            self.map_view.add_marker(self.start_marker)
        if self.finish_lat and self.finish_lon:
            self.finish_marker = MapMarker(lat=self.finish_lat, lon=self.finish_lon)
            self.map_view.add_marker(self.finish_marker)

    def _center_map_on_points(self):
        if self.start_lat and self.finish_lat:
            center_lat = (self.start_lat + self.finish_lat) / 2
            center_lon = (self.start_lon + self.finish_lon) / 2
            self.map_view.lat = center_lat
            self.map_view.lon = center_lon
            lat_diff = abs(self.start_lat - self.finish_lat)
            lon_diff = abs(self.start_lon - self.finish_lon)
            max_diff = max(lat_diff, lon_diff)
            if max_diff < 0.01:
                zoom = 14
            elif max_diff < 0.05:
                zoom = 12
            elif max_diff < 0.1:
                zoom = 10
            else:
                zoom = 8
            self.map_view.zoom = min(zoom, ZOOM + 2)
        elif self.start_lat:
            self.map_view.lat = self.start_lat
            self.map_view.lon = self.start_lon
            self.map_view.zoom = ZOOM
        elif self.finish_lat:
            self.map_view.lat = self.finish_lat
            self.map_view.lon = self.finish_lon
            self.map_view.zoom = ZOOM

    def show_route(self, instance):
        if self.start_lat and self.finish_lat:
            popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            distance = self._calculate_distance()
            time_min = self._calculate_time()
            info_text = (
                f"[b]🚗 МАРШРУТ[/b]\n\n"
                f"[b]📍 Откуда:[/b]\n{self.start_address}\n\n"
                f"[b]🏁 Куда:[/b]\n{self.finish_address}\n\n"
                f"[b]📏 Расстояние:[/b] {distance:.1f} км\n\n"
                f"[b]🕐 Примерное время:[/b] {time_min:.0f} мин.\n\n"
                f"[i]✨ Полная навигация будет доступна в следующей версии[/i]"
            )
            info_label = Label(text=info_text, size_hint_y=None, markup=True)
            info_label.bind(size=info_label.setter('text_size'))
            close_btn = Button(text='Закрыть', size_hint_y=None, height=50)
            popup_content.add_widget(info_label)
            popup_content.add_widget(close_btn)
            popup = Popup(title='🗺️ Построение маршрута', content=popup_content, size_hint=(0.85, 0.6))
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
        else:
            self.show_status('⚠️ Выберите обе точки маршрута!', is_error=True)

    def _calculate_distance(self):
        from math import radians, sin, cos, sqrt, atan2
        R = 6371
        lat1, lon1 = radians(self.start_lat), radians(self.start_lon)
        lat2, lon2 = radians(self.finish_lat), radians(self.finish_lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _calculate_time(self):
        distance = self._calculate_distance()
        return distance / 40 * 60

    def clear_all(self):
        self.start_lat = None
        self.start_lon = None
        self.start_address = ""
        self.start_input.text_input.text = ""

        self.finish_lat = None
        self.finish_lon = None
        self.finish_address = ""
        self.finish_input.text_input.text = ""

        if hasattr(self, 'start_marker') and self.start_marker:
            self.map_view.remove_marker(self.start_marker)
        if hasattr(self, 'finish_marker') and self.finish_marker:
            self.map_view.remove_marker(self.finish_marker)

        self.start_marker = None
        self.finish_marker = None

        self.route_button.opacity = 0
        self.route_button.disabled = True

        self.map_view.lat = KAZAN_LAT
        self.map_view.lon = KAZAN_LON
        self.map_view.zoom = ZOOM

        self.active_input = None
        self.show_status('🗑️ Все точки очищены')


class NavigatorApp(App):
    def build(self):
        return MainWidget()


if __name__ == '__main__':
    app = NavigatorApp()
    app.run()