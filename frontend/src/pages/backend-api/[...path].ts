import type { APIRoute } from 'astro';

export const prerender = false;

const PROXY_HEADERS = ['content-type', 'content-disposition', 'cache-control'];

export const ALL: APIRoute = async ({ request, url }) => {
  const configuredBackend = process.env.BACKEND_API_URL?.trim();
  if (process.env.VERCEL && !configuredBackend) {
    return Response.json(
      { detail: 'Configura BACKEND_API_URL con la URL del backend FastAPI.' },
      { status: 503 },
    );
  }

  const backend = configuredBackend || 'http://127.0.0.1:8000';
  const path = url.pathname.slice('/backend-api'.length);
  const upstreamUrl = new URL(path + url.search, backend);
  const headers = new Headers();

  for (const name of ['accept', 'content-type']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  try {
    const response = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: ['GET', 'HEAD'].includes(request.method)
        ? undefined
        : await request.arrayBuffer(),
      signal: request.signal,
    });
    const responseHeaders = new Headers();
    for (const name of PROXY_HEADERS) {
      const value = response.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`FastAPI proxy failed for ${upstreamUrl.pathname}:`, error);
    return Response.json(
      { detail: 'No se pudo conectar con el motor FastAPI local.' },
      { status: 502 },
    );
  }
};
