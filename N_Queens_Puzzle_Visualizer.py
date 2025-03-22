from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from functools import partial
from kivy.metrics import dp
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.animation import Animation
from kivy.core.text import LabelBase
from kivy.lang import Builder

# Register custom fonts if available (you can replace with your preferred heading font)
try:
    LabelBase.register(name="Roboto",
                       fn_regular="Roboto-Regular.ttf",
                       fn_bold="Roboto-Bold.ttf")
except Exception:
    pass

# Minimal custom style for flat buttons (if needed)
Builder.load_string('''
<FlatButton@Button>:
    background_normal: ''
    background_down: ''
    background_color: 0.0, 0.5, 0.7, 1
    color: 1, 1, 1, 1
    font_size: '16sp'
    size_hint: 1, None
    height: dp(50)
    border: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: self.background_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
''')

class QueenButton(Button):
    has_queen = BooleanProperty(False)
    row = NumericProperty(0)
    col = NumericProperty(0)
    opacity_value = NumericProperty(1.0)
    queen_number = NumericProperty(0)

    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.background_normal = ''
        self.background_down = ''
        self.border = (0, 0, 0, 0)
        # For dark theme: light blue for safe queens, red for conflicts.
        self.queen_safe_color = get_color_from_hex('#64b5f6')
        self.queen_conflict_color = get_color_from_hex('#ef5350')
        self.queen_color = self.queen_safe_color

    def toggle_queen(self, is_solution=False, is_solving=False, animate=True, queen_number=0):
        if is_solving and self.has_queen:
            return
        new_state = not self.has_queen if not is_solution else True
        if animate and new_state != self.has_queen:
            if new_state:
                self.text = ''
                self.has_queen = True
                self.queen_number = queen_number
                anim = Animation(opacity_value=0, duration=0.1) + Animation(opacity_value=1, duration=0.3)
                anim.bind(on_complete=lambda *args: self.update_appearance())
                anim.start(self)
            else:
                anim = Animation(opacity_value=0, duration=0.2)
                anim.bind(on_complete=lambda *args: self.complete_removal())
                anim.start(self)
        else:
            self.has_queen = new_state
            self.queen_number = queen_number
            self.update_appearance()

    def complete_removal(self):
        self.has_queen = False
        self.queen_number = 0
        self.update_appearance()
        Animation(opacity_value=1, duration=0.1).start(self)

    def update_appearance(self, is_conflict=False):
        if self.has_queen:
            self.text = f"Q{self.queen_number}"
            self.font_size = '20sp'
            self.color = self.queen_conflict_color if is_conflict else self.queen_safe_color
            self.bold = True
        else:
            self.text = ''

