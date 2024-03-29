#!/usr/bin/python
import time

from PyQt5.QtCore import QTimer
from qgis.core import QgsProject, QgsFeature, QgsApplication
from qgis.utils import iface

from .classes import PgConn

# Zmienne globalne:
dlg = None
powiat_m = None
vn = None
vn_ids = []  # type: ignore

# Stałe globalne:
SQL_1 = "SELECT vn_id, x_row, y_row, b_done FROM team_"
SQL_2 = ".team_viewnet WHERE user_id = "
SQL_3 = "_row "
SQL_4 = "UPDATE team_"
SQL_5 = " AND b_done is False ORDER BY vn_id"

def dlg_viewnet(_dlg):
    """Przekazanie referencji interfejsu dockwiget'u do zmiennej globalnej."""
    global dlg
    dlg = _dlg

class SelVN:
    """Klasa przechowywująca parametry wybranego vn'a."""
    l_btn = 0
    d_btn = None

    def __init__(self, l=-1, x=-1, y=-1, d=None):
        self.l = l
        self.x = x
        self.y = y
        self.d = d

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
            # Włączenie/wyłączenie skrótów klawiszowych:
            if dlg.seq_dock.box.currentIndex() == 0 and dlg.p_vn.box.currentIndex() == 0:
                # Nie może być włączony setup vn lub seq
                dlg.hk_vn = False if val == 1 else True
            if val == 1:
                vn_btn_enable(False)  # Wyłączenie przycisków
            elif val == 2:
                vn_btn_enable(True)  # Włączenie przycisków

    def d_chk(self, val):
        """Zmiana atrybutu d (b_done) vn'a i rekonfiguracja przycisków vn."""
        if val != self.d_btn:
            self.d_btn = val
            if val == False:
                dlg.button_cfg(dlg.p_vn.widgets["btn_vn_done"],'vn_doneT', tooltip=u'oznacz jako "SPRAWDZONE"')
                dlg.button_cfg(dlg.p_vn.widgets["btn_vn_doneF"],'vn_doneTf', tooltip=u'oznacz jako "SPRAWDZONE" i idź do następnego')
            if val == True:
                dlg.button_cfg(dlg.p_vn.widgets["btn_vn_done"],'vn_doneF', tooltip=u'oznacz jako "NIESPRAWDZONE"')
                dlg.button_cfg(dlg.p_vn.widgets["btn_vn_doneF"],'vn_doneTf', tooltip=u'oznacz jako "SPRAWDZONE" i idź do następnego')

def vn_btn_enable(state):
    """Włączenie lub wyłączenie przycisków vn."""
    buttons = [dlg.p_vn.widgets["btn_vn_sel"],
               dlg.p_vn.widgets["btn_vn_zoom"],
               dlg.p_vn.widgets["btn_vn_done"],
               dlg.p_vn.widgets["btn_vn_doneF"]]
    for button in buttons:
        button.setEnabled(state)

def vn_change(vn_layer, feature):
    """Zmiana wybranego vn'a przy użyciu maptool'a"""
    dlg.mt.init("multi_tool")  # Wyłączenie maptool'a
    # Zmiana wybranego vn'a, jeśli maptool przechwycił obiekt vn'a
    if vn_layer:
        t_l = feature.attributes()[vn_layer.fields().indexFromName('vn_id')]
        t_x = feature.attributes()[vn_layer.fields().indexFromName('x_row')]
        t_y = feature.attributes()[vn_layer.fields().indexFromName('y_row')]
        t_d = feature.attributes()[vn_layer.fields().indexFromName('b_done')]
        vn_set_sel(t_l, t_x, t_y, t_d)  # Zmieniamy na vn'a o ustalonych parametrach
        stage_refresh()

def vn_powsel(pow_layer, feature):
    """Zaznaczenie vn'ów, znajdujących się w obrębie wybranego powiatu."""
    global vn_ids
    dlg.mt.init("multi_tool")  # Wyłączenie maptool'a
    if pow_layer:  # Kliknięto na obiekt z właściwej warstwy
        sel_geom = feature.geometry()  # Geometria wybranego powiatu
        select_vn(sel_geom)

