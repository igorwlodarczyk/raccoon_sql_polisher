SELECT departments.department_name,
AVG ( employees.salary )   AS avg_salary
FROM employees
JOIN   departments
ON employees.department_id=departments.department_id
GROUP BY departments.department_name
HAVING  AVG ( employees.salary )    >50000;

SELECT products.product_name,COUNT(orders.order_id)AS order_count
FROM products
LEFT   JOIN order_items
ON products.product_id=order_items.product_id
LEFT JOIN orders
ON order_items.order_id=orders.order_id
GROUP BY
products.product_name;

DELETE  FROM employees   e USING   departments d WHERE e.department_id=d.department_id
AND d.department_name='marketing';

CREATE  TABLE users (
id serial PRIMARY KEY,
 name   VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL,
created_at TIMESTAMP DEFAULT now());

INSERT INTO users (name,email)VALUES
('Jan Kowalski','jan.kowalski@example.com'),
('Anna Nowak' , 'anna.nowak@example.com'),
( 'Piotr Wiśniewski','piotr.wisniewski@example.com');

SELECT *
FROM users;

UPDATE  users
SET email=  'nowy.email@example.com'
WHERE   name= 'Jan Kowalski';

DELETE
FROM   users WHERE
name ='Piotr Wiśniewski';
