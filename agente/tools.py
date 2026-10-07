import unicodedata

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .config import get_settings
from .tienda import consultar


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c)).strip()


class BuscarClienteInput(BaseModel):
    nombre: str = Field(min_length=2, description="Nombre, apellido o parte del nombre del cliente")


class PedidosInput(BaseModel):
    cliente_id: int = Field(gt=0, description="ID numérico del cliente (ej. 102)")


class DetalleInput(BaseModel):
    pedido_id: int = Field(gt=0, description="ID numérico del pedido (ej. 5004)")


@tool(args_schema=BuscarClienteInput)
async def buscar_cliente(nombre: str) -> dict:
    """Busca clientes de la tienda por nombre o apellido (no distingue mayúsculas ni tildes).

    Devuelve los clientes que coinciden con su id, email y ciudad. Usala cuando el usuario
    menciona a un cliente por su nombre y necesitás el cliente_id para otras consultas.
    Si hay más de una coincidencia, pedile al usuario que aclare a cuál se refiere.
    """
    clientes = await consultar(get_settings().tienda_db, "SELECT * FROM clientes")
    buscado = _normalizar(nombre)
    encontrados = [c for c in clientes if buscado in _normalizar(c["nombre"])]
    if not encontrados:
        return {"error": f"No hay clientes que coincidan con '{nombre}'. Revisá el nombre o pedí el ID."}
    return {"coincidencias": len(encontrados), "clientes": encontrados}


@tool(args_schema=PedidosInput)
async def buscar_pedidos(cliente_id: int) -> dict:
    """Devuelve el historial de pedidos de un cliente a partir de su ID numérico.

    Incluye la cantidad de pedidos, el monto total gastado (en pesos) y la lista de pedidos
    con id, fecha, estado (preparando, en camino, entregado, cancelado) y total, ordenados
    del más viejo al más reciente. No incluye los productos: para eso usá detalle_pedido.
    """
    db = get_settings().tienda_db
    if not await consultar(db, "SELECT id FROM clientes WHERE id = ?", (cliente_id,)):
        return {"error": f"No existe el cliente {cliente_id}. Si tenés el nombre, usá buscar_cliente."}

    pedidos = await consultar(
        db,
        "SELECT id, fecha, estado, total FROM pedidos WHERE cliente_id = ? ORDER BY fecha",
        (cliente_id,),
    )
    return {
        "cliente_id": cliente_id,
        "pedidos": len(pedidos),
        "total": sum(p["total"] for p in pedidos),
        "detalle": pedidos,
    }


@tool(args_schema=DetalleInput)
async def detalle_pedido(pedido_id: int) -> dict:
    """Devuelve los productos de un pedido puntual: nombre, cantidad y precio unitario.

    Usala cuando el usuario pregunta qué compró en un pedido específico. Necesita el ID
    del pedido, que se obtiene con buscar_pedidos.
    """
    db = get_settings().tienda_db
    pedido = await consultar(db, "SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
    if not pedido:
        return {"error": f"No existe el pedido {pedido_id}. Consultá los IDs con buscar_pedidos."}
    items = await consultar(
        db, "SELECT producto, cantidad, precio_unitario FROM items WHERE pedido_id = ?", (pedido_id,)
    )
    return {**pedido[0], "items": items}


TOOLS = [buscar_cliente, buscar_pedidos, detalle_pedido]
