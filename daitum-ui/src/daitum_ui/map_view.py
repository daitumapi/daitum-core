# Copyright 2026 Daitum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Map view components for the UI Generator framework.

This module provides geospatial visualization capabilities through the MapView class,
enabling the display of location-based data on interactive maps. Map views support
both individual location markers and connected route visualizations with rich
customization options.

Map views transform geographic coordinate data into interactive visual representations,
allowing users to explore spatial relationships, track movement patterns, and analyze
location-based information intuitively.

Classes:
    - MapType: Enum defining LOCATION and ROUTE map types
    - MarkerInteraction: Configuration for marker hover and click behavior
    - MapConfig: Base configuration class for map views
    - LocationConfig: Configuration specific to LOCATION map type
    - RouteConfig: Configuration specific to ROUTE map type
    - PlaybackConfig: Configuration for route playback animation
    - MapView: Complete map view with geographic visualization

Example:
    >>> # Define the data source for store locations
    >>> stores_table = Table("store_locations")
    >>> lat_field = Field("latitude", DataType.DECIMAL)
    >>> lng_field = Field("longitude", DataType.DECIMAL)
    >>> name_field = Field("store_name", DataType.STRING)
    >>>
    >>> # Create a location map view
    >>> builder = UiBuilder()
    >>> map_view = builder.add_location_view(
    ...     table=stores_table,
    ...     latitude=lat_field,
    ...     longitude=lng_field,
    ...     display_name="Store Locations"
    ... )
    >>>
    >>> # Customize the map
    >>> map_view.set_name(name_field)
    >>> map_view.set_colour(Field("region_color", DataType.STRING))
    >>> map_view.set_editable(True)
    >>>
    >>> # Add marker interaction
    >>> from daitum_ui.elements import Card
    >>> info_card = Card(...)
    >>> map_view.set_marker_behaviour(info_card)
    >>>
    >>> # Example: Create a route map for deliveries
    >>> routes_table = Table("delivery_routes")
    >>> route_lat = Field("waypoint_lat", DataType.DECIMAL_ARRAY)
    >>> route_lng = Field("waypoint_lng", DataType.DECIMAL_ARRAY)
    >>>
    >>> route_view = builder.add_route_view(
    ...     table=routes_table,
    ...     latitude=route_lat,
    ...     longitude=route_lng,
    ...     display_name="Delivery Routes"
    ... )
    >>>
    >>> # Configure route-specific features
    >>> route_view.set_date_time(Field("timestamps", DataType.DATETIME_ARRAY))
    >>> route_view.set_collapse_markers(True)
    >>> route_view.set_start_location_icon(Field("start_icon", DataType.STRING))
    >>> route_view.set_end_location_icon(Field("end_icon", DataType.STRING))
