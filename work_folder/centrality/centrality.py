import networkx as nx
from shutil import copy
from os.path import join
from os import replace


class CentralityGraph:
    """
    This class calculates three centrality indices (Closeness, Degree, and Betweenness) based on the networkx library.
    """

    def __init__(self, file_path: str, change_all_name: bool):
        """
        :param file_path: The directory in which the sight lines and sight points files are located.
        :param change_all_name: A flag to control whether node file names should be changed
        """

        self.graph = nx.Graph(nx.readwrite.nx_shp.read_shp(file_path).to_undirected())
        self.change_all_name = change_all_name
        self.degree()
        self.betweenness()
        self.edge_betweenness()
        self.closeness()
        if change_all_name:
            self.to_shp(location=file_path, extensions=['shp', 'shx', 'dbf'],
                        new_old=[('edges', 'sight_line'), ('nodes', 'sight_node')])
        else:
            self.to_shp(location=file_path, extensions=['shp', 'shx', 'dbf'],
                        new_old=[('edges', 'sight_line')])

    def degree(self):
        """
        Compute the degree centrality for nodes.
        """
        print('degree')
        node_degree = nx.degree_centrality(self.graph)
        nx.set_node_attributes(self.graph, node_degree, 'degree')

    def betweenness(self):
        """
        Compute the degree centrality for nodes.
        """
        print('betweenness')
        node_degree = nx.betweenness_centrality(self.graph)
        nx.set_node_attributes(self.graph, node_degree, 'betwenes')

    def edge_betweenness(self):
        """
        Compute the degree centrality for nodes.
        """
        print('edge_betweenness')

        edge_betweenness = nx.edge_betweenness_centrality(self.graph)
        nx.set_edge_attributes(self.graph, edge_betweenness, 'betwenes')
        # self.graph = nx.MultiGraph(self.graph)

    def closeness(self):
        """
        Compute the degree centrality for nodes.
        """
        print('closeness')
        node_closeness = nx.closeness_centrality(self.graph)
        nx.set_node_attributes(self.graph, node_closeness, 'closeness')

    def to_shp(self, location, extensions: list, new_old: list):
        """
        It saves the graph as a shapefiles and change its name
        param: extensions: the file extensions to change its name
        param: new_old: the new names
        """
        print('to_shp')
        nx.readwrite.nx_shp.write_shp(self.graph, location)
        [replace(join(location, '.'.join([new_old_file[0], ext])),
                 join(location, '.'.join([new_old_file[1], ext]))) for new_old_file in new_old for ext in extensions]
        # In case the the nodes file name is not changed, a projection file for the nodes should be created.
        # It be done by  copy the sight_line.prj and paste it in the same location as odes.prj
        if not self.change_all_name:
            import shutil
            shutil.copyfile(join(location, 'sight_line.prj'), join(location, 'nodes.prj'))


if __name__ == '__main__':
    CentralityGraph('.', True)
