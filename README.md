# Death Radar – Aurera Global

Painel privado para acompanhar as últimas mortes do Aurera Global, classificar personagens das guilds Vanguard e Chora pra Warning e enviar alertas pelo Telegram.

## O que já está no repositório

- Aplicação FastAPI com painel responsivo e login por sessão.
- Histórico persistente em PostgreSQL (SQLite apenas para desenvolvimento local).
- Leitura periódica da página oficial de últimas mortes.
- Atualização do painel por WebSocket e consulta automática periódica.
- Alertas Telegram apenas para mortes novas identificadas como membro de uma das guilds.
- Listas de personagens importadas dos arquivos fornecidos: **460** nomes de Chora pra Warning e **206** nomes de Vanguard.
- Personagens que não correspondem às listas permanecem como **Não identificado**.
- A primeira leitura popula o histórico sem disparar uma enxurrada de alertas antigos.

## Atenção: validação antes de uso real

O parser foi ajustado ao formato textual observado na página de últimas mortes. Ainda é necessário validar a execução no Render contra o HTML efetivamente servido pelo site. A página pode mudar sua estrutura. Até concluir essa validação, não considere o monitor como operacional nem dependa dele para alertas críticos.

A classificação usa correspondência exata de nomes, ignorando anotações finais entre parênteses presentes na planilha de Vanguard. Se algum personagem mudar de guild ou se as listas ficarem desatualizadas, atualize `data/rosters.json`.

## Implantação no Render

1. Crie um **PostgreSQL** e um **Web Service** no Render usando este repositório e o arquivo `render.yaml`.
2. No serviço web, configure:
   - `ADMIN_PASSWORD`: senha longa e exclusiva para o painel.
   - `TELEGRAM_BOT_TOKEN`: token do bot criado no BotFather.
   - `TELEGRAM_CHAT_ID`: ID do chat privado onde o bot enviará os alertas.
3. O `SECRET_KEY` é gerado pelo Blueprint; não o substitua por um valor público.
4. Aguarde o deploy e confira `/health`. Depois abra a URL do serviço e entre com `ADMIN_PASSWORD`.

Não publique tokens, senhas, chaves ou arquivos `.env` no GitHub. Configure segredos somente em **Render → Environment**.

## Preparar o Telegram

1. Abra [@DeathRadarAureraBot](https://t.me/DeathRadarAureraBot) e envie `/start`.
2. Para descobrir o `chat.id`, abra no seu navegador a URL `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`, substituindo localmente pelo token do bot. Não envie essa URL nem o token para ninguém.
3. Copie o valor numérico de `message.chat.id` para `TELEGRAM_CHAT_ID` no Render.

## Variáveis de ambiente

- `DATABASE_URL` (fornecida pelo PostgreSQL do Render)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ADMIN_PASSWORD`
- `SECRET_KEY` (gerada pelo Render)
- `GUILD_ALLY=Chora pra Warning`
- `GUILD_ENEMY=Vanguard`
- `DEATHS_URL=https://telaria.aurera-global.com/?view=ultimas_mortes`
- `POLL_INTERVAL_SECONDS=30` (mínimo aplicado: 15 segundos)

## Execução local

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; no Linux/macOS, use cp
uvicorn app.main:app --reload
```

Defina `ADMIN_PASSWORD` e `SECRET_KEY` no ambiente local antes de iniciar.
