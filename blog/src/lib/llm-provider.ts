/**
 * Proveedor Unificado de Modelos LLM: Google Gemini (Online) & Microsoft Phi (Local)
 * Diseñado para operar en la nube o en entornos locales con Ollama / LM Studio.
 */

export type LLMProvider = 'gemini' | 'phi';

export interface LLMRequestOptions {
  provider?: LLMProvider;
  apiKey?: string;
  localEndpoint?: string;
  phiModel?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

/**
 * Consulta de estado y modelos disponibles en Microsoft Phi local (Ollama o LM Studio)
 */
export async function checkLocalPhiStatus(endpoint: string = 'http://localhost:11434'): Promise<{
  connected: boolean;
  models: string[];
  message: string;
}> {
  const cleanEndpoint = endpoint.replace(/\/+$/, '');
  try {
    const isV1 = cleanEndpoint.endsWith('/v1');
    const tagsUrl = isV1 ? `${cleanEndpoint}/models` : `${cleanEndpoint}/api/tags`;

    const res = await fetch(tagsUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000),
    });

    if (!res.ok) {
      return {
        connected: false,
        models: [],
        message: `Servidor local respondió con código HTTP ${res.status}`,
      };
    }

    const data = await res.json();
    let modelNames: string[] = [];

    if (Array.isArray(data.models)) {
      // Formato Ollama
      modelNames = data.models.map((m: any) => m.name || m.model).filter(Boolean);
    } else if (Array.isArray(data.data)) {
      // Formato OpenAI / LM Studio
      modelNames = data.data.map((m: any) => m.id).filter(Boolean);
    }

    return {
      connected: true,
      models: modelNames,
      message: modelNames.length > 0 
        ? `Conectado a Microsoft Phi local (${modelNames.length} modelos detectados)` 
        : 'Conectado a servidor local (no se encontraron modelos descargados aún)',
    };
  } catch (err: any) {
    return {
      connected: false,
      models: [],
      message: `No se pudo conectar a ${cleanEndpoint}. Inicia Ollama con 'ollama serve' o 'ollama run phi3'.`,
    };
  }
}

/**
 * Ejecución de Generación Directa con Gemini o Microsoft Phi
 */
export async function generateWithModel(
  prompt: string,
  systemInstruction: string,
  options: LLMRequestOptions = {}
): Promise<{ text: string; providerUsed: LLMProvider; modelName: string }> {
  const provider: LLMProvider = options.provider === 'phi' ? 'phi' : 'gemini';

  if (provider === 'phi') {
    return await callMicrosoftPhi(prompt, systemInstruction, options);
  } else {
    return await callGoogleGemini(prompt, systemInstruction, options);
  }
}

/**
 * Generación con Microsoft Phi (Local - Ollama / LM Studio)
 */
