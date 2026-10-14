"""Choose an external channel for a display or a display group."""

from homeassistant.components.select import SelectEntity
from homeassistant.core import callback

from .entity import KioskyEntity

SCHEDULE = "[Kiosky schedule]"


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    known = set()

    @callback
    def discover():
        entities = []
        for kind, key in (("display", "displays"), ("group", "display-groups")):
            for resource in coordinator.data[key]:
                identity = (kind, resource["id"])
                if identity not in known:
                    known.add(identity)
                    entities.append(KioskyChannelSelect(coordinator, kind, resource))
        async_add_entities(entities)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))


class KioskyChannelSelect(KioskyEntity, SelectEntity):
    """Direct external assignment; does not claim to show effective player output."""

    _attr_name = "External channel"
    _attr_icon = "mdi:television-play"

    def __init__(self, coordinator, kind, resource):
        super().__init__(coordinator, kind, resource)
        self.kind, self.resource_id = kind, resource["id"]
        self._attr_unique_id += ":channel"

    def _channels(self):
        # IDs make duplicate names and reserved labels unambiguous.
        return {
            f"{item.get('name', 'Channel')} [{item['id']}]": item["id"] for item in self.coordinator.data["channels"]
        }

    @property
    def available(self):
        key = "displays" if self.kind == "display" else "display-groups"
        return super().available and any(item["id"] == self.resource_id for item in self.coordinator.data[key])

    @property
    def options(self):
        return [SCHEDULE, *self._channels()]

    @property
    def current_option(self):
        assignment = next(
            (
                item
                for item in self.coordinator.data["assignments"]
                if item["target"] == {"type": self.kind, "id": self.resource_id}
            ),
            None,
        )
        if assignment is None:
            return SCHEDULE
        if assignment["content"]["type"] != "channel":
            return None
        return next(
            (name for name, identity in self._channels().items() if identity == assignment["content"]["id"]), None
        )

    async def async_select_option(self, option):
        if option == SCHEDULE:
            await self.coordinator.command(
                "POST", "presets/stop", {"targets": [{"type": self.kind, "id": self.resource_id}], "endWarnings": False}
            )
        else:
            await self.coordinator.command(
                "POST",
                "assignments",
                {
                    "target": {"type": self.kind, "id": self.resource_id},
                    "content": {"type": "channel", "id": self._channels()[option]},
                    "priority": 100,
                },
            )
