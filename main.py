#!/usr/bin/python
import os

from qgis.PyQt.QtWidgets import QMessageBox
from typing import List

from .classes import PgConn

# Zmienne globalne
user_login = os.getlogin()
user_id = int()
user_name = ""
dlg = None
teams = List[tuple]
team_i = int()
team_t = ""

def pass_dlg(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

def db_login():
    """Logowanie do bazy danych."""
    db = PgConn() # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie aliasu systemowego w tabeli users
    sql = "SELECT user_id, t_user_alias, t_user_name, i_active_team FROM users WHERE t_user_alias = '" + user_login + "';"
    if db: # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res: # Alias użytkownika znajduje się w tabeli users - logujemy
            global user_id
            user_id = res[0]  # Globalna zmienna user_id
            global user_name
            user_name = res[2]  # Globalna zmienna user_name
            if res[3]:  # Użytkownik ma zdefiniowany aktywny team
                global team_i
                team_i = res[3]  # Globalna zmienna team_i
            QMessageBox.information(None, "Logowanie...", "Użytkownik " + user_name + " zalogował się do systemu MOEK.")
            return True
        else: # Użytkownika nie ma w tabeli users - nie logujemy
            QMessageBox.warning(None, "Logowanie...", "Użytkownik " + user_login + " nie ma dostępu do systemu MOEK.")
            return False
    else:
        return False