# Tell Python where you will get processing from

from os.path import join, exists, dirname
import sys

from operator import itemgetter
import numpy
from PyQt5.QtGui import *

from qgis.PyQt.QtCore import QVariant

from qgis.core import QgsPointXY, QgsRectangle, QgsGeometry, QgsVectorLayer, QgsFields, QgsField, QgsFeature

from qgis.analysis import QgsNativeAlgorithms
import time
from shutil import copy

# Reference the algorithm you want to run
sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.16\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.22.3\apps\qgis\python\plugins')
from plugins import processing


class Cell:
    def __init__(self, x, y, spacing, i_x, i_y):
        """
        :param x:
        :param y:
        :param spacing: size cell
        :param i_x: cell index in x direction
        :param i_y: cell index in y direction
        """
        self.poly, self.extent, self.i_e, self.i_n = [], {'SW': QgsPointXY(x, y), 'SE': QgsPointXY(x + spacing, y),
                                                          'NE': QgsPointXY(x + spacing, y + spacing),
                                                          'NW': QgsPointXY(x, y + spacing)}, i_x, i_y

    def __iter__(self):
        return iter(self.poly)


class SameAreaPoly:
    def __init__(self, poly: QgsGeometry):
        """
        The class stores : QgsGeometry Polygon and a boolean value that check if it is checked in  the SameArea database
        :param poly:
        """
        self.poly_qgs = poly
        self.is_no_passed = True

    def set_is_no_passed(self):
        self.is_no_passed = True


class SameAreaCell:
    def __init__(self, points_list, size):
        """
        The class gets a points list and build SameAreaCell upon it with the specified cell size
        :param points_list:
        """
        # Number of cell in each dimension
        self.size_cell, self.num_of_pnt, self.x_min, self.y_min, x_max, y_max = size, 0, min(points_list,
                                                                                             key=itemgetter(
                                                                                                 0))[
            0], min(points_list, key=itemgetter(1))[1], max(points_list, key=itemgetter(0))[0], max(points_list,
                                                                                                    key=itemgetter(1))[
                                                                                    1]
        size_cell, x_min, y_min = self.size_cell, self.x_min, self.y_min
        n_y, n_x = int((y_max - y_min) / size_cell) + 1, int(
            (x_max - x_min) / size_cell) + 1
        self.data_set = [
            [Cell(x_min + ii * size_cell, y_min + j * size_cell, size_cell, ii, j) for j in
             range(n_y)] for ii in range(n_x)]

    def __getitem__(self, p):
        """
        :param p: tuple of indices
        :return: a cell from the dataset based on the indices
        """
        x, y = p
        return self.data_set[x][y]

    def add_polygons(self, bounding: QgsRectangle, cur_poly: SameAreaPoly):
        """
        add a polygon to all cells that cross the polygon
        :param bounding: polygon rectangle extent
        :param cur_poly: the polygon to add
        :return:
        """
        size_cell = self.size_cell

        in_x, in_y = ((numpy.array([bounding.xMinimum(), bounding.xMaximum()]) - self.x_min) / size_cell).astype(
            int), ((numpy.array([bounding.yMinimum(), bounding.yMaximum()]) - self.y_min) / size_cell).astype(int)
        try:
            [[self[x, y].poly.append(cur_poly) for x in range(in_x[0], in_x[1] + 1)] for y in
             range(in_y[0], in_y[1] + 1)]
        except:
            pass

    def find_cell(self, pnt: QgsPointXY):
        size_cell = self.size_cell
        in_x, in_y = int((pnt[0] - self.x_min) / size_cell), int((pnt[1] - self.y_min) / size_cell)
        return [in_x, in_y]

    # def create_grid_shapefile(self):
    #     # Create the grid layer
    #     # vector_grid = QgsVectorLayer('Polygon?crs=' + crs, 'vector_grid', 'memory')
    #     path = "test_same_area/grid.shp"
    #     if exists(path):
    #         print(path)
    #     else:
    #         print("path not exist - {}".format(path))
    #         return
    #     vector_grid = QgsVectorLayer(path, "grid", "ogr")
    #     vector_grid.dataProvider().truncate()
    #     prov = vector_grid.dataProvider()
    #
    #     # Add ids and coordinates fields
    #     if vector_grid.fields()[-1].name() != 'num_of_pnt':
    #         fields = QgsFields()
    #         fields.append(QgsField('id_east', QVariant.Int, '', 20, 0))
    #         fields.append(QgsField('id_north', QVariant.Int, '', 20, 0))
    #         fields.append(QgsField('num_of_pnt', QVariant.Int, '', 20, 0))
    #         prov.addAttributes(fields)
    #     my_id = 0
    #     for cell_row in self.data_set:
    #         for cell in cell_row:
    #             feat = QgsFeature()
    #             feat.setGeometry(
    #                 QgsGeometry().fromPolygonXY([list(cell.extent.values())]))  # Set geometry for the current id
    #             print(list(cell.extent.values()))
    #             feat.setAttributes([my_id, cell.i_e, cell.i_n, len(cell.poly)])  # Set attributes for the current id
    #             print('{},{} :{}'.format(cell.i_e, cell.i_n, len(cell.poly)))
    #             prov.addFeatures([feat])
    #             my_id += 1
    #     # Update fields for the vector grid
    #     vector_grid.updateFields()


