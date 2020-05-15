#!/usr/bin/python
import os

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsReadWriteContext, QgsProject
from PyQt5.QtXml import QDomDocument
from qgis.utils import iface

from .classes import PgConn, CfgPars

# Zmienne globalne
user_login = "asko"  # os.getlogin()
user_id = int()
user_name = ""
dlg = None
teams = []  # type: ignore
team_i = int()
team_t = ""
powiaty = []  # type: ignore
powiat_i = int()
powiat_t = ""

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
    """Wczytanie team'ów użytkownika z bazy danych i wgranie ich do teamComboBox."""
    global team_i, team_t, teams
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie nazw team'ów użytkownika
    sql = "SELECT t.team_id, t.t_team_name FROM teams AS t INNER JOIN team_users AS tu ON t.team_id = tu.team_id WHERE tu.user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, True)  # Rezultat kwerendy
        if res:  # Użytkownik jest przypisany do team'ów
            teams = [(r[0], r[1]) for r in res]  # Populacja globalnej listy teams
            dlg.teamComboBox.addItems([r[1] for r in res]) # Populacja comboboxa nazwami team'ów
            db.close()
            if team_i:  # Użytkownik ma aktywny team
                # Ustawienie aktualnej wartości team_t
                list_srch = [i for i in teams if team_i in i]
                team_t = list_srch[0][1]
            else:  # Użytkownik nie ma aktywnego team'u
                # Ustawienie wartości team_i i team_t na pierwszą pozycję z listy teams
                team_i = teams[0][0]
                team_t = teams[0][1]
            dlg.teamComboBox.setCurrentText(team_t)  # Ustawienie cb na aktualny team_t
            teams_cb_changed()  # Sposób na kontynuowanie procesu intializacji systemu
            # Podłączenie eventu teamComboBox_changed
            dlg.teamComboBox.currentIndexChanged.connect(teams_cb_changed)
            return True
        else: # Użytkownik nie ma przypisanych teamów
            QMessageBox.warning(None, "Problem", "Nie jesteś członkiem żadnego zespołu. Skontaktuj się z administratorem systemu.")
            db.close()
            return False
    else:
        return False

def teams_cb_changed():
    """Zmiana w cb aktywnego team'u."""
    global team_t, team_i
    t_team_t = dlg.teamComboBox.currentText()  # Tymczasowy team_t
    list_srch = [t for t in teams if t_team_t in t]
    t_team_i = list_srch[0][0]  # Tymczasowy team_i
    # Aktualizacja i_active_team w db
    db_act_team_changed = db_act_team_change(t_team_i)
    if db_act_team_changed:  # Udana zmiana i_active_team w db
        team_t = t_team_t
        team_i = t_team_i
        print("Pomyślnie załadowano team: ", team_t)
        # Próba odłączenia sygnału zmiany powiatComboBox
        try:
            dlg.powiatComboBox.currentIndexChanged.disconnect(powiaty_cb_changed)
        except:
            print("powiatComboBox.currentIndexChanged nie jest podłączony.")
        powiaty_load()  # Załadowanie powiatów do combobox'a i ustawienie aktywnego powiatu
        # Podłączenie sygnału zmiany powiatComboBox
        dlg.powiatComboBox.currentIndexChanged.connect(powiaty_cb_changed)
    else:  # Nie udało się zmienić i_active_team - powrót do poprzedniego
        # Odłączenie eventu teamComboBox_changed
        dlg.teamComboBox.currentIndexChanged.disconnect(teams_cb_changed)
        dlg.teamComboBox.setCurrentText(team_t)  # Przywrócenie poprzedniego stanu cb
        # Podłączenie eventu teamComboBox_changed
        dlg.teamComboBox.currentIndexChanged.connect(teams_cb_changed)
        print("Nie udało się zmienić team'u!")

def db_act_team_change(t_team_i):
    """Zmiana aktywnego teamu użytkownika w bazie danych."""
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Aktualizacja i_active_team w tabeli 'users'
    sql = "UPDATE users SET i_active_team = " + str(t_team_i) + " WHERE user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z db
        res = db.query_upd(sql)  # Rezultat kwerendy
        db.close()
        if res:  # Udało się zaktualizować i_active_team
            return True
        else:
            return False
    else:
        return False

