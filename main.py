#!/usr/bin/python
import os

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsReadWriteContext, QgsProject
from PyQt5.QtXml import QDomDocument
from qgis.utils import iface

from .classes import PgConn, CfgPars
from .viewnet import vn_set_gvars, stage_refresh

# Stałe globalne
SQL_1 = " WHERE user_id = "

# Zmienne globalne
user_login = "asko"  # os.getlogin()
dlg = None
vn_setup = False

def dlg_main(_dlg):
    """Przekazanie referencji interfejsu dockwiget'u do zmiennej globalnej."""
    global dlg
    dlg = _dlg

def db_login():
    """Logowanie do bazy danych."""
    # print("[db_login]")
    db = PgConn()
    # Wyszukanie aliasu systemowego w tabeli users:
    sql = "SELECT user_id, t_user_name, i_active_team FROM users WHERE t_user_alias = '" + user_login + "';"
    if db:
        res = db.query_sel(sql, False)
        if res: # Alias użytkownika znajduje się w tabeli users - logujemy
            user_id = res[0]
            user_name = res[1]
            if res[2]:  # Użytkownik ma zdefiniowany aktywny team
                team_i = res[2]
            print("Użytkownik " + user_name + " zalogował się do systemu MOEK.")
            return res[0], res[1], res[2]
        else: # Użytkownika nie ma w tabeli users - nie logujemy
            QMessageBox.warning(None, "Logowanie...", "Użytkownik " + user_login + " nie ma dostępu do systemu MOEK.")
            return False, False, False
    else:
        return False, False, False

def teams_load():
    """Wczytanie team'ów użytkownika z bazy danych i wgranie ich do combobox'a (cmb_team_act)."""
    # print("[teams_load]")
    db = PgConn()
    # Wyszukanie nazw team'ów użytkownika:
    sql = "SELECT t.team_id, t.t_team_name FROM teams AS t INNER JOIN team_users AS tu ON t.team_id = tu.team_id WHERE tu.user_id = " + str(dlg.user_id) + ";"
    if db:
        res = db.query_sel(sql, True)
        if res:  # Użytkownik jest przypisany do team'ów
            dlg.teams = [(r[0], r[1]) for r in res]  # Populacja globalnej listy dlg.teams
            dlg.p_team.box.widgets["cmb_team_act"].addItems([r[1] for r in res])  # Populacja combobox'a nazwami team'ów
            if dlg.team_i:  # Użytkownik ma aktywny team
                # Ustawienie aktualnej wartości dlg.team_t:
                list_srch = [i for i in dlg.teams if dlg.team_i in i]
                dlg.team_t = list_srch[0][1]
            else:  # Użytkownik nie ma aktywnego team'u
                # Ustawienie wartości dlg.team_i i dlg.team_t na pierwszą pozycję z listy dlg.teams:
                dlg.team_i = dlg.teams[0][0]
                dlg.team_t = dlg.teams[0][1]
            dlg.p_team.box.widgets["cmb_team_act"].setCurrentText(dlg.team_t)  # Ustawienie cb na aktualny dlg.team_t
            # Podłączenie eventu zmiany team'u w cb:
            dlg.p_team.box.widgets["cmb_team_act"].currentIndexChanged.connect(teams_cb_changed)
            return True
        else: # Użytkownik nie ma przypisanych teamów
            QMessageBox.warning(None, "Problem", "Nie jesteś członkiem żadnego zespołu. Skontaktuj się z administratorem systemu.")
            return False
    else:
        return False

