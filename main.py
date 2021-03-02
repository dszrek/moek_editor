#!/usr/bin/python
import os
import time as tm

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsReadWriteContext, QgsProject, QgsDataSourceUri, QgsVectorLayer, QgsWkbTypes
from PyQt5.QtXml import QDomDocument
from qgis.utils import iface

from .classes import PgConn, CfgPars
from .viewnet import vn_set_gvars, stage_refresh

# Stałe globalne
SQL_1 = " WHERE user_id = "

USER = ""

# Zmienne globalne

dlg = None
vn_setup = False

def dlg_main(_dlg):
    """Przekazanie referencji interfejsu dockwiget'u do zmiennej globalnej."""
    global dlg
    dlg = _dlg

def db_login():
    """Logowanie do bazy danych."""
    # print("[db_login]")
    user_login = os.getlogin().lower() if USER == "" else USER
    db = PgConn()
    # Wyszukanie aliasu systemowego w tabeli users:
    sql = "SELECT user_id, t_user_name, i_active_team FROM users WHERE t_user_alias = '" + user_login + "' AND b_active = true;"
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
    sql = "SELECT t.team_id, t.t_team_name FROM teams AS t INNER JOIN team_users AS tu ON t.team_id = tu.team_id WHERE tu.user_id = " + str(dlg.user_id) + " AND b_active = true;"
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
    """Aktualizacja warstwy powiaty."""
    # print("[pow_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        uri = params + 'table="team_' + str(dlg.team_i) + '"."powiaty" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "'"
    else:  # Tryb wielu powiatów
        uri = params + 'table="team_' + str(dlg.team_i) + '"."powiaty" (geom)'
    layer = QgsProject.instance().mapLayersByName("powiaty")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy powiatów
    ark_layer_update()  # Aktualizacja warstwy z arkuszami
    flag_layer_update()  # Aktualizacja warstwy z flagami
    wyr_layer_update()  # Aktualizacja warstwy z wyrobiskami
    # auto_layer_update()  # Aktualizacja warstwy z parkingami
    # marsz_layer_update()  # Aktualizacja warstwy z marszrutami
    # zloza_layer_update()  # Aktualizacja warstwy ze złożami
    layer_zoom(layer)  # Przybliżenie widoku mapy do wybranego powiatu/powiatów
    stage_refresh()  # Odświeżenie sceny

def ark_layer_update():
    """Aktualizacja warstwy arkusze."""
    # print("[ark_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        uri = params + 'table="team_' + str(dlg.team_i) + '"."arkusze" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "'"
    else:  # Tryb wielu powiatów
        uri = params + 'table="team_' + str(dlg.team_i) + '"."arkusze" (geom)'
    layer = QgsProject.instance().mapLayersByName("arkusze")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy powiatów

def flag_layer_update():
    """Aktualizacja warstwy flagi."""
    # print("[flag_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        uri_1 = params + 'table="team_' + str(dlg.team_i) + '"."flagi" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "' AND b_fieldcheck = True"
        uri_2 = params + 'table="team_' + str(dlg.team_i) + '"."flagi" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "' AND b_fieldcheck = False"
    else:  # Tryb wielu powiatów
        uri_1 = params + 'table="team_' + str(dlg.team_i) + '"."flagi" (geom) sql=b_fieldcheck = True'
        uri_2 = params + 'table="team_' + str(dlg.team_i) + '"."flagi" (geom) sql=b_fieldcheck = False'
    lyr_1 = QgsProject.instance().mapLayersByName("flagi_z_teren")[0]
    lyr_2 = QgsProject.instance().mapLayersByName("flagi_bez_teren")[0]
    # Zmiana zawartości warstwy flagi:
    pg_layer_change(uri_1, lyr_1)
    pg_layer_change(uri_2, lyr_2)