def powiaty_load():
    """Wczytanie powiatów z wybranego team'u i wgranie ich do powiatComboBox."""
    global team_i, powiat_i, powiat_t, powiaty
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie powiatów z aktywnego team'u
    sql = "SELECT tp.pow_grp, p.t_pow_name FROM teams t JOIN team_powiaty tp ON tp.team_id = t.team_id JOIN powiaty p ON p.pow_id = tp.pow_id WHERE tp.pow_grp = tp.pow_id AND t.team_id = " + str(team_i) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, True)  # Rezultat kwerendy
        if res:  # Team posiada powiaty
            powiaty = [(r[0],r[1]) for r in res]  # Populacja globalnej listy powiatów numerami TERYT i ich nazwami
            dlg.powiatComboBox.clear()  # Skasowanie zawartości combobox'a
            dlg.powiatComboBox.addItems([r[1] for r in res])  # Populacja combobox'a nazwami powiatów
            db.close()
            powiat_i = act_pow_check()
            if powiat_i:  # Użytkownik ma w aktywnym team'ie wybrany powiat
                # Ustawienie aktualnej wartości team_t
                list_srch = [i for i in powiaty if powiat_i in i]
                powiat_t = list_srch[0][1]
                print("team ma aktywny powiat: ", str(powiat_i), " | ", str(powiat_t))
            else:  # Użytkownik nie ma w aktywnym team'ie wybranego powiatu
                # Ustawienie wartości powiat_i i powiat_t na pierwszą pozycję z listy powiaty
                powiat_i = powiaty[0][0]
                powiat_t = powiaty[0][1]
                print("team nie ma aktywnego powiatu. Ustawiony pierwszy: ", str(powiat_i), " | ", str(powiat_t))
            dlg.powiatComboBox.setCurrentText(powiat_t)  # Ustawienie cb na aktualny powiat_t
            powiaty_cb_changed()  # Sposób na kontynuowanie procesu intializacji systemu
        else:  # Do team'u nie ma przypisanych powiatów
            QMessageBox.warning(None, "Problem", "Podany zespół nie ma przypisanych powiatów. Skontaktuj się z administratorem systemu.")
            db.close()

def powiaty_cb_changed():
    """Zmiana w cb aktywnego powiatu."""
    global powiat_t, powiat_i
    t_powiat_t = dlg.powiatComboBox.currentText()  # Tymczasowy powiat_t
    list_srch = [t for t in powiaty if t_powiat_t in t]
    t_powiat_i = list_srch[0][0]  # Tymczasowy powiat_i
    # Aktualizacja t_active_pow w db
    db_act_pow_changed = db_act_pow_change(t_powiat_i)
    if db_act_pow_changed:  # Udana zmiana t_active_pow w db
        powiat_t = t_powiat_t
        powiat_i = t_powiat_i
        print("Ustawiono aktywny powiat: ", str(powiat_i), " | ", str(powiat_t))
        # TODO: aktualizacja warstwy
    else:  # Nie udało się zmienić t_active_pow - powrót do poprzedniego
        # Odłączenie eventu powiatComboBox_changed
        dlg.powiatComboBox.currentIndexChanged.disconnect(powiaty_cb_changed)
        dlg.powiatComboBox.setCurrentText(powiat_t)  # Przywrócenie poprzedniego stanu cb
        # Podłączenie eventu powiatComboBox_changed
        dlg.powiatComboBox.currentIndexChanged.connect(powiaty_cb_changed)
        print("Nie udało ci się zmienić powiatu!")

def act_pow_check():
    """Zwraca parametr t_active_pow z bazy danych."""
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie nazw team'ów użytkownika
    sql = "SELECT t_active_pow FROM team_users WHERE team_id = " + str(team_i) + " AND user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False)  # Rezultat kwerendy
        if res:  # Użytkownik w aktywnym team'ie ma ustalony wybrany powiat
            return res[0]

def db_act_pow_change(t_powiat_i):
    """Zmiana aktywnego powiatu użytkownika w bazie danych."""
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Aktualizacja t_active_pow w tabeli 'team_users'
    sql = "UPDATE team_users SET t_active_pow = " + str(t_powiat_i) + " WHERE user_id = " + str(user_id) + " AND team_id = " + str(team_i) + ";"
    if db:  # Udane połączenie z db
        res = db.query_upd(sql)  # Rezultat kwerendy
        db.close()
        if res:  # Udało się zaktualizować t_active_pow
            return True
        else:
            return False
    else:
        return False

def powiaty_layer():
    """Załadowanie powiatów, które należą do danego teamu."""
    cfg = CfgPars()
    params = cfg.uri()
    uri = params + 'table="public"."mv_team_powiaty" (geom) sql=team_id = ' + str(team_i)
    layer = QgsProject.instance().mapLayersByName("mv_team_powiaty")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy powiatów
    # vn_load()  # Załadowanie vn z obszaru wybranych powiatów

def pg_layer_change(uri, layer):
    """Zmiana zawartości warstwy postgis na podstawie Uri"""
    xml_document = QDomDocument("style")
    xml_maplayers = xml_document.createElement("maplayers")
    xml_maplayer = xml_document.createElement("maplayer")
    context = QgsReadWriteContext()
    layer.writeLayerXml(xml_maplayer,xml_document, context)
    xml_maplayer.firstChildElement("datasource").firstChild().setNodeValue(uri)
    xml_maplayer.firstChildElement("provider").firstChild().setNodeValue("postgres")
    xml_maplayers.appendChild(xml_maplayer)
    xml_document.appendChild(xml_maplayers)
    layer.readLayerXml(xml_maplayer, context)
    iface.actionDraw().trigger()
    iface.mapCanvas().refresh()
