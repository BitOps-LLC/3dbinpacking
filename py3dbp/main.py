import copy

from .auxiliary_methods import intersect, set_to_decimal
from .constants import Axis, RotationType

DEFAULT_NUMBER_OF_DECIMALS = 3
START_POSITION = [0, 0, 0]


class Item:
    def __init__(self, name, width, height, depth, weight):
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.weight = weight
        self.rotation_type = 0
        self.position = list(START_POSITION)
        self.number_of_decimals = DEFAULT_NUMBER_OF_DECIMALS

    def format_numbers(self, number_of_decimals):
        self.width = set_to_decimal(self.width, number_of_decimals)
        self.height = set_to_decimal(self.height, number_of_decimals)
        self.depth = set_to_decimal(self.depth, number_of_decimals)
        self.weight = set_to_decimal(self.weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals

    def string(self):
        return (
            f"{self.name}({self.width}x{self.height}x{self.depth}, weight: {self.weight})"
            f" pos({self.position}) rt({self.rotation_type}) vol({self.get_volume()})"
        )

    def get_volume(self):
        return set_to_decimal(self.width * self.height * self.depth, self.number_of_decimals)

    def get_dimension(self):
        if self.rotation_type == RotationType.RT_WHD:
            dimension = [self.width, self.height, self.depth]
        elif self.rotation_type == RotationType.RT_HWD:
            dimension = [self.height, self.width, self.depth]
        elif self.rotation_type == RotationType.RT_HDW:
            dimension = [self.height, self.depth, self.width]
        elif self.rotation_type == RotationType.RT_DHW:
            dimension = [self.depth, self.height, self.width]
        elif self.rotation_type == RotationType.RT_DWH:
            dimension = [self.depth, self.width, self.height]
        elif self.rotation_type == RotationType.RT_WDH:
            dimension = [self.width, self.depth, self.height]
        else:
            dimension = []

        return dimension


class Bin:
    def __init__(self, name, width, height, depth, max_weight):
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.max_weight = max_weight
        self.items = []
        self.unfitted_items = []
        self.number_of_decimals = DEFAULT_NUMBER_OF_DECIMALS

    def format_numbers(self, number_of_decimals):
        self.width = set_to_decimal(self.width, number_of_decimals)
        self.height = set_to_decimal(self.height, number_of_decimals)
        self.depth = set_to_decimal(self.depth, number_of_decimals)
        self.max_weight = set_to_decimal(self.max_weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals

    def string(self):
        return (
            f"{self.name}({self.width}x{self.height}x{self.depth},"
            f" max_weight:{self.max_weight}) vol({self.get_volume()})"
        )

    def get_volume(self):
        return set_to_decimal(self.width * self.height * self.depth, self.number_of_decimals)

    def get_total_weight(self):
        total_weight = 0

        for item in self.items:
            total_weight += item.weight

        return set_to_decimal(total_weight, self.number_of_decimals)

    def put_item(self, item, pivot):
        if self.get_total_weight() + item.weight > self.max_weight:
            return False

        previous_position = item.position
        previous_rotation_type = item.rotation_type
        item.position = list(pivot)

        for rotation_type in RotationType.ALL:
            item.rotation_type = rotation_type
            dimension = item.get_dimension()
            if (
                self.width < pivot[0] + dimension[0]
                or self.height < pivot[1] + dimension[1]
                or self.depth < pivot[2] + dimension[2]
            ):
                continue

            if any(intersect(placed, item) for placed in self.items):
                continue

            self.items.append(item)
            return True

        item.position = previous_position
        item.rotation_type = previous_rotation_type
        return False


class Packer:
    def __init__(self):
        self.bins = []
        self.items = []
        self.unfit_items = []
        self.total_items = 0

    def add_bin(self, bin):
        return self.bins.append(bin)

    def add_item(self, item):
        self.total_items = len(self.items) + 1

        return self.items.append(item)

    def pack_to_bin(self, bin, item):
        fitted = False

        if not bin.items:
            response = bin.put_item(item, START_POSITION)

            if not response:
                bin.unfitted_items.append(item)

            return

        for axis in range(0, 3):
            items_in_bin = bin.items

            for ib in items_in_bin:
                pivot = [0, 0, 0]
                w, h, d = ib.get_dimension()
                if axis == Axis.WIDTH:
                    pivot = [ib.position[0] + w, ib.position[1], ib.position[2]]
                elif axis == Axis.HEIGHT:
                    pivot = [ib.position[0], ib.position[1] + h, ib.position[2]]
                elif axis == Axis.DEPTH:
                    pivot = [ib.position[0], ib.position[1], ib.position[2] + d]

                if bin.put_item(item, pivot):
                    fitted = True
                    break
            if fitted:
                break

        if not fitted:
            bin.unfitted_items.append(item)

    def pack(
        self,
        bigger_first=False,
        distribute_items=False,
        number_of_decimals=DEFAULT_NUMBER_OF_DECIMALS,
    ):
        for bin in self.bins:
            bin.items = []
            bin.unfitted_items = []
            bin.format_numbers(number_of_decimals)

        for item in self.items:
            item.format_numbers(number_of_decimals)

        self.bins.sort(key=lambda bin: bin.get_volume(), reverse=bigger_first)
        self.items.sort(key=lambda item: item.get_volume(), reverse=bigger_first)

        for bin in self.bins:
            # Each bin packs its own copies: placements recorded in one bin
            # must survive the same items being tried against the next bin.
            clones = [copy.deepcopy(item) for item in self.items]

            for clone in clones:
                self.pack_to_bin(bin, clone)

            if distribute_items:
                placed = {id(clone) for clone in bin.items}
                self.items = [
                    item
                    for item, clone in zip(self.items, clones, strict=True)
                    if id(clone) not in placed
                ]
