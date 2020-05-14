#!/usr/bin/python
import os

from qgis.PyQt.QtWidgets import QMessageBox

from .classes import PgConn

# Zmienne globalne
user_login = os.getlogin()
user_id = int()
user_name = ""
dlg = None
teams = []  # type: ignore
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

def teams_load():
    """Wczytanie team'ów użytkownika z bazy danych i wgranie ich do teamCB."""
    global team_i, team_t, teams
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie nazw team'ów użytkownika
    sql = "SELECT t.team_id, t.t_team_name FROM teams AS t INNER JOIN team_users AS tu ON t.team_id = tu.team_id WHERE tu.user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, True)  # Rezultat kwerendy
        if res:  # Użytkownik jest przypisany do team'ów
            teams = [(r[0],r[1]) for r in res]  # Populacja globalnej listy teams nazwami team'ów i ich id
            dlg.teamComboBox.addItems([r[1] for r in res]) # Populacja comboboxa nazwami team'ów
            db.close()
            if team_i:  # Usżytkownik ma aktywny team
                # Ustawienie aktualnej wartości team_t
                list_srch = [i for i in teams if team_i in i]
                team_t = list_srch[0][1]
            else:  # Użytkownik nie ma aktywnego team'u
                # Ustawienie wartości team_i i team_t na pierwszą pozycję z listy teams
                team_i = teams[0][0]
                team_t = teams[0][1]
            dlg.teamComboBox.setCurrentText(team_t)  # Ustawienie cb na aktualny team_t
            return True
        else: # Użytkownik nie ma przypisanych teamów
            QMessageBox.warning(None, "Problem", "Nie jesteś członkiem żadnego zespołu. Skontaktuj się z administratorem systemu.")
            db.close()
            return False
    else:
        return False
