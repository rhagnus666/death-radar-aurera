# Death Radar – Aurera Global

Painel privado para acompanhar mortes em tempo real no Aurera Global, classificar personagens das guilds Vanguard e Chora pra Warning e enviar alertas pelo Telegram.

## Status

Projeto em implementação. O parser da página de mortes e a identificação de guilds precisam ser validados com dados reais antes de ativar alertas.

## Configuração

As credenciais devem ser configuradas como variáveis de ambiente no provedor de hospedagem. Nunca publique tokens, senhas ou arquivos `.env` neste repositório.

## Variáveis previstas

- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ADMIN_PASSWORD`
- `SECRET_KEY`
- `GUILD_ALLY=Chora pra Warning`
- `GUILD_ENEMY=Vanguard`
- `DEATHS_URL=https://telaria.aurera-global.com/?view=ultimas_mortes`
- `POLL_INTERVAL_SECONDS`

## Implantação

A implantação será feita no Render após a inclusão e validação da aplicação FastAPI, banco PostgreSQL e configuração do bot Telegram.
