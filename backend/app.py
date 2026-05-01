import asyncio
import json
import logging
import os
import random

import aiohttp
from quart import Quart, Response, jsonify, request
from redis.asyncio import Redis

from modules.providers.mtg import MtgProvider
from modules.utils.ip_whitelist import init_ip_whitelist, require_tiered_access

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
log = logging.getLogger(__name__)

app = Quart(__name__)

REFRESH_HOURS = float(os.getenv('REFRESH_HOURS', '1'))
SCRYFALL_SETS_API = 'https://api.scryfall.com/sets'
USER_AGENT = 'TRMNL-MTG-Plugin/1.0 (trmnl.bettens.dev)'

NORMAL_SET_TYPES = {
    'expansion', 'core', 'masters', 'draft_innovation',
    'commander', 'planechase', 'archenemy',
}

_redis = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', '6379')),
    db=0,
    decode_responses=True,
)
_provider = MtgProvider(name='mtg', redis=_redis)


@app.before_serving
async def _startup():
    await init_ip_whitelist()
    log.info('MTG Cards backend started — cache TTL: %sh', REFRESH_HOURS)


@app.route('/card')
@require_tiered_access(lambda: _redis, prefix='card')
async def card():
    args = dict(request.args)
    if '::' in args.get('set_code', ''):
        args['set_code'] = args['set_code'].split('::')[0]
    ttl = REFRESH_HOURS * 3600

    if await _provider.is_expired(ttl, **args):
        cached = await _provider.get_cached(**args)
        if cached:
            asyncio.create_task(_provider.refresh(**args))
        else:
            cached = await _provider.refresh(**args)
    else:
        cached = await _provider.get_cached(**args)

    if not cached:
        return jsonify({'error': 'Failed to fetch cards'}), 503

    selected = random.sample(cached, min(4, len(cached)))
    return jsonify({'data': selected})


async def _fetch_sets() -> list:
    async with aiohttp.ClientSession(headers={'User-Agent': USER_AGENT}) as session:
        async with session.get(SCRYFALL_SETS_API, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get('data', [])


@app.route('/sets', methods=['GET', 'POST', 'OPTIONS'])
async def sets():
    if request.method == 'OPTIONS':
        return _cors(Response('', status=204))

    search = await _parse_search()

    cache_key = 'mtg:sets:v1'
    raw_sets = None
    try:
        cached = await _redis.get(cache_key)
        if cached:
            raw_sets = json.loads(cached)
    except Exception:
        pass

    if raw_sets is None:
        try:
            raw_sets = await _fetch_sets()
            try:
                await _redis.set(cache_key, json.dumps(raw_sets), ex=86400)
            except Exception:
                pass
        except Exception as exc:
            log.error('Error fetching sets: %s', exc)
            return _cors(jsonify({'error': 'Failed to fetch sets'})), 503

    result = _build_sets(raw_sets, search)
    return _cors(Response(json.dumps(result), content_type='application/json'))


async def _parse_search() -> str:
    if request.method == 'POST':
        try:
            body = await request.get_json(silent=True) or {}
            term = body.get('query') or body.get('search') or body.get('q') or ''
            return str(term).lower().strip()
        except Exception:
            pass
    queries = request.args.getlist('query')
    for q in reversed(queries):
        if q.strip():
            return q.lower().strip()
    return request.args.get('q', '').lower().strip()


def _build_sets(raw_sets: list, search: str) -> list:
    result = []
    for s in raw_sets:
        if s.get('set_type') not in NORMAL_SET_TYPES:
            continue
        code = s.get('code', '')
        name = s.get('name', '')
        released = s.get('released_at', '')
        year = released[:4] if released else ''
        label = f"{name} ({year})" if year else name
        if not code or not label:
            continue
        if not search or search in label.lower():
            result.append({'id': code, 'name': label})
    return result


def _cors(response: Response) -> Response:
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response


@app.route('/health')
async def health():
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
