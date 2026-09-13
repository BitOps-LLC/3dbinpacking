"""Geometry helpers and invariant checks used by the packing tests.

Everything here is deliberately independent of py3dbp's own geometry code. The
overlap test below is a plain axis aligned bounding box interval check, written
from scratch, so that it can act as an oracle for the library's `intersect`
rather than agreeing with it by construction.

All comparisons are numeric (==, <=, <). Nothing here inspects types, so the
suite keeps working if the library swaps Decimal for plain integers.
"""

from py3dbp import Bin, Item, Packer

AXES = (0, 1, 2)
AXIS_NAMES = ("width", "height", "depth")


def bin_dimensions(container):
    """The container's extent along each axis, in the same order as positions."""
    return [container.width, container.height, container.depth]


def intervals_overlap(start_a, size_a, start_b, size_b):
    """True when [start_a, start_a + size_a) and [start_b, start_b + size_b)
    share more than a boundary. Touching faces are not an overlap."""
    return start_a < start_b + size_b and start_b < start_a + size_a


def boxes_overlap(position_a, size_a, position_b, size_b):
    """True when two axis aligned boxes share volume."""
    return all(
        intervals_overlap(position_a[axis], size_a[axis],
                          position_b[axis], size_b[axis])
        for axis in AXES
    )


def build_packer(bin_specs, item_specs):
    """Build a Packer from (name, w, h, d, max_weight) and (name, w, h, d, weight)
    tuples. Item names must be unique: the invariant checks identify items by
    name."""
    packer = Packer()

    for spec in bin_specs:
        packer.add_bin(Bin(*spec))

    for spec in item_specs:
        packer.add_item(Item(*spec))

    return packer


def pack(bin_specs, item_specs, bigger_first=False):
    """Build a packer, run pack(), and hand back the packer."""
    packer = build_packer(bin_specs, item_specs)
    packer.pack(bigger_first=bigger_first)
    return packer


def find_bin(packer, name):
    """Look a bin up by name. pack() sorts packer.bins, so index is not stable."""
    for container in packer.bins:
        if container.name == name:
            return container

    raise AssertionError("no bin named %r in %r" % (
        name, [b.name for b in packer.bins]))


def placed_names(container):
    return [item.name for item in container.items]


def unfitted_names(container):
    return [item.name for item in container.unfitted_items]


def assert_item_inside_bin(item, container):
    """Every corner of the placed item lies within the container."""
    size = item.get_dimension()
    limits = bin_dimensions(container)

    for axis in AXES:
        assert item.position[axis] >= 0, (
            "item %r starts at %s on the %s axis, before the bin origin"
            % (item.name, item.position[axis], AXIS_NAMES[axis])
        )
        assert item.position[axis] + size[axis] <= limits[axis], (
            "item %r spans %s to %s on the %s axis of bin %r, which ends at %s"
            % (item.name, item.position[axis], item.position[axis] + size[axis],
               AXIS_NAMES[axis], container.name, limits[axis])
        )


def assert_no_overlaps(container):
    """No two items placed in the same bin share volume."""
    items = container.items

    for first in range(len(items)):
        for second in range(first + 1, len(items)):
            a = items[first]
            b = items[second]
            assert not boxes_overlap(
                a.position, a.get_dimension(),
                b.position, b.get_dimension()
            ), (
                "items %r at %s size %s and %r at %s size %s overlap in bin %r"
                % (a.name, list(a.position), a.get_dimension(),
                   b.name, list(b.position), b.get_dimension(), container.name)
            )


def assert_weight_within_limit(container):
    total = 0

    for item in container.items:
        total += item.weight

    assert total <= container.max_weight, (
        "bin %r holds %s of weight but its limit is %s"
        % (container.name, total, container.max_weight)
    )


def assert_every_item_accounted_for(container, all_items):
    """Each input item is either placed in this bin or recorded as unfitted for
    it, never both and never neither, and never listed twice."""
    placed = placed_names(container)
    unfitted = unfitted_names(container)
    expected = sorted(item.name for item in all_items)

    assert len(set(placed)) == len(placed), (
        "bin %r lists a placed item more than once: %s"
        % (container.name, placed))
    assert len(set(unfitted)) == len(unfitted), (
        "bin %r lists an unfitted item more than once: %s"
        % (container.name, unfitted))

    both = sorted(set(placed) & set(unfitted))
    assert not both, (
        "items %s are both placed in and unfitted for bin %r"
        % (both, container.name))

    seen = sorted(placed + unfitted)
    assert seen == expected, (
        "bin %r accounts for %s but the packer was given %s"
        % (container.name, seen, expected))


def assert_bin_invariants(container, all_items):
    for item in container.items:
        assert_item_inside_bin(item, container)

    assert_no_overlaps(container)
    assert_weight_within_limit(container)
    assert_every_item_accounted_for(container, all_items)


def assert_position(item, expected):
    """Numeric, element by element position comparison."""
    actual = list(item.position)

    assert len(actual) == len(expected)

    for axis in AXES:
        assert actual[axis] == expected[axis], (
            "item %r sits at %s, expected %s" % (item.name, actual, expected))


def assert_dimension(item, expected):
    """Numeric, element by element comparison of the rotated extent."""
    actual = item.get_dimension()

    assert len(actual) == len(expected)

    for axis in AXES:
        assert actual[axis] == expected[axis], (
            "item %r measures %s, expected %s" % (item.name, actual, expected))
