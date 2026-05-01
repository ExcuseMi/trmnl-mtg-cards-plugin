import logging
import random

import aiohttp

from modules.formatters.card import shape_card
from modules.providers.base import BaseProvider

log = logging.getLogger(__name__)

SCRYFALL_SEARCH = 'https://api.scryfall.com/cards/search'
SAMPLE_SIZE = 20
USER_AGENT = 'TRMNL-MTG-Plugin/1.0 (trmnl.bettens.dev)'


def _build_query(color: str, card_type: str, rarity: str, set_code: str, language: str) -> str:
    parts = ['has:art', '-layout:art_series', '-layout:token', '-layout:emblem']
    if set_code and set_code.lower() != 'any':
        parts.append(f's:{set_code}')
    if color and color.lower() not in ('any', ''):
        parts.append(f'c:{color}')
    if card_type and card_type.lower() not in ('any', ''):
        parts.append(f't:{card_type}')
    if rarity and rarity.lower() not in ('any', ''):
        parts.append(f'r:{rarity}')
    if language and language.lower() not in ('en', 'any', ''):
        parts.append(f'lang:{language}')
    return ' '.join(parts)


class MtgProvider(BaseProvider):

    async def _fetch(self, **filters) -> list[dict] | None:
        color = filters.get('color', '').strip()
        card_type = filters.get('card_type', '').strip()
        rarity = filters.get('rarity', '').strip()
        set_code = filters.get('set_code', '').strip()
        language = (filters.get('language', 'en') or 'en').strip()

        query = _build_query(color, card_type, rarity, set_code, language)
        cards = await self._search(query)
        if not cards and language != 'en':
            log.info('No cards for language=%s, falling back to en', language)
            query_en = _build_query(color, card_type, rarity, set_code, 'en')
            cards = await self._search(query_en)
        return cards

    async def _search(self, query: str) -> list[dict] | None:
        params = {
            'q': query,
            'order': 'random',
            'unique': 'prints',
        }
        try:
            async with aiohttp.ClientSession(headers={'User-Agent': USER_AGENT}) as session:
                async with session.get(
                    SCRYFALL_SEARCH,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 404:
                        log.warning('Scryfall 404 for query: %s', query)
                        return None
                    resp.raise_for_status()
                    data = await resp.json()

            raw_cards = data.get('data', [])
            if not raw_cards:
                return None

            sample = random.sample(raw_cards, min(SAMPLE_SIZE, len(raw_cards)))
            cards = [shape_card(c) for c in sample]
            cards = [c for c in cards if c.get('image_large')]
            return cards if cards else None
        except Exception as exc:
            log.error('Scryfall search error (query=%r): %s', query, exc)
            return None
