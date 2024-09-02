import sys

from PyQt5.QtGui import *
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

# Tell Python where you will get processing from


# sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.16\apps\qgis-ltr\python\plugins')
# sys.path.append(r'C:\Program Files\QGIS 3.22.3\apps\qgis\python\plugins')
# Reference the algorithm you want to run
from plugins import processing

from plugins.processing.algs.qgis.PointDistance import *
inty = int(Qgis.QGIS_VERSION.split('-')[0].split('.')[1])
if inty < 16:
    from plugins.processing.algs.qgis.DeleteDuplicateGeometries import *

# This 2 following defs intend to calculate distance matrix with point to herself

def linearMatrix(self, parameters, context, source, inField, target_source, targetField,
                 nPoints, feedback):
    inIdx = source.fields().lookupField(inField)
    outIdx = target_source.fields().lookupField(targetField)

    fields = QgsFields()
    input_id_field = source.fields()[inIdx]
    input_id_field.setName('InputID')
    fields.append(input_id_field)

    target_id_field = target_source.fields()[outIdx]
    target_id_field.setName('TargetID')
    fields.append(target_id_field)
    fields.append(QgsField('Distance', QVariant.Double))

    out_wkb = QgsWkbTypes.multiType(source.wkbType())
    (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                           fields, out_wkb, source.sourceCrs())

    index = QgsSpatialIndex(target_source.getFeatures(
        QgsFeatureRequest().setSubsetOfAttributes([]).setDestinationCrs(source.sourceCrs(),
                                                                        context.transformContext())), feedback)

    dist_area = QgsDistanceArea()
    dist_area.setSourceCrs(source.sourceCrs(), context.transformContext())
    dist_area.setEllipsoid(context.project().ellipsoid())

    features = source.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([inIdx]))
    total = 100.0 / source.featureCount() if source.featureCount() else 0
    for current, inFeat in enumerate(features):
        if feedback.isCanceled():
            break

        in_geom = inFeat.geometry()
        in_id = str(inFeat.attributes()[inIdx])
        feat_list = index.nearestNeighbor(in_geom.asPoint(), nPoints)
        request = QgsFeatureRequest().setFilterFids(feat_list).setSubsetOfAttributes([outIdx]).setDestinationCrs(
            source.sourceCrs(), context.transformContext())
        for outFeat in target_source.getFeatures(request):
            if feedback.isCanceled():
                break

            out_id = outFeat.attributes()[outIdx]
            out_geom = outFeat.geometry()
            dist = dist_area.measureLine(in_geom.asPoint(),
                                         out_geom.asPoint())

            out_feature = QgsFeature()
            out_geom = QgsGeometry.unaryUnion([inFeat.geometry(), outFeat.geometry()])
            out_feature.setGeometry(out_geom)
            out_feature.setAttributes([in_id, out_id, dist])
            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

        feedback.setProgress(int(current * total))

    return {self.OUTPUT: dest_id}


def processAlgorithm(self, parameters, context, feedback):
    source = self.parameterAsSource(parameters, self.INPUT, context)
    source_field = self.parameterAsString(parameters, self.INPUT_FIELD, context)
    target_source = self.parameterAsSource(parameters, self.TARGET, context)
    target_field = self.parameterAsString(parameters, self.TARGET_FIELD, context)
    n_points = self.parameterAsInt(parameters, self.NEAREST_POINTS, context)

    if n_points < 1:
        n_points = target_source.featureCount()

    # Linear distance matrix
    return linearMatrix(self, parameters, context, source, source_field, target_source, target_field,
                        n_points, feedback)


class MeanClosePoint:
    def __init__(self, distance_to_aggregate):
        feedback = QgsProcessingFeedback()

        """implement add ID"""

        junc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), r'general/intersections.shp')
        junc = self.upload_new_layer(junc_path, "junc")
        if junc.fields()[len(junc.fields()) - 1].name() != "vis_id":
            junc.dataProvider().addAttributes([QgsField("vis_id", QVariant.Int)])
            junc.updateFields()
        n = len(junc.fields())
        for i, feature in enumerate(junc.getFeatures()):
            junc.dataProvider().changeAttributeValues({i: {n - 1: i}})

        """ implement distance matrix"""
        my_input = os.path.join(os.path.dirname(os.path.dirname(__file__)), r'general\intersections.shp')

        input_field = 'vis_id'
        target = os.path.join(os.path.dirname(os.path.dirname(__file__)), r'general\intersections.shp')
        target_field = 'vis_id'
        output = os.path.join(os.path.dirname(__file__), r'results_file\distance_matrix.shp')
        params = {'INPUT': my_input, 'INPUT_FIELD': input_field, 'TARGET': target, 'TARGET_FIELD': target_field,
                  'OUTPUT': output,
                  'MATRIX_TYPE': 0, 'NEAREST_POINTS': 10, 'OUTPUT': output}

        alg = PointDistance()
        alg.initAlgorithm()

        # Some postprocessing for context
        project = QgsProject.instance()

        target_crs = QgsCoordinateReferenceSystem()
        layer_1 = self.upload_new_layer(my_input, "intersections")
        target_crs.createFromOgcWmsCrs(layer_1.crs().authid())
        project.setCrs(target_crs)
        context = QgsProcessingContext()
        context.setProject(project)
        processAlgorithm(alg, params, context, feedback=feedback)

        """ implement extract"""

        my_input = os.path.join(os.path.dirname(__file__), r'results_file\distance_matrix.shp')
        output = os.path.join(os.path.dirname(__file__), r'results_file\extracted.shp')
        params = {'INPUT': my_input, 'FIELD': 'Distance', 'OPERATOR': 4, 'VALUE': distance_to_aggregate,
                  'OUTPUT': output}

        processing.run('native:extractbyattribute', params, feedback=feedback)

        """ implement Multipart to singleparts"""

        my_input = os.path.join(os.path.dirname(__file__), r'results_file\extracted.shp')
        output = os.path.join(os.path.dirname(__file__), r'results_file\single_part.shp')
        params = {'INPUT': my_input, 'OUTPUT': output}

        processing.run('native:multiparttosingleparts', params, feedback=feedback)

        """ implement Delete duplicate geometries"""

        my_input = os.path.join(os.path.dirname(__file__), r'results_file\single_part.shp')

        output = os.path.join(os.path.dirname(__file__), r'results_file\cleaned.shp')
        params = {'INPUT': my_input, 'OUTPUT': output}
        if inty < 16:
            alg = DeleteDuplicateGeometries()
            alg.initAlgorithm()
            context = QgsProcessingContext()
            alg.processAlgorithm(params, context, feedback=feedback)
        else:
            processing.run("native:deleteduplicategeometries", params,feedback=feedback)

        """ implement Mean coordinates"""

        my_input = self.upload_new_layer(
            os.path.join(os.path.dirname(__file__), r'results_file\cleaned.shp'), 'cleaned')
        output = os.path.join(os.path.dirname(__file__), r'results_file\final.shp')
        params = {'INPUT': my_input, 'UID': 'InputID', 'OUTPUT': output}

        processing.run('native:meancoordinates', params, feedback=feedback)

        """For standalone application"""


    def upload_new_layer(self, path, name):
        """Upload shp layers"""
        layer_name = "layer" + name
        provider_name = "ogr"
        layer = QgsVectorLayer(
            path,
            layer_name,
            provider_name)
        if not layer:
            return "Layer failed to load!-" + path
        return layer
