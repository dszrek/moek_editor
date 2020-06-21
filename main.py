#!/usr/bin/python
import os

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsReadWriteContext, QgsProject
from PyQt5.QtXml import QDomDocument
from qgis.utils import iface

from .classes import PgConn, CfgPars
from .viewnet import vn_set_gvars

# Stałe globalne
SQL_1 = " WHERE user_id = "

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
powiat_m = None
t_powiat_m = None
vn_setup = False

def dlg_main(_dlg):
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
            # QMessageBox.information(None, "Logowanie...", "Użytkownik " + user_name + " zalogował się do systemu MOEK.")
            return True
        else: # Użytkownika nie ma w tabeli users - nie logujemy
            QMessageBox.warning(None, "Logowanie...", "Użytkownik " + user_login + " nie ma dostępu do systemu MOEK.")
            return False
    else:
        return False

def teams_load():
    print("[teams_load]")
    """Wczytanie team'ów użytkownika z bazy danych i wgranie ich do combobox'a."""
    global team_i, team_t, teams
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie nazw team'ów użytkownika
    sql = "SELECT t.team_id, t.t_team_name FROM teams AS t INNER JOIN team_users AS tu ON t.team_id = tu.team_id WHERE tu.user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, True)  # Rezultat kwerendy
        if res:  # Użytkownik jest przypisany do team'ów
            teams = [(r[0], r[1]) for r in res]  # Populacja globalnej listy teams
            dlg.p_team.box.widgets["cmb_team_act"].addItems([r[1] for r in res]) # Populacja combobox'a nazwami team'ów
            db.close()
            if team_i:  # Użytkownik ma aktywny team
                # Ustawienie aktualnej wartości team_t
                list_srch = [i for i in teams if team_i in i]
                team_t = list_srch[0][1]
            else:  # Użytkownik nie ma aktywnego team'u
                # Ustawienie wartości team_i i team_t na pierwszą pozycję z listy teams
                team_i = teams[0][0]
                team_t = teams[0][1]
            dlg.p_team.box.widgets["cmb_team_act"].setCurrentText(team_t)  # Ustawienie cb na aktualny team_t
            # teams_cb_changed()  # Sposób na kontynuowanie procesu intializacji systemu
            # Podłączenie eventu zmiany team'u w cb
            dlg.p_team.box.widgets["cmb_team_act"].currentIndexChanged.connect(teams_cb_changed)
            return True
        else: # Użytkownik nie ma przypisanych teamów
            QMessageBox.warning(None, "Problem", "Nie jesteś członkiem żadnego zespołu. Skontaktuj się z administratorem systemu.")
            db.close()
            return False
    else:
        return False

def teams_cb_changed():
    """Zmiana w cb aktywnego team'u."""
    print("[teams_cb_changed]")
    global team_t, team_i
    t_team_t = dlg.p_team.box.widgets["cmb_team_act"].currentText()  # Tymczasowy team_t
    list_srch = [t for t in teams if t_team_t in t]
    t_team_i = list_srch[0][0]  # Tymczasowy team_i
    # Aktualizacja i_active_team w db
    db_act_team_changed = db_act_team_change(t_team_i)
    if db_act_team_changed:  # Udana zmiana i_active_team w db
        team_t = t_team_t
        team_i = t_team_i
        print("Pomyślnie załadowano team: ", team_t)
        # Próba odłączenia sygnału zmiany cmb_pow_act
        try:
            dlg.p_pow.box.widgets["cmb_pow_act"].currentIndexChanged.disconnect(powiaty_cb_changed)
        except TypeError:
            print("cmb_pow_act nie jest podłączony.")
        powiaty_load()  # Załadowanie powiatów do combobox'a i ustawienie aktywnego powiatu
        # Podłączenie sygnału zmiany cmb_pow_act
        dlg.p_pow.box.widgets["cmb_pow_act"].currentIndexChanged.connect(powiaty_cb_changed)
    else:  # Nie udało się zmienić i_active_team - powrót do poprzedniego
        # Odłączenie eventu zmiany cb
        dlg.p_team.box.widgets["cmb_team_act"].currentIndexChanged.disconnect(teams_cb_changed)
        dlg.p_team.box.widgets["cmb_team_act"].setCurrentText(team_t)  # Przywrócenie poprzedniego stanu cb
        # Podłączenie eventu zmiany cb
        dlg.p_team.box.widgets["cmb_team_act"].currentIndexChanged.connect(teams_cb_changed)
        print("Nie udało się zmienić team'u!")

