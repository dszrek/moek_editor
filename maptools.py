#!/usr/bin/python
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.gui import QgsMapToolIdentify, QgsMapTool, QgsRubberBand
from qgis.core import QgsProject, QgsGeometry, QgsFeature, QgsWkbTypes, QgsPointXY, QgsExpressionContextUtils, QgsFeatureRequest, QgsRectangle
from qgis.PyQt.QtCore import Qt, pyqtSignal
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
        self.sel_id = None
        self.layers = [
            {"name" : "flagi_z_teren", "id_col" : 0},
            {"name" : "flagi_bez_teren", "id_col" : 0}
        ]

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
            {"name" : "wyr_add_poly", "class" : PolyDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_wyr_add_poly"], "fn" : wyr_add_poly}
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
        self.old_button = new_tool.button()

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
