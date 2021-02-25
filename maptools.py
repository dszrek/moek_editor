#!/usr/bin/python
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.gui import QgsMapToolIdentify, QgsMapTool, QgsRubberBand
from qgis.core import QgsApplication, QgsProject, QgsSettings, QgsGeometry, QgsVectorLayer, QgsFeature, QgsWkbTypes, QgsPointXY, QgsPoint, QgsExpressionContextUtils, QgsFeatureRequest, QgsRectangle, QgsTolerance, QgsPointLocator, edit
from qgis.PyQt.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QColor, QKeySequence, QCursor
from qgis.utils import iface
from itertools import combinations

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

    def edit_mode(self, enabled):
        """Zmiana ui pod wpływem włączenia/wyłączenia EditPolyMapTool."""
        dlg.side_dock.hide() if enabled else dlg.side_dock.show()
        dlg.bottom_dock.show() if enabled else dlg.bottom_dock.hide()


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
            try:
                self.old_button.setChecked(False)
            except:
                pass
        try:  # Maptool może nie mieć atrybutu '.button()'
            self.old_button = new_tool.button()
        except:
            self.old_button = None

    def init(self, maptool):
        """Zainicjowanie zmiany maptool'a."""
        if maptool == "multi_tool" and self.mt_name == "multi_tool":  # Zablokowanie próby wyłączenia multi_tool'a
            self.dlg.side_dock.toolboxes["tb_multi_tool"].widgets["btn_multi_tool"].setChecked(True)
            return
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
        dp = lyr.dataProvider()
        dp.truncate()
        pg = 0  # Numer poligonu
        with edit(lyr):  # Ekstrakcja poligonów
            for poly in geom.asMultiPolygon():
                feat = QgsFeature(lyr.fields())
                feat.setAttribute("part", pg)
                feat.setGeometry(QgsGeometry.fromPolygonXY(poly))
                dp.addFeature(feat)
                lyr.updateExtents()
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
    mode_changed = pyqtSignal(str)
    cursor_changed = pyqtSignal(str)
    node_selected = pyqtSignal(bool)
    area_hover = pyqtSignal(int)
    valid_changed = pyqtSignal(bool)
    ending = pyqtSignal(QgsVectorLayer, QgsGeometry)

    def __init__(self, canvas, layer, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.layer = layer
        self.start_point = None
        self.dragging = False
        self.moving = False
        self.refreshing = False
        self.drawing = False
        self.move_void = False
        self.snap_void = False
        self.geom = None
        self.init_extent = self.canvas.extent()
        self.a_temp = -1
        self.area_idx = -1
        self.part_idx = -1
        self.node_presel = []
        self.node_sel = False
        self.node_idx = (-1, -1)
        self.prev_node = None
        self.area_rbs = []
        self.vertex_rbs = []
        self.change_is_valid = True
        self.valid_changed.connect(self.valid_change)
        self.flash = 0
        self.edit_layer = QgsProject.instance().mapLayersByName("edit_poly")[0]
        self.snap_settings()
        self.rbs_create()
        self.rbs_populate()
        self.mode_changed.connect(self.mode_change)
        self.mode = "edit"
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "open_hand"
        self.node_selected.connect(self.node_sel_change)
        self.area_hover.connect(self.area_hover_change)
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool"].clicked.connect(self.edit_clicked)
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_add"].clicked.connect(self.add_clicked)
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_sub"].clicked.connect(self.sub_clicked)
        dlg.obj.edit_mode(True)  # Zmiana ui przy wejściu do trybu edycji geometrii wyrobiska
        self.zoom_to_geom()  # Przybliżenie widoku mapy do geometrii wyrobiska

    def zoom_to_geom(self):
        """Przybliżenie widoku mapy do granic wyrobiska."""
        # Określenie zasięgu warstwy:
        box = None
        for feat in self.edit_layer.getFeatures():
            if not box:
                box = feat.geometry().boundingBox()
            else:
                box.combineExtentWith(feat.geometry().boundingBox())
        # Określenie nowego zasięgu widoku mapy:

        w_off = box.width() * 0.4
        h_off = box.height() * 0.4
        ext = QgsRectangle(box.xMinimum() - w_off,
                            box.yMinimum() - h_off,
                            box.xMaximum() + w_off,
                            box.yMaximum() + h_off
                            )
        self.canvas.setExtent(ext)

    def snap_settings(self):
        """Zmienia globalne ustawienia snappingu."""
        s = QgsSettings()
        s.setValue('/qgis/digitizing/default_snap_type', 'VertexAndSegment')
        s.setValue('/qgis/digitizing/search_radius_vertex_edit', 12)
        s.setValue('/qgis/digitizing/search_radius_vertex_edit_unit', 'Pixels')

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)
        if attr == "mode":
            self.mode_changed.emit(val)
        if attr == "area_idx":
            self.area_hover.emit(val)
        if attr == "node_sel":
            self.node_selected.emit(val)
        if attr == "change_is_valid":
            self.valid_changed.emit(val)

    def mode_change(self, mode_name):
        """Zmiana trybu maptool'a."""
        modes = [
                ["edit", dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool"]],
                ["add", dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_add"]],
                ["sub", dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_sub"]]
                ]
        if self.area_painter:
            self.area_painter.reset(QgsWkbTypes.PolygonGeometry)
        self.node_idx = (-1, -1)
        self.node_sel = False
        self.start_point = None
        for mode in modes:
            if mode[0] == mode_name and not mode[1].isChecked():
                mode[1].setChecked(True)
            elif mode[0] != mode_name:
                mode[1].setChecked(False)
            if mode_name == "add":
                self.area_painter.setColor(QColor(0, 255, 0, 128))
                self.area_painter.setFillColor(QColor(0, 255, 0, 80))
            elif mode_name == "sub":
                self.area_painter.setColor(QColor(255, 0, 0, 128))
                self.area_painter.setFillColor(QColor(255, 0, 0, 80))

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["arrow", Qt.ArrowCursor],
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor],
                    ["cross", Qt.CrossCursor],
                    ["move", Qt.SizeAllCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def edit_clicked(self):
        """Kliknięcie na przycisk btn_edit_tool."""
        btn = dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool"]
        if btn.isChecked():
            self.mode = "edit"
        else:
            self.mode = "edit"

    def add_clicked(self):
        """Kliknięcie na przycisk btn_edit_tool_add."""
        btn = dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_add"]
        if btn.isChecked():
            self.mode = "add"
        else:
            self.mode = "edit"

    def sub_clicked(self):
        """Kliknięcie na przycisk btn_edit_tool_sub."""
        btn = dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_sub"]
        if btn.isChecked():
            self.mode = "sub"
        else:
            self.mode = "edit"

    def node_sel_change(self, _bool):
        """Zmiana zaznaczonego node'a."""
        if not self.node_selector:
            return
        if _bool:
            self.node_idx = self.get_node_index()
            self.node_selector.movePoint(self.node_presel[0], 0)
            self.node_selector.setVisible(True)
        else:
            self.node_idx = (-1, -1)
            self.node_selector.setVisible(False)
        self.area_hover_change(self.area_idx)

    def selector_update(self):
        """Przywrócenie node_selector'a po ponownym wczytaniu rubberband'ów."""
        if self.node_idx[0] < 0:
            return
        geom = self.vertex_rbs[self.node_idx[0]].asGeometry()
        node = list(geom.vertices())[self.node_idx[1]]
        self.node_selector.movePoint(QgsPointXY(node.x(), node.y()))
        self.node_selector.setVisible(True)

    def area_hover_change(self, part):
        """Zmiana podświetlenia poligonów."""
        if part < 0:
            self.area_marker.setVisible(False)
        else:
            self.area_marker.reset(QgsWkbTypes.PolygonGeometry)
            try:
                self.area_marker.addGeometry(self.area_rbs[part].asGeometry())
                self.area_marker.setVisible(True)
            except Exception as err:
                print(err)
        for i in range(len(self.vertex_rbs)):
            if self.node_idx[0] == i or self.area_idx == i:
                self.vertex_rbs[i].setVisible(True)
            else:
                self.vertex_rbs[i].setVisible(False)

    def valid_change(self, _bool):
        """Zmiana poprawności geometrii rubberband'a, w trakcie przemieszczania wierzchołka lub rysowania area_painter'a."""
        if self.mode == "edit":
            self.line_helper.setColor(QColor(255, 255, 0, 255)) if _bool else self.line_helper.setColor(QColor(255, 0, 0, 255))
            self.node_selector.setFillColor(QColor(255, 255, 0, 255)) if _bool else self.node_selector.setFillColor(QColor(255, 0, 0, 255))
        elif self.mode == "add":
            self.area_painter.setFillColor(QColor(0, 255, 0, 80)) if _bool else self.area_painter.setFillColor(QColor(0, 0, 0, 80))
        elif self.mode == "sub":
            self.area_painter.setFillColor(QColor(255, 0, 0, 80)) if _bool else self.area_painter.setFillColor(QColor(0, 0, 0, 80))

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        for i in range(self.edit_layer.featureCount()):
            _vrb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
            _vrb.setIcon(QgsRubberBand.ICON_CIRCLE)
            _vrb.setColor(QColor(255, 255, 0, 0))
            _vrb.setFillColor(QColor(255, 255, 0, 128))
            _vrb.setIconSize(10)
            _vrb.setVisible(False)
            self.vertex_rbs.append(_vrb)
            _arb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            _arb.setWidth(1)
            _arb.setColor(QColor(255, 255, 0, 255))
            _arb.setFillColor(QColor(255, 255, 0, 28))
            _arb.setVisible(True)
            self.area_rbs.append(_arb)

        self.valid_checker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.valid_checker.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.valid_checker.setColor(QColor(0, 0, 0, 0))
        self.valid_checker.setFillColor(QColor(0, 0, 0, 0))
        self.valid_checker.setIconSize(1)
        self.valid_checker.setVisible(False)

        self.line_helper = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.line_helper.setWidth(2)
        self.line_helper.setColor(QColor(255, 255, 0, 255))
        self.line_helper.setLineStyle(Qt.DotLine)
        self.line_helper.setVisible(False)

        self.area_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.area_marker.setWidth(2)
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

        self.node_hover = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_hover.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_hover.setColor(QColor(0, 0, 0, 255))
        self.node_hover.setFillColor(QColor(255, 255, 0, 128))
        self.node_hover.setIconSize(10)
        self.node_hover.addPoint(QgsPointXY(0, 0), False)
        self.node_hover.setVisible(False)

        self.node_selector = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_selector.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_selector.setColor(QColor(0, 0, 0, 255))
        self.node_selector.setFillColor(QColor(255, 255, 0, 255))
        self.node_selector.setIconSize(12)
        self.node_selector.addPoint(QgsPointXY(0, 0), False)
        self.node_selector.setVisible(False)

        self.area_painter = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.area_painter.setColor(QColor(0, 255, 0, 128))
        self.area_painter.setFillColor(QColor(0, 255, 0, 80))
        self.area_painter.setWidth(1)
        self.area_painter.setVisible(False)

        self.node_valider = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_valider.setIcon(QgsRubberBand.ICON_FULL_DIAMOND)
        self.node_valider.setColor(QColor(255, 0, 0, 255))
        self.node_valider.setFillColor(QColor(0, 0, 0, 255))
        self.node_valider.setIconSize(12)
        self.node_valider.setVisible(False)

        self.area_valider = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.area_valider.setColor(QColor(255, 0, 0, 255))
        self.area_valider.setFillColor(QColor(0, 0, 0, 255))
        self.area_valider.setWidth(3)
        self.area_valider.setVisible(False)

    def rbs_populate(self):
        """Załadowanie poligonów i punktów do rubberband'ów."""
        for i in range(len(self.area_rbs)):
            geom = self.get_geom_from_part(i)
            poly = geom.asPolygon()[0]
            for j in range(len(poly) - 1):
                self.area_rbs[i].addPoint(poly[j])
                self.vertex_rbs[i].addPoint(poly[j])
            self.vertex_rbs[i].setVisible(False)

    def snap_to_layer(self, event):
        """Zwraca wyniki przyciągania do wierzchołków, krawędzi i powierzchni."""
        self.canvas.snappingUtils().setCurrentLayer(self.edit_layer)
        v = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Vertex)
        e = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Edge)
        a = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Area)
        return v, e, a

    def canvasMoveEvent(self, event):
        if self.move_void:
            self.move_void = False
            return
        v, e, a = self.snap_to_layer(event)
        snap_type = v.type() + e.type() + a.type()
        map_point = self.toMapCoordinates(event.pos())
        if event.buttons() == Qt.LeftButton and not self.refreshing:
            if self.mode == "edit":
                self.dragging = True
            else:
                # Umożliwienie panningu mapy podczas rysowania area_painter'a:
                dist = QgsGeometry().fromPointXY(self.start_point).distance(QgsGeometry().fromPointXY(map_point))
                dist_scale = dist / self.canvas.scale() * 1000
                self.dragging = True if dist_scale > 6.0 else False
            if self.node_presel and self.mode == "edit":  # Przesunięcie wierzchołka
                if not self.moving:
                    self.change_is_valid = True
                    self.node_sel = True
                    self.moving = True
                    self.cursor = "move"
                    self.valid_checker_create()
                    self.line_create()
                self.node_selector.movePoint(map_point)
                self.line_helper.movePoint(1, map_point)
                self.valid_check(map_point)
            elif self.edge_marker.isVisible() and not self.moving and self.mode == "edit":
                # Szybkie dodanie wierzchołka:
                self.node_add(map_point)
                self.geom_refresh(True)
                self.node_presel = [map_point, self.part_idx]
                self.node_sel = True
                self.move_void = True
            elif self.dragging:  # Panning mapy
                self.cursor = "closed_hand"
                self.canvas.panAction(event)
        elif (event.button() == Qt.NoButton and not self.dragging) or self.refreshing:
            # Odświeżanie rubberband'ów po zmianie geometrii:
            if self.refreshing:
                self.mouse_move_emit(True)
                self.refreshing = False
            # Rysowanie area_painter:
            if self.drawing and not self.dragging and self.area_painter.numberOfVertices() > 0:
                if self.snap_void:  # Zapobiega usunięciu punktu utworzonego z przyciąganiem
                    self.snap_void = False
                else:
                    self.area_painter.removeLastPoint(0)
                self.area_painter.addPoint(map_point)
                if self.area_painter.numberOfVertices() > 2:
                    self.valid_check(map_point, area_rb=self.area_painter, poly_check=False, node_check=True)
            if self.a_temp != a.featureId():
                self.a_temp = a.featureId()
                self.part_idx = self.get_part_from_id(a.featureId())
                self.area_idx = -1
            if snap_type == 0:  # Kursor poza poligonami, brak obiektów do przyciągnięcia
                if self.mode == "edit" and self.cursor != "open_hand":
                    self.cursor = "open_hand"
                if self.node_presel:
                    self.node_presel = []
                self.node_hover.setVisible(False) #if self.node_sel else self.node_hover.setVisible(False)
                self.edge_marker.setVisible(False)
                if self.area_idx != -1:
                    self.area_idx = -1
            elif snap_type == 4:  # Kursor w obrębie poligonu
                if self.mode == "edit" and self.cursor != "open_hand":
                    self.cursor = "open_hand"
                if self.node_presel:
                    self.node_presel = []
                self.node_hover.setVisible(False)
                self.edge_marker.setVisible(False)
                if self.area_idx != self.part_idx:
                    self.area_idx = self.part_idx
            elif snap_type == 5 or snap_type == 7:  # Wierzchołek do przyciągnięcia
                if self.mode == "edit" and self.cursor != "arrow":
                    self.cursor = "arrow"
                self.node_presel = [v.point(), e.featureId()]
                self.node_hover.movePoint(v.point(), 0)
                self.node_hover.setVisible(True)
                self.edge_marker.setVisible(False)
                if self.area_idx != self.part_idx:
                    self.area_idx = self.part_idx
            elif snap_type == 6:  # Krawędź do przyciągnięcia
                if self.cursor != "cross":
                    self.cursor = "cross"
                    if self.prev_node != e.edgePoints()[0]:
                        self.prev_node = e.edgePoints()[0]
                if self.node_presel:
                    self.node_presel = []
                self.edge_marker.movePoint(e.point(), 0)
                if self.mode == "edit":
                    self.edge_marker.setVisible(True)
                self.node_hover.setVisible(False)
                if self.area_idx != self.part_idx:
                    self.area_idx = self.part_idx
            if self.mode != "edit" and self.cursor != "cross":
                self.cursor = "cross"

    def canvasPressEvent(self, event):
        if self.mode != "edit" and event.button() == Qt.LeftButton and not self.dragging:
            self.start_point = self.toMapCoordinates(event.pos())
            if not self.drawing:
                self.drawing = True
                self.change_is_valid = True
            if self.node_presel:
                self.area_painter.removeLastPoint(0)
                snapped_point = self.node_presel[0]
                self.area_painter.addPoint(snapped_point)
                self.snap_void = True
            else:
                self.area_painter.addPoint(self.toMapCoordinates(event.pos()))
        elif self.mode != "edit" and event.button() == Qt.RightButton and not self.dragging:
            if self.drawing:
                if not self.snap_void:
                    self.area_painter.removeLastPoint(0)
                if self.area_painter.numberOfVertices() > 2:
                    self.area_drawn()
            self.geom_refresh()
            self.drawing = False
            self.mode = "edit"
        elif self.mode == "edit" and event.button() == Qt.RightButton and not self.dragging:
            self.reset()

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.dragging:
            if self.mode == "edit":
                if self.node_presel:
                    self.node_sel = True  # Zaznaczenie wierzchołka
                else:
                    self.node_sel = False  # Odzaznaczenie wierzchołka
        elif event.button() == Qt.LeftButton and self.dragging:
            # Przemieszczenie wierzchołka:
            if self.moving:
                map_point = self.toMapCoordinates(event.pos())
                if self.change_is_valid:
                    self.vertex_rbs[self.node_idx[0]].movePoint(self.node_idx[1], map_point)
                else:
                    self.change_is_valid = True
                self.geom_refresh()
                self.selector_update()
                self.moving = False
            # Panning mapy:
            else:
                # Panning podczas rysowania area_painter'a:
                if self.drawing and self.area_painter.numberOfVertices() > 0:
                    self.area_painter.removeLastPoint(0)
                self.canvas.panActionEnd(event.pos())
            self.dragging = False
            self.cursor = "open_hand"
        # elif event.button() == Qt.RightButton and not self.dragging:
        #     if self.mode == "edit":
        #         self.reset()

    def canvasDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self.dragging and self.mode == "edit":
            if self.edge_marker.isVisible():
                # Ustalenie lokalizacji nowego wierzchołka:
                geom = self.edge_marker.asGeometry()
                p_list = list(geom.vertices())
                p_last = len(p_list) - 1
                self.node_add(p_list[p_last])
                self.geom_refresh()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            event.ignore()  # Przerwanie domyślnego działania skrótu klawiszowego
            if self.node_sel and self.mode == "edit":
                self.vertex_delete()  # Skasowanie wierzchołka
        elif event.key() == Qt.Key_Escape:
            if self.dragging:
                pass  # TODO
                # self.stop_dragging()
        elif self.mode != "edit" and event.matches(QKeySequence.Undo) and self.area_painter.numberOfVertices() > 1:
            self.area_painter.removeLastPoint()

    def mouse_move_emit(self, after=False):
        """Sposób na odpalenie canvasMoveEvent."""
        cursor = QCursor()
        pos = self.canvas.mouseLastXY()
        global_pos = self.canvas.mapToGlobal(pos)
        if after:
            # Blokada canvasMoveEvent, żeby przypadkiem nie przemieścić nowego wierzchołka:
            self.move_void = True
            # Przywrócenie pierwotnej pozycji kursora:
            cursor.setPos(global_pos.x() + 2, global_pos.y() + 2)
        else:
            # Nieznaczne przesunięcie kursora, żeby odpalić canvasMoveEvent:
            self.refreshing = True
            cursor.setPos(global_pos.x(), global_pos.y())

    def area_drawn(self):
        if not self.change_is_valid:
            return
        new_poly = self.area_painter.asGeometry()
        overlaps = self.overlap_check(new_poly)
        if self.mode == "add":
            if len(overlaps[0]) == 0:  # Geometria area_painter nie przecina się z żadnym poligonem
                if len(overlaps[1]) > 0:
                    # Geometria area_painter dotyka wierzchołkiem(-kami) choć jeden poligon -
                    # prowadzi to do powstania błędnej topologii - rezygnacja z dodawania obszaru
                    pass
                else:
                    # Geometria area_painter nie dotyka żadnego poligonu-
                    # rysowanie nowego poligonu:
                    self.part_add(new_poly)
            else:
                # Geometria area_painter łączy się z przynajmniej jednym poligonem -
                # łączenie poligonów z listy overlaps i area_painter w jeden poligon:
                self.parts_combine(new_poly, overlaps[0])

    def part_add(self, new_poly):
        """Dodanie nowego poligonu do geometrii."""
        _vrb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.vertex_rbs.append(_vrb)
        poly = new_poly.asPolygon()[0]
        i = len(self.vertex_rbs) - 1
        for j in range(len(poly) - 1):
            self.vertex_rbs[i].addPoint(poly[j])

    def parts_combine(self, new_poly, overlaps):
        """Utworzenie nowej geometrii z połączenia wybranych poligonów i aktualizacja listy vertex_rbs."""
        combined_poly = self.polygon_from_parts(new_poly, overlaps)
        if not combined_poly:
            print("Wystąpił błąd przy złączaniu geometrii!")
            return
        # Usunięcie zbędnych rubberband'ów z listy vertex_rbs:
        for i in sorted(overlaps, reverse=True):
            self.area_rbs[i].reset(QgsWkbTypes.PolygonGeometry)
            del self.area_rbs[i]  # Usunięcie area rubberband'a z listy
            self.vertex_rbs[i].reset(QgsWkbTypes.PointGeometry)
            del self.vertex_rbs[i]  # Usunięcie vertex rubberband'a z listy
        # Utworzenie rubberband'a ze złączonej geometrii:
        self.part_add(combined_poly)

    def polygon_from_parts(self, new_poly, overlaps):
        """Złączenie geometrii area_painter i poligonów o id podanych na liście 'overlaps'."""
        for i in range(len(self.area_rbs)):
            if i in overlaps:  # Poligon znajduje się na liście
                poly = self.area_rbs[i].asGeometry()
                # Sprawdzenie, czy geometria jest poprawna:
                err = poly.validateGeometry()
                if not err:
                    new_poly = new_poly.combine(poly)
                else:
                    return None
        return new_poly

    def segments_from_polygon(self, poly):
        """Zwraca listę boków poligonu."""
        segments = []
        poly = poly.asPolygon()[0]
        for i in range(len(poly) - 1):
            line = QgsGeometry().fromPolylineXY([poly[i], poly[i + 1]])
            segments.append(line)
        return segments

    def valid_check(self, map_point, remove=False, area_rb=None, poly_check=True, node_check=False):
        """Sprawdza, czy geometria po przemieszczeniu wierzchołka jest prawidłowa lub nachodzi na inny poligon."""
        is_valid = True  # Wstępne założenie, że geometria jest poprawna
        # Kasowanie poprzednich stanów rubberband'ów:
        self.node_valider.reset(QgsWkbTypes.PointGeometry)
        self.area_valider.reset(QgsWkbTypes.PolygonGeometry)
        if not area_rb:  # Nie wskazano rubberband'a do walidacji - użyty jest valid_checker
            # Aktualizacja geometrii valid_checker'a:
            if remove:
                self.valid_checker.removePoint(map_point, True)
            else:
                self.valid_checker.movePoint(self.node_idx[1], map_point)
            rb = self.valid_checker.asGeometry()
            rb_geom = self.get_geom_from_vertex_rb(rb)
        else:
            rb_geom = area_rb.asGeometry()
            rb = self.get_nodes_from_area_rb(rb_geom)
        # Sprawdzenie, czy nowa geometria jest poprawna:
        rb_check = self.rubberband_check(rb_geom)
        if not rb_check:  # Nowa geometria nie jest poprawna - pokazanie błędnych punktów
            # Stworzenie listy z wierzchołkami valid_checker'a:
            rb_nodes = []
            nodes = rb.constParts() if not area_rb else rb
            for node in nodes:
                rb_nodes.append(QgsPointXY(node.x(), node.y()))
            # Stworzenie listy z liniami boków valid_checker'a:
            segments = self.segments_from_polygon(rb_geom)
            # Sprawdzenie, czy któreś linie się przecinają -
            # wykluczone są przecięcia na wierzchołkach:
            pairs = list(combinations(segments, 2))
            for p in pairs:
                intersect_geom = p[0].intersection(p[1])
                if intersect_geom and intersect_geom.type() == QgsWkbTypes.PointGeometry:
                    if not intersect_geom.asPoint() in rb_nodes:
                        # Pokazanie błędnych przecięć:
                        self.node_valider.addPoint(intersect_geom.asPoint())
            is_valid = False
            rb_geom = rb_geom.makeValid()  # Inaczej nie będzie można spawdzić przecięcia z innymi poligonami
        # Sprawdzenie, czy nowa geometria styka się z innymi poligonami tylko na wierzchołkach:
        if node_check:
            overlaps = self.overlap_check(rb_geom)
            # Area_painter styka się z innymi poligonami wyłącznie na wierzchołkach:
            if len(overlaps[1]) > 0:
                # Pokazanie nałożonych wierzchołków:
                for point in overlaps[1]:
                    self.node_valider.addPoint(point.asPoint())
                is_valid = False
        # Sprawdzenie, czy nowa geometria przecina się z innymi poligonami:
        if poly_check:
            for i in range(len(self.area_rbs)):
                if i == self.node_idx[0]:  # Wykluczenie aktualnie edytowanego poligonu
                    continue
                poly = self.area_rbs[i].asGeometry()
                overlap_geom = rb_geom.intersection(poly).asGeometryCollection()
                for geom in overlap_geom:
                    if geom and geom.type() == QgsWkbTypes.PolygonGeometry:
                        # Pokazanie błędnych powierzchni:
                        self.area_valider.addGeometry(geom)
                        is_valid = False
        self.change_is_valid = is_valid

    def rubberband_check(self, geom):
        """Zwraca geometrię, jesli jest poprawna."""
        return geom if geom.isGeosValid() else None

    def overlap_check(self, new_poly):
        """Zwraca id poligonów, które przecinają się z geometrią area_painter'a i listę wierzchołków, jeśli są jedynymi połączeniami z danym poligonem."""
        overlaps = []
        touches = []
        for i in range(len(self.area_rbs)):
            poly = self.area_rbs[i].asGeometry()
            overlap_geom = new_poly.intersection(poly).asGeometryCollection()
            appended = False
            for geom in overlap_geom:
                if geom.type() == QgsWkbTypes.PolygonGeometry or geom.type() == QgsWkbTypes.LineGeometry:
                    if geom and not appended:
                        appended = True
                        overlaps.append(i)
                elif geom.type() == QgsWkbTypes.PointGeometry:
                    if geom:
                        touches.append(geom)
        return overlaps, touches

    def node_add(self, point):
        """Utworzenie nowego wierzchołka w poligonie."""
        new_node = QgsPointXY(point.x(), point.y())
        rb = self.vertex_rbs[self.area_idx]
        geom = rb.asGeometry()
        p_list = list(geom.vertices())
        rb.reset(QgsWkbTypes.PointGeometry)
        s = -1
        for i in range(len(p_list)):
            node = QgsPointXY(p_list[i].x(), p_list[i].y())
            if node == self.prev_node:
                s = s + i
                rb.addPoint(node)
                rb.addPoint(new_node)
            else:
                rb.addPoint(node)

    def valid_checker_create(self):
        """Tworzy tymczasową kopię rubberband'a, którego wierzchołek będzie przesuwany."""
        if self.valid_checker:
            self.valid_checker.reset(QgsWkbTypes.PointGeometry)
        for i in range(self.vertex_rbs[self.node_idx[0]].numberOfVertices()):
            self.valid_checker.addPoint(self.vertex_rbs[self.node_idx[0]].getPoint(0, i))
        self.valid_checker.setVisible(False)

    def line_create(self):
        """Utworzenie i wyświetlenie linii pomocniczej przy przesuwaniu wierzchołka."""
        part = self.node_idx[0]
        node = self.node_idx[1]
        node_cnt = self.vertex_rbs[part].numberOfVertices() - 1
        if node == 0:  # Zaznaczony jest pierwszy wierzchołek
            picked_nodes = [node_cnt, node, node + 1]
        elif node == node_cnt:  # Zaznaczony jest ostatni wierzchołek
            picked_nodes = [node - 1, node, 0]
        else:
            picked_nodes = [node -1, node, node + 1]
        line_points = self.get_points_from_indexes(part, picked_nodes)
        self.line_helper.reset(QgsWkbTypes.LineGeometry)
        for p in line_points:
            self.line_helper.addPoint(p)
        self.line_helper.setVisible(True)

    def geom_refresh(self, no_move=False):
        """Aktualizacja warstwy i rubberband'ów po zmianie geometrii."""
        self.geom_update()  # Aktualizacja geometrii na warstwie
        self.rbs_clear()  # Skasowanie rubberband'ów
        self.rbs_create()  # Utworzenie nowych rubberband'ów
        self.rbs_populate()  # Załadowanie geometrii do rubberband'ów
        if no_move:
            self.area_hover_change(self.area_idx)
        else:
            self.mouse_move_emit()  # Sztuczne odpalenie canvasMoveEvent, żeby odpowiednio wyświetlić rubberband'y

    def get_part_from_id(self, id):
        """Zwraca atrybut 'part' poligonu o numerze id."""
        for feat in self.edit_layer.getFeatures():
            if feat.id() == id:
                return feat.attribute("part")
        return None

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
        """Zwraca index punktu i poligonu, znajdującego się pod node_selector'em."""
        i = 0
        point = self.node_presel[0]
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

    def get_nodes_from_vertex_rb(self, rb):
        """Zwraca punkty z punktowego rubberband'u."""
        pts = []
        for part in rb.constParts():
            pts.append(part)
        return pts

    def get_nodes_from_area_rb(self, rb):
        """Zwraca punkty z poligonalnego rubberband'u."""
        pts = []
        for vertex in rb.vertices():
            pts.append(vertex)
        return pts

    def get_points_from_indexes(self, part, nodes):
        """Zwraca punkty wybranego poligonu na podstawie ich indeksów."""
        pts = []
        geom = self.vertex_rbs[part].asGeometry()
        p_list = list(geom.vertices())
        for node in nodes:
            pt = p_list[node]
            pts.append(QgsPointXY(pt.x(), pt.y()))
        return pts

    def vertex_delete(self):
        """Usuwa zaznaczony wierzchołek poligonu."""
        if self.node_idx[0] < 0:
            print("brak zaznaczonego wierzchołka")
            return
        if self.vertex_rbs[self.node_idx[0]].numberOfVertices() > 3:
            self.valid_checker_create()
            self.valid_check(self.node_idx[1], remove=True, node_check=True)
            if self.change_is_valid:
                self.vertex_rbs[self.node_idx[0]].removePoint(self.node_idx[1], True)
                self.after_vertex_delete()
            else:
                self.move_is_valid = True
                self.selector_update()
                self.line_create()
                self.line_helper.setFillColor(QColor(255, 0, 0, 255))
                self.line_helper.removePoint(1, True)
                self.node_flasher()
        else:
            self.vertex_rbs[self.node_idx[0]].reset(QgsWkbTypes.PointGeometry)
            del self.vertex_rbs[self.node_idx[0]]
            self.node_idx = (-1, -1)
            self.node_sel = False
            self.geom_refresh(True)

    def after_vertex_delete(self):
        """Aktualizacja rubberband'ów po próbie usunięcia wierzchołka."""
        # Zmiana numeru zaznaczonego wierzchołka, jeśli został usunięty ostatni:
        if self.node_idx[1] > self.vertex_rbs[self.node_idx[0]].numberOfVertices() - 1:
            self.node_idx = (self.node_idx[0], self.node_idx[1] - 1)
        self.geom_refresh(True)
        self.selector_update()

    def node_flasher(self):
        """Efekt graficzny mrugania punktu."""
        # Przerwanie poprzedniego flash'a, jeśli jeszcze trwa:
        try:
            self.timer.stop()
            self.timer.deleteLater()
        except:
            pass
        # Stworzenie stopera i jego odpalenie:
        self.timer = QTimer(self, interval=150)
        self.timer.timeout.connect(self.flash_change)
        self.timer.start()  # Odpalenie stopera

    def flash_change(self):
        """Zmienia kolor node_selector'a."""
        if self.flash > 1:
            self.flash = 0
            self.timer.stop()
            self.timer.deleteLater()
            self.after_vertex_delete()
            return
        else:
            self.flash += 1
            self.node_selector.setVisible(True) if (self.flash % 2) == 0 else self.node_selector.setVisible(False)

    def geom_update(self):
        """Aktualizacja geometrii poligonów po jej zmianie."""
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
        self.canvas.setExtent(self.init_extent)
        dlg.obj.edit_mode(False)
        self.ending.emit(self.layer, self.geom)

    def rbs_clear(self):
        for a in self.area_rbs:
            a.reset(QgsWkbTypes.PolygonGeometry)
        for v in self.vertex_rbs:
            v.reset(QgsWkbTypes.PointGeometry)
        self.area_rbs = []
        self.vertex_rbs = []
        self.valid_checker.reset(QgsWkbTypes.PointGeometry)
        self.node_valider.reset(QgsWkbTypes.PointGeometry)
        self.area_valider.reset(QgsWkbTypes.PolygonGeometry)
        self.line_helper.reset(QgsWkbTypes.LineGeometry)
        self.node_hover.reset(QgsWkbTypes.PointGeometry)
        self.node_selector.reset(QgsWkbTypes.PointGeometry)
        self.edge_marker.reset(QgsWkbTypes.PointGeometry)
        self.area_marker.reset(QgsWkbTypes.PolygonGeometry)
        self.area_painter.reset(QgsWkbTypes.PolygonGeometry)
        self.valid_checker = None
        self.node_valider = None
        self.area_valider = None
        self.line_helper = None
        self.node_hover = None
        self.node_selector = None
        self.edge_marker = None
        self.area_marker = None
        # self.area_painter = None
        # self.area_painter.deleteLater()


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
