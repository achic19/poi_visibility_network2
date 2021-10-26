import networkx as nx


class CentralityGraph:
    """
    This class calculates three centrality indices (Closeness, Degree, and Betweenness) based on the networkx library.
    """

    def __init__(self, file_path: str):
        """
        :param file_path: The directory in which the sight lines and sight points files are located.
        """

        self.graph = nx.readwrite.nx_shp.read_shp(file_path).to_undirected()

    def degree(self):
        """
        Compute the degree centrality for nodes.
        """
        node_degree = nx.degree_centrality(self.graph)
        nx.set_edge_attributes(self.graph, node_degree, 'degree')

    def to_shp(self, out_dir_shp):
        """
        It saves the graph as a shapefile.
        :param out_dir_shp: The directory where the output will be stored.
        """
        nx.readwrite.nx_shp.write_shp(self.graph, outdir=out_dir_shp)


if __name__ == '__main__':
    test = CentralityGraph('.')
    test.degree()
    test.to_shp('results')