class NQueensBoard(GridLayout):
    queens_positions = ListProperty([])
    solving = BooleanProperty(False)
    animating = BooleanProperty(False)
    solution_index = NumericProperty(0)
    all_solutions = []
    animation_speed = NumericProperty(0.5)

    def __init__(self, n, **kwargs):
        super().__init__(**kwargs)
        self.n = n
        self.cols = n
        # Set spacing as a numeric value
        self.spacing = 2  
        self.padding = 2
        # Dark chessboard palette
        self.light_color = get_color_from_hex('#3d3d3d')
        self.dark_color = get_color_from_hex('#2c2c2c')
        self.threat_color = get_color_from_hex('#ef5350')
        self.threat_dark_color = get_color_from_hex('#e57373')
        self.initialize_board()
        self.bind(size=self.update_board_size)

    def initialize_board(self):
        self.clear_widgets()
        self.queens_positions = []
        self.buttons = []
        for row in range(self.n):
            row_buttons = []
            for col in range(self.n):
                is_light = (row + col) % 2 == 0
                btn = QueenButton(
                    row=row,
                    col=col,
                    background_color=self.light_color if is_light else self.dark_color
                )
                btn.bind(on_release=self.on_square_click)
                self.add_widget(btn)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def update_board_size(self, *args):
        # Ensure spacing is a number
        spacing = self.spacing[0] if isinstance(self.spacing, (list, tuple)) else self.spacing
        min_dim = min(self.width, self.height)
        cell_size = (min_dim - (spacing * (self.n + 1))) / self.n
        for row in range(self.n):
            for col in range(self.n):
                btn = self.buttons[row][col]
                btn.size_hint = (None, None)
                btn.size = (cell_size, cell_size)

    def on_square_click(self, instance):
        if self.solving or self.animating:
            return
        queen_number = len(self.queens_positions) + 1 if not instance.has_queen else 0
        instance.toggle_queen(animate=True, queen_number=queen_number)
        if instance.has_queen:
            self.queens_positions.append((instance.row, instance.col))
        else:
            if (instance.row, instance.col) in self.queens_positions:
                self.queens_positions.remove((instance.row, instance.col))
                queen_num = 1
                for row, col in self.queens_positions:
                    self.buttons[row][col].queen_number = queen_num
                    self.buttons[row][col].update_appearance()
                    queen_num += 1
        self.highlight_conflicts()

    def highlight_conflicts(self):
        for row in range(self.n):
            for col in range(self.n):
                is_light = (row + col) % 2 == 0
                button = self.buttons[row][col]
                button.background_color = self.light_color if is_light else self.dark_color

        queen_conflicts = {pos: False for pos in self.queens_positions}
        for i, (row1, col1) in enumerate(self.queens_positions):
            for j, (row2, col2) in enumerate(self.queens_positions):
                if i != j and (row1 == row2 or col1 == col2 or abs(row1 - row2) == abs(col1 - col2)):
                    queen_conflicts[(row1, col1)] = True
                    queen_conflicts[(row2, col2)] = True

        for (row, col), has_conflict in queen_conflicts.items():
            button = self.buttons[row][col]
            button.update_appearance(is_conflict=has_conflict)
            if has_conflict:
                is_light = (row + col) % 2 == 0
                highlight_color = self.threat_color if is_light else self.threat_dark_color
                Animation(background_color=highlight_color, duration=0.3).start(button)

    def clear_board(self, animate=True):
        self.animating = animate
        self.queens_positions = []
        if animate:
            for row in range(self.n):
                for col in range(self.n):
                    button = self.buttons[row][col]
                    if button.has_queen:
                        delay = (row + col) * 0.03
                        Clock.schedule_once(partial(self.clear_queen, button), delay)
            total_time = self.n * 0.06 + 0.3
            Clock.schedule_once(lambda dt: setattr(self, 'animating', False), total_time)
        else:
            for row in range(self.n):
                for col in range(self.n):
                    button = self.buttons[row][col]
                    button.has_queen = False
                    button.queen_number = 0
                    is_light = (row + col) % 2 == 0
                    button.background_color = self.light_color if is_light else self.dark_color
                    button.update_appearance()
            self.animating = False

    def clear_queen(self, button, dt):
        button.toggle_queen(animate=True)
        is_light = (button.row + button.col) % 2 == 0
        button.background_color = self.light_color if is_light else self.dark_color

    def solve_nqueens(self):
        self.solving = True
        self.all_solutions = []
        self.solution_index = 0
        self.clear_board(animate=True)
        Clock.schedule_once(self.perform_solving, 0.5)

    def perform_solving(self, dt):
        board = [-1] * self.n
        def solve(row):
            if row == self.n:
                self.all_solutions.append(board[:])
                return
            for col in range(self.n):
                if all(board[r] != col and abs(board[r]-col) != row-r for r in range(row)):
                    board[row] = col
                    solve(row + 1)
        solve(0)
        if self.all_solutions:
            self.animating = True
            self.show_solution(0, animate=True)

    def show_solution(self, index, animate=True):
        if not self.all_solutions:
            return
        index = index % len(self.all_solutions)
        self.solution_index = index
        self.clear_board(animate=False)
        self.queens_positions = []
        solution = self.all_solutions[index]
        if animate:
            self.animating = True
            for row, col in enumerate(solution):
                delay = row * 0.15
                Clock.schedule_once(partial(self.place_queen, row, col), delay)
            total_time = len(solution) * 0.15 + 0.3
            Clock.schedule_once(lambda dt: setattr(self, 'animating', False), total_time)
        else:
            for row, col in enumerate(solution):
                self.buttons[row][col].toggle_queen(is_solution=True, animate=False, queen_number=row+1)
                self.queens_positions.append((row, col))
            self.animating = False

    def place_queen(self, row, col, dt):
        self.buttons[row][col].toggle_queen(is_solution=True, animate=True, queen_number=row+1)
        self.queens_positions.append((row, col))

    def next_solution(self):
        if self.all_solutions and not self.animating:
            self.show_solution(self.solution_index + 1)

    def prev_solution(self):
        if self.all_solutions and not self.animating:
            self.show_solution(self.solution_index - 1)

    def change_board_size(self, n):
        self.n = n
        self.cols = n
        self.solution_index = 0
        self.all_solutions = []
        self.solving = False
        self.animating = False
        self.initialize_board()
        self.update_board_size()

class InfoPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(160)
        self.padding = [15, 10]
        self.spacing = 10
        # Standalone heading title with larger, bold text.
        self.title = Label(
            text="N Queens Puzzle Visualizer",
            font_size='26sp',
            color=get_color_from_hex('#64b5f6'),
            size_hint_y=None,
            height=dp(50),
            bold=True,
            halign='center'
        )
        self.title.bind(size=self.title.setter('text_size'))
        self.scroll = ScrollView(size_hint=(1, 1), bar_width=5)
        self.description = Label(
            text=(
                "Place N queens on an N×N board so that no queen attacks another.\n\n"
                "Did you know?\n"
                "• For N=8, there are 92 solutions\n"
                "• For N=9, there are 352 solutions\n"
                "• For N=10, there are 724 solutions\n"
                "• No solutions exist for N=2 and N=3"
            ),
            font_size='15sp',
            color=get_color_from_hex('#bdbdbd'),
            size_hint_y=None,
            halign='left',
            valign='top',
            padding=[5, 5]
        )
        self.description.bind(width=lambda *x: setattr(self.description, 'text_size', (self.width - dp(30), None)))
        self.description.bind(texture_size=lambda *x: setattr(self.description, 'height', self.description.texture_size[1]))
        self.scroll.add_widget(self.description)
        self.add_widget(self.title)
        self.add_widget(self.scroll)
        with self.canvas.after:
            Color(0.5, 0.5, 0.5, 1)
            self.line = Line(points=[0, 0, 0, 0], width=1)
        self.bind(pos=self.update_line, size=self.update_line)

    def update_line(self, *args):
        self.line.points = [self.x, self.y, self.x + self.width, self.y]

