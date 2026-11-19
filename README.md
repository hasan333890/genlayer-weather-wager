# 🌧️ Dhaka Weather Wager

An **original GenLayer intelligent contract**: bet YES or NO on whether it will
rain in Dhaka on a chosen day. The contract fetches real weather data from the
web (Open-Meteo API), an LLM extracts the rainfall for that date, and GenLayer
validators must agree on the result (equivalence principle) before the round
settles. Correct predictions earn points and build winning streaks on a
leaderboard.

Built by Md. Nahid Hasan (GitHub: [hasan333890](https://github.com/hasan333890)).
Testnet demo on the GenLayer Studio network — no real money, no tokens, no prizes.

## How the game works

1. **Create a round** — `create_round("2026-11-19")` opens a round for a date.
   One round exists per date, and **everybody bets on the same round**.
2. **Place a wager** — `place_wager("2026-11-19", true)` bets it will rain,
   `false` bets it will stay dry. One wager per player per round.
3. **Resolve the round** — after the date has passed, anyone calls
   `resolve_round("2026-11-19")`. The contract reads Dhaka's rainfall from
   Open-Meteo and records whether it rained (≥ 0.1 mm counts as rain).
4. **Claim your result** — `claim_result("2026-11-19")` settles your wager:
   a correct prediction earns **1 point** and extends your winning streak;
   a wrong one resets your streak to zero.

Views: `get_round`, `get_rounds`, `get_wager`, `get_round_wagers`,
`get_player_stats`, `get_leaderboard` (sorted by points), `get_total_rounds`.

## How it differs from the Football Bets example

The `football_bets.py` contract from the GenLayer boilerplate was used only as
a **style reference** for the genlayer-py SDK patterns. The game itself is new:

| Football Bets (boilerplate example) | Dhaka Weather Wager (this project) |
| --- | --- |
| Football match winner | Rain or no rain in Dhaka — a weather question |
| BBC Sport scores page | Open-Meteo weather API (free, no key, JSON) |
| Each player keeps private bets | One shared round per date — everyone bets together, with live yes/no counts |
| Points settled inside `resolve_bet` | Two-step settle: `resolve_round` fixes the weather, then each player claims with `claim_result` |
| Points only | Points + winning streaks (current & best) + sorted leaderboard view |

## Project structure

```
genlayer-weather-wager/
├── contracts/
│   └── weather_wager.py   # the intelligent contract
├── index.html             # static demo page (no wallet UI)
├── app.js                 # live Dhaka forecast + contract address display
├── README.md
└── DEPLOY-NOTES.md        # exact CLI commands for deploy day
```

## Deploy (GenLayer Studio network / studionet, via CLI)

Run on the PC that already has the GenLayer CLI and the imported account
(`main`). The keystore password is typed by the account owner in their own
terminal — never shared with anyone, never pasted in chat.

```bash
# 1. Go to the project folder (wherever the repo was cloned)
cd genlayer-weather-wager

# 2. Make sure the Studio network is selected
genlayer network set studionet

# 3. Check the account is there (already imported earlier — do NOT re-import)
genlayer account

# 4. Deploy (empty constructor, no arguments)
genlayer deploy --contract contracts/weather_wager.py
```

Copy the **contract address** from the deploy output, then verify it on the
Studio Explorer:

```
https://explorer-studio.genlayer.com/address/<CONTRACT_ADDRESS>
```

## After deploy

1. Paste the contract address into `app.js` (`CONTRACT_ADDRESS`) so the demo
   page links to the Explorer.
2. Push the repo to GitHub as `genlayer-weather-wager` (public).
3. Enable GitHub Pages on the repo (Settings → Pages → deploy from branch)
   so the demo page has a live URL.
4. Play one full round on studionet to prove it works: create a round for
   tomorrow, place a wager, resolve it after the day, claim the result.

## Evidence to attach to the GenLayer Projects submission

- **GenLayer Explorer Contract** — `https://explorer-studio.genlayer.com/address/<CONTRACT_ADDRESS>`
- **GitHub Repository** — `https://github.com/hasan333890/genlayer-weather-wager`
- **Live demo** — the GitHub Pages URL of `index.html` (after Pages is enabled)

## Notes and limits

- **Lint first:** `genvm-lint check contracts/weather_wager.py` before deploying.
- **Weather data:** Open-Meteo forecast API with `past_days=3`; a round can only
  resolve once the API returns data for the target date. Resolve the round the
  day after the date, not before.
- **Rain threshold:** ≥ 0.1 mm of precipitation on the target date counts as rain.
- **No real money:** studionet GEN is free testnet gas; the contract holds no
  funds and pays no prizes — points are leaderboard standing only.
- **Streaks:** skipping a round does not break a streak; only a wrong claim does.

## License

MIT — see the boilerplate repo this project was inspired by.