def db_act_team_change(t_team_i):
    """Zmiana aktywnego teamu użytkownika w bazie danych."""
    print("[db_act_team_change]")
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Aktualizacja i_active_team w tabeli 'users'
    sql = "UPDATE users SET i_active_team = " + str(t_team_i) + SQL_1 + str(user_id) + ";"
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
    """Wczytanie powiatów z wybranego team'u i wgranie ich do cmb_pow_act."""
    print("[powiaty_load]")
    global team_i, powiat_i, powiat_t, powiaty
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie powiatów z aktywnego team'u
    sql = "SELECT tp.pow_grp, p.t_pow_name FROM teams t JOIN team_powiaty tp ON tp.team_id = t.team_id JOIN powiaty p ON p.pow_id = tp.pow_id WHERE tp.pow_grp = tp.pow_id AND t.team_id = " + str(team_i) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, True)  # Rezultat kwerendy
        if res:  # Team posiada powiaty
            powiaty = [(r[0],r[1]) for r in res]  # Populacja globalnej listy powiatów numerami TERYT i ich nazwami
            dlg.p_pow.box.widgets["cmb_pow_act"].clear()  # Skasowanie zawartości combobox'a
            dlg.p_pow.box.widgets["cmb_pow_act"].addItems([r[1] for r in res])  # Populacja combobox'a nazwami powiatów
            db.close()
            # Pobranie atrybutu t_active_pow z db
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
            dlg.p_pow.box.widgets["cmb_pow_act"].setCurrentText(powiat_t)  # Ustawienie cb na aktualny powiat_t
            # powiaty_cb_changed()  # Sposób na kontynuowanie procesu intializacji systemu
        else:  # Do team'u nie ma przypisanych powiatów
            QMessageBox.warning(None, "Problem", "Podany zespół nie ma przypisanych powiatów. Skontaktuj się z administratorem systemu.")
            db.close()

def powiaty_cb_changed():
    """Zmiana w combobox'ie aktywnego powiatu."""
    print("[powiaty_cb_changed]")
    global powiat_t, powiat_i
    t_powiat_t = dlg.p_pow.box.widgets["cmb_pow_act"].currentText()  # Tymczasowy powiat_t
    list_srch = [t for t in powiaty if t_powiat_t in t]
    t_powiat_i = list_srch[0][0]  # Tymczasowy powiat_i
    # Aktualizacja t_active_pow w db
    db_act_pow_changed = db_act_pow_change(t_powiat_i)
    if db_act_pow_changed:  # Udana zmiana t_active_pow w db
        powiat_t = t_powiat_t
        powiat_i = t_powiat_i
        print("Ustawiono aktywny powiat: ", str(powiat_i), " | ", str(powiat_t))
        powiaty_mode_changed(clicked=False)  # Ustawienie trybu wyświetlania powiatów (jeden lub wszystkie)
    else:  # Nie udało się zmienić t_active_pow - powrót do poprzedniego
        dlg.p_pow.box.widgets["cmb_pow_act"].setCurrentText(powiat_t)  # Przywrócenie poprzedniego stanu cb
        print("Nie udało się zmienić powiatu!")

