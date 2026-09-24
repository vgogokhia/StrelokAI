/** LLM provider adapters. The browser always speaks the Anthropic Messages format (text / tool_use / tool_result
 *  blocks); these adapters translate to OpenAI Chat Completions and Gemini generateContent and back. */

export const VENDORS = {
  anthropic: { label: 'Anthropic (Claude)', env: 'ANTHROPIC_API_KEY' },
  openai: { label: 'OpenAI (GPT)', env: 'OPENAI_API_KEY' },
  gemini: { label: 'Google (Gemini)', env: 'GEMINI_API_KEY' },
};

const clean = b => { const { _sig, ...rest } = b; return rest; };
const blocks = c => (typeof c === 'string' ? [{ type: 'text', text: c }] : Array.isArray(c) ? c : []);
const toolText = c => (typeof c === 'string' ? c : Array.isArray(c) ? c.map(x => x.text ?? '').join('') : JSON.stringify(c ?? ''));

async function anthropic({ key, model, system, state, tools, messages, fetch }) {
  const r = await fetch('https://api.anthropic.com/v1/messages', { method: 'POST',
    headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({ model, max_tokens: 1024,
      system: [{ type: 'text', text: system, cache_control: { type: 'ephemeral' } }, { type: 'text', text: state }],
      tools: tools.map((x, k, a) => (k === a.length - 1 ? { ...x, cache_control: { type: 'ephemeral' } } : x)),
      messages: messages.map(m => ({ role: m.role, content: typeof m.content === 'string' ? m.content : m.content.map(clean) })) }) });
  const d = await r.json();
  if (!r.ok) throw new Error(d?.error?.message || d?.error?.type || `HTTP ${r.status}`);
  return { content: d.content, stop_reason: d.stop_reason };
}

