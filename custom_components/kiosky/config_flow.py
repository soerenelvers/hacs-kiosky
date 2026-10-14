"""UI setup, reconfiguration, reauthentication, and polling options."""

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import KioskyAuthError, KioskyClient, KioskyError, normalize_url
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .schema import vol


def form(defaults=None):
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "Kiosky")): str,
            vol.Required(CONF_URL, default=defaults.get(CONF_URL, "")): str,
            vol.Required(CONF_API_KEY): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        }
    )


class KioskyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Connect to one Kiosky installation."""

    VERSION = 1

    async def _validate(self, data):
        try:
            data[CONF_URL] = normalize_url(data[CONF_URL])
            data[CONF_API_KEY] = data[CONF_API_KEY].strip()
            if not data[CONF_API_KEY]:
                return "invalid_auth"
            await KioskyClient(async_get_clientsession(self.hass), data[CONF_URL], data[CONF_API_KEY]).validate()
        except ValueError:
            return "invalid_url"
        except KioskyAuthError:
            return "invalid_auth"
        except KioskyError:
            return "cannot_connect"
        return None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            data = dict(user_input)
            if error := await self._validate(data):
                errors["base"] = error
            else:
                await self.async_set_unique_id(data[CONF_URL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_NAME], data=data)
        return self.async_show_form(step_id="user", data_schema=form(user_input), errors=errors)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        entry = self._get_reauth_entry()
        errors = {}
        if user_input is not None:
            data = {**entry.data, **user_input}
            if error := await self._validate(data):
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(entry, data=data)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_API_KEY): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))}
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            data = dict(user_input)
            if error := await self._validate(data):
                errors["base"] = error
            else:
                await self.async_set_unique_id(data[CONF_URL])
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(entry, data=data, title=data[CONF_NAME])
        return self.async_show_form(step_id="reconfigure", data_schema=form(user_input or entry.data), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return KioskyOptionsFlow()


class KioskyOptionsFlow(config_entries.OptionsFlow):
    """Configure the polling interval."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                }
            ),
        )
