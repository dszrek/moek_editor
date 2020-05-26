#!/usr/bin/python

from qgis.core import QgsProject, QgsFeature
from qgis.utils import iface

from .classes import PgConn

# Zmienne globalne:
dlg = None
user_id = int()
team_i = int()
powiat_m = None
vn = None
hk_active = None
vn_ids = []  # type: ignore

# Stałe globalne:
SQL_1 = "SELECT vn_id, x_row, y_row, b_done FROM team_"
SQL_2 = ".team_viewnet WHERE user_id = "
SQL_3 = "_row "
SQL_4 = "UPDATE team_"
SQL_5 = " AND b_done is False ORDER BY vn_id"

def dlg_viewnet(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

class SelVN:
    """Klasa przechowywująca parametry wybranego vn'a."""
    l_btn = 0
    d_btn = None

    def __init__(self, l=-1, x=-1, y=-1, d=None):
        """Inicjalizator."""
        self.l = l
        self.x = x
        self.y = y
        self.d = d

    @staticmethod
    def _active(val):
        """Włączenie/wyłączenie skrótów klawiszowych"""
        global hk_active
        if val != hk_active:
            if val == True:
                hk_active = True
                dlg.toggle_hk(True)  # Aktywacja skrótów klawiszowych
            elif val == False:
                if hk_active:
                    dlg.toggle_hk(False)  # Deaktywacja skrótów klawiszowych
                hk_active = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        if attr == "l":
            self.l_chk(val)
        elif attr == "d":
            self.d_chk(val)
        super().__setattr__(attr, val)

    def l_state(self, val):
        """Zamiana wartości atrybutu l na unset:0, off:1 lub on:2."""
        if val == 0:
            return 1
        elif val < 0:
            return 0
        elif val > 0:
            return 2

    def l_chk(self, val):
        """Zmiana atrybutu l (vn_id) vn'a."""
        val = self.l_state(val)
        if val != self.l_btn:  # Stan atrybutu l się zmienił
            self.l_btn = val
            self.l_chg(val)

    def l_chg(self, val):
        """Włączenie lub wyłączenie przycisków vn w zależności od atrybutu l."""
        if val > 0:
            # Włączenie/wyłączenie skrótów klawiszowych
            SelVN._active(False) if val == 1 else SelVN._active(True)
            # Lista przycisków do włączenia/wyłączenia
            buttons = [dlg.btn_sel, dlg.btn_zoom, dlg.btn_done, dlg.btn_doneF]
            for button in buttons:
                if val == 1:
                    button.setEnabled(False)  # Wyłączenie przycisków
                elif val == 2:
                    button.setEnabled(True)  # Włączenie przycisków

    def d_chk(self, val):
        """Zmiana atrybutu d (b_done) vn'a i rekonfiguracja przycisków vn."""
        if val != self.d_btn:
            self.d_btn = val
            if val == False:
                dlg.button_cfg(dlg.btn_done,'vn_doneT.png', tooltip=u'oznacz jako "SPRAWDZONE"')
                dlg.button_cfg(dlg.btn_doneF,'vn_doneTf.png', tooltip=u'oznacz jako "SPRAWDZONE" i idź do następnego')
            if val == True:
                dlg.button_cfg(dlg.btn_done,'vn_doneF.png', tooltip=u'oznacz jako "NIESPRAWDZONE"')
                dlg.button_cfg(dlg.btn_doneF,'vn_doneFf.png', tooltip=u'oznacz jako "NIESPRAWDZONE" i idź do następnego')

def vn_change(vn_layer, feature):
    """Zmiana wybranego vn'a przy użyciu maptool'a"""
    unset_maptool(dlg.btn_sel)  # Dezaktywacja maptool'a
    # Zmiana wybranego vn'a, jeśli maptool przechwycił obiekt vn'a
    if vn_layer:
        t_l = feature.attributes()[vn_layer.fields().indexFromName('vn_id')]
        t_x = feature.attributes()[vn_layer.fields().indexFromName('x_row')]
        t_y = feature.attributes()[vn_layer.fields().indexFromName('y_row')]
        t_d = feature.attributes()[vn_layer.fields().indexFromName('b_done')]
        vn_set_sel(t_l, t_x, t_y, t_d)  # Zmieniamy na vn'a o ustalonych parametrach
        stage_refresh()

def vn_pow_sel(pow_layer, feature):
    """Zaznaczenie vn'ów, znajdujących się w obrębie wybranego powiatu."""
    global vn_ids
    unset_maptool(dlg.btn_vn_pow_sel)  # Dezaktywacja maptool'a
    if pow_layer:  # Kliknięto na obiekt z właściwej warstwy
        sel_geom = feature.geometry()  # Geometria wybranego powiatu
        select_vn(sel_geom)

def vn_polysel(geom):
    """Poligonalne zaznaczenie vn'ów."""
    unset_maptool(dlg.btn_vn_polysel)  # Dezaktywacja maptool'a
    feature = QgsFeature()
    feature.setGeometry(geom)
    sel_geom = feature.geometry()  # Geometria zaznaczenia poligonalnego
    select_vn(sel_geom)

def select_vn(sel_geom):
    global vn_ids
    vn_layer = QgsProject.instance().mapLayersByName("vn_all")[0]
    vn_feats = vn_layer.getFeatures()
    sel_id = []  # Lista dla wybieranych vn'ów
    # Wybranie vn'ów, które nakładają się na geometrię zaznaczenia
    if len(vn_ids) > 0:
        vn_ids = []
    for sel_vn in vn_feats:
        if sel_vn.geometry().intersects(sel_geom):
            sel_id.append(sel_vn.id())
            vn_ids.append((sel_vn["vn_id"], ))
    vn_layer.removeSelection()  # Na warstwie nie ma zaznaczonych obiektów
    vn_layer.selectByIds(sel_id)  # Selekcja wybranych vn'ów

def unset_maptool(btn):
    """Dezaktywacja aktywnego maptoola."""
    btn.setChecked(False)  # Odznaczenie przycisku
    dlg.iface.mapCanvas().unsetMapTool(dlg.maptool)

def vn_set_gvars(_user_id, _team_i, _powiat_m, no_vn):
    """Ustawienie globalnych zmiennych dotyczących aktywnego vn dla aktywnego teamu."""
    global user_id, team_i, powiat_m, vn
    user_id = _user_id
    team_i = _team_i
    powiat_m = _powiat_m
    if vn:  # Kasowanie obiektu SelVN, jeżeli już istnieje
        del vn
    vn = SelVN()
    if no_vn:  # Użytkownik nie ma przydzielonych vn w aktywnym teamie
        if vn.l:  # Resetowanie parametrów
            vn.l, vn.x, vn.y, vn.d = int(), int(), int(), None
            print("Użytkownik nie ma przydzielonych vn w aktywnym team'ie")
        return  #  Przerwanie funkcji - czekamy na przydzielenie vn
    vn.l, vn.x, vn.y, vn.d = vn_with_sel()
    print("Użytkownik ma wybrany vn. l:{}, x:{}, y:{}, d:{}".format(vn.l, vn.x, vn.y, vn.d))
    if not vn.l:
        print("Błąd pobrania parametrów wybranego vn!")

def vn_with_sel():
    """Sprawdzenie czy użytkownik ma aktywny vn w aktywnym teamie i zwrócenie jego parametrów."""
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND b_pow is True AND b_sel is True;"
    else:
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND b_sel is True;"
    if db: # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if not res: # Użytkownik nie ma wybranego vn w aktywnym teamie
            return vn_first_undone_sel()  # Wybieramy pierwszy z kolei vn
        return res  # Zwracamy parametry wybranego vn
    else:
        return

def vn_first_undone_sel():
    """Wybranie pierwszego z kolei niesprawdzonego vn."""
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND b_done is False AND b_pow is True ORDER BY vn_id"
    else:
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + SQL_5
    if db: # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res:  # Zwracamy parametry pierwszego z kolei niesprawdzonego vn'a
            return vn_set_sel(*res)
        else:
            return vn_first_sel()  # Wybieramy pierwszy z kolei vn
    else:
        return

def vn_first_sel():
    """Wybranie pierwszego z kolei vn."""
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND b_pow is True ORDER BY vn_id"
    else:
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " ORDER BY vn_id"
    if db: # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res:  # Zwracamy parametry pierwszego z kolei vn'a
            return vn_set_sel(*res)
    else:
        return

def vn_set_sel(*params):
    """Zmiana w db wybranego vn użytkownika w aktywnym teamie."""
    global vn
    t_l, t_x, t_y, t_d = params
    vn_cleared = vn_set_clear()  # Czyszczenie w db wybranego vn'a
    if not vn_cleared:  # Nie udało się wyczyścić wybranego vn'a
         return vn.l, vn.x, vn.y, vn.d  # Zwracamy poprzednio wybranego vn'a i przerywamy algorytm
    db = PgConn() # Tworzenie obiektu połączenia z db
    # Ustawienie b_sel = True dla nowo wybranego vn'a
    sql = SQL_4 + str(team_i) + ".team_viewnet SET b_sel = True WHERE vn_id = " + str(t_l) + ";"
    if db: # Udane połączenie z bazą danych
        res = db.query_upd(sql) # Rezultat kwerendy
        if res: # Udało się zaktualizować wybrany vn
            # Aktualizacja globalów do parametrów nowowybranego vn'a
            vn.l, vn.x, vn.y, vn.d = t_l, t_x, t_y, t_d
        else:
            print("Nie udało się zmienić wybranego vn!")
    return vn.l, vn.x, vn.y, vn.d

def vn_set_clear():
    """Ustawienie b_sel wszystkich vn'ów użytkownika na False."""
    db = PgConn() # Tworzenie obiektu połączenia z db
    sql = SQL_4 + str(team_i) + ".team_viewnet SET b_sel = False WHERE user_id = " + str(user_id) + " AND b_sel = True;"
    if db: # Udane połączenie z bazą danych
        db.query_upd(sql) # Rezultat kwerendy
        return True
    else:
        return False

def vn_forward():
    """Przejście do następnego niesprawdzonego vn'a."""
    new_vn = vn_next()
    if not new_vn:  # Brak następnego vn'a, trzeba wrócić do pierwszego
        new_vn = vn_first()
        if not new_vn:  # Nie udało się ustalić parametrów nowowybranego vn'a
            print("vn_forward error!")
            return
    vn_set_sel(*new_vn)  # Zmieniamy na vn'a o ustalonych parametrach
    vn_zoom()
    stage_refresh()

def vn_next():
    """Ustalenie parametrów pierwszego niesprawdzonego vn'a."""
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND vn_id > " + str(vn.l) + " AND b_pow is True AND b_done is False ORDER BY vn_id"
    else:
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND vn_id > " + str(vn.l) + SQL_5
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res:  # Po wskazanej stronie jest jeszcze vn - zwracamy jego parametry
           return res

def vn_first():
    """Ustalenie parametrów następnego vn'a."""
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND b_pow is True AND b_done is False ORDER BY vn_id"
    else:
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + SQL_5
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res:  # Po wskazanej stronie jest jeszcze vn - zwracamy jego parametry
           return res

def vn_zoom():
    """Zbliżenie mapy do wybranego vn'a."""
    layer = QgsProject.instance().mapLayersByName("vn_sel")[0]
    layer.selectAll()
    canvas = iface.mapCanvas()
    canvas.zoomToSelected(layer)
    layer.removeSelection()
    canvas.refresh()

def vn_pan():
    """Wyśrodkowanie mapy na wybranego vn'a."""
    layer = QgsProject.instance().mapLayersByName("vn_sel")[0]
    layer.selectAll()
    canvas = iface.mapCanvas()
    canvas.panToSelected(layer)
    layer.removeSelection()
    canvas.refresh()

def vn_add():
    """Przydzielenie wybranych vn'ów do użytkownika."""
    global vn_ids
    layer = QgsProject.instance().mapLayersByName("vn_all")[0]
    db = PgConn()  # Tworzenie obiektu połączenia z db
    sql = SQL_4 + str(team_i) +".team_viewnet AS tv SET user_id = " + str(user_id) + " FROM (VALUES %s) AS d (vn_id) WHERE tv.vn_id = d.vn_id"
    if db:  # Udane połączenie z db
        db.query_exeval(sql, vn_ids)  # Rezultat kwerendy
        db.close()
    layer.removeSelection()
    vn_ids = []
    stage_refresh()

def vn_sub():
    """Zabranie wybranych vn'ów użytkownikowi."""
    global vn_ids
    sel_ids = []  # Lista dla wybieranych vn'ów
    all_layer = QgsProject.instance().mapLayersByName("vn_all")[0]
    user_layer = QgsProject.instance().mapLayersByName("vn_user")[0]
    user_ids = []
    for feat in user_layer.getFeatures():
        user_ids.append((feat["vn_id"],))
    sel_ids = [value for value in user_ids if value in vn_ids]
    db = PgConn()  # Tworzenie obiektu połączenia z db
    sql = SQL_4 + str(team_i) +".team_viewnet AS tv SET user_id = Null FROM (VALUES %s) AS d (vn_id) WHERE tv.vn_id = d.vn_id"
    if db:  # Udane połączenie z db
        db.query_exeval(sql, sel_ids)  # Rezultat kwerendy
        db.close()
    all_layer.removeSelection()
    vn_ids = []
    stage_refresh()

def change_done(forward):
    """Zmiana parametru b_done wybranego vn'a."""
    global vn
    db = PgConn() # Tworzenie obiektu połączenia z db
    # Ustawienie przeciwnego do obecnego parametru b_done wybranego vn'a
    if vn.d == False:
        t_d = True
    elif vn.d == True:
        t_d = False
    sql = SQL_4 + str(team_i) + ".team_viewnet SET b_done = " + str(t_d) + " WHERE vn_id = " + str(vn.l) + ";"
    if db: # Udane połączenie z bazą danych
        res = db.query_upd(sql) # Rezultat kwerendy
        if res: # Udało się zaktualizować wybrany vn
            # Aktualizacja parametru b_done wybranego vn'a
            vn.d = t_d
            if forward:
                vn_forward()
            else:
                stage_refresh()
        else:
            print("Nie udało się zmienić parametr b_done wybranego vn!")

def hk_up_pressed():
    """Przejście do vn'a znajdującego się wyżej."""
    new_vn = vn_neighbour("v", "ls", "DESC")
    if not new_vn:  # Brak vn'ów poniżej, trzeba iść na górę kolumny
        new_vn = vn_first_last("v", "DESC")
        if not new_vn:  # Nie udało się ustalić parametrów nowowybranego vn'a
            print("hk_up error!")
            return
    vn_set_sel(*new_vn)  # Zmieniamy na vn'a o ustalonych parametrach
    vn_pan()
    stage_refresh()

def hk_down_pressed():
    """Przejście do vn'a znajdującego się niżej."""
    new_vn = vn_neighbour("v", "gr", "ASC")
    if not new_vn:  # Brak vn'ów poniżej, trzeba iść na górę kolumny
        new_vn = vn_first_last("v", "ASC")
        if not new_vn:  # Nie udało się ustalić parametrów nowowybranego vn'a
            print("hk_down error!")
            return
    vn_set_sel(*new_vn)  # Zmieniamy na vn'a o ustalonych parametrach
    vn_pan()
    stage_refresh()

def hk_left_pressed():
    """Przejście do vn'a znajdującego się po lewej stronie."""
    new_vn = vn_neighbour("h", "ls", "DESC")
    if not new_vn:  # Brak vn'ów po lewej, trzeba iść na koniec wiersza
        new_vn = vn_first_last("h", "DESC")
        if not new_vn:  # Nie udało się ustalić parametrów nowowybranego vn'a
            print("hk_left error!")
            return
    vn_set_sel(*new_vn)  # Zmieniamy na vn'a o ustalonych parametrach
    vn_pan()
    stage_refresh()

def hk_right_pressed():
    """Przejście do vn'a znajdującego się po prawej stronie."""
    new_vn = vn_neighbour("h", "gr", "ASC")
    if not new_vn:  # Brak vn'ów po prawej, trzeba wrócić do początku wiersza
        new_vn = vn_first_last("h", "ASC")
        if not new_vn:  # Nie udało się ustalić parametrów nowowybranego vn'a
            print("hk_right error!")
            return
    vn_set_sel(*new_vn)  # Zmieniamy na vn'a o ustalonych parametrach
    vn_pan()
    stage_refresh()

def vn_neighbour(axis, operand, order):
    """Sprawdzenie czy po wskazanej stronie znajduje się jakiś vn."""
    if axis == "h":
        st_row, nd_row = "y", "x"
        st_vn, nd_vn = vn.y, vn.x
    elif axis == "v":
        st_row, nd_row = "x", "y"
        st_vn, nd_vn = vn.x, vn.y
    if operand == "gr":
        op = ">"
    elif operand == "ls":
        op = "<"
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND b_pow is True AND " + st_row + SQL_3 + "= " + str(st_vn) + " AND " + nd_row + SQL_3 + op + " " + str(nd_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    else:
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND " + st_row + SQL_3 + "= " + str(st_vn) + " AND " + nd_row + SQL_3 + op + " " + str(nd_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res:  # Po wskazanej stronie jest jeszcze vn - zwracamy jego parametry
           return res

def vn_first_last(axis, order):
    """Ustalenie parametrów pierwszego lub ostatniego vn'a z wiersza lub kolumny."""
    if axis == "h":
        st_row, nd_row = "y", "x"
        st_vn, nd_vn = vn.y, vn.x
    elif axis == "v":
        st_row, nd_row = "x", "y"
        st_vn, nd_vn = vn.x, vn.y
    db = PgConn() # Tworzenie obiektu połączenia z db
    if powiat_m:  # Właczony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND b_pow is True AND " + st_row + SQL_3 + "= " + str(st_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    else:
        sql = SQL_1 + str(team_i) + SQL_2 + str(user_id) + " AND " + st_row + SQL_3 + "= " + str(st_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    if db:  # Udane połączenie z bazą danych
        res = db.query_sel(sql, False) # Rezultat kwerendy
        if res:  # Zwracamy parametry nowowybranego vn'a
           return res

def stage_refresh():
    """Odświeżenie zawartości mapy."""
    iface.actionDraw().trigger()
    iface.mapCanvas().refresh()
