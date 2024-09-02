
POI Visibility Network is a QGIS plug-in that constructs graphs (networks) of unobstructed lines of sight  between two types of decision points during urban travel – junctions and turning points within the street network (SN), and origins and destinations of travel, i.e. points of interest (POI). POIs are locations designated as relevant for the analysis, i.e. buildings, entrances, amenities, stations, and other. These are point-based, linear or polygon entities, as the user might wish to encode them in the input data. 
Graphs are constructed by connecting potential observer’s locations in an open space between buildings with straight lines of mutual vision. Visibility graphs (VG) that are created in this way illustrate a net of hypothetical visual trajectories of a person wandering around the city.

The plug-in offers three options for graph construction:

1.Integrative Visibility Graph (IVG) – creates visual connections that integrate locations of POIs within the street network.
2.Street Network Visibility Graph (SNVG) - creates visual connections between decision points of the street network, i.e. street intersections and turning points.
3.Point of Interest Visibility Graph (POIVG) - creates visual connections between POIs that are visible from each other in a given building arrangement. 

In addition, POI Visibility Network provides advanced options to build a graph using a predefined viewing distance and perceptual perspective. The plug-in then calculates and distributes specific weights among graph nodes according to their distance from the viewing location.

Graphs are constructed and visualised as new layers in QGIS and delivered as Geographic Data Files (GDF), in which nodes and edges of the graph are represented in two distinct comma-separated value sections. GDF file is suitable for further network exploration, analysis and visualisation in all kinds of network software, e.g. https://gephi.org/. 

Sample dataset is available to make it easier for you to test this plug-in: https://drive.google.com/file/d/19EsWVHqqZTXTyvWvpQ98U7xRrc9ZUu6V/view?usp=sharing

Tutorials demonstrating aims and uses of the plug-in:
https://youtu.be/52_wwbwj-vo
https://youtu.be/GYP0f1aC5c4
https://youtu.be/HdV4uGWjBQo