async function callMicrosoftPhi(
  prompt: string,
  systemInstruction: string,
  options: LLMRequestOptions
): Promise<{ text: string; providerUsed: 'phi'; modelName: string }> {
  const endpoint = (options.localEndpoint || process.env.OLLAMA_BASE_URL || 'http://localhost:11434').replace(/\/+$/, '');
  const model = options.phiModel || process.env.FAST_MODEL || 'phi3';

  // Soporte para endpoints compatibles con OpenAI (/v1)
  if (endpoint.endsWith('/v1')) {
    try {
      const res = await fetch(`${endpoint}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: [
            { role: 'system', content: systemInstruction },
            { role: 'user', content: prompt }
          ],
          temperature: options.temperature ?? 0.25,
          max_tokens: options.maxTokens ?? 4000,
        }),
        signal: AbortSignal.timeout(60000),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Error en servidor local Phi (${res.status}): ${errorText}`);
      }

      const data = await res.json();
      const content = data.choices?.[0]?.message?.content || '';
      return { text: content, providerUsed: 'phi', modelName: model };
    } catch (err: any) {
      if (err.name === 'TimeoutError') {
        throw new Error(`El modelo local Microsoft Phi en ${endpoint} tardó más de 60 segundos en responder.`);
      }
      throw new Error(`Fallo de conexión con Microsoft Phi local en ${endpoint}: ${err.message}. Asegúrate de ejecutar 'ollama serve' o 'ollama run phi3'.`);
    }
  }

  // Endpoints estándar de Ollama (/api/generate)
  try {
    const res = await fetch(`${endpoint}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        system: systemInstruction,
        prompt,
        stream: false,
        options: {
          temperature: options.temperature ?? 0.25,
          num_predict: options.maxTokens ?? 4000,
        }
      }),
      signal: AbortSignal.timeout(90000),
    });

    if (!res.ok) {
      if (res.status === 404) {
        throw new Error(`El modelo '${model}' no está descargado en tu Ollama local. Ejecuta en tu terminal: 'ollama pull ${model}' o 'ollama run phi3'.`);
      }
      const errorText = await res.text();
      throw new Error(`Error en Ollama (${res.status}): ${errorText}`);
    }

    const data = await res.json();
    const text = data.response || '';
    if (!text) {
      throw new Error('Microsoft Phi no retornó contenido en la respuesta.');
    }

    return { text, providerUsed: 'phi', modelName: model };
  } catch (err: any) {
    if (err.name === 'TimeoutError') {
      throw new Error(`Microsoft Phi (${model}) en ${endpoint} excedió el tiempo límite.`);
    }
    throw new Error(`No se pudo comunicar con Microsoft Phi en ${endpoint}. Detalle: ${err.message}. Para usarlo en local ejecuta 'ollama run phi3'.`);
  }
}

/**
 * Generación con Google Gemini REST API
 */
async function callGoogleGemini(
  prompt: string,
  systemInstruction: string,
  options: LLMRequestOptions
): Promise<{ text: string; providerUsed: 'gemini'; modelName: string }> {
  const clientKey = options.apiKey?.trim();
  const serverKey = process.env.GEMINI_API_KEY?.trim() || process.env.API_KEY?.trim();
  const keyToUse = clientKey || serverKey;

  if (!keyToUse) {
    throw new Error('Falta la API Key de Gemini. Ingresa tu clave en el campo de configuración del editor.');
  }

  const modelVersion = 'gemini-3.5-flash-lite';
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelVersion}:generateContent?key=${encodeURIComponent(keyToUse)}`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      systemInstruction: {
        parts: [{ text: systemInstruction }]
      },
      contents: [
        {
          role: 'user',
          parts: [{ text: prompt }]
        }
      ],
      generationConfig: {
        temperature: options.temperature ?? 0.25,
        maxOutputTokens: options.maxTokens ?? 5000,
      }
    })
  });

  const data = await res.json();
  if (data.error) {
    throw new Error(`Gemini API: ${data.error.message || 'Error en Google Generative Language'}`);
  }

  const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  if (!text) {
    throw new Error('Gemini no devolvió contenido.');
  }

  return { text, providerUsed: 'gemini', modelName: modelVersion };
}

/**
 * Conversación Multi-Turno (Chat) con Gemini o Microsoft Phi
 */
export async function chatWithModel(
  messages: ChatMessage[],
  systemInstruction: string,
  options: LLMRequestOptions = {}
): Promise<{ reply: string; providerUsed: LLMProvider; modelName: string }> {
  const provider: LLMProvider = options.provider === 'phi' ? 'phi' : 'gemini';

  if (provider === 'phi') {
    const endpoint = (options.localEndpoint || process.env.OLLAMA_BASE_URL || 'http://localhost:11434').replace(/\/+$/, '');
    const model = options.phiModel || process.env.FAST_MODEL || 'phi3';

    // Formatear mensajes con system incluido
    const ollamaMessages = [
      { role: 'system', content: systemInstruction },
      ...messages.map(m => ({ role: m.role, content: m.content }))
    ];

    try {
      const res = await fetch(`${endpoint}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: ollamaMessages,
          stream: false,
          options: {
            temperature: options.temperature ?? 0.3,
          }
        }),
        signal: AbortSignal.timeout(60000),
      });

      if (!res.ok) {
        throw new Error(`Error en servidor local Phi (${res.status}): ${await res.text()}`);
      }

      const data = await res.json();
      const reply = data.message?.content || '';
      return { reply, providerUsed: 'phi', modelName: model };
    } catch (err: any) {
      throw new Error(`Error comunicando con Microsoft Phi local: ${err.message}. Para local, inicia 'ollama run phi3'.`);
    }
  } else {
    // Gemini Chat via generateContent
    const clientKey = options.apiKey?.trim();
    const serverKey = process.env.GEMINI_API_KEY?.trim() || process.env.API_KEY?.trim();
    const keyToUse = clientKey || serverKey;

    if (!keyToUse) {
      throw new Error('Falta la API Key de Gemini para el chat.');
    }

    const modelVersion = 'gemini-3.5-flash-lite';
    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelVersion}:generateContent?key=${encodeURIComponent(keyToUse)}`;

    // Mapear historial de chat a formato Gemini (contents con 'user' y 'model')
    const contents = messages.map(m => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }]
    }));

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        systemInstruction: {
          parts: [{ text: systemInstruction }]
        },
        contents,
        generationConfig: {
          temperature: options.temperature ?? 0.35,
          maxOutputTokens: 4000,
        }
      })
    });

    const data = await res.json();
    if (data.error) {
      throw new Error(`Gemini Chat: ${data.error.message || 'Error en la API'}`);
    }

    const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    return { reply, providerUsed: 'gemini', modelName: modelVersion };
  }
}
