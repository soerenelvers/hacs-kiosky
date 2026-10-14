"""Expose resource counts and IDs for automation setup."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory

from .entity import KioskyEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            KioskyResourceSensor(entry.runtime_data, key, name)
            for key, name in (
                ("displays", "Displays"),
                ("display-groups", "Display groups"),
                ("channels", "Channels"),
                ("slides", "Slides"),
                ("presets", "Presets"),
            )
        ]
    )


class KioskyResourceSensor(KioskyEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id += f":{key}"

    @property
    def native_value(self):
        return len(self.coordinator.data[self.key])

    @property
    def extra_state_attributes(self):
        # Whitelist IDs/names only: displays may contain sensitive player keys.
        return {
            "resources": [
                {"id": item["id"], "name": item.get("name", item["id"])} for item in self.coordinator.data[self.key]
            ]
        }
