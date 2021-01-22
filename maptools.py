#!/usr/bin/python

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.gui import QgsMapToolIdentify, QgsMapTool, QgsRubberBand
from qgis.core import QgsProject, QgsGeometry, QgsFeature, QgsWkbTypes, QgsPointXY
from qgis.PyQt.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence
from qgis.utils import iface

from .classes import PgConn
from .viewnet import vn_change, vn_powsel, vn_polysel

dlg = None

def dlg_maptools(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

class MapToolManager():
    """Menadżer maptool'ów."""
    def __init__(self, dlg, canvas):
        self.maptool = None  # Instancja klasy maptool'a
        self.mt_name = None  # Nazwa maptool'a
        self.params = {}  # Słownik z parametrami maptool'a
        self.dlg = dlg  # Referencja do wtyczki
        self.canvas = canvas
        self.maptools = [
            {"name" : "vn_sel", "class" : IdentMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_sel"], "lyr" : ["vn_user"], "fn" : vn_change},
            {"name" : "vn_powsel", "class" : IdentMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_powsel"], "lyr" : ["powiaty"], "fn" : vn_powsel},
            {"name" : "vn_polysel", "class" : PolyDrawMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_polysel"], "fn" : vn_polysel},
            {"name" : "flt_add", "class" : PointDrawMapTool, "button" : self.dlg.p_flag.widgets["btn_flag_fchk"], "fn" : flag_add, "extra" : ['true']},
            {"name" : "flf_add", "class" : PointDrawMapTool, "button" : self.dlg.p_flag.widgets["btn_flag_nfchk"], "fn" : flag_add, "extra" : ['false']},
            {"name" : "flag_del", "class" : IdentMapTool, "button" : self.dlg.p_flag.widgets["btn_flag_del"], "lyr" : ["flagi_z_teren", "flagi_bez_teren"], "fn" : flag_del},
            {"name" : "wyr_add", "class" : PolyDrawMapTool, "button" : self.dlg.p_wyr.widgets["btn_wyr_add"], "fn" : wyr_add},
            {"name" : "wyr_del", "class" : IdentMapTool, "button" : self.dlg.p_wyr.widgets["btn_wyr_del"], "lyr" : ["wyrobiska"], "fn" : wyr_del},
            {"name" : "auto_add", "class" : PointDrawMapTool, "button" : self.dlg.p_auto.widgets["btn_auto_add"], "fn" : auto_add},
            {"name" : "auto_del", "class" : IdentMapTool, "button" : self.dlg.p_auto.widgets["btn_auto_del"], "lyr" : ["parking"], "fn" : auto_del},
            {"name" : "marsz_add", "class" : LineDrawMapTool, "button" : self.dlg.p_auto.widgets["btn_marsz_add"], "fn" : marsz_add},
            {"name" : "marsz_del", "class" : IdentMapTool, "button" : self.dlg.p_auto.widgets["btn_marsz_del"], "lyr" : ["marsz"], "fn" : marsz_del}
        ]

    def init(self, maptool):
        """Zainicjowanie zmiany maptool'a."""
        # print(f"mt: {self.mt_name}")
        if not self.mt_name:  # Nie ma obecnie uruchomionego maptool'a
            self.tool_on(maptool)  # Włączenie maptool'a
        else:
            mt_old = self.mt_name
            self.tool_off()  # Wyłączenie obecnie uruchomionego maptool'a
            if mt_old != maptool:  # Inny maptool był włączony
                self.tool_on(maptool)  # Włączenie nowego maptool'a

    def tool_on(self, maptool):
        """Włączenie maptool'a."""
        self.params = self.dict_name(maptool)  # Wczytanie parametrów maptool'a
        if "lyr" in self.params:
            lyr = self.lyr_ref(self.params["lyr"])
        if self.params["class"] == IdentMapTool:
            self.maptool = self.params["class"](self.canvas, lyr)
            self.maptool.identified.connect(self.params["fn"])
        else:
            self.maptool = self.params["class"](self.canvas)
            self.maptool.drawn.connect(self.params["fn"])
        self.canvas.setMapTool(self.maptool)
        self.mt_name = self.params["name"]

    def tool_off(self):
        """Wyłączenie maptool'a."""
        if not self.maptool:  # Nie ma aktywnego maptool'a
            return
        # self.params = self.dict_name(self.mt_name)  # Wczytanie parametrów maptool'a
        self.params["button"].setChecked(False)
        self.canvas.unsetMapTool(self.maptool)
        self.maptool = None
        self.mt_name = None
        self.params = {}

    def lyr_ref(self, lyr):
        """Zwraca referencje warstw na podstawie ich nazw."""
        layer = []
        for l in lyr:
            layer.append(QgsProject.instance().mapLayersByName(l)[0])
        return layer

    def dict_name(self, maptool):
        """Wyszukuje na liście wybrany toolmap na podstawie nazwy i zwraca słownik z jego parametrami."""
        for tool in self.maptools:
            if tool["name"] == maptool:
                return tool


class IdentMapTool(QgsMapToolIdentify):
    """Maptool do zaznaczania obiektów z wybranej warstwy."""
    identified = pyqtSignal(object, object)

    def __init__(self, canvas, layer):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        # if type(layer) is list:
        #     self.layer = layer
        # else:
        #     self.layer = [layer]
        self.layer = layer
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        result = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, self.layer, self.VectorLayer)
        if len(result) > 0:
            self.identified.emit(result[0].mLayer, result[0].mFeature)
        else:
            self.identified.emit(None, None)


class PointDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów punktowych."""
    drawn = pyqtSignal(QgsPointXY)

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.drawn.emit(point)


class LineDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów liniowych."""
    drawn = pyqtSignal(QgsGeometry)
    move = pyqtSignal

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.begin = True
        self.rb = QgsRubberBand(canvas, QgsWkbTypes.LineGeometry)
        self.rb.setColor(QColor(255, 0, 0, 128))
        self.rb.setFillColor(QColor(255, 0, 0, 80))
        self.rb.setWidth(1)

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
        QgsMapTool.deactivate(self)
        self.clearMapCanvas()

    def clearMapCanvas(self):
        self.rb.reset(QgsWkbTypes.LineGeometry)


class PolyDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów poligonalnych."""
    drawn = pyqtSignal(QgsGeometry)
    move = pyqtSignal()

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.begin = True
        self.rb = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(QColor(255, 0, 0, 128))
        self.rb.setFillColor(QColor(255, 0, 0, 80))
        self.rb.setWidth(1)

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
        QgsMapTool.deactivate(self)
        self.clearMapCanvas()

    def clearMapCanvas(self):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)

# ========== Funkcje:

def flag_add(point):
    """Utworzenie nowego obiektu flagi."""
    is_fldchk = dlg.mt.params["extra"][0]
    dlg.mt.tool_off()
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
    iface.actionDraw().trigger()

def flag_del(layer, feature):
    """Skasowanie wybranego obiektu flagi."""
    dlg.mt.tool_off()
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
    iface.actionDraw().trigger()

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

def wyr_add(geom):
    """Utworzenie nowego obiektu wyrobiska."""
    dlg.mt.tool_off()
    layer = QgsProject.instance().mapLayersByName("wyrobiska")[0]
    fields = layer.fields()
    feature = QgsFeature()
    feature.setFields(fields)
    feature.setGeometry(geom)
    feature.setAttribute('user_id', dlg.user_id)
    feature.setAttribute('b_fldchk', False)
    layer.startEditing()
    layer.addFeature(feature)
    layer.commitChanges()
    iface.actionDraw().trigger()

def wyr_del(layer, feature):
    dlg.mt.tool_off()
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
    iface.actionDraw().trigger()

def auto_add(geom):
    """Utworzenie nowego obiektu parkingu."""
    dlg.mt.tool_off()
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
    dlg.mt.tool_off()
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
    dlg.mt.tool_off()
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
    dlg.mt.tool_off()
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
