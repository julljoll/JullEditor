import type { APIRoute } from 'astro';
import { checkLocalPhiStatus } from '../../lib/llm-provider';

export const prerender = false;

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url);
  const endpoint = url.searchParams.get('endpoint') || 'http://localhost:11434';

  const status = await checkLocalPhiStatus(endpoint);

  return new Response(JSON.stringify(status), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};
