"""Config flow for Pandascore integration.

Step 1: ask for API token and search string.
Step 2: allow selecting teams from search results.
"""

import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from voluptuous import Required, Schema

from .api import PandascoreAPI
from .const import CONF_SEARCH, CONF_TEAMS, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = Schema(
    {Required(CONF_TOKEN): str, Required(CONF_SEARCH, default=""): str}
)


class PandascoreConfigFlow(ConfigFlow, domain=DOMAIN):
    """
    Handle the PandaScore integration configuration flow.


    The configuration flow first asks the user for a PandaScore API token
    and an optional team search string. It then searches for matching teams
    and allows the user to select the teams to configure.

    The selected teams are stored in the config entry options, while the
    PandaScore API token is stored in the config entry data.
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the PandaScore configuration flow."""
        self._token: str = ""
        self._search: str = ""
        self._teams: list[dict[str, Any]] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """
        Return the options flow for an existing PandaScore config entry.

        :param config_entry: The PandaScore configuration entry for which
            the options flow is being created.
        :return: The options flow instance used to reconfigure the integration.
        """
        return PandascoreOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handle the initial PandaScore configuration step.

        The user is asked to provide an API token and an optional search string.
        The search is then performed through the PandaScore API. If matching
        teams are found, the flow continues to the team selection step.

        :param user_input: The data submitted by the user, containing the
            PandaScore API token and optional team search string. ``None``
            when the form has not yet been submitted.
        :return: The result of the configuration flow step, either displaying
            the configuration form again or advancing to the team selection
            step.
        """
        errors = {}

        # Process user input
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

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_select_teams(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handle the team selection step of the configuration flow.

        The user can select one or more teams from the results returned by
        the previous team search. The selected teams are stored in the config
        entry options.

        :param user_input: The data submitted by the user, containing the
            identifiers of the selected teams. ``None`` when the selection
            form has not yet been submitted.
        :return: The result of the configuration flow step, either displaying
            the team selection form again or creating the config entry.
        """
        errors = {}

        # Process user input
        if user_input is not None:
            selected_ids = set(user_input.get(CONF_TEAMS, []))
            selected_teams = [
                team for team in self._teams if str(team.get("id")) in selected_ids
            ]

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
    """
    Handle the PandaScore integration options flow.


    This flow allows the user to update the list of selected teams for an
    existing PandaScore configuration entry. Teams that are no longer selected
    are removed from the associated Home Assistant device registry entry.
    """

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """
        Handle the initial options flow step.

        The currently configured team search is used to retrieve the latest
        matching teams from PandaScore. The user can then update the selected
        teams. Devices associated with teams that are no longer selected are
        removed from the config entry.

        :param user_input: The data submitted by the user, containing the
            identifiers of the selected teams. ``None`` when the options form
            has not yet been submitted.
        :return: The result of the options flow step, either displaying the
            team selection form again or creating an updated options entry.
        """
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
                stale_teams = [
                    t for t in current_teams if str(t.get("id")) not in selected_ids
                ]
                device_registry = dr.async_get(self.hass)
                for team in stale_teams:
                    device = device_registry.async_get_device(
                        identifiers={(DOMAIN, f"pandascore_{team.get('slug')}")}
                    )
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
    """
    Convert PandaScore team data into selector options.


    Each team is converted into a selector option containing its PandaScore
    identifier as the value and a display label combining the current
    videogame name and team name. The resulting options are sorted
    alphabetically by their display label.

    :param teams: A list of dictionaries containing PandaScore team data.
        Each dictionary is expected to contain an ``id``, ``name``, and
        optionally a ``current_videogame`` dictionary with a ``name`` field.
    :return: A list of selector options suitable for use with a
        :class:`SelectSelector`.
    """
    options: list[SelectOptionDict] = []
    for team in teams:
        game_name = (team.get("current_videogame") or {}).get("name", None)
        label = f"[{game_name}] {team.get('name', None)}"
        options.append(SelectOptionDict(value=str(team.get("id")), label=label))
    options.sort(key=lambda x: x["label"])
    return options


def get_schema(teams: list[dict[str, Any]], default_values: list[str]) -> Schema:
    """
    Build the schema used to select PandaScore teams.


    The generated schema provides a multi-selection list containing the
    provided teams. The identifiers in ``default_values`` are preselected
    when the form is displayed.

    :param teams: A list of dictionaries containing PandaScore team data
        to display as selectable options.
    :param default_values: A list of team identifiers that should be
        selected by default.
    :return: A Voluptuous schema containing the team selection field.
    """
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
