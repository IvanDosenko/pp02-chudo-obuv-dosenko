import sys
from PyQt5.QtWidgets import QApplication
from src.login_window import LoginWindow
from src.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 1. Показываем окно авторизации
    login_win = LoginWindow()
    
    # Если пользователь успешно вошел
    if login_win.exec_() == LoginWindow.Accepted:
        user_data = login_win.user_data
        
        # 2. Открываем главное окно
        main_win = MainWindow(user_data)
        main_win.show()
        
        # Запускаем цикл приложения
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()