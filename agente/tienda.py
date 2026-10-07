"""Base SQLite de ejemplo (clientes, pedidos e items) que consultan las herramientas."""

import sqlite3
from pathlib import Path

import aiosqlite

CLIENTES = [
    (101, "Ana García", "ana.garcia@mail.com", "Córdoba"),
    (102, "Martín López", "martin.lopez@mail.com", "Rosario"),
    (103, "Lucía Fernández", "lucia.f@mail.com", "Mendoza"),
    (104, "Diego García", "dgarcia@mail.com", "Buenos Aires"),
    (105, "Sofía Romero", "sofi.romero@mail.com", "La Plata"),
]

PEDIDOS = [
    (5001, 101, "2026-07-02", "entregado", 8200),
    (5002, 102, "2026-07-15", "entregado", 3500),
    (5003, 102, "2026-08-21", "entregado", 4800),
    (5004, 102, "2026-09-30", "en camino", 6200),
    (5005, 103, "2026-08-05", "cancelado", 12000),
    (5006, 104, "2026-09-12", "entregado", 2750),
    (5007, 101, "2026-09-28", "preparando", 15400),
]

ITEMS = [
    (5001, "Auriculares inalámbricos", 1, 8200),
    (5002, "Mouse óptico", 1, 3500),
    (5003, "Teclado mecánico", 1, 4800),
    (5004, "Hub USB-C", 2, 1900),
    (5004, "Cable HDMI 2m", 2, 1200),
    (5005, "Monitor 24 pulgadas", 1, 12000),
    (5006, "Pad para mouse", 1, 2750),
    (5007, "Webcam Full HD", 1, 9400),
    (5007, "Micrófono USB", 1, 6000),
]


def crear_base(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.executescript(
            """
            CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT, email TEXT, ciudad TEXT);
            CREATE TABLE pedidos (id INTEGER PRIMARY KEY, cliente_id INTEGER REFERENCES clientes(id),
                                  fecha TEXT, estado TEXT, total INTEGER);
            CREATE TABLE items (pedido_id INTEGER REFERENCES pedidos(id), producto TEXT,
                                cantidad INTEGER, precio_unitario INTEGER);
            """
        )
        con.executemany("INSERT INTO clientes VALUES (?, ?, ?, ?)", CLIENTES)
        con.executemany("INSERT INTO pedidos VALUES (?, ?, ?, ?, ?)", PEDIDOS)
        con.executemany("INSERT INTO items VALUES (?, ?, ?, ?)", ITEMS)


async def consultar(path: Path, sql: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(path) as con:
        con.row_factory = aiosqlite.Row
        async with con.execute(sql, params) as cur:
            return [dict(row) for row in await cur.fetchall()]