def teams_cb_changed():
    """Zmiana w cb aktywnego team'u."""
    # print("[teams_cb_changed]")
    t_team_t = dlg.p_team.box.widgets["cmb_team_act"].currentText()  # Zapamiętanie aktualnego dlg.team_t
    list_srch = [t for t in dlg.teams if t_team_t in t]
    t_team_i = list_srch[0][0]  # Tymczasowy team_i
    # Aktualizacja i_active_team w db i zmiana globali:
    if db_attr_change(tbl="users", attr="i_active_team", val=t_team_i, sql_bns=""):
        dlg.team_t = t_team_t
        dlg.team_i = t_team_i
        print("Pomyślnie załadowano team: ", dlg.team_t)
        # Próba (bo może być jeszcze nie podłączony) odłączenia sygnału zmiany cmb_pow_act:
        try:
            dlg.p_pow.box.widgets["cmb_pow_act"].currentIndexChanged.disconnect(powiaty_cb_changed)
        except TypeError:
            print("cmb_pow_act nie jest podłączony.")
        powiaty_load()  # Załadowanie powiatów do cmb_pow_act i ustawienie aktywnego powiatu
        powiaty_mode_changed(clicked=False)  # Ustawienie parametru active dla p_pow
        # Podłączenie sygnału zmiany cmb_pow_act:
        dlg.p_pow.box.widgets["cmb_pow_act"].currentIndexChanged.connect(powiaty_cb_changed)
    else:  # Nie udało się zmienić i_active_team - powrót do poprzedniego
        # Odłączenie eventu zmiany cb:
        dlg.p_team.box.widgets["cmb_team_act"].currentIndexChanged.disconnect(teams_cb_changed)
        dlg.p_team.box.widgets["cmb_team_act"].setCurrentText(dlg.team_t)  # Przywrócenie poprzedniego stanu cb
        # Podłączenie eventu zmiany cb:
        dlg.p_team.box.widgets["cmb_team_act"].currentIndexChanged.connect(teams_cb_changed)
        print("Nie udało się zmienić team'u!")

def teamusers_load():
    """Wczytanie użytkowników z wybranego team'u i wgranie ich do cmb_teamusers."""
    # print("[teamusers_load]")
    db = PgConn()
    # Wyszukanie użytkowników z aktywnego team'u:
    sql = "SELECT tu.user_id, u.t_user_name FROM team_users tu JOIN users u ON tu.user_id = u.user_id WHERE tu.team_id = " + str(dlg.team_i) + ";"
    if db:
        res = db.query_sel(sql, True)
        if res:
            dlg.team_users = [(r[0],r[1]) for r in res]  # Populacja globalnej listy team_users numerami id użytkowników i ich nazwiskami
            dlg.p_vn.widgets["cmb_teamusers"].clear()  # Skasowanie zawartości combobox'a
            dlg.p_vn.widgets["cmb_teamusers"].addItems([r[1] for r in res])  # Populacja combobox'a nazwiskami użytkowników
            dlg.t_user_name = dlg.user_name  # Ustawienie aktywnego użytkownika na tymczasowo aktywnego użytkownika w trybie vn_setup
            list_srch = [t for t in dlg.team_users if dlg.t_user_name in t]
            dlg.t_user_id = list_srch[0][0]  # User_id tymczasowo aktywnego użytkownika
            # Aktualizacja wartości aktywnej combobox'a:
            dlg.p_vn.widgets["cmb_teamusers"].setCurrentText(dlg.t_user_name)
            # Podłączenie eventu zmiany cb:
            dlg.p_vn.widgets["cmb_teamusers"].currentIndexChanged.connect(teamusers_cb_changed)
            QgsProject.instance().mapLayersByName("vn_all")[0].selectionChanged.connect(vn_sel_changed)
            vn_sel_changed()

        else:
            print("Nie udało się wczytać użytkowników team'u do combobox'a!")

def teamusers_cb_changed():
    """Zmiana w combobox'ie (cmb_teamusers) aktywnego użytkownika w trybie vn_setup."""
    # print("[teamusers_cb_changed]")
    dlg.t_user_name = dlg.p_vn.widgets["cmb_teamusers"].currentText()  # Zapamiętanie nazwiska aktywnego w trybie vn_setup użytkownika
    list_srch = [t for t in dlg.team_users if dlg.t_user_name in t]
    dlg.t_user_id = list_srch[0][0]  # User_id tymczasowo aktywnego użytkownika
    vn_layer_update()

