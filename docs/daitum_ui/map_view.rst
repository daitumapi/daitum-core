Map View
========

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

.. autoclass:: daitum_ui.map_view.MapView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.map_view.LocationConfig
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.map_view.MapConfig
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.map_view.MapType
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.map_view.MarkerInteraction
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.map_view.PlaybackConfig
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.map_view.RouteConfig
    :no-index:
    :members:
    :show-inheritance:
