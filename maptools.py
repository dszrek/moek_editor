#!/usr/bin/python
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.gui import QgsMapToolIdentify, QgsMapTool, QgsRubberBand
from qgis.core import QgsApplication, QgsProject, QgsGeometry, QgsVectorLayer, QgsFeature, QgsWkbTypes, QgsPointXY, QgsPoint, QgsExpressionContextUtils, QgsFeatureRequest, QgsRectangle, QgsTolerance, QgsPointLocator, QgsSnappingConfig, edit
from qgis.PyQt.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QColor, QKeySequence
from qgis.utils import iface

from .classes import PgConn, threading_func
from .viewnet import vn_change, vn_powsel, vn_polysel

dlg = None

def dlg_maptools(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg


class ObjectManager:
    """Menadżer obiektów."""
    def __init__(self, dlg, canvas):
        self.dlg = dlg  # Referencja do wtyczki
        self.canvas = canvas  # Referencja do mapy
        self.flag_menu = False
        self.flag = None
        self.flag_data = [None, None, None]
        self.wyr = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "flag":
            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'flag_sel', val)
            QgsProject.instance().mapLayersByName("flagi_bez_teren")[0].triggerRepaint()
            QgsProject.instance().mapLayersByName("flagi_z_teren")[0].triggerRepaint()
        elif attr == "flag_data":
            if self.flag_data[0] and self.flag != self.flag_data[1][0]:
                self.flag = self.flag_data[1][0]
        elif attr == "wyr":
            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'wyr_sel', val)
            QgsProject.instance().mapLayersByName("wyr_point")[0].triggerRepaint()
            QgsProject.instance().mapLayersByName("wyr_poly")[0].triggerRepaint()

    def obj_change(self, obj_data, click):
        lyr_name = obj_data[0]
        if click == "left":
            if lyr_name == "wyr_point":
                self.wyr = obj_data[1][0]
            else:
                self.flag_data = obj_data
                self.menu_hide()
        elif click == "right":
            if self.flag == obj_data[1][0]:
                self.menu_show()
            else:
                self.menu_hide()

    def menu_hide(self):
        if self.flag_menu:
            dlg.flag_menu.hide()
            self.flag_menu = False

    def menu_show(self):
        if self.flag_menu:
            return
        extent =iface.mapCanvas().extent()
        geom = self.flag_data[2]
        x_map = round(extent.xMaximum()) - round(extent.xMinimum())
        y_map = round(extent.yMaximum()) - round(extent.yMinimum())
        xp = round(geom.x()) - round(extent.xMinimum())
        yp = round(extent.yMaximum()) - round(geom.y())
        x_scr = round(xp * iface.mapCanvas().width() / x_map)
        y_scr = round(yp * iface.mapCanvas().height() / y_map)
        dlg.flag_menu.move(x_scr - 56, y_scr + 25)
        dlg.flag_menu.show()
        self.flag_menu = True


