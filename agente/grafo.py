from langchain_core.messages import SystemMessage, trim_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .config import Settings
from .tools import TOOLS

SYSTEM_PROMPT = """Sos el asistente de atención de una tienda de tecnología.
Respondé en español rioplatense, breve y con los datos exactos que devuelven las herramientas.
- No inventes datos: si necesitás información de clientes o pedidos, usá las herramientas.
- Si una herramienta devuelve un error, leelo y probá otra herramienta o pedí una aclaración.
- Si una búsqueda devuelve varios clientes, preguntá a cuál se refiere antes de seguir.
- Los montos están en pesos: escribilos como $14.500."""


class Estado(MessagesState):
    pass


def crear_llm(settings: Settings):
    def modelo(nombre: str):
        llm = ChatGoogleGenerativeAI(
            model=nombre,
            api_key=settings.api_key,
            temperature=settings.temperature,
            max_retries=2,
        )
        return llm.bind_tools(TOOLS)

    llm = modelo(settings.model)
    if settings.fallback_model:
        llm = llm.with_fallbacks([modelo(settings.fallback_model)])
    return llm


def construir_grafo(settings: Settings, checkpointer=None):
    llm = crear_llm(settings)

    async def agente(state: Estado) -> dict:
        # el checkpointer guarda todo, pero al modelo solo le mandamos lo último
        historial = trim_messages(
            state["messages"],
            max_tokens=settings.max_historial,
            token_counter=len,
            strategy="last",
            start_on="human",
        )
        respuesta = await llm.ainvoke([SystemMessage(SYSTEM_PROMPT), *historial])
        return {"messages": [respuesta]}

    grafo = StateGraph(Estado)
    grafo.add_node("agente", agente)
    grafo.add_node("tools", ToolNode(TOOLS, handle_tool_errors=True))
    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", tools_condition)
    grafo.add_edge("tools", "agente")
    return grafo.compile(checkpointer=checkpointer)
