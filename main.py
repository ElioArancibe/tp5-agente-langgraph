import argparse
import asyncio
import json
import sys
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.errors import GraphRecursionError

from agente.config import get_settings
from agente.grafo import construir_grafo
from agente.tienda import crear_base


def _contenido(mensaje) -> str | dict:
    if isinstance(mensaje, ToolMessage):
        try:
            return json.loads(mensaje.content)
        except (TypeError, ValueError):
            return mensaje.content
    return mensaje.text


async def preguntar(app, pregunta: str, config: dict) -> dict:
    """Corre un turno del grafo y arma la traza ReAct (qué nodo hizo qué)."""
    pasos = []
    respuesta = ""
    entrada = {"messages": [HumanMessage(pregunta)]}

    async for update in app.astream(entrada, config, stream_mode="updates"):
        for nodo, salida in update.items():
            for msg in salida.get("messages", []):
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    pasos.append({
                        "nodo": nodo,
                        "accion": "llamar_herramienta",
                        "llamadas": [{"tool": tc["name"], "args": tc["args"]} for tc in msg.tool_calls],
                    })
                elif isinstance(msg, ToolMessage):
                    pasos.append({"nodo": nodo, "tool": msg.name, "resultado": _contenido(msg)})
                elif isinstance(msg, AIMessage):
                    respuesta = _contenido(msg)
                    pasos.append({"nodo": nodo, "accion": "responder", "texto": respuesta})

    return {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "pregunta": pregunta,
        "pasos": pasos,
        "llamadas_a_herramientas": sum(1 for p in pasos if "tool" in p),
        "respuesta": respuesta,
    }


def guardar_traza(path, thread_id: str, turno: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    traza = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"thread_id": thread_id, "turnos": []}
    traza["turnos"].append(turno)
    path.write_text(json.dumps(traza, ensure_ascii=False, indent=2), encoding="utf-8")


async def main(thread_id: str) -> None:
    settings = get_settings()
    crear_base(settings.tienda_db)
    config = {"recursion_limit": settings.recursion_limit, "configurable": {"thread_id": thread_id}}
    traza_path = settings.trazas_dir / f"{thread_id}.json"

    async with AsyncSqliteSaver.from_conn_string(str(settings.memoria_db)) as checkpointer:
        app = construir_grafo(settings, checkpointer)
        print(f"Sesión '{thread_id}'. Escribí tu consulta ('salir' para terminar).\n")

        while True:
            try:
                pregunta = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not pregunta:
                continue
            if pregunta.lower() in {"salir", "exit", "quit"}:
                break

            try:
                turno = await preguntar(app, pregunta, config)
            except GraphRecursionError:
                print("El agente no llegó a una respuesta dentro del límite de pasos. Probá reformular.\n")
                continue
            except Exception as exc:
                detalle = str(exc)
                if "RESOURCE_EXHAUSTED" in detalle or "429" in detalle:
                    print("Se agotó la cuota de la API de Gemini. Probá de nuevo en un rato.\n")
                else:
                    print(f"Error al consultar el modelo: {detalle.splitlines()[0][:200]}\n")
                continue

            print(f"\n{turno['respuesta']}\n")
            guardar_traza(traza_path, thread_id, turno)


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Agente de consultas de pedidos (LangGraph + Gemini)")
    parser.add_argument("--thread", default="sesion-1", help="id de la conversación; mismo id = misma memoria")
    args = parser.parse_args()
    asyncio.run(main(args.thread))
