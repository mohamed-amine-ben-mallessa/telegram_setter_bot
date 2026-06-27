<h1 align="center">🤖 MySetterBot TG</h1>

<p align="center">
  <b>A six-stage sales funnel that lives inside your Telegram DMs.</b><br>
  Every inbound message gets scored, tagged, answered by an LLM, and routed — and the ones worth your time land in a channel with the reason attached.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Telegram-MTProto%20user%20API-229ED9?logo=telegram&logoColor=white" alt="Telegram">
  <img src="https://img.shields.io/badge/funnel-6%20stages-1f9d55" alt="6 stages">
  <img src="https://img.shields.io/badge/LLM-any%20OpenAI--compatible-orange" alt="LLM">
  <img src="https://img.shields.io/badge/config-100%25%20YAML-6E59F7" alt="YAML">
  <img src="https://img.shields.io/badge/works-without%20an%20LLM-brightgreen" alt="Fallback">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">
</p>

```bash
python simulate.py      # score 12 sample conversations — no bot, no token, no account
```

---

> **A "setter" opens conversations and qualifies leads — it doesn't pitch and it doesn't close.**
> This bot is the setter for your Telegram inbox: it replies in seconds, figures out who
> is actually buying, and hands you only those.

## Why this exists

If you sell anything in Telegram — signals, a community, coaching, a SaaS — your DMs are
the funnel. And they're a mess: a hundred "how much?" messages, three real buyers, and no
way to tell them apart until you've typed the same four answers all day.

Most bots solve this with a rigid keypad menu that everyone abandons. This one lets people
**talk normally**, then does the boring part:

- **scores** every message across 7 dimensions (budget, urgency, experience, market, interest, referral, negativity),
- **routes** the lead through a 6-stage funnel with explicit transitions,
- **replies** with an LLM constrained to a JSON schema — so the answer is always valid,
- **forwards** the hot ones (score ≥ 85) into a channel, with tags and score attached.

Miss nothing. Read nothing.

| A keypad menu bot | **MySetterBot TG** |
|---|---|
| "Press 1 for pricing" | People type like people |
| No idea who's serious | **0-100 score**, 7 signals, visible reasoning |
| You read every DM | **Only hot leads** hit your channel |
| Logic hardcoded in Python | **Everything in YAML** — funnel, scripts, scoring, prices |
| Dies when the API key dies | **Falls back to scripted replies** — still works |

## How a lead moves

```
Incoming DM
     ↓
  Scoring (7 dimensions, keyword + pattern based)
     ↓
┌─────────────┬───────────────┬────────────────┬─────────────────┐
│  score < 30 │  score 30-70  │   score 70-85  │    score ≥ 85   │
│   ❄️ Cold    │   💬 Engaged  │    🔥 Warm     │   🔥🔥 Burning   │
│  close out  │  qualify +1   │  propose trial │  handoff        │
│             │               │                │  ✅ → channel   │
└─────────────┴───────────────┴────────────────┴─────────────────┘
                                                        ↓
                                              📅 Booked → ✅ Subscribed
```

## Scoring — what earns points

| Signal | Detected | Points |
|--------|----------|--------|
| 💰 High budget | `200€`, `500 euros`, `300$`, `150 balles` | +25 |
| 🔥 Strong urgency | `maintenant`, `urgent`, `cette semaine` | +20 |
| 🎯 Strong interest | `intéressé`, `je veux`, `signaux`, `abonner` | +20 |
| 🪙 Market named | `crypto`, `bitcoin`, `forex`, `actions` | +10 |
| 👥 Referral | `ami`, `on m'a dit`, `membre` | +10 |
| 🌱 Experience | `débutant`, `confirmé`, `expert` | +5 to +15 |
| ❌ Negative | `arnaque`, `pas intéressé`, `spam` | −50 |

Budget detection handles how people actually write money:

```
200€   ·   200 €   ·   200 euros   ·   200e   ·   200$   ·   200 bucks   ·   150 balles
```

The shipped keyword sets are **French, for a trading-signals offer** — because that's what
this was built for. They live entirely in [`config/scoring.yaml`](config/scoring.yaml) and
[`config/tunnel.yaml`](config/tunnel.yaml): swap the words, keep the machine.

## See it work in 30 seconds

```bash
pip install -r requirements.txt
python simulate.py
```

No Telegram account, no API key, no LLM. It scores 12 realistic messages and prints the
score, detected tags, funnel stage, whether it would forward, the reply it would send, and
the price it would quote. **Tune your YAML against this before going anywhere near a real inbox.**

## Install