class NQueensUI(BoxLayout):
    board_size = NumericProperty(8)
    theme_bg_color = ListProperty([0.12, 0.12, 0.15, 1])   # Dark background
    theme_panel_color = ListProperty([0.18, 0.18, 0.22, 1])  # Slightly lighter panel
    theme_accent_color = ListProperty([0.30, 0.65, 0.85, 1]) # Accent (blue)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        with self.canvas.before:
            Color(*self.theme_bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        self.info_panel = InfoPanel()
        self.add_widget(self.info_panel)
        self.main_content = BoxLayout(orientation='horizontal', spacing=20)
        self.board_container = BoxLayout(orientation='vertical', size_hint=(0.75, 1))
        # Board container with curvy edges.
        with self.board_container.canvas.before:
            Color(*self.theme_panel_color)
            self.board_panel = RoundedRectangle(pos=self.board_container.pos, size=self.board_container.size, radius=[20,])
        self.board_container.bind(pos=self.update_board_panel, size=self.update_board_panel)
        # Vertical box to hold the stats bar and solution array (below the solution text).
        self.solution_info_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(60), spacing=5)
        self.stats_bar = BoxLayout(size_hint=(1, None), height=dp(30), spacing=10, padding=[10, 5])
        self.board_label = Label(
            text=f"{self.board_size}×{self.board_size} Board",
            size_hint=(0.6, 1),
            color=get_color_from_hex('#bdbdbd'),
            halign='left',
            font_size='16sp'
        )
        self.solution_label = Label(
            text="No solutions yet",
            size_hint=(0.4, 1),
            color=self.theme_accent_color,
            halign='right',
            font_size='16sp'
        )
        self.stats_bar.add_widget(self.board_label)
        self.stats_bar.add_widget(self.solution_label)
        # Label for the solution's column numbers with bigger, bold text.
        self.solution_array_label = Label(
            text="Columns: []",
            size_hint=(1, None),
            height=dp(30),
            color=get_color_from_hex('#bdbdbd'),
            font_size='18sp',
            bold=True,
            halign='center'
        )
        self.solution_info_box.add_widget(self.stats_bar)
        self.solution_info_box.add_widget(self.solution_array_label)
        self.board_container.add_widget(self.solution_info_box)
        self.board = NQueensBoard(self.board_size)
        self.board_container.add_widget(self.board)
        self.main_content.add_widget(self.board_container)
        self.controls = BoxLayout(orientation='vertical', size_hint=(0.25, 1), spacing=15, padding=[15, 15])
        with self.controls.canvas.before:
            Color(*self.theme_panel_color)
            self.controls_panel = RoundedRectangle(pos=self.controls.pos, size=self.controls.size, radius=[20,])
        self.controls.bind(pos=self.update_controls_panel, size=self.update_controls_panel)
        self.size_box = BoxLayout(orientation='vertical', size_hint=(1, 0.25), spacing=5)
        self.size_label = Label(
            text=f"Board Size: {self.board_size}",
            color=get_color_from_hex('#bdbdbd'),
            font_size='16sp',
            size_hint=(1, 0.5),
            halign='left'
        )
        self.size_slider = Slider(
            min=4,
            max=12,
            step=1,
            value=self.board_size,
            size_hint=(1, 0.5),
            cursor_size=(dp(20), dp(20))
        )
        self.size_slider.bind(value=self.on_slider_change)
        with self.size_slider.canvas.before:
            Color(0.5, 0.5, 0.5, 1)
            self.slider_bg = RoundedRectangle(pos=self.size_slider.pos, size=self.size_slider.size, radius=[10,])
        self.size_slider.bind(pos=self.update_slider_bg, size=self.update_slider_bg)
        self.size_box.add_widget(self.size_label)
        self.size_box.add_widget(self.size_slider)
        # Solve button now uses a green color.
        self.solve_btn = Button(
            text="Solve with Animation",
            background_color=get_color_from_hex('#4CAF50'),
            background_normal='',
            color=[1, 1, 1, 1],
            size_hint=(1, None),
            height=dp(50),
            font_size='16sp',
            bold=True
        )
        self.solve_btn.bind(on_release=self.on_solve)
        self.clear_btn = Button(
            text="Clear Board",
            background_color=get_color_from_hex('#ef5350'),
            background_normal='',
            color=[1, 1, 1, 1],
            size_hint=(1, None),
            height=dp(50),
            font_size='16sp',
            bold=True
        )
        self.clear_btn.bind(on_release=self.on_clear)
        self.nav_box = BoxLayout(size_hint=(1, None), height=dp(50), spacing=10)
        self.prev_btn = Button(
            text="<",
            background_color=get_color_from_hex('#64b5f6'),
            background_normal='',
            size_hint=(0.5, 1),
            font_size='24sp',
            bold=True
        )
        self.prev_btn.bind(on_release=self.on_prev_solution)
        self.next_btn = Button(
            text=">",
            background_color=get_color_from_hex('#64b5f6'),
            background_normal='',
            size_hint=(0.5, 1),
            font_size='24sp',
            bold=True
        )
        self.next_btn.bind(on_release=self.on_next_solution)
        self.nav_box.add_widget(self.prev_btn)
        self.nav_box.add_widget(self.next_btn)
        self.controls.add_widget(self.size_box)
        self.controls.add_widget(self.solve_btn)
        self.controls.add_widget(self.clear_btn)
        self.controls.add_widget(self.nav_box)
        self.main_content.add_widget(self.controls)
        self.add_widget(self.main_content)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def update_board_panel(self, *args):
        self.board_panel.pos = self.board_container.pos
        self.board_panel.size = self.board_container.size

    def update_controls_panel(self, *args):
        self.controls_panel.pos = self.controls.pos
        self.controls_panel.size = self.controls.size

    def update_slider_bg(self, *args):
        self.slider_bg.pos = self.size_slider.pos
        self.slider_bg.size = self.size_slider.size

    def on_slider_change(self, instance, value):
        new_size = int(value)
        if new_size != self.board_size:
            self.board_size = new_size
            self.size_label.text = f"Board Size: {self.board_size}"
            self.board_label.text = f"{self.board_size}×{self.board_size} Board"
            self.board.change_board_size(self.board_size)
            self.solution_label.text = "No solutions yet"
            self.solution_array_label.text = "Columns: []"

    def on_solve(self, instance):
        self.board.solve_nqueens()
        Clock.schedule_once(self.update_solution_label, 0.5)

    def on_clear(self, instance):
        self.board.clear_board(animate=True)
        self.board.solving = False
        self.solution_label.text = "No solutions yet"
        self.solution_array_label.text = "Columns: []"

    def on_prev_solution(self, instance):
        if self.board.solving and self.board.all_solutions and not self.board.animating:
            self.board.prev_solution()
            self.update_solution_label()

    def on_next_solution(self, instance):
        if self.board.solving and self.board.all_solutions and not self.board.animating:
            self.board.next_solution()
            self.update_solution_label()

    def update_solution_label(self, *args):
        count = len(self.board.all_solutions)
        current = self.board.solution_index + 1
        self.solution_label.text = f"Solution {current}/{count}"
        # Display the current solution's column array (using 1-indexing)
        if self.board.all_solutions:
            sol = self.board.all_solutions[self.board.solution_index]
            sol_str = ", ".join(str(col + 1) for col in sol)
            self.solution_array_label.text = f"Columns: [{sol_str}]"
        else:
            self.solution_array_label.text = "Columns: []"

class NQueensApp(App):
    def build(self):
        Window.minimum_width, Window.minimum_height = 600, 500
        root = NQueensUI()
        Window.size = (900, 700)
        Window.clearcolor = root.theme_bg_color
        self.title = "N Queens Puzzle Visualizer"
        return root

if __name__ == "__main__":
    NQueensApp().run()
