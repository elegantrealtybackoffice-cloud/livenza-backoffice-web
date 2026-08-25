import json
import os

class AIClientAdapter:
    def __init__(self, api_key='', model=''):
        self.api_key=str(api_key or '').strip()
        self.model=str(model or os.getenv('OPENAI_LETTERHEAD_MODEL') or os.getenv('OPENAI_HELP_MODEL') or 'gpt-5.6-luna').strip()

    @property
    def available(self):
        return bool(self.api_key)

    def _client(self):
        if not self.api_key:
            raise RuntimeError('AI integration is not configured.')
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, timeout=60)

    def generate_json(self, request_payload):
        prompt=(
            'You are Ask Livenza AI inside Livenza Letterhead Studio. Return ONLY one JSON object. '
            'Use only facts and source IDs supplied by the server. Never invent names, dates, amounts, room numbers, IDs, or legal facts. '
            'Write professional Indian business correspondence. Keep body_sections as simple paragraph/heading/list/table blocks. '
            'Do not choose a template or signature. Suggested attachment IDs must come from allowed_attachment_ids.\n\n'
            + json.dumps(request_payload, ensure_ascii=False)
        )
        response=self._client().responses.create(model=self.model,input=prompt)
        text=getattr(response,'output_text','') or ''
        start=text.find('{'); end=text.rfind('}')
        if start<0 or end<start: raise ValueError('AI did not return structured JSON.')
        return json.loads(text[start:end+1])

    def rewrite_blocks(self, blocks, action):
        prompt=(
            'Rewrite only the prose of these document body blocks. Preserve all factual values, dates, amounts, names, identifiers, '
            'source references and structure. Return ONLY JSON with key body_sections. '
            f'Action: {action}. Blocks: {json.dumps(blocks,ensure_ascii=False)}'
        )
        response=self._client().responses.create(model=self.model,input=prompt)
        text=getattr(response,'output_text','') or ''
        start=text.find('{'); end=text.rfind('}')
        if start<0 or end<start: raise ValueError('AI rewrite did not return structured JSON.')
        data=json.loads(text[start:end+1])
        blocks=data.get('body_sections')
        if not isinstance(blocks,list): raise ValueError('AI rewrite body_sections missing.')
        return blocks


def get_ai_client(actor=None, provider_config=None):
    config=provider_config or {}
    api_key=str(config.get('api_key') or os.getenv('OPENAI_API_KEY') or '').strip()
    model=str(config.get('model') or os.getenv('OPENAI_LETTERHEAD_MODEL') or '').strip()
    return AIClientAdapter(api_key=api_key,model=model)


def _invoke_delivery(channel, payload, provider=None):
    from letterhead_delivery import normalize_delivery_result
    if provider is None:
        return normalize_delivery_result(channel, {
            'accepted': False,
            'provider': f'configured-{channel}',
            'error_code': 'integration_not_configured',
        })
    try:
        raw = provider(payload)
    except Exception:
        raw = {'accepted': False, 'provider': f'configured-{channel}', 'error_code': 'provider_exception'}
    return normalize_delivery_result(channel, raw)


def send_email(actor, payload, provider=None):
    """Send through a server-provided Integrations Center adapter.

    ``actor`` is intentionally accepted for a stable permission-aware interface; credentials
    never cross this module boundary inside ``payload``.
    """
    return _invoke_delivery('email', payload, provider=provider)


def send_whatsapp(actor, payload, provider=None):
    """Send through a server-provided WhatsApp adapter without serializing credentials."""
    return _invoke_delivery('whatsapp', payload, provider=provider)
