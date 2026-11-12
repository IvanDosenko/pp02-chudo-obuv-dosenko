-- Роли
INSERT INTO roles (role_name) VALUES ('admin'), ('manager'), ('user');

-- Пользователи
INSERT INTO users (last_name, first_name, middle_name, login, role_id) VALUES 
('Иванов', 'Иван', 'Иванович', 'admin', 1),
('Петров', 'Петр', 'Петрович', 'manager1', 2),
('Сидорова', 'Анна', 'Сергеевна', 'user1', 3);

-- Размеры
INSERT INTO sizes (size_value) VALUES (36), (37), (38), (39), (40), (41), (42), (43), (44), (45);

-- Товары (добавим пути к картинкам, если их нет - сработает заглушка)
INSERT INTO products (category, manufacturer, name, image_path, composition, description, price) VALUES 
('Мужская', 'Nike', 'Air Max', 'nike.jpg', 'Текстиль', 'Кроссовки для бега', 8000.00),
('Женская', 'Ecco', 'Shape 55', 'ecco.jpg', 'Кожа', 'Туфли классические', 12000.00),
('Детская', 'Adidas', 'Sandals', '', 'Синтетика', 'Сандалии', 3000.00);

-- Остатки (товар 1: размеры 40, 41; товар 2: 37, 38; товар 3: 36)
INSERT INTO stock_items (product_id, size_id, quantity) VALUES 
(1, 5, 10), (1, 6, 2), (2, 2, 5), (3, 1, 20);