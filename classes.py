#!/usr/bin/python

import sys
import psycopg2
import psycopg2.extras
import os.path
import os
import win32api
import win32gui
import win32ui
import win32con
import win32process
import tempfile
import codecs
import time
import math
try:
    from osgeo import gdal, osr
except:
    import gdal
    import osr
import pandas as pd
import numpy as np

from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY, QgsSettings, QgsRasterDataProvider, QgsRasterBlock, QgsRasterFileWriter, QgsRasterPipe, QgsRasterInterface
from qgis.PyQt.QtCore import Qt, pyqtSlot, pyqtProperty, QTimer, QAbstractTableModel, QVariant, QModelIndex, QRect, QObject, pyqtSignal, QFileSystemWatcher
from qgis.PyQt.QtWidgets import QMessageBox, QHeaderView, QStyledItemDelegate, QStyle
from qgis.PyQt.QtGui import QColor, QFont, QLinearGradient, QBrush, QPen, QPainter
from qgis.utils import iface
from threading import Thread
from PIL import Image
from win32com.client import GetObject
from configparser import ConfigParser
from win32con import MONITOR_DEFAULTTONEAREST
# from contextlib import contextmanager

DB_SOURCE = "MOEK"
TEMP_PATH = tempfile.gettempdir()
ValueRole = Qt.UserRole + 1


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

    def query_pd(self, query, col_names):
        """Wykonanie kwerendy SELECT i zwrócenie dataframe'u."""
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
        except Exception as error:
            self.__error_msg("query", error, query)
            return None
        else:
            df = pd.DataFrame(result, columns=col_names)
            return df
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

    def query_upd_ret(self, query):
        """Wykonanie kwerendy UPDATE ze zwracaniem wartości."""
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
            return self.cursor.fetchone()[0]
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


class MonitorManager:
    """Menedżer ustawień monitorów."""
    def __init__(self, dlg):
        self.dlg = dlg
        self.monitors = []
        self.monitors_props = []
        self.test_monitors = []
        self.test_monitors_props = []
        self.create_monitors()

    def create_monitors(self, check=False):
        """Tworzenie monitorów lub monitorów testowych (jeśli check=True)."""
        monitors = self.test_monitors if check else self.monitors
        monitors_props = self.test_monitors_props if check else self.monitors_props
        monitors.clear()
        monitors_props.clear()
        try:
            i = 0
            for hMonitor, hdcMonitor, pyRect in win32api.EnumDisplayMonitors():
                mon_props = self.monitor_properties(hMonitor)
                if not mon_props:
                    continue
                hmon, device, scale_factor = mon_props
                _mon = Monitor(i, hmon, device, scale_factor)
                monitors.append(_mon)
                monitors_props.append([i, hmon, device, scale_factor])
                i += 1
        except win32api.error:
            return None

    def check_monitors(self):
        """Sprawdza, czy ustawienia monitorów się nie zmieniły. Jeśli tak, to tworzy monitory od nowa."""
        self.create_monitors(check=True)  # Aktualizacja listy monitorów testowych
        if self.monitors_props != self.test_monitors_props:
            self.create_monitors()

    def monitor_properties(self, hmon):
        """Zwraca ustawienia monitora."""
        try:
            device = win32api.GetMonitorInfo(hmon)["Device"]
        except win32api.error:
            return None
        try:
            l,t,r,b = win32api.GetMonitorInfo(hmon)["Monitor"]
        except win32api.error:
            return None
        v_w = r - l
        try:
            r_w = win32api.EnumDisplaySettings(device, win32con.ENUM_CURRENT_SETTINGS).PelsWidth
        except win32api.error:
            return None
        if v_w > 0:
            scale_factor = r_w / v_w
        else:
            return
        return hmon, device, scale_factor

    def monitor_from_window(self, window):
        """Zwraca id monitora, na którym znajduje się wskazane okno."""
        for monitor in self.monitors:
            if monitor.contains_window(window):
                return monitor.id
        return None

    def scale_factor_from_window(self, window):
        "Zwraca scale_factor monitora, na którym znajduje się wskazane okno."
        for monitor in self.monitors:
            if monitor.contains_window(window):
                return monitor.scale_factor
        return None

