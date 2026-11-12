CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    login VARCHAR(20) UNIQUE NOT NULL CHECK(length(login) BETWEEN 3 AND 20),
    role_id INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    image_path VARCHAR(255),
    composition TEXT,
    description TEXT,
    price NUMERIC(10,2) NOT NULL CHECK(price > 0)
);

CREATE TABLE sizes (
    size_id SERIAL PRIMARY KEY,
    size_value NUMERIC(4,1) NOT NULL
);

CREATE TABLE stock_items (
    stock_item_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    size_id INTEGER NOT NULL REFERENCES sizes(size_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK(quantity >= 0)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    stock_item_id INTEGER NOT NULL REFERENCES stock_items(stock_item_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price_at_order NUMERIC(10,2) NOT NULL CHECK(price_at_order > 0)
);