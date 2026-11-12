from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QMessageBox, QHeaderView, QHBoxLayout)
from src.db_utils import get_connection
from src.order_details_dialog import OrderDetailsDialog

class OrdersWidget(QWidget):
    def __init__(self, user_role, parent=None):
        super().__init__(parent)
        self.user_role = user_role
        layout = QVBoxLayout()

        # --- Панель кнопок ---
        top_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self.load_orders)
        
        self.btn_delete_order = QPushButton("Удалить заказ")
        self.btn_delete_order.setStyleSheet("background-color: #f44336; color: white;")
        self.btn_delete_order.clicked.connect(self.delete_order)
        
        top_layout.addWidget(self.btn_refresh)
        top_layout.addWidget(self.btn_delete_order)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # --- Таблица заказов ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Номер заказа", "Дата", "Клиент (ФИО)", "Сумма заказа"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_order_details)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_orders()

    def load_orders(self):
        """Загружает список всех заказов."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Получаем заказы + ФИО клиента + сумму
        query = """
            SELECT 
                o.order_id, 
                o.order_date, 
                u.last_name || ' ' || u.first_name || ' ' || COALESCE(u.middle_name, '') AS client_fio,
                COALESCE(SUM(oi.quantity * oi.price_at_order), 0) AS total_sum
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id, u.last_name, u.first_name, u.middle_name
            ORDER BY o.order_date DESC
        """
        cursor.execute(query)
        orders = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            order_id, order_date, client_fio, total_sum = order
            
            # Сохраняем ID заказа в скрытых данных
            id_item = QTableWidgetItem(str(order_id))
            id_item.setData(256, order_id) # 256 - это Qt.UserRole
            
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, QTableWidgetItem(order_date.strftime('%d.%m.%Y')))
            self.table.setItem(row, 2, QTableWidgetItem(client_fio))
            self.table.setItem(row, 3, QTableWidgetItem(f"{float(total_sum):.2f} руб."))

    def open_order_details(self, row, column):
        """Открывает окно деталей при двойном клике."""
        order_id = self.table.item(row, 0).data(256)
        # Получаем дату заказа для передачи в диалог
        order_date_str = self.table.item(row, 1).text() 
        
        # Нам нужен объект datetime для QDateEdit, конвертируем
        from datetime import datetime
        order_date = datetime.strptime(order_date_str, '%d.%m.%Y').date()

        dialog = OrderDetailsDialog(order_id, order_date, self.user_role, self)
        dialog.exec_()
        self.load_orders() # Обновляем список после закрытия (сумма могла измениться)

    def delete_order(self):
        """Удаляет выбранный заказ."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите заказ для удаления!")
            return

        order_id = self.table.item(current_row, 0).data(256)
        
        reply = QMessageBox.question(self, "Подтверждение", 
                                     f"Вы уверены, что хотите удалить заказ №{order_id}?\nВсе позиции этого заказа также будут удалены.", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                # Благодаря ON DELETE CASCADE в БД, позиции удалятся автоматически
                cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
                conn.commit()
                self.load_orders()
                QMessageBox.information(self, "Успех", "Заказ удален!")
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить заказ:\n{e}")
            finally:
                conn.close()