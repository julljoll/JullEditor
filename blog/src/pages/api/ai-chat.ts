import type { APIRoute } from 'astro';
import { chatWithModel, type ChatMessage, type LLMProvider } from '../../lib/llm-provider';

export const prerender = false;

const CHAT_SYSTEM_INSTRUCTION = `Eres el Agente Copiloto Editorial & Pericial de JullEditor para el laboratorio sha256.us.
Tu misión es asistir interactivamente al autor en la redacción, revisión, pulido, ampliación y aseguramiento técnico de artículos de ciberseguridad forense, peritaje digital y doctrina jurídica según el derecho positivo de la República Bolivariana de Venezuela 🇻🇪.

PRINCIPIOS FUNDAMENTALES:
1. Especialidad Dogmática y Técnica: Dominas la Constitución (Arts. 28, 60, 110), Ley Especial contra los Delitos Informáticos (G.O. 37.313), Ley de Mensajes de Datos y Firmas Electrónicas (G.O. 37.148), Ley de Infogobierno (G.O. 40.274), Manual de Cadena de Custodia MP/CICPC 2017, directrices ISO/IEC 27037 y preservación RFC 3227.
2. Formato Blog -Astro.md (sha256.us): Conoces a fondo la estructura de 3 columnas:
   - Frontmatter YAML completo.
   - <div class="editorial-container">
   - <div class="editorial-lead">
   - <div class="editorial-quote">
   - <div class="editorial-three-columns"> con EXACTAMENTE 6 bloques <div class="editorial-col">.
   - Preguntas Frecuentes (FAQ).
   - <div class="editorial-author-box"> para Equipo Pericial sha256.us.

3. REGLA DE VOLUMEN PARA RELLENO DE 3 COLUMNAS (CERO ESPACIOS EN BLANCO):
   - Para que las 3 columnas queden 100% llenas de texto sin dejar fondos vacíos ni espacios en blanco al pie, cada bloque <div class="editorial-col"> debe poseer entre 1.350 y 1.600 caracteres (~200 a 240 palabras), sumando entre 8.000 y 9.200 caracteres dentro de las 3 columnas (~10.500 caracteres totales en el artículo).
   - Si el artículo está corto o desbalanceado, amplía los párrafos con doctrina jurídica o metodología forense para igualar el nivel vertical de las 3 columnas.

4. COLOCACIÓN DE NEGRITAS EN PALABRAS CLAVE:
   - En CADA párrafo del artículo deben colocarse negritas (**término** o <strong>término</strong>) en 2 o 3 conceptos rectores (normas legales, estándares ISO/RFC, términos periciales como cadena de custodia, hash SHA-256, memoria RAM).

INSTRUCCIONES DE RESPUESTA EN CHAT:
- Sé conciso, profesional, analítico y directo.
- Si el usuario te pide modificar, agregar contenido, pulir o corregir el artículo actual, explícale brevemente la mejora y proporciónele el bloque Markdown o la versión actualizada completa delimitada en un bloque de código:
\`\`\`markdown
---
...
\`\`\`
- Si el usuario hace una consulta teórica o legal, responde con rigor pericial sin rodeos.`;

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const provider: LLMProvider = body.provider === 'phi' ? 'phi' : 'gemini';
    const apiKey = body.api_key;
    const localEndpoint = body.local_endpoint || 'http://localhost:11434';
    const phiModel = body.phi_model || 'phi3';
    const currentArticle = body.current_article ? body.current_article.trim() : '';

    let history: ChatMessage[] = Array.isArray(body.messages) ? body.messages : [];

    // Si viene una instrucción única
    if (body.instruction && typeof body.instruction === 'string') {
      history.push({ role: 'user', content: body.instruction });
    }

    if (history.length === 0) {
      return new Response(JSON.stringify({
        error: 'No se enviaron mensajes para la conversación.',
      }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }

    // Contextualizar el primer mensaje del usuario con el artículo actual si existe
    let enrichedSystem = CHAT_SYSTEM_INSTRUCTION;
    if (currentArticle) {
      enrichedSystem += `\n\nARTÍCULO ACTUAL EN EL EDITOR DEL USUARIO:\n"""\n${currentArticle.slice(0, 8000)}\n"""\nUsa este contenido como referencia cuando el usuario solicite ajustes o adiciones.`;
    }

    const result = await chatWithModel(history, enrichedSystem, {
      provider,
      apiKey,
      localEndpoint,
      phiModel,
      temperature: 0.35,
    });

    // Detectar si la respuesta contiene un artículo markdown completo actualizado
    let updatedArticle: string | null = null;
    const mdBlockMatch = result.reply.match(/```(?:markdown|md)?\s*\n([\s\S]*?)\n```/i);
    if (mdBlockMatch && (mdBlockMatch[1].includes('editorial-container') || mdBlockMatch[1].startsWith('---'))) {
      updatedArticle = mdBlockMatch[1].trim();
    }

    return new Response(JSON.stringify({
      success: true,
      reply: result.reply,
      updatedArticle,
      providerUsed: result.providerUsed,
      modelName: result.modelName,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (err: any) {
    console.error('Error en /api/ai-chat:', err);
    return new Response(JSON.stringify({
      error: err.message || 'Error al comunicarse con el agente de IA.',
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
