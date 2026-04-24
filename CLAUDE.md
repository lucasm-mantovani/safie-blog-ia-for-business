# CLAUDE.md — Blog IA for Business SAFIE

## O que é este projeto
Blog automatizado em HTML estático, publicado em **ia.safie.blog.br**, com artigos gerados diariamente via Claude API.
O blog cobre direito e contabilidade aplicados ao mercado de inteligência artificial e tecnologia disruptiva, com foco em empresas brasileiras que usam ou desenvolvem IA.

## ATENÇÃO: dois domínios completamente diferentes

| Domínio | O que é | Pode alterar? |
|---|---|---|
| safie.com.br | Site institucional da SAFIE | **NUNCA** |
| safie.blog.br | Rede de blogs temáticos | Sim |
| ia.safie.blog.br | Este blog específico | Sim |

**NUNCA modifique, acesse para edição ou mencione safie.com.br como destino de qualquer ação de código.**

## Estrutura de pastas

```
Blog-ia-for-business/
├── config/          # Configurações do blog (blog.json, temas.json, fontes.json)
├── dados/           # Histórico de notícias e controle
├── templates/       # Templates HTML (index, artigo, tema, sobre)
├── assets/
│   ├── css/         # Estilos (herdados do Blog-Cripto)
│   ├── js/          # Scripts (busca, paginação)
│   └── img/         # Imagens e ícones
├── artigos/         # HTMLs gerados de cada artigo
├── temas/           # Páginas de listagem por tema
├── scripts/         # Scripts Python do pipeline
│   ├── buscar_noticia.py
│   ├── gerar_artigo.py
│   └── publicar.py
├── logs/            # Logs diários (não versionados)
├── rodar_diario.sh  # Script orquestrador (chamado pelo launchd às 8h)
├── sitemap.xml      # Atualizado automaticamente a cada publicação
├── robots.txt
├── .env             # Credenciais (NÃO versionado)
└── .env.template    # Modelo de credenciais (versionado, sem valores reais)
```

## Credenciais necessárias (arquivo .env)
- `ANTHROPIC_API_KEY` — geração de artigos via Claude API
- `GITHUB_TOKEN` — push automático dos artigos
- `GITHUB_REPO` — repositório no formato `usuario/nome-repo`
- `APIFY_TOKEN` — opcional, busca de notícias (fallback automático para RSS se ausente)

**Nunca hardcode credenciais. Sempre ler de variável de ambiente.**

## Pipeline diário (rodar_diario.sh — executa às 8h via launchd)
1. `buscar_noticia.py` — busca notícias via RSS (Apify opcional via config)
2. `gerar_artigo.py` — gera artigo via Claude API
3. `publicar.py` — gera HTML, atualiza home/sitemap, commit + push GitHub

## Nicho e linha editorial
- Regulação de IA (PL 2338, AI Act, ANPD)
- Direitos autorais e IA generativa (LGPD + IA)
- Responsabilidade civil por IA
- Contratos envolvendo IA e SLA
- Tributação de empresas de tecnologia e IA
- Investimento em IA e deep tech (rodadas, M&A)
- IA no trabalho e questões trabalhistas

## Regras de SEO e GEO
- Título: máximo 60 caracteres, com palavra-chave principal
- Meta description: máximo 155 caracteres
- Estrutura obrigatória: resumo executivo → contexto jurídico → impacto prático → FAQ (3-5 perguntas)
- Schema.org: BlogPosting + FAQPage em JSON-LD
- URL: `https://ia.safie.blog.br/artigos/AAAA-MM-DD-slug-do-artigo`
- Artigos: mínimo 800, máximo 1.500 palavras
- Tom: técnico, direto, sem juridiquês, sem clichês

## Estado atual do projeto (2026-04-24)
- **Fase 1 concluída:** Estrutura de pastas, configs, Git — PENDENTE INICIALIZAÇÃO GIT
- **Fase 2:** Interface HTML/CSS — PENDENTE
- **Fase 3:** buscar_noticia.py — PENDENTE
- **Fase 4:** gerar_artigo.py + publicar.py + rodar_diario.sh — PENDENTE
- **Fase 5:** GitHub + Cloudflare Pages + launchd — PENDENTE
- **Fase 6:** Validação SEO e documentação final — PENDENTE
