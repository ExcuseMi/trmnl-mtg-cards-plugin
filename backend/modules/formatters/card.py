def _fmt_price(sym: str, v) -> str:
    try:
        return f'{sym}{float(v):.2f}' if v is not None else ''
    except (TypeError, ValueError):
        return ''


def _get_image_uris(raw: dict) -> dict:
    if 'image_uris' in raw:
        return raw['image_uris']
    faces = raw.get('card_faces', [])
    if faces and 'image_uris' in faces[0]:
        return faces[0]['image_uris']
    return {}


def shape_card(raw: dict) -> dict:
    image_uris = _get_image_uris(raw)
    if not image_uris:
        return {}

    faces = raw.get('card_faces', [])
    mana_cost = raw.get('mana_cost') or (faces[0].get('mana_cost', '') if faces else '')
    type_line = raw.get('type_line') or (faces[0].get('type_line', '') if faces else '')
    oracle_text = raw.get('oracle_text') or (faces[0].get('oracle_text', '') if faces else '')
    power = raw.get('power') or (faces[0].get('power') if faces else None)
    toughness = raw.get('toughness') or (faces[0].get('toughness') if faces else None)
    loyalty = raw.get('loyalty') or (faces[0].get('loyalty') if faces else None)

    prices = raw.get('prices') or {}
    set_code = raw.get('set', '')

    return {
        'id': raw.get('id', ''),
        'name': raw.get('name', ''),
        'mana_cost': mana_cost,
        'cmc': raw.get('cmc'),
        'type_line': type_line,
        'oracle_text': oracle_text,
        'power': power,
        'toughness': toughness,
        'loyalty': loyalty,
        'colors': raw.get('colors') or [],
        'color_identity': raw.get('color_identity') or [],
        'rarity': raw.get('rarity', ''),
        'set_code': set_code,
        'set_name': raw.get('set_name', ''),
        'set_release_date': raw.get('released_at', ''),
        'set_icon': f'https://svgs.scryfall.io/sets/{set_code}.svg' if set_code else '',
        'collector_number': raw.get('collector_number', ''),
        'artist': raw.get('artist', ''),
        'image_large': image_uris.get('large') or image_uris.get('normal', ''),
        'image_small': image_uris.get('normal') or image_uris.get('small', ''),
        'price_usd': _fmt_price('$', prices.get('usd')),
        'price_usd_foil': _fmt_price('$', prices.get('usd_foil')),
        'price_eur': _fmt_price('€', prices.get('eur')),
        'price_eur_foil': _fmt_price('€', prices.get('eur_foil')),
    }
