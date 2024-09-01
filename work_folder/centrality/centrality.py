import logging
from qgis.PyQt.QtCore import QVariant
import networkx as nx
from qgis.core import (
    QgsVectorLayer,
    QgsField
)


class CentralityGraph:
    """
    This class calculates three centrality indices (Closeness, Degree, and Betweenness) based on the networkx library.
    """

    def __init__(self, file_path: str):
        """
        :param file_path: The directory in which the sight lines and sight points files are located.
        """
        self.graph = nx.Graph()
        self.lines_layer, self.points_layer = self.from_shp_to_graph(file_path)

        # Calculate centralities
        self.calculate_centralities()

        # Update shapefiles with centrality measures
        self.update_centrality_into_shp()

    def from_shp_to_graph(self, file_path: str):
        """
        Loads point and line shapefiles from the specified file path and constructs a graph
        using NetworkX. Points from the shapefile are added as nodes, and lines are added
        as edges between the nodes in the graph.

        Parameters:
        -----------
        file_path : str
            The file path to the directory containing the 'sight_node.shp' and 'sight_line.shp' shapefiles.

        Returns:
        --------
        lines_layer, points_layer : QgsVectorLayer
            The QGIS vector layers representing lines and points, respectively.
        """
        points_layer = QgsVectorLayer(f'{file_path}/sight_node.shp', 'sight_node', 'ogr')
        lines_layer = QgsVectorLayer(f'{file_path}/sight_line.shp', 'sight_line', 'ogr')

        # Add nodes from points layer
        self.graph.add_nodes_from(
            (tuple(feature.geometry().asPoint()), {}) for feature in points_layer.getFeatures()
        )

        # Add edges from lines layer
        for feature in lines_layer.getFeatures():
            geom = feature.geometry()
            coords = geom.asMultiPolyline()[0] if geom.isMultipart() else geom.asPolyline()
            line_id = feature['id']

            self.graph.add_edges_from(
                (tuple(coords[i]), tuple(coords[i + 1]), {'line_id': line_id})
                for i in range(len(coords) - 1)
            )

        self._prepare_layers(points_layer, lines_layer)
        return lines_layer, points_layer

    def _prepare_layers(self, points_layer, lines_layer):
        """
        Prepares the layers by starting an editing session and adding necessary fields.
        """
        points_layer.startEditing()
        lines_layer.startEditing()

        points_layer.dataProvider().addAttributes([
            QgsField('degree', QVariant.Double),
            QgsField('between', QVariant.Double),
            QgsField('closeness', QVariant.Double)
        ])

        lines_layer.dataProvider().addAttributes([
            QgsField('edge_btw', QVariant.Double)
        ])

        points_layer.updateFields()
        lines_layer.updateFields()

    def calculate_centralities(self):
        """
        Calculate centralities (degree, betweenness, closeness) for nodes and edges.
        """
        print('Calculating centralities...')
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        closeness_centrality = nx.closeness_centrality(self.graph)
        edge_betweenness_centrality = nx.edge_betweenness_centrality(self.graph)

        nx.set_node_attributes(self.graph, degree_centrality, 'degree')
        nx.set_node_attributes(self.graph, betweenness_centrality, 'between')
        nx.set_node_attributes(self.graph, closeness_centrality, 'closeness')
        nx.set_edge_attributes(self.graph, edge_betweenness_centrality, 'between')

    def update_centrality_into_shp(self):
        """
        Updates the shapefiles of line and point layers with centrality measures.
        """
        print('Updating shapefiles...')

        lines_layer = self.lines_layer
        points_layer = self.points_layer

        attr_line = [self.graph.edges[edge]['between'] for edge in self.graph.edges()]
        attributes = {
            i: (
                self.graph.nodes[node]['degree'],
                self.graph.nodes[node]['between'],
                self.graph.nodes[node]['closeness']
            )
            for i, node in enumerate(self.graph.nodes())
        }

        lines_layer.startEditing()
        for i, feature in enumerate(lines_layer.getFeatures()):
            feature['edge_btw'] = attr_line[i]
            lines_layer.updateFeature(feature)
        lines_layer.commitChanges()

        points_layer.startEditing()
        for i, feature in enumerate(points_layer.getFeatures()):
            feature['degree'], feature['between'], feature['closeness'] = attributes[i]
            points_layer.updateFeature(feature)
        points_layer.commitChanges()

    @staticmethod
    def write_to_log(file_path):
        logger = logging.getLogger('my_logger')
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(
            r'C:\Users\...\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\poi_visibility_network\work_folder\centrality\my_log_file.log'
        )
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info('Custom message: %s', file_path)


if __name__ == '__main__':
    CentralityGraph(
        r'C:\Users\18059\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\poi_visibility_network\results'
    )