def powiaty_load():
    """Wczytanie powiatów z wybranego team'u i wgranie ich do cmb_pow_act."""
    # print("[powiaty_load]")
    db = PgConn()
    # Wyszukanie powiatów z aktywnego team'u:
    sql = "SELECT tp.pow_grp, p.t_pow_name FROM teams t JOIN team_powiaty tp ON tp.team_id = t.team_id JOIN powiaty p ON p.pow_id = tp.pow_id WHERE tp.pow_grp = tp.pow_id AND t.team_id = " + str(dlg.team_i) + ";"
    if db:
        res = db.query_sel(sql, True)
        if res:  # Team posiada powiaty
            dlg.powiaty = [(r[0],r[1]) for r in res]  # Populacja globalnej listy powiatów numerami TERYT i ich nazwami
            dlg.p_pow.box.widgets["cmb_pow_act"].clear()  # Skasowanie zawartości combobox'a
            dlg.p_pow.box.widgets["cmb_pow_act"].addItems([r[1] for r in res])  # Populacja combobox'a nazwami powiatów
            dlg.powiat_i = db_attr_check("t_active_pow")  # Pobranie atrybutu t_active_pow z db
            if dlg.powiat_i:  # Użytkownik ma w aktywnym team'ie wybrany powiat
                # Ustawienie aktualnej wartości dlg.powiat_t:
                list_srch = [i for i in dlg.powiaty if dlg.powiat_i in i]
                dlg.powiat_t = list_srch[0][1]
                print("team ma aktywny powiat: ", str(dlg.powiat_i), " | ", str(dlg.powiat_t))
            else:  # Użytkownik nie ma w aktywnym team'ie wybranego powiatu
                # Ustawienie wartości dlg.powiat_i i dlg.powiat_t na pierwszą pozycję z listy dlg.powiaty:
                dlg.powiat_i = dlg.powiaty[0][0]
                dlg.powiat_t = dlg.powiaty[0][1]
                print("team nie ma aktywnego powiatu. Ustawiony pierwszy: ", str(dlg.powiat_i), " | ", str(dlg.powiat_t))
            dlg.p_pow.box.widgets["cmb_pow_act"].setCurrentText(dlg.powiat_t)  # Ustawienie cb na aktualny dlg.powiat_t
        else:  # Do team'u nie ma przypisanych powiatów
            QMessageBox.warning(None, "Problem", "Podany zespół nie ma przypisanych powiatów. Skontaktuj się z administratorem systemu.")

def powiaty_mode_changed(clicked):
    """Zmiana trybu wyświetlania powiatów (jeden albo wszystkie)."""
    # print("[powiaty_mode_changed:", clicked, "]")
    if clicked:  # Zmiana trybu wyświetlania powiatów spowodowana kliknięciem w io_btn
        db_attr_change(tbl="team_users", attr="b_pow_mode", val=dlg.p_pow.is_active(), sql_bns=" AND team_id = " + str(dlg.team_i))  # Aktualizacja b_pow_mode w db
    else:  # Zmiana trybu wyświetlania powiatów spowodowana zmianą aktywnego team'u
        # Wczytanie z db b_pow_mode dla nowowybranego team'u i ustawienie trybu active dla p_pow:
        dlg.p_pow.active = db_attr_check("b_pow_mode")
    powiaty_cb_changed()

def powiaty_cb_changed():
    """Zmiana w combobox'ie (cmb_pow_act) aktywnego powiatu."""
    # print("[powiaty_cb_changed]")
    t_powiat_t = dlg.p_pow.box.widgets["cmb_pow_act"].currentText()  # Zapamiętanie nazwy aktualnego powiatu
    list_srch = [t for t in dlg.powiaty if t_powiat_t in t]
    t_powiat_i = list_srch[0][0]  # Tymczasowy powiat_i
    # Aktualizacja t_active_pow w db i zmiana globali:
    if db_attr_change(tbl="team_users", attr="t_active_pow", val=t_powiat_i, sql_bns=" AND team_id = " + str(dlg.team_i)):
        dlg.powiat_t = t_powiat_t
        dlg.powiat_i = t_powiat_i
        print("Ustawiono aktywny powiat: ", str(dlg.powiat_i), " | ", str(dlg.powiat_t))
        pow_layer_update()  # Aktualizacja warstwy z powiatami
        vn_mode_changed(clicked=False)
    else:  # Nie udało się zmienić t_active_pow - powrót do poprzedniego
        dlg.p_pow.box.widgets["cmb_pow_act"].setCurrentText(dlg.powiat_t)  # Przywrócenie poprzedniego stanu cb
        print("Nie udało się zmienić powiatu!")

def pow_layer_update():
    """Aktualizacja warstwy powiatów."""
    # print("[pow_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        uri = params + 'table="public"."mv_team_powiaty" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "'"
    else:  # Tryb wielu powiatów
        uri = params + 'table="public"."mv_team_powiaty" (geom) sql=team_id = ' + str(dlg.team_i)
    layer = QgsProject.instance().mapLayersByName("mv_team_powiaty")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy powiatów
    layer_zoom(layer)  # Przybliżenie widoku mapy do wybranego powiatu/powiatów
    stage_refresh()  # Odświeżenie sceny

