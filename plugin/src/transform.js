function transform(input) {
  var LABELS = {
    en: { type: 'Type', mana: 'Mana', pt: 'P/T', loyalty: 'Loyalty', rarity: 'Rarity', artist: 'Artist', price: 'Price', set_label: 'Set' },
    de: { type: 'Typ',  mana: 'Mana', pt: 'A/W', loyalty: 'Loyalität', rarity: 'Seltenheit', artist: 'Illustrator', price: 'Preis', set_label: 'Set' },
    fr: { type: 'Type', mana: 'Mana', pt: 'F/E', loyalty: 'Loyauté', rarity: 'Rareté', artist: 'Artiste', price: 'Prix', set_label: 'Série' },
    es: { type: 'Tipo', mana: 'Maná', pt: 'F/R', loyalty: 'Lealtad', rarity: 'Rareza', artist: 'Artista', price: 'Precio', set_label: 'Serie' },
    it: { type: 'Tipo', mana: 'Mana', pt: 'F/R', loyalty: 'Fedeltà', rarity: 'Rarità', artist: 'Artista', price: 'Prezzo', set_label: 'Serie' },
    pt: { type: 'Tipo', mana: 'Mana', pt: 'F/R', loyalty: 'Lealdade', rarity: 'Raridade', artist: 'Artista', price: 'Preço', set_label: 'Coleção' },
    ja: { type: 'タイプ', mana: 'マナ', pt: 'P/T', loyalty: '忠誠度', rarity: 'レアリティ', artist: 'アーティスト', price: '価格', set_label: 'セット' },
    ko: { type: '유형', mana: '마나', pt: 'P/T', loyalty: '충성도', rarity: '희귀도', artist: '일러스트레이터', price: '가격', set_label: '세트' },
    ru: { type: 'Тип', mana: 'Мана', pt: 'С/В', loyalty: 'Верность', rarity: 'Редкость', artist: 'Художник', price: 'Цена', set_label: 'Набор' },
    zhs: { type: '类型', mana: '法术力', pt: '力量/防御', loyalty: '忠诚度', rarity: '稀有度', artist: '画师', price: '价格', set_label: '系列' },
    zht: { type: '類型', mana: '魔法力', pt: '力量/防禦', loyalty: '忠誠度', rarity: '稀有度', artist: '畫師', price: '價格', set_label: '系列' },
  };

  var raw  = Array.isArray(input.data) ? input.data : [];
  var lang = ((((input.trmnl || {}).plugin_settings || {}).custom_fields_values || {}).language || 'en').toLowerCase();
  var labels = LABELS[lang] || LABELS['en'];

  return {
    items: raw.slice(0, 4),
    labels: labels,
  };
}
