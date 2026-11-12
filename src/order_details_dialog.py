from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QMessageBox, QHeaderView, QDateEdit, QHBoxLayout)
from PyQt5.QtCore import QDate
from src.db_utils import get_connection

class OrderDetailsDialog(QDialog):
    def __init__(self, order_id, order_date, user_role, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.user_role = user_role
        self.setWindowTitle(f"Состав заказа №{order_id}")
        self.resize(700, 400)

        layout = QVBoxLayout()

        # --- Блок с датой (только для админа) ---
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Дата заказа:"))
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        
        # Парсим дату из БД (формат может быть datetime.date)
        qdate = QDate(order_date.year, order_date.month, order_date.day)
        self.date_edit.setDate(qdate)
        
        # Если это не админ, запрещаем редактировать дату
        if self.user_role != 'admin':
            self.date_edit.setReadOnly(True)
        else:
            self.btn_save_date = QPushButton("Сохранить дату")
            self.btn_save_date.clicked.connect(self.save_date)
            date_layout.addWidget(self.btn_save_date)

        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # --- Таблица с товарами ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID позиции", "Товар", "Размер", "Кол-во", "Цена за шт.", "Сумма"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # --- Кнопки управления ---
        btn_layout = QHBoxLayout()
        
        self.btn_delete_item = QPushButton("Удалить выбранную позицию")
        self.btn_delete_item.setStyleSheet("background-color: #f44336; color: white;")
        self.btn_delete_item.clicked.connect(self.delete_item)
        # Удалять позиции может только админ
        if self.user_role != 'admin':
            self.btn_delete_item.setEnabled(False)

        self.lbl_total = QLabel("Итого: 0.00 руб.")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold;")

        btn_layout.addWidget(self.btn_delete_item)
        btn_layout.addStretch()
        btn_layout.addWidget(self.lbl_total)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_items()

    def load_items(self):
        """Загружает позиции заказа из БД."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oi.order_item_id, p.name, s.size_value, oi.quantity, oi.price_at_order 
            FROM order_items oi
            JOIN stock_items si ON oi.stock_item_id = si.stock_item_id
            JOIN products p ON si.product_id = p.product_id
            JOIN sizes s ON si.size_id = s.size_id
            WHERE oi.order_id = %s
        """, (self.order_id,))
        items = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(items))
        total_sum = 0.0

        for row, item in enumerate(items):
            item_id, name, size, qty, price = item
            item_sum = float(qty) * float(price)
            total_sum += item_sum

            self.table.setItem(row, 0, QTableWidgetItem(str(item_id)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(size)))
            self.table.setItem(row, 3, QTableWidgetItem(str(qty)))
            self.table.setItem(row, 4, QTableWidgetItem(f"{float(price):.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{item_sum:.2f}"))

        self.lbl_total.setText(f"Итого: {total_sum:.2f} руб.")

    def save_date(self):
        """Сохраняет новую дату заказа (только для админа)."""
        new_date = self.date_edit.date().toString("yyyy-MM-dd")
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE orders SET order_date = %s WHERE order_id = %s", (new_date, self.order_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Дата заказа обновлена!")
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить дату:\n{e}")
        finally:
            conn.close()

    def delete_item(self):
        """Удаляет выбранную позицию из заказа (только для админа)."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите позицию для удаления!")
            return

        item_id = self.table.item(current_row, 0).text()
        
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить эту позицию?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM order_items WHERE order_item_id = %s", (item_id,))
                conn.commit()
                self.load_items() # Обновляем таблицу
                QMessageBox.information(self, "Успех", "Позиция удалена!")
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить позицию:\n{e}")
            finally:
                conn.close()