from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QHeaderView, QMessageBox, QPushButton, QTabWidget)
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtCore import Qt
from src.db_utils import get_connection
from src.product_dialog import ProductDialog
from src.cart_window import CartWindow
from src.orders_widget import OrdersWidget # Импортируем новую вкладку
import os

class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle("Чудо Обувь: Менеджер заказов")
        self.resize(1100, 700)
        self.cart = []

        # Главный виджет - вкладки
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 1. Вкладка "Каталог"
        self.catalog_widget = QWidget()
        self.setup_catalog_ui()
        self.tabs.addTab(self.catalog_widget, "Каталог товаров")

        # 2. Вкладка "Заказы" (только для админа и менеджера)
        if self.user_data['role'] in ['admin', 'manager']:
            self.orders_widget = OrdersWidget(self.user_data['role'])
            self.tabs.addTab(self.orders_widget, "Управление заказами")

        # Обновление каталога при переключении вкладок (чтобы остатки были актуальны)
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def setup_catalog_ui(self):
        """Настройка интерфейса вкладки 'Каталог'."""
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        self.header = QLabel(f"Пользователь: {self.user_data['name']} | Роль: {self.user_data['role']}")
        self.header.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; padding: 10px;")
        
        self.btn_cart = QPushButton("Корзина (0)")
        self.btn_cart.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px;")
        self.btn_cart.clicked.connect(self.open_cart)

        header_layout.addWidget(self.header)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_cart)
        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Фото", "Категория", "Наименование", "Производитель", "Состав", "Цена (со скидкой)", "На складе (пар)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_product_card)
        layout.addWidget(self.table)

        self.catalog_widget.setLayout(layout)
        self.load_catalog()

    def on_tab_changed(self, index):
        """Вызывается при переключении вкладки."""
        if index == 0:
            self.load_catalog() # Обновляем остатки
        elif index == 1 and hasattr(self, 'orders_widget'):
            self.orders_widget.load_orders() # Обновляем заказы

    def load_catalog(self):
        # (Код точно такой же, как был в прошлом шаге)
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
            if orders_last_month == 0: final_price *= 0.75

            self.table.setItem(row_idx, 1, QTableWidgetItem(category))
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

            self.table.setItem(row_idx, 6, QTableWidgetItem(str(stock)))

            if stock <= 3:
                for col in range(1, 7):
                    item = self.table.item(row_idx, col)
                    if item: item.setBackground(QColor("#ffcccc"))

            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            image_file = os.path.join("resources", img_path) if img_path else ""
            if not os.path.exists(image_file): image_file = os.path.join("resources", "picture.png")
            if os.path.exists(image_file):
                pixmap = QPixmap(image_file).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(pixmap)
            
            self.table.setCellWidget(row_idx, 0, img_label)
            self.table.setRowHeight(row_idx, 90)

    def open_product_card(self, row, column):
        # (Код точно такой же, как был в прошлом шаге)
        name_item = self.table.item(row, 2)
        if not name_item: return
        product_id = name_item.data(Qt.UserRole)
        product_name = name_item.text()
        price_str = self.table.item(row, 5).text().replace(" руб.", "")
        price = float(price_str)

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
        self.btn_cart.setText(f"Корзина ({len(self.cart)})")

    def open_cart(self):
        if not self.cart:
            QMessageBox.warning(self, "Внимание", "Корзина пуста!")
            return
        cart_win = CartWindow(self.cart, self.user_data['id'], self)
        if cart_win.exec_() == CartWindow.Accepted and cart_win.order_created:
            self.cart.clear()
            self.update_cart_button()
            self.load_catalog()