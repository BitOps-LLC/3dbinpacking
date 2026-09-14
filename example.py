from py3dbp import Bin, Item, Packer

packer = Packer()

# all dimensions in mm, all weights in g
packer.add_bin(Bin("small-envelope", 292, 155, 6, 4500))
packer.add_bin(Bin("large-envelope", 381, 304, 19, 6800))
packer.add_bin(Bin("small-box", 219, 136, 41, 31000))
packer.add_bin(Bin("medium-box", 279, 215, 139, 31000))
packer.add_bin(Bin("medium-2-box", 346, 301, 85, 31000))
packer.add_bin(Bin("large-box", 304, 304, 139, 31000))
packer.add_bin(Bin("large-2-box", 601, 298, 76, 31000))

packer.add_item(Item("50g [powder 1]", 100, 50, 50, 50))
packer.add_item(Item("50g [powder 2]", 100, 50, 50, 50))
packer.add_item(Item("50g [powder 3]", 100, 50, 50, 50))
packer.add_item(Item("250g [powder 4]", 200, 100, 50, 250))
packer.add_item(Item("250g [powder 5]", 200, 100, 50, 250))
packer.add_item(Item("250g [powder 6]", 200, 100, 50, 250))
packer.add_item(Item("250g [powder 7]", 200, 100, 50, 250))
packer.add_item(Item("250g [powder 8]", 200, 100, 50, 250))
packer.add_item(Item("250g [powder 9]", 200, 100, 50, 250))

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