"""

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Optional, cast

from daitum_model import DataType, Field, Table
from daitum_model.named_values import NamedValue
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.elements import Card
from daitum_ui.filter_component import FilterableView, FilterComponent
from daitum_ui.model_event import ModelEvent


class MapType(Enum):
    """
    Defines the type of map view to be displayed.

    Attributes:
        ROUTE:
            Displays routes between locations, showing connections and paths.
        LOCATION:
            Displays individual locations or waypoints without showing routes between them.
    """

    ROUTE = "ROUTE"
    LOCATION = "LOCATION"


@dataclass
@typechecked
class MarkerInteraction(ABC, Buildable):
    """
    Defines the interaction behaviour for map markers.

    Attributes:
        hover_card (Card): Card to display on marker hover or click.
        on_click (Optional[ModelEvent]): Event to trigger on marker click.
    """

    hover_card: Card
    on_click: ModelEvent | None = None


@dataclass
@typechecked
class MapConfig(ABC, Buildable):
    """
    Base configuration for map views.

    Attributes:
        latitude_column (str): Field representing latitude values.
        longitude_column (str): Field representing longitude values.
        colour_column (Optional[str]): Field used to colour map elements.
        name_column (Optional[str]): Field used to name map elements.
    """

    latitude_column: str
    longitude_column: str
    colour_column: str | None = None
    name_column: str | None = None
    marker_interaction: MarkerInteraction | None = None

    start_location_icon_column: str | None = None
    end_location_icon_column: str | None = None
    resource_icon_column: str | None = None


@dataclass
@typechecked
@json_type_info("location")
class LocationConfig(MapConfig):
    """
    Configuration for LOCATION map type.

    Attributes:
        editable (bool): Whether the map points are editable by the user.
    """

    editable: bool = False


@dataclass
@typechecked
@json_type_info("route")
class RouteConfig(MapConfig):
    """
    Configuration for ROUTE map type.

    Attributes:
        date_time_column (Optional[str]): Field containing datetime values for routes.
        marker_name_column (Optional[str]): Field containing marker names for tooltips.
        resource_column (Optional[str]): Field containing route resource identifiers.
        collapse_markers (bool): Whether markers should be collapsed on the map.
        detailed_route_overview (Optional[bool]):
            Whether to show detailed road-following routes (True) or simplified
            straight lines (False). None defers to frontend default.
        work_duration_column (Optional[str]):
            Field containing work/service duration per waypoint (DECIMAL_ARRAY, hours).
        job_id_column (Optional[str]):
            Field containing job/visit identifiers per waypoint (STRING_ARRAY).
        playback_icon_column (Optional[str]):
            Field containing an icon identifier for the playback position marker (STRING).
        wait_time_column (Optional[str]):
            Field containing model-provided wait time per waypoint (DECIMAL_ARRAY, hours).
        travel_time_column (Optional[str]):
            Field containing model-provided travel time per waypoint (DECIMAL_ARRAY, hours).
        travel_distance_column (Optional[str]):
            Field containing model-provided travel distance per waypoint
            (DECIMAL_ARRAY, km).
        travel_time_is_to_waypoint (bool):
            Controls how travel time/distance arrays are indexed. When False (default),
            array[i] is the value for the leg departing FROM waypoint i. When True,
            array[i] is the value for the leg arriving AT waypoint i.
        playback_config (Optional[PlaybackConfig]):
            Playback animation configuration. If None, playback UI is hidden.
    """

    date_time_column: str | None = None
    marker_name_column: str | None = None
    resource_column: str | None = None
    collapse_markers: bool = True
    detailed_route_overview: bool | None = None
    work_duration_column: str | None = None
    job_id_column: str | None = None
    playback_icon_column: str | None = None
    wait_time_column: str | None = None
    travel_time_column: str | None = None
    travel_distance_column: str | None = None
    travel_time_is_to_waypoint: bool = False
    playback_config: Optional["PlaybackConfig"] = None


@dataclass
@typechecked
class PlaybackConfig(Buildable):
    """
    Configuration for route playback animation.

    Attributes:
        enabled (bool): Whether playback is enabled for this route view.
        playback_duration_ref (Optional[str]):
            Reference to a named value providing the total playback duration in seconds.
        playback_start_time_ref (Optional[str]):
            Reference to a named value providing the playback start time.
        playback_end_time_ref (Optional[str]):
            Reference to a named value providing the playback end time.
        metric_labels (Optional[dict[str, str]]):
            Configurable labels for the metrics summary box.
        show_all_routes (bool):
            Whether to show travel markers for all routes from the start of playback.
    """

    enabled: bool = False
    playback_duration_ref: str | None = None
    playback_start_time_ref: str | None = None
    playback_end_time_ref: str | None = None
    metric_labels: dict[str, str] | None = None
    show_all_routes: bool = True


@typechecked
@json_type_info("map")
class MapView(BaseView, FilterableView):
    """
    Represents a map view for visualising either locations or routes.

    Attributes:
        source_table (str): ID of the source table containing the data.
        map_type (MapType): Type of map (ROUTE or LOCATION).
        config (MapConfig): Configuration object specific to the map type.
    """

    def __init__(
        self,
        table: Table,
        map_type: MapType,
        latitude: Field,
        longitude: Field,
    ):
        BaseView.__init__(self)
        FilterableView.__init__(self)

        self._table = table

        self.source_table = self._table.id
        self.map_type = map_type

        expected_data_type = (
            DataType.DECIMAL if map_type == MapType.LOCATION else DataType.DECIMAL_ARRAY
        )
        self._check_field(latitude, expected_data_type)
        self._check_field(longitude, expected_data_type)

        self.map_config: MapConfig
        if map_type == MapType.LOCATION:
            self.map_config = LocationConfig(latitude.id, longitude.id)
        else:
            self.map_config = RouteConfig(latitude.id, longitude.id)

    def set_display_name(self, display_name: str) -> "MapView":
        """Sets the display name for this map view."""
        self._display_name = display_name
        return self

    def set_hidden(self, hidden: bool) -> "MapView":
        """Sets whether this map view is hidden."""
        self._hidden = hidden
        return self

    def set_use_filter(self, use_filter: "FilterComponent") -> "MapView":
        """Attaches a filter component to this map view."""
        self.use_filter = use_filter.filter_name
        self.show_filter = use_filter.filter_name
        return self

    def set_marker_behaviour(self, card: Card, on_click: ModelEvent | None = None):
        """
        Sets the marker interaction behaviour for the map view.

        Args:
            card (Card): The card to display when interacting with a marker.
            on_click (Optional[ModelEvent]): Event to trigger on marker click.
        """
        self.map_config.marker_interaction = MarkerInteraction(card, on_click)

    def set_colour(self, colour: Field):
        """
        Sets the colour column for the map view.

        Args:
            colour (Field): The field to use for colouring map elements.
        """
        self._check_field(colour, DataType.STRING)
        self.map_config.colour_column = colour.id

    def set_name(self, name: Field):
        """
        Sets the name column for the map view.

        Args:
            name (Field): The field to use for naming map elements.
        """
        self._check_field(name, DataType.STRING)
        self.map_config.name_column = name.id

    def set_editable(self, editable: bool):
        """
        Sets whether the map view is editable. Only applicable for LOCATION map type.

        Args:
            editable (bool): True to make the map editable, False otherwise.
        """
        if self.map_type != MapType.LOCATION:
            raise ValueError("ERROR - Editable property can only be set for LOCATION map type.")
        cast(LocationConfig, self.map_config).editable = editable

    def set_start_location_icon(self, start_location_icon: Field):
        """
        Sets the start location icon for the route.

        Args:
            start_location_icon (Field): The field containing the icon to display as the start
            location.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Start location icon can only be set for ROUTE map type.")
        self._check_field(start_location_icon, DataType.STRING)
        self.map_config.start_location_icon_column = start_location_icon.id

    def set_end_location_icon(self, end_location_icon: Field):
        """
        Sets the end location icon for the route.

        Args:
            end_location_icon (Field): The field containing the icon to display as the end location.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - End location icon can only be set for ROUTE map type.")
        self._check_field(end_location_icon, DataType.STRING)
        self.map_config.end_location_icon_column = end_location_icon.id

    def set_marker_name(self, marker_name: Field):
        """
        Sets the marker name.

        Args:
            marker_name (Field): The field containing the marker name.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Marker name can only be set for ROUTE map type.")
        self._check_field(marker_name, DataType.STRING_ARRAY)
        cast(RouteConfig, self.map_config).marker_name_column = marker_name.id

    def set_resource(self, resource: Field):
        """
        Sets the resource.

        Args:
            resource (Field): The field containing the resource.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Resource can only be set for ROUTE map type.")
        self._check_field(resource, DataType.STRING)
        cast(RouteConfig, self.map_config).resource_column = resource.id

    def set_resource_icon(self, resource_icon: Field):
        """
        Sets the resource icon.

        Args:
            resource_icon (Field): The field containing the icon to display for resources.
                For ROUTE map type, accepts STRING or STRING_ARRAY.
        """
        if self.map_type == MapType.ROUTE:
            self._check_field_data_types(resource_icon, DataType.STRING, DataType.STRING_ARRAY)
        else:
            self._check_field(resource_icon, DataType.STRING)
        self.map_config.resource_icon_column = resource_icon.id

    def set_date_time(self, date_time: Field):
        """
        Sets the date-time for markers on a route view.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - DateTime column can only be set for ROUTE map type.")
        expected_data_type = DataType.DATETIME_ARRAY
        self._check_field(date_time, expected_data_type)
        cast(RouteConfig, self.map_config).date_time_column = date_time.id

    def set_collapse_markers(self, collapse_markers: bool):
        """
        Sets whether to collapse markers on the map view. Only applicable for ROUTE map type.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError(
                "ERROR - Collapse markers property can only be set for ROUTE map type."
            )
        cast(RouteConfig, self.map_config).collapse_markers = collapse_markers

    def set_detailed_route_overview(self, detailed_route_overview: bool):
        """
        Sets whether to show detailed road-following routes.

        Args:
            detailed_route_overview (bool): True for detailed routes, False for simplified.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Detailed route overview can only be set for ROUTE map type.")
        cast(RouteConfig, self.map_config).detailed_route_overview = detailed_route_overview

    def set_work_duration(self, work_duration: Field):
        """
        Sets the work/service duration column per waypoint.

        Args:
            work_duration (Field): The field containing work duration values
                (DECIMAL_ARRAY, hours).
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Work duration can only be set for ROUTE map type.")
        self._check_field(work_duration, DataType.DECIMAL_ARRAY)
        cast(RouteConfig, self.map_config).work_duration_column = work_duration.id

    def set_job_id(self, job_id: Field):
        """
        Sets the job/visit identifier column per waypoint.

        Args:
            job_id (Field): The field containing job identifiers (STRING_ARRAY).
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Job ID can only be set for ROUTE map type.")
        self._check_field(job_id, DataType.STRING_ARRAY)
        cast(RouteConfig, self.map_config).job_id_column = job_id.id

    def set_playback_icon(self, playback_icon: Field):
        """
        Sets the icon for the playback position marker.

        Args:
            playback_icon (Field): The field containing the icon identifier (STRING).
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Playback icon can only be set for ROUTE map type.")
        self._check_field(playback_icon, DataType.STRING)
        cast(RouteConfig, self.map_config).playback_icon_column = playback_icon.id

    def set_wait_time(self, wait_time: Field):
        """
        Sets the model-provided wait time column per waypoint.

        Args:
            wait_time (Field): The field containing wait time values
                (DECIMAL_ARRAY, hours).
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Wait time can only be set for ROUTE map type.")
        self._check_field(wait_time, DataType.DECIMAL_ARRAY)
        cast(RouteConfig, self.map_config).wait_time_column = wait_time.id

    def set_travel_time(self, travel_time: Field):
        """
        Sets the model-provided travel time column per waypoint.

        Args:
            travel_time (Field): The field containing travel time values
                (DECIMAL_ARRAY, hours).
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Travel time can only be set for ROUTE map type.")
        self._check_field(travel_time, DataType.DECIMAL_ARRAY)
        cast(RouteConfig, self.map_config).travel_time_column = travel_time.id

    def set_travel_distance(self, travel_distance: Field):
        """
        Sets the model-provided travel distance column per waypoint.

        Args:
            travel_distance (Field): The field containing travel distance values
                (DECIMAL_ARRAY, km).
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Travel distance can only be set for ROUTE map type.")
        self._check_field(travel_distance, DataType.DECIMAL_ARRAY)
        cast(RouteConfig, self.map_config).travel_distance_column = travel_distance.id

    def set_travel_time_is_to_waypoint(self, travel_time_is_to_waypoint: bool):
        """
        Sets how travel time and distance arrays are indexed.

        Args:
            travel_time_is_to_waypoint (bool): When False (default), array[i] is the
                value for the leg departing FROM waypoint i. When True, array[i] is
                the value for the leg arriving AT waypoint i.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Travel time direction can only be set for ROUTE map type.")
        cast(RouteConfig, self.map_config).travel_time_is_to_waypoint = travel_time_is_to_waypoint

    def enable_playback(
        self,
        playback_duration: NamedValue | None = None,
        playback_start_time: NamedValue | None = None,
        playback_end_time: NamedValue | None = None,
        metric_labels: dict[str, str] | None = None,
        show_all_routes: bool = True,
    ):
        """
        Enables playback animation for this route view.

        Args:
            playback_duration (Optional[NamedValue]): Named value providing the
                total playback duration in seconds.
            playback_start_time (Optional[NamedValue]): Named value providing the
                playback start time.
            playback_end_time (Optional[NamedValue]): Named value providing the
                playback end time.
            metric_labels (Optional[dict[str, str]]): Configurable labels for the
                metrics summary box.
            show_all_routes (bool): Whether to show all route polylines fully from
                the start of playback. Default is True.
        """
        if self.map_type != MapType.ROUTE:
            raise ValueError("ERROR - Playback can only be enabled for ROUTE map type.")
        if playback_duration is not None:
            if playback_duration.to_data_type() != DataType.INTEGER:
                raise TypeError(
                    f"ERROR - Named value {playback_duration.id} must be of"
                    f" type INTEGER. Received"
                    f" {playback_duration.to_data_type()}."
                )
        if playback_start_time is not None:
            if playback_start_time.to_data_type() != DataType.DATETIME:
                raise TypeError(
                    f"ERROR - Named value {playback_start_time.id} must be of"
                    f" type DATETIME. Received"
                    f" {playback_start_time.to_data_type()}."
                )
        if playback_end_time is not None:
            if playback_end_time.to_data_type() != DataType.DATETIME:
                raise TypeError(
                    f"ERROR - Named value {playback_end_time.id} must be of"
                    f" type DATETIME. Received"
                    f" {playback_end_time.to_data_type()}."
                )
        playback_config = PlaybackConfig(
            enabled=True,
            playback_duration_ref=(playback_duration.id if playback_duration is not None else None),
            playback_start_time_ref=(
                playback_start_time.id if playback_start_time is not None else None
            ),
            playback_end_time_ref=(playback_end_time.id if playback_end_time is not None else None),
            metric_labels=metric_labels,
            show_all_routes=show_all_routes,
        )
        cast(RouteConfig, self.map_config).playback_config = playback_config

    def _check_field(self, field: Field, data_type: DataType):
        if field not in self._table.get_fields():
            raise ValueError(
                f"ERROR - Field {field.id} is not present in the table " f"{self._table.id}."
            )

        if field.to_data_type() != data_type:
            raise TypeError(
                f"ERROR - Field {field.id} must be of type "
                f"{data_type}. Received {field.to_data_type()}."
            )

    def _check_field_data_types(self, field: Field, *data_types: DataType):
        if field not in self._table.get_fields():
            raise ValueError(
                f"ERROR - Field {field.id} is not present in the table " f"{self._table.id}."
            )

        if field.to_data_type() not in data_types:
            allowed_types = ", ".join([str(dt) for dt in data_types])
            raise TypeError(
                f"ERROR - Field {field.id} must be of type "
                f"{allowed_types}. Received {field.to_data_type()}."
            )
