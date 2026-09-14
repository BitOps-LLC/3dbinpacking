"""Regression tests for defects this fork fixed after taking over upstream.

Each test states the behaviour the library must have and was originally marked
xfail(strict=True) while the defect was open. The fixes landed together with
the removal of those markers; these tests now pin the corrected behaviour so
none of the defects can quietly return. Do not relax these assertions.
"""

import helpers

from py3dbp import Bin, Item


def test_remaining_rotations_are_tried_after_a_collision():
    """A crate 2 wide, 2 high and 3 deep, packed with a unit cube and two slabs
    measuring 2 by 1 by 2.

    The cube takes the origin and the first slab stands at the far width face.
    The second slab is then offered the pivot one unit along the depth axis.
    In its width-height-depth orientation it runs into the first slab, but
    turned on its side it clears both items and sits inside the crate.
    Bin.put_item used to return from inside its rotation loop, so the first
    in-bounds rotation that collided ended the attempt and the slab was
    dropped instead of rotated.
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
        f"expected all three items to fit, got placed={helpers.placed_names(container)}"
        f" unfitted={helpers.unfitted_names(container)}"
    )
    helpers.assert_bin_invariants(container, packer.items)


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


def test_item_rejected_on_weight_keeps_its_original_position():
    """A vault limited to 5 units of weight takes a 1 unit pebble, then is
    offered a boulder weighing 10.

    The boulder is tried at three pivots and is over the limit at every one, so
    it ends up unfitted. Its position must be untouched, because it was never
    placed anywhere. Bin.put_item used to return straight out of the weight
    check without restoring item.position, which made an unfitted item
    indistinguishable from a placed one for any caller reading item.position.
    """
    packer = helpers.pack(
        [("vault", 10, 10, 10, 5)],
        [("pebble", 1, 1, 1, 1), ("boulder", 2, 2, 2, 10)],
    )
    container = helpers.find_bin(packer, "vault")
    boulder = {item.name: item for item in packer.items}["boulder"]

    assert helpers.unfitted_names(container) == ["boulder"]
    helpers.assert_position(boulder, [0, 0, 0])


def test_packing_twice_does_not_corrupt_the_bin_bookkeeping():
    """Found while writing this suite, not part of the original defect list.

    A crate is packed, then packed again with no changes in between. The second
    run must repeat the first result. Packer.pack used to append to bin.items
    and bin.unfitted_items without clearing them first, so the second call
    reported the fitting item as both placed and unfitted and listed the
    oversized one twice.
    """
    packer = helpers.build_packer(
        [("crate", 4, 4, 4, 100)],
        [("fits", 2, 2, 2, 1), ("huge", 9, 9, 9, 1)],
    )
    packer.pack()
    packer.pack()
    container = helpers.find_bin(packer, "crate")

    helpers.assert_every_item_accounted_for(container, packer.items)


def test_placements_in_the_first_bin_survive_packing_the_second():
    """Three identical 2 unit cubes offered to a 4 unit crate and a 10 unit one.

    The small crate is packed first (bins are ordered by volume) and fits all
    three. Packer.pack used to offer the same Item objects to every bin in
    turn while Bin.put_item wrote position and rotation onto the item itself,
    so packing the big crate moved items the small crate still held references
    to, leaving the small crate reporting an item outside its own wall. Each
    bin now packs its own copies.
    """
    packer = helpers.pack(
        [("small_crate", 4, 4, 4, 100), ("big_crate", 10, 10, 10, 100)],
        [("alpha", 2, 2, 2, 1), ("beta", 2, 2, 2, 1), ("gamma", 2, 2, 2, 1)],
    )
    small_crate = helpers.find_bin(packer, "small_crate")

    assert sorted(helpers.placed_names(small_crate)) == ["alpha", "beta", "gamma"]
    helpers.assert_bin_invariants(small_crate, packer.items)