def powiaty_mode_changed(clicked):
    """Zmiana trybu wyświetlania powiatów (jeden albo wszystkie)."""
    print("[powiaty_mode_changed:", clicked, "]")
    global powiat_m
    btn_state = dlg.p_pow.io_btn.isChecked()
    if clicked:  # Zmiana powiatu spowodowana kliknięciem w checkbox
        powiat_m = btn_state
        db_pow_mode_change(powiat_m)  # Aktualizacja b_pow_mode w db
    else:  # Zmiana powiatu spowodowana zmianą team'u
        powiat_m = pow_mode_check()  # Wczytanie z db b_pow_mode dla nowowybranego team'u
        # Aktualizacja stanu p_pow
        dlg.p_pow.active = True if powiat_m else False
    powiaty_layer()  # Aktualizacja warstwy z powiatami

def act_pow_check():
    """Zwraca parametr t_active_pow z bazy danych."""
    print("[act_pow_check]")
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie t_active_pow z db
    sql = "SELECT t_active_pow FROM team_users WHERE team_id = " + str(team_i) + " AND user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False)  # Rezultat kwerendy
        if res:  # Użytkownik w aktywnym team'ie ma ustalony wybrany powiat
            return res[0]

def db_act_pow_change(t_powiat_i):
    """Zmiana aktywnego powiatu użytkownika w bazie danych."""
    print("[db_act_pow_change]")
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Aktualizacja t_active_pow w tabeli 'team_users'
    sql = "UPDATE team_users SET t_active_pow = " + str(t_powiat_i) + SQL_1 + str(user_id) + " AND team_id = " + str(team_i) + ";"
    if db:  # Udane połączenie z db
        res = db.query_upd(sql)  # Rezultat kwerendy
        db.close()
        if res:  # Udało się zaktualizować t_active_pow
            return True
        else:
            return False
    else:
        return False

def pow_mode_check():
    """Zwraca parametr b_pow_mode z bazy danych."""
    print("[pow_mode_check]")
    db = PgConn()  # Tworzenie obiektu połączenia z bazą danych
    # Wyszukanie b_pow_mode w db
    sql = "SELECT b_pow_mode FROM team_users WHERE team_id = " + str(team_i) + " AND user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False)  # Rezultat kwerendy
        if res:  # Udało się ustalić b_pow_mode
            return res[0]

def db_pow_mode_change(powiat_m):
    """Zmiana atrybutu b_pow_mode w bazie danych."""
    print("[db_pow_mode_change:", powiat_m, "]")
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Aktualizacja b_pow_mode w tabeli 'team_users'
    sql = "UPDATE team_users SET b_pow_mode = " + str(powiat_m) + SQL_1 + str(user_id) + " AND team_id = " + str(team_i) + ";"
    if db:  # Udane połączenie z db
        db.query_upd(sql)  # Rezultat kwerendy
        db.close()

