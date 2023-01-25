# Prepare the environment

import json
import math as mt
import os
from os.path import join
import sys

from PyQt5.QtGui import *
from qgis.PyQt.QtCore import QVariant
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

# Tell Python where you will get processing from
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.16\apps\qgis-ltr\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.22.3\apps\qgis\python\plugins')
# Reference the algorithm you want to run
from plugins import processing

inty = int(Qgis.QGIS_VERSION.split('-')[0].split('.')[1])
if inty < 16:
    from plugins.processing.algs.qgis.DeleteDuplicateGeometries import *
    from plugins.processing.algs.qgis.ExtractSpecificVertices import *


def find_dead_end(lines: str, feedback):
    """
    This method finds dead end points by performing three tasks. It first finds the intersections, then gets the first and
    last vertex of each line, and then extracts the points in task 1 from the points in task 2.
    :param lines is the path for the shp file on which to find dead ends
    :param feedback
    """
    input_output = os.path.dirname(__file__) + '/work_folder/general/dead_end_int.shp'
    local_output = os.path.dirname(__file__) + '/work_folder/general/dead_end_str_end.shp'
    final_output = os.path.dirname(__file__) + '/work_folder/general/dead_end.shp'

    processing.run("native:lineintersections", {
        'INPUT': lines,
        'INTERSECT': lines,
        'INPUT_FIELDS': [], 'INTERSECT_FIELDS': [], 'INTERSECT_FIELDS_PREFIX': '', 'OUTPUT': input_output})
    params = {'INPUT': lines, 'VERTICES': '0,-1', 'OUTPUT': local_output}
    if inty < 16:
        alg = ExtractSpecificVertices()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        alg.processAlgorithm(params, context, feedback=feedback)
    else:
        processing.run("native:extractspecificvertices", params)

    processing.run("native:extractbylocation", {
        'INPUT': local_output,
        'PREDICATE': [2],
        'INTERSECT': input_output,
        'OUTPUT': final_output})


def upload_new_layer(path, name):
    """Upload shp layers"""
    layer_name = "layer" + name
    provider_name = "ogr"
    layer = QgsVectorLayer(
        path,
        layer_name,
        provider_name)
    if not layer:
        print("Layer failed to load!-" + path)
    return layer


