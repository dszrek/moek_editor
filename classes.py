#!/usr/bin/python

import psycopg2
import psycopg2.extras
import os.path

from qgis.PyQt.QtWidgets import QMessageBox
from configparser import ConfigParser
from qgis.gui import QgsMapToolIdentify, QgsMapTool, QgsRubberBand
from qgis.core import QgsGeometry, QgsWkbTypes
from qgis.PyQt.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence

DB_SOURCE = "MOEK"

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
        # uri = 'dbname="moek_ripper" host=localhost port=5432 user="pgi_user" table="public"."mv_team_powiaty" (geom) sql=team_id = ' + str(team_i)
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

class IdentMapTool(QgsMapToolIdentify):
    """Maptool do zaznaczania obiektów z wybranej warstwy."""
    identified = pyqtSignal(object, object)

    def __init__(self, canvas, layer):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        result = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, [self.layer], self.VectorLayer)
        if len(result) > 0:
            self.identified.emit(result[0].mLayer, result[0].mFeature)
        else:
            self.identified.emit(None, None)

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