class Monitor:
    """Obiekt reprezentujący monitor."""
    def __init__(self, id, handle, device, scale_factor):
        self.id = id
        self.handle = handle
        self.device = device
        self.scale_factor = scale_factor
        self.prop_list = [self.id]

    def contains_window(self, window):
        """Sprawdza, czy podane okno znajduje się w obrębie tego monitora."""
        try:
            if win32api.MonitorFromWindow(window, MONITOR_DEFAULTTONEAREST) == self.handle:
                return True
            else:
                return False
        except win32api.error:
            return None


class GESync:
    """Integracja QGIS'a z Google Earth Pro."""
    def __init__(self, dlg):
        self.dlg = dlg
        self.q_id = None  # Id procesu QGIS'a
        self.ge_id = None  # Id procesu Google Earth Pro
        self.q_hwnd = None  # Handler okna QGIS'a
        self.ge_hwnd = None  # Handler okna Google Earth Pro
        self.tif_hwnd = None  # Handler subokna Google Earth Pro z widokiem samej mapy
        self.downscale = None  # Mnożnik obniżenia rozdzielczości podkładu GEP
        # self.loaded = False
        self.t0 = None
        self.t1 = None
        self.update_timer = None  # Obiekt stopera aktualizacji screengraba GEP
        self.data_source = "/vsimem/ge.tif"  # Tymczasowy plik geotiff (zapisywany bezpośrednio do pamięci)
        # self.data_source = TEMP_PATH + "\\ge.tif"  # Tymczasowy plik geotiff
        self.blocker = False
        self.is_on = False  # Czy warstwa 'Google Earth Pro' jest włączona?
        self.tif_w = None  # Szerokość geotiff'a
        self.tif_h = None  # Wysokość geotiff'a
        self.img_array = np.array([])  # Macierz numpy przechwyconego obrazu GEP
        self.img_matrix = np.array([])  # Uproszczona matryca z macierzy numpy przechwyconego obrazu GEP
        self.get_handlers()
        self.dlg.bm_panel.ge_sync = False
        self.dlg.bm_panel.date_selector.init_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "ge_hwnd":
            print(f"ge_hwnd: {val}")
            self.dlg.p_map.btns.ge_light.is_on = True if val else False
        # elif attr == "blocker":
        #     print(f"blocker: {val}")
            # iface.mapCanvas().freeze(val)  # Zablokowanie odświeżania canvas'u
        elif attr == "is_on":
            if val:
                QgsSettings().setValue("/qgis/map_update_interval", 750) #  Redukcja flickering'u podkładu GEP
                self.dlg.bm_panel.check_extent()
            else:
                QgsSettings().setValue("/qgis/map_update_interval", 250)
                self.update_timer_reset()

    def ge_probe(self):
        """Sprawdza, czy GEP jest uruchomiony."""
        if self.ge_hwnd and not win32gui.IsWindow(self.ge_hwnd):
            self.ge_hwnd = None
            self.tif_hwnd = None
            self.dlg.bm_panel.check_extent()

    def ge_reset(self):
        """Próba naprawienia ewentualnych błędów."""
        # print(f"[ge_reset]")
        self.get_handlers()
        if not self.ge_hwnd:
            self.q2ge()
        time.sleep(3)  # Czas uruchomienia GEP
        self.dlg.bm_panel.check_extent()

    def get_handlers(self):
        """Ustalenie id procesów i handlerów okien QGIS'a i Google Earth Pro (jeśli jest uruchomiony)."""
        # Utworzenie listy uruchomionych procesów:
        processes = GetObject('winmgmts:').InstancesOf('Win32_Process')
        process_list = [(p.Properties_("ProcessID").Value, p.Properties_("Name").Value) for p in processes]
        q_flag = False
        ge_flag = False
        for p in process_list:
            if p[1] == "qgis-bin-g7.exe" or p[1] == "qgis-bin.exe" or p[1] == "qgis-ltr-bin.exe" or p[1] == "qgis-ltr-bin-g7.exe":
                q_flag = True
                self.q_id = p[0]
                # print(f"qgis: {p[1]}")
            elif p[1] == "googleearth.exe":
                ge_flag = True
                self.ge_id = p[0]
        if not q_flag:
            self.q_id = None
            self.q_hwnd = None
        if not ge_flag:  # Google Earth Pro nie jest uruchomiony
            self.ge_id = None
            self.ge_hwnd = None
        # Pętla przeszukująca okna uruchomionych programów:
        win32gui.EnumWindows(self._enum_callback, None)

    def _enum_callback(self, hwnd, extras):
        """Ustalenie handlerów dla QGIS i Google Earth Pro."""
        # Wyszukanie handlera QGIS'a:
        w_title = win32gui.GetWindowText(hwnd)
        # print(f"w_title: {w_title}")
        if w_title.find("| MOEK_Editor") != -1:  # W nazwie otwartego pliku .qgz musi być fraza "*MOEK_editor"
            self.q_hwnd = hwnd
            print(f"self.q_hwnd: {self.q_hwnd}")
        # Wyszukanie handlera Google Earth Pro:
        if w_title == "Google Earth Pro":
            self.ge_hwnd = hwnd
            # Wyszukanie handlera subokna Google Earth Pro z obrazem mapy:
            self.child = 0
            try:
                win32gui.EnumChildWindows(self.ge_hwnd, self._enum_children, None)
                print("Handler subokna Google Earth Pro został ustalony.")
            except:
                pass

    def _enum_children(self, hwnd, extras):
        """Ustalenie handlera subokna Google Earth Pro z obrazem mapy."""
        # print(f"child: {self.child}")
        self.child += 1
        rect = win32gui.GetWindowRect(hwnd)
        # print(f"ge_width: {rect[2] - rect[0]}, ge_height: {rect[3] - rect[1]}")
        if self.child == 12:
            self.tif_hwnd = hwnd

    def start_updater(self):
        """Uruchomienie stopera odświeżania podkładu GEP"""
        print("[start_updater]")
        if self.update_timer != None:
            self.update_timer_reset()
        # self.loaded = False
        self.blocker = False
        self.update_timer = QTimer(interval=300)
        self.update_timer.timeout.connect(self.ge_grabber)
        self.update_timer.start()  # Odpalenie stopera

    def update_timer_reset(self):
        """Kasowanie stopera odświeżenia podkładu GEP."""
        print("[update_timer_reset]")
        if self.update_timer:
            # self.loaded = False
            self.update_timer.stop()
            self.update_timer = None

    def on_top_off(self):
        """Wyłączenie dla QGIS'a funkcji always on top."""
        # print(f"[on_top_off]")
        try:
            win32gui.SetWindowPos(self.q_hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            # print(f"qgis on top: False")
        except:
            print(f"q_hwnd ({self.q_hwnd}) exception!")
            self.get_handlers()
            return
        try:
            win32gui.SetForegroundWindow(self.q_hwnd)
        except Exception as err:
            print(err)

    def limit_pixel_size(self, px_limit):
        """Pomniejszenie wymiarów tiff'a, aby nie przekraczał dopuszczalnej ilość pikseli
        - redukcja flickeringu podczas ładowania obrazka do warstwy."""
        w_0, h_0 = self.tif_w, self.tif_h
        w, h = w_0, h_0
        pxs = w * h
        if pxs < px_limit:
            return
        w_min = 0
        w_max = w_0
        while w_max - w_min > 1:
            w = w_min + int(round((w_max - w_min) / 2))
            h = int(round(w * h_0 / w_0))
            pxs = w * h
            if pxs < px_limit:
                w_min = w
            else:
                w_max = w
            # print(f"w_min: {w_min}, w_max: {w_max}, w: {w}, h: {h}, pxs: {pxs}")
        self.tif_w, self.tif_h = w, h

    def get_tif_size(self, ge_w, ge_h, q_w):
        """Ustala wymiary tif'a w zależności od rozmiarów mapcanvas'u."""
        if ge_w < q_w:
            # Szerokość obrazka z GEP jest mniejsza od QGIS
            # nie ma sensu go upscalować
            return ge_w, ge_h
        else:
            # Obrazek z GEP jest większy od QGIS
            # zmniejszamy go, żeby plik był lżejszy
            tif_w = q_w
            tif_h = round(ge_h * tif_w / ge_w)
            return tif_w, tif_h

    def calculate_ge_size(self, l, t, r, b):
        """Ustalenie rzeczywistych wymiarów przechwyconego z GEP obrazu."""
        # print("[calculate_ge_size]")
        # Ustalenie współczynników skalowania monitorów:
        try:
            q_scale_factor = self.dlg.mon.scale_factor_from_window(self.q_hwnd)
        except Exception as e:
            print(f"scale_factor_from_window [self.q_hwnd] exception: {e}")
        try:
            ge_scale_factor = self.dlg.mon.scale_factor_from_window(self.tif_hwnd)
        except Exception as e:
            print(f"scale_factor_from_window [self.tif_hwnd] exception: {e}")
        if not q_scale_factor or not ge_scale_factor:
            self.ge_reset()
            return
        # Szerokość i wysokość przechwytywanego obrazu:
        ge_w_0 = int(r - l)
        ge_h_0 = int(b - t)
        # Rzeczywista (niezależna od ustawionego skalowania) szerokość i wysokość przechwytywanego obrazu:
        ge_w_scaled = int(ge_w_0 * ge_scale_factor)
        ge_h_scaled = int(ge_h_0 * ge_scale_factor)
        # Ustalenie wymiarów tiff'a:
        q_w_scaled = int(iface.mapCanvas().width() * q_scale_factor)
        self.tif_w, self.tif_h = self.get_tif_size(ge_w_scaled, ge_h_scaled, q_w_scaled)
        self.limit_pixel_size(3000000)
        # Ustalenie mnożnika obniżenia rozdzielczości przechwyconego obrazu w zależności od wymiarów mapcanvas'u:
        self.downscale = ge_w_scaled / self.tif_w
        # print(f"downscale: {self.downscale}")
        # self.downscale = 1 if downscale < 1 else downscale
        # # Ostateczne ustalenie szerokości i wysokości przechwyconego obrazu:
        # self.tif_w = int(self.tif_w / self.downscale)
        # self.tif_h = int(self.tif_h / self.downscale)
        # print(f"{self.tif_w}x{self.tif_h} x{self.downscale}, q_w_scaled: {q_w_scaled}")

    def matrix_is_equal(self, tmp_matrix):
        """Sprawdza, czy podobieństwa w matrycach nowego i poprzednio ustalonego przechwycownego obrazu GEP są na poziomie 98%."""
        number_of_equal_elements = np.sum(self.img_matrix==tmp_matrix)
        total_elements = self.img_matrix.size
        equality = round(number_of_equal_elements/total_elements*100, 2)
        return False if equality < 98 or np.isnan(equality) else True

    def array_merger(self, array):
        """Tworzy 2D matrycę z 3D macierzy."""
        return array[:,:,0] + array[:,:,1] + array[:,:,2]

    def q2ge(self, back=True, player=False):
        """Przejście w Google Earth Pro do widoku mapy z QGIS'a."""
        # print(f"[q2ge]")
        canvas = iface.mapCanvas()
        extent = self.dlg.bm_panel.extent
        if not extent:
            extent.check_extent()
            return
        # Współrzędne rogów widoku mapy:
        x1 = extent.xMinimum()
        x2 = extent.xMaximum()
        y1 = extent.yMinimum()
        y2 = extent.yMaximum()
        # Wyznaczenie punktu centralnego:
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        proj = QgsPointXY(x, y)  # Punkt centralny w PL1992
        # Transformacja punktu centralnego do WGS84:
        crs_src = canvas.mapSettings().destinationCrs()  # PL1992
        crs_dest = QgsCoordinateReferenceSystem(4326)  # WGS84
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())  # Transformacja między układami
        geo = xform.transform(QgsPointXY(proj.x(), proj.y()))
        # Współrzędne geograficzne punktu centralnego:
        lon = geo.x()
        lat = geo.y()
        # Ustalenie kąta obrotu mapy w GEP:
        rot = -3.85 + (lon-14.11677234)*7.85/10.02872526
        # Ustalenie wysokości kamery w GEP:
        rng = canvas.scale() * (canvas.width()/100) * 0.022875
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
        # Włączenie dla QGIS'a trybu always on top:
        if back and self.ge_hwnd:
            # print(f"qgis on top: True")
            try:
                win32gui.SetWindowPos(self.q_hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            except:
                print(f"q_hwnd ({self.q_hwnd}) exception!")
                self.ge_reset()
                return
        # Odpalenie pliku w Google Earth Pro:
        os.startfile(TEMP_PATH + '/moek.kml')
        if not self.ge_hwnd:
            self.get_handlers()
        # Opóźnione wyłączenie dla QGIS'a trybu always on top:
        if back and self.ge_hwnd:
            QTimer.singleShot(1000, self.on_top_off)

    def ge_grabber(self):
        """Przechwyca obraz z Google Earth Pro i wczytuje go do warstwy Google Earth Pro."""
        if self.blocker or self.dlg.bm_panel.rendering:
            # print("============> blocked")
            return
        self.dlg.mon.check_monitors()  # Sprawdza, czy ustawienia monitorów się nie zmieniły
        # Ustalenie wymiarów okna GEP:
        try:
            l,t,r,b = win32gui.GetClientRect(self.tif_hwnd)
        except:
            print("ge_grabber exception!")
            self.ge_reset()
            return
        # Ustalenie rzeczywistej rozdzielczości (niezależnej od skalowania) i downscalingu przechwyconego obrazu GEP:
        self.calculate_ge_size(l, t, r ,b)
        # Przechwycenie obrazu w formie macierzy:
        tmp_array = self.create_img()
        # Konwersja macierzy do matrycy:
        tmp_matrix = self.array_merger(tmp_array)
        # Określenie % podobieństwa aktualnego obrazu z poprzednio ustalonym.
        # Przerwanie funkcji, jeśli podobieństwa są na poziomie 98%:
        if self.matrix_is_equal(tmp_matrix):
            return
        # Zachowanie aktualnej macierzy i matrycy:
        self.img_array = tmp_array
        self.img_matrix = tmp_matrix
        # Utworzenie geotiff'a:
        self.create_tif()
        # Aktualizacja warstwy Google Earth Pro:
        self.layer_update()

    def create_img(self):
        """Przechwycenie obrazu z Google Earth Pro do macierzy numpy."""
        # print(f"[create_img]")
        try:
            dc = win32gui.GetDC(self.tif_hwnd)
        except:
            print("create_img exception!")
            self.ge_reset()
            return
        hdc = win32ui.CreateDCFromHandle(dc)
        new_dc = hdc.CreateCompatibleDC()
        new_img = win32ui.CreateBitmap()
        new_img.CreateCompatibleBitmap(hdc, self.tif_w, self.tif_h)
        new_dc.SelectObject(new_img)
        if self.downscale == 1:
            new_dc.BitBlt((0,0),(self.tif_w, self.tif_h) , hdc, (0,0), win32con.SRCCOPY)
        else:
            new_dc.StretchBlt((0,0),(self.tif_w, self.tif_h) , hdc, (0,0), (int(self.tif_w * self.downscale), int(self.tif_h * self.downscale)), win32con.SRCCOPY)
        img_bits = new_img.GetBitmapBits(True)
        img = Image.frombytes('RGB', (self.tif_w, self.tif_h), img_bits, 'raw', 'BGRX')
        win32gui.DeleteObject(new_img.GetHandle())
        new_dc.DeleteDC()
        hdc.DeleteDC()
        win32gui.ReleaseDC(self.tif_hwnd, dc)
        return np.array(img)

    def create_tif(self):
        """Tworzy geotiff z przechwycownego obrazu GEP i zapisuje go na dysku."""
        x_pixs = self.img_array.shape[1]
        y_pixs = self.img_array.shape[0]
        bands = self.img_array.shape[2]
        # Stworzenie pustego geotiff'a:
        driver = gdal.GetDriverByName('GTiff')
        options=["COMPRESS=NONE", "NUM_THREADS=ALL_CPUS", "TILED=YES", "BLOCKXSIZE=16", "BLOCKYSIZE=16"]
        ds = driver.Create(self.data_source, x_pixs, y_pixs, bands, gdal.GDT_Byte, options=options)
        if not ds:
            return
        # Przeniesienie danych z macierzy do geotiff'a:
        for i in range(bands):
            ds.GetRasterBand(i+1).WriteArray(self.img_array[:, :, i])
            ds.GetRasterBand(i+1).SetNoDataValue(np.nan)
        # Nadanie georeferencji:
        ds.SetGeoTransform(self.georef_params())
        # Nadanie układu współrzędnych:
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(2180)
        ds.SetProjection(out_srs.ExportToWkt())
        # Zapis pliku na dysku:
        ds.FlushCache()
        ds = None
        # print("----------> flushed")

    def georef_params(self):
        """Zwraca parametry georeferencyjne geotiff'a."""
        extent = self.dlg.bm_panel.extent
        if not extent:
            extent.check_extent()
            return
        # Współrzędne rogów widoku mapy [m]:
        x1 = extent.xMinimum()
        x2 = extent.xMaximum()
        y1 = extent.yMinimum()
        y2 = extent.yMaximum()
        # Wymiary geoprzestrzenne mapy [m]:
        width = x2 - x1
        height = y2 - y1
        # Wymiary ekranowe mapy [px]:
        cnv_w = iface.mapCanvas().width()
        cnv_h = iface.mapCanvas().height()
        # Skalowanie tif do szerokości ekranowej mapy:
        tif_h_scaled = (cnv_w * self.tif_h) / self.tif_w
        # Wysokość geoprzestrzenna zeskalowanego tif'a:
        height_scaled = (tif_h_scaled * height) / cnv_h
        # Różnica wysokości geoprzestrzennej mapy i przeskalowanego tif'a:
        height_diff = height_scaled - height
        # Współrzędna y2 przeskalowanego tif'a:
        y2_tif = y2 + (height_diff / 2)
        return x1, width / self.tif_w, 0, y2_tif, 0, -(height_scaled / self.tif_h)

    def layer_update(self):
        """Aktualizacja warstwy Google Earth Pro."""
        # print(f"[layer_update]: {self.blocker}")
        canvas = iface.mapCanvas()
        ge_layer = QgsProject.instance().mapLayersByName('Google Earth Pro')[0]  # Referencja warstwy 'Google Earth Pro'
        base_name = ge_layer.name()
        provider = ge_layer.providerType()
        options = ge_layer.dataProvider().ProviderOptions()

        ge_layer.setDataSource(self.data_source, base_name, provider, options)
        if canvas.isCachingEnabled():
            ge_layer.triggerRepaint()
        else:
            canvas.refresh()
        # print("==========> updated")


class DataFrameModel(QAbstractTableModel):
    """Podstawowy model tabeli zasilany przez pandas dataframe."""
    DtypeRole = Qt.UserRole + 1000
    ValueRole = Qt.UserRole + 1001

    def __init__(self, df=pd.DataFrame(), tv=None, col_names=[], parent=None):
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df
        self.col_names = col_names
        self.tv = tv  # Referencja do tableview
        self.tv.setModel(self)
        self.tv.selectionModel().selectionChanged.connect(lambda: self.layoutChanged.emit())
        self.tv.horizontalHeader().setSortIndicatorShown(False)
        self.tv.horizontalHeader().setSortIndicator(-1, 0)
        self.sort_col = -1
        self.sort_ord = 0

    def col_names(self, df, col_names):
        """Nadanie nazw kolumn tableview'u."""
        df.columns = col_names
        return df

    def sort_reset(self):
        """Wyłącza sortowanie po kolumnie."""
        self.tv.horizontalHeader().setSortIndicator(-1, 0)
        self.sort_col = -1
        self.sort_ord = 0

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

    @pyqtSlot(int, Qt.Orientation, result=str)
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if self.col_names:
                    try:
                        return self.col_names[section]  # type: ignore
                    except:
                        pass
                return self._dataframe.columns[section]
            else:
                return str(self._dataframe.index[section])
        return QVariant()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount() \
            and 0 <= index.column() < self.columnCount()):
            return QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype
        try:
            val = self._dataframe.iloc[row][col]
        except:
            return QVariant()
        if role == DataFrameModel.ValueRole:
            return val
        if role == DataFrameModel.DtypeRole:
            return dt
        return QVariant()

    def roleNames(self):
        roles = {
            Qt.DisplayRole: b'display',
            DataFrameModel.DtypeRole: b'dtype',
            DataFrameModel.ValueRole: b'value'
        }
        return roles


