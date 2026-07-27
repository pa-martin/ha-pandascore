# 🕹️ PandaScore Integration for Home Assistant

[![HACS Badge](https://img.shields.io/badge/Available%20in-HACS-41BDF5?logo=home-assistant)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pa-martin&repository=ha-pandascore&category=integration)
[![Home Assistant](https://img.shields.io/badge/Home--Assistant-2026.7+-blue?logo=home-assistant)](https://www.home-assistant.io/blog/2026/07/01/release-20267/)

[![Licence MIT](https://img.shields.io/github/license/pa-martin/ha-pandascore?label=License&logo=github)](https://github.com/pa-martin/ha-pandascore/blob/main/LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/pa-martin/ha-pandascore?label=Release&logo=github)](https://github.com/pa-martin/ha-pandascore/releases)
[![Last Commit](https://img.shields.io/github/last-commit/pa-martin/ha-pandascore?label=Last%20Release&logo=github)](https://github.com/pa-martin/ha-pandascore/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/pa-martin/ha-pandascore?style=social)](https://github.com/pa-martin/ha-pandascore/stargazers)
<br>

Follow your favorite e-Sports teams' matches through the PandaScore API and the custom Team Tracker Card.

This documentation is also available in
- [French - Français](./README.fr.md)

---

## 📦 Installation

### 1. Via HACS (recommended)

> Requires HACS to be installed in Home Assistant

1. Go to **HACS**
2. Search for **PandaScore API**
3. Install the integration and restart Home Assistant

### 2. Manual (without HACS)

1. Download the repository contents
2. Copy the `pandascore` folder to `config/custom_components/`
3. Restart Home Assistant

---

## ⚙️ Configuration

1. Go to **Settings → Devices & services → Add Integration**
2. Search for **PandaScore API**
3. Search for teams:
   * PandaScore API key
   * Keywords used to search for multiple teams (e.g., karmine, gentle mates)
4. Team selection:
   * A list of teams returned by the API is displayed
   * Select the teams you are interested in
   * Teams are displayed using the format `[Video game] Team name`

Multiple searches can be configured separately.

## 🔐 PandaScore API Key

Get your API key here: https://app.pandascore.co/signup

1. Create an account or log in
2. Generate a free API key (under the "Your access token" section)
3. Use it when configuring the integration (limit of 1,000 requests per hour)

---

## 📊 Created Sensors

* `sensor.{videGame_slug}_{team_slug}` - The team's next match if they have an upcoming match, otherwise the last match

    * Compatible with the Team Tracker Card
* `sensor.{videGame_slug}_{team_slug}_name` - The team's name
* `sensor.{videGame_slug}_{team_slug}_game` - The video game associated with the team
* `sensor.{videGame_slug}_{team_slug}_next_match` - The next scheduled match

    * Compatible with the Team Tracker Card
* `sensor.{videGame_slug}_{team_slug}_last_match` - The last played match

    * Compatible with the Team Tracker Card
* `sensor.{videGame_slug}_{team_slug}_matches_won` - The number of matches won during the current year
* `sensor.{videGame_slug}_{team_slug}_matches_lost` - The number of matches lost during the current year
* `sensor.{videGame_slug}_{team_slug}_win_rate` - The team's win rate during the current year
* `sensor.{videGame_slug}_{team_slug}_matches_played` - The number of matches played during the current year

    * Matches - The list of played matches
* `sensor.{videGame_slug}_{team_slug}_upcoming_matches` - The number of upcoming matches

    * Matches - The list of upcoming matches

### Match Sensor Attributes

These attributes can be used with the Lovelace `custom:teamtracker-card` card (see below).

Match-related attributes:

* `state` - The match state: PRE (upcoming), IN (in progress), POST (finished)

* `sport` - The short name of the league (should be replaced with the game name?)

* `league_name` - The full league name: `[Short name] Current tournament` (e.g., `[LEC] Winter split`)

* `league_logo` - The league logo

* `date` - The match start date

* `last_update` - The last time the sensor was updated

* `clock` - Relative time since the match started (POST)

* `kickoff_in` - Relative time until the match starts (first line on the left - PRE)

* `odds` - The number of matches that need to be won to win the game (first line on the right - PRE)

* `venue` - The video game of the match (second line on the left - PRE)

* `overunder` - The full name of the match (second line on the right - PRE)

* `location` - The version of the video game (third line on the left - PRE)

* `tv_network` - The match broadcast link (third line on the right - PRE)

* `down_distance_text` - The full name of the match (line on the left - IN)

* `tv_network` - The match broadcast link (line on the right - IN)

Side-dependent attributes (`team` and `opponent`):

* `_name` - The team's name
* `_logo` - The team's logo (light mode)
* `_logo_dark` - The team's logo (dark mode)
* `_score` - The current (IN) or final (POST) match score
* `_timeouts` - The current match timeout score (IN)
* `_win_probability` - Not implemented (IN)
* `_colors` - The color to use for timeouts (IN)
* `_homeaway` - Home or away
* `_winner` - Match winner (POST)
* `_record` - League record (X-Y)
* `_rank` - Not implemented

---

## 🎨 Lovelace Card — Team Tracker Card

The integration is designed to be compatible with the Lovelace [ha-teamtracker-card](https://github.com/vasqued2/ha-teamtracker-card).

The following sensors can be used with the card:

* `sensor.{videGame_slug}_{team_slug}`
* `sensor.{videGame_slug}_{team_slug}_next_match`
* `sensor.{videGame_slug}_{team_slug}_last_match`

### Adding the Card

In a dashboard, click **+ Add Card** → search for **Team Tracker Card**.

The configuration can then be done:

* through the Lovelace visual editor (requires external configuration)
* or using YAML

Or using YAML:

```yaml
type: custom:teamtracker-card
entity: sensor.lol_karmine_corp_last_match
```

```yaml
type: custom:teamtracker-card
entity: sensor.lol_karmine_corp
home_side: left
show_timeouts: true
show_rank: true
show_league: true
outline: true
debug: true
```

---

## 📸 Previews

**First step:**

<img width="500" alt="First configuration step" src="./assets/setup_step_1.png" />

**Second step:**

<img width="500" alt="Second configuration step" src="./assets/setup_step_2.png" />

---

## 🛠 Development

Compatible with Home Assistant `2026.7+`.

See the [development documentation](./DEV.md) for local development.

Structure:

* `translations/*.json`: sensor translation files
* `__init__.py`: integration and Lovelace card registration
* `api.py`: API integration
* `config_flow.py`: configuration UI wizard
* `const.py`: constants
* `coordinator.py`: smart data retrieval logic
* `manifest.json`: metadata and dependencies
* `models.py`: data models
* `sensor.py`: sensor entities
* `strings.json`: translated strings
* `utils.py`: utility functions

---

## 👨‍💻 Author

Developed by [pa-martin](https://github.com/pa-martin)

Contributions are welcome via **Pull Requests** or **Issues**.

---

## 📄 License

Open-source code licensed under the **MIT License**.
