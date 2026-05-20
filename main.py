import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QSpinBox, QCheckBox
)
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

import db


class TimerCanvas(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.pw = parent_window

    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        side = min(width, height) - 20
        x = (width - side) // 2
        y = (height - side) // 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Серый фоновый круг
        pen = QPen(QColor("#444444"), 8)
        painter.setPen(pen)
        painter.drawEllipse(x, y, side, side)

        # Красный прогресс
        if self.pw.total_seconds > 0:
            progress = self.pw.remaining_seconds / self.pw.total_seconds
            pen.setColor(QColor("#ff5555"))
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            start_angle = 90 * 16
            span_angle = int(progress * 360 * 16)
            painter.drawArc(x, y, side, side, start_angle, span_angle)

        # Текст времени (ММ:СС)
        minutes = self.pw.remaining_seconds // 60
        seconds = self.pw.remaining_seconds % 60
        time_text = f"{minutes:02}:{seconds:02}"

        painter.setFont(QFont("Arial", 36, QFont.Bold))
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(self.rect(), Qt.AlignCenter, time_text)


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализация БД
        db.init_db()
        db.init_streak()

        self.setWindowTitle("Pomodoro")
        self.setMinimumSize(600, 520)
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QWidget { background-color: #2b2b2b; }
            QPushButton {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #4e5254; }
            QPushButton:pressed { background-color: #ff5555; }
            QLineEdit {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
            }
            QListWidget {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                font-size: 13px;
            }
            QListWidget::item:selected { background-color: #ff5555; }
            QSpinBox {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 3px;
                font-size: 13px;
            }
            QLabel { color: #ffffff; font-size: 13px; }
            QCheckBox { color: #ffffff; font-size: 13px; }
        """)

        # === Аудио плеер ===
        self.player = QMediaPlayer()
        sound_path = "/Users/insomnia/PycharmProjects/RevorkPomadar/sound/02599.mp3"
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))

        # === Время ===
        self.time_m = 25
        self.total_seconds = self.time_m * 60
        self.remaining_seconds = self.total_seconds

        # === Таймер ===
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        # Streak из БД
        self.streak_count = self._load_streak_count()

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # панель(таймер)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        left_layout.setSpacing(12)

        self.streak_label = QLabel(f"🔥 Streak: {self.streak_count}")
        self.streak_label.setAlignment(Qt.AlignCenter)
        self.streak_label.setStyleSheet("font-size: 17px; font-weight: bold; color: #ff5555;")
        left_layout.addWidget(self.streak_label)

        self.canvas = TimerCanvas(self)
        self.canvas.setMinimumSize(260, 260)
        left_layout.addWidget(self.canvas, alignment=Qt.AlignHCenter)

        # Спинбокс минут
        spin_row = QHBoxLayout()
        self.spin = QSpinBox()
        self.spin.setRange(1, 120)
        self.spin.setValue(25)
        self.spin.valueChanged.connect(self.on_time_changed)
        spin_row.addStretch()
        spin_row.addWidget(QLabel("мин:"))
        spin_row.addWidget(self.spin)
        spin_row.addStretch()
        left_layout.addLayout(spin_row)

        # Start / Stop
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_timer)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_timer)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        left_layout.addLayout(btn_row)

        main_layout.addWidget(left)

        # панель Todo
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(8)

        todo_title = QLabel("📝 Задачи")
        todo_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        right_layout.addWidget(todo_title)

        input_row = QHBoxLayout()
        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("Новая задача...")
        self.todo_input.returnPressed.connect(self.add_todo)
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(36)
        add_btn.clicked.connect(self.add_todo)
        input_row.addWidget(self.todo_input)
        input_row.addWidget(add_btn)
        right_layout.addLayout(input_row)

        self.todo_list = QListWidget()
        self.todo_list.setSpacing(2)
        right_layout.addWidget(self.todo_list)

        del_btn = QPushButton("🗑 Удалить выбранное")
        del_btn.clicked.connect(self.delete_selected)
        right_layout.addWidget(del_btn)

        main_layout.addWidget(right)

        # Загружаем задачи из БД
        self.load_todos()

    # Streak
    def _load_streak_count(self) -> int:
        import sqlite3
        try:
            conn = sqlite3.connect('data/streak.db')
            cursor = conn.cursor()
            cursor.execute("SELECT streak_count FROM streak WHERE id = 1")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else 0
        except Exception:
            return 0


    # Таймер
    def on_time_changed(self, value):
        self.time_m = value
        self.total_seconds = value * 60
        self.remaining_seconds = self.total_seconds
        self.timer.stop()
        self.canvas.update()

    def start_timer(self):
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()

    def update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.canvas.update()

        if self.remaining_seconds == 0:
            self.timer.stop()
            self.player.play()


            new_streak = db.update_streak()
            if new_streak is not None:
                self.streak_count = new_streak
            else:
                self.streak_count = self._load_streak_count()
            self.streak_label.setText(f"🔥 Streak: {self.streak_count}")

            # Сброс таймера
            self.total_seconds = self.time_m * 60
            self.remaining_seconds = self.total_seconds
            self.canvas.update()


    # ToDo
    def load_todos(self):
        self.todo_list.clear()
        for todo_id, text, done in db.load_todos():
            self._add_item(todo_id, text, bool(done))

    def _add_item(self, todo_id, text, done):
        item = QListWidgetItem()
        item.setData(Qt.UserRole, todo_id)
        self.todo_list.addItem(item)

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(6, 2, 6, 2)

        cb = QCheckBox(text)
        cb.setChecked(done)
        self._style_checkbox(cb, done)
        cb.stateChanged.connect(lambda state, tid=todo_id, c=cb: self.toggle_todo(tid, state, c))
        layout.addWidget(cb)

        item.setSizeHint(row.sizeHint())
        self.todo_list.setItemWidget(item, row)

    def _style_checkbox(self, cb, done):
        if done:
            cb.setStyleSheet("color: #888888; font-size: 13px; text-decoration: line-through;")
        else:
            cb.setStyleSheet("color: #ffffff; font-size: 13px;")

    def add_todo(self):
        text = self.todo_input.text().strip()
        if not text:
            return
        todo_id = db.add_todo(text)
        self._add_item(todo_id, text, False)
        self.todo_input.clear()

    def toggle_todo(self, todo_id, state, cb):
        done = state == Qt.Checked
        db.toggle_todo(todo_id, done)
        self._style_checkbox(cb, done)

    def delete_selected(self):
        for item in self.todo_list.selectedItems():
            self.todo_list.takeItem(self.todo_list.row(item))


def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()