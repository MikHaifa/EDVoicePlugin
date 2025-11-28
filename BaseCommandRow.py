from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


class BasePseudocodeLine(QWidget):
    """Базовый класс для всех строк псевдокода"""

    def __init__(self, template_type, mode="editor", indent_level=0, parent=None):
        super().__init__(parent)
        self.template_type = template_type
        self.mode = mode
        self.indent_level = indent_level

        # Устанавливаем фиксированную высоту для всех строк псевдокода
        self.setFixedHeight(22)

        # Основной layout
        self.main_layout = QHBoxLayout(self)

        # ==== НАСТРОЙКИ ОТСТУПОВ ====
        # Шаг отступа 40 пикселей для наглядности
        indent_pixels = indent_level * 40

        if mode == "tree":
            self.main_layout.setContentsMargins(indent_pixels, 1, 2, 1)
            self.main_layout.setSpacing(5)
        else:
            self.main_layout.setContentsMargins(indent_pixels, 1, 5, 1)
            self.main_layout.setSpacing(5)
        # ====

        # Базовые стили
        self.setStyleSheet("""
            QLabel {
                color: white;
            }
            QLineEdit {
                color: white;
                background-color: #2b2b2b;
                border: 1px solid #555;
                padding: 2px;
            }
            QComboBox {
                color: white;
                background-color: #2b2b2b;
                border: 1px solid #555;
                padding: 2px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(:/icon/icons/arrow_drop_down_24dp.svg);
            }
        """)

        self.delete_btn = None

    def add_delete_button(self):
        """Добавляет кнопку удаления в конец layout (только в режиме editor)"""
        if self.mode == "editor":
            self.delete_btn = QToolButton()
            self.delete_btn.setIcon(QIcon(":/icon/icons/close_24dp.svg"))
            self.delete_btn.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    border: none;
                }
                QToolButton:hover {
                    background-color: rgba(203, 0, 0, 100);
                    border-radius: 5px;
                }
            """)
            self.main_layout.addWidget(self.delete_btn)

    def get_data(self):
        raise NotImplementedError

    def set_data(self, data):
        raise NotImplementedError

    def generate_python_code(self, indent=""):
        raise NotImplementedError