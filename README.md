# Agente de pedidos con LangGraph

Agente ReAct que responde consultas sobre clientes y pedidos de una tienda. Usa Gemini con tool calling, un `StateGraph` basado en `MessagesState` y memoria persistente en SQLite (`AsyncSqliteSaver`, la versión async de `SqliteSaver`).

```
START → agente ⇄ tools → (sin tool calls) → END
```

Herramientas (`agente/tools.py`): `buscar_cliente`, `buscar_pedidos` y `detalle_pedido`, sobre una base SQLite de ejemplo que se crea sola en `data/tienda.db`.

## Uso

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # completar GEMINI_API_KEY
python main.py --thread sesion-1
```

Las consultas se escriben por consola (`salir` para terminar). Con el mismo `--thread` el agente recuerda la conversación aunque se reinicie el programa. Cada turno se guarda en `trazas/<thread>.json`.

`recursion_limit` está en 10 pasos por consulta.

## Traza de ejemplo

[`trazas/ejemplo_traza.json`](trazas/ejemplo_traza.json):

```
> ¿Cuánto gastó en total Lucía Fernandes?
  buscar_cliente("Lucía Fernandes")  → error: no hay coincidencias
  buscar_cliente("Lucía")            → Lucía Fernández (id 103)
  buscar_pedidos(103)                → 1 pedido, total 12000
Lucía Fernández gastó un total de $12.000 (en su único pedido, que figura como cancelado).
```

## Tests

```bash
pytest
```