def vn_mode_changed(clicked):
    """Włączenie bądź wyłączenie viewnet."""
    # print("[vn_mode_changed:", clicked, "]")
    if clicked:  # Włączenie/wyłączenie vn spowodowane kliknięciem w io_btn
        db_attr_change(tbl="team_users", attr="b_vn_mode", val=dlg.p_vn.is_active(), sql_bns=" AND team_id = " + str(dlg.team_i))  # Aktualizacja b_vn_mode w db
    else:  # Włączenie/wyłączenie vn spowodowane zmianą team'u
        # Wczytanie z db b_vn_mode dla nowowybranego team'u i ustawienie trybu active dla p_vn:
        dlg.p_vn.active = db_attr_check("b_vn_mode")
    if not dlg.p_vn.is_active():  # Vn jest wyłączony
        vn_layer_update()  # Aktualizacja warstw z vn
        return
    if dlg.p_pow.is_active():  # Włączony tryb pojedynczego powiatu
        vn_pow()  # Załadowanie vn z obszaru wybranego powiatu
    vn_layer_update()  # Aktualizacja warstw z vn
    if user_has_vn():  # Użytkownik ma przydzielone vn'y w aktywnym teamie
        vn_set_gvars(dlg.p_pow.is_active(), False)  # Ustalenie parametrów aktywnego vn'a
    else:  # Użytkownik nie ma przydzielonych vn w aktywnym teamie
        vn_set_gvars(dlg.p_pow.is_active(), True)  # Ustalenie parametrów aktywnego vn'a

def vn_pow():
    """Ustalenie w db zakresu wyświetlanych vn'ów dla wybranego powiatu/powiatów."""
    # print("[vn_pow]")
    # Resetowanie b_pow () w db
    if db_vn_pow_reset():
        print("Zresetowano b_pow w db")
    else:
        print("Nie udało się zresetować siatki widoków!")
        return
    db = PgConn()
    # Ustawienie b_pow = True dla vn'ów, które znajdują się w obrębie wybranego powiatu/powiatów:
    sql = "UPDATE team_" + str(dlg.team_i) +".team_viewnet AS tv SET b_pow = True FROM (SELECT tv.vn_id	FROM powiaty p JOIN team_powiaty tp ON tp.pow_id = p.pow_id JOIN team_" + str(dlg.team_i) + ".team_viewnet tv ON ST_Intersects(tv.geom, p.geom) WHERE tp.pow_grp = '" + str(dlg.powiat_i) + "') AS s WHERE tv.vn_id = s.vn_id;"
    if db:
        res = db.query_upd(sql)
        if res:
            print("Udało się zaktualizować b_pow: ", str(dlg.powiat_i))
            return
    QMessageBox.warning(None, "Problem", "Nie udało się ustawić zakresu siatki widoków. Skontaktuj się z administratorem systemu.")

def db_vn_pow_reset():
    """Ustawienie b_pow = False dla wszystkich vn'ów użytkownika z team_viewnet."""
    # print("[db_vn_pow_reset]")
    db = PgConn()
    # Aktualizacja b_pow = False w tabeli 'team_viewnet':
    sql = "UPDATE team_" + str(dlg.team_i) + ".team_viewnet SET b_pow = False WHERE user_id = " + str(dlg.user_id) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            return True
        else:
            return False
    else:
        return False

def user_has_vn():
    """Sprawdzenie czy użytkownik ma przydzielone vn w aktywnym teamie."""
    # print("[user_has_vn]")
    db = PgConn()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        sql = "SELECT vn_id FROM team_" + str(dlg.team_i) + ".team_viewnet WHERE user_id = " + str(dlg.user_id) + " AND b_pow is True;"
    else:  # Tryb wielu powiatów
        sql = "SELECT vn_id FROM team_" + str(dlg.team_i) + ".team_viewnet WHERE user_id = " + str(dlg.user_id) + ";"
    if db:
        res = db.query_sel(sql, False)
        if res:
            return True
        else:
            return False
    else:
        return False

