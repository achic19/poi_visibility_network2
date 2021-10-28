import networkx as nx
from shutil import copy

class CentralityGraph:
    """
    This class calculates three centrality indices (Closeness, Degree, and Betweenness) based on the networkx library.
    """

    def __init__(self, file_path: str):
        """
        :param file_path: The directory in which the sight lines and sight points files are located.
        """

        self.graph = nx.Graph(nx.readwrite.nx_shp.read_shp(file_path).to_undirected())

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

    def to_shp(self, out_dir_shp,prj):
        """
        It saves the graph as a shapefile.
        :param out_dir_shp: The directory where the output will be stored.
        """
        print('to_shp')
        nx.readwrite.nx_shp.write_shp(self.graph, outdir=out_dir_shp)
        # copy the projection file into results folder
        # copy()
        # [copy('.'.join((path, file_ext)), folder) for file_ext in ('dbf', 'prj', 'shp', 'shx')]


if __name__ == '__main__':
    test = CentralityGraph('.')
    test.degree()
    test.betweenness()
    test.edge_betweenness()
    test.closeness()
    test.to_shp('results')
