# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Dhaka Weather Wager — an original GenLayer intelligent contract.

The game: for any given day, anyone can bet YES or NO on one simple
question — "Will it rain in Dhaka tomorrow?" (or on any chosen date).

How a round works:
  1. Anyone creates a round for a date, e.g. "2026-11-19".
     One round exists per date, and everybody bets on the SAME round.
  2. Players place a wager on that round: predicts_rain = True/False.
     One wager per player per round. Betting closes when the round
     is resolved.
  3. After the date has passed, anyone calls resolve_round(). The
     contract fetches real weather data for Dhaka from the Open-Meteo
     API (free, no key), an LLM extracts the rainfall for that date,
     and the validators must agree on the result (GenLayer equivalence
     principle). A day counts as rainy when at least 0.1 mm of rain
     was recorded.
  4. Each player then claims their own result with claim_result().
     A correct prediction earns 1 point and extends the player's
     winning streak; a wrong prediction resets the streak to zero.

Points and streaks feed a leaderboard view, so the game is a
season-long competition, not a one-off bet.

Testnet only — no real money, no tokens, no prizes. GEN on the
GenLayer Studio network (studionet) is free testnet gas.
"""

import json

from dataclasses import dataclass

from genlayer import *


# Dhaka, Bangladesh (Asia/Dhaka timezone).
DHAKA_LATITUDE = 23.81
DHAKA_LONGITUDE = 90.41

# A day counts as "rainy" when Open-Meteo reports at least this much rain.
RAIN_THRESHOLD_MM = 0.1


@allow_storage
@dataclass
class Round:
    target_date: str  # "YYYY-MM-DD" — the day being bet on
    question: str  # fixed question for this round
    has_resolved: bool
    did_rain: bool
    precipitation_mm: str  # e.g. "2.4" (stored as text; LLM returns a float)
    yes_count: u256  # how many players bet "rain"
    no_count: u256  # how many players bet "no rain"


@allow_storage
@dataclass
class Wager:
    player: Address
    round_date: str
    predicts_rain: bool
    has_resolved: bool  # True once the player claimed the result
    was_correct: bool


@allow_storage
@dataclass
class PlayerStats:
    points: u256
    total_wagers: u256
    correct_wagers: u256
    current_streak: u256
    best_streak: u256


class WeatherWager(gl.Contract):
    rounds: TreeMap[str, Round]
    wagers: TreeMap[str, TreeMap[Address, Wager]]
    stats: TreeMap[Address, PlayerStats]
    total_rounds: u256

    def __init__(self):
        pass

    # -- internal: fetch real weather data under the equivalence principle --

    def _check_weather(self, target_date: str) -> dict:
        def get_weather() -> str:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                "?latitude=23.81&longitude=90.41"
                "&daily=precipitation_sum"
                "&timezone=Asia%2FDhaka&forecast_days=3&past_days=3"
            )
            web_data = gl.nondet.web.render(url, mode="text")

            task = f"""
Extract the weather for Dhaka on {target_date} from this Open-Meteo data:
{web_data}

The data has a "daily" object with a "time" list and a matching
"precipitation_sum" list (millimetres of rain for each date).
Find the entry whose date equals {target_date}.

Respond in JSON:
{{
    "resolved": bool,          // true only if the target date is present in the data
    "rained": bool,            // true if precipitation_sum for that date is >= 0.1 mm
    "precipitation_mm": float  // precipitation_sum for that date, 0.0 if absent
}}

