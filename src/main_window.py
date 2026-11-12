from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QHeaderView, QMessageBox, QPushButton)
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtCore import Qt
from src.db_utils import get_connection
from src.product_dialog import ProductDialog
from src.cart_window import CartWindow
import os

class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle("Чудо Обувь: Менеджер заказов")
        self.resize(1100, 600)
        self.cart = [] # Список для хранения выбранных товаров

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # --- Шапка ---
        header_layout = QHBoxLayout()
        self.header = QLabel(f"Пользователь: {self.user_data['name']} | Роль: {self.user_data['role']}")
        self.header.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; padding: 10px;")
        
        self.btn_cart = QPushButton("Корзина (0)")
        self.btn_cart.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px;")
        self.btn_cart.clicked.connect(self.open_cart)

        header_layout.addWidget(self.header)
        header_layout.addStretch() # Прижимаем корзину вправо
        header_layout.addWidget(self.btn_cart)
        layout.addLayout(header_layout)

        # --- Таблица ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Фото", "Категория", "Наименование", "Производитель", "Состав", "Цена (со скидкой)", "На складе (пар)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_product_card) # Обработка двойного клика
        layout.addWidget(self.table)

        central_widget.setLayout(layout)
        self.load_catalog()

    def load_catalog(self):
        """Загружает товары из БД."""
        conn = get_connection()
        if not conn: return
        cursor = conn.cursor()

        query = """
            SELECT 
                p.product_id, p.category, p.name, p.manufacturer, p.composition, p.price, p.image_path,
                COALESCE(SUM(si.quantity), 0) AS total_stock,
                (
                    SELECT COUNT(*) FROM order_items oi 
                    JOIN stock_items si2 ON oi.stock_item_id = si2.stock_item_id 
                    JOIN orders o ON oi.order_id = o.order_id
                    WHERE si2.product_id = p.product_id AND o.order_date >= (CURRENT_DATE - INTERVAL '1 month')
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

            final_price = float(price)
            if orders_last_month == 0:
                final_price = final_price * 0.75

            self.table.setItem(row_idx, 1, QTableWidgetItem(category))
            
            # Сохраняем ID товара в скрытых данных ячейки с именем, чтобы потом получить его при клике
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, prod_id) 
            self.table.setItem(row_idx, 2, name_item)

            self.table.setItem(row_idx, 3, QTableWidgetItem(manuf))
            self.table.setItem(row_idx, 4, QTableWidgetItem(comp))
            
            price_item = QTableWidgetItem(f"{final_price:.2f} руб.")
            if orders_last_month == 0:
                price_item.setForeground(QColor("green"))
                price_item.setToolTip("Скидка 25%")
            self.table.setItem(row_idx, 5, price_item)

            stock_item = QTableWidgetItem(str(stock))
            self.table.setItem(row_idx, 6, stock_item)

            if stock <= 3:
                for col in range(1, 7):
                    item = self.table.item(row_idx, col)
                    if item: item.setBackground(QColor("#ffcccc"))

            # Картинка
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            image_file = os.path.join("resources", img_path) if img_path else ""
            if not os.path.exists(image_file):
                image_file = os.path.join("resources", "picture.png")
            if os.path.exists(image_file):
                pixmap = QPixmap(image_file).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(pixmap)
            
            self.table.setCellWidget(row_idx, 0, img_label)
            self.table.setRowHeight(row_idx, 90)

    def open_product_card(self, row, column):
        """Открывает карточку товара при двойном клике."""
        name_item = self.table.item(row, 2)
        if not name_item: return

        product_id = name_item.data(Qt.UserRole)
        product_name = name_item.text()
        
        # Получаем актуальную цену со скидкой из таблицы (парсим текст)
        price_str = self.table.item(row, 5).text().replace(" руб.", "")
        price = float(price_str)

        # Открываем диалоговое окно
        dialog = ProductDialog(product_id, product_name, price, self)
        if dialog.exec_() == ProductDialog.Accepted:
            data = dialog.get_data()
            if data:
                data['product_id'] = product_id
                data['name'] = product_name
                self.cart.append(data)
                self.update_cart_button()
                QMessageBox.information(self, "Успех", f"{product_name} (Размер {data['size']}) добавлен в корзину!")

    def update_cart_button(self):
        """Обновляет счетчик на кнопке корзины."""
        self.btn_cart.setText(f"Корзина ({len(self.cart)})")

    def open_cart(self):
        """Открывает окно корзины."""
        if not self.cart:
            QMessageBox.warning(self, "Внимание", "Корзина пуста!")
            return

        cart_win = CartWindow(self.cart, self.user_data['id'], self)
        if cart_win.exec_() == CartWindow.Accepted and cart_win.order_created:
            # Если заказ успешно оформлен, очищаем корзину и обновляем каталог
            self.cart.clear()
            self.update_cart_button()
            self.load_catalog() # Обновляем таблицу (остатки уменьшились)