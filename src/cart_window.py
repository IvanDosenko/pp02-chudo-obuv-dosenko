from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QMessageBox, QHeaderView)
from src.db_utils import get_connection
from datetime import date

class CartWindow(QDialog):
    def __init__(self, cart_items, user_id, parent=None):
        super().__init__(parent)
        self.cart_items = cart_items # Список словарей с добавленными товарами
        self.user_id = user_id
        self.setWindowTitle("Корзина")
        self.resize(600, 400)
        self.order_created = False

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Товар (ID)", "Размер", "Кол-во", "Сумма"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.lbl_total = QPushButton()
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #e0e0e0; padding: 10px;")
        layout.addWidget(self.lbl_total)

        self.btn_checkout = QPushButton("Оформить заказ")
        self.btn_checkout.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        self.btn_checkout.clicked.connect(self.checkout)
        layout.addWidget(self.btn_checkout)

        self.setLayout(layout)
        self.update_table()

    def update_table(self):
        """Обновляет вид корзины и итоговую сумму."""
        self.table.setRowCount(len(self.cart_items))
        total_sum = 0

        for row, item in enumerate(self.cart_items):
            item_sum = item['price'] * item['qty']
            total_sum += item_sum

            self.table.setItem(row, 0, QTableWidgetItem(str(item['product_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(str(item['size'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(item['qty'])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item_sum:.2f} руб."))

        self.lbl_total.setText(f"Итого к оплате: {total_sum:.2f} руб.")

    def checkout(self):
        """Сохранение заказа в БД с использованием транзакции."""
        if not self.cart_items:
            QMessageBox.warning(self, "Внимание", "Корзина пуста!")
            return

        conn = get_connection()
        try:
            cursor = conn.cursor()
            # Начинаем транзакцию (по умолчанию в psycopg2 она начинается автоматически, но явно скажем об этом)
            cursor.execute("BEGIN")
            
            # 1. Создаем заказ
            today = date.today()
            cursor.execute("""
                INSERT INTO orders (order_date, user_id) 
                VALUES (%s, %s) RETURNING order_id
            """, (today, self.user_id))
            order_id = cursor.fetchone()[0]

            # 2. Добавляем позиции и обновляем остатки
            for item in self.cart_items:
                # Добавляем в order_items
                cursor.execute("""
                    INSERT INTO order_items (order_id, stock_item_id, quantity, price_at_order) 
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['stock_item_id'], item['qty'], item['price']))

                # Проверяем, хватает ли товара (защита от гонок данных)
                cursor.execute("SELECT quantity FROM stock_items WHERE stock_item_id = %s FOR UPDATE", (item['stock_item_id'],))
                current_stock = cursor.fetchone()[0]
                
                if current_stock < item['qty']:
                    raise Exception(f"Недостаточно товара на складе для {item['product_id']} (размер {item['size']})")

                # Уменьшаем остаток
                cursor.execute("""
                    UPDATE stock_items 
                    SET quantity = quantity - %s 
                    WHERE stock_item_id = %s
                """, (item['qty'], item['stock_item_id']))

            # Если все прошло успешно - коммитим
            conn.commit()
            QMessageBox.information(self, "Успех", f"Заказ №{order_id} успешно оформлен!")
            self.order_created = True
            self.accept() # Закрываем окно корзины

        except Exception as e:
            # Откатываем изменения в случае ошибки
            conn.rollback()
            QMessageBox.critical(self, "Ошибка оформления", f"Заказ не оформлен:\n{e}")
        finally:
            conn.close()