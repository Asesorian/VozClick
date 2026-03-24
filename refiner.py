"""
DictaFlow — Refiner IA multi-provider
Toma texto dictado desordenado y lo estructura según tipo de salida.
Providers: Groq Llama (gratis), OpenAI, Anthropic
"""
import logging

from config import REFINER_PROVIDERS, DEFAULT_REFINER_PROVIDER

logger = logging.getLogger(__name__)

# Output type-specific instructions
OUTPUT_INSTRUCTIONS = {
    "Prompt (estándar)": "Estructúralo en secciones claras: Contexto, Objetivo, Instrucciones y Restricciones.",
    "Correo electrónico": "Incluye asunto adecuado, saludo, cuerpo principal y despedida.",
    "Informe": "Usa formato estructurado con introducción, desarrollo en puntos clave y conclusión.",
    "Mensaje Slack/Chat": "Sé conciso y directo, usa párrafos cortos. Sin formalidades excesivas.",
    "Documentación técnica": "Estructura con secciones claras, ejemplos de código si aplica, y notas importantes.",
    "Lista de tareas": "Organiza en items accionables, priorizados si es posible, con contexto breve.",
    "Guion de vídeo": "Estructura en introducción (gancho), desarrollo visual/hablado, y cierre con llamada a la acción.",
    "Novela": "Usa un tono narrativo, une las escenas o personajes con descripciones ricas y flujo natural.",
}

SYSTEM_PROMPT_TEMPLATE = """Eres un asistente experto en estructurar, ordenar y dar formato a textos.
Tu tarea es procesar el input crudo (que puede estar desordenado) y convertirlo en un resultado excelente y listo para usar de tipo: '{output_type}'.

{context_block}REGLAS:
1. Mantén la intención e información proporcionada por el usuario. Si el input está desordenado o es una lluvia de ideas, ordénalo con lógica.
2. Adapta el tono, la estructura y el formato a lo que corresponde a '{output_type}'.
3. CRÍTICO: NO inventes datos que no se aporten. Si es necesario, deja marcadores claros (ej. [Nombre], [Fecha]).
4. Si hay nombres de archivos, código o variables, no los modifiques ni traduzcas.
5. Entrega DIRECTAMENTE el resultado final, sin introducciones tipo 'Aquí tienes...' ni comentarios extra.
6. {type_instruction}"""


def _build_system_prompt(output_type: str, context: str = "") -> str:
    context_block = f"CONTEXTO PROPORCIONADO:\n{context}\n\n" if context else ""
    type_instruction = OUTPUT_INSTRUCTIONS.get(output_type, f"Adapta al formato '{output_type}' de la mejor manera posible.")
    return SYSTEM_PROMPT_TEMPLATE.format(
        output_type=output_type,
        context_block=context_block,
        type_instruction=type_instruction,
    )


def refine_with_groq(text: str, output_type: str, context: str, api_key: str, model: str) -> str:
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _build_system_prompt(output_type, context)},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=4000,
    )
    return response.choices[0].message.content.strip()


def refine_with_openai(text: str, output_type: str, context: str, api_key: str, model: str) -> str:
    import openai
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _build_system_prompt(output_type, context)},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=4000,
    )
    return response.choices[0].message.content.strip()


def refine_with_anthropic(text: str, output_type: str, context: str, api_key: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=_build_system_prompt(output_type, context),
        messages=[{"role": "user", "content": text}],
    )
    return response.content[0].text.strip()


PROVIDER_FUNCTIONS = {
    "groq": refine_with_groq,
    "openai": refine_with_openai,
    "anthropic": refine_with_anthropic,
}


class RefinerError(Exception):
    pass


def refine_text(text: str, output_type: str, context: str,
                provider: str, api_key: str, model: str | None = None) -> str:
    """
    Refine raw dictated text into structured output.
    
    Args:
        text: Raw transcribed text
        output_type: Target format (email, report, prompt, etc.)
        context: Additional context from user
        provider: 'groq', 'openai', or 'anthropic'
        api_key: API key for the provider
        model: Override model (uses default from config if None)
    """
    if not api_key:
        raise RefinerError(f"API key no configurada para {provider}")
    
    if provider not in PROVIDER_FUNCTIONS:
        raise RefinerError(f"Provider desconocido: {provider}")
    
    if model is None:
        model = REFINER_PROVIDERS[provider]["model"]
    
    try:
        fn = PROVIDER_FUNCTIONS[provider]
        return fn(text, output_type, context, api_key, model)
    except Exception as e:
        logger.error(f"Refiner error ({provider}): {e}")
        raise RefinerError(f"Error al refinar: {e}")
