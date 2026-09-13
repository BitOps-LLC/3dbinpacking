"""Regression tests for defects that are present in the library right now.

Each test states the behaviour the library should have and is marked
xfail(strict=True). That means two things: the suite stays green while the
defect is open, and the moment a defect is fixed the corresponding test turns
into an XPASS failure, so nobody can fix one of these quietly. Do not relax
these assertions. If one of them starts failing as XPASS, delete the marker and
keep the assertion.
"""

import pytest

from py3dbp import Bin, Item

import helpers


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Bin.put_item returns from inside its rotation loop, so the first "
        "rotation that is in bounds is also the last one tried. When that "
        "rotation collides with an item already in the bin, the remaining "
        "rotations are never evaluated and the item is reported as unfitted."
    ),
)
def test_remaining_rotations_are_tried_after_a_collision():
    """A crate 2 wide, 2 high and 3 deep, packed with a unit cube and two slabs
    measuring 2 by 1 by 2.

    The cube takes the origin and the first slab stands at the far width face.
    The second slab is then offered the pivot one unit along the depth axis.
    In its width-height-depth orientation it runs into the first slab, but
    turned on its side it clears both items and sits inside the crate. The
    library stops at the colliding orientation and drops the slab.
    """
    packer = helpers.pack(
        [("crate", 2, 2, 3, 100)],
        [
            ("cube", 1, 1, 1, 1),
            ("slab_a", 2, 1, 2, 1),
            ("slab_b", 2, 1, 2, 1),
        ],
    )
    container = helpers.find_bin(packer, "crate")

    assert sorted(helpers.placed_names(container)) == ["cube", "slab_a", "slab_b"], (
        "expected all three items to fit, got placed=%s unfitted=%s"
        % (helpers.placed_names(container), helpers.unfitted_names(container))
    )
    helpers.assert_bin_invariants(container, packer.items)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Same rotation early return as the packer level case, reduced to a "
        "single Bin.put_item call: the flat orientation collides, the upright "
        "orientation is free, and only the flat one is ever tested."
    ),
)
def test_put_item_falls_back_to_a_later_rotation_at_the_same_pivot():
    """Smallest possible form of the rotation defect.

    A tray 3 by 3 by 1 holds a unit blocker at the far end of the width axis.
    A plank 3 by 1 by 1 is offered the origin. Lying flat it runs the full
    width and hits the blocker. Stood up across the height axis it occupies a
    different column entirely and fits.
    """
    tray = Bin("tray", 3, 3, 1, 100)
    blocker = Item("blocker", 1, 1, 1, 1)
    plank = Item("plank", 3, 1, 1, 1)

    assert tray.put_item(blocker, [2, 0, 0]) is True

    assert tray.put_item(plank, [0, 0, 0]) is True, (
        "the plank fits at this pivot when stood upright, but put_item gave up "
        "after the first in bounds rotation collided with the blocker"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Bin.put_item returns straight out of the weight check without "
        "restoring item.position, so an item rejected for weight keeps the "
        "pivot it was speculatively moved to."
    ),
)
def test_item_rejected_on_weight_keeps_its_original_position():
    """A vault limited to 5 units of weight takes a 1 unit pebble, then is
    offered a boulder weighing 10.

    The boulder is tried at three pivots and is over the limit at every one, so
    it ends up unfitted. Its position should be untouched, because it was never
    placed anywhere. Instead it reports the last pivot the packer speculatively
    moved it to, which makes an unfitted item indistinguishable from a placed
    one for any caller reading item.position.
    """
    packer = helpers.pack(
        [("vault", 10, 10, 10, 5)],
        [("pebble", 1, 1, 1, 1), ("boulder", 2, 2, 2, 10)],
    )
    container = helpers.find_bin(packer, "vault")
    boulder = {item.name: item for item in packer.items}["boulder"]

    assert helpers.unfitted_names(container) == ["boulder"]
    helpers.assert_position(boulder, [0, 0, 0])


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Packer.pack appends to bin.items and bin.unfitted_items without "
        "clearing them first, so a second call to pack() on the same packer "
        "adds every item again. Items already placed are re-offered, fail on "
        "collision with themselves, and land in unfitted_items while still "
        "sitting in items."
    ),
)
def test_packing_twice_does_not_corrupt_the_bin_bookkeeping():
    """Found while writing this suite, not part of the original defect list.

    A crate is packed, then packed again with no changes in between. The second
    run should be a no-op, or at worst repeat the first result. Instead the
    lists grow: the item that fits is reported as both placed and unfitted, and
    the item that does not fit is listed as unfitted twice.
    """
    packer = helpers.build_packer(
        [("crate", 4, 4, 4, 100)],
        [("fits", 2, 2, 2, 1), ("huge", 9, 9, 9, 1)],
    )
    packer.pack()
    packer.pack()
    container = helpers.find_bin(packer, "crate")

    helpers.assert_every_item_accounted_for(container, packer.items)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Packer.pack offers the same Item objects to every bin in turn, and "
        "Bin.put_item writes position and rotation_type onto the item itself. "
        "Placements recorded by an earlier bin are overwritten while a later "
        "bin is tried, so the earlier bin ends up holding items positioned for "
        "a different container."
    ),
)
def test_placements_in_the_first_bin_survive_packing_the_second():
    """Three identical 2 unit cubes offered to a 4 unit crate and a 10 unit one.

    The small crate is packed first (bins are ordered by volume) and fits all
    three: two along its width and the third on the second row. The big crate
    is then packed with the same objects and puts the third cube at 4 units
    along the width, which is outside the small crate. Because both crates hold
    references to the same objects, the small crate now reports an item hanging
    out of its own wall.
    """
    packer = helpers.pack(
        [("small_crate", 4, 4, 4, 100), ("big_crate", 10, 10, 10, 100)],
        [("alpha", 2, 2, 2, 1), ("beta", 2, 2, 2, 1), ("gamma", 2, 2, 2, 1)],
    )
    small_crate = helpers.find_bin(packer, "small_crate")

    assert sorted(helpers.placed_names(small_crate)) == ["alpha", "beta", "gamma"]
    helpers.assert_bin_invariants(small_crate, packer.items)
