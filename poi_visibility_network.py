# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PoiVisibilityNetwork
                                 A QGIS plugin
 A tool for constructing and visualising a graph of sightlines between urban points of interest and street network.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-01-12
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Achituv Cohen and Asya Natapov
        email                : achic19@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path
from os import replace as rp_file_path
import sys

from PyQt5.QtCore import *
from qgis.PyQt.QtWidgets import QAction, QFileDialog

# Import my code
# Tell Python where you get processing from
from .poi_visibility_network_dialog import PoiVisibilityNetworkDialog

# Initialize Qt resources from file resources.py
# Import the code for the dialog
# from .resources import *
sys.path.append(os.path.dirname(__file__))
from .resources import *
from .work_folder.fix_geometry.QGIS import *
from .work_folder.mean_close_point.mean_close_point import *
from .work_folder.POI.merge_points import *
from .create_sight_line import *
from plugins.processing.algs.qgis.LinesToPolygons import *
from .work_folder.same_area.same_area import *
from .work_folder.centrality.centrality import *


class PoiVisibilityNetwork:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PoiVisibilityNetwork_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = PoiVisibilityNetworkDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&POI Visibility Network')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.poi_name, self.poi_list = None, None
        # This flag manages what to run: all - 1, run with points layers -2, create visibility sight lines - 3
        # create point layers to perform latter create visibility sight lines
        self.processing_option = 1

        # Specific code for this plugin
        self.graph_to_draw = 'ivg'
        self.dlg.pushButton.clicked.connect(self.select_output_folder)
        self.dlg.radioButton_4.toggled.connect(self.select_ivg_graph)
        self.dlg.radioButton_5.toggled.connect(self.select_snvg_graph)
        self.dlg.radioButton_6.toggled.connect(self.select_poi_graph)

        # Listen for type of processing
        self.dlg.radioButton_2.toggled.connect(self.run_all)
        self.dlg.radioButton.toggled.connect(self.run_with_pnt_layer)
        self.dlg.radioButton_3.toggled.connect(self.create_pnt_layer)

        self.filename = os.path.join(os.path.dirname(__file__), 'results')
        self.layer_list = []
        self.error = ''

        # if the sight lines are generated straight form sight lines allow only point geometry


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PoiVisibilityNetwork', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/poi_visibility_network/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Visualize a graph of sightlines'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&POI Visibility Network'),
                action)
            self.iface.removeToolBarIcon(action)

    # New methods
    def select_output_folder(self):

        self.filename = QFileDialog.getExistingDirectory(self.dlg, "Select output folder ", self.plugin_dir)
        self.dlg.lineEdit.setText(str(self.filename))
        if str(self.filename) == '':
            self.iface.messageBar().pushMessage('You should select folder to store output files', level=Qgis.Warning)
            self.dlg.buttonBox.setEnabled(False)
        else:
            self.dlg.buttonBox.setEnabled(True)

    # Based on the selected graph customize the plugins
    def select_snvg_graph(self):

        self.dlg.comboBox_3.setEnabled(False)
        # Unable aggregation distance
        self.dlg.checkBox_3.setEnabled(True)
        self.dlg.lineEdit_3.setEnabled(True)
        self.graph_to_draw = 'snvg'
        # 2

    def select_poi_graph(self):

        self.dlg.comboBox_3.setEnabled(True)
        # Unable aggregation distance
        self.dlg.checkBox_3.setEnabled(False)
        self.dlg.lineEdit_3.setEnabled(False)
        self.graph_to_draw = 'poi'
        # 3

    def select_ivg_graph(self):
        self.dlg.comboBox_3.setEnabled(True)
        # Unable aggregation distance
        self.dlg.checkBox_3.setEnabled(True)
        self.dlg.lineEdit_3.setEnabled(True)
        self.graph_to_draw = 'ivg'
        # 1

    # The next four functions menage which button to en/unable
    def run_all(self):
        self.processing_option = 1
        self.select_what_to_perform()

        # if the sight lines are generated straight form sight lines allow only point geometry if no allow all
        self.dlg.comboBox_3.clear()
        self.poi_name, self.poi_list = self.papulate_comboList([0, 1, 2])
        self.dlg.comboBox_3.addItems(self.poi_name)


    def run_with_pnt_layer(self):
        self.processing_option = 2
        self.select_what_to_perform()

        # if the sight lines are generated straight form sight lines allow only point geometry if no allow all
        self.dlg.comboBox_3.clear()
        self.poi_name, self.poi_list = self.papulate_comboList([0])
        self.dlg.comboBox_3.addItems(self.poi_name)

    def create_pnt_layer(self):
        self.processing_option = 3
        self.select_what_to_perform()

        # if the sight lines are generated straight form sight lines allow only point geometry if no allow all
        self.dlg.comboBox_3.clear()
        self.poi_name, self.poi_list = self.papulate_comboList([0, 1, 2])
        self.dlg.comboBox_3.addItems(self.poi_name)

    def select_what_to_perform(self):
        flag_streets = True
        if self.processing_option == 2:
            flag_streets = False

        # # #  Create Visibility Graph
        # self.dlg.groupBox_2.enabled = False
        self.dlg.groupBox_2.setEnabled(flag_streets)

        # #Input Layers
        self.dlg.comboBox_1.setEnabled(flag_streets)
        self.dlg.label.setEnabled(flag_streets)
        if self.processing_option == 2:
            self.dlg.label_4.setText('Select points layer')
            self.dlg.comboBox_3.setEnabled(True)
        else:
            self.dlg.label_4.setText('Select  POI')
            if self.dlg.radioButton_5.isChecked():
                self.dlg.comboBox_3.setEnabled(False)

        # # Advanced Options
        self.dlg.checkBox_3.setEnabled(flag_streets)
        self.dlg.lineEdit_3.setEnabled(flag_streets)
        if self.processing_option == 3:
            self.dlg.checkBox_centrality.setEnabled(False)
            self.dlg.checkBox_2.setEnabled(False)
            self.dlg.checkBox.setEnabled(False)
            self.dlg.lineEdit_2.setEnabled(False)
        else:
            self.dlg.checkBox_centrality.setEnabled(True)
            self.dlg.checkBox_2.setEnabled(True)
            self.dlg.checkBox.setEnabled(True)
            self.dlg.lineEdit_2.setEnabled(True)

    def papulate_comboList(self, geometry_type):
        '''

        :param geometry_type: array of allowed geometry type

        :return: lists with layers and layer name to display
        '''
        name_list = []
        layer_list = []

        for layer in self.iface.mapCanvas().layers():
            try:
                if layer.geometryType() in geometry_type:
                    name_list.append(layer.name())
                    layer_list.append(layer)
            except:
                continue
        return name_list, layer_list

    def run(self):

        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()

        # Get all loaded layers in the interface
        self.layers = self.iface.mapCanvas().layers()
        if not self.layers:
            self.iface.messageBar().pushMessage('No layers in layers list', level=Qgis.Critical)
            return

        # Clear comboBox (useful so we don't create duplicate items in list)
        self.dlg.comboBox_1.clear()
        # Clear comboBox_2
        self.dlg.comboBox_2.clear()
        # Clear comboBox_3
        self.dlg.comboBox_3.clear()

        # Add all items in list to comboBox
        # Add items to constrain comboBox
        constrains_list_name, constrains_list = self.papulate_comboList([1, 2])
        self.dlg.comboBox_2.addItems(constrains_list_name)
        # Add items to network comboBox
        network_list_name, network_list = self.papulate_comboList([1])
        self.dlg.comboBox_1.addItems(network_list_name)
        # Add items to poi comboBox
        self.poi_name, self.poi_list = self.papulate_comboList([0, 1, 2])
        self.dlg.comboBox_3.addItems(self.poi_name)

        # Run the dialog event loop
        result = self.dlg.exec_()

        # Identify network layer by its index and get his path

        # Identify constrains layer by its index and get his path
        selectedLayerIndex_2 = self.dlg.comboBox_2.currentIndex()
        constrains = constrains_list[selectedLayerIndex_2]
        constrains_temp = constrains.dataProvider().dataSourceUri()
        constrains_temp = str.split(constrains_temp, '|')[0]

        selectedLayerIndex = self.dlg.comboBox_1.currentIndex()
        network = network_list[selectedLayerIndex]
        network_temp = network.dataProvider().dataSourceUri()
        network_temp = str.split(network_temp, '|')[0]

        poi_temp = None
        poi = None
        if self.graph_to_draw in ['ivg', 'poi'] or self.processing_option == 2:
            # Identify Point Of Interest layer by its index and get his path
            selectedLayerIndex_3 = self.dlg.comboBox_3.currentIndex()
            poi = self.poi_list[selectedLayerIndex_3]
            poi_temp = poi.dataProvider().dataSourceUri()
            poi_temp = str.split(poi_temp, '|')[0]

        # Store the result folder to work with
        res_folder = str(self.filename)

        # See if OK was pressed
        if result:
            time_tot = time.time()
            # var to validate all inputs
            flag = True
            # handle weight
            if self.dlg.checkBox_2.isChecked():
                weight = 1
            else:
                weight = 0
            # handle restricted vision
            if self.dlg.checkBox.isChecked() and not self.dlg.radioButton_3.isChecked():
                restricted = 1
                try:
                    restricted_length = float(self.dlg.lineEdit_2.text())
                except ValueError:
                    self.error = 'Non-numeric data found in the restricted vision input'
                    flag = False
            else:
                restricted = 0
                restricted_length = 0

            # handle aggregation distance
            if self.dlg.checkBox_3.isChecked() and self.graph_to_draw != 'poi' and not self.dlg.radioButton.isChecked():
                try:
                    aggr_dist = float(self.dlg.lineEdit_3.text())
                except ValueError:
                    self.error = 'Non-numeric data found in the aggregation distance input'
                    flag = False
            else:
                aggr_dist = 20
            if flag:
                self.run_logic(network_temp, constrains, constrains_temp, poi_temp, res_folder, weight, restricted,
                               restricted_length, poi, aggr_dist, self.dlg.checkBox_centrality.isChecked())
                self.iface.messageBar().pushMessage("Sight lines is created in {} seconds".
                                                    format(str(time.time() - time_tot)), level=Qgis.Info)
            else:
                self.iface.messageBar().pushMessage(self.error, level=Qgis.Critical)

    def run_logic(self, network_temp, constrains_gis, constrains_temp, poi_temp, res_folder, weight, restricted,
                  restricted_length, poi, aggr_dist, is_centrality):
        '''
        The params are input from user
        :param aggr_dist: aggregation distance when  MeanClosePoint function is applied
        :param network_temp:
        :param constrains_temp:
        :param poi_temp:
        :param res_folder:
        :param weight:
        :param restricted:
        :param restricted_length:
        :param poi: check its geometry and if necessary centerlized it
        :param is_centrality: control whether centrality measures are should be calculate
        :return:
        '''
        # delete old files
        from work_folder import delete_file
        delete_file.delete_file()

        # what to do
        # 1- all , 2 - create sight lines 3 - prepare sight lines
        # In case of constrain as polyline file and network involve POI, the polyline file should convert to
        # to polygon file
        if constrains_gis.geometryType() == 1 and self.graph_to_draw in ['ivg', 'poi']:
            feedback = QgsProcessingFeedback()
            output = os.path.join(os.path.dirname(__file__), r'work_folder/input/building_1.shp')
            alg = LinesToPolygons()
            alg.initAlgorithm()
            context = QgsProcessingContext()
            params = {'INPUT': constrains_gis, 'OUTPUT': output}
            alg.processAlgorithm(params, context, feedback=feedback)
            constrains_temp = output
        # #  Reproject layers files
        if self.processing_option != 2:
            SightLine.reproject([constrains_temp, poi_temp, network_temp])
        else:
            SightLine.reproject([constrains_temp, poi_temp])

        # Define intersections only between more than 2 lines return dissolve_0
        constrains = os.path.join(os.path.dirname(__file__), r'work_folder\general\constrains.shp')
        if self.processing_option != 2:
            network = os.path.join(os.path.dirname(__file__), r'work_folder\general\networks.shp')
            myQGIS(network, "_lines")
            network_new = os.path.join(os.path.dirname(__file__),
                                       r'work_folder\fix_geometry\results_file\dissolve_0.shp')

            # Create sight_line instance success
            my_sight_line = SightLine(network_new, constrains, res_folder, NULL)

            # Don't run in case of POI graph
            if self.graph_to_draw in ['ivg', 'snvg']:
                # Find intersections success
                my_sight_line.intersections_points()
                my_sight_line.delete_duplicate_geometries()

                # Calculate mean for close points, Finish with mean_close_coor.shp
                my_sight_line.turning_points()
                MeanClosePoint(aggr_dist)
                my_sight_line.delete_duplicate_geometries()

            if self.graph_to_draw in ['ivg', 'poi']:
                # Merge all the visibility POI's and intersections
                #  to one file and project POI points outside polygons ,
                # Finish with final.shp
                poi_path = os.path.join(os.path.dirname(__file__), r'work_folder\general\pois.shp')
                # In a case of POI as polygon or polyline  centralized the layer
                if not poi.geometryType() == 0:
                    poi_path = SightLine.centerlized()

                if self.graph_to_draw == 'poi':
                    MergePoint(poi_path)
                else:
                    MergePoint(poi_path, graph_type=1)
                final = os.path.join(os.path.dirname(__file__), r'work_folder\POI\results_file\final.shp')
            else:
                final = os.path.join(os.path.dirname(__file__), r'work_folder\mean_close_point\results_file\final.shp')

        # Calc sight lines
        # calc sight lines directly from the user input ( after projection)
        else:
            my_sight_line = SightLine(constrains=constrains, res_folder=res_folder, project=NULL)
            final = os.path.join(os.path.dirname(__file__), r'work_folder\general\pois.shp')

        if self.processing_option != 3:
            SightLineDB(constrains, final, restricted, restricted_length, res_folder)
            # self.iface.messageBar().pushMessage("Sight lines is created in {} seconds".
            #                                     format(str(test_time.times)), level=Qgis.Info)
        # copy sight nodes file to result folder
        my_sight_line.copy_shape_file_to_result_file(final, 'sight_node')

        # Add centrality indices

        # Add  new fields that store information about points type and id point

        path_node = os.path.join(res_folder, 'sight_node.shp')
        if self.processing_option != 3:
            if is_centrality:
                if self.processing_option == 1:
                    CentralityGraph(res_folder, True)
                else:
                    CentralityGraph(res_folder, False)
            sight_line = os.path.join(res_folder, 'sight_line.shp')
            sight_lines = QgsVectorLayer(
                sight_line,
                "sight_line",
                "ogr")

        nodes = QgsVectorLayer(
            path_node,
            "nodes",
            "ogr")

        # update Point ID if needed
        if nodes.fields()[len(nodes.fields()) - 1].name() != 'point_id':
            nodes.dataProvider().addAttributes(
                [QgsField('poi_type', QVariant.String), QgsField('point_id', QVariant.Int)])
            nodes.updateFields()
        n = len(nodes.fields())
        for i, feature in enumerate(nodes.getFeatures()):
            nodes.dataProvider().changeAttributeValues({i: {n - 1: i}})

        if self.processing_option != 2:
            if self.graph_to_draw == 'ivg':
                for i, feature in enumerate(nodes.getFeatures()):
                    if str(feature['InputID']) is 'NULL':
                        nodes.dataProvider().changeAttributeValues({i: {n - 2: 'POI'}})
                    else:
                        nodes.dataProvider().changeAttributeValues({i: {n - 2: 'intersection'}})
            if self.graph_to_draw == 'snvg':
                for i, feature in enumerate(nodes.getFeatures()):
                    nodes.dataProvider().changeAttributeValues({i: {n - 2: 'intersection'}})
            elif self.graph_to_draw == 'poi':
                for i, feature in enumerate(nodes.getFeatures()):
                    nodes.dataProvider().changeAttributeValues({i: {n - 2: 'POI'}})

        # create gdf file and update weight and length fields
        my_sight_line.layers[0] = nodes
        if self.processing_option != 3:
            my_sight_line.layers[1] = sight_lines
        my_sight_line.create_gdf_file(weight=weight, graph_name=self.graph_to_draw,
                                      is_sight_line=self.processing_option)

        if self.processing_option != 3:
            self.iface.addVectorLayer(sight_line, " ", "ogr")

        # Update symbology for the layers being upload to Qgis project
        if self.processing_option != 2:

            layer = self.iface.addVectorLayer(path_node, " ", "ogr")
            if self.graph_to_draw == 'ivg':

                # define some rules: label, expression, symbol
                symbol_rules = (
                    ('POI', '"InputID" is NULL', 'red', 4),
                    ('Intersetions', '"InputID" is not NULL', 'blue', 2),
                )

                # create a new rule-based renderer
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                renderer = QgsRuleBasedRenderer(symbol)

                # get the "root" rule
                root_rule = renderer.rootRule()

                for label, expression, color_name, size in symbol_rules:
                    # create a clone (i.e. a copy) of the default rule
                    rule = root_rule.children()[0].clone()
                    # set the label, expression and color
                    rule.setLabel(label)
                    rule.setFilterExpression(expression)
                    rule.symbol().setColor(QColor(color_name))
                    rule.symbol().setSize(size)
                    # append the rule to the list of rules
                    root_rule.appendChild(rule)

                # delete the default rule
                root_rule.removeChildAt(0)

            if self.graph_to_draw == 'snvg':
                symbol_1 = QgsMarkerSymbol.createSimple({'size': '2.0',
                                                         'color': 'blue'})

                renderer = QgsSingleSymbolRenderer(symbol_1)

            elif self.graph_to_draw == 'poi':
                symbol_1 = QgsMarkerSymbol.createSimple({'size': '4.0',
                                                         'color': 'red'})

                renderer = QgsSingleSymbolRenderer(symbol_1)
                # apply the renderer to the layer
            layer.setRenderer(renderer)
        elif is_centrality:
            path_node = os.path.join(res_folder, 'nodes.shp')
            self.iface.addVectorLayer(path_node, " ", "ogr")
