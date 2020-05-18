#!/usr/bin/python

import psycopg2
import os.path

from qgis.PyQt.QtWidgets import QMessageBox
from configparser import ConfigParser


class PgConn:
    """Połączenie z bazą PostgreSQL przez psycopg2."""
    _instance = None

    def __new__(cls):
        """Próba połączenia z db."""
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            try:
                #print("Próba połączenia z bazą PostgreSQL...")
                cfg = CfgPars()
                params = cfg.psycopg2()
                connection = PgConn._instance.connection = psycopg2.connect(**params)
                cursor = PgConn._instance.cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                cursor.fetchone()
            except Exception as error:
                QMessageBox.critical(None, "Połączenie z bazą danych", "Połączenie nie zostało nawiązane. \n Błąd: {}".format(error))
                PgConn._instance = None
        return cls._instance

    def __init__(self):
        self.connection = self._instance.connection
        self.cursor = self._instance.cursor

    def query_sel(self, query, all):
        """Wykonanie kwerendy SELECT."""
        try:
            self.cursor.execute(query)
            if all:
                result = self.cursor.fetchall()
            else:
                result = self.cursor.fetchone()
        except Exception as error:
            print('Błąd w trakcie wykonywania kwerendy "{}", {}'.format(query, error))
            PgConn._instance = None
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
            print('Błąd w trakcie wykonywania kwerendy "{}", {}'.format(query, error))
            #PgConn._instance = None
            self.connection.rollback()
            return
        else:
            return result

    def close(self):
        """Zamykanie połączenia i czyszczenie instancji."""
        if PgConn._instance is not None:
            self.cursor.close()
            self.connection.close()
            PgConn._instance = None

    def __del__(self):
        self.close()


class CfgPars(ConfigParser):
    """Parser parametrów konfiguracji połączenia z bazą danych."""
    def __init__(self, filename='database.ini', section='intranet'):
        super().__init__()
        self.filename = self.resolve(filename)
        self.section = section
        self.read(self.filename)  # Pobranie zawartości pliku
        if not self.has_section(section):
            raise Exception('Sekcja {0} nie istnieje w pliku {1}!'.format(section, filename))

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