def wyr_layer_update(check=True):
    """Aktualizacja warstw z wyrobiskami."""
    if check:
    # Sprawdzenie, czy wszystkie wyrobiska mają przypisane powiaty
    # i dokonanie aktualizacji, jeśli występują braki:
        wyr_powiaty_check()
    # Stworzenie listy wyrobisk z aktywnych powiatów:
    pows = active_pow_listed()
    dlg.obj.wyr_ids = get_wyr_ids("wyr_pow", "pow_id", pows)
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.obj.wyr_ids:
        uri_1 = params + 'table="team_' + str(dlg.team_i) + '"."wyrobiska" (centroid) sql=wyr_id IN (' + str(dlg.obj.wyr_ids)[1:-1] + ')'
        uri_2 = params + 'table="team_' + str(dlg.team_i) + '"."wyr_geom" (geom) sql=wyr_id IN (' + str(dlg.obj.wyr_ids)[1:-1] + ')'
    else:
        uri_1 = params + 'table="team_' + str(dlg.team_i) + '"."wyrobiska" (centroid) sql=wyr_id = 0'
        uri_2 = params + 'table="team_' + str(dlg.team_i) + '"."wyr_geom" (geom) sql=wyr_id = 0'
    lyr_1 = QgsProject.instance().mapLayersByName("wyr_point")[0]
    lyr_2 = QgsProject.instance().mapLayersByName("wyr_poly")[0]
    # Zmiana zawartości warstw z wyrobiskami:
    pg_layer_change(uri_1, lyr_1)
    pg_layer_change(uri_2, lyr_2)

def wyr_powiaty_check():
    """Sprawdza, czy wszystkie wyrobiska zespołu mają wpisy w tabeli 'wyr_pow'.
    Jeśli nie, to przypisuje je na podstawie geometrii poligonalnej lub punktowej."""
    wyr_ids = get_wyr_ids("wyrobiska")
    wyr_pow_ids = get_wyr_ids("wyr_pow")
    wyr_id_diff = list_diff(wyr_ids, wyr_pow_ids)
    if not wyr_id_diff:
        return
    # Uzupełnienie brakujących rekordów w tabeli 'wyr_pow':
    wyr_poly_ids = []
    wyr_point_ids = []
    for wyr in wyr_id_diff:
        wyr_poly_ids.append(wyr) if wyr_poly_exist(wyr) else wyr_point_ids.append(wyr)
    print(f"wyr_poly_ids: {wyr_poly_ids}")
    print(f"wyr_point_ids: {wyr_point_ids}")
    # Pozyskanie informacji o powiatach z geometrii poligonalnej:
    if wyr_poly_ids:
        wyr_polys = get_poly_from_ids(wyr_poly_ids)
        for wyr_poly in wyr_polys:
            wyr_powiaty_change(wyr_poly[0], wyr_poly[1])
    # Pozyskanie informacji o powiatach z geometrii punktowej:
    if wyr_point_ids:
        wyr_pts = get_point_from_ids(wyr_point_ids)
        for wyr_pt in wyr_pts:
            wyr_powiaty_change(wyr_pt[0], wyr_pt[1])

def get_poly_from_ids(wyr_ids):
    """Zwraca listę z geometriami poligonalnymi wyrobisk na podstawie ich id."""
    wyr_polys = []
    with CfgPars() as cfg:
        params = cfg.uri()
    table = '"team_' + str(dlg.team_i) + '"."wyr_geom"'
    sql = "wyr_id IN (" + str(wyr_ids)[1:-1] + ")"
    uri = f'{params} table={table} (geom) sql={sql}'
    lyr_poly = QgsVectorLayer(uri, "temp_wyr_poly", "postgres")
    feats = lyr_poly.getFeatures()
    for feat in feats:
        wyr_polys.append((feat.attribute("wyr_id"), feat.geometry()))
    del lyr_poly
    return wyr_polys

def get_point_from_ids(wyr_ids):
    """Zwraca listę z geometriami punktowymi wyrobisk na podstawie ich id."""
    wyr_pts = []
    with CfgPars() as cfg:
        params = cfg.uri()
    table = '"team_' + str(dlg.team_i) + '"."wyrobiska"'
    sql = "wyr_id IN (" + str(wyr_ids)[1:-1] + ")"
    uri = f'{params} table={table} (centroid) sql={sql}'
    lyr_pt = QgsVectorLayer(uri, "temp_wyr_pt", "postgres")
    feats = lyr_pt.getFeatures()
    for feat in feats:
        wyr_pts.append((feat.attribute("wyr_id"), feat.geometry()))
    del lyr_pt
    return wyr_pts