class FindSightLine:
    def __init__(self, cur_line: QgsGeometry, cur_cell: list, end_cell: list, data_base: SameAreaCell):
        """
        It checks and builds a sight line between two points
        :param cur_cell:
        :param end_cell:
        :param data_base:
        """
        self.test_line, self.cur_cell, self.end_cell, self.data_base, self.is_sight_line = cur_line, cur_cell, end_cell, \
                                                                                           data_base, True
        # Only polygons been passed will be store it to change their status later
        self.passed_polys = []

        # If the current line intersects polygon lines, this line is not sight line
        if self.calculate_intersections():
            self.is_sight_line = False
        elif cur_cell == end_cell:
            pass
        # if the points have the same index horizontally or vertically
        elif cur_cell[0] == end_cell[0]:
            if cur_cell[1] > end_cell[1]:
                self.loop_over_horizontal_vertical_cells(1, -1)
            else:
                self.loop_over_horizontal_vertical_cells(1, 1)
        elif cur_cell[1] == end_cell[1]:
            if cur_cell[0] > end_cell[0]:
                self.loop_over_horizontal_vertical_cells(0, -1)
            else:
                self.loop_over_horizontal_vertical_cells(0, 1)
        else:
            # A pivot variable is a dictionary.
            # {pointer to the one of the cell corners:
            # [optional next cell: the examined azimuth is smaller/same/larger]}
            cur_line_0 = self.test_line.asPolyline()
            self.start_line = cur_line_0[0]
            self.azi_line = azimuth_calculator(self.start_line, cur_line_0[1])
            if 0 < self.azi_line < 90:
                self.pivot = {'NE': [(0, 1), (1, 1), (1, 0)]}
            elif 90 < self.azi_line < 180:
                self.pivot = {'SE': [(1, 0), (1, -1), (0, -1)]}
            elif 180 < self.azi_line < 270:
                self.pivot = {'SW': [(0, -1), (-1, -1), (-1, 0)]}
            else:
                self.pivot = {'NW': [(-1, 0), (-1, 1), (0, 1)]}
            self.pivot_list = list(self.pivot.values())
            self.loop_over_cell_with_pivot()

    def loop_over_horizontal_vertical_cells(self, dir_ind: int, step: int):
        """
        Loop over cells horizontally or vertically (based on  @dir_ind) from first cell to destination cell
        :param dir_ind:
        :param step forward in the grid(+1) or backward(-1)
        :return:
        """
        while not self.cur_cell == self.end_cell:
            self.cur_cell[dir_ind] += step
            if self.calculate_intersections():
                self.is_sight_line = False
                break

    def loop_over_cell_with_pivot(self):
        """
        It loops over points in the cells from the cell of the current point to the destination cell through the cells
        that are selected based on the direction in the pivot dictionary and the line azimuth.
        :return:
        """
        while self.cur_cell != self.end_cell:
            key = list(self.pivot.keys())[0]
            pivot_point = self.data_base[self.cur_cell].extent[key]
            ex_az = azimuth_calculator(self.start_line, pivot_point)

            if ex_az < self.azi_line:
                self.find_next_cell(self.pivot_list[0][2])

            elif ex_az == self.azi_line:
                self.find_next_cell(self.pivot_list[0][1])
            else:
                self.find_next_cell(self.pivot_list[0][0])
            # calculate_intersection
            if self.calculate_intersections():
                self.is_sight_line = False
                break

    def find_next_cell(self, values: tuple):
        """
        find the next cell according to the specified values
        :param values: it added to the current cell to find the next cell
        :return:
        """

        self.cur_cell[0] += values[0]
        self.cur_cell[1] += values[1]

    def calculate_intersections(self):
        """
        It goes over all the points in the current cell and search for intersection between each pair of points and the
        optional sight line
        :return:
        """
        cur_cell = self.data_base[self.cur_cell]
        for poly in cur_cell:
            if poly.is_no_passed:
                if self.test_line.crosses(poly.poly_qgs):
                    return True
                else:
                    poly.is_no_passed = False
                    self.passed_polys.append(poly)
        return False


def find_next_cell(values: tuple, ind_0):
    """
    find the next cell according to the specified values
    :param ind_0:
    :param values: it added to the current cell to find the next cell
    :return:
    """

    ind_0[0] += values[0]
    ind_0[1] += values[1]
    return ind_0