async function openai({ key, model, system, state, tools, messages, fetch }) {
  const out = [{ role: 'system', content: `${system}\n\n${state}` }];
  for (const m of messages) {
    const bs = blocks(m.content);
    if (m.role === 'assistant') {
      const text = bs.filter(b => b.type === 'text').map(b => b.text).join('\n');
      const calls = bs.filter(b => b.type === 'tool_use').map(b => ({ id: b.id, type: 'function', function: { name: b.name, arguments: JSON.stringify(b.input ?? {}) } }));
      out.push({ role: 'assistant', content: text || null, ...(calls.length ? { tool_calls: calls } : {}) });
    } else {
      for (const b of bs.filter(b => b.type === 'tool_result')) out.push({ role: 'tool', tool_call_id: b.tool_use_id, content: toolText(b.content) });
      const text = bs.filter(b => b.type === 'text').map(b => b.text).join('\n');
      if (text) out.push({ role: 'user', content: text });
    }
  }
  const r = await fetch('https://api.openai.com/v1/chat/completions', { method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${key}` },
    body: JSON.stringify({ model, max_completion_tokens: 2048, messages: out,
      tools: tools.map(t => ({ type: 'function', function: { name: t.name, description: t.description, parameters: t.input_schema } })) }) });
  const d = await r.json();
  if (!r.ok) throw new Error(d?.error?.message || `HTTP ${r.status}`);
  const msg = d.choices?.[0]?.message ?? {};
  const content = [];
  if (msg.content) content.push({ type: 'text', text: msg.content });
  for (const c of msg.tool_calls ?? []) { let input = {}; try { input = JSON.parse(c.function.arguments || '{}'); } catch { /* keep empty */ } content.push({ type: 'tool_use', id: c.id, name: c.function.name, input }); }
  return { content, stop_reason: msg.tool_calls?.length ? 'tool_use' : 'end_turn' };
}

/** Gemini accepts an OpenAPI subset: drop empty `properties` objects. */
const gemSchema = s => (s && s.type === 'object' && (!s.properties || !Object.keys(s.properties).length) ? undefined : s);
async function gemini({ key, model, system, state, tools, messages, fetch }) {
  const names = new Map(); const contents = [];
  for (const m of messages) {
    const parts = [];
    for (const b of blocks(m.content)) {
      if (b.type === 'text' && b.text) parts.push({ text: b.text });
      else if (b.type === 'tool_use') { names.set(b.id, b.name); parts.push({ functionCall: { name: b.name, args: b.input ?? {} }, ...(b._sig ? { thoughtSignature: b._sig } : {}) }); }
      else if (b.type === 'tool_result') { let resp; try { resp = JSON.parse(toolText(b.content)); } catch { resp = { result: toolText(b.content) }; } parts.push({ functionResponse: { name: names.get(b.tool_use_id) || 'tool', response: resp } }); }
    }
    if (parts.length) contents.push({ role: m.role === 'assistant' ? 'model' : 'user', parts });
  }
  const id = String(model).replace(/^models\//, '');
  const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(id)}:generateContent`, { method: 'POST',
    headers: { 'content-type': 'application/json', 'x-goog-api-key': key },
    body: JSON.stringify({ systemInstruction: { parts: [{ text: `${system}\n\n${state}` }] }, contents,
      tools: [{ functionDeclarations: tools.map(t => { const p = gemSchema(t.input_schema); return { name: t.name, description: t.description, ...(p ? { parameters: p } : {}) }; }) }],
      generationConfig: { maxOutputTokens: 2048 } }) });
  const d = await r.json();
  if (!r.ok) throw new Error(d?.error?.message || `HTTP ${r.status}`);
  const content = []; let n = 0;
  for (const p of d.candidates?.[0]?.content?.parts ?? []) {
    if (p.thought) continue;
    if (p.text) content.push({ type: 'text', text: p.text });
    if (p.functionCall) content.push({ type: 'tool_use', id: `g_${Date.now().toString(36)}_${n++}`, name: p.functionCall.name, input: p.functionCall.args ?? {}, ...(p.thoughtSignature ? { _sig: p.thoughtSignature } : {}) });
  }
  return { content, stop_reason: content.some(b => b.type === 'tool_use') ? 'tool_use' : 'end_turn' };
}

export const ADAPTERS = { anthropic, openai, gemini };

/** Chat-capable models from the provider's own model list, so the dropdown never goes stale. */
export async function listModels(vendor, key, fetch) {
  if (vendor === 'anthropic') {
    const r = await fetch('https://api.anthropic.com/v1/models?limit=100', { headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01' } });
    const d = await r.json(); if (!r.ok) throw new Error(d?.error?.message || `HTTP ${r.status}`);
    return (d.data ?? []).map(m => ({ id: m.id, name: m.display_name || m.id }));
  }
  if (vendor === 'openai') {
    const r = await fetch('https://api.openai.com/v1/models', { headers: { authorization: `Bearer ${key}` } });
    const d = await r.json(); if (!r.ok) throw new Error(d?.error?.message || `HTTP ${r.status}`);
    const skip = /(audio|realtime|transcribe|tts|image|embedding|moderation|search|whisper|dall-e|davinci|babbage|instruct|codex)/i;
    return (d.data ?? []).filter(m => /^(gpt-|o\d|chatgpt-)/.test(m.id) && !skip.test(m.id)).sort((a, b) => (b.created ?? 0) - (a.created ?? 0)).map(m => ({ id: m.id, name: m.id }));
  }
  if (vendor === 'gemini') {
    const r = await fetch('https://generativelanguage.googleapis.com/v1beta/models?pageSize=200', { headers: { 'x-goog-api-key': key } });
    const d = await r.json(); if (!r.ok) throw new Error(d?.error?.message || `HTTP ${r.status}`);
    return (d.models ?? []).filter(m => (m.supportedGenerationMethods ?? []).includes('generateContent') && /gemini/i.test(m.name) && !/(embedding|image|tts|audio|live)/i.test(m.name))
      .map(m => ({ id: m.name.replace(/^models\//, ''), name: m.displayName || m.name }));
  }
  throw new Error('unknown vendor');
}
