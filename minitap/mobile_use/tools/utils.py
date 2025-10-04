from __future__ import annotations

from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.controllers.mobile_command_controller import (
    CoordinatesSelectorRequest,
    IdSelectorRequest,
    SelectorRequestWithCoordinates,
    tap,
)
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.utils.logger import get_logger
from minitap.mobile_use.utils.ui_hierarchy import (
    ElementBounds,
    Point,
    find_element_by_resource_id,
    get_bounds_for_element,
    get_element_text,
    is_element_focused,
)

logger = get_logger(__name__)


def find_element_by_text(ui_hierarchy: list[dict], text: str) -> dict | None:
    """
    Find a UI element by its text content (adapted to both flat and rich hierarchy)

    This function performs a recursive, case-insensitive partial search.

    Args:
        ui_hierarchy: List of UI element dictionaries.
        text: The text content to search for.

    Returns:
        The complete UI element dictionary if found, None otherwise.
    """

    def search_recursive(elements: list[dict]) -> dict | None:
        for element in elements:
            if isinstance(element, dict):
                src = element.get("attributes", element)
                if text and text.lower() == src.get("text", "").lower():
                    return element
                if (children := element.get("children", [])) and (
                    found := search_recursive(children)
                ):
                    return found
        return None

    return search_recursive(ui_hierarchy)


def tap_bottom_right_of_element(bounds: ElementBounds, ctx: MobileUseContext):
    bottom_right: Point = bounds.get_relative_point(x_percent=0.99, y_percent=0.99)
    tap(
        ctx=ctx,
        selector_request=SelectorRequestWithCoordinates(
            coordinates=CoordinatesSelectorRequest(
                x=bottom_right.x,
                y=bottom_right.y,
            ),
        ),
    )


def move_cursor_to_end_if_bounds(
    ctx: MobileUseContext,
    state: State,
    text_input_resource_id: str | None,
    text_input_coordinates: ElementBounds | None,
    text_input_text: str | None,
    elt: dict | None = None,
) -> dict | None:
    """
    Best-effort move of the text cursor near the end of the input by tapping the
    bottom-right area of the focused element (if bounds are available).
    """
    if text_input_resource_id:
        if not elt:
            elt = find_element_by_resource_id(
                ui_hierarchy=state.latest_ui_hierarchy or [],
                resource_id=text_input_resource_id,
            )
        if not elt:
            return

        bounds = get_bounds_for_element(elt)
        if not bounds:
            return elt

        logger.debug("Tapping near the end of the input to move the cursor")
        tap_bottom_right_of_element(bounds=bounds, ctx=ctx)
        logger.debug(f"Tapped end of input {text_input_resource_id}")
        return elt

    if text_input_coordinates:
        tap_bottom_right_of_element(text_input_coordinates, ctx=ctx)
        logger.debug("Tapped end of input by coordinates")
        return elt

    if text_input_text:
        text_elt = find_element_by_text(state.latest_ui_hierarchy or [], text_input_text)
        if text_elt:
            bounds = get_bounds_for_element(text_elt)
            if bounds:
                tap_bottom_right_of_element(bounds=bounds, ctx=ctx)
                logger.debug(f"Tapped end of input that had text'{text_input_text}'")
                return text_elt
        return None

    return None


def focus_element_if_needed(
    ctx: MobileUseContext,
    input_resource_id: str | None,
    input_coordinates: ElementBounds | None,
    input_text: str | None,
) -> bool:
    """
    Ensures the element is focused, with a sanity check to prevent trusting misleading IDs.
    """
    rich_hierarchy = ctx.hw_bridge_client.get_rich_hierarchy()

    elt_from_id = None
    if input_resource_id:
        elt_from_id = find_element_by_resource_id(
            ui_hierarchy=rich_hierarchy, resource_id=input_resource_id, is_rich_hierarchy=True
        )

    if elt_from_id and input_text:
        text_from_id_elt = get_element_text(elt_from_id)
        if not text_from_id_elt or input_text.lower() != text_from_id_elt.lower():
            logger.warning(
                f"ID '{input_resource_id}' and text '{input_text}'"
                + "seem to be on different elements. "
                "Ignoring the resource_id and falling back to other locators."
            )
            elt_from_id = None

    if elt_from_id:
        if not is_element_focused(elt_from_id):
            tap(ctx=ctx, selector_request=IdSelectorRequest(id=input_resource_id))  # type: ignore
            logger.debug(f"Focused (tap) on resource_id={input_resource_id}")
            rich_hierarchy = ctx.hw_bridge_client.get_rich_hierarchy()
            elt_from_id = find_element_by_resource_id(
                ui_hierarchy=rich_hierarchy,
                resource_id=input_resource_id,  # type: ignore
                is_rich_hierarchy=True,
            )
        if elt_from_id and is_element_focused(elt_from_id):
            logger.debug(f"Text input is focused: {input_resource_id}")
            return True

        logger.warning(f"Failed to focus using resource_id='{input_resource_id}'. Fallback...")

    if input_coordinates:
        relative_point = input_coordinates.get_center()
        tap(
            ctx=ctx,
            selector_request=SelectorRequestWithCoordinates(
                coordinates=CoordinatesSelectorRequest(
                    x=relative_point.x,
                    y=relative_point.y,
                ),
            ),
        )
        logger.debug(f"Tapped on coordinates ({relative_point.x}, {relative_point.y}) to focus.")
        return True

    if input_text:
        text_elt = find_element_by_text(rich_hierarchy, input_text)
        if text_elt:
            bounds = get_bounds_for_element(text_elt)
            if bounds:
                relative_point = bounds.get_center()
                tap(
                    ctx=ctx,
                    selector_request=SelectorRequestWithCoordinates(
                        coordinates=CoordinatesSelectorRequest(
                            x=relative_point.x,
                            y=relative_point.y,
                        ),
                    ),
                )
                logger.debug(f"Tapped on text element '{input_text}' to focus.")
                return True

    logger.error(
        "Failed to focus element. No valid locator"
        + "(resource_id, coordinates, or text) succeeded."
    )
    return False
