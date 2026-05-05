"""
buscar_noticia.py — Fase 3 do pipeline diário

Fluxo:
  1. Para cada tema em config/temas.json, busca notícias via RSS
  2. Filtra resultados das últimas 48h
  3. Seleciona a notícia mais relevante (sem repetir histórico dos últimos 15 dias)
  4. Se RSS não encontrar nada → retorna tema evergreen

Uso:
  python3 scripts/buscar_noticia.py
  python3 scripts/buscar_noticia.py --tema regulacao-ia-brasil
"""

import json
import os
import sys
import argparse
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict

import feedparser
from dotenv import load_dotenv

# ── Caminhos ──────────────────────────────────────────────────────────────────
BASE           = Path(__file__).resolve().parent.parent
CONFIG_BLOG    = BASE / "config" / "blog.json"
CONFIG_TEMAS   = BASE / "config" / "temas.json"
CONFIG_FONTES  = BASE / "config" / "fontes.json"
HISTORICO      = BASE / "dados" / "historico_noticias.json"
LOG_DIR        = BASE / "logs"

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)
hoje = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"busca_{hoje}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

load_dotenv(BASE / ".env")
load_dotenv(Path.home() / ".zshrc", override=False)


# ── Helpers de arquivo ────────────────────────────────────────────────────────