def upload_new_layer(path, name):
    """Upload shp layers"""
    layer_name = "layer" + name
    provider_name = "ogr"
    layer = QgsVectorLayer(
        path,
        layer_name,
        provider_name)
    return layer


def azimuth_calculator(pnt1: QgsPointXY, pnt2: QgsPointXY) -> float:
    """
    Calculate and return azimuth by two points
    :param pnt1:
    :param pnt2:
    :return:
    """
    azimuth = pnt1.azimuth(pnt2)
    if azimuth < 0:
        azimuth += 360
    return azimuth


class SightLineDB:
    def __init__(self, input_constrains: str, input_in: str, restricted: bool, restricted_length: int, folder: str):
        """
        The start point of the algorithm
        :param input_constrains: path to constrains shape file
        :param input_in: path to intersections shape file
        :param restricted: whether is there any restriction on the the sight line length
        :param restricted_length: if restricted is true,only  sight line shorter than that int will calculated
        :param folder: where to solve the results
        """
        # Input

        input_layers, rectangle_points = [upload_new_layer(input_in, 'file'),
                                          upload_new_layer(input_constrains, 'file')], []
        # Get  the layers' rectangle extent
        extent = ''
        for input_layer in input_layers:
            extent = input_layer.extent()
            rectangle_points.append((extent.xMaximum(), extent.yMaximum()))
            rectangle_points.append((extent.xMinimum(), extent.yMinimum()))

        # Build SameAreaCell object
        size_cell = int(extent.area() / len([feature for feature in input_layers[1].getFeatures()]) * 0.0118)

        geo_data_base = SameAreaCell(rectangle_points, size_cell)

        # if Necessary create grid. Uncomment the method
        # geo_data_base.create_grid_shapefile()

        [geo_data_base.add_polygons(feature.geometry().boundingBox(), SameAreaPoly(feature.geometry())) for feature in
         input_layers[1].getFeatures()]

        # calculate sight line
        # In this list all the new features (sight lines) will be stored
        feats, inter_pnt_list = [], [feature.geometry().asPoint() for feature in input_layers[0].getFeatures()]
        # save the cell location of each point in another array
        inter_cell_list = [(geo_data_base.find_cell(feature)) for feature in inter_pnt_list]
        # id for the lines
        line_id = 0
        for index_i, point_start in enumerate(inter_pnt_list[:-1]):
            # print(index_i)
            index_j = index_i
            for point_end in inter_pnt_list[index_i + 1:]:
                cell_first = inter_cell_list[index_i].copy()
                index_j += 1
                # if the two points are the same
                if point_start == point_end:
                    continue
                # If there is limitation on the max distance, make sure the distance is shorter than that
                if restricted and point_start.distance(point_end) > restricted_length:
                    continue
                # Call to FindSightLine class to check if sight line is exist
                cell_end, test_line = inter_cell_list[index_j], QgsGeometry.fromPolylineXY([point_start, point_end])
                find_sight_line = FindSightLine(test_line, cell_first, cell_end, geo_data_base)
                if find_sight_line.is_sight_line:
                    feat = QgsFeature()
                    feat.setGeometry(test_line)
                    feat.setAttributes([line_id, index_i, index_j])  # Set attributes for the current id
                    feats.append(feat)
                    line_id += 1
                # Set the status of polygons to be not passed
                [feature.set_is_no_passed() for feature in find_sight_line.passed_polys]

        # upload the gis file to remove old sight lines and make it ready for new sight lines
        path = join(dirname(__file__), 'sight_line')
        sight_line = QgsVectorLayer(path + '.shp', "sight_line", "ogr")
        sight_line.dataProvider().truncate()
        sight_line.dataProvider().addFeatures(feats)

        # save the results into the specified folder
        [copy('.'.join((path, file_ext)), folder) for file_ext in ('dbf', 'prj', 'shp', 'shx')]


def main():
    from qgis.core import QgsApplication

    # Start new Qgis application
    app = QGuiApplication([])
    QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    QgsApplication.initQgis()

    SightLineDB('test_same_area/building_1.shp', 'test_same_area/sight_node.shp', True, 1000, 'test_same_area')

    # create line for other points in the list
    """For standalone application"""
    # Exit applications
    QgsApplication.exitQgis()
    app.exit()


if __name__ == "__main__":
    import cProfile, pstats
    from os import unlink, path

    # delete old sight line file
    file_path = 'test_same_area/sight_line'
    for file_ext in ('dbf', 'prj', 'shp', 'shx'):
        file_path_ext = '.'.join((file_path, file_ext))
        if path.isfile(file_path_ext):
            unlink(file_path_ext)

    profiler = cProfile.Profile()
    profiler.enable()
    main()
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('time')
    stats.print_stats()
