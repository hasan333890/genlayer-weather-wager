# DEPLOY-NOTES — Dhaka Weather Wager

Exact commands for deploy day. Run on the user's own PC, in the project
folder, with the GenLayer CLI (v0.39.2, already installed). The keystore
password is typed by the user in their own terminal — never shared, never
pasted in chat.

## 0. Get the code on the PC

Clone the repo (or copy the folder) into Downloads, then open a terminal
inside the project folder (File Explorer address bar → type `cmd` → Enter):

```cmd
cd C:\Users\User\Downloads\genlayer-weather-wager
```

## 1. Select the network

```cmd
genlayer network set studionet
```

Expected: `Network successfully set to Genlayer Studio Network`.

## 2. Check the account (already imported — do NOT re-import)

```cmd
genlayer account
```

Expected: account `main`, address `0xFCaad8Ca52d2c3e5D2C8B1B168b949c00F4Fed1F`,
network Genlayer Studio Network, balance ~1020 GEN.
If the account is missing, import it first with
`genlayer account import --name main` (private key typed by the user only).

## 3. Lint (optional but recommended)

```cmd
genvm-lint check contracts/weather_wager.py
```

Fix anything it reports before deploying.

## 4. Deploy

```cmd
genlayer deploy --contract contracts/weather_wager.py
```

- The contract has an empty constructor, so no arguments are needed.
- When asked, type the keystore password (the one set during import).
- Copy the **contract address** and **transaction hash** from the output.

## 5. Verify on the Explorer

Open in a browser:

```
https://explorer-studio.genlayer.com/address/<CONTRACT_ADDRESS>
```

Check: creator is the user's wallet, status FINALIZED, GenVM SUCCESS.

## 6. Update the demo page

In `app.js`, set:

```js
const CONTRACT_ADDRESS = "<CONTRACT_ADDRESS>";
```

Then push to GitHub (`genlayer-weather-wager` repo) and enable GitHub Pages
so `index.html` has a live demo URL.

## 7. Play one full round (proves it works, in Studio web UI)

In GenLayer Studio (studio.genlayer.com), connect the same wallet, open the
contract, and call — tomorrow's date as `YYYY-MM-DD`:

1. `create_round("<tomorrow>")`
2. `place_wager("<tomorrow>", true)` — true = rain, false = dry
3. Wait until after that date, then `resolve_round("<tomorrow>")`
4. `claim_result("<tomorrow>")` — point + streak update
5. `get_leaderboard()` — check the points show up

## 8. Submit to GenLayer Projects

Portal → Submit contribution → Builder → Projects. Attach as evidence:

- GenLayer Explorer Contract URL (step 5)
- GitHub Repository URL — https://github.com/hasan333890/genlayer-weather-wager
- Live demo URL — the GitHub Pages link for index.html

Notes for the submission text: original weather-betting game, Open-Meteo data,
shared daily rounds, streaks + leaderboard, deployed on studionet.
