"""Config flow for Pandascore integration.

Step 1: ask for API token and search string.
Step 2: allow selecting teams from search results.
"""
import logging
from typing import Any, List

from homeassistant.config_entries import ConfigEntry, OptionsFlow, ConfigFlowResult, ConfigFlow
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode, SelectOptionDict
from voluptuous import Required, Schema

from .api import PandascoreAPI
from .const import DOMAIN, CONF_TOKEN, CONF_SEARCH, CONF_TEAMS

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = Schema(
    {Required(CONF_TOKEN): str, Required(CONF_SEARCH, default=""): str})


class PandascoreConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._token: str = ""
        self._search: str = ""
        self._teams: list[dict[str, Any]] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Traitement de la reconfiguration."""
        return PandascoreOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Premier formulaire de configuration"""
        errors = {}

        # Traitement du retour de l'utilisateur
        if user_input is not None:
            self._token = user_input[CONF_TOKEN]
            self._search = user_input.get(CONF_SEARCH, "").strip()
            api = PandascoreAPI(self.hass, self._token)

            try:
                self._teams = await api.async_search_teams(self._search)
                if not self._teams:
                    errors["base"] = "no_teams_found"
                else:
                    return await self.async_step_select_teams()
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error validating Pandascore token")
                errors["base"] = "cannot_connect"

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

    async def async_step_select_teams(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Allow the user to select teams from the previous search result."""
        errors = {}

        # Traitement de la sélection de l'utilisateur
        if user_input is not None:
            selected_ids = set(user_input.get(CONF_TEAMS, []))
            selected_teams = [team for team in self._teams if str(
                team.get("id")) in selected_ids]

            if selected_teams:
                data = {
                    CONF_TOKEN: self._token,
                }
                options = {
                    CONF_SEARCH: self._search,
                    CONF_TEAMS: selected_teams,
                }
                return self.async_create_entry(
                    title=f"{self._search or 'teams'}", data=data, options=options
                )
            else:
                errors["base"] = "no_team_selected"

        # Création du schéma de sélection des équipes
        schema = get_schema(self._teams, [])

        # Affichage du formulaire de sélection des équipes
        return self.async_show_form(
            step_id="select_teams",
            data_schema=schema,
            errors=errors,
        )


class PandascoreOptionsFlow(OptionsFlow):
    """Handle Pandascore options."""

    async def async_step_init(
            self,
            user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:

        errors: dict[str, str] = {}
        entry = self.config_entry

        token = entry.data.get(CONF_TOKEN, "")
        search = entry.options.get(CONF_SEARCH, "")
        current_teams = entry.options.get(CONF_TEAMS, [])

        api = PandascoreAPI(
            self.hass,
            token,
        )

        try:
            teams = await api.async_search_teams(search)
            if not teams:
                errors["base"] = "no_teams_found"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error searching Pandascore teams")
            errors["base"] = "cannot_connect"
            teams = []

        # Traitement du retour de l'utilisateur
        if user_input is not None:
            selected_ids = set(user_input.get(CONF_TEAMS, []))
            if not selected_ids:
                errors["base"] = "no_team_selected"

            if not errors:
                updated_teams = [
                    team for team in teams if str(team.get("id")) in selected_ids
                ]

                # Removes teams which are unselected
                stale_teams = [t for t in current_teams if str(
                    t.get("id")) not in selected_ids]
                device_registry = dr.async_get(self.hass)
                for team in stale_teams:
                    device = device_registry.async_get_device(
                        identifiers={(DOMAIN, f"pandascore_{team.get('slug')}")})
                    device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )

                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SEARCH: search,
                        CONF_TEAMS: updated_teams,
                    },
                )

        # Récupération des équipes sélectionnées
        default_ids = [str(team.get("id")) for team in current_teams]

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(
                teams,
                default_ids,
            ),
            errors=errors,
        )


def parse_team_options(teams: list[dict[str, Any]]) -> list[SelectOptionDict]:
    options: list[SelectOptionDict] = []
    for team in teams:
        game_name = (team.get("current_videogame")
                     or {}).get("name", "Unknown")
        label = f"[{game_name}] {team.get('name', 'Unknown')}"
        options.append(SelectOptionDict(
            value=str(team.get("id")), label=label))
    options.sort(key=lambda x: x["label"])
    return options


def get_schema(teams, default_values: List) -> Schema:
    return Schema(
        {
            Required(CONF_TEAMS, default=default_values): SelectSelector(
                SelectSelectorConfig(
                    options=parse_team_options(teams),
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
        }
    )
