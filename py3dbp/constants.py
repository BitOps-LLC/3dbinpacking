class RotationType:
    RT_WHD: int = 0
    RT_HWD: int = 1
    RT_HDW: int = 2
    RT_DHW: int = 3
    RT_DWH: int = 4
    RT_WDH: int = 5

    ALL: list[int] = [RT_WHD, RT_HWD, RT_HDW, RT_DHW, RT_DWH, RT_WDH]


class Axis:
    WIDTH: int = 0
    HEIGHT: int = 1
    DEPTH: int = 2

    ALL: list[int] = [WIDTH, HEIGHT, DEPTH]
