import os
import sys

from qgis.core import (QgsProcessingContext,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingFeedback,
                       QgsVectorLayer,
                       Qgis)

# Tell Python where you will get processing from
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.16\apps\qgis-ltr\python\plugins')


# Reference the algorithm you want to run
from plugins import processing
# Reference the algorithm you want to run

from plugins.processing.algs.qgis.HubDistanceLines import HubDistanceLines
import time


class MergePoint:
    def __init__(self, poi_path, graph_type=0):
        '''

        :param graph_type:
        :param poi_path: which poi file work with
        '''

        feedback = QgsProcessingFeedback()

        # The next variables are needed for more then one tool
        overlay = os.path.join(os.path.split(os.path.dirname(__file__))[0], r'general\constrains.shp')
        output_clip = os.path.join(os.path.dirname(__file__), r'results_file/cliped.shp')
        output__along_geometry = os.path.join(os.path.dirname(__file__), r'results_file\points_along.shp')
        self.stat = dict()
        # this parameter is in order to perform different algorithms according the QGIS version
        inty = int(Qgis.QGIS_VERSION.split('-')[0].split('.')[1])
        # Clip to project only POI in polygons
        processing.run('native:extractbylocation', {'INPUT': poi_path, 'PREDICATE': [0],
                                                    'INTERSECT': overlay, 'OUTPUT': output_clip}, feedback=feedback)

        ######### Create shp file with POI not inside polygons
        processing.run('native:extractbylocation', {'INPUT': poi_path, 'PREDICATE': [2], 'INTERSECT': os.path.join(
            os.path.split(os.path.dirname(__file__))[0], r'general\constrains.shp'), 'OUTPUT': os.path.join(
            os.path.dirname(__file__), r'results_file\extracted.shp')}, feedback=feedback)
        ######### Point along geometry of network file
        params = {'INPUT': os.path.join(os.path.split(os.path.dirname(__file__))[0], r'general\networks.shp'),
                  'DISTANCE': 5, 'START_OFFSET': 0, 'END_OFFSET': 0,
                  'OUTPUT': output__along_geometry}
        # different implementation among QGIS versions
        if inty < 10:
            from plugins.processing.algs.qgis.PointsAlongGeometry import PointsAlongGeometry
            alg = PointsAlongGeometry()
            alg.initAlgorithm()
            context = QgsProcessingContext()
            alg.processAlgorithm(params, context, feedback=feedback)
        else:
            processing.run('native:pointsalonglines', params, feedback=feedback)

        ##########Create line that connect between each POI to nearest points along roads
        input_path = output_clip
        input_clip = self.upload_new_layer(input_path, "input")
        hubs_path = output__along_geometry
        output_hub_dis_line = os.path.join(os.path.dirname(__file__), r'results_file/line_to_points.shp')

        alg = HubDistanceLines()
        alg.initAlgorithm()
        # Some preprocessing for context
        project = QgsProject.instance()

        target_crs = QgsCoordinateReferenceSystem()
        target_crs.createFromOgcWmsCrs(input_clip.crs().authid())
        project.setCrs(target_crs)
        context = QgsProcessingContext()
        context.setProject(project)
        params = {'INPUT': input_path, 'HUBS': hubs_path, 'FIELD': 'angle', 'UNIT': 4, 'OUTPUT': output_hub_dis_line}
        alg.processAlgorithm(params, context, feedback=feedback)

        ########## Buffer over constrain layer
        constrains = overlay
        buffer = os.path.join(os.path.dirname(__file__), "results_file/buffer.shp")

        params = {'INPUT': constrains, 'DISTANCE': 1, 'SEGMENTS': 1, 'END_CAP_STYLE': 2,
                  'JOIN_STYLE': 1, 'MITER_LIMIT': 2,
                  'DISSOLVE': True, 'OUTPUT': buffer}

        processing.run('native:buffer', params, feedback=feedback)

        ##########Convrt constrains layer as polylines
        constrains = buffer
        output_poly_as_lines = os.path.join(os.path.dirname(__file__), r'results_file/poly_as_lines.shp')
        params = {'INPUT': constrains, 'OUTPUT': output_poly_as_lines}
        # different implementation among QGIS versions
        if inty < 10:
            from plugins.processing.algs.qgis.PolygonsToLines import PolygonsToLines
            alg = PolygonsToLines()
            alg.initAlgorithm()
            alg.processAlgorithm(params, context, feedback=feedback)
        else:
            processing.run("native:polygonstolines", params)
        ##########Find intersction points between hub distance lines to the constrains as polylines
        input_path = output_hub_dis_line
        input_hub_dis = self.upload_new_layer(input_path, "input")
        intersect = self.upload_new_layer(output_poly_as_lines, "intersect")
        output = os.path.join(os.path.dirname(__file__), r'results_file\off_pnts.shp')
        params = {'INPUT': input_hub_dis, 'INTERSECT': intersect, 'INPUT_FIELDS': [],
                  'INTERSECT_FIELDS': [], 'OUTPUT': output}
        processing.run('native:lineintersections', params, feedback=feedback)

        ##########Merge all points to one layer
        layer_1 = os.path.join(os.path.dirname(__file__), r'results_file\off_pnts.shp')
        layer_2 = os.path.join(os.path.dirname(__file__), r'results_file\extracted.shp')

        merge_layers = [layer_1, layer_2]
        # Merge also intersection points in case of all
        if graph_type:
            merge_layers.append(os.path.join(os.path.split(os.path.dirname(__file__))[0]
                                             , r'mean_close_point\results_file\final.shp'))
        OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\merge.shp')
        params = {'LAYERS': merge_layers, 'CRS': 'EPSG:3857', 'OUTPUT': OUTPUT}

        processing.run('native:mergevectorlayers', params, feedback=feedback)

        ##########Delete duplicate geomeyry
        input = OUTPUT
        OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\final.shp')
        params = {'INPUT': input, 'OUTPUT': OUTPUT}
        if inty < 16:
            from plugins.processing.algs.qgis.DeleteDuplicateGeometries import DeleteDuplicateGeometries
            alg = DeleteDuplicateGeometries()
            alg.initAlgorithm()
            alg.processAlgorithm(params, context, feedback=feedback)
        else:
            processing.run("native:deleteduplicategeometries", params, feedback=feedback)

    def upload_new_layer(self, path, name):
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