It is mandatory that you respond only using the JSON format above,
nothing else. Don't include any other words or characters,
your output must be only JSON without any formatting prefix or suffix.
This result should be perfectly parsable by a JSON parser without errors.
"""
            result = gl.nondet.exec_prompt(task, response_format="json")
            return json.dumps(result, sort_keys=True)

        result_json = json.loads(gl.eq_principle.strict_eq(get_weather))
        return result_json

    # -- writes --

    @gl.public.write
    def create_round(self, target_date: str) -> None:
        if len(target_date) != 10:
            raise Exception("Date must be YYYY-MM-DD")
        if target_date in self.rounds:
            raise Exception("Round already exists for this date")

        self.rounds[target_date] = Round(
            target_date=target_date,
            question=f"Will it rain in Dhaka on {target_date}?",
            has_resolved=False,
            did_rain=False,
            precipitation_mm="",
            yes_count=0,
            no_count=0,
        )
        self.total_rounds += 1

    @gl.public.write
    def place_wager(self, target_date: str, predicts_rain: bool) -> None:
        if target_date not in self.rounds:
            raise Exception("Round does not exist — create it first")

        round_ = self.rounds[target_date]
        if round_.has_resolved:
            raise Exception("Round already resolved — betting is closed")

        sender = gl.message.sender_address
        if target_date in self.wagers and sender in self.wagers[target_date]:
            raise Exception("You already placed a wager on this round")

        wager = Wager(
            player=sender,
            round_date=target_date,
            predicts_rain=predicts_rain,
            has_resolved=False,
            was_correct=False,
        )
        self.wagers.get_or_insert_default(target_date)[sender] = wager

        if predicts_rain:
            round_.yes_count += 1
        else:
            round_.no_count += 1
        self.rounds[target_date] = round_

        if sender not in self.stats:
            self.stats[sender] = PlayerStats(
                points=0,
                total_wagers=0,
                correct_wagers=0,
                current_streak=0,
                best_streak=0,
            )
        player_stats = self.stats[sender]
        player_stats.total_wagers += 1
        self.stats[sender] = player_stats

    @gl.public.write
    def resolve_round(self, target_date: str) -> None:
        if target_date not in self.rounds:
            raise Exception("Round does not exist")

        round_ = self.rounds[target_date]
        if round_.has_resolved:
            raise Exception("Round already resolved")

        weather = self._check_weather(target_date)
        if not weather["resolved"]:
            raise Exception("Weather data not available yet for this date")

        round_.has_resolved = True
        round_.did_rain = bool(weather["rained"])
        round_.precipitation_mm = str(weather["precipitation_mm"])
        self.rounds[target_date] = round_

    @gl.public.write
    def claim_result(self, target_date: str) -> None:
        if target_date not in self.rounds:
            raise Exception("Round does not exist")

        round_ = self.rounds[target_date]
        if not round_.has_resolved:
            raise Exception("Round not resolved yet")

        sender = gl.message.sender_address
        if target_date not in self.wagers or sender not in self.wagers[target_date]:
            raise Exception("You did not place a wager on this round")

        wager = self.wagers[target_date][sender]
        if wager.has_resolved:
            raise Exception("Result already claimed")

        correct = wager.predicts_rain == round_.did_rain
        wager.has_resolved = True
        wager.was_correct = correct
        self.wagers[target_date][sender] = wager

        player_stats = self.stats[sender]
        if correct:
            player_stats.points += 1
            player_stats.correct_wagers += 1
            player_stats.current_streak += 1
            if player_stats.current_streak > player_stats.best_streak:
                player_stats.best_streak = player_stats.current_streak
        else:
            player_stats.current_streak = 0
        self.stats[sender] = player_stats

    # -- views --

    @gl.public.view
    def get_round(self, target_date: str) -> dict:
        if target_date not in self.rounds:
            raise Exception("Round does not exist")
        round_ = self.rounds[target_date]
        return {
            "target_date": round_.target_date,
            "question": round_.question,
            "has_resolved": round_.has_resolved,
            "did_rain": round_.did_rain,
            "precipitation_mm": round_.precipitation_mm,
            "yes_count": round_.yes_count,
            "no_count": round_.no_count,
        }

    @gl.public.view
    def get_rounds(self) -> dict:
        return {date: r for date, r in self.rounds.items()}

    @gl.public.view
    def get_wager(self, target_date: str, player_address: str) -> dict:
        player = Address(player_address)
        if target_date not in self.wagers or player not in self.wagers[target_date]:
            raise Exception("No wager found for this player on this round")
        wager = self.wagers[target_date][player]
        return {
            "player": wager.player.as_hex,
            "round_date": wager.round_date,
            "predicts_rain": wager.predicts_rain,
            "has_resolved": wager.has_resolved,
            "was_correct": wager.was_correct,
        }

    @gl.public.view
    def get_round_wagers(self, target_date: str) -> dict:
        if target_date not in self.wagers:
            return {}
        return {p.as_hex: w for p, w in self.wagers[target_date].items()}

    @gl.public.view
    def get_player_stats(self, player_address: str) -> dict:
        player = Address(player_address)
        if player not in self.stats:
            return {
                "points": 0,
                "total_wagers": 0,
                "correct_wagers": 0,
                "current_streak": 0,
                "best_streak": 0,
            }
        player_stats = self.stats[player]
        return {
            "points": player_stats.points,
            "total_wagers": player_stats.total_wagers,
            "correct_wagers": player_stats.correct_wagers,
            "current_streak": player_stats.current_streak,
            "best_streak": player_stats.best_streak,
        }

    @gl.public.view
    def get_leaderboard(self) -> dict:
        entries = []
        for player, player_stats in self.stats.items():
            entries.append(
                {
                    "player": player.as_hex,
                    "points": player_stats.points,
                    "correct_wagers": player_stats.correct_wagers,
                    "total_wagers": player_stats.total_wagers,
                    "current_streak": player_stats.current_streak,
                    "best_streak": player_stats.best_streak,
                }
            )
        entries.sort(key=lambda e: e["points"], reverse=True)
        return {"leaderboard": entries}

    @gl.public.view
    def get_total_rounds(self) -> int:
        return self.total_rounds
