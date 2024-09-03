import os
import sys

from PyQt5.QtGui import *
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

from .Qtree import *

# Tell Python where you will get processing from
# sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.16\apps\qgis-ltr\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.22.3\apps\qgis\python\plugins')

from qgis.PyQt.QtCore import QVariant
from plugins import processing


class myQGIS:
    """This class handles part of the logic about Qgis objects ."""

    def __init__(self, path_shp, name):
        # Initiate QgsApplication in case of standalone app
        self.feedback = QgsProcessingFeedback()
        self.shp = self.upload_new_layer(path_shp, name)
        # This variable is to run built tools
        self.shp_path = path_shp

        # Build Qtree object
        my_tree = QTree(10)
        my_tree = self.from_qgis_to_Qtree_list(my_tree)

        # Dimension for Qtree
        x0 = min(my_tree.points, key=lambda x: x.x).x
        y0 = min(my_tree.points, key=lambda x: x.y).y
        x1 = max(my_tree.points, key=lambda x: x.x).x
        y1 = max(my_tree.points, key=lambda x: x.y).y
        w = x1 - x0
        h = y1 - y0
        my_tree.add_root(x0, y0, w, h)
        # print(str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1))
        # Build the graph
        my_tree.subdivide()
        # Add new field to the network based on which it would be dissolved
        self.add_new_field_and_papulate_it(my_tree.line, "group", QVariant.LongLong)
        # Dissolve the network
        file_path = os.path.join(os.path.dirname(__file__), r'results_file\dissolve_0.shp')
        self.dissolve("group", file_path)

    def from_qgis_to_Qtree_list(self, qtree):
        """:self.shp to convert
        @:param self.shp to convert to point list that part of Qtree that store the source line Id
        @:param  qtree to populate with points"""
        lines_features = self.shp.getFeatures()
        # Read geometry from shpfile to point list and store the source line id
        for i, feature in enumerate(lines_features):
            qtree.line.append(i)
            try:

                index_to_end = len(feature.geometry().asMultiPolyline()[0]) - 1
                qtree.add_point(feature.geometry().asMultiPolyline()[0][0][0],
                                feature.geometry().asMultiPolyline()[0][0][1], i)
                qtree.add_point(feature.geometry().asMultiPolyline()[0][index_to_end][0],
                                feature.geometry().asMultiPolyline()[0][index_to_end][1], i)
            except TypeError:
                continue
        return qtree

    def upload_new_layer(self, path, name):
        """Upload shp layers"""
        layer_name = ''.join(("layer", name))
        provider_name = "ogr"
        layer = QgsVectorLayer(
            path,
            layer_name,
            provider_name)
        if not layer:
            return ("Layer failed to load!-" + path)
        return layer

    def add_new_field_and_papulate_it(self, python_list, field_name, field_type):
        """@:param python_list with tha data to add"""
        if self.shp.fields()[len(self.shp.fields()) - 1].name() != field_name:
            self.shp.dataProvider().addAttributes([QgsField(field_name, field_type)])
            self.shp.updateFields()
        n = len(self.shp.fields())
        for i, feature in enumerate(self.shp.getFeatures()):
            self.shp.dataProvider().changeAttributeValues({i: {n - 1: python_list[i]}})

    def dissolve(self, field_name, output):
        """Dissolve shp by field name and store it in output"""
        try:
            params = {'INPUT': self.shp_path, 'FIELD': [field_name], 'OUTPUT': output}
            # return processing.run('native:dissolve', params, feedback=self.feedback)
            processing.run('native:dissolve', params, feedback=self.feedback)
            print(" dissolve works")
        except:
            print(" NO dissolve ")
        return False

# if __name__ == "__main__":
#     # Create Qgis object and convert lines shp to python list
#     print("start")
#     lines = os.path.dirname(__file__) + r'\processing\highways_1.shp'
#     linesQgis = myQGIS("standalone", lines, "_lines")
#
#     # Build Qtree object
#     my_tree = QTree(10)
#     my_tree = linesQgis.from_qgis_to_Qtree_list(my_tree)
#
#     # Dimension for Qtree
#     x0 = min(my_tree.points, key=lambda x: x.x).x
#     y0 = min(my_tree.points, key=lambda x: x.y).y
#     x1 = max(my_tree.points, key=lambda x: x.x).x
#     y1 = max(my_tree.points, key=lambda x: x.y).y
#     w = x1 - x0
#     h = y1 - y0
#     my_tree.add_root(x0, y0, w, h)
#     # print(str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1))
#     # Build the graph
#     my_tree.subdivide()
#     # Add new field to the network based on which it would be dissolved
#     linesQgis.add_new_field_and_papulate_it(my_tree.line, "group", QVariant.LongLong)
#     # Dissolve the network
#     dissolve_shp = linesQgis.dissolve("group", os.path.dirname(__file__) + r'/processing/dissolve_0.shp')
#
#     # for i, gg in enumerate(my_tree.line):
#     #     print(str(i) + "," + str(gg))