def powiaty_layer():
    """Załadowanie powiatów, które należą do danego teamu."""
    print("[powiaty_layer]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if powiat_m:
        uri = params + 'table="public"."mv_team_powiaty" (geom) sql=pow_grp = ' + "'" + str(powiat_i) + "'"
    else:
        uri = params + 'table="public"."mv_team_powiaty" (geom) sql=team_id = ' + str(team_i)
    layer = QgsProject.instance().mapLayersByName("mv_team_powiaty")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy powiatów
    layer_zoom(layer)  # Ustawienie zasięgu widoku mapy do wybranych powiatów
    if not vn_mode_check():  # Viewnet jest wyłączony, przerywamy funkcję
        return
    if powiat_m: # Załadowanie vn z obszaru wybranych powiatów
        vn_pow()
    user_with_vn = user_has_vn()
    if user_with_vn:  # Użytkownik ma przydzielone vn'y w aktywnym teamie
        vn_set_gvars(user_id, team_i, powiat_m, False)  # Ustalenie parametrów aktywnego vn'a
    else:  # Użytkownik nie ma przydzielonych vn w aktywnym teamie
        vn_set_gvars(user_id, team_i, powiat_m, True)  # Ustalenie parametrów aktywnego vn'a

def user_has_vn():
    """Sprawdzenie czy użytkownik ma przydzielone vn w aktywnym teamie."""
    print("[user_has_vn]")
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = "SELECT vn_id FROM team_" + str(team_i) + ".team_viewnet WHERE user_id = " + str(user_id) + " AND b_pow is True;"
    else:
        sql = "SELECT vn_id FROM team_" + str(team_i) + ".team_viewnet WHERE user_id = " + str(user_id) + ";"
    if db: # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res: # Użytkownik ma przydzielone vn w aktywnym teamie
            return True
        else:
            return False
    else:
        return False

def vn_pow():
    """Ustalenie w db zakresu wyświetlanych vn'ów do wybranego powiatu."""
    print("[vn_pow]")
    is_vn_reset = db_vn_pow_reset()  # Resetowanie b_pow w db
    if not is_vn_reset:
        # QMessageBox.warning(None, "Problem", "Nie udało się zresetować siatki widoków. Skontaktuj się z administratorem systemu.")
        return
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Ustawienie b_pow = True dla vn'ów, które znajdują się w obrębie wybranego powiatu
    sql = "UPDATE team_" + str(team_i) +".team_viewnet AS tv SET b_pow = True FROM (SELECT tv.vn_id	FROM powiaty p JOIN team_powiaty tp ON tp.pow_id = p.pow_id JOIN team_" + str(team_i) + ".team_viewnet tv ON ST_Intersects(tv.geom, p.geom) WHERE tp.pow_grp = '" + str(powiat_i) + "') AS s WHERE tv.vn_id = s.vn_id;"
    if db:  # Udane połączenie z db
        res = db.query_upd(sql)  # Rezultat kwerendy
        db.close()
        if res:  # Udało się zaktualizować b_pow
            print("Udało się zaktualizować b_pow: ", str(powiat_i))
            return
    QMessageBox.warning(None, "Problem", "Nie udało się ustawić zakresu siatki widoków. Skontaktuj się z administratorem systemu.")

def db_vn_pow_reset():
    """Ustawienie b_pow = False dla wszystkich vn'ów użytkownika z team_viewnet."""
    print("[db_vn_pow_reset]")
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Aktualizacja t_active_pow w tabeli 'team_users'
    sql = "UPDATE team_" + str(team_i) + ".team_viewnet SET b_pow = False WHERE user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z db
        res = db.query_upd(sql)  # Rezultat kwerendy
        db.close()
        if res:  # Udało się zaktualizować b_pow
            return True
        else:
            return False
    else:
        return False

def vn_setup_mode(b_flag):
    """Włączenie lub wyłączenie trybu ustawień viewnet."""
    print("[vn_setup_mode:", b_flag, "]")
    global powiat_m, t_powiat_m, vn_setup
    if b_flag:  # Włączenie trybu ustawień vn przez wciśnięcie przycisku konfiguracji w p_vn
        vn_setup = True
        if powiat_m:
            t_powiat_m = True  # Zapamiętanie, że tryb powiatu był włączony
            powiat_m = False
        dlg.p_pow.active = False
        dlg.p_vn.box.setCurrentIndex(1)  # zmiana strony p_vn
    else:  # Wyłączenie trybu ustawień vn przez wyciśnięcie przycisku konfiguracji w p_vn
        vn_setup = False
        if t_powiat_m:  # Tryb powiat_m był tymczasowo wyłączony, następuje jego przywrócenie
            powiat_m = t_powiat_m
            t_powiat_m = None
        dlg.p_pow.active = True
        dlg.p_vn.box.setCurrentIndex(0)  # zmiana strony p_vn
    powiaty_layer()

def vn_mode_changed(clicked):
    """Włączenie bądź wyłączenie viewnet."""
    print("[vn_mode_changed:", clicked, "]")
    if clicked:  # Zmiana vn spowodowana kliknięciem w io_btn
        db_vn_mode_change(dlg.p_vn.bar.io_btn.isChecked())  # Aktualizacja b_pow_mode w db
    else:  # Zmiana vn spowodowana zmianą team'u
        # vn_mode = vn_mode_check()  # Wczytanie z db b_vn_mode dla nowowybranego team'u
        # Aktualizacja stanu p_vn
        dlg.p_vn.active = True if vn_mode_check() else False
    vn_load()  # Aktualizacja warstwy z vn

def vn_mode_check():
    """Zwraca parametr b_vn_mode z bazy danych."""
    print("[vn_mode_check]")
    db = PgConn()
    # Wyszukanie b_vn_mode w db
    sql = "SELECT b_vn_mode FROM team_users WHERE team_id = " + str(team_i) + " AND user_id = " + str(user_id) + ";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False)  # Rezultat kwerendy
        if res:  # Udało się ustalić b_vn_mode
            return res[0]

def db_vn_mode_change(value):
    """Zmiana atrybutu b_pow_mode w bazie danych."""
    print("[db_vn_mode_change:", value, "]")
    db = PgConn()  # Tworzenie obiektu połączenia z db
    # Aktualizacja b_pow_mode w tabeli 'team_users'
    sql = "UPDATE team_users SET b_vn_mode = " + str(value) + SQL_1 + str(user_id) + " AND team_id = " + str(team_i) + ";"
    if db:  # Udane połączenie z db
        db.query_upd(sql)  # Rezultat kwerendy
        db.close()

def vn_load():
    """Załadowanie vn z obszaru wybranych powiatów."""
    print("[vn_load]")
    with CfgPars() as cfg:
        params = cfg.uri()
    proj = QgsProject.instance()
    URI_CONST = params + ' table="team_'

    if powiat_m:
        SQL_POW = " AND b_pow = True"
    else:
        SQL_POW = ""

    if dlg.p_vn.is_active():
        # Warstwy vn do włączenia/wyłączenia w zależności od trybu ustawień vn
        show_layers = ["vn_user", "vn_other", "vn_null", "vn_all"] if vn_setup else ["vn_sel", "vn_user"]
        hide_layers = ["vn_sel"] if vn_setup else ["vn_other", "vn_null", "vn_all"]
    else:
        show_layers = []
        hide_layers = ["vn_sel", "vn_user", "vn_other", "vn_null", "vn_all"]

    # Włączenie/wyłączenie warstw vn
    for layer in show_layers:
        proj.layerTreeRoot().findLayer(proj.mapLayersByName(layer)[0].id()).setItemVisibilityChecked(True)
    for layer in hide_layers:
        proj.layerTreeRoot().findLayer(proj.mapLayersByName(layer)[0].id()).setItemVisibilityChecked(False)

    # Wyrażenia sql dla warstw vn
    layer_sql = {"vn_all": "",
                "vn_null": "user_id IS NULL",
                "vn_other": "user_id <> " + str(user_id) + " AND user_id IS NOT NULL",
                "vn_user": "user_id = " + str(user_id)  + SQL_POW,
                "vn_sel": "user_id = " + str(user_id) + " AND b_sel IS TRUE" + SQL_POW}

    # Usuwanie wyrażeń sql warstw wyłączonych
    [layer_sql.pop(i) for i in hide_layers if i in layer_sql.keys()]

    # Aktualizacja włączonych warstw vn
    for key, value in layer_sql.items():
        uri =  URI_CONST + str(team_i) +'"."team_viewnet" (geom) sql= ' + str(value)
        layer = QgsProject.instance().mapLayersByName(key)[0]
        pg_layer_change(uri, layer)

def pg_layer_change(uri, layer):
    """Zmiana zawartości warstwy postgis na podstawie Uri"""
    print("[pg_layer_change:", uri, layer, "]")
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

def layer_zoom(layer):
    """Zbliżenie mapy do obiektów z danej warstwy."""
    print("[layer_zoom:", layer, "]")
    layer.selectAll()
    iface.mapCanvas().zoomToSelected(layer)
    layer.removeSelection()
    iface.mapCanvas().refresh()