def wyr_poly_exist(wyr_id):
    """Zwraca geometrię poligonalną wyrobiska."""
    db = PgConn()
    sql = "SELECT geom FROM team_" + str(dlg.team_i) + ".wyr_geom WHERE wyr_id = " + str(wyr_id) + ";"
    if db:
        res = db.query_sel(sql, False)
        if res:
            return res[0]
        else:
            return None

def get_wyr_ids(table, col_name=None, vals=None):
    """Zwraca listę unkalnych wyr_id z podanej tabeli."""
    db = PgConn()
    extras = f" WHERE {col_name} IN ({str(vals)[1:-1]})" if col_name else ""
    sql = "SELECT DISTINCT wyr_id FROM team_" + str(dlg.team_i) + "." + table + extras + " ORDER BY wyr_id;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if len(res) > 1:
                return list(zip(*res))[0]
            else:
                return list(res[0])
        else:
            return None

def list_diff(l1, l2):
    return (list(list(set(l1)-set(l2)) + list(set(l2)-set(l1))))

def active_pow_listed():
    """Zwraca listę z numerami aktywnych powiatów."""
    pows = []
    lyr_pow = QgsProject.instance().mapLayersByName("powiaty")[0]
    feats = lyr_pow.getFeatures()
    for feat in feats:
        pows.append(feat.attribute("pow_id"))
    return pows

def wyr_powiaty_change(wyr_id, geom):
    """Aktualizuje tabelę 'wyr_pow' po zmianie geometrii wyrobiska."""
    # Usunięcie poprzednich wpisów z tabeli 'wyr_pow':
    wyr_powiaty_delete(wyr_id)
    # Stworzenie listy z aktualnymi powiatami dla wyrobiska:
    p_list = wyr_powiaty_listed(wyr_id, geom)
    if not p_list:  # Brak powiatów
        print(f"Nie udało się stworzyć listy powiatów dla wyrobiska {wyr_id}")
        return
    # Wstawienie nowych rekordów do tabeli 'wyr_pow':
    wyr_powiaty_update(p_list)

def wyr_powiaty_delete(wyr_id):
    """Usunięcie z tabeli 'wyr_pow' rekordów odnoszących się do wyr_id."""
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".wyr_pow WHERE wyr_id = " + str(wyr_id) + ";"
    if db:
        res = db.query_upd(sql)
        if not res:
            print("Brak rekordów dla tego wyrobiska.")

def wyr_powiaty_update(p_list):
    """Wstawienie do tabeli 'wyr_pow' aktualnych numerów powiatów dla wyrobiska."""
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".wyr_pow(wyr_id, pow_id) VALUES %s"
    if db:
        db.query_exeval(sql, p_list)

def wyr_powiaty_listed(wyr_id, geom):
    """Zwraca listę powiatów, w obrębie których leży geometria wyrobiska."""
    p_list = []
    if geom.type() == QgsWkbTypes.PointGeometry:
        geom = geom.buffer(1., 1)
    bbox = geom.makeValid().boundingBox().asWktPolygon()
    with CfgPars() as cfg:
        params = cfg.uri()
    table = '"(SELECT pow_id, geom FROM public.powiaty)"'
    key = '"pow_id"'
    sql = "ST_Intersects(ST_SetSRID(ST_GeomFromText('" + str(bbox) + "'), 2180), geom)"
    uri = f'{params} key={key} table={table} (geom) sql={sql}'
    lyr_pow = QgsVectorLayer(uri, "powiaty_bbox", "postgres")
    feats = lyr_pow.getFeatures()
    for feat in feats:
        if geom.makeValid().intersects(feat.geometry()):
            p_list.append((wyr_id, feat.attribute("pow_id")))
    del lyr_pow
    return p_list

def auto_layer_update():
    """Aktualizacja warstwy parking."""
    # print("[parking_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    uri = params + 'table="team_' + str(dlg.team_i) + '"."auto" (geom)'
    layer = QgsProject.instance().mapLayersByName("parking")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy parking

def marsz_layer_update():
    """Aktualizacja warstwy marsz."""
    # print("[marsz_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    uri = params + 'table="team_' + str(dlg.team_i) + '"."marsz" (geom)'
    layer = QgsProject.instance().mapLayersByName("marsz")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy mnarsz

