"""Deterministic placement cases with hand computed expected results.

Each case fixes the bin, the items, and the exact outcome the algorithm should
produce, worked out by hand from the pivot order (width, then height, then
depth) and the rotation order (width-height-depth first). Where a value sits on
a limit, the partner case one unit either side of it is included, so the
boundary itself is covered rather than assumed.
"""

import helpers
import pytest


def test_item_exactly_the_size_of_the_bin_fits_at_the_origin():
    """Boundary: every dimension is exactly at its limit, which must still fit."""
    packer = helpers.pack(
        [("box", 10, 10, 10, 10)],
        [("cargo", 10, 10, 10, 5)],
    )
    container = helpers.find_bin(packer, "box")

    assert helpers.placed_names(container) == ["cargo"]
    assert helpers.unfitted_names(container) == []
    helpers.assert_position(container.items[0], [0, 0, 0])
    helpers.assert_dimension(container.items[0], [10, 10, 10])


def test_item_one_unit_larger_than_the_bin_does_not_fit():
    """Boundary partner to the exact fit case: one unit over on a single axis."""
    packer = helpers.pack(
        [("box", 10, 10, 10, 10)],
        [("cargo", 10, 10, 11, 5)],
    )
    container = helpers.find_bin(packer, "box")

    assert helpers.placed_names(container) == []
    assert helpers.unfitted_names(container) == ["cargo"]


def test_item_too_long_in_its_given_orientation_is_rotated_to_fit():
    """The beam is 10 wide in a bin only 5 wide, but the bin is 10 high. Turning
    it on its end (the height-width-depth rotation) puts it inside."""
    packer = helpers.pack(
        [("narrow", 5, 10, 5, 100)],
        [("beam", 10, 5, 5, 1)],
    )
    container = helpers.find_bin(packer, "narrow")

    assert helpers.placed_names(container) == ["beam"]
    beam = container.items[0]
    helpers.assert_position(beam, [0, 0, 0])
    helpers.assert_dimension(beam, [5, 10, 5])
    assert beam.rotation_type != 0
    helpers.assert_item_inside_bin(beam, container)


def test_item_too_big_in_every_orientation_is_unfitted():
    packer = helpers.pack(
        [("cramped", 5, 5, 5, 100)],
        [("boulder", 6, 6, 6, 1)],
    )
    container = helpers.find_bin(packer, "cramped")

    assert helpers.placed_names(container) == []
    assert helpers.unfitted_names(container) == ["boulder"]


def test_item_that_fits_by_volume_but_not_by_shape_is_unfitted():
    """The rod holds 25 units of volume against the bin's 125, so a volume only
    check would accept it. No rotation gets a 25 unit edge into a 5 unit bin."""
    packer = helpers.pack(
        [("cramped", 5, 5, 5, 100)],
        [("rod", 25, 1, 1, 1)],
    )
    container = helpers.find_bin(packer, "cramped")

    assert helpers.placed_names(container) == []
    assert helpers.unfitted_names(container) == ["rod"]


def test_item_heavier_than_the_limit_is_unfitted_despite_fitting_geometrically():
    packer = helpers.pack(
        [("featherweight", 10, 10, 10, 5)],
        [("anvil", 1, 1, 1, 6)],
    )
    container = helpers.find_bin(packer, "featherweight")

    assert helpers.placed_names(container) == []
    assert helpers.unfitted_names(container) == ["anvil"]
    assert container.get_total_weight() == 0


def test_item_exactly_at_the_weight_limit_is_accepted():
    """Boundary partner: the limit is inclusive, so an exact match must fit."""
    packer = helpers.pack(
        [("featherweight", 10, 10, 10, 5)],
        [("anvil", 1, 1, 1, 5)],
    )
    container = helpers.find_bin(packer, "featherweight")

    assert helpers.placed_names(container) == ["anvil"]
    assert container.get_total_weight() == 5


def test_two_items_are_placed_side_by_side_along_the_width():
    """The bin is exactly two items wide and one item high and deep, so the only
    packing is side by side. Width is the first pivot axis, so the second item
    lands at the first item's far face."""
    packer = helpers.pack(
        [("shelf", 10, 5, 5, 100)],
        [("left", 5, 5, 5, 1), ("right", 5, 5, 5, 1)],
    )
    container = helpers.find_bin(packer, "shelf")

    assert sorted(helpers.placed_names(container)) == ["left", "right"]
    assert helpers.unfitted_names(container) == []

    by_name = {item.name: item for item in container.items}
    helpers.assert_position(by_name["left"], [0, 0, 0])
    helpers.assert_position(by_name["right"], [5, 0, 0])
    helpers.assert_no_overlaps(container)


def test_an_occupied_pivot_is_skipped_in_favour_of_the_next_one():
    """An alcove 4 by 4 by 1 takes three tiles of 2 by 2 by 1.

    The first two tiles fill the bottom row. The third is offered the first
    tile's width pivot, which the second tile already occupies, so it has to
    fall through to the height pivot and start the second row.
    """
    packer = helpers.pack(
        [("alcove", 4, 4, 1, 100)],
        [("tile_a", 2, 2, 1, 1), ("tile_b", 2, 2, 1, 1), ("tile_c", 2, 2, 1, 1)],
    )
    container = helpers.find_bin(packer, "alcove")

    assert sorted(helpers.placed_names(container)) == ["tile_a", "tile_b", "tile_c"]
    by_name = {item.name: item for item in container.items}
    helpers.assert_position(by_name["tile_a"], [0, 0, 0])
    helpers.assert_position(by_name["tile_b"], [2, 0, 0])
    helpers.assert_position(by_name["tile_c"], [0, 2, 0])


def test_second_item_is_rejected_when_the_combined_weight_exceeds_the_limit():
    """Both items fit geometrically with room to spare. Only weight stops the
    second one: 6 plus 6 is over the limit of 10."""
    packer = helpers.pack(
        [("scale", 10, 10, 10, 10)],
        [("first", 5, 5, 5, 6), ("second", 5, 5, 5, 6)],
    )
    container = helpers.find_bin(packer, "scale")

    assert helpers.placed_names(container) == ["first"]
    assert helpers.unfitted_names(container) == ["second"]
    assert container.get_total_weight() == 6


def test_second_item_is_accepted_when_the_combined_weight_hits_the_limit_exactly():
    """Boundary partner to the rejection case: the same two items under a limit
    of exactly their combined weight."""
    packer = helpers.pack(
        [("scale", 10, 10, 10, 12)],
        [("first", 5, 5, 5, 6), ("second", 5, 5, 5, 6)],
    )
    container = helpers.find_bin(packer, "scale")

    assert sorted(helpers.placed_names(container)) == ["first", "second"]
    assert helpers.unfitted_names(container) == []
    assert container.get_total_weight() == 12


@pytest.mark.parametrize("bigger_first", [False, True])
def test_bigger_first_controls_which_item_is_placed_when_only_one_fits(bigger_first):
    """The bin holds exactly one of the two items. bigger_first decides which one
    is offered first, and therefore which one gets the space."""
    packer = helpers.pack(
        [("single_slot", 4, 4, 4, 100)],
        [("small", 2, 2, 2, 1), ("large", 4, 4, 4, 1)],
        bigger_first=bigger_first,
    )
    container = helpers.find_bin(packer, "single_slot")

    if bigger_first:
        assert helpers.placed_names(container) == ["large"]
        assert helpers.unfitted_names(container) == ["small"]
    else:
        assert helpers.placed_names(container) == ["small"]
        assert helpers.unfitted_names(container) == ["large"]
