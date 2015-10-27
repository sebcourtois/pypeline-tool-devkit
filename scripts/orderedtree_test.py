from pytd.util.utiltypes import OrderedTree


srcPaths = ["A/B/C", "A/C/D", "A/C/D/E", "A/C/D/F", "A/B/D/F", "A/A/D/F", "A/C/D/G"]

tree = OrderedTree.fromPaths(srcPaths)
print tree

for p in tree.iterPaths(rootPath="A/C/D"):
    print p