class SightLine:
    """This class handles all the logic about the  sight lines."""

    def __init__(self, network=None, constrains=None, res_folder=None, project=None):
        """ Constrictor
         :param network to find intersections
         :param constrains the optional sight lines
         :param res_folder storing the results
         :param project loading the layers into
         :param use to identify who call that class -  plugin or standalone """
        # Initiate QgsApplication
        self.junc_loc = os.path.dirname(__file__) + r'\work_folder\general\intersections.shp'
        self.network_st = join(os.path.dirname(__file__),
                               r'work_folder\fix_geometry\results_file\dissolve_0.shp')
        self.junc_loc_0 = os.path.dirname(__file__) + r'\work_folder\general\intersections_0.shp'

        # These attributes are input from the user
        if network is not None:
            self.network = upload_new_layer(network, "_network")
        self.constrain = upload_new_layer(constrains, "_constrain")
        self.feedback = QgsProcessingFeedback()
        self.res_folder = res_folder

        # These will be used latter
        self.res = []

        # layers[0] = intersections
        # layers[1] =  edges
        self.layers = []
        self.layers.append("intersections")
        self.layers.append("edges")
        # attributes to create QgsVectorLayer in memory
        self.vl = QgsVectorLayer()
        # QgsVectorDataProvider
        self.lines = None
        # QgsProject.instance()
        self.project = project

    @staticmethod
    def reproject(layers_to_project_path, target_crs='EPSG:3857', relative_folder='work_folder/general/'):
        '''
        :param layers_to_project_path: list of layer to project
        :param target_crs: to project
        :param names_list: new name for the projected layers
        :param relative_folder: to save the new files
        :return:
        '''
        """Reproject all input layers to 3857 CRS (default - 3857)"""
        names_list = ['constrains', 'pois', 'networks']
        for i, layer in enumerate(layers_to_project_path):
            if not (layer is None):
                # the name for the new reproject file
                output = join(os.path.dirname(__file__), relative_folder, names_list[i] + '.shp')
                params = {'INPUT': layer, 'TARGET_CRS': target_crs, 'OUTPUT': output}
                feedback = QgsProcessingFeedback()
                processing.run("native:reprojectlayer", params, feedback=feedback)

    @staticmethod
    def centerlized():
        """Reproject all input layers to 3857 CRS"""

        input = os.path.dirname(__file__) + r'/work_folder/general/pois.shp'
        output = os.path.dirname(__file__) + r'/work_folder/general/pois1.shp'
        feedback = QgsProcessingFeedback()
        params = {
            'INPUT': input,
            'OUTPUT': output}
        processing.run("native:centroids", params, feedback=feedback)
        return output

    def intersections_points(self):
        """Upload input data"""
        # Find intersections points
        params = {'INPUT': self.network_st, 'INTERSECT': self.network_st, 'INPUT_FIELDS': [],
                  'INTERSECT_FIELDS': [],
                  'OUTPUT': self.junc_loc_0}

        self.res = processing.run('native:lineintersections', params, feedback=self.feedback)

    def delete_duplicate_geometries(self):
        """Delete duplicate geometries in intesections_0 layer"""
        try:
            local_input = self.junc_loc_0
            local_output = os.path.dirname(__file__) + r'\work_folder\general\intersections_1.shp'
            params = {'INPUT': local_input,
                      'OUTPUT': local_output}
            if inty < 16:
                alg = DeleteDuplicateGeometries()
                alg.initAlgorithm()
                context = QgsProcessingContext()
                self.res = alg.processAlgorithm(params, context, feedback=self.feedback)
            else:
                processing.run("native:deleteduplicategeometries", params, feedback=self.feedback)
            print("delete_duplicate_geometries is success")
        except QgsProcessingException:
            pass

    def turning_points(self):

        # input data
        line_path = os.path.dirname(__file__) + r'/work_folder/fix_geometry/results_file/dissolve_0.shp'
        single_part = os.path.dirname(__file__) + r'/work_folder/general/single_part.shp'

        # populate turning points layer with new points
        layer_path = os.path.dirname(__file__) + r'/work_folder/turning_points.shp'
        layer = upload_new_layer(layer_path, "layer")
        layer.dataProvider().truncate()

        # to single parts
        params = {'INPUT': line_path, 'OUTPUT': single_part}
        feedback = QgsProcessingFeedback()
        processing.run('native:multiparttosingleparts', params, feedback=feedback)

        # split with lines
        split_with_lines = os.path.dirname(__file__) + r'/splitwithlines.shp'
        processing.run("native:splitwithlines", {'INPUT': single_part,
                                                 'LINES': single_part,
                                                 'OUTPUT': split_with_lines})
        lines = upload_new_layer(split_with_lines, "lines")
        temp_list = []

        # calculate azimuth and save points with azimuth larger than 30 degrees
        for feature in lines.getFeatures():
            feature_list = feature.geometry().asJson()
            json1_data = json.loads(feature_list)['coordinates']
            for cor_set in json1_data:
                for i in range(0, len(cor_set) - 2):
                    # calc slope as  an angle
                    x1 = cor_set[i][0]
                    y1 = cor_set[i][1]
                    x2 = cor_set[i + 1][0]
                    y2 = cor_set[i + 1][1]
                    x3 = cor_set[i + 2][0]
                    y3 = cor_set[i + 2][1]
                    angle1 = mt.atan2(x2 - x1, y2 - y1) * 180 / mt.pi
                    angle2 = mt.atan2(x3 - x2, y3 - y2) * 180 / mt.pi
                    # calc angle between two lines
                    angleB = 180 - angle1 + angle2
                    if angleB < 0:
                        angleB = angleB + 360
                    if angleB > 360:
                        angleB = angleB - 360
                    if abs(angleB - 180) > 30:
                        feat = QgsFeature()
                        my_point = QgsPointXY(x2, y2)
                        g_pnt = QgsGeometry.fromPointXY(my_point)
                        feat.setGeometry(g_pnt)
                        temp_list.append(feat)

        layer.dataProvider().addFeatures(temp_list)
        # Find dead ends points
        find_dead_end(split_with_lines,self.feedback)
        # Merge all points to one layer
        layer_2 = os.path.dirname(__file__) + r'\work_folder\general\intersections_1.shp'
        layer_3 = os.path.dirname(__file__) + '/work_folder/general/dead_end.shp'
        merge_layers = [layer_path, layer_2, layer_3]
        # Merge also intersection points in case of all
        params = {'LAYERS': merge_layers, 'CRS': 'EPSG:3857', 'OUTPUT': self.junc_loc}

        processing.run('native:mergevectorlayers', params, feedback=feedback)

    def create_gdf_file(self, weight, graph_name, is_sight_line: int):
        """
        :param weight: 0 all sight lines with same weight 1 all sight lines with weight based on their length
        :param graph_name: for the name of the generated gdf file
        :param is_sight_line: 1 or 2 - there is sight line 3- no sight line layer
        :return:
        """
        """create gdf file"""

        # Open text file as gdf file
        file_path = join(self.res_folder, graph_name + '.gdf')
        file1 = open(file_path, "w")
        # Write intersection nodes to file
        title = "nodedef>name VARCHAR,x DOUBLE,y DOUBLE,size DOUBLE,type VARCHAR"
        file1.write(title)
        nodes_features = self.layers[0].getFeatures()
        # lambda x: x.geometry(), nodes_features
        for i, feature in enumerate(nodes_features):
            file1.write('\n')
            file1.write('"' + str(feature['point_id']) + '"' + ',' + '"' +
                        str(feature.geometry().asPoint()[0]) + '"' + ',' + '"' + str(
                feature.geometry().asPoint()[1]) + '"' +
                        ',' + '"10"' + ',' + '"' + str(feature['poi_type']) + '"')

        # Write sight edges to file
        if is_sight_line != 3:
            # Add new fields to layer (length and weight)
            if self.layers[1].fields()[len(self.layers[1].fields()) - 2].name() != "length":
                self.layers[1].dataProvider().addAttributes([QgsField("length", QVariant.Double)])
                self.layers[1].updateFields()

            if self.layers[1].fields()[len(self.layers[1].fields()) - 1].name() != "weight":
                self.layers[1].dataProvider().addAttributes([QgsField("weight", QVariant.Double)])
                self.layers[1].updateFields()

            # Populate weight data
            n = len(self.layers[1].fields())
            i = 0
            for f in self.layers[1].getFeatures():
                geom_length = f.geometry().length()
                self.layers[1].dataProvider().changeAttributeValues({i: {n - 2: geom_length}})
                if weight:
                    self.weight_calculation(i, n, 1 / mt.pow(geom_length, 2) * 10000)
                    i = i + 1
                else:
                    self.weight_calculation(i, n, 1)
                    i = i + 1

            # Write title
            file1.write("\nedgedef>node1 VARCHAR,node2 VARCHAR,weight DOUBLE\n")
            edges_features = self.layers[1].getFeatures()

            # Write
            for feature in edges_features:
                file1.write("{},{},{}\n".format(feature['from'], feature['to'], feature['weight']))
        file1.close()

    def weight_calculation(self, i, n, weight):
        self.layers[1].dataProvider().changeAttributeValues({i: {n - 1: weight}})

    def create_new_layer(self, selected_crs, vector_type):
        """Create new shp layers"""

        # Define coordinate system
        target_crs = QgsCoordinateReferenceSystem()
        target_crs.createFromOgcWmsCrs(selected_crs)
        fields = QgsFields()
        fields.append(QgsField("from", QVariant.Int))
        fields.append(QgsField("to", QVariant.Int))
        writer = QgsVectorFileWriter("new_lines5", "system", fields, vector_type, target_crs)
        if writer.hasError() != QgsVectorFileWriter.NoError:
            print("Error when creating shapefile: ", writer.errorMessage())

        # delete the writer to flush features to disk
        del writer
        path = os.path.dirname(__file__) + r'/new_lines4.shp'

        return upload_new_layer(path, "pot_lines")

    def copy_shape_file_to_result_file(self, src, trg_name):
        """
        :param src: folder to copy shp file from
        :param trg_name: name for the new shp file, the file will save in the result folders ( a variable of this class
        """
        from shutil import copyfile
        src = src[:-4]
        dst = join(self.res_folder, trg_name)
        for ext in ['.shp', '.dbf', '.prj', '.shx']:
            copyfile(src + ext, dst + ext)

    def add_layers_to_pro(self, layer_array):
        """Adding layers to project"""
        self.project.addMapLayers(layer_array)


if __name__ == "__main__":
    from qgis.core import QgsApplication

    # Start new Qgis application
    app = QGuiApplication([])
    QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    QgsApplication.initQgis()

    split_with_lines = os.path.dirname(__file__) + r'/splitwithlines.shp'
    find_dead_end(split_with_lines)
    # create line for other points in the list
    """For standalone application"""
    # Exit applications
    QgsApplication.exitQgis()
    app.exit()
