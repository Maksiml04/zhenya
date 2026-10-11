const TURNSTILE_SITEKEY = '0x4AAAAAAFUJ0lLeXaBJRDJb';

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405, headers: { 'Content-Type': 'application/json' } });
    }

    const origin = request.headers.get('Origin') || '';
    const allowedOrigins = ['http://localhost:8000', 'http://127.0.0.1:8000', 'https://forum-dance.ru'];
    const corsOrigin = allowedOrigins.includes(origin) ? origin : '';

    const corsHeaders = {
      'Access-Control-Allow-Origin': corsOrigin,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'application/json',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      const formData = await request.formData();
      const token = formData.get('cf-turnstile-response');
      const name = formData.get('name') || '';
      const phone = formData.get('phone') || '';
      const direction = formData.get('direction') || '';

      if (!token) {
        return new Response(JSON.stringify({ error: 'Missing captcha token' }), { status: 400, headers: corsHeaders });
      }

      const ip = request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || '';

      const verifyResp = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          secret: env.TURNSTILE_SECRET,
          response: token,
          remoteip: ip,
        }),
      });

      const verifyResult = await verifyResp.json();

      if (!verifyResult.success) {
        return new Response(JSON.stringify({ error: 'Captcha verification failed', detail: verifyResult['error-codes'] }), { status: 403, headers: corsHeaders });
      }

      const submission = {
        name,
        phone,
        direction,
        timestamp: new Date().toISOString(),
        hostname: verifyResult.hostname,
      };

      console.log('Form submission:', JSON.stringify(submission));

      return new Response(JSON.stringify({ success: true, message: 'Form submitted successfully' }), { status: 200, headers: corsHeaders });
    } catch (err) {
      return new Response(JSON.stringify({ error: 'Internal error' }), { status: 500, headers: corsHeaders });
    }
  },
};
