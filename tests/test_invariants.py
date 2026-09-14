"""Invariants that must hold for any pack() result.

These are the safety net for refactors: they never assert on a specific chosen
layout, only on properties that any correct packing must satisfy. A refactor is
free to place items differently, but not to place them outside the bin, on top
of each other, over the weight limit, or to lose track of them.

Scenario selection uses equivalence partitioning over the input space (one item
vs many, loose fit vs exact fit vs no fit, uniform vs mixed sizes, unconstrained
vs weight constrained) plus the boundary cases that sit between those classes
(an item exactly the size of the bin, a load exactly at the weight limit).

Every scenario uses a single bin. Packing the same items into several bins is a
separate matter and is covered in test_known_bugs.py, because the library
currently corrupts placements when it does that.
"""

import helpers
import pytest

SCENARIOS = {
    # One item in a bin many times its size: the simplest possible placement.
    "single_small_item": (
        ("solo", 10, 10, 10, 100),
        [("small_box", 2, 3, 4, 5)],
    ),
    # Boundary: the item is exactly the bin, so every dimension is at its limit.
    "exact_fit_item": (
        ("snug", 5, 5, 5, 10),
        [("filler", 5, 5, 5, 10)],
    ),
    # A uniform load that tiles the bin, which exercises pivot generation the
    # hardest: 12 cubes into a bin with room for 27.
    "many_identical_items": (
        ("grid", 6, 6, 6, 100),
        [(f"cube_{index:02d}", 2, 2, 2, 1) for index in range(12)],
    ),
    # Mixed shapes, including a flat one and a long one, so rotation matters.
    "mixed_sizes": (
        ("mixed", 10, 10, 10, 100),
        [
            ("pebble", 1, 1, 1, 1),
            ("brick", 2, 3, 4, 3),
            ("slab", 8, 1, 6, 4),
            ("rod", 10, 1, 1, 2),
            ("chunk", 5, 5, 5, 6),
            ("plank", 9, 2, 1, 2),
        ],
    ),
    # More volume offered than the bin has: most items must end up unfitted.
    "more_items_than_space": (
        ("tight", 4, 4, 4, 100),
        [(f"block_{index}", 3, 3, 3, 1) for index in range(5)],
    ),
    # Geometry is never the constraint here, weight always is. The limit is an
    # exact multiple of the item weight, so the cutoff lands on a boundary.
    "weight_constrained": (
        ("light", 10, 10, 10, 6),
        [(f"weight_{index}", 2, 2, 2, 2) for index in range(5)],
    ),
    # Nothing fits at all: the empty result is its own equivalence class.
    "nothing_fits": (
        ("doll_house", 2, 2, 2, 100),
        [("wardrobe", 5, 5, 5, 1), ("sofa", 9, 1, 1, 1)],
    ),
}


@pytest.mark.parametrize("bigger_first", [False, True])
@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_pack_result_satisfies_invariants(scenario, bigger_first):
    bin_spec, item_specs = SCENARIOS[scenario]
    packer = helpers.pack([bin_spec], item_specs, bigger_first=bigger_first)
    container = helpers.find_bin(packer, bin_spec[0])

    helpers.assert_bin_invariants(container, packer.items)


@pytest.mark.parametrize("bigger_first", [False, True])
@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_pack_does_not_lose_or_duplicate_items(scenario, bigger_first):
    """The input set is preserved across pack(), independent of where things
    ended up. Sorting happens in place, so this also guards against the sort
    dropping or duplicating entries."""
    bin_spec, item_specs = SCENARIOS[scenario]
    packer = helpers.pack([bin_spec], item_specs, bigger_first=bigger_first)

    assert sorted(item.name for item in packer.items) == sorted(spec[0] for spec in item_specs)


def test_overlap_oracle_detects_a_real_overlap():
    """The invariant suite is only worth anything if its overlap check can
    actually fire, so pin the oracle down on hand computed cases."""
    assert helpers.boxes_overlap([0, 0, 0], [2, 2, 2], [1, 1, 1], [2, 2, 2])
    assert helpers.boxes_overlap([0, 0, 0], [4, 4, 4], [1, 1, 1], [1, 1, 1])


def test_overlap_oracle_treats_touching_faces_as_clear():
    """Two boxes that share a face are packed, not overlapping."""
    assert not helpers.boxes_overlap([0, 0, 0], [2, 2, 2], [2, 0, 0], [2, 2, 2])
    assert not helpers.boxes_overlap([0, 0, 0], [2, 2, 2], [0, 0, 2], [2, 2, 2])


def test_overlap_oracle_needs_all_three_axes():
    """Separation on any single axis is enough to be clear, even when the other
    two axes overlap completely."""
    assert not helpers.boxes_overlap([0, 0, 0], [2, 2, 2], [0, 0, 5], [2, 2, 2])
