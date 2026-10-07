import asyncio

from agente.tools import buscar_cliente, buscar_pedidos, detalle_pedido


def correr(tool, **args):
    return asyncio.run(tool.ainvoke(args))


def test_buscar_cliente_ignora_tildes_y_mayusculas():
    r = correr(buscar_cliente, nombre="lucia FERNANDEZ")
    assert r["coincidencias"] == 1 and r["clientes"][0]["id"] == 103


def test_buscar_cliente_ambiguo_devuelve_todos():
    r = correr(buscar_cliente, nombre="garcia")
    assert {c["id"] for c in r["clientes"]} == {101, 104}


def test_buscar_cliente_inexistente_devuelve_error():
    assert "error" in correr(buscar_cliente, nombre="Fernandes")


def test_pedidos_del_cliente_102():
    r = correr(buscar_pedidos, cliente_id=102)
    assert (r["pedidos"], r["total"]) == (3, 14500)
    assert r["detalle"][-1]["id"] == 5004


def test_errores_de_ids():
    assert "error" in correr(buscar_pedidos, cliente_id=999)
    assert "error" in correr(detalle_pedido, pedido_id=9999)


def test_detalle_pedido():
    r = correr(detalle_pedido, pedido_id=5004)
    assert len(r["items"]) == 2 and r["total"] == 6200
