INSERT INTO categoria (descripcion) VALUES ('MATERIA PRIMA');
INSERT INTO categoria (descripcion) VALUES ('PARA VENTA');

INSERT INTO tipo_venta(nombre) VALUES ('Mostrador'), ('Entrega propia'), ('Retiro en tienda');

INSERT INTO iva (descripcion) VALUES ('10');
INSERT INTO iva (descripcion) VALUES ('5');

INSERT INTO tipo_pago (descripcion) VALUES ('Efectivo');
INSERT INTO tipo_pago (descripcion) VALUES ('POS');
INSERT INTO tipo_pago (descripcion) VALUES ('Transferencia');

INSERT INTO clientes (
    documento, nombre, apellido, correo, celular, direccion, estado
) VALUES (
    '0000000',
    'Cliente',
    'Generico',
    'cliente.generico@elartesano.local',
    '000000000',
    'Sin direccion',
    'ACTIVO'
);

INSERT INTO public.productos (
    nombre, precio_actual, stock_minimo, stock_actual, costo_actual, usuario_creacion, usuario_modificacion, fecha_creacion, fecha_modificacion, id_iva
) VALUES
('Billetera de cuero clasica', 85000, 3, 10, 45000, 1, NULL, NOW(), NULL, 1),
('Cinturon de cuero artesanal', 120000, 2, 8, 65000, 1, NULL, NOW(), NULL, 1),
('Porta documentos cuero', 95000, 2, 6, 50000, 1, NULL, NOW(), NULL, 1),
('Bandolera de cuero', 280000, 1, 4, 160000, 1, NULL, NOW(), NULL, 1),
('Llaveros de cuero', 25000, 10, 30, 10000, 1, NULL, NOW(), NULL, 1);
