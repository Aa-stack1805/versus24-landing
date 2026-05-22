import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");
const AUDIENCE_ID = "72f0ab07-8949-4772-ad75-a30c77975f91";

const ALLOWED_ORIGINS = new Set([
  "https://versus24.net",
  "https://www.versus24.net",
  "http://localhost:8000",
  "http://localhost:5500",
  "http://127.0.0.1:5500",
]);

function corsHeaders(origin: string | null): Record<string, string> {
  const allow = origin && ALLOWED_ORIGINS.has(origin) ? origin : "https://versus24.net";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type, authorization, apikey, x-client-info",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

function jsonResponse(body: unknown, status: number, cors: Record<string, string>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && email.length <= 254;
}

function clip(value: unknown, max: number): string {
  return typeof value === "string" ? value.slice(0, max) : "";
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin");
  const cors = corsHeaders(origin);

  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: cors });
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405, cors);
  }
  if (!RESEND_API_KEY) {
    console.error("RESEND_API_KEY missing");
    return jsonResponse({ error: "Server is not configured." }, 500, cors);
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON." }, 400, cors);
  }

  // Honeypot — silently accept and drop bots
  if (typeof body.website === "string" && body.website.trim().length > 0) {
    return jsonResponse({ ok: true }, 200, cors);
  }

  const email = clip(body.email, 254).trim().toLowerCase();
  if (!isValidEmail(email)) {
    return jsonResponse({ error: "Please enter a valid email." }, 400, cors);
  }

  const source_page = clip(body.source_page, 200);
  const utm_source = clip(body.utm_source, 100);
  const utm_medium = clip(body.utm_medium, 100);
  const utm_campaign = clip(body.utm_campaign, 100);

  const resendRes = await fetch(
    `https://api.resend.com/audiences/${AUDIENCE_ID}/contacts`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, unsubscribed: false }),
    },
  );

  if (!resendRes.ok) {
    const text = await resendRes.text();
    console.error("Resend error", resendRes.status, text);
    // Treat duplicates as success so the user gets a friendly state
    if (resendRes.status === 409 || resendRes.status === 422) {
      return jsonResponse({ ok: true, duplicate: true }, 200, cors);
    }
    return jsonResponse(
      { error: "Could not add you right now. Try again in a moment." },
      502,
      cors,
    );
  }

  // Log non-PII attribution only
  console.log("waitlist signup", { source_page, utm_source, utm_medium, utm_campaign });

  return jsonResponse({ ok: true }, 200, cors);
});
