from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QHeaderView, QMessageBox)
from PyQt5.QtGui import QColor, QPixmap, QIcon
from PyQt5.QtCore import Qt
from src.db_utils import get_connection
import os

class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle("Чудо Обувь: Менеджер заказов")
        self.resize(1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Шапка с ФИО
        self.header = QLabel(f"Пользователь: {self.user_data['name']} | Роль: {self.user_data['role']}")
        self.header.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; padding: 10px;")
        layout.addWidget(self.header)

        # Таблица каталога
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Фото", "Категория", "Наименование", "Производитель", "Состав", "Цена (со скидкой)", "На складе (пар)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # Запрет редактирования
        layout.addWidget(self.table)

        central_widget.setLayout(layout)
        self.load_catalog()

    def load_catalog(self):
        """Загружает товары из БД, считает скидку и остатки."""
        conn = get_connection()
        if not conn:
            return
            
        cursor = conn.cursor()

        # Сложный запрос: получаем товары + общее количество на складе + проверяем, были ли заказы за последний месяц
        query = """
            SELECT 
                p.product_id, p.category, p.name, p.manufacturer, p.composition, p.price, p.image_path,
                COALESCE(SUM(si.quantity), 0) AS total_stock,
                (
                    SELECT COUNT(*) 
                    FROM order_items oi 
                    JOIN stock_items si2 ON oi.stock_item_id = si2.stock_item_id 
                    JOIN orders o ON oi.order_id = o.order_id
                    WHERE si2.product_id = p.product_id 
                    AND o.order_date >= (CURRENT_DATE - INTERVAL '1 month')
                ) AS orders_last_month
            FROM products p
            LEFT JOIN stock_items si ON p.product_id = si.product_id
            GROUP BY p.product_id
        """
        
        cursor.execute(query)
        products = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(products))

        for row_idx, prod in enumerate(products):
            prod_id, category, name, manuf, comp, price, img_path, stock, orders_last_month = prod

            # 1. Логика скидки 25%
            final_price = float(price)
            if orders_last_month == 0:
                final_price = final_price * 0.75 # Скидка 25%

            # 2. Заполнение ячеек
            self.table.setItem(row_idx, 1, QTableWidgetItem(category))
            self.table.setItem(row_idx, 2, QTableWidgetItem(name))
            self.table.setItem(row_idx, 3, QTableWidgetItem(manuf))
            self.table.setItem(row_idx, 4, QTableWidgetItem(comp))
            
            # Форматируем цену
            price_item = QTableWidgetItem(f"{final_price:.2f} руб.")
            if orders_last_month == 0:
                price_item.setForeground(QColor("green")) # Зеленый цвет для скидки
                price_item.setToolTip("Скидка 25% (не было заказов в прошлом месяце)")
            self.table.setItem(row_idx, 5, price_item)

            # Остаток
            stock_item = QTableWidgetItem(str(stock))
            self.table.setItem(row_idx, 6, stock_item)

            # 3. Подсветка красным (если остаток <= 3)
            if stock <= 3:
                for col in range(1, 7):
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setBackground(QColor("#ffcccc")) # Светло-красный

            # 4. Картинка (заглушка, если нет файла)
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            
            # Пытаемся загрузить картинку товара, если нет - заглушку
            image_file = os.path.join("resources", img_path) if img_path else ""
            if not os.path.exists(image_file):
                image_file = os.path.join("resources", "picture.png")
                
            if os.path.exists(image_file):
                pixmap = QPixmap(image_file).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(pixmap)
            
            self.table.setCellWidget(row_idx, 0, img_label)
            self.table.setRowHeight(row_idx, 90) # Высота строки под картинку