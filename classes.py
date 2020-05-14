#!/usr/bin/python

import psycopg2

from qgis.PyQt.QtWidgets import QMessageBox

from .config import config

class PgConn:
    """Połączenie z bazą PostgreSQL przez psycopg2."""
    _instance = None

    def __new__(cls):
        """Próba połączenia z bazą"""
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            try:
                #print("Próba połączenia z bazą PostgreSQL...")
                params = config()
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
            if result == 1:
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
        """Zamykanie połączenia i czyszczenie instancji"""
        if PgConn._instance is not None:
            self.cursor.close()
            self.connection.close()
            PgConn._instance = None

    def __del__(self):
        self.close()