def vn_setup_mode(b_flag):
    """Włączenie lub wyłączenie trybu ustawień viewnet."""
    # print("[vn_setup_mode:", b_flag, "]")
    global vn_setup
    if b_flag:  # Włączenie trybu ustawień vn przez wciśnięcie cfg_btn w p_vn
        vn_setup = True
        dlg.p_pow.t_active = dlg.p_pow.is_active()  # Zapamiętanie trybu powiatu przed ewentualną zmianą
        dlg.p_pow.active = False  # Wyłączenie trybu wybranego powiatu
        # Próba (bo może być jeszcze nie podłączone) odłączenia sygnałów:
        try:
            dlg.p_vn.widgets["cmb_teamusers"].currentIndexChanged.disconnect(teamusers_cb_changed)
            QgsProject.instance().mapLayersByName("vn_all")[0].selectionChanged.disconnect(vn_sel_changed)
        except TypeError:
            print("Obiekt nie jest jeszcze podłączony.")
        teamusers_load()  # Wczytanie użytkowników do cmb_teamusers
        dlg.p_vn.box.setCurrentIndex(1)  # zmiana strony p_vn
    else:  # Wyłączenie trybu ustawień vn przez wyciśnięcie cfg_btn w p_vn
        vn_setup = False
        dlg.p_pow.active = dlg.p_pow.t_active  # Ewentualne przywrócenie trybu powiatu sprzed zmiany
        # Próba (bo może być jeszcze nie podłączone) odłączenia sygnałów:
        try:
            dlg.p_vn.widgets["cmb_teamusers"].currentIndexChanged.disconnect(teamusers_cb_changed)
            QgsProject.instance().mapLayersByName("vn_all")[0].selectionChanged.disconnect(vn_sel_changed)
        except TypeError:
            print("Obiekt nie jest jeszcze podłączony.")
        dlg.p_vn.box.setCurrentIndex(0)  # zmiana strony p_vn
    pow_layer_update()
    vn_layer_update()

def vn_sel_changed():
    """Rekonfiguracja przycisków w zależności od stanu zaznaczenia vn'ów."""
    vn_layer = QgsProject.instance().mapLayersByName("vn_all")[0]
    value = True if vn_layer.selectedFeatureCount() > 0 else False
    dlg.p_vn.widgets["btn_vn_add"].setEnabled(value)
    dlg.p_vn.widgets["btn_vn_sub"].setEnabled(value)
    dlg.p_vn.widgets["btn_vn_unsel"].setEnabled(value)

def vn_layer_update():
    """Załadowanie vn z obszaru wybranych powiatów."""
    # print("[vn_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    proj = QgsProject.instance()
    URI_CONST = params + ' table="team_'

    # Wartość user_id w zależności od włączenia trybu vn_setup:
    _user_id = dlg.t_user_id if vn_setup else dlg.user_id

    if dlg.p_pow.is_active():
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
                "vn_other": "user_id <> " + str(_user_id) + " AND user_id IS NOT NULL",
                "vn_user": "user_id = " + str(_user_id)  + SQL_POW,
                "vn_sel": "user_id = " + str(_user_id) + " AND b_sel IS TRUE" + SQL_POW}

    # Usuwanie wyrażeń sql warstw wyłączonych
    [layer_sql.pop(i) for i in hide_layers if i in layer_sql.keys()]

    # Aktualizacja włączonych warstw vn
    for key, value in layer_sql.items():
        uri =  URI_CONST + str(dlg.team_i) +'"."team_viewnet" (geom) sql= ' + str(value)
        layer = QgsProject.instance().mapLayersByName(key)[0]
        pg_layer_change(uri, layer)

    stage_refresh()  # Odświeżenie sceny

def db_attr_check(attr):
    """Zwraca parametr z db."""
    # print("[db_attr_check:", attr, "]")
    db = PgConn()
    # Wyszukanie t_active_pow w db:
    sql = "SELECT " + attr + " FROM team_users WHERE team_id = " + str(dlg.team_i) + " AND user_id = " + str(dlg.user_id) + ";"
    if db:
        res = db.query_sel(sql, False)
        if res:
            return res[0]

def db_attr_change(tbl, attr, val, sql_bns):
    """Zmiana atrybutu w db."""
    # print("[db_attr_change(", tbl, ",", attr, "):", val, "]")
    db = PgConn()
    # Aktualizacja atrybutu (attr) w tabeli (tbl) na wartość (val):
    sql = "UPDATE " + tbl + " SET " + attr + " = " + str(val) + SQL_1 + str(dlg.user_id) + sql_bns + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            return True
        else:
            return False
    else:
        return False

def pg_layer_change(uri, layer):
    """Zmiana zawartości warstwy postgis na podstawie Uri"""
    # print("[pg_layer_change:", uri, layer, "]")
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
    iface.layerTreeView().refreshLayerSymbology(layer.id())

def layer_zoom(layer):
    """Zbliżenie mapy do obiektów z danej warstwy."""
    # print("[layer_zoom:", layer, "]")
    layer.selectAll()
    iface.mapCanvas().zoomToSelected(layer)
    layer.removeSelection()
    iface.mapCanvas().refresh()
