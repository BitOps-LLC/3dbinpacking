from .constants import Axis


def intersect(item1, item2):
    """True when the two items' boxes share volume.

    Plain per-axis interval overlap: two boxes intersect exactly when their
    extents overlap on all three axes. Touching faces are not an overlap.
    """
    d1 = item1.get_dimension()
    d2 = item2.get_dimension()

    return all(
        item1.position[axis] < item2.position[axis] + d2[axis]
        and item2.position[axis] < item1.position[axis] + d1[axis]
        for axis in Axis.ALL
    )
