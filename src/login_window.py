from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from src.db_utils import get_connection

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация - Чудо Обувь")
        self.resize(300, 200)
        self.user_data = None # Сюда сохраним данные вошедшего пользователя

        layout = QVBoxLayout()

        self.label = QLabel("Введите ваш логин:")
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Например: admin")

        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.check_login)

        layout.addWidget(self.label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.btn_login)
        self.setLayout(layout)

    def check_login(self):
        login = self.login_input.text().strip()
        if not login:
            QMessageBox.warning(self, "Ошибка", "Логин не может быть пустым!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к базе данных!")
            return

        cursor = conn.cursor()
        # Ищем пользователя и его роль
        cursor.execute("""
            SELECT u.user_id, u.first_name, u.last_name, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.login = %s
        """, (login,))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Сохраняем данные (id, имя, фамилия, роль)
            self.user_data = {
                "id": user[0],
                "name": f"{user[2]} {user[1]}",
                "role": user[3]
            }
            self.accept() # Закрываем окно с успехом
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином не найден!")