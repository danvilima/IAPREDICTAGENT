# Mapeamento estático de bandeiras

MAPA_BANDEIRAS = {
    "Argentina": "🇦🇷",
    "Brazil": "🇧🇷",
    "France": "🇫🇷",
    "Spain": "🇪🇸",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", # ISO-3166-2:GB-ENG
    "Germany": "🇩🇪",
    "Portugal": "🇵🇹",
    "Netherlands": "🇳🇱",
    "Italy": "🇮🇹",
    "Croatia": "🇭🇷",
    "Belgium": "🇧🇪",
    "Uruguay": "🇺🇾",
    "Colombia": "🇨🇴",
    "United States": "🇺🇸",
    "Mexico": "🇲🇽",
    "Senegal": "🇸🇳",
    "Morocco": "🇲🇦",
    "Japan": "🇯🇵",
    "South Korea": "🇰🇷",
    "Iran": "🇮🇷",
    "Australia": "🇦🇺",
    "Switzerland": "🇨🇭",
    "Denmark": "🇩🇰",
    "Sweden": "🇸🇪",
    "Serbia": "🇷🇸",
    "Poland": "🇵🇱",
    "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Tunisia": "🇹🇳",
    "Cape Verde": "🇨🇻",
    "DR Congo": "🇨🇩",
    "Czech Republic": "🇨🇿"
}

def obter_bandeira(selecao: str) -> str:
    """Retorna o Emoji da Bandeira se mapeado, ou a bandeira branca como fallback."""
    return MAPA_BANDEIRAS.get(selecao, "🏳️")

def com_bandeira(selecao: str) -> str:
    """Retorna o nome formatado ex: 🇧🇷 Brazil"""
    return f"{obter_bandeira(selecao)} {selecao}"

import os
import base64

NATIONS_TO_SVG = {'Argentina': 'arg_argentina.svg', 'Australia': 'aus_australia.svg', 'Austria': 'aut_austria.svg', 'Belgium': 'bel_belgica.svg', 'Brazil': 'bra_brasil.svg', 'Canada': 'can_canada.svg', 'Colombia': 'col_colombia.svg', 'Croatia': 'cro_croacia.svg', 'Czech Republic': 'cze_chequia.svg', 'Denmark': 'den_dinamarca.svg', 'England': 'eng_inglaterra.svg', 'France': 'fra_franca.svg', 'Germany': 'ger_alemanha.svg', 'Iran': 'irn_ira.svg', 'Japan': 'jpn_japao.svg', 'Mexico': 'mex_mexico.svg', 'Morocco': 'mar_marrocos.svg', 'Netherlands': 'ned_holanda.svg', 'Poland': 'pol_polonia.svg', 'Portugal': 'por_portugal.svg', 'Senegal': 'sen_senegal.svg', 'Serbia': 'srb_servia.svg', 'South Korea': 'kor_coreia_do_sul.svg', 'Spain': 'esp_espanha.svg', 'Sweden': 'swe_suecia.svg', 'Switzerland': 'sui_suica.svg', 'Tunisia': 'tun_tunisia.svg', 'United States': 'usa_estados_unidos.svg', 'Uruguay': 'uru_uruguai.svg', 'Wales': 'wal_gales.svg', 'Ecuador': 'ecu_equador.svg', 'Qatar': 'qat_qatar.svg', 'Saudi Arabia': 'ksa_arabia_saudita.svg', 'Cameroon': 'cmr_camaroes.svg', 'Ghana': 'gha_gana.svg', 'Costa Rica': 'crc_costa_rica.svg', 'DR Congo': 'cod_rd_congo.svg', 'Cape Verde': 'cpv_cabo_verde.svg', 'Panama': 'pan_panama.svg', 'Haiti': 'hai_haiti.svg', 'Iraq': 'irq_iraque.svg', 'Egypt': 'egy_egito.svg'}

_CACHE_SVG = {}

def obter_svg_data_uri(selecao: str) -> str:
    if selecao in _CACHE_SVG:
        return _CACHE_SVG[selecao]
        
    filename = NATIONS_TO_SVG.get(selecao)
    if not filename:
        return ''
        
    path = os.path.join('Seleções', filename)
    if not os.path.exists(path):
        return ''
        
    with open(path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
        
    uri = f"data:image/svg+xml;base64,{encoded}"
    _CACHE_SVG[selecao] = uri
    return uri

def com_bandeira_html(selecao: str) -> str:
    uri = obter_svg_data_uri(selecao)
    if uri:
        return f'<img src="{uri}" width="24" style="vertical-align: middle; margin-right: 8px; border-radius: 2px;" />{selecao}'
    return com_bandeira(selecao)