class WDfModel(DataFrameModel):
    """Subklasa dataframemodel dla tableview wyświetlającą wdf."""

    def __init__(self, df=pd.DataFrame(), tv=None, col_widths=[], col_names=[], parent=None):
        super().__init__(df, tv, col_names)
        self.tv = tv  # Referencja do tableview
        de = WDfDelegate()
        self.tv.setItemDelegate(de)
        self.col_format(col_widths)

    def col_format(self, col_widths):
        """Formatowanie szerokości kolumn tableview'u."""
        cols = list(enumerate(col_widths, 0))
        for col in cols:
            self.tv.setColumnWidth(col[0], col[1])
        h_header = self.tv.horizontalHeader()
        h_header.setMinimumSectionSize(1)
        h_header.setSectionResizeMode(QHeaderView.Fixed)
        h_header.resizeSection(0, 10)
        v_header = self.tv.verticalHeader()
        v_header.setDefaultSectionSize(24)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount() \
            and 0 <= index.column() < self.columnCount()):
            return QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype
        val = self._dataframe.iloc[row][col]
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return QVariant()
            else:
                return str(val)
        elif role == Qt.FontRole:
            font = QFont()
            font.setPointSize(11)
            return font
        elif role == Qt.ForegroundRole:
            if index.row() == self.tv.currentIndex().row():
                return QColor(Qt.white)
            else:
                return QColor(Qt.black)
        elif role == Qt.BackgroundRole:
            if index.row() == self.tv.currentIndex().row():
                gradient = QLinearGradient(0, 0, 66, 0)
                gradient.setColorAt(0, QColor(0, 0, 0, 128))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
                if index.column() == 0:
                    return QColor(0, 0, 0, 128)
                else:
                    return QBrush(gradient)
        if role == ValueRole:
            return val
        if role == DataFrameModel.DtypeRole:
            return dt
        return QVariant()


class WDfDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        selected = option.state & QStyle.State_Selected
        if index.column() == 0:
            s_data = index.data(ValueRole)
            if s_data == 0:
                color = QColor(123, 123, 123)  # szary
            # elif s_data == 1:
            #     color = QColor(224, 0, 0)  # czerwony
            elif s_data == 1:
                color = QColor(180, 40, 180)  # fioletowy
            elif s_data == 2:
                color = QColor(40, 140, 40)  # zielony
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            pen = painter.pen()
            pen.setStyle(Qt.NoPen)
            painter.setPen(pen)
            painter.setBrush(color)
            rect_1 = QRect(option.rect)
            rect_1.adjust(2, 2, -3, -2)
            painter.drawRoundedRect(rect_1, 2, 2)
            painter.restore()
        if selected:
            gradient = QLinearGradient(0, 0, 66, 0)
            gradient.setColorAt(0, QColor(0, 0, 0, 255))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(QPen(gradient, 1))
            rect_2 = QRect(option.rect)
            painter.drawLine(rect_2.topLeft(), rect_2.topRight())
            painter.drawLine(rect_2.bottomLeft(), rect_2.bottomRight())

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        selected = option.state & QStyle.State_Selected
        focused = option.state & QStyle.State_HasFocus
        if selected:
            option.state = option.state & ~QStyle.State_Selected
        if focused:
            option.state = option.state & ~QStyle.State_HasFocus


class CmbDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.data(Qt.AccessibleDescriptionRole) == "separator":
            painter.setPen(Qt.white)
            painter.drawLine(option.rect.left() + 10, option.rect.center().y(), option.rect.right() - 7 , option.rect.center().y())

    def sizeHint(self, option, index):
        s = QStyledItemDelegate.sizeHint(self, option, index)
        if index.data(Qt.AccessibleDescriptionRole) == "separator":
            s.setHeight(11)
        return s


class CurrentThread(QObject):
    """Obiekt referencji głównego wątku QGIS'a - potrzebna do komunikacji wydzielonego wątku z wątkiem głównym."""

    _on_execute = pyqtSignal(object, tuple, dict)

    def __init__(self):
        super(QObject, self).__init__()
        self._on_execute.connect(self._execute_in_thread)

    def execute(self, f, args, kwargs):
        self._on_execute.emit(f, args, kwargs)

    def _execute_in_thread(self, f, args, kwargs):
        f(*args, **kwargs)

main_thread = CurrentThread()


def run_in_main_thread(f):
    """Uruchamia funkcję w wątku głównym QGIS z poziomu wątku wydzielonego."""
    def result(*args, **kwargs):
        main_thread.execute(f, args, kwargs)
    return result


def threading_func(f):
    """Dekorator dla funkcji zwracającej wartość i działającej poza głównym wątkiem QGIS'a."""
    def start(*args, **kwargs):
        def run():
            try:
                th.ret = f(*args, **kwargs)
            except:
                th.exc = sys.exc_info()
        def get(timeout=None):
            th.join(timeout)
            if th.exc:
                raise th.exc[1]
            return th.ret
        th = Thread(None, run)
        th.exc = None
        th.get = get
        th.start()
        return th
    return start
