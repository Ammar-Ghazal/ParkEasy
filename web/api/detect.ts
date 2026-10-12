// Serverless proxy for Roboflow, deployed on Vercel.
//
// The browser sends a photo here; this function adds the Roboflow API key from
// the ROBOFLOW_API_KEY environment variable and forwards the request. The key
// never reaches the browser.
//
// Environment variables (set in the Vercel project settings):
//   ROBOFLOW_API_KEY   required
//   ALLOWED_ORIGINS    optional, comma-separated extra origins allowed to call
//                      this endpoint (the deployment's own origin always is)

const ROBOFLOW_URL = 'https://serverless.roboflow.com';

// Only these models can be requested, so the key cannot be used for anything else.
const ALLOWED_MODELS = ['parking-space-detect/1'];
const DEFAULT_ORIGINS = ['https://ammar-ghazal.github.io'];

const MAX_IMAGE_CHARS = 4_000_000; // about 3 MB of image data as base64
const RATE_LIMIT = 10; // requests per IP per window
const RATE_WINDOW_MS = 60_000;

// Best-effort limit: memory is per function instance, so this slows down casual
// abuse but is not a hard guarantee.
const hits = new Map<string, number[]>();

function rateLimited(ip: string): boolean {
    const now = Date.now();
    const recent = (hits.get(ip) ?? []).filter((t) => now - t < RATE_WINDOW_MS);
    recent.push(now);
    hits.set(ip, recent);
    if (hits.size > 5000) hits.clear();
    return recent.length > RATE_LIMIT;
}

function allowedOrigin(request: Request): string | null {
    const origin = request.headers.get('origin');
    if (!origin) return null;
    const extra = (process.env.ALLOWED_ORIGINS ?? '')
        .split(',')
        .map((o) => o.trim())
        .filter(Boolean);
    const own = new URL(request.url).origin;
    return [own, ...DEFAULT_ORIGINS, ...extra].includes(origin) ? origin : null;
}

function corsHeaders(request: Request): Record<string, string> {
    const origin = allowedOrigin(request);
    return origin
        ? {
              'Access-Control-Allow-Origin': origin,
              'Access-Control-Allow-Methods': 'POST, OPTIONS',
              'Access-Control-Allow-Headers': 'Content-Type',
              Vary: 'Origin',
          }
        : {};
}

function json(request: Request, status: number, body: unknown): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json', ...corsHeaders(request) },
    });
}

export function OPTIONS(request: Request): Response {
    return new Response(null, { status: 204, headers: corsHeaders(request) });
}

export async function POST(request: Request): Promise<Response> {
    // Browsers always send Origin on cross-site POSTs; reject ones we don't know.
    if (request.headers.get('origin') && !allowedOrigin(request)) {
        return json(request, 403, { message: 'Origin not allowed.' });
    }

    const apiKey = process.env.ROBOFLOW_API_KEY;
    if (!apiKey) {
        return json(request, 500, { message: 'The server is missing its Roboflow API key.' });
    }

    const ip = (request.headers.get('x-forwarded-for') ?? 'unknown').split(',')[0].trim();
    if (rateLimited(ip)) {
        return json(request, 429, { message: 'Too many requests. Wait a minute and try again.' });
    }

    let body: { image?: unknown; model_id?: unknown };
    try {
        body = await request.json();
    } catch {
        return json(request, 400, { message: 'Request body must be JSON.' });
    }

    const image = body.image;
    if (typeof image !== 'string' || image.length === 0) {
        return json(request, 400, { message: 'Missing image.' });
    }
    if (image.length > MAX_IMAGE_CHARS) {
        return json(request, 413, { message: 'Image is too large.' });
    }
    if (!/^[A-Za-z0-9+/]+=*$/.test(image)) {
        return json(request, 400, { message: 'Image must be base64 data.' });
    }

    const modelId = body.model_id ?? ALLOWED_MODELS[0];
    if (typeof modelId !== 'string' || !ALLOWED_MODELS.includes(modelId)) {
        return json(request, 400, { message: 'Unknown model.' });
    }

    // Roboflow's hosted API: POST /<project>/<version> with the base64 image as
    // the body. Thresholds are percentages; ask for nearly everything and let
    // the page filter by confidence.
    const url = new URL(`${ROBOFLOW_URL}/${modelId}`);
    url.searchParams.set('api_key', apiKey);
    url.searchParams.set('confidence', '5');

    // The first request after a quiet period can fail while Roboflow loads the
    // model, so try twice before giving up.
    let upstream: Response | undefined;
    for (let attempt = 0; attempt < 2; attempt++) {
        try {
            upstream = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: image,
                signal: AbortSignal.timeout(12_000),
            });
            if (upstream.status < 500) break;
        } catch {
            upstream = undefined;
        }
    }
    if (!upstream) {
        return json(request, 502, { message: 'The detection service did not respond.' });
    }

    if (!upstream.ok) {
        // Do not pass Roboflow's error body through: it can describe the key.
        const message =
            upstream.status === 401 || upstream.status === 403
                ? 'The server’s Roboflow API key was rejected.'
                : `The detection service returned an error (${upstream.status}).`;
        // Full detail goes to the function log only.
        console.error('Roboflow error', upstream.status, (await upstream.text()).slice(0, 500));
        return json(request, 502, { message });
    }

    const data = await upstream.json();
    const result = Array.isArray(data) ? data[0] : data;
    return json(request, 200, { image: result?.image, predictions: result?.predictions ?? [] });
}
