3D Bin Packing
====

3D Bin Packing implementation based on [this paper](erick_dube_507-034.pdf). The code is based on [gedex](https://github.com/gedex/bp3d) implementation in Go.

This is a maintained fork of [enzoruiz/3dbinpacking](https://github.com/enzoruiz/3dbinpacking) by [BitOps LLC](https://bitops.it). It is maintained as we need it: bug fixes and features land when our own use cases require them.

## Features
1. Sorting Bins and Items:
    ```[bigger_first=True/False]``` By default bins and items are sorted from the biggest to the smallest, matching the First Fit Decreasing ordering from the underlying paper. Pass `bigger_first=False` for smallest-first. This default is flipped relative to upstream py3dbp (changed in 2.0).
2. Item Distribution:
    - ```[distribute_items=True]``` From a list of bins and items, put the items in the bins that at least one item be in one bin that can be fitted. That is, distribute all the items in all the bins so that they can be contained.
    - ```[distribute_items=False]``` From a list of bins and items, try to put all the items in each bin and in the end it show per bin all the items that was fitted and the items that was not.
3. Integer units:
    Dimensions and weights are expected as integers in a unit of your choice (millimetres and grams work well). All arithmetic is then exact: no floats, no rounding, no tolerance questions. Convert from cm/kg at your application boundary. The upstream `number_of_decimals` Decimal machinery was removed in 2.0.
4. Usable-dimension slack:
    ```[usable_factor=1]``` Optional on `Bin`. Real cartons flex and contents shift; a factor below 1 shrinks the usable inner dimensions (floored, so they stay integer), e.g. `usable_factor=0.95` packs against 95% of the nominal inner size. Default 1 uses the dimensions exactly as given.

## Install

```
pip install git+https://github.com/BitOps-LLC/3dbinpacking.git
```

(`pip install py3dbp` installs the original, unmaintained upstream release from PyPI, not this fork.)

## Basic Explanation

Bin and Items have the same creation params (integer units recommended, e.g. mm and g):
```
my_bin = Bin(name, width, height, depth, max_weight, usable_factor=1)
my_item = Item(name, width, height, depth, weight)
```
Packer have three main functions:
```
packer = Packer()           # PACKER DEFINITION

packer.add_bin(my_bin)      # ADDING BINS TO PACKER
packer.add_item(my_item)    # ADDING ITEMS TO PACKER

packer.pack()               # PACKING - by default (bigger_first=True, distribute_items=False)
```

After packing:
```
packer.bins                 # GET ALL BINS OF PACKER
my_bin.items                # GET ALL FITTED ITEMS IN EACH BIN
my_bin.unfitted_items       # GET ALL UNFITTED ITEMS IN EACH BIN
```


## Usage

```
from py3dbp import Packer, Bin, Item

packer = Packer()

# all dimensions in mm, all weights in g
packer.add_bin(Bin('small-envelope', 292, 155, 6, 4500))
packer.add_bin(Bin('large-envelope', 381, 304, 19, 6800))
packer.add_bin(Bin('small-box', 219, 136, 41, 31000))
packer.add_bin(Bin('medium-box', 279, 215, 139, 31000))
packer.add_bin(Bin('medium-2-box', 346, 301, 85, 31000))
packer.add_bin(Bin('large-box', 304, 304, 139, 31000))
packer.add_bin(Bin('large-2-box', 601, 298, 76, 31000))

packer.add_item(Item('50g [powder 1]', 100, 50, 50, 50))
packer.add_item(Item('50g [powder 2]', 100, 50, 50, 50))
packer.add_item(Item('50g [powder 3]', 100, 50, 50, 50))
packer.add_item(Item('250g [powder 4]', 200, 100, 50, 250))
packer.add_item(Item('250g [powder 5]', 200, 100, 50, 250))
packer.add_item(Item('250g [powder 6]', 200, 100, 50, 250))
packer.add_item(Item('250g [powder 7]', 200, 100, 50, 250))
packer.add_item(Item('250g [powder 8]', 200, 100, 50, 250))
packer.add_item(Item('250g [powder 9]', 200, 100, 50, 250))

packer.pack()

for b in packer.bins:
    print(":::::::::::", b.string())

    print("FITTED ITEMS:")
    for item in b.items:
        print("====> ", item.string())

    print("UNFITTED ITEMS:")
    for item in b.unfitted_items:
        print("====> ", item.string())

    print("***************************************************")
    print("***************************************************")

```

## Development

Set up a working environment with the dev extras and the git hooks:

```
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" pre-commit
pre-commit install
```

Every commit then runs [pre-commit](https://pre-commit.com) automatically:
ruff (lint with autofix, plus formatting), the pytest suite, and basic
hygiene checks (trailing whitespace, file endings, TOML/YAML validity,
merge-conflict markers, oversized files). The commit message must follow
[Conventional Commits](https://www.conventionalcommits.org)
(`type(scope): subject`, e.g. `fix: try all rotations at a pivot`).
A commit is rejected if any hook fails.

Run the same checks by hand:

```
pre-commit run --all-files   # everything, exactly as on commit
ruff check .                 # lint only
ruff format .                # format only
pytest                       # test suite only
```

The suite contains strict `xfail` tests documenting known upstream defects;
they count as passing until the defect is fixed, at which point they fail
loudly and must be flipped to regular tests in the same change.

All changes go through pull requests; nothing is pushed to `main` directly.
CI runs the same gates on every pull request (pre-commit over all files,
plus the test suite on every supported Python from 3.10 to 3.14), so the
checks hold even for a clone that never ran `pre-commit install`.

## Versioning
- **2.x** (this fork)
    - Correct rotation search, state handling, and independent per-bin packing.
    - Default ordering biggest-first (First Fit Decreasing, per the paper).
    - Integer units, exact arithmetic; Decimal and `number_of_decimals` removed.
    - Optional `usable_factor` on `Bin` for packing slack.
- **1.x**
    - Two ways to distribute items (all items in all bins - all items in each bin).
    - Get per bin the fitted and unfitted items.
    - Set the limit of decimals of inputs and outputs.
- **0.x**
    - Try to put all items in the first bin that can fit at least one.

## Credit

* https://github.com/bom-d-van/binpacking
* https://github.com/gedex/bp3d
* [Optimizing three-dimensional bin packing through simulation](erick_dube_507-034.pdf)

## License

[MIT](./LICENSE)