def vn_polysel(geom):
    """Poligonalne zaznaczenie vn'ów."""
    dlg.mt.init("multi_tool")  # Wyłączenie maptool'a
    feature = QgsFeature()
    feature.setGeometry(geom)
    sel_geom = feature.geometry()  # Geometria zaznaczenia poligonalnego
    select_vn(sel_geom)

def select_vn(sel_geom):
    """Wybranie vn'ów znajdujących się w obrębie geometrii sel_geom."""
    global vn_ids
    vn_layer = dlg.proj.mapLayersByName("vn_all")[0]
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

def vn_set_gvars(_powiat_m, no_vn):
    """Ustawienie globalnych zmiennych dotyczących aktywnego vn dla aktywnego teamu."""
    global powiat_m, vn
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
    db = PgConn()
    if powiat_m:  # Włączony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND b_pow is True AND b_sel is True;"
    else:
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND b_sel is True;"
    if db:
        res = db.query_sel(sql, False)
        if not res: # Użytkownik nie ma wybranego vn w aktywnym teamie
            return vn_first_undone_sel()  # Wybieramy pierwszy z kolei vn
        return res  # Zwracamy parametry wybranego vn
    else:
        return

def vn_first_undone_sel():
    """Wybranie pierwszego z kolei niesprawdzonego vn."""
    db = PgConn()
    if powiat_m:  # Włączony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND b_done is False AND b_pow is True ORDER BY vn_id"
    else:
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + SQL_5
    if db:
        res = db.query_sel(sql, False)
        if res:  # Zwracamy parametry pierwszego z kolei niesprawdzonego vn'a
            return vn_set_sel(*res)
        else:
            return vn_first_sel()  # Wybieramy pierwszy z kolei vn
    else:
        return

def vn_first_sel():
    """Wybranie pierwszego z kolei vn."""
    db = PgConn()
    if powiat_m:  # Włączony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND b_pow is True ORDER BY vn_id"
    else:
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " ORDER BY vn_id"
    if db:
        res = db.query_sel(sql, False)
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
    sql = SQL_4 + str(dlg.team_i) + ".team_viewnet SET b_sel = True WHERE vn_id = " + str(t_l) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            # Aktualizacja globalów do parametrów nowowybranego vn'a
            vn.l, vn.x, vn.y, vn.d = t_l, t_x, t_y, t_d
        else:
            print("Nie udało się zmienić wybranego vn!")
    return vn.l, vn.x, vn.y, vn.d

def vn_set_clear():
    """Ustawienie b_sel wszystkich vn'ów użytkownika na False."""
    db = PgConn()
    sql = SQL_4 + str(dlg.team_i) + ".team_viewnet SET b_sel = False WHERE user_id = " + str(dlg.user_id) + " AND b_sel = True;"
    if db:
        db.query_upd(sql)
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
    if dlg.seq_dock.widgets["sqb_seq"].num > 0:  # Włączony tryb sekwencyjnego wczytywania podkładów mapowych
        dlg.seq_dock.widgets["sqb_seq"].player()
    else:
        vn_zoom()
        stage_refresh()

def vn_next():
    """Ustalenie parametrów pierwszego niesprawdzonego vn'a."""
    db = PgConn()
    if powiat_m:  # Włączony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND vn_id > " + str(vn.l) + " AND b_pow is True AND b_done is False ORDER BY vn_id"
    else:
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND vn_id > " + str(vn.l) + SQL_5
    if db:
        res = db.query_sel(sql, False)
        if res:  # Po wskazanej stronie jest jeszcze vn - zwracamy jego parametry
           return res

def vn_first():
    """Ustalenie parametrów następnego vn'a."""
    db = PgConn()
    if powiat_m:  # Włączony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND b_pow is True AND b_done is False ORDER BY vn_id"
    else:
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + SQL_5
    if db:
        res = db.query_sel(sql, False)
        if res:  # Po wskazanej stronie jest jeszcze vn - zwracamy jego parametry
           return res