class MapToolManager:
    """Menadżer maptool'ów."""
    def __init__(self, dlg, canvas):
        self.maptool = None  # Instancja klasy maptool'a
        self.mt_name = None  # Nazwa maptool'a
        self.params = {}  # Słownik z parametrami maptool'a
        self.dlg = dlg  # Referencja do wtyczki
        self.canvas = canvas  # Referencja do mapy
        self.old_button = None
        self.feat_backup = None
        self.canvas.mapToolSet.connect(self.maptool_change)


        self.maptools = [
            # {"name" : "edit_poly", "class" : EditPolyMapTool, "lyr" : ["flagi_z_teren", "flagi_bez_teren", "wn_kopaliny_pne", "wyrobiska"], "fn" : obj_sel},
            {"name" : "multi_tool", "class" : MultiMapTool, "button" : self.dlg.side_dock.toolboxes["tb_multi_tool"].widgets["btn_multi_tool"], "lyr" : ["flagi_z_teren", "flagi_bez_teren", "wn_kopaliny_pne", "wyr_point"], "fn" : obj_sel},
            {"name" : "vn_sel", "class" : IdentMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_sel"], "lyr" : ["vn_user"], "fn" : vn_change},
            {"name" : "vn_powsel", "class" : IdentMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_powsel"], "lyr" : ["powiaty"], "fn" : vn_powsel},
            {"name" : "vn_polysel", "class" : PolyDrawMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_polysel"], "fn" : vn_polysel},
            {"name" : "flt_add", "class" : PointDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_flag_fchk"], "fn" : flag_add, "extra" : ['true']},
            {"name" : "flf_add", "class" : PointDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_flag_nfchk"], "fn" : flag_add, "extra" : ['false']},
            # {"name" : "flag_del", "class" : IdentMapTool, "button" : self.dlg.p_flag.widgets["btn_flag_del"], "lyr" : ["flagi_z_teren", "flagi_bez_teren"], "fn" : flag_del},
            {"name" : "wyr_add_poly", "class" : PolyDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_wyr_add_poly"], "fn" : wyr_add_poly},
            {"name" : "wyr_edit", "class" : EditPolyMapTool, "button" : self.dlg.side_dock.toolboxes["tb_multi_tool"].widgets["btn_wyr_edit"], "lyr" : ["wyr_poly"], "fn" : wyr_poly_change}
            # {"name" : "wyr_del", "class" : IdentMapTool, "button" : self.dlg.p_wyr.widgets["btn_wyr_del"], "lyr" : ["wyrobiska"], "fn" : wyr_del}
            # {"name" : "auto_add", "class" : PointDrawMapTool, "button" : self.dlg.p_auto.widgets["btn_auto_add"], "fn" : auto_add},
            # {"name" : "auto_del", "class" : IdentMapTool, "button" : self.dlg.p_auto.widgets["btn_auto_del"], "lyr" : ["parking"], "fn" : auto_del},
            # {"name" : "marsz_add", "class" : LineDrawMapTool, "button" : self.dlg.p_auto.widgets["btn_marsz_add"], "fn" : marsz_add},
            # {"name" : "marsz_del", "class" : IdentMapTool, "button" : self.dlg.p_auto.widgets["btn_marsz_del"], "lyr" : ["marsz"], "fn" : marsz_del}
        ]
        self.init("multi_tool")

    def maptool_change(self, new_tool, old_tool):
        if not new_tool and not old_tool:
            # Jeśli wyłączany jest maptool o klasie QgsMapToolIdentify,
            # event jest puszczany dwukrotnie (pierwszy raz z wartościami None, None)
            return
        try:
            dlg.obj.menu_hide()
        except:
            pass
        if self.old_button:
            self.old_button.setChecked(False)
        try:  # Maptool może nie mieć atrybutu '.button()'
            self.old_button = new_tool.button()
        except:
            self.old_button = None

    def init(self, maptool):
        """Zainicjowanie zmiany maptool'a."""
        if not self.mt_name:  # Nie ma obecnie uruchomionego maptool'a
            self.tool_on(maptool)  # Włączenie maptool'a
        else:
            mt_old = self.mt_name
            if mt_old != maptool:  # Inny maptool był włączony
                self.tool_on(maptool)  # Włączenie nowego maptool'a
            else:
                self.tool_on("multi_tool")

    def tool_on(self, maptool):
        """Włączenie maptool'a."""
        self.params = self.dict_name(maptool)  # Wczytanie parametrów maptool'a
        if "lyr" in self.params:
            lyr = lyr_ref(self.params["lyr"])
        if self.params["class"] == MultiMapTool:
            self.maptool = self.params["class"](self.canvas, lyr, self.params["button"])
            self.maptool.identified.connect(self.params["fn"])
        elif self.params["class"] == IdentMapTool:
            self.maptool = self.params["class"](self.canvas, lyr, self.params["button"])
            self.maptool.identified.connect(self.params["fn"])
        elif self.params["class"] == EditPolyMapTool:
            geom = self.get_feat_geom(lyr[0])
            if not geom:
                self.maptool = DummyMapTool(self.canvas, self.params["button"])
                self.mt_name = "dummy"
                self.canvas.setMapTool(self.maptool)
                self.init("multi_tool")
                return
            else:
                self.geom_to_layers(geom)
                self.maptool = self.params["class"](self.canvas, lyr[0], self.params["button"])
                self.maptool.ending.connect(self.params["fn"])
        else:
            self.maptool = self.params["class"](self.canvas, self.params["button"])
            self.maptool.drawn.connect(self.params["fn"])
        self.canvas.setMapTool(self.maptool)
        self.mt_name = self.params["name"]

    def dict_name(self, maptool):
        """Wyszukuje na liście wybrany toolmap na podstawie nazwy i zwraca słownik z jego parametrami."""
        for tool in self.maptools:
            if tool["name"] == maptool:
                return tool

    def get_feat_geom(self, lyr):
        feats = lyr.getFeatures(f'"wyr_id" = {dlg.obj.wyr}')
        try:
            feat = list(feats)[0]
        except Exception as err:
            print(f"{err}")
            return None
        if isinstance(feat, QgsFeature):
            geom = self.feat_caching(lyr, feat)
            if isinstance(geom, QgsGeometry):
                return geom
            else:
                return None
        else:
            return None

    def feat_caching(self, lyr, feat):
        self.feat_backup = feat
        geom = self.feat_backup.geometry()
        with edit(lyr):
            feat.clearGeometry()
            try:
                lyr.updateFeature(feat)
            except Exception as err:
                print(err)
                self.feat_backup = None
                return None
        return geom

    def geom_to_layers(self, geom):
        """Rozkłada geometrię poligonalną na części pierwsze i przenosi je do warstw tymczasowych."""
        lyr = QgsProject.instance().mapLayersByName("edit_poly")[0]
        lyr.dataProvider().truncate()
        pg = 0  # Numer poligonu
        with edit(lyr):  # Ekstrakcja poligonów
            for poly in geom.asMultiPolygon():
                feat = QgsFeature(lyr.fields())
                feat.setAttribute("part", pg)
                feat.setGeometry(QgsGeometry.fromPolygonXY(poly))
                lyr.addFeature(feat)
                pg += 1


class DummyMapTool(QgsMapTool):
    """Pusty maptool przekazujący informacje o przycisku innego maptool'a."""
    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)

    def button(self):
        return self._button


class EditPolyMapTool(QgsMapTool):
    """Maptool do edytowania poligonalnej geometrii wyrobiska."""
    cursor_changed = pyqtSignal(str)
    node_selected = pyqtSignal(bool)
    ending = pyqtSignal(QgsVectorLayer, QgsGeometry)

    def __init__(self, canvas, layer, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.layer = layer
        self.dragging = False
        self.geom = None
        self.node_presel = []
        self.node_sel = False
        self.node_idx = (-1, -1)
        self.area_rbs = []
        self.vertex_rbs = []
        self.edit_layer = QgsProject.instance().mapLayersByName("edit_poly")[0]
        self.snap_config = QgsSnappingConfig(QgsProject.instance())
        self.snap_config.setMode(QgsSnappingConfig.SnappingMode.AdvancedConfiguration)
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                if layer.name() == "edit_poly":
                    lyr_settings = QgsSnappingConfig.IndividualLayerSettings(True, QgsSnappingConfig.SnappingType.VertexAndSegment, 20.0, QgsTolerance.Pixels)
                else:
                    lyr_settings = QgsSnappingConfig.IndividualLayerSettings(False, 0, 0.0, QgsTolerance.Pixels)
                self.snap_config.setIndividualLayerSettings(layer, lyr_settings)
        self.snap_config.setEnabled(True)
        self.canvas.snappingUtils().setConfig(self.snap_config)
        self.rbs_create()
        self.rbs_populate()
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "open_hand"
        self.node_selected.connect(self.node_sel_change)

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)
        if attr == "node_sel":
            self.node_selected.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["arrow", Qt.ArrowCursor],
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor],
                    ["cross", Qt.CrossCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def node_sel_change(self, _bool):
        """Zmiana zaznaczonego node'a."""
        if _bool:
            self.node_idx = self.get_node_index()
            self.node_selector.movePoint(self.node_presel[0].point(), 0)
            self.node_selector.setVisible(True)
        else:
            self.node_idx = (-1, -1)
            self.node_selector.setVisible(False)

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        for i in range(self.edit_layer.featureCount()):
            _arb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            _arb.setWidth(1)
            _arb.setColor(QColor(255, 255, 0, 255))
            _arb.setFillColor(QColor(255, 255, 0, 24))
            _arb.setVisible(True)
            self.area_rbs.append(_arb)
            _vrb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
            _vrb.setIcon(QgsRubberBand.ICON_CIRCLE)
            _vrb.setColor(QColor(255, 255, 0, 255))
            _vrb.setFillColor(QColor(255, 255, 0, 0))
            _vrb.setIconSize(8)
            _vrb.setVisible(True)
            self.vertex_rbs.append(_vrb)

        self.area_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.area_marker.setWidth(3)
        self.area_marker.setColor(QColor(255, 255, 0, 255))
        self.area_marker.setFillColor(QColor(255, 255, 0, 0))
        self.area_marker.setVisible(False)

        self.edge_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.edge_marker.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.edge_marker.setColor(QColor(0, 0, 0, 255))
        self.edge_marker.setFillColor(QColor(255, 255, 0, 255))
        self.edge_marker.setIconSize(6)
        self.edge_marker.addPoint(QgsPointXY(0, 0), False)
        self.edge_marker.setVisible(False)

        self.vertex_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.vertex_marker.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.vertex_marker.setColor(QColor(255, 255, 0, 255))
        self.vertex_marker.setFillColor(QColor(255, 255, 0, 255))
        self.vertex_marker.setIconSize(8)
        self.vertex_marker.addPoint(QgsPointXY(0, 0), False)
        self.vertex_marker.setVisible(False)

        self.node_selector = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_selector.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_selector.setColor(QColor(0, 0, 0, 255))
        self.node_selector.setFillColor(QColor(255, 255, 0, 255))
        self.node_selector.setIconSize(14)
        self.node_selector.addPoint(QgsPointXY(0, 0), False)
        self.node_selector.setVisible(False)

    def rbs_populate(self):
        """Załadowanie poligonów i punktów do rubberband'ów."""
        for i in range(len(self.area_rbs)):
            geom = self.get_geom_from_part(i)
            poly = geom.asPolygon()[0]
            for j in range(len(poly) - 1):
                self.area_rbs[i].addPoint(poly[j])
                self.vertex_rbs[i].addPoint(poly[j])

    def snap_to_layer(self, event):
        self.canvas.snappingUtils().setCurrentLayer(self.edit_layer)
        v = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Vertex)
        e = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Edge)
        a = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Area)
        return v, e, a

    def canvasMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.dragging = True
            self.cursor = "closed_hand"
            self.canvas.panAction(event)
        elif event.button() == Qt.NoButton and not self.dragging:
            map_point = self.toMapCoordinates(event.pos())
            v, e, a = self.snap_to_layer(event)
            snap_type = v.type() + e.type() + a.type()
            if snap_type == 0:  # Kursor poza poligonami, brak obiektów do przyciągnięcia
                if self.node_presel:
                    self.node_presel = []
                self.vertex_marker.setVisible(False)
                self.edge_marker.setVisible(False)
                self.area_marker.setVisible(False)
                self.cursor = "open_hand"
            elif snap_type == 4:  # Kursor w obrębie poligonu
                if self.node_presel:
                    self.node_presel = []
                self.vertex_marker.setVisible(False)
                self.edge_marker.setVisible(False)
                self.area_marker.setVisible(True)
                self.cursor = "open_hand"
            elif snap_type == 5 or snap_type == 7:  # Wierzchołek do przyciągnięcia
                self.node_presel = [v, e.featureId()]
                self.vertex_marker.movePoint(v.point(), 0)
                self.vertex_marker.setVisible(True)
                self.edge_marker.setVisible(False)
                self.area_marker.setVisible(True)
                self.cursor = "arrow"
            elif snap_type == 6:  # Krawędź do przyciągnięcia
                if self.node_presel:
                    self.node_presel = []
                self.edge_marker.movePoint(e.point(), 0)
                self.edge_marker.setVisible(True)
                self.vertex_marker.setVisible(False)
                self.area_marker.setVisible(True)
                self.cursor = "cross"

    def get_geom_from_id(self, id):
        """Zwraca geometrię poligonu o numerze id."""
        for feat in self.edit_layer.getFeatures():
            if feat.id() == id:
                return feat.geometry()
        return None

    def get_geom_from_part(self, part):
        """Zwraca geometrię poligonu o numerze atrybutu 'part'."""
        feats = self.edit_layer.getFeatures(f'"part" = {part}')
        try:
            feat = list(feats)[0]
        except:
            return None
        return feat.geometry()

    def get_node_index(self):
        """Zwraca index punktu i poligonu, znajdującego się pod vertex_selector'em."""
        i = 0
        point = self.node_presel[0].point()
        for rb in self.vertex_rbs:
            j = 0
            rb_geom = rb.asGeometry()
            for part in rb_geom.constParts():
                p_geom = QgsPointXY(part.x(), part.y())
                if point == p_geom:
                    return i, j
                j += 1
            i += 1
        return -1, -1

    def get_geom_from_vertex_rb(self, rb):
        """Zwraca geometrię zbudowaną z punktów rubberband'u."""
        pts = []
        for part in rb.constParts():
            pts.append((part.x(), part.y()))
        poly = QgsGeometry.fromPolygonXY([[QgsPointXY(pair[0], pair[1]) for pair in pts]])
        return poly

    def vertex_delete(self):
        """Usuwa zaznaczony wierzchołek poligonu."""
        if self.node_idx[0] < 0:
            print("brak zaznaczonego wierzchołka")
            return
        self.vertex_rbs[self.node_idx[0]].removePoint(self.node_idx[1], True)
        self.node_sel = False

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.dragging:
            if self.node_presel:
                self.node_sel = True
            else:
                self.node_sel = False
        elif event.button() == Qt.LeftButton and self.dragging:
            self.canvas.panActionEnd(event.pos())
            self.dragging = False
            self.cursor = "open_hand"
        elif event.button() == Qt.RightButton and not self.dragging:
            self.reset()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            event.ignore()  # Przerwanie domyślnego działania skrótu klawiszowego
            if self.node_sel:
                self.vertex_delete()  # Skasowanie wierzchołka
                self.geom_update()  # Aktualizacja geometrii na warstwie
                self.rbs_clear()  # Skasowanie rubberband'ów
                self.rbs_create()  # Utworzenie nowych rubberband'ów
                self.rbs_populate()  # Załadowanie geometrii do rubberband'ów
        elif event.key() == Qt.Key_Escape:
            if self.dragging:
                self.stop_dragging()

    def geom_update(self):
        """Aktualizacja geometrii poligonów, po jej zmianie."""
        self.edit_layer.dataProvider().truncate()
        # Załadowanie aktualnej geometrii do warstwy edit_poly:
        geom_list = []
        with edit(self.edit_layer):
            for i in range(len(self.vertex_rbs)):
                geom = self.get_geom_from_vertex_rb(self.vertex_rbs[i].asGeometry())
                feat = QgsFeature(self.edit_layer.fields())
                feat.setAttribute("part", i)
                feat.setGeometry(geom)
                self.edit_layer.addFeature(feat)
                geom_list.append(geom)
        if len(geom_list) > 1:
            self.geom = QgsGeometry.collectGeometry(geom_list)
        else:
            self.geom = geom_list[0]
        return self.geom

    def reset(self):
        if not self.geom:
            self.geom = self.geom_update()
        self.rbs_clear()
        self.edit_layer.dataProvider().truncate()
        self.edit_layer.triggerRepaint()
        self.ending.emit(self.layer, self.geom)

    def rbs_clear(self):
        for a in self.area_rbs:
            a.reset(QgsWkbTypes.PolygonGeometry)
        for v in self.vertex_rbs:
            v.reset(QgsWkbTypes.PointGeometry)
        self.area_rbs = []
        self.vertex_rbs = []
        self.vertex_marker.reset(QgsWkbTypes.PointGeometry)
        self.node_selector.reset(QgsWkbTypes.PointGeometry)
        self.edge_marker.reset(QgsWkbTypes.PointGeometry)
        self.area_marker.reset(QgsWkbTypes.PolygonGeometry)
        self.vertex_marker = None
        self.node_selector = None
        self.edge_marker = None
        self.area_marker = None


class MultiMapTool(QgsMapToolIdentify):
    """Domyślny maptool łączący funkcje nawigacji po mapie i selekcji obiektów."""
    identified = pyqtSignal(object, object, str)
    cursor_changed = pyqtSignal(str)

    def __init__(self, canvas, layer, button):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.dragging = False
        self.sel = False
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "open_hand"

    def button(self):
        return self._button

    @threading_func
    def findFeatureAt(self, pos):
        pos = self.toLayerCoordinates(self.layer[0], pos)
        scale = iface.mapCanvas().scale()
        tolerance = scale / 250
        search_rect = QgsRectangle(pos.x() - tolerance,
                                  pos.y() - tolerance,
                                  pos.x() + tolerance,
                                  pos.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(search_rect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        for lyr in self.layer:
            for feat in lyr.getFeatures(request):
                return feat
        return None

    @threading_func
    def ident_in_thread(self, x, y):
        """Zwraca wynik identyfikacji przeprowadzonej poza wątkiem głównym QGIS'a."""
        return self.identify(x, y, self.TopDownStopAtFirst, self.layer, self.VectorLayer)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["arrow", Qt.ArrowCursor],
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def canvasMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            dlg.flag_menu.hide()
            self.dragging = True
            self.cursor = "closed_hand"
            self.canvas.panAction(event)
        elif event.buttons() == Qt.NoButton and not self.dragging:
            th = self.findFeatureAt(event.pos())
            feat = th.get()
            if feat == None:
                if self.sel:
                    self.cursor = "open_hand"
                    self.sel = False
            else:
                if not self.sel:
                    self.cursor = "arrow"
                    self.sel = True

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.canvas.panActionEnd(event.pos())
            self.dragging = False
            self.cursor = "open_hand"
        elif event.button() == Qt.LeftButton and not self.dragging:
            th = self.ident_in_thread(event.x(), event.y())
            result = th.get()
            if len(result) > 0:
                self.identified.emit(result[0].mLayer, result[0].mFeature, "left")
            else:
                self.identified.emit(None, None, "left")
        elif event.button() == Qt.RightButton and not self.dragging:
            th = self.ident_in_thread(event.x(), event.y())
            result = th.get()
            if len(result) > 0:
                self.identified.emit(result[0].mLayer, result[0].mFeature, "right")
            else:
                self.identified.emit(None, None, "right")

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if dlg.obj.flag_menu:
            dlg.obj.menu_hide()


class IdentMapTool(QgsMapToolIdentify):
    """Maptool do zaznaczania obiektów z wybranej warstwy."""
    identified = pyqtSignal(object, object)

    def __init__(self, canvas, layer, button):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.setCursor(Qt.CrossCursor)

    def button(self):
        return self._button

    def canvasReleaseEvent(self, event):
        result = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, self.layer, self.VectorLayer)
        if len(result) > 0:
            self.identified.emit(result[0].mLayer, result[0].mFeature)
        else:
            self.identified.emit(None, None)


class PointDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów punktowych."""
    drawn = pyqtSignal(QgsPointXY)

    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.setCursor(Qt.CrossCursor)

    def button(self):
        return self._button

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.drawn.emit(point)


class LineDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów liniowych."""
    drawn = pyqtSignal(QgsGeometry)
    move = pyqtSignal

    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.begin = True
        self.rb = QgsRubberBand(canvas, QgsWkbTypes.LineGeometry)
        self.rb.setColor(QColor(255, 0, 0, 128))
        self.rb.setFillColor(QColor(255, 0, 0, 80))
        self.rb.setWidth(1)

    def button(self):
        return self._button

    def keyPressEvent(self, e):
        # Funkcja undo - kasowanie ostatnio dodanego vertex'a po naciśnięciu ctrl+z
        if e.matches(QKeySequence.Undo) and self.rb.numberOfVertices() > 1:
            self.rb.removeLastPoint()

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.begin:
                self.rb.reset(QgsWkbTypes.LineGeometry)
                self.begin = False
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        else:
            self.rb.removeLastPoint(0)
            if self.rb.numberOfVertices() > 1:
                self.begin = True
                self.drawn.emit(self.rb.asGeometry())
                self.reset()
            else:
                self.reset()
        return None

    def canvasMoveEvent(self, e):
        if self.rb.numberOfVertices() > 0 and not self.begin:
            self.rb.removeLastPoint(0)
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        return None

    def reset(self):
        self.begin = True
        self.clearMapCanvas()

    def deactivate(self):
        super().deactivate()
        self.clearMapCanvas()

    def clearMapCanvas(self):
        self.rb.reset(QgsWkbTypes.LineGeometry)


class PolyDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów poligonalnych."""
    drawn = pyqtSignal(QgsGeometry)
    move = pyqtSignal()

    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.begin = True
        self.rb = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(QColor(255, 0, 0, 128))
        self.rb.setFillColor(QColor(255, 0, 0, 80))
        self.rb.setWidth(1)

    def button(self):
        return self._button

    def keyPressEvent(self, e):
        # Funkcja undo - kasowanie ostatnio dodanego vertex'a po naciśnięciu ctrl+z
        if e.matches(QKeySequence.Undo) and self.rb.numberOfVertices() > 1:
            self.rb.removeLastPoint()

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.begin:
                self.rb.reset(QgsWkbTypes.PolygonGeometry)
                self.begin = False
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        else:
            self.rb.removeLastPoint(0)
            if self.rb.numberOfVertices() > 2:
                self.begin = True
                self.drawn.emit(self.rb.asGeometry())
                self.reset()
            else:
                self.reset()
        return None

    def canvasMoveEvent(self, e):
        if self.rb.numberOfVertices() > 0 and not self.begin:
            self.rb.removeLastPoint(0)
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        return None

    def reset(self):
        self.begin = True
        self.clearMapCanvas()

    def deactivate(self):
        self.clearMapCanvas()

    def clearMapCanvas(self):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)


# ========== Funkcje:

def obj_sel(layer, feature, click):
    """Przekazuje do menadżera obiektów dane nowowybranego obiektu (nazwa warstwy i atrybuty obiektu)."""
    if layer:
        dlg.obj.obj_change([layer.name(), feature.attributes(), feature.geometry().asPoint()], click)
    else:
        dlg.obj.menu_hide()

def flag_add(point):
    """Utworzenie nowego obiektu flagi."""
    is_fldchk = dlg.mt.params["extra"][0]
    dlg.mt.init("multi_tool")
    fl_pow = fl_valid(point)
    if not fl_pow:
        QMessageBox.warning(None, "Tworzenie flagi", "Flagę można postawić wyłącznie na obszarze wybranego (aktywnego) powiatu/ów.")
        return
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".flagi(user_id, pow_grp, b_fieldcheck, geom) VALUES (" + str(dlg.user_id) + ", " + str(fl_pow) + ", " + is_fldchk + ", ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180))"
    if db:
        res = db.query_upd(sql)
        if res:
            print("Dodano flagę")
    QgsProject.instance().mapLayersByName("flagi_bez_teren")[0].triggerRepaint()
    QgsProject.instance().mapLayersByName("flagi_z_teren")[0].triggerRepaint()

def flag_del(layer, feature):
    """Skasowanie wybranego obiektu flagi."""
    dlg.mt.init("multi_tool")
    if layer:
        fid = feature.attributes()[layer.fields().indexFromName('id')]
    else:
        return
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".flagi WHERE id = " + str(fid) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            print("Usunięto flagę")
    QgsProject.instance().mapLayersByName("flagi_bez_teren")[0].triggerRepaint()
    QgsProject.instance().mapLayersByName("flagi_z_teren")[0].triggerRepaint()

def fl_valid(point):
    """Sprawdzenie, czy flaga znajduje się wewnątrz wybranego powiatu/ów."""
    db = PgConn()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        sql = "SELECT p.pow_grp FROM team_" + str(dlg.team_i) + ".powiaty AS p WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180), p.geom) AND p.pow_grp = '" + str(dlg.powiat_i) + "';"
    else:
        sql = "SELECT p.pow_grp FROM team_" + str(dlg.team_i) + ".powiaty AS p WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180), p.geom);"
    if db:
        res = db.query_sel(sql, False)
        if res:
            return res[0]

def wyr_add_point(point):
    """Utworzenie centroidu nowego obiektu wyrobiska."""
    if isinstance(point, QgsGeometry):
        point = point.asPoint()
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".wyrobiska(wyr_id, user_id, wyr_sys, centroid) SELECT nextval, " + str(dlg.user_id) + ", concat('" + str(dlg.team_i) + "_', nextval), ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180) FROM (SELECT nextval(pg_get_serial_sequence('team_" + str(dlg.team_i) + ".wyrobiska', 'wyr_id')) nextval) q RETURNING wyr_id"
    if db:
        res = db.query_upd_ret(sql)
        if res:
            QgsProject.instance().mapLayersByName("wyr_point")[0].triggerRepaint()
            print(res)
            return res

def wyr_add_poly(geom):
    """Utworzenie nowego obiektu wyrobiska."""
    dlg.mt.init("multi_tool")
    layer = QgsProject.instance().mapLayersByName("wyr_poly")[0]
    fields = layer.fields()
    feature = QgsFeature()
    feature.setFields(fields)
    feature.setGeometry(geom)
    wyr_id = wyr_add_point(geom.centroid())
    feature.setAttribute('wyr_id', wyr_id)
    layer.startEditing()
    layer.addFeature(feature)
    layer.commitChanges()
    QgsProject.instance().mapLayersByName("wyr_poly")[0].triggerRepaint()

def wyr_del(layer, feature):
    dlg.mt.init("multi_tool")
    if layer:
        fid = feature.attributes()[layer.fields().indexFromName('wyr_id')]
    else:
        return
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".wyrobiska WHERE wyr_id = " + str(fid) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            print("Usunięto wyrobisko")
    QgsProject.instance().mapLayersByName("wyrobiska")[0].triggerRepaint()

def auto_add(geom):
    """Utworzenie nowego obiektu parkingu."""
    dlg.mt.init("multi_tool")
    layer = QgsProject.instance().mapLayersByName("parking")[0]
    fields = layer.fields()
    feature = QgsFeature()
    feature.setFields(fields)
    feature.setGeometry(QgsGeometry.fromPointXY(geom))
    feature.setAttribute('user_id', dlg.user_id)
    feature.setAttribute('i_status', 0)
    layer.startEditing()
    layer.addFeature(feature)
    layer.commitChanges()
    iface.actionDraw().trigger()

def auto_del(layer, feature):
    """Usunięcie wybranego obiektu parkingu."""
    dlg.mt.init("multi_tool")
    if layer:
        fid = feature.attributes()[layer.fields().indexFromName('id')]
    else:
        return
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".auto WHERE id = " + str(fid) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            print("Usunięto miejsce parkowania")
    iface.actionDraw().trigger()

def marsz_add(geom):
    """Utworzenie nowego obiektu marszruty."""
    dlg.mt.init("multi_tool")
    layer = QgsProject.instance().mapLayersByName("marsz")[0]
    fields = layer.fields()
    feature = QgsFeature()
    feature.setFields(fields)
    feature.setGeometry(geom)
    feature.setAttribute('user_id', dlg.user_id)
    layer.startEditing()
    layer.addFeature(feature)
    layer.commitChanges()
    iface.actionDraw().trigger()

def marsz_del(layer, feature):
    """Usunięcie wybranego obiektu marszruty."""
    dlg.mt.init("multi_tool")
    if layer:
        fid = feature.attributes()[layer.fields().indexFromName('id')]
    else:
        return
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".marsz WHERE id = " + str(fid) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            print("Usunięto marszrutę")
    iface.actionDraw().trigger()

def lyr_ref(lyr):
    """Zwraca referencje warstw na podstawie ich nazw."""
    layer = []
    for l in lyr:
        layer.append(QgsProject.instance().mapLayersByName(l)[0])
    return layer

def wyr_poly_change(lyr, geom):
    feats = lyr.getFeatures(f'"wyr_id" = {dlg.obj.wyr}')
    feat = list(feats)[0]
    with edit(lyr):
        feat.setGeometry(geom)
        try:
            lyr.updateFeature(feat)
        except Exception as err:
            print(err)
    dlg.mt.init("multi_tool")