```bash
git clone https://github.com/mohamed-amine-ben-mallessa/telegram_setter_bot
cd telegram_setter_bot

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # fill it in — see below
nano config/tunnel.yaml            # your URLs, your prices, your scripts

python -m app.main
```

**Requirements:** Python 3.10+, a Telegram account with API credentials from
[my.telegram.org/apps](https://my.telegram.org/apps), and (optionally) any OpenAI-compatible
LLM endpoint.

### `.env` — never commit this

```bash
# Telegram API (https://my.telegram.org/apps)
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_STRING=1BAAb...            # StringSession — recommended over a .session file

# LLM — any OpenAI-compatible endpoint (OpenAI, OpenRouter, Groq, Cerebras, a local server…)
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini

DATABASE_URL=sqlite:///./data/leads.db
LOG_LEVEL=INFO
```

### The YAML that runs everything

| File | Owns |
|---|---|
| [`config/tunnel.yaml`](config/tunnel.yaml) | The whole funnel: stages, tags, URLs, pricing, every script, scoring rules |
| [`config/scoring.yaml`](config/scoring.yaml) | Weights and thresholds |
| [`config/routing.yaml`](config/routing.yaml) | Stage transitions |
| [`config/scripts.yaml`](config/scripts.yaml) | Fallback replies when the LLM is unavailable |
| [`config/prompts.yaml`](config/prompts.yaml) | The setter system prompt |
| [`config/roles.yaml`](config/roles.yaml) | The setter's role definition |
| [`config/app.yaml`](config/app.yaml) | Forward channel, limits, AI settings |

Change your offer without touching a line of Python.

## The LLM layer (and why it can't produce garbage)

Replies go through **Structured Outputs** — the model is bound to a JSON schema, so it
physically cannot return prose where the bot expects a stage:

```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "ai_output",
            "strict": True,
            "schema": AIOutput.model_json_schema(),
        },
    },
)
```

Works with **OpenAI**, **OpenRouter**, **Groq**, **Cerebras**, a local server — anything
OpenAI-compatible. And if the LLM is down or unfunded, the bot falls back to the scripted
replies in `scripts.yaml` and keeps qualifying.

## What's in the box

```
app/main.py               entry point, Telethon connection, startup notification
app/config.py             Pydantic settings + YAML loader
app/ai/generator.py       LLM call with Structured Outputs
app/bot/handlers.py       receive DM → score → reply → forward
app/services/scoring.py   the 7-dimension scorer
app/services/router.py    the funnel state machine
app/services/storage.py   SQLite lead store
config/*.yaml             all the business logic
systemd/                  production service unit
simulate.py               offline scoring simulator
```

## Deploy

**systemd (Linux/VPS)** — recommended:

```bash
sudo cp systemd/telegram-setter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-setter
journalctl -u telegram-setter -f
```

Also fine under `screen`, or a Windows scheduled task calling `python -m app.main`.

## ⚠️ Read before you run this

- **It uses the Telegram *user* API** (MTProto/Telethon), not the Bot API — that's what
  lets it read your DMs and forward to a channel. Telegram can **limit or ban an account**
  that behaves like a bot. Use a **dedicated account**, keep volumes human, never mass-DM.
- **Reply, don't spam.** This is built to answer people who messaged *you*. Outbound
  blasting is how accounts die, and in most jurisdictions it's also illegal.
- **`.env` is gitignored** — keep it that way. Sessions use `StringSession`, so there's no
  `.session` file to leak.
- Tags are sanitized before reaching the prompt, so a lead can't inject instructions into
  your LLM.
- Selling trading signals is **regulated** in many countries. That's your compliance
  problem, not the bot's.

## Roadmap

- English keyword sets + language detection (`lang_code`)
- Webhook out to n8n / a CRM
- Postgres backend for scale
- Stripe / LemonSqueezy for the trial checkout
- A small web dashboard over the lead store

PRs and ideas welcome.

## Related

- 🦅 [**mysetterbot-claw**](https://github.com/mohamed-amine-ben-mallessa/mysetterbot-claw) — the same setter idea for Instagram, as 42 MCP tools your agent can call.
- ⚙️ [**mysetterbot-claw-cli**](https://github.com/mohamed-amine-ben-mallessa/mysetterbot-claw-cli) — its Instagram action layer.

## License

MIT — see [LICENSE](LICENSE).

> Not affiliated with or endorsed by Telegram. "Telegram" is a trademark of its owner.

---

<p align="center">
  <sub>Built by <a href="https://github.com/mohamed-amine-ben-mallessa">Mohamed Amine Ben Mallessa</a> · ⭐ star it if it read your DMs so you didn't have to</sub>
</p>