def ler_json(caminho: Path, padrao):
    if caminho.exists():
        try:
            return json.loads(caminho.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Erro ao ler {caminho}: {e}")
    return padrao


def salvar_json(caminho: Path, dados):
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Histórico de notícias ─────────────────────────────────────────────────────

def ja_publicado(url: str, tema_slug: str,
                 dias_url: int = 15, dias_tema: int = 3) -> bool:
    """
    Retorna True se URL ou tema_slug já foi publicado dentro
    de sua respectiva janela de tempo.
    - dias_url: janela em dias para bloquear mesma URL (default 15)
    - dias_tema: janela em dias para espaçar mesmo tema (default 3)
    Entradas com url_fonte ou tema_slug vazios são ignoradas.
    Entradas com data_publicacao inválida são ignoradas.
    """
    dados = ler_json(HISTORICO, {"noticias": []})
    agora = datetime.now(timezone.utc)
    limite_url = agora - timedelta(days=dias_url)
    limite_tema = agora - timedelta(days=dias_tema)

    for item in dados.get("noticias", []):
        item_url = item.get("url_fonte", "")
        item_tema = item.get("tema_slug", "")
        data_str = item.get("data_publicacao", "")

        try:
            data_pub = datetime.fromisoformat(data_str)
        except (ValueError, TypeError):
            continue

        if url and item_url == url and data_pub >= limite_url:
            return True

        if tema_slug and item_tema == tema_slug and data_pub >= limite_tema:
            return True

    return False


def registrar_noticia_publicada(noticia: dict):
    dados = ler_json(HISTORICO, {"noticias": []})
    dados["noticias"].append({
        "data_publicacao": datetime.now(timezone.utc).isoformat(),
        "titulo_noticia": noticia.get("titulo", ""),
        "url_fonte": noticia.get("url", ""),
        "tema_slug": noticia.get("tema_slug", ""),
    })
    dados["noticias"] = dados["noticias"][-90:]
    salvar_json(HISTORICO, dados)


# ── RSS ───────────────────────────────────────────────────────────────────────

def buscar_rss(tema: Dict, fontes: List[Dict]) -> List[Dict]:
    """
    Percorre os feeds RSS e filtra itens das últimas 48h
    que contenham alguma palavra-chave do tema.
    """
    palavras = set()
    for frase in tema.get("palavras_chave", []):
        for palavra in frase.lower().split():
            if len(palavra) >= 4:
                palavras.add(palavra)

    limite = datetime.now(timezone.utc) - timedelta(hours=48)
    resultados = []

    for fonte in fontes:
        log.info(f"[RSS] Lendo {fonte['nome']}...")
        try:
            feed = feedparser.parse(fonte["url"])
            for entry in feed.entries:
                texto = (
                    (entry.get("title") or "") + " " +
                    (entry.get("summary") or "")
                ).lower()

                if not any(p in texto for p in palavras):
                    continue

                data_entry = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    ts = time.mktime(entry.published_parsed)
                    data_entry = datetime.fromtimestamp(ts, tz=timezone.utc)

                if data_entry and data_entry < limite:
                    continue

                resultados.append({
                    "titulo": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "fonte": fonte["nome"],
                    "data": data_entry.isoformat() if data_entry else "",
                    "resumo": entry.get("summary", "")[:300],
                    "tema_slug": tema["slug"],
                    "tema_nome": tema["nome"],
                    "origem": "rss",
                })

        except Exception as e:
            log.warning(f"[RSS] Erro em {fonte['nome']}: {e}")

    log.info(f"[RSS] {len(resultados)} resultado(s) para tema '{tema['nome']}'")
    return resultados


# ── Pontuação de relevância ───────────────────────────────────────────────────

FONTES_AUTORIDADE = {
    "valor.globo.com":        10,
    "startupi.com.br":         8,
    "exame.com":               7,
    "infomoney.com.br":        7,
    "mittechreview.com.br":    9,
    "tecmundo.com.br":         5,
    "olhardigital.com.br":     5,
}

PALAVRAS_RELEVANTES = [
    # Regulação de IA
    "pl 2338", "ai act", "anpd", "regulação", "lei", "resolução", "marco legal",
    "governança", "compliance", "normativo",
    # Direito e contratos
    "responsabilidade civil", "direitos autorais", "propriedade intelectual",
    "contrato", "lgpd", "dados pessoais", "privacidade",
    # Tributação e negócios
    "tributação", "iss", "irpj", "lei do bem", "startup", "venture capital",
    "investimento", "rodada", "aquisição",
    # Trabalhista
    "trabalhista", "demissão", "automação", "substituição",
]


def pontuar_noticia(noticia: dict) -> float:
    texto = (noticia.get("titulo", "") + " " + noticia.get("resumo", "")).lower()
    pontos = 0.0

    for dominio, score in FONTES_AUTORIDADE.items():
        if dominio in noticia.get("url", "").lower() or dominio in noticia.get("fonte", "").lower():
            pontos += score
            break

    for palavra in PALAVRAS_RELEVANTES:
        if palavra in texto:
            pontos += 2

    data_str = noticia.get("data", "")
    if data_str:
        try:
            data = datetime.fromisoformat(data_str)
            if data.tzinfo is None:
                data = data.replace(tzinfo=timezone.utc)
            horas_atras = (datetime.now(timezone.utc) - data).total_seconds() / 3600
            if horas_atras < 6:
                pontos += 8
            elif horas_atras < 24:
                pontos += 4
        except Exception:
            pass

    if not noticia.get("resumo"):
        pontos -= 3

    return pontos


# ── Seleção da notícia mais relevante ────────────────────────────────────────

def selecionar_melhor(candidatos: List[Dict]) -> Optional[Dict]:
    validos = [
        c for c in candidatos
        if c.get("url") and not ja_publicado(c["url"], c.get("tema_slug", ""))
    ]

    if not validos:
        return None

    validos.sort(key=pontuar_noticia, reverse=True)
    escolhida = validos[0]
    log.info(f"Notícia selecionada: [{escolhida['tema_nome']}] {escolhida['titulo']}")
    return escolhida


# ── Evergreen fallback ────────────────────────────────────────────────────────

TEMAS_EVERGREEN = [
    {
        "tipo": "evergreen",
        "tema_slug": "lgpd-ia",
        "tema_nome": "LGPD e proteção de dados em IA",
        "titulo": "LGPD e inteligência artificial: o que toda empresa precisa saber",
        "resumo": "Guia prático sobre como sistemas de IA devem tratar dados pessoais no Brasil, quais bases legais usar e as obrigações perante a ANPD.",
        "url": "",
        "fonte": "evergreen",
        "data": "",
        "origem": "evergreen",
    },
    {
        "tipo": "evergreen",
        "tema_slug": "regulacao-ia-brasil",
        "tema_nome": "Regulação de IA no Brasil",
        "titulo": "PL 2338: o que muda para empresas que usam IA",
        "resumo": "Análise completa do Projeto de Lei 2338, o marco legal de inteligência artificial no Brasil, e o impacto prático para startups e empresas de tecnologia.",
        "url": "",
        "fonte": "evergreen",
        "data": "",
        "origem": "evergreen",
    },
    {
        "tipo": "evergreen",
        "tema_slug": "direitos-autorais-ia",
        "tema_nome": "Direitos autorais e IA generativa",
        "titulo": "Quem é o autor do conteúdo gerado por IA?",
        "resumo": "Análise jurídica sobre titularidade de obras criadas por inteligência artificial, uso de dados para treinamento e o debate internacional sobre copyright e IA generativa.",
        "url": "",
        "fonte": "evergreen",
        "data": "",
        "origem": "evergreen",
    },
    {
        "tipo": "evergreen",
        "tema_slug": "contratos-ia",
        "tema_nome": "Contratos e responsabilidade em IA",
        "titulo": "Responsabilidade civil por erros de algoritmos: quem responde?",
        "resumo": "Como distribuir responsabilidade em contratos de software com IA, cláusulas essenciais de SLA e o que diz a jurisprudência brasileira sobre danos causados por sistemas automatizados.",
        "url": "",
        "fonte": "evergreen",
        "data": "",
        "origem": "evergreen",
    },
]


def escolher_evergreen(temas_slugs_usados: List[str]) -> Dict:
    for tema in TEMAS_EVERGREEN:
        if tema["tema_slug"] not in temas_slugs_usados:
            return tema
    return TEMAS_EVERGREEN[0]


# ── Orquestrador principal ────────────────────────────────────────────────────

def main(apenas_tema: str = "") -> Dict:
    log.info("=" * 60)
    log.info("BUSCAR NOTÍCIA — início")

    config_temas  = ler_json(CONFIG_TEMAS, {"temas": []})
    config_fontes = ler_json(CONFIG_FONTES, {"rss_feeds": []})

    temas      = config_temas.get("temas", [])
    fontes_rss = config_fontes.get("rss_feeds", [])

    if apenas_tema:
        temas = [t for t in temas if t["slug"] == apenas_tema]
        if not temas:
            log.error(f"Tema '{apenas_tema}' não encontrado em config/temas.json")
            sys.exit(1)

    todos_candidatos = []

    for tema in temas:
        resultados_rss = buscar_rss(tema, fontes_rss)
        todos_candidatos.extend(resultados_rss)

    noticia = selecionar_melhor(todos_candidatos)

    if not noticia:
        log.warning("Nenhuma notícia nova encontrada. Usando tema evergreen.")
        slugs_usados = [t["slug"] for t in temas]
        noticia = escolher_evergreen(slugs_usados)

    log.info("=" * 60)
    log.info("RESULTADO FINAL:")
    log.info(f"  Tema:   {noticia.get('tema_nome')}")
    log.info(f"  Título: {noticia.get('titulo')}")
    log.info(f"  Fonte:  {noticia.get('fonte')} ({noticia.get('origem')})")
    log.info(f"  URL:    {noticia.get('url') or '(sem URL — evergreen)'}")
    log.info("=" * 60)

    resultado_path = BASE / "dados" / "noticia_selecionada.json"
    salvar_json(resultado_path, noticia)
    log.info(f"Resultado salvo em {resultado_path}")

    if noticia.get("url"):
        try:
            registrar_noticia_publicada(noticia)
        except Exception as e:
            log.warning(f"[aviso] falha ao registrar histórico: {e}")

    print(json.dumps(noticia, ensure_ascii=False, indent=2))

    return noticia


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Busca notícia para o artigo diário")
    parser.add_argument("--tema", default="", help="Slug do tema específico (ex: regulacao-ia-brasil)")
    args = parser.parse_args()

    main(apenas_tema=args.tema)
