#!/usr/bin/python

import psycopg2
import psycopg2.extras
import os.path
import win32gui
import win32ui
import win32con
import win32process
import tempfile
import codecs
import time

from PIL import Image
from win32com.client import GetObject
from qgis.PyQt.QtWidgets import QMessageBox
from configparser import ConfigParser
from qgis.gui import QgsMapToolIdentify, QgsMapTool, QgsRubberBand
from qgis.core import QgsProject, QgsGeometry, QgsWkbTypes, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY
from qgis.PyQt.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtCore import QTimer
from qgis.utils import iface

DB_SOURCE = "MOEK"
TEMP_PATH = tempfile.gettempdir()


class PgConn:
    """Połączenie z bazą PostgreSQL przez psycopg2."""
    _instance = None

    def __new__(cls):
        """Próba połączenia z db."""
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            try:
                with CfgPars() as cfg:
                    params = cfg.psycopg2()
                connection = cls._instance.connection = psycopg2.connect(**params)
                cursor = cls._instance.cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                cursor.fetchone()
            except Exception as error:
                cls._instance.__error_msg("connection", error)
                cls._instance = None
                return
        return cls._instance

    def __init__(self):
        self.connection = self._instance.connection
        self.cursor = self._instance.cursor

    @classmethod
    def __error_msg(cls, case, error, *query):
        """Komunikator błędów."""
        if case == "connection":
            QMessageBox.critical(None, "Połączenie z bazą danych", "Połączenie nie zostało nawiązane. \n Błąd: {}".format(error))
        if case == "query":
            print('Błąd w trakcie wykonywania kwerendy "{}", {}'.format(query, error))

    def query_sel(self, query, all):
        """Wykonanie kwerendy SELECT."""
        try:
            self.cursor.execute(query)
            if all:
                result = self.cursor.fetchall()
            else:
                result = self.cursor.fetchone()
        except Exception as error:
            self.__error_msg("query", error, query)
            return
        else:
            return result
        finally:
            self.close()

    def query_upd(self, query):
        """Wykonanie kwerendy UPDATE."""
        try:
            self.cursor.execute(query)
            result = self.cursor.rowcount
            if result > 0:
                self.connection.commit()
            else:
                self.connection.rollback()
        except Exception as error:
            self.__error_msg("query", error, query)
            self.connection.rollback()
            return
        else:
            return result
        finally:
            self.close()

    def query_exeval(self, query, values):
        """Wykonanie kwerendy EXECUTE_VALUES."""
        try:
            psycopg2.extras.execute_values(self.cursor, query, values)
            self.connection.commit()
        except Exception as error:
            self.__error_msg("query", error, query)
            return
        finally:
            self.close()

    def close(self):
        """Zamykanie połączenia i czyszczenie instancji."""
        if PgConn._instance is not None:
            self.cursor.close()
            self.connection.close()
            PgConn._instance = None


class CfgPars(ConfigParser):
    """Parser parametrów konfiguracji połączenia z bazą danych."""
    def __init__(self, filename='database.ini', section=DB_SOURCE):
        super().__init__()
        self.filename = self.resolve(filename)
        self.section = section
        self.read(self.filename)  # Pobranie zawartości pliku
        if not self.has_section(section):
            raise AttributeError(f'Sekcja {section} nie istnieje w pliku {filename}!')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        return True

    def resolve(self, name):
        """Zwraca ścieżkę do folderu plugina wraz z nazwą pliku .ini."""
        basepath = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(basepath, name)

    def psycopg2(self):
        """Przekazanie parametrów połączenia z db za pośrednictwem Psycopg2."""
        db = {}  # Stworzenie słownika
        # Ładowanie parametrów do słownika
        params = self.items(self.section)
        for param in params:
            db[param[0]] = param[1]
        return db

    def uri(self):
        """Przekazanie parametrów połączenia z db za pośrednictwem Uri."""
        result = ""
        # Ładowanie parametrów do słownika
        params = self.items(self.section)
        for key, val in params:
            if key == "database":
                key = "dbname"
                val = str('"' + val + '"')
            elif key == "user":
                val = str('"' + val + '"')
            result += key + "=" + val + " "
        return result


