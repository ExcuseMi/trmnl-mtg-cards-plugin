import asyncio
import logging
import os

import aiohttp

from modules.formatters.card import shape_card
from modules.providers.base import BaseProvider

log = logging.getLogger(__name__)

SCRYFALL_SEARCH = 'https://api.scryfall.com/cards/search'
MAX_PAGES = int(os.getenv('MTG_MAX_PAGES', '3'))
USER_AGENT = 'TRMNL-MTG-Plugin/1.0 (trmnl.bettens.dev)'


def _parse_multi(value: str) -> list[str]:
    return [v.strip() for v in (value or '').split(',') if v.strip() and v.strip().lower() != 'any']


def _or_clause(prefix: str, values: list[str]) -> str:
    if not values:
        return ''
    if len(values) == 1:
        return f'{prefix}:{values[0]}'
    return '(' + ' or '.join(f'{prefix}:{v}' for v in values) + ')'


def _build_query(colors: list[str], card_types: list[str], rarities: list[str], set_code: str, language: str) -> str:
    parts = ['has:art', '-layout:art_series', '-layout:token', '-layout:emblem']
    if set_code and set_code.lower() != 'any':
        parts.append(f's:{set_code}')
    clause = _or_clause('c', colors)
    if clause:
        parts.append(clause)
    clause = _or_clause('t', card_types)
    if clause:
        parts.append(clause)
    clause = _or_clause('r', rarities)
    if clause:
        parts.append(clause)
    if language and language.lower() not in ('en', 'any', ''):
        parts.append(f'lang:{language}')
    return ' '.join(parts)


class MtgProvider(BaseProvider):

    async def _fetch(self, **filters) -> list[dict] | None:
        colors = _parse_multi(filters.get('color', ''))
        card_types = _parse_multi(filters.get('card_type', ''))
        rarities = _parse_multi(filters.get('rarity', ''))
        set_code = filters.get('set_code', '').strip()
        language = (filters.get('language', 'en') or 'en').strip()

        query = _build_query(colors, card_types, rarities, set_code, language)
        cards = await self._search(query)
        if not cards and language != 'en':
            log.info('No cards for language=%s, falling back to en', language)
            query_en = _build_query(colors, card_types, rarities, set_code, 'en')
            cards = await self._search(query_en)
        return cards

    async def _search(self, query: str) -> list[dict] | None:
        all_raw: list[dict] = []
        url: str | None = SCRYFALL_SEARCH
        params: dict | None = {'q': query, 'order': 'random', 'unique': 'prints'}
        pages_fetched = 0
        try:
            async with aiohttp.ClientSession(headers={'User-Agent': USER_AGENT}) as session:
                while url and pages_fetched < MAX_PAGES:
                    if pages_fetched > 0:
                        await asyncio.sleep(0.1)
                    async with session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        if resp.status == 404:
                            log.warning('Scryfall 404 for query: %s', query)
                            break
                        resp.raise_for_status()
                        data = await resp.json()
                    all_raw.extend(data.get('data', []))
                    pages_fetched += 1
                    url = data.get('next_page') if data.get('has_more') else None
                    params = None
        except Exception as exc:
            log.error('Scryfall search error (query=%r): %s', query, exc)
            return None

        if not all_raw:
            return None
        cards = [shape_card(c) for c in all_raw]
        cards = [c for c in cards if c.get('image_large')]
        return cards if cards else None