def vn_zoom(player=False):
    """Zbliżenie mapy do wybranego vn'a."""
    layer = dlg.proj.mapLayersByName("vn_sel")[0]
    layer.selectAll()
    canvas = iface.mapCanvas()
    canvas.zoomToSelected(layer)
    QgsApplication.processEvents()
    layer.removeSelection()
    canvas.refresh()

def vn_pan():
    """Wyśrodkowanie mapy na wybranego vn'a."""
    layer = dlg.proj.mapLayersByName("vn_sel")[0]
    layer.selectAll()
    canvas = iface.mapCanvas()
    canvas.panToSelected(layer)
    layer.removeSelection()
    canvas.refresh()

def vn_add():
    """Przydzielenie wybranych vn'ów do użytkownika."""
    global vn_ids
    layer = dlg.proj.mapLayersByName("vn_all")[0]
    db = PgConn()
    sql = SQL_4 + str(dlg.team_i) +".team_viewnet AS tv SET user_id = " + str(dlg.t_user_id) + " FROM (VALUES %s) AS d (vn_id) WHERE tv.vn_id = d.vn_id"
    if db:
        db.query_exeval(sql, vn_ids)
    layer.removeSelection()
    vn_ids = []
    stage_refresh()

def vn_sub():
    """Zabranie wybranych vn'ów użytkownikowi."""
    global vn_ids
    sel_ids = []
    all_layer = dlg.proj.mapLayersByName("vn_all")[0]
    user_layer = dlg.proj.mapLayersByName("vn_user")[0]
    user_ids = []
    for feat in user_layer.getFeatures():
        user_ids.append((feat["vn_id"],))
    sel_ids = [value for value in user_ids if value in vn_ids]
    db = PgConn()
    sql = SQL_4 + str(dlg.team_i) +".team_viewnet AS tv SET user_id = Null FROM (VALUES %s) AS d (vn_id) WHERE tv.vn_id = d.vn_id"
    if db:
        db.query_exeval(sql, sel_ids)
    all_layer.removeSelection()
    vn_ids = []
    stage_refresh()

def change_done(forward):
    """Zmiana parametru b_done wybranego vn'a."""
    global vn
    if forward and vn.d:  # Vn już jest oznaczony, tylko przejście do następnego
        vn_forward()
        return
    # Ustawienie przeciwnego do obecnego parametru b_done wybranego vn'a:
    t_d = False if vn.d else True
    db = PgConn()
    sql = SQL_4 + str(dlg.team_i) + ".team_viewnet SET b_done = " + str(t_d) + " WHERE vn_id = " + str(vn.l) + ";"
    if db:
        res = db.query_upd(sql)
        if res: # Udało się zaktualizować wybrany vn
            vn.d = t_d  # Aktualizacja parametru b_done wybranego vn'a
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
    db = PgConn()
    if powiat_m:  # Włączony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND b_pow is True AND " + st_row + SQL_3 + "= " + str(st_vn) + " AND " + nd_row + SQL_3 + op + " " + str(nd_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    else:
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND " + st_row + SQL_3 + "= " + str(st_vn) + " AND " + nd_row + SQL_3 + op + " " + str(nd_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    if db:
        res = db.query_sel(sql, False)
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
    db = PgConn()
    if powiat_m:  # Włączony jest tryb wyświetlania pojedynczego powiatu
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND b_pow is True AND " + st_row + SQL_3 + "= " + str(st_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    else:
        sql = SQL_1 + str(dlg.team_i) + SQL_2 + str(dlg.user_id) + " AND " + st_row + SQL_3 + "= " + str(st_vn) + " ORDER BY " + nd_row + SQL_3 + order +";"
    if db:
        res = db.query_sel(sql, False)
        if res:  # Zwracamy parametry nowowybranego vn'a
           return res

def stage_refresh():
    """Odświeżenie zawartości mapy."""
    t1 = time.perf_counter()
    iface.actionDraw().trigger()
    iface.mapCanvas().refresh()
    t2 = time.perf_counter()
    # print(f"************* {round(t2 - t1, 2)} sek.")
