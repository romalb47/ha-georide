"""Device tracker platform for georide."""

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CLIENT_ID

from georideapilib.objects import GeoRideAccount
import georideapilib.api as GeoRideApi
from georideapilib.socket import GeoRideSocket


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    add_entities([GeorideDeviceTracker(config)])


class GeorideDeviceTracker(TrackerEntity):
    """georide device tracker."""

    def get_tracker(account, trackerId):
        trackers = GeoRideApi.get_trackers(account.auth_token)
        for tracker in trackers:
            if int(tracker["trackerId"]) == int(trackerId):
                return tracker
        return None

    def __init__(self, config) -> None:
        self._user = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]
        self._deviceId = config[CONF_DEVICE_ID]

        self._account = GeoRideApi.get_authorisation_token(self._user, self._password)
        self._tracker = get_tracker(self._account.auth_token, self._deviceId)

    def update(self) -> None:
        self._tracker = get_tracker(self._account.auth_token, self._deviceId)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and bool(self._tracker["status"] == "online")
        )

    @property
    def latitude(self):
        """Return latitude value of the device."""
        if "latitude" in self._tracker:
            return self._tracker["latitude"]

    @property
    def longitude(self):
        """Return longitude value of the device."""
        if "longitude" in self._tracker:
            return self._tracker["longitude"]

    @property
    def source_type(self) -> SourceType:
        """Return the source type, e.g. GPS or router, of the device."""
        return SourceType.GPS

    @property
    def location_accuracy(self):
        """Return the location accuracy of the device.

        Value in meters.
        """
        return 10

    @property
    def battery_level(self):
        if "externalBatteryVoltage" in self._tracker:
            return self._tracker["externalBatteryVoltage"]

    @property
    def extra_state_attributes(self):
        """Return device specific attributes."""
        res = self._attr_extra_state_attributes

        if "trackerName" in self._tracker:
            res["trackerName"] = self._tracker["trackerName"]
        if "altitude" in self._tracker:
            res["altitude"] = self._tracker["altitude"]
        if "odometer" in self._tracker:
            res["odometer"] = self._tracker["odometer"]
        if "isLocked" in self._tracker:
            res["isLocked"] = self._tracker["isLocked"]
        if "speed" in self._tracker:
            res["speed"] = self._tracker["speed"]
        if "fixtime" in self._tracker:
            res["fixtime"] = self._tracker["fixtime"]

        return res
