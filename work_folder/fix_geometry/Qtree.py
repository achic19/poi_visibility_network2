import matplotlib as mpl

mpl.use('agg')
import matplotlib.pyplot as plt


class Point():
    def __init__(self, x, y, id_line=None):
        self.x = x
        self.y = y
        self.id_line = id_line


class Node():
    def __init__(self, x0, y0, w, h, points):
        self.x0 = x0
        self.y0 = y0
        self.width = w
        self.height = h
        self.points = points
        self.children = []

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_points(self):
        return self.points


class QTree():
    def __init__(self, k):
        self.threshold = k
        self.points = list()
        self.line = list()
        self.root = None

    def add_point(self, x, y, id_line):
        self.points.append(Point(x, y, id_line))

    def add_root(self, x0, y0, w, h):
        self.root = Node(x0, y0, w, h, self.points)

    def get_points(self):
        return self.points

    def subdivide(self):
        self.line = recursive_subdivide(self.root, self.threshold, self.line)

    def graph(self):
        fig = plt.figure(figsize=(12, 8))
        plt.title("Quadtree")
        ax = fig.add_subplot(111)
        c = find_children(self.root)
        print("Number of segments: %d" % len(c))

        areas = set()
        for el in c:
            areas.add(el.width * el.height)
        print("Minimum segment area: %.3f units" % min(areas))

        for n in c:
            ax.add_patch(mpl.patches.Rectangle((n.x0, n.y0), n.width, n.height, fill=False))
        x = [point.x for point in self.points]
        y = [point.y for point in self.points]
        plt.plot(x, y, 'ro')
        plt.savefig("res.png")

        return


def recursive_subdivide(node, k, lines):
    if len(node.points) <= k:
        # It's ready to find a similar points
        for k, point in enumerate(node.points):
            flag = -1
            i = k
            while i + 1 < len(node.points):
                # If it's the points
                if point.x == node.points[i + 1].x and point.y == node.points[i + 1].y:
                    if flag == -1:
                        flag = node.points[i + 1].id_line
                        node.points.remove(node.points[i + 1])
                    # In case of real intersection
                    else:
                        node.points.remove(node.points[i + 1])
                        flag = -2
                else:
                    i = i + 1
            # here we indicate two line is actually the same line
            if flag > -1:
                # in case more than one segments is the same line
                if lines[flag] != flag:
                    lines[point.id_line] = lines[flag]
                else:
                    lines[flag] = lines[point.id_line]
        return lines

    w_ = float(node.width / 2)
    h_ = float(node.height / 2)

    p = contains(node.x0, node.y0, w_, h_, node.points)
    x1 = Node(node.x0, node.y0, w_, h_, p)
    lines = recursive_subdivide(x1, k, lines)

    p = contains(node.x0, node.y0 + h_, w_, h_, node.points)
    x2 = Node(node.x0, node.y0 + h_, w_, h_, p)
    lines = recursive_subdivide(x2, k, lines)

    p = contains(node.x0 + w_, node.y0, w_, h_, node.points)
    x3 = Node(node.x0 + w_, node.y0, w_, h_, p)
    lines = recursive_subdivide(x3, k, lines)

    p = contains(node.x0 + w_, node.y0 + h_, w_, h_, node.points)
    x4 = Node(node.x0 + w_, node.y0 + h_, w_, h_, p)
    lines = recursive_subdivide(x4, k, lines)

    node.children = [x1, x2, x3, x4]
    return lines


def contains(x, y, w, h, points):
    pts = []
    for point in points:
        if point.x >= x and point.x <= x + w and point.y >= y and point.y <= y + h:
            pts.append(point)
    return pts


def find_children(node):
    if not node.children:
        return [node]
    else:
        children = []
        for child in node.children:
            children += (find_children(child))
    return children


# def checks_similarity(self,node):


if __name__ == "__main__":
    my_tree = QTree(10, 0)
    my_tree.subdivide()
    my_tree.graph()