class GESync:
    """Integracja QGIS'a z Google Earth Pro."""
    def __init__(self):
        self.screen_scale = 1  # Wartość skalowania rozdzielczości ekranowej
        self.q_id = None  # Id procesu QGIS'a
        self.ge_id = None  # Id procesu Google Earth Pro
        self.q_hwnd = None  # Handler okna QGIS'a
        self.ge_hwnd = None  # Handler okna Google Earth Pro
        self.bmp_hwnd = None  # Handler subokna Google Earth Pro z widokiem samej mapy
        self.bytes = int()  # Rozmiar aktualnego pliku jpg
        self.is_ge = False  # Czy Google Earth Pro jest uruchomiony?
        self.is_on = False  # Czy warstwa 'Google Earth Pro' jest włączona?
        self.tmp_num = 0  # Numer pliku tymczasowego
        self.extent = None  # Zasięg geoprzestrzenny aktualnego widoku mapy
        self.t_void = False  # Blokada stopera
        self.player = False  # Czy w danym momencie uruchomiony jest player sekwencji?
        self.loaded = False  # Czy widok mapy się załadował?
        self.ge_layer = QgsProject.instance().mapLayersByName('Google Earth Pro')[0]  # Referencja warstwy 'Google Earth Pro'
        self.ge_legend = QgsProject.instance().layerTreeRoot().findLayer(self.ge_layer.id())  # Referencja warstwy w legendzie
        self.bmp_w = int()  # Szerokość bmp
        self.bmp_h = int()  # Wysokość bmp
        self.jpg_file = ""  # Ścieżka do pliku jpg
        self.get_handlers()
        iface.mapCanvas().extentsChanged.connect(self.extent_changed)

    def extent_changed(self):
        """Zmiana zakresu geoprzestrzennego widoku mapy."""
        # Wyjście z funkcji, jeśli stoper obecnie pracuje:
        if self.t_void:
            return
        self.t_void = True
        if self.is_on:
            self.extent = iface.mapCanvas().extent()
            self.loaded = False
        # print(f"loaded: {self.loaded}")
        # Wyłączenie warstwy z maską powiatu (QGIS zawiesza się przy częstym zoomowaniu z tą włączoną warstwą):
        QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("powiaty_mask")[0].id()).setItemVisibilityChecked(False)
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.check_extent)
        self.timer.start()  # Odpalenie stopera

    def check_extent(self):
        """Sprawdzenie, czy widok mapy przestał się zmieniać."""
        if self.extent != iface.mapCanvas().extent():  # Zmienił się
            self.extent = iface.mapCanvas().extent()
        else:
            # Kasowanie licznika:
            self.timer.stop()
            self.timer.deleteLater()
            self.t_void = False
            self.extent = iface.mapCanvas().extent()
            # self.loaded = True
            # print(f"loaded: {self.loaded}")
            # Włączenie warstwy z maską powiatu:
            QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("powiaty_mask")[0].id()).setItemVisibilityChecked(True)
            if self.is_on:
                self.ge_sync()

    def visible_changed(self, value):
        """Włączenie / wyłączenie warstwy 'Google Earth Pro'."""
        print(f"[visible_changed]")
        if value:  # Włączono warstwę
            self.is_on = True
            print(f"{self.extent} - {iface.mapCanvas().extent()}")
            if self.extent != iface.mapCanvas().extent():
                self.extent = iface.mapCanvas().extent()
                self.ge_sync()
                print(f"ge_sync")
            if self.player or not self.loaded:
                self.ge_grabber()
                print(f"ge_grabber")
        else:  # Wyłączono warstwę
            self.is_on = False

    def get_handlers(self):
        """Ustalenie id procesów i handlerów okien QGIS'a i Google Earth Pro (jeśli jest uruchomiony)."""
        # Utworzenie listy uruchomionych procesów:
        processes = GetObject('winmgmts:').InstancesOf('Win32_Process')
        process_list = [(p.Properties_("ProcessID").Value, p.Properties_("Name").Value) for p in processes]
        ge_flag = False
        for p in process_list:
            if p[1] == "qgis-bin-g7.exe" or p[1] == "qgis-bin.exe" or p[1] == "qgis-ltr-bin.exe" or p[1] == "qgis-ltr-bin-g7.exe":
                self.q_id = p[0]
                print(f"qgis: {p[1]}")
            elif p[1] == "googleearth.exe":
                ge_flag = True
                self.is_ge = True
                self.ge_id = p[0]
                print(f"is_ge: {self.is_ge}, ge_id: {self.ge_id}")
        if not ge_flag:  # Google Earth Pro nie jest uruchomiony
            self.ge_id = None
            self.is_ge = False
        # Pętla przeszukująca okna uruchomionych programów:
        win32gui.EnumWindows(self._enum_callback, None)

    def _enum_callback(self, hwnd, extras):
        """Ustalenie handlerów dla QGIS i Google Earth Pro."""
        # Wyszukanie handlera QGIS'a:
        # if win32process.GetWindowThreadProcessId(hwnd)[1] == self.q_id:
        w_title = win32gui.GetWindowText(hwnd)
        # print(f"w_title: {w_title}")
        if w_title.find("*MOEK_editor") != -1:  # W nazwie otwartego pliku .qgz musi być fraza "*MOEK_editor"
            self.q_hwnd = hwnd
            print(f"self.q_hwnd: {self.q_hwnd}")
        # Wyszukanie handlera Google Earth Pro:
        if self.is_ge and w_title == "Google Earth Pro":
            self.ge_hwnd = hwnd
            print(f"self.ge_hwnd: {self.ge_hwnd}")
            # Wyszukanie handlera subokna Google Earth Pro z obrazem mapy:
            self.child = 0
            try:
                win32gui.EnumChildWindows(self.ge_hwnd, self._enum_children, None)
            except:
                print(f"EnumChildWindows exception!")

    def _enum_children(self, hwnd, extras):
        """Ustalenie handlera subokna Google Earth Pro z obrazem mapy."""
        print(f"child: {self.child}")
        self.child += 1
        rect = win32gui.GetWindowRect(hwnd)
        print(f"ge_width: {rect[2] - rect[0]}, ge_height: {rect[3] - rect[1]}")
        if self.child == 12:
            self.bmp_hwnd = hwnd

    def ge_sync(self):
        """Wyświetlenie w Google Earth Pro obszaru mapy z QGIS'a."""
        print("[ge_sync]")
        if not self.is_ge:
            print(f"2. q2ge")
            self.q2ge()
            self.get_handlers()
            return
        # Sprawdzenie, czy Google Earth Pro jeszcze działa:
        try:
            win32gui.GetClientRect(self.bmp_hwnd)
        except:
            self.is_ge = False
            return
        print(f"3. q2ge")
        self.q2ge()
        self.ge_grabber()

    def q2ge(self, back=True, player=False):
        """Przejście w Google Earth Pro do widoku mapy z QGIS'a."""
        print(f"[q2ge]")
        if not self.is_ge:
            self.get_handlers()
        canvas = iface.mapCanvas()
        crs_src = canvas.mapSettings().destinationCrs()  # PL1992
        crs_dest = QgsCoordinateReferenceSystem(4326)  # WGS84
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())  # Transformacja między układami
        if not self.extent or not back or player:
            print("extent changed")
            self.loaded = False
            self.extent = iface.mapCanvas().extent()
        # Współrzędne rogów widoku mapy:
        x1 = self.extent.xMinimum()
        x2 = self.extent.xMaximum()
        y1 = self.extent.yMinimum()
        y2 = self.extent.yMaximum()
        # Wyznaczenie punktu centralnego:
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        proj = QgsPointXY(x, y)  # Punkt centralny w PL1992
        # Transformacja punktu centralnego do WGS84:
        geo = xform.transform(QgsPointXY(proj.x(), proj.y()))
        # Współrzędne geograficzne punktu centralnego:
        lon = geo.x()
        lat = geo.y()
        # Ustalenie kąta obrotu mapy w GE:
        rot = -3.85 + (lon-14.11677234)*7.85/10.02872526
        # Ustalenie wysokości kamery w GE:
        rng = canvas.scale() * (canvas.width()/100) * (0.022875 / self.screen_scale)
        TEMP_PATH = tempfile.gettempdir()  # Ścieżka do folderu TEMP
        # Utworzenie pliku kml:
        kml = codecs.open(TEMP_PATH + '/moek.kml', 'w', encoding='utf-8')
        kml.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        kml.write('<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">\n')
        kml.write('    <Document>\n')
        kml.write('        <LookAt>\n')
        k_txt = f'            <longitude>{lon}</longitude>\n'
        kml.write(k_txt)
        k_txt = f'            <latitude>{lat}</latitude>\n'
        kml.write(k_txt)
        kml.write('            <altitude>0</altitude>\n')
        k_txt = f'            <heading>{rot}</heading>\n'
        kml.write(k_txt)
        kml.write('            <tilt>0</tilt>\n')
        k_txt = f'            <range>{rng}</range>\n'
        kml.write(k_txt)
        kml.write('            <gx:altitudeMode>relativeToGround</gx:altitudeMode>\n')
        kml.write('        </LookAt>\n')
        kml.write('    </Document>\n')
        kml.write('</kml>\n')
        kml.close()
        # Włączenie dla QGIS'a funkcji always on top:
        if back and self.is_ge:
            print(f"qgis on top: True")
            try:
                win32gui.SetWindowPos(self.q_hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            except:
                print(f"q_hwnd ({self.q_hwnd}) exception!")
                pass
        # Odpalenie pliku w Google Earth Pro:
        os.startfile(TEMP_PATH + '/moek.kml')
        if back and self.is_ge:
            QTimer.singleShot(1000, self.on_top_off)

    def on_top_off(self):
        """Wyłączenie dla QGIS'a funkcji always on top."""
        # print(f"[on_top_off]")
        try:
            win32gui.SetWindowPos(self.q_hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            win32gui.SetForegroundWindow(self.q_hwnd)
            print(f"qgis on top: False")
        except:
            print(f"q_hwnd ({self.q_hwnd}) exception!")
            self.get_handlers()

    def ge_grabber(self):
        """Główna funkcja przechwytywania obrazu z Google Earth Pro."""
        # Ekranowe wymiary obrazka do przechwycenia:
        print("[ge_grabber]")
        try:
            l,t,r,b = win32gui.GetClientRect(self.bmp_hwnd)
        except:
            print("ge_grabber exception!")
            self.get_handlers()
            self.ge_sync()
            return
        self.bmp_w = int((r - l) / self.screen_scale)
        self.bmp_h = int((b - t)  / self.screen_scale)
        print(f"bmp_w: {self.bmp_w}, bmp_h: {self.bmp_h}")
        self.tmp_num = 0
        self.bytes = 0
        # Przechwycenie obrazu i określenie ile waży zapisany jpg:
        tmp_bytes = self.create_jpg()
        # Tworzenie obrazów w pętli, aż do momentu braku zmian w rozmiarze pliku:
        while self.bytes != tmp_bytes:
            if self.tmp_num == 10:
                break
            self.tmp_num += 1
            self.bytes = tmp_bytes
            time.sleep(0.2)
            tmp_bytes = self.create_jpg()
        self.create_jpg()  # Ostateczne zapisanie pliku
        self.wld_creator()  # Utworzenie pliku z georeferencjami
        self.layer_update()  # Wczytanie jpg'a do warstwy
        self.loaded = True
        print(f"loaded: {self.loaded}")
        # Wyłączenie dla QGIS'a funkcji always on top:
        self.on_top_off()

    def create_jpg(self):
        """Przechwycenie obrazu z Google Earth Pro i zapisanie go do .jpg."""
        print(f"[create_jpg]")
        dc = win32gui.GetDC(self.bmp_hwnd)
        hdc = win32ui.CreateDCFromHandle(dc)
        new_dc = hdc.CreateCompatibleDC()
        new_bmp = win32ui.CreateBitmap()
        new_bmp.CreateCompatibleBitmap(hdc, self.bmp_w, self.bmp_h)
        new_dc.SelectObject(new_bmp)
        new_dc.BitBlt((0,0),(self.bmp_w, self.bmp_h) , hdc, (0,0), win32con.SRCCOPY)
        bmp_bits = new_bmp.GetBitmapBits(True)
        img = Image.frombytes('RGB', (self.bmp_w, self.bmp_h), bmp_bits, 'raw', 'BGRX')
        self.jpg_file = TEMP_PATH + "\\ge.jpg"
        img.save(self.jpg_file, "JPEG", quality=75, optimize=False, progressive=False)
        win32gui.DeleteObject(new_bmp.GetHandle())
        new_dc.DeleteDC()
        hdc.DeleteDC()
        win32gui.ReleaseDC(self.bmp_hwnd, dc)
        time.sleep(0.2)
        return os.stat(self.jpg_file).st_size

    def wld_creator(self):
        """Tworzenie pliku georeferencyjnego dla jpg'a."""
        # Współrzędne rogów widoku mapy [m]:
        x1 = self.extent.xMinimum()
        x2 = self.extent.xMaximum()
        y1 = self.extent.yMinimum()
        y2 = self.extent.yMaximum()
        # Wymiary geoprzestrzenne mapy [m]:
        width = x2 - x1
        height = y2 - y1
        # Wymiary ekranowe mapy [px]:
        cnv_w = iface.mapCanvas().width()
        cnv_h = iface.mapCanvas().height()
        # Skalowanie bmp do szerokości ekranowej mapy:
        bmp_h_scaled = (cnv_w * self.bmp_h) / self.bmp_w
        # Wysokość geoprzestrzenna zeskalowanej bmp:
        height_scaled = (bmp_h_scaled * height) / cnv_h
        # Różnica wysokości geoprzestrzennej mapy i przeskalowanej bmp:
        height_diff = height_scaled - height
        # Współrzędna y2 przeskalowanej bmp:
        y2_bmp = y2 + (height_diff / 2)
        # Utworzenie pliku wld:
        wld = codecs.open(TEMP_PATH + '\\ge.wld', 'w', encoding='utf-8')
        wld.write(f'{width / self.bmp_w}\n')
        wld.write('0\n')
        wld.write('0\n')
        wld.write(f'{-height_scaled / self.bmp_h}\n')
        wld.write(f'{x1}\n')
        wld.write(f'{y2_bmp}\n')
        wld.close()

    def layer_update(self):
        """Aktualizacja warstwy Google Earth Pro."""
        time.sleep(0.2)  # Poczekanie, aż .jpg zapisze się na dysku
        iface.mainWindow().blockSignals(True)  # Żeby QGIS nie monitował o braku crs'a
        ge_layer = QgsProject.instance().mapLayersByName('Google Earth Pro')[0]
        data_source = TEMP_PATH + "\\ge.jpg"
        base_name = ge_layer.name()
        provider = ge_layer.providerType()
        options = ge_layer.dataProvider().ProviderOptions()
        ge_layer.setDataSource(data_source, base_name, provider, options)
        ge_layer.setCrs(QgsCoordinateReferenceSystem(2180, QgsCoordinateReferenceSystem.EpsgCrsId))
        ge_layer.reload()
        iface.mainWindow().blockSignals(False)
        iface.actionDraw().trigger()
        iface.mapCanvas().refresh()


class IdentMapTool(QgsMapToolIdentify):
    """Maptool do zaznaczania obiektów z wybranej warstwy."""
    identified = pyqtSignal(object, object)

    def __init__(self, canvas, layer):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        if type(layer) is list:
            self.layer = layer
        else:
            self.layer = [layer]
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        result = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, self.layer, self.VectorLayer)
        if len(result) > 0:
            self.identified.emit(result[0].mLayer, result[0].mFeature)
        else:
            self.identified.emit(None, None)


class addFlag(QgsMapTool):
    flagAdded = pyqtSignal(QgsPointXY)

    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapTool.__init__(self, canvas)
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.flagAdded.emit(point)


class AddPointMapTool(QgsMapTool):
    """Maptool do dodawania geometrii punktowej."""
    added = pyqtSignal(QgsPointXY)

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.added.emit(point)


class PolySelMapTool(QgsMapTool):
    """Maptool do poligonalnego zaznaczania obiektów."""
    selected = pyqtSignal(QgsGeometry)
    move = pyqtSignal

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
                self.selected.emit(self.rb.asGeometry())
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

class LineDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów liniowych."""
    selected = pyqtSignal(QgsGeometry)
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
                self.selected.emit(self.rb.asGeometry())
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