def zloza_layer_update():
    """Aktualizacja warstwy zloza."""
    # print("[flag_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        uri = params + 'key="zv_id" table="team_' + str(dlg.team_i) + '"."zloza" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "'"
    else:  # Tryb wielu powiatów
        uri = params + ' key="zv_id" table="team_' + str(dlg.team_i) + '"."zloza" (geom)'
    layer = QgsProject.instance().mapLayersByName("zloza")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy zloza

def vn_mode_changed(clicked):
    """Włączenie bądź wyłączenie viewnet."""
    # print("[vn_mode_changed:", clicked, "]")
    if clicked:  # Włączenie/wyłączenie vn spowodowane kliknięciem w io_btn
        db_attr_change(tbl="team_users", attr="b_vn_mode", val=dlg.p_vn.is_active(), sql_bns=" AND team_id = " + str(dlg.team_i))  # Aktualizacja b_vn_mode w db
    else:  # Włączenie/wyłączenie vn spowodowane zmianą team'u
        # Wczytanie z db b_vn_mode dla nowowybranego team'u i ustawienie trybu active dla p_vn:
        dlg.p_vn.active = db_attr_check("b_vn_mode")
    if not dlg.p_vn.is_active():  # Vn jest wyłączony
        dlg.hk_vn = False  # Wyłączenie skrótów klawiszowych
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

def vn_cfg(seq=0):
    """Wejście lub wyjście z odpowiedniego trybu konfiguracyjnego panelu viewnet (vn_setup lub sekwencje podkładów mapowych)."""
    if dlg.p_vn.bar.cfg_btn.isChecked():  # Przycisk konfiguracyjny został wciśnięty
        if dlg.hk_vn:  # Skróty klawiszowe vn włączone
            dlg.t_hk_vn = True  # Zapamiętanie stanu hk_vn
        dlg.hk_vn = False  # Wyłączenie skrótów klawiszowych do obsługi vn
        if seq == 0:  # Włączenie trybu vn_setup
            vn_setup_mode(True)
        else:  # Włączenie ustawień którejś z sekwencji
            dlg.p_vn.widgets["sqb_seq"].enter_setup(seq)
            # dlg.p_vn.box.setCurrentIndex(seq)
    else:  # Przycisk konfiguracyjny został wyciśnięty
        if dlg.t_hk_vn:  # Przed włączeniem trybu vn_setup były aktywne skróty klawiszowe
            dlg.hk_vn = True  # Ponowne włączenie skrótów klawiszowych do obsługi vn
            dlg.t_hk_vn = False
        if dlg.p_vn.box.currentIndex() == 4:  # Wychodzenie z trybu vn_setup
            vn_setup_mode(False)
        else:  # Wychodzenie z ustawień któreś z sekwencji
            dlg.p_vn.widgets["sqb_seq"].exit_setup()

def vn_setup_mode(b_flag):
    """Włączenie lub wyłączenie trybu ustawień viewnet."""
    # print("[vn_setup_mode:", b_flag, "]")
    global vn_setup
    dlg.mt.tool_off()  # Wyłączenie maptool'a (mógł być uruchomiony)
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
        dlg.p_vn.box.setCurrentIndex(4)  # zmiana strony p_vn
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
        vn_mode_changed(False)
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

def db_attr_change(tbl, attr, val, sql_bns, user=True):
    """Zmiana atrybutu w db."""
    # print("[db_attr_change(", tbl, ",", attr, "):", val, "]")
    db = PgConn()
    # Aktualizacja atrybutu (attr) w tabeli (tbl) na wartość (val):
    if user:
        sql = "UPDATE " + tbl + " SET " + attr + " = " + str(val) + SQL_1 + str(dlg.user_id) + sql_bns + ";"
    else:
        sql = "UPDATE " + tbl + " SET " + attr + " = " + str(val) + sql_bns + ";"
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

def block_panels(_panel, value):
    """Zablokowanie wszystkich paneli prócz wybranego."""
    for panel in dlg.panels:
        if panel != _panel or panel == "p_map":
            panel.setEnabled(not value)
