from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                             QSpinBox, QPushButton, QMessageBox, QHBoxLayout)
from src.db_utils import get_connection

class ProductDialog(QDialog):
    def __init__(self, product_id, product_name, price, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.price = price
        self.setWindowTitle(f"Товар: {product_name}")
        self.resize(300, 250)
        
        self.selected_stock_item_id = None
        self.selected_size = None
        self.selected_qty = 0

        layout = QVBoxLayout()
        
        self.lbl_name = QLabel(product_name)
        self.lbl_name.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.lbl_name)
        
        self.lbl_price = QLabel(f"Цена: {price:.2f} руб.")
        layout.addWidget(self.lbl_price)

        # Выбор размера
        layout.addWidget(QLabel("Выберите размер:"))
        self.size_combo = QComboBox()
        layout.addWidget(self.size_combo)
        
        # Выбор количества
        layout.addWidget(QLabel("Количество:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        layout.addWidget(self.qty_spin)

        # Кнопка добавления
        self.btn_add = QPushButton("Добавить в корзину")
        self.btn_add.clicked.connect(self.accept)
        layout.addWidget(self.btn_add)

        self.setLayout(layout)
        self.load_sizes()

    def load_sizes(self):
        """Загружает доступные размеры (где остаток > 0) из БД."""
        conn = get_connection()
        cursor = conn.cursor()
        # Ищем остатки для этого товара
        cursor.execute("""
            SELECT si.stock_item_id, s.size_value, si.quantity
            FROM stock_items si
            JOIN sizes s ON si.size_id = s.size_id
            WHERE si.product_id = %s AND si.quantity > 0
        """, (self.product_id,))
        sizes = cursor.fetchall()
        conn.close()

        if not sizes:
            self.size_combo.addItem("Нет в наличии")
            self.btn_add.setEnabled(False)
            return

        # Сохраняем данные в словарь для быстрого доступа: {индекс: (stock_item_id, size, qty)}
        self.sizes_data = {}
        for idx, (stock_item_id, size_val, qty) in enumerate(sizes):
            self.size_combo.addItem(f"Размер {size_val} (в наличии: {qty} шт.)")
            self.sizes_data[idx] = (stock_item_id, size_val, qty)
            
        # Настраиваем спиннер количества в зависимости от выбранного размера
        self.size_combo.currentIndexChanged.connect(self.update_max_qty)
        self.update_max_qty()

    def update_max_qty(self):
        """Обновляет максимально возможное количество для выбора."""
        idx = self.size_combo.currentIndex()
        if idx in self.sizes_data:
            _, _, max_qty = self.sizes_data[idx]
            self.qty_spin.setMaximum(max_qty)
        else:
            self.qty_spin.setMaximum(1)

    def get_data(self):
        """Возвращает выбранные данные для корзины."""
        idx = self.size_combo.currentIndex()
        if idx in self.sizes_data:
            stock_item_id, size_val, _ = self.sizes_data[idx]
            return {
                "stock_item_id": stock_item_id,
                "size": size_val,
                "qty": self.qty_spin.value(),
                "price": self.price
            }
        return None