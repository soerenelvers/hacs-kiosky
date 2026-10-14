"""Run configured Kiosky presets."""

from urllib.parse import quote

from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback

from .entity import KioskyEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator, known = entry.runtime_data, set()

    @callback
    def discover():
        entities = []
        for preset in coordinator.data["presets"]:
            if preset["id"] not in known:
                known.add(preset["id"])
                entities.append(KioskyPresetButton(coordinator, preset))
        async_add_entities(entities)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))


class KioskyPresetButton(KioskyEntity, ButtonEntity):
    _attr_name = "Execute"
    _attr_icon = "mdi:play-box"

    def __init__(self, coordinator, preset):
        super().__init__(coordinator, "preset", preset)
        self.preset_id = preset["id"]
        self._attr_unique_id += ":execute"

    @property
    def available(self):
        return super().available and any(item["id"] == self.preset_id for item in self.coordinator.data["presets"])

    async def async_press(self):
        await self.coordinator.command("POST", f"presets/{quote(self.preset_id, safe='')}/execute", {})
