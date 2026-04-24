# Como replicar este blog para outros subdomínios de safie.blog.br

Este guia permite criar um novo blog temático (ex: `trabalhista.safie.blog.br`) a partir deste projeto.

---

## 1. Copiar a pasta

```bash
cp -r ~/CLAUDE/Blog-ia-for-business ~/CLAUDE/Blog-Novo-Tema
cd ~/CLAUDE/Blog-Novo-Tema
```

---

## 2. Ajustar configurações de nicho

### config/blog.json
```json
{
  "nome": "SAFIE Trabalhista",
  "descricao": "Direito trabalhista e previdenciário para empresas",
  "dominio": "trabalhista.safie.blog.br",
  "url_completa": "https://trabalhista.safie.blog.br"
}
```

### config/temas.json
Substitua os temas e palavras-chave pelo novo nicho.

### config/fontes.json
Substitua os feeds RSS por fontes relevantes para o novo nicho.

---

## 3. Limpar dados do blog anterior

```bash
echo '{"noticias":[]}' > dados/historico_noticias.json
echo '{"registros":[]}' > dados/consumo_apify.json
rm -f artigos/*.html temas/*.html dados/artigo_gerado.json dados/noticia_selecionada.json
```

---

## 4. Adaptar os templates HTML

Substituir todas as ocorrências de "SAFIE IA" / "IA for Business" / "ia.safie.blog.br" nos arquivos:
- `index.html`
- `sobre.html`
- `busca.html`
- `temas/index.html`
- `templates/artigo.html`
- `templates/tema.html`

---

## 5. Adaptar o system prompt em scripts/gerar_artigo.py

Linha `SYSTEM_PROMPT` — alterar o nicho descrito, o público-alvo e o nome do blog.

---

## 6. Criar repositório no GitHub

```bash
# Via curl (sem gh CLI):
source .env
curl -X POST https://api.github.com/user/repos \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"safie-blog-trabalhista","description":"SAFIE Trabalhista","private":false}'
```

```bash
# Inicializar git e fazer push:
git init
git add .
git commit -m "setup: estrutura inicial blog trabalhista"
git remote add origin "https://${GITHUB_TOKEN}@github.com/lucasm-mantovani/safie-blog-trabalhista.git"
git push -u origin main
```

Atualizar `.env`:
```
GITHUB_REPO=lucasm-mantovani/safie-blog-trabalhista
```

---

## 7. Criar projeto no Cloudflare Pages

1. [dash.cloudflare.com](https://dash.cloudflare.com) → Pages → Criar aplicação → Conectar ao Git
2. Selecionar o repositório recém-criado
3. Build: Framework preset = None, Build command = *(vazio)*, Output directory = `/`
4. Salvar e aguardar deploy
5. Anotar o domínio gerado (ex: `safie-blog-trabalhista.pages.dev`)

---

## 8. DNS no Registro.br

1. Acessar [registro.br](https://registro.br) → `safie.blog.br` → Zona DNS
2. Adicionar: Tipo `CNAME`, Nome `trabalhista`, Destino `safie-blog-trabalhista.pages.dev`
3. No Cloudflare Pages → Domínios personalizados → adicionar `trabalhista.safie.blog.br`

---

## 9. Configurar cron job (launchd)

```bash
LABEL="br.safie.blog.trabalhista.diario"
PASTA="$HOME/CLAUDE/Blog-Trabalhista"
HORA=8  # ajuste conforme necessário (evitar conflito com outros blogs)

cat > ~/Library/LaunchAgents/${LABEL}.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/zsh</string>
        <string>${PASTA}/rodar_diario.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${HORA}</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${PASTA}/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${PASTA}/logs/launchd_erro.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/${LABEL}.plist
```

---

## Checklist de replicação

- [ ] Pasta copiada e renomeada
- [ ] `config/blog.json` atualizado
- [ ] `config/temas.json` atualizado
- [ ] `config/fontes.json` atualizado
- [ ] Dados zerados
- [ ] Templates HTML adaptados (nome do blog, URLs)
- [ ] `SYSTEM_PROMPT` em `gerar_artigo.py` adaptado
- [ ] `.env` atualizado com `GITHUB_REPO` correto
- [ ] Repositório GitHub criado e código enviado
- [ ] Cloudflare Pages criado e conectado
- [ ] CNAME no Registro.br configurado
- [ ] Domínio personalizado no Cloudflare Pages
- [ ] Cron job (launchd) configurado
- [ ] Pipeline testado: `rodar_diario.sh` executado manualmente com sucesso
