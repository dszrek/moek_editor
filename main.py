#!/usr/bin/python
import os
import shutil
import time as tm
import pandas as pd
import numpy as np
import xlsxwriter as xls

from PIL import Image, ImageQt, ImageEnhance
from win32com import client
from docxtpl import DocxTemplate
from qgis.core import QgsApplication, QgsVectorLayer, QgsWkbTypes, QgsReadWriteContext, QgsFeature, QgsGeometry, QgsRectangle, QgsMapSettings, QgsMapRendererCustomPainterJob, edit
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog, QDialog
from qgis.PyQt.QtCore import Qt, QDir, QSize, QRectF, QPointF
from qgis.PyQt.QtGui import QImage, QPainter, QPen, QFont, QPainterPath, QPolygonF
from PyQt5.QtXml import QDomDocument
from qgis.utils import iface

from .classes import PgConn, CfgPars
from .viewnet import vn_set_gvars, stage_refresh

# Stałe globalne:
SQL_1 = " WHERE user_id = "
PLUGIN_VER = "0.5.5"
USER = ""

# Zmienne globalne:
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
    sql = "SELECT user_id, t_user_name, i_active_team, t_plugin_ver FROM users WHERE t_user_alias = '" + user_login + "' AND b_active = true;"
    if db:
        res = db.query_sel(sql, False)
        if res: # Alias użytkownika znajduje się w tabeli users - logujemy
            user_id = res[0]
            user_name = res[1]
            if res[2]:  # Użytkownik ma zdefiniowany aktywny team
                team_i = res[2]
            print("Użytkownik " + user_name + " zalogował się do systemu MOEK.")
            # Sprawdzenie, czy zainstalowana wersja wtyczki się zmieniła:
            if PLUGIN_VER != res[3]:
                # Aktualizacja numeru zainstalowanej wersji wtyczki w db:
                version_update(res[0])
            return res[0], res[1], res[2]
        else: # Użytkownika nie ma w tabeli users - nie logujemy
            QMessageBox.warning(None, "Logowanie...", "Użytkownik " + user_login + " nie ma dostępu do systemu MOEK.")
            return False, False, False
    else:
        return False, False, False

def version_update(user_id):
    """Aktualizacja numeru wersji wtyczki w db."""
    db = PgConn()
    sql = f"UPDATE public.users SET t_plugin_ver = '{PLUGIN_VER}' WHERE user_id = {user_id}"
    if db:
        res = db.query_upd(sql)

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
    dlg.freeze_set(True)  # Zablokowanie odświeżania dockwidget'u
    dlg.obj.clear_sel()  # Odznaczenie flag, wyrobisk i punktów WN_PNE
    dlg.export_panel.pow_reset()  # Wyczyszczenie zmiennych pow_bbox i pow_all
    t_team_t = dlg.p_team.box.widgets["cmb_team_act"].currentText()  # Zapamiętanie aktualnego dlg.team_t
    list_srch = [t for t in dlg.teams if t_team_t in t]
    t_team_i = list_srch[0][0]  # Tymczasowy team_i
    # Aktualizacja i_active_team w db i zmiana globali:
    if db_attr_change(tbl="users", attr="i_active_team", val=t_team_i, sql_bns=""):
        dlg.team_t = t_team_t
        dlg.team_i = t_team_i
        print("Pomyślnie załadowano team: ", dlg.team_t)
        dlg.basemaps_and_sequences_load()  # Wczytanie ustawień podkładów i sekwencji
        dlg.cfg.cfg_vals_read()  # Wczytanie ustawień paneli i warstw do PanelManager
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
            dlg.proj.mapLayersByName("vn_all")[0].selectionChanged.connect(vn_sel_changed)
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
    dlg.freeze_set(True)  # Zablokowanie odświeżania dockwidget'u
    dlg.obj.clear_sel()  # Odznaczenie flag, wyrobisk i punktów WN_PNE
    # if clicked:  # Zmiana trybu wyświetlania powiatów spowodowana kliknięciem w io_btn
    #     dlg.cfg.set_val(name="powiaty", val=dlg.p_pow.is_active())
    # else:  # Zmiana trybu wyświetlania powiatów spowodowana zmianą aktywnego team'u
    #     Wczytanie z db b_pow_mode dla nowowybranego team'u i ustawienie trybu active dla p_pow:
    #     dlg.p_pow.active = dlg.cfg.get_val(name="powiaty")
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
        dlg.cfg.cfg_vals_read()
        vn_mode_changed(clicked=False)
    else:  # Nie udało się zmienić t_active_pow - powrót do poprzedniego
        dlg.p_pow.box.widgets["cmb_pow_act"].setCurrentText(dlg.powiat_t)  # Przywrócenie poprzedniego stanu cb
        print("Nie udało się zmienić powiatu!")
    dlg.freeze_set(False)  # Odblokowanie odświeżania dockwidget'u

def pow_layer_update():
    """Aktualizacja warstwy powiaty."""
    # print("[pow_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        uri = params + 'table="team_' + str(dlg.team_i) + '"."powiaty" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "'"
    else:  # Tryb wielu powiatów
        uri = params + 'table="team_' + str(dlg.team_i) + '"."powiaty" (geom)'
    layer = dlg.proj.mapLayersByName("powiaty")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy powiatów
    ark_layer_update()  # Aktualizacja warstwy z arkuszami
    flag_layer_update()  # Aktualizacja warstw z flagami
    wyr_layer_update()  # Aktualizacja warstw z wyrobiskami
    wn_layer_update()  # Aktualizacja warstwy z wn_pne
    parking_layer_update()  # Aktualizacja warstwy z parkingami
    marsz_layer_update()  # Aktualizacja warstwy z marszrutami
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
    layer = dlg.proj.mapLayersByName("arkusze")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy powiatów

def flag_layer_update():
    """Aktualizacja warstwy flagi."""
    # print("[flag_layer_update]")
    QgsApplication.setOverrideCursor(Qt.WaitCursor)
    # Określenie, które rodzaje flag są włączone:
    case = dlg.cfg.flag_case()
    # Aktualizacja listy flag w ObjectManager:
    dlg.obj.flag_ids = get_flag_ids(case)
    # Utworzenie listy z id flag, których rodzaje są włączone:
    sql_cases = [
        {'value': 0, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 1, 'sql_1': "user_id = {dlg.user_id} AND b_fieldcheck = True", 'sql_2': "user_id = 0"},
        {'value': 2, 'sql_1': "user_id = 0", 'sql_2': " user_id = {dlg.user_id} AND b_fieldcheck = False"},
        {'value': 3, 'sql_1': "user_id = {dlg.user_id} AND b_fieldcheck = True", 'sql_2': "user_id = {dlg.user_id} AND b_fieldcheck = False"},
        {'value': 4, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 5, 'sql_1': "b_fieldcheck = True", 'sql_2': "user_id = 0"},
        {'value': 6, 'sql_1': "user_id = 0", 'sql_2': "b_fieldcheck = False"},
        {'value': 7, 'sql_1': "b_fieldcheck = True", 'sql_2': "b_fieldcheck = False"},
        {'value': 8, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 9, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND b_fieldcheck = True", 'sql_2': "user_id = 0"},
        {'value': 10, 'sql_1': "user_id = 0", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND b_fieldcheck = False"},
        {'value': 11, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND b_fieldcheck = True", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND b_fieldcheck = False"},
        {'value': 12, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 13, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = True", 'sql_2': "user_id = 0"},
        {'value': 14, 'sql_1': "user_id = 0", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = False"},
        {'value': 15, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = True", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = False"}
                ]
    sql_1 = ""
    sql_2 = ""
    for e_dict in sql_cases:
        if e_dict["value"] == case:
            raw_sql_1 = e_dict["sql_1"]
            sql_1 = eval('f"{}"'.format(raw_sql_1))
            raw_sql_2 = e_dict["sql_2"]
            sql_2 = eval('f"{}"'.format(raw_sql_2))
            break
    with CfgPars() as cfg:
        params = cfg.uri()
    uri_1 = params + 'table="team_' + str(dlg.team_i) + '"."flagi" (geom) sql=' + sql_1
    uri_2 = params + 'table="team_' + str(dlg.team_i) + '"."flagi" (geom) sql=' + sql_2
    # Zmiana zawartości warstw z flagami:
    l_tuples = [
        ("flagi_z_teren", uri_1),
        ("flagi_bez_teren", uri_2)
        ]
    for l_tuple in l_tuples:
        lyr = dlg.proj.mapLayersByName(l_tuple[0])[0]
        pg_layer_change(l_tuple[1], lyr)
        lyr.triggerRepaint()
    dlg.flag_visibility()  # Aktualizacja widoczności warstw
    QgsApplication.restoreOverrideCursor()

def wyr_layer_update(check=True):
    """Aktualizacja warstw z wyrobiskami."""
    QgsApplication.setOverrideCursor(Qt.WaitCursor)
    if check:
        # Sprawdzenie, czy wszystkie wyrobiska mają przypisane powiaty i dane
        # oraz dokonanie aktualizacji, jeśli występują braki:
        wyr_powiaty_check()
        wyr_dane_check()
    # Stworzenie listy wyrobisk z aktywnych powiatów:
    dlg.obj.wyr_ids = get_wyr_ids()
    if dlg.wyr_panel.pow_all:
        dlg.obj.order_ids = []
    else:
        dlg.wyr_panel.status_indicator.order_check()
        dlg.obj.order_ids = get_order_ids()
    # Aktualizacja wdf:
    wdf_update()
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.obj.wyr_ids:
        table = f'''"(SELECT row_number() OVER (ORDER BY w.wyr_id::int) AS row_num, w.wyr_id, w.t_teren_id as teren_id, w.t_wn_id as wn_id, w.t_midas_id as midas_id, w.user_id, w.t_notatki as notatki, d.i_area_m2 as pow_m2, w.centroid AS point FROM team_{dlg.team_i}.wyrobiska w INNER JOIN team_{dlg.team_i}.wyr_dane d ON w.wyr_id = d.wyr_id WHERE w.wyr_id IN ({str(dlg.obj.wyr_ids)[1:-1]})'''
        if dlg.wyr_panel.pow_all:
            table_green = f'''"(SELECT row_number() OVER (ORDER BY w.wyr_id::int) AS row_num, w.wyr_id, w.t_teren_id as teren_id, w.t_wn_id as wn_id, w.t_midas_id as midas_id, w.user_id, w.t_notatki as notatki, d.i_area_m2 as pow_m2, w.centroid AS point FROM team_{dlg.team_i}.wyrobiska w INNER JOIN team_{dlg.team_i}.wyr_dane d ON w.wyr_id = d.wyr_id WHERE w.wyr_id IN ({str(dlg.obj.wyr_ids)[1:-1]}) AND w.b_after_fchk = True AND w.b_confirmed = True)"'''
        else:
            table_green = f'''"(SELECT row_number() OVER (ORDER BY p.order_id) AS row_num, p.order_id, w.wyr_id, w.t_teren_id as teren_id, w.t_wn_id as wn_id, w.t_midas_id as midas_id, w.user_id, w.t_notatki as notatki, d.i_area_m2 as pow_m2, w.centroid AS point FROM team_{dlg.team_i}.wyrobiska w INNER JOIN team_{dlg.team_i}.wyr_prg p ON w.wyr_id = p.wyr_id INNER JOIN team_{dlg.team_i}.wyr_dane d ON w.wyr_id = d.wyr_id WHERE w.wyr_id IN ({str(dlg.obj.wyr_ids)[1:-1]}) AND w.b_after_fchk = True AND w.b_confirmed = True AND p.pow_grp = '{dlg.powiat_i}')"'''
        uri_a1 = f'''{params} key="row_num" table={table} AND b_after_fchk = False)" (point) sql='''
        uri_a2 = f'{params} key="row_num" table={table_green} (point) sql='
        uri_a3 = f'''{params} key="row_num" table={table} AND b_after_fchk = True AND b_confirmed = False)" (point) sql='''
        uri_a4 = params + 'table="team_' + str(dlg.team_i) + '"."wyrobiska" (centroid) sql=wyr_id IN (' + str(dlg.obj.wyr_ids)[1:-1] + ')'
        uri_b = params + 'table="team_' + str(dlg.team_i) + '"."wyr_geom" (geom) sql=wyr_id IN (' + str(dlg.obj.wyr_ids)[1:-1] + ')'
    else:
        uri_a1 = params + 'table="team_' + str(dlg.team_i) + '"."wyrobiska" (centroid) sql=wyr_id = 0'
        uri_a2 = params + 'table="team_' + str(dlg.team_i) + '"."wyrobiska" (centroid) sql=wyr_id = 0'
        uri_a3 = params + 'table="team_' + str(dlg.team_i) + '"."wyrobiska" (centroid) sql=wyr_id = 0'
        uri_a4 = params + 'table="team_' + str(dlg.team_i) + '"."wyrobiska" (centroid) sql=wyr_id = 0'
        uri_b = params + 'table="team_' + str(dlg.team_i) + '"."wyr_geom" (geom) sql=wyr_id = 0'
    # Zmiana zawartości warstw z wyrobiskami:
    l_tuples = [
        ("wyr_przed_teren", uri_a1),
        ("wyr_potwierdzone", uri_a2),
        ("wyr_odrzucone", uri_a3),
        ("wyr_point", uri_a4),
        ("wyr_poly", uri_b)
        ]
    for l_tuple in l_tuples:
        lyr = dlg.proj.mapLayersByName(l_tuple[0])[0]
        pg_layer_change(l_tuple[1], lyr)
        lyr.triggerRepaint()
    dlg.wyr_visibility()  # Aktualizacja widoczności warstw
    QgsApplication.restoreOverrideCursor()

def wdf_update():
    """Aktualizacja dataframe'u wdf."""
    # Załadowanie danych o wyrobiskach do dataframe'u:
    wdf_load()
    # Aktualizacja tableview:
    dlg.wyr_panel.wdf_mdl.setDataFrame(dlg.wyr_panel.wdf)

def wdf_load():
    """Załadowanie danych o wyrobiskach z db do dataframe'u wdf."""
    db = PgConn()
    extras = f" WHERE wyr_id IN ({str(dlg.obj.wyr_ids)[1:-1]})" if dlg.obj.wyr_ids else f" WHERE wyr_id = 0"
    sql = "SELECT wyr_id, b_after_fchk, b_confirmed, t_wn_id FROM team_" + str(dlg.team_i) + ".wyrobiska" + extras + " ORDER BY wyr_id;"
    if db:
        temp_df = db.query_pd(sql, ['wyr_id', 'fchk', 'cnfrm', 'wn_id'])
        if isinstance(temp_df, pd.DataFrame):
            wn_df = temp_df.copy()
            wn_df.drop(['fchk', 'cnfrm'], axis=1, inplace=True)
            wn_check(wn_df)
            wdf = wyr_status_determine(temp_df)
            dlg.wyr_panel.wdf = wdf
        else:
            dlg.wyr_panel.wdf = pd.DataFrame(columns=dlg.wyr_panel.wn_df.columns)  # Wyczyszczenie dataframe'a z połączeniami wyrobiska-wn_pne
            return None

def wn_check(wn_df):
    """Kontrola zmian w połączeniach wyrobisk z WN_PNE."""
    wn_df_new = wn_df[~wn_df['wn_id'].isna()].reset_index(drop=True)
    wn_df_old = dlg.wyr_panel.wn_df.copy()
    wn_df_old = wn_df_old[['wyr_id', 'wn_id']]
    if not wn_df_new.equals(wn_df_old):
        dlg.wyr_panel.wn_df = wn_df_new
        wn_update(wn_df_new)

def wn_update(wn_df):
    """Aktualizacja danych dla warstwy wn_link."""
    if len(dlg.wyr_panel.wn_df) == 0:
        lyr = dlg.proj.mapLayersByName("wn_link")[0]
        if lyr.featureCount() > 0:
            pr = lyr.dataProvider()
            pr.truncate()
        return
    # Pobranie geometrii punktowych wybranych wyrobisk:
    wyr_ids = wn_df['wyr_id'].tolist()
    table = f'"team_{dlg.team_i}"."wyrobiska"'
    wyr_pts = get_point_from_ids(wyr_ids, table, "wyr_id", "centroid")
    if len(wyr_pts) == 0:
        return
    # Pobranie geometrii punktowych wybranych WN_PNE:
    wn_ids = wn_df['wn_id'].tolist()
    table = f'"external"."wn_pne"'
    wn_pts = get_point_from_ids(wn_ids, table, "id_arkusz", "geom")
    if len(wn_pts) == 0:
        return
    # Stworzenie linii łączących wyrobiska i punkty WN_PNE:
    lyr = dlg.proj.mapLayersByName("wn_link")[0]
    pr = lyr.dataProvider()
    pr.truncate()
    i = 0
    with edit(lyr):
        for index in dlg.wyr_panel.wn_df.to_records():
            wyr_id = index[1]
            wyr_pnt = get_geom_from_id(wyr_id, wyr_pts)
            wn_id = index[2]
            wn_pnt = get_geom_from_id(wn_id, wn_pts)
            ft = QgsFeature()
            attrs = [i, int(wyr_id), str(wn_id)]
            ft.setAttributes(attrs)
            ft.setGeometry(QgsGeometry.fromPolylineXY([wyr_pnt.asPoint(), wn_pnt.asPoint()]))
            pr.addFeature(ft)
            i += 1

def get_geom_from_id(id, ids):
    """Zwraca geometrię punktową z listy na podstawie id."""
    for item in ids:
        if id == item[0]:
            return item[1]

def wyr_status_determine(temp_df):
    """Ustala status wyrobiska na podstawie atrybutów: 'fchk' i 'cnfrm', następnie zwraca gotową wersję wdf."""
    conditions = [temp_df['fchk'].eq(False),
                temp_df['fchk'].eq(True) & temp_df['cnfrm'].eq(False),
                temp_df['fchk'].eq(True) & temp_df['cnfrm'].eq(True)]
    choices = [0, 1, 2]
    temp_df['status'] = np.select(conditions, choices, default=0)
    temp_df.drop(['fchk', 'cnfrm'], axis=1, inplace=True)
    temp_df = temp_df[['status', 'wyr_id']]
    return temp_df

def wyr_powiaty_check():
    """Sprawdza, czy wszystkie wyrobiska zespołu mają wpisy w tabeli 'wyr_prg'.
    Jeśli nie, to przypisuje je na podstawie geometrii poligonalnej lub punktowej."""
    wyr_ids = get_wyr_ids_with_pows("wyrobiska")
    wyr_pow_ids = get_wyr_ids_with_pows("wyr_prg")
    if not wyr_ids:
        return
    wyr_pow_to_add = list_diff(wyr_ids, wyr_pow_ids)
    if not wyr_pow_to_add:
        return
    print(f"wyr_pow_to_add: {wyr_pow_to_add}")
    # Uzupełnienie brakujących rekordów w tabeli 'wyr_prg':
    wyr_poly_ids = []
    wyr_point_ids = []
    for wyr in wyr_pow_to_add:
        wyr_poly_ids.append(wyr) if wyr_poly_exist(wyr) else wyr_point_ids.append(wyr)
    if wyr_poly_ids:
    # Pozyskanie informacji o powiatach z geometrii poligonalnej:
        wyr_polys = get_poly_from_ids(wyr_poly_ids)
        for wyr_poly in wyr_polys:
            wyr_powiaty_change(wyr_poly[0], wyr_poly[1])
    if wyr_point_ids:
        # Pozyskanie informacji o powiatach z geometrii punktowej:
        table = f'"team_{dlg.team_i}"."wyrobiska"'
        wyr_pts = get_point_from_ids(wyr_point_ids, table, "wyr_id", "centroid")
        for wyr_pt in wyr_pts:
            wyr_powiaty_change(wyr_pt[0], wyr_pt[1])

def wyr_dane_check():
    """Sprawdza, czy wszystkie wyrobiska zespołu mają wpisy w tabeli 'wyr_dane'.
    Jeśli nie, to tworzy odpowiednie wpisy."""
    wyr_ids = get_wyr_ids_with_pows("wyrobiska")
    wyr_dane_ids = get_wyr_ids_with_pows("wyr_dane")
    if not wyr_ids:
        return
    wyr_dane_to_add = list(zip((list_diff(wyr_ids, wyr_dane_ids))))
    if not wyr_dane_to_add:
        return
    print(f"wyr_dane_to_add: {wyr_dane_to_add}")
    # Uzupełnienie brakujących rekordów w tabeli 'wyr_dane':
    wyr_dane_update(wyr_dane_to_add)

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

def get_point_from_ids(ids, table, id_col, geom_col):
    """Zwraca listę z geometriami punktowymi wyrobisk na podstawie ich id."""
    pts = []
    with CfgPars() as cfg:
        params = cfg.uri()
    sql = f"{id_col} IN ({str(ids)[1:-1]})"
    uri = f'{params} table={table} ({geom_col}) sql={sql}'
    lyr_pt = QgsVectorLayer(uri, "temp_pt", "postgres")
    feats = lyr_pt.getFeatures()
    for feat in feats:
        pts.append((feat.attribute(id_col), feat.geometry()))
    del lyr_pt
    return pts

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

def get_order_ids():
    """Zwraca listę unikalnych order_id wraz z wyr_id i order_lock w obrębie aktywnego powiatu."""
    db = PgConn()
    sql = f"SELECT order_id, wyr_id, order_lock FROM team_{dlg.team_i}.wyr_prg WHERE pow_grp = '{dlg.powiat_i}' AND order_id IS NOT NULL ORDER BY order_id;"
    if db:
        res = db.query_sel(sql, True)
        if res:
                return res
        else:
            return []

def get_wyr_ids_with_pows(table, pows=None):
    """Zwraca listę unikalnych wyr_id z podanej tabeli w obrębie podanych powiatów."""
    db = PgConn()
    extras = f" WHERE pow_id IN ({str(pows)[1:-1]})" if pows else ""
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

def get_wyr_ids_with_filter(filter):
    """Zwraca listę wyr_id z użyciem podanego filtru sql."""
    db = PgConn()
    sql = "SELECT wyr_id FROM team_" + str(dlg.team_i) + ".wyrobiska" + filter + " ORDER BY wyr_id;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if len(res) > 1:
                return list(zip(*res))[0]
            else:
                return list(res[0])
        else:
            return []

def get_wyr_ids():
    """Zwraca listę unkalnych wyr_id zgodnych z aktualnie zastosowanymi filtrami."""
    # Określenie, które rodzaje wyrobisk są włączone:
    case = dlg.cfg.wyr_case()
    if case == 0 or case == 8:
        # Wszystkie rodzaje wyrobisk są wyłączone - brak wyrobisk do wyświetlenia
        return []
    # Utworzenie listy z wyr_id wyrobisk, które należą do aktywnych powiatów:
    pows = active_pow_listed()
    wyr_ids_from_pows = get_wyr_ids_with_pows("wyr_prg", pows)
    if not wyr_ids_from_pows:
        # Brak wyrobisk w aktywnych powiatach
        return []
    if case == 15:
        # Wszystkie rodzaje wyrobisk są włączone - brak filtrowania
        return wyr_ids_from_pows
    # Utworzenie listy z wyr_id wyrobisk, których rodzaje są włączone:
    filter_cases = [
        {'value': 1, 'sql': " WHERE user_id = {dlg.user_id} AND b_after_fchk = False "},
        {'value': 2, 'sql': " WHERE user_id = {dlg.user_id} AND b_after_fchk = True AND b_confirmed = True "},
        {'value': 3, 'sql': " WHERE user_id = {dlg.user_id} AND (b_after_fchk = False OR (b_after_fchk = True AND b_confirmed = True )) "},
        {'value': 4, 'sql': " WHERE user_id = {dlg.user_id} AND b_after_fchk = True AND b_confirmed = False "},
        {'value': 5, 'sql': " WHERE user_id = {dlg.user_id} AND (b_after_fchk = False OR (b_after_fchk = True AND b_confirmed = False )) "},
        {'value': 6, 'sql': " WHERE user_id = {dlg.user_id} AND b_after_fchk = True "},
        {'value': 7, 'sql': " WHERE user_id = {dlg.user_id} "},
        {'value': 9, 'sql': " WHERE b_after_fchk = False "},
        {'value': 10, 'sql': " WHERE b_after_fchk = True AND b_confirmed = True "},
        {'value': 11, 'sql': " WHERE b_after_fchk = False OR (b_after_fchk = True AND b_confirmed = True ) "},
        {'value': 12, 'sql': " WHERE b_after_fchk = True AND b_confirmed = False "},
        {'value': 13, 'sql': " WHERE b_after_fchk = False OR (b_after_fchk = True AND b_confirmed = False ) "},
        {'value': 14, 'sql': " WHERE b_after_fchk = True "}
                ]
    filter = ""
    for e_dict in filter_cases:
        if e_dict["value"] == case:
            raw_sql = e_dict["sql"]
            filter = eval("f'{}'".format(raw_sql))
            break
    wyr_ids_from_filter = get_wyr_ids_with_filter(filter)
    if not wyr_ids_from_filter:
        # Wszystkie wyrobiska zostały wyfiltrowane
        return []
    # Zwrócenie listy wyr_id wyrobisk, które znajdują się w obu listach:
    result = sorted(set(wyr_ids_from_pows).intersection(wyr_ids_from_filter))
    return result

def get_flag_ids(case):
    """Zwraca listę wyfiltrowanych id flag i sql filtru."""
    if case == 0 or case == 4 or case == 8 or case == 12:
        # Wszystkie rodzaje flag są wyłączone - brak flag do wyświetlenia:
        return []
    # Utworzenie listy z id flag, których rodzaje są włączone:
    filter_cases = [
        {'value': 1, 'sql': " WHERE user_id = {dlg.user_id} AND b_fieldcheck = True "},
        {'value': 2, 'sql': " WHERE user_id = {dlg.user_id} AND b_fieldcheck = False "},
        {'value': 3, 'sql': " WHERE user_id = {dlg.user_id} "},
        {'value': 5, 'sql': " WHERE b_fieldcheck = True "},
        {'value': 6, 'sql': " WHERE b_fieldcheck = False "},
        {'value': 7, 'sql': ""},
        {'value': 9, 'sql': " WHERE user_id = {dlg.user_id} AND pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = True "},
        {'value': 10, 'sql': " WHERE user_id = {dlg.user_id} AND pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = False "},
        {'value': 11, 'sql': " WHERE user_id = {dlg.user_id} AND pow_grp = '{dlg.powiat_i}' "},
        {'value': 13, 'sql': " WHERE pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = True "},
        {'value': 14, 'sql': " WHERE pow_grp = '{dlg.powiat_i}' AND b_fieldcheck = False "},
        {'value': 15, 'sql': " WHERE pow_grp = '{dlg.powiat_i}' "}
                ]
    filter = ""
    for e_dict in filter_cases:
        if e_dict["value"] == case:
            raw_sql = e_dict["sql"]
            filter = eval('f"{}"'.format(raw_sql))
            break
    db = PgConn()
    sql = "SELECT id FROM team_" + str(dlg.team_i) + ".flagi" + filter + " ORDER BY id;"
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
    """Zwraca listę elementów l1, które nie występują w l2."""
    if not l1:
        return None
    if not l2:
        return l1
    return (list(set(l1)-set(l2)))

def active_pow_listed():
    """Zwraca listę z numerami aktywnych powiatów."""
    db = PgConn()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        sql = "SELECT pow_id FROM team_" + str(dlg.team_i) + ".powiaty WHERE pow_grp = '" + str(dlg.powiat_i) + "'"
    else:  # Tryb wielu powiatów
        sql = "SELECT pow_id FROM team_" + str(dlg.team_i) + ".powiaty"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if len(res) > 1:
                return list(zip(*res))[0]
            else:
                return list(res[0])
        else:
            return None

def wyr_powiaty_change(wyr_id, geom, new=False):
    """Aktualizuje tabelę 'wyr_prg' po zmianie geometrii wyrobiska."""
    if not new:
        # Usunięcie poprzednich wpisów z tabeli 'wyr_prg':
        wyr_powiaty_delete(wyr_id)
    # Stworzenie listy z aktualnymi powiatami dla wyrobiska:
    p_list = wyr_powiaty_listed(wyr_id, geom)
    if not p_list:  # Brak powiatów
        print(f"wyr_powiaty_change: Nie udało się stworzyć listy powiatów dla wyrobiska {wyr_id}")
        return
    # Wstawienie nowych rekordów do tabeli 'wyr_prg':
    wyr_powiaty_update(p_list)

def wyr_powiaty_delete(wyr_id):
    """Usunięcie z tabeli 'wyr_prg' rekordów odnoszących się do wyr_id."""
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".wyr_prg WHERE wyr_id = " + str(wyr_id) + ";"
    if db:
        res = db.query_upd(sql)
        # if not res:
            # print(f"wyr_powiaty_delete: brak rekordów dla wyrobiska {wyr_id}")

def wyr_powiaty_update(p_list):
    """Wstawienie do tabeli 'wyr_prg' aktualnych numerów powiatów dla wyrobiska."""
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".wyr_prg(wyr_id, gmi_id, t_gmi_name, pow_id, pow_grp, t_pow_name, t_woj_name, t_mie_name) VALUES %s"
    if db:
        db.query_exeval(sql, p_list)

def wyr_dane_update(p_list):
    """Wstawienie do tabeli 'wyr_dane' rekordów dla brakujących numerów wyr_id."""
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".wyr_dane(wyr_id) VALUES %s"
    if db:
        db.query_exeval(sql, p_list)

def wyr_powiaty_listed(wyr_id, geom):
    """Zwraca listę z danymi jednostek administracyjnych, w obrębie których leży geometria wyrobiska."""
    non_team = False
    p_list = []
    g_list = []
    if geom.type() == QgsWkbTypes.PointGeometry:
        geom = geom.buffer(1., 1)
    bbox = geom.makeValid().boundingBox().asWktPolygon()
    with CfgPars() as cfg:
        params = cfg.uri()
    table = '"team_' + str(dlg.team_i) + '"."gminy"'
    key = '"gmi_id"'
    sql = "ST_Intersects(ST_SetSRID(ST_GeomFromText('" + str(bbox) + "'), 2180), geom)"
    uri = f'{params} key={key} table={table} (geom) sql={sql}'
    lyr_pow = QgsVectorLayer(uri, "powiaty_bbox", "postgres")
    feats = lyr_pow.getFeatures()
    if lyr_pow.featureCount() == 0:  # Wyrobisko może być poza gminami przydzielonymi do zespołu
        del lyr_pow
        non_team = True
        with CfgPars() as cfg:
            params = cfg.uri()
        table = '"public"."gminy"'
        key = '"gmi_id"'
        sql = "ST_Intersects(ST_SetSRID(ST_GeomFromText('" + str(bbox) + "'), 2180), geom)"
        uri = f'{params} key={key} table={table} (geom) sql={sql}'
        lyr_pow = QgsVectorLayer(uri, "powiaty_bbox", "postgres")
        feats = lyr_pow.getFeatures()
    if lyr_pow.featureCount() == 0:
        del lyr_pow
        return None
    if lyr_pow.featureCount() == 1:
        for feat in feats:
            mie_name = mie_picker(geom, feat.attribute("gmi_id"))
            pow_grp = feat.attribute("pow_id") if non_team else feat.attribute("pow_grp")
            attrs = (wyr_id, feat.attribute("gmi_id"), feat.attribute("t_gmi_name"), feat.attribute("pow_id"), pow_grp, feat.attribute("t_pow_name"), feat.attribute("t_woj_name"), mie_name)
            p_list.append(attrs)
    elif lyr_pow.featureCount() > 1:
        for feat in feats:
            pow_grp = feat.attribute("pow_id") if non_team else feat.attribute("pow_grp")
            if geom.makeValid().intersects(feat.geometry()):
                attrs = (wyr_id, feat.attribute("gmi_id"), feat.attribute("t_gmi_name"), feat.attribute("pow_id"), pow_grp, feat.attribute("t_pow_name"), feat.attribute("t_woj_name"))
                g_list.append((feat.attribute("gmi_id"), pow_grp, feat.geometry(), attrs))
        p_list = wyr_powiaty_splitter(geom, g_list)
    del lyr_pow
    return p_list

def wyr_powiaty_splitter(wyr_geom, g_list):
    """Dzieli wyrobisko wzdłuż granic gmin i zwraca listę 'pow_grp' z danymi gmin, które mają największy udział powierzchni."""
    # Agregacja gmin w 'pow_grp':
    p_list = []
    grp_list = []
    pows = {}
    for g in g_list:
        pow_grp = g[1]
        if not pow_grp in grp_list:
            grp_list.append(pow_grp)
            _grp = []
            pows[pow_grp] = _grp
            _grp.append((g[0], g[2], g[3]))
        else:
            pows[pow_grp].append((g[0], g[2], g[3]))
    # Wybór gminy dla każdego 'pow_grp':
    for p in pows:
        p_items = pows[p]
        if len(p_items) == 1:  # Tylko jedna gmina
            for gp in p_items:
                g_chosed = gp[2]
                mie_name = mie_picker(wyr_geom, g_chosed[1])
                result = g_chosed + (mie_name,)
                p_list.append(result)
        else:  # Więcej niż jedna gmina
            area = 0
            g_chosed = None
            for gp in p_items:
                g_geom = wyr_geom.intersection(gp[1])
                g_area = g_geom.area()
                if g_area > area:
                    area = g_area
                    g_chosed = gp[2]
            mie_name = mie_picker(wyr_geom, g_chosed[1])
            result = g_chosed + (mie_name,)
            p_list.append(result)
    return p_list

def mie_picker(geom, gmi_id):
    """Wybiera najbliższą do wyrobiska miejscowość w wybranej gminie."""
    # Przygotowanie współrzędnych centroidu wyrobiska:
    p_geom = geom.centroid()
    p_xy = np.array((p_geom.asPoint().x(), p_geom.asPoint().y()))
    mdf = mie_loader(gmi_id)  # Wczytanie danych z db
    if not isinstance(mdf, pd.DataFrame):
        # Wyrobisko znajduje się poza gminami zespołu
        return "!!!"
    # Obliczenie odległości pomiędzy punktem, a miejscowościami z wybranej gminy:
    mdf['dist'] = compute_dist(mdf.iloc[:,4:6], p_xy).astype('float32')
    # Obróbka dataframe'u:
    mdf = mdf.sort_values(by=['dist'], ascending=[True]).reset_index(drop=True)
    mdf = mdf.groupby('i_rank').first().reset_index()
    mdf_near = mdf[mdf['dist'] < 1000]  # Filtrowanie obiektów poniżej 1 km odległości
    if len(mdf_near) > 0:
        return mdf_near['t_mie_name'].iloc[0]
    else:
        mdf_far = mdf.sort_values(by=['dist'], ascending=[True]).reset_index(drop=True)
        return mdf_far['t_mie_name'].iloc[0]

def compute_dist(df, a_pnt):
    """Oblicza jednocześnie dla całego dataframe'u odległości od wskazanego punktu."""
    result = apply_numba_dist(df['X'].to_numpy(), df['Y'].to_numpy(), a_pnt)
    return pd.Series(result, index=df.index, name='dist')

def apply_numba_dist(x, y, a_pnt):
    n = len(x)
    result = np.empty(n, dtype='float32')
    for i in range(n):
        result[i] = numba_dist(x[i], y[i], a_pnt)
    return result

def numba_dist(x, y, a_pnt):
    if np.isnan(x) or np.isnan(y):
        return np.nan
    b_pnt = np.array((x, y))
    return np.sqrt(np.sum(((a_pnt - b_pnt) ** 2)))

def mie_loader(gmi_id):
    """Zwraca dataframe z miejscowościami wybranej gminy."""
    db = PgConn()
    sql = f"SELECT mie_id, t_mie_name, t_mie_rodz, i_rank, ST_X(geom) as X, ST_Y(geom) as Y FROM team_{dlg.team_i}.miejscowosci WHERE gmi_id = '{gmi_id}';"
    if db:
        mdf = db.query_pd(sql, ['mie_id', 't_mie_name', 't_mie_rodz', 'i_rank', 'X', 'Y'])
        if isinstance(mdf, pd.DataFrame):
            return mdf if len(mdf) > 0 else None
        else:
            return None

def wn_layer_update():
    """Aktualizacja warstwy z wn_pne."""
    QgsApplication.setOverrideCursor(Qt.WaitCursor)
    # Stworzenie listy wn_pne z aktywnych powiatów:
    pows = active_pow_listed()
    dlg.obj.wn_ids = get_wn_ids_with_pows(pows)
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.obj.wn_ids:
        uri = params + 'key="id_arkusz" table="(SELECT e.id_arkusz, e.kopalina, e.wyrobisko, e.zawodn, e.eksploat, e.wyp_odpady, e.nadkl_min, e.nadkl_max, e.nadkl_sr, e.miazsz_min, e.miazsz_max, e.dlug_max, e.szer_max, e.wys_min, e.wys_max, e.data_kontrol, e.uwagi, (SELECT COUNT(*) FROM external.wn_pne_pow AS p WHERE e.id_arkusz = p.id_arkusz AND p.b_active = true) AS i_pow_cnt, t.t_notatki, e.geom FROM external.wn_pne e, team_' + str(dlg.team_i) + '.wn_pne t WHERE e.id_arkusz = t.id_arkusz AND e.id_arkusz IN (' + str(dlg.obj.wn_ids)[1:-1] + '))" (geom) sql='
    else:
        uri = params + 'table="external"."wn_pne" (geom) sql=id_arkusz = Null'
    # Zmiana zawartości warstwy z wn_pne:
    lyr = dlg.proj.mapLayersByName("wn_pne")[0]
    pg_layer_change(uri, lyr)
    lyr.triggerRepaint()
    QgsApplication.restoreOverrideCursor()

def get_wn_ids_with_pows(pows=None):
    """Zwraca listę unikalnych id_arkusz z tabeli wn_pne_pow w obrębie podanych powiatów."""
    if not pows:
        return
    db = PgConn()
    sql = f"SELECT DISTINCT id_arkusz FROM external.wn_pne_pow WHERE pow_id IN ({str(pows)[1:-1]}) AND b_active = True ORDER BY id_arkusz;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if len(res) > 1:
                return list(zip(*res))[0]
            else:
                return list(res[0])
        else:
            return None

def parking_layer_update():
    """Aktualizacja warstwy parking."""
    # print("[parking_layer_update]")
    QgsApplication.setOverrideCursor(Qt.WaitCursor)
    # Określenie, które rodzaje parkingów są włączone:
    case = dlg.cfg.parking_case()
    # Aktualizacja listy flag w ObjectManager:
    dlg.obj.parking_ids = get_parking_ids(case)
    # Utworzenie listy z id parkingów, których rodzaje są włączone:
    sql_cases = [
        {'value': 0, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 1, 'sql_1': "user_id = {dlg.user_id} AND i_status = 0", 'sql_2': "user_id = 0"},
        {'value': 2, 'sql_1': "user_id = 0", 'sql_2': " user_id = {dlg.user_id} AND i_status = 1"},
        {'value': 3, 'sql_1': "user_id = {dlg.user_id} AND i_status = 0", 'sql_2': "user_id = {dlg.user_id} AND i_status = 1"},
        {'value': 4, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 5, 'sql_1': "i_status = 0", 'sql_2': "user_id = 0"},
        {'value': 6, 'sql_1': "user_id = 0", 'sql_2': "i_status = 1"},
        {'value': 7, 'sql_1': "i_status = 0", 'sql_2': "i_status = 1"},
        {'value': 8, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 9, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND i_status = 0", 'sql_2': "user_id = 0"},
        {'value': 10, 'sql_1': "user_id = 0", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND i_status = 1"},
        {'value': 11, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND i_status = 0", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND user_id = {dlg.user_id} AND i_status = 1"},
        {'value': 12, 'sql_1': "user_id = 0", 'sql_2': "user_id = 0"},
        {'value': 13, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND i_status = 0", 'sql_2': "user_id = 0"},
        {'value': 14, 'sql_1': "user_id = 0", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND i_status = 1"},
        {'value': 15, 'sql_1': "pow_grp = '{dlg.powiat_i}' AND i_status = 0", 'sql_2': "pow_grp = '{dlg.powiat_i}' AND i_status = 1"}
                ]
    sql_1 = ""
    sql_2 = ""
    for e_dict in sql_cases:
        if e_dict["value"] == case:
            raw_sql_1 = e_dict["sql_1"]
            sql_1 = eval('f"{}"'.format(raw_sql_1))
            raw_sql_2 = e_dict["sql_2"]
            sql_2 = eval('f"{}"'.format(raw_sql_2))
            break
    with CfgPars() as cfg:
        params = cfg.uri()
    uri_1 = params + 'table="team_' + str(dlg.team_i) + '"."parking" (geom) sql=' + sql_1
    uri_2 = params + 'table="team_' + str(dlg.team_i) + '"."parking" (geom) sql=' + sql_2
    # Zmiana zawartości warstw z parkingami:
    l_tuples = [
        ("parking_planowane", uri_1),
        ("parking_odwiedzone", uri_2)
        ]
    for l_tuple in l_tuples:
        lyr = dlg.proj.mapLayersByName(l_tuple[0])[0]
        pg_layer_change(l_tuple[1], lyr)
        lyr.triggerRepaint()
    dlg.komunikacja_visibility()  # Aktualizacja widoczności warstw
    QgsApplication.restoreOverrideCursor()

def get_parking_ids(case):
    """Zwraca listę wyfiltrowanych id parkingów i sql filtru."""
    if case == 0 or case == 4 or case == 8 or case == 12:
        # Wszystkie rodzaje parkingów są wyłączone - brak parkingów do wyświetlenia:
        return []
    # Utworzenie listy z id parkingów, których rodzaje są włączone:
    filter_cases = [
        {'value': 1, 'sql': " WHERE user_id = {dlg.user_id} AND i_status = 0 "},
        {'value': 2, 'sql': " WHERE user_id = {dlg.user_id} AND i_status = 1 "},
        {'value': 3, 'sql': " WHERE user_id = {dlg.user_id} "},
        {'value': 5, 'sql': " WHERE i_status = 0 "},
        {'value': 6, 'sql': " WHERE i_status = 1 "},
        {'value': 7, 'sql': ""},
        {'value': 9, 'sql': " WHERE user_id = {dlg.user_id} AND pow_grp = '{dlg.powiat_i}' AND i_status = 0 "},
        {'value': 10, 'sql': " WHERE user_id = {dlg.user_id} AND pow_grp = '{dlg.powiat_i}' AND i_status = 1 "},
        {'value': 11, 'sql': " WHERE user_id = {dlg.user_id} AND pow_grp = '{dlg.powiat_i}' "},
        {'value': 13, 'sql': " WHERE pow_grp = '{dlg.powiat_i}' AND i_status = 0 "},
        {'value': 14, 'sql': " WHERE pow_grp = '{dlg.powiat_i}' AND i_status = 1 "},
        {'value': 15, 'sql': " WHERE pow_grp = '{dlg.powiat_i}' "}
                ]
    filter = ""
    for e_dict in filter_cases:
        if e_dict["value"] == case:
            raw_sql = e_dict["sql"]
            filter = eval('f"{}"'.format(raw_sql))
            break
    db = PgConn()
    sql = "SELECT id FROM team_" + str(dlg.team_i) + ".parking" + filter + " ORDER BY id;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if len(res) > 1:
                return list(zip(*res))[0]
            else:
                return list(res[0])
        else:
            return None

def marsz_layer_update(check=True):
    """Aktualizacja warstwy z marszrutami."""
    QgsApplication.setOverrideCursor(Qt.WaitCursor)
    if check:
    # Sprawdzenie, czy wszystkie marszruty mają przypisane powiaty
    # i dokonanie aktualizacji, jeśli występują braki:
        marsz_powiaty_check()
    # Stworzenie listy marszrut z aktywnych powiatów:
    dlg.obj.marsz_ids = get_marsz_ids()
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.obj.marsz_ids:
        uri = params + 'table="team_' + str(dlg.team_i) + '"."marsz" (geom) sql=marsz_id IN (' + str(dlg.obj.marsz_ids)[1:-1] + ')'
    else:
        uri = params + 'table="team_' + str(dlg.team_i) + '"."marsz" (geom) sql=marsz_id = 0'
    # Zmiana zawartości warstw z wyrobiskami:
    l_tuples = [
        ("marszruty", uri)
        ]
    for l_tuple in l_tuples:
        lyr = dlg.proj.mapLayersByName(l_tuple[0])[0]
        pg_layer_change(l_tuple[1], lyr)
        lyr.triggerRepaint()
    dlg.komunikacja_visibility()  # Aktualizacja widoczności warstw
    QgsApplication.restoreOverrideCursor()

def get_marsz_ids():
    """Zwraca listę unkalnych marsz_id zgodnych z aktualnymi filtrami."""
    # Określenie, które rodzaje wyrobisk są włączone:
    case = dlg.cfg.marsz_case()
    if case == 0 or case == 2 or case == 4 or case == 6:
        # Warstwa z marszrutami jest wyłączona - brak marszrut do wyświetlenia
        return []
    # Utworzenie listy z marsz_id marszrut, które należą do aktywnych powiatów:
    pows = active_pow_listed()
    marsz_ids_from_pows = get_marsz_ids_with_pows("marsz_pow", pows)
    if not marsz_ids_from_pows:
        # Brak wyrobisk w aktywnych powiatach
        return []
    if case == 7:
        # Wszystkie marszruty są włączone - brak filtrowania
        return marsz_ids_from_pows
    # Utworzenie listy z marsz_id wyrobisk, których rodzaje są włączone:
    filter_cases = [
        {'value': 1, 'sql': " WHERE user_id = {dlg.user_id}"}
                ]
    filter = ""
    for e_dict in filter_cases:
        if e_dict["value"] == case:
            raw_sql = e_dict["sql"]
            filter = eval("f'{}'".format(raw_sql))
            break
    marsz_ids_from_filter = get_marsz_ids_with_filter(filter)
    if not marsz_ids_from_filter:
        # Wszystkie marszruty zostały wyfiltrowane
        return []
    # Zwrócenie listy marsz_id marszrut, które znajdują się w obu listach:
    result = sorted(set(marsz_ids_from_pows).intersection(marsz_ids_from_filter))
    return result

def get_marsz_ids_with_filter(filter):
    """Zwraca listę marsz_id z użyciem podanego filtru sql."""
    db = PgConn()
    sql = "SELECT marsz_id FROM team_" + str(dlg.team_i) + ".marsz" + filter + " ORDER BY marsz_id;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if len(res) > 1:
                return list(zip(*res))[0]
            else:
                return list(res[0])
        else:
            return []

def marsz_powiaty_check():
    """Sprawdza, czy wszystkie marszruty zespołu mają wpisy w tabeli 'marsz_pow'.
    Jeśli nie, to przypisuje je na podstawie geometrii liniowej."""
    marsz_ids = get_marsz_ids_with_pows("marsz")
    marsz_pow_ids = get_marsz_ids_with_pows("marsz_pow")
    if not marsz_ids:
        return
    marsz_pow_to_add = list_diff(marsz_ids, marsz_pow_ids)
    if not marsz_pow_to_add:
        return
    print(f"marsz_pow_to_add: {marsz_pow_to_add}")
    # Uzupełnienie brakujących rekordów w tabeli 'marsz_pow':
    marsz_lines = get_lines_from_ids(marsz_pow_to_add)
    for marsz_line in marsz_lines:
        marsz_powiaty_change(marsz_line[0], marsz_line[1])

def get_marsz_ids_with_pows(table, pows=None):
    """Zwraca listę unikalnych marsz_id z podanej tabeli w obrębie podanych powiatów."""
    db = PgConn()
    extras = f" WHERE pow_id IN ({str(pows)[1:-1]})" if pows else ""
    sql = "SELECT DISTINCT marsz_id FROM team_" + str(dlg.team_i) + "." + table + extras + " ORDER BY marsz_id;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if len(res) > 1:
                return list(zip(*res))[0]
            else:
                return list(res[0])
        else:
            return None

def get_lines_from_ids(marsz_ids):
    """Zwraca listę z geometriami liniowymi marszrut na podstawie ich id."""
    marsz_lines = []
    with CfgPars() as cfg:
        params = cfg.uri()
    table = '"team_' + str(dlg.team_i) + '"."marsz"'
    sql = "marsz_id IN (" + str(marsz_ids)[1:-1] + ")"
    uri = f'{params} table={table} (geom) sql={sql}'
    lyr_line = QgsVectorLayer(uri, "temp_marsz_line", "postgres")
    feats = lyr_line.getFeatures()
    for feat in feats:
        marsz_lines.append((feat.attribute("marsz_id"), feat.geometry()))
    del lyr_line
    return marsz_lines

def marsz_powiaty_change(marsz_id, geom, new=False):
    """Aktualizuje tabelę 'marsz_pow' po zmianie geometrii marszruty."""
    if not new:
        # Usunięcie poprzednich wpisów z tabeli 'marsz_pow':
        marsz_powiaty_delete(marsz_id)
    # Stworzenie listy z aktualnymi powiatami dla marszruty:
    p_list = marsz_powiaty_listed(marsz_id, geom)
    if not p_list:  # Brak powiatów
        print(f"marsz_powiaty_change: Nie udało się stworzyć listy powiatów dla marszruty {marsz_id}")
        return
    # Wstawienie nowych rekordów do tabeli 'marsz_pow':
    marsz_powiaty_update(p_list)

def marsz_powiaty_delete(marsz_id):
    """Usunięcie z tabeli 'marsz_pow' rekordów odnoszących się do marsz_id."""
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".marsz_pow WHERE marsz_id = " + str(marsz_id) + ";"
    if db:
        res = db.query_upd(sql)
        if not res:
            print(f"marsz_powiaty_delete: brak rekordów dla marszruty {marsz_id}")

def marsz_powiaty_listed(marsz_id, geom):
    """Zwraca listę powiatów, w obrębie których leży geometria marszruty."""
    p_list = []
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
            p_list.append((marsz_id, feat.attribute("pow_id")))
    del lyr_pow
    return p_list

def marsz_powiaty_update(p_list):
    """Wstawienie do tabeli 'marsz_pow' aktualnych numerów powiatów dla marszruty."""
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".marsz_pow(marsz_id, pow_id) VALUES %s"
    if db:
        db.query_exeval(sql, p_list)

def zloza_layer_update():
    """Aktualizacja warstwy zloza."""
    # print("[flag_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        uri = params + 'key="zv_id" table="team_' + str(dlg.team_i) + '"."zloza" (geom) sql=pow_grp = ' + "'" + str(dlg.powiat_i) + "'"
    else:  # Tryb wielu powiatów
        uri = params + ' key="zv_id" table="team_' + str(dlg.team_i) + '"."zloza" (geom)'
    layer = dlg.proj.mapLayersByName("zloza")[0]
    pg_layer_change(uri, layer)  # Zmiana zawartości warstwy zloza

def vn_mode_changed(clicked):
    """Włączenie bądź wyłączenie viewnet."""
    # print("[vn_mode_changed:", clicked, "]")
    if clicked:  # Włączenie/wyłączenie vn spowodowane kliknięciem w io_btn
        dlg.cfg.set_val(name="vn", val=dlg.p_vn.is_active())
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
    if not db_vn_pow_reset():
        print("main/vn_pow: Nie udało się zresetować siatki widoków!")
        return
    db = PgConn()
    # Ustawienie b_pow = True dla vn'ów, które znajdują się w obrębie wybranego powiatu/powiatów:
    sql = "UPDATE team_" + str(dlg.team_i) +".team_viewnet AS tv SET b_pow = True FROM (SELECT tv.vn_id	FROM powiaty p JOIN team_powiaty tp ON tp.pow_id = p.pow_id JOIN team_" + str(dlg.team_i) + ".team_viewnet tv ON ST_Intersects(tv.geom, p.geom) WHERE tp.pow_grp = '" + str(dlg.powiat_i) + "') AS s WHERE tv.vn_id = s.vn_id;"
    if db:
        res = db.query_upd(sql)
        if not res:
            QMessageBox.warning(None, "Problem", "Nie udało się ustawić zakresu siatki widoków. Jeśli sytuacja będzie się powtarzać, skontaktuj się z administratorem systemu.")

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

def vn_cfg():
    """Wejście lub wyjście z trybu konfiguracyjnego viewnet."""
    dlg.freeze_set(True, delay=True)  # Zablokowanie odświeżania dockwidget'u
    if dlg.p_vn.bar.cfg_btn.isChecked():  # Przycisk konfiguracyjny został wciśnięty
        dlg.obj.clear_sel()  # Odznaczenie flag, wyrobisk i punktów WN_PNE
        # Wyłączenie warstw flag, wyrobisk i external'i:
        dlg.cfg.switch_lyrs_on_setup(off=True)
        block_panels(dlg.p_vn, True)  # Zablokowanie pozostałych paneli
        dlg.side_dock.hide()  # Schowanie bocznego dock'u
        vn_setup_mode(True)
        dlg.freeze_set(False)  # Odblokowanie odświeżania dockwidget'u
    else:  # Przycisk konfiguracyjny został wyciśnięty
        # Włączenie warstw flag, wyrobisk i external'i:
        dlg.cfg.switch_lyrs_on_setup(off=False)
        block_panels(dlg.p_vn, False)  # Odblokowanie pozostałych paneli
        dlg.side_dock.show()  # Odkrycie bocznego dock'u
        vn_setup_mode(False)
        dlg.freeze_set(False)  # Odblokowanie odświeżania dockwidget'u

def vn_setup_mode(b_flag):
    """Włączenie lub wyłączenie trybu ustawień viewnet."""
    # print("[vn_setup_mode:", b_flag, "]")
    global vn_setup
    dlg.mt.init("multi_tool")  # Przełączenie na multi_tool'a
    if b_flag:  # Włączenie trybu ustawień vn przez wciśnięcie cfg_btn w p_vn
        vn_setup = True
        dlg.p_pow.t_active = dlg.p_pow.is_active()  # Zapamiętanie trybu powiatu przed ewentualną zmianą
        dlg.p_pow.active = False  # Wyłączenie trybu wybranego powiatu
        # Próba (bo może być jeszcze nie podłączone) odłączenia sygnałów:
        try:
            dlg.p_vn.widgets["cmb_teamusers"].currentIndexChanged.disconnect(teamusers_cb_changed)
            dlg.proj.mapLayersByName("vn_all")[0].selectionChanged.disconnect(vn_sel_changed)
        except TypeError:
            print("Obiekt nie jest jeszcze podłączony.")
        teamusers_load()  # Wczytanie użytkowników do cmb_teamusers
        dlg.p_vn.box.setCurrentIndex(1)  # zmiana strony p_vn
        if dlg.seq_dock.box.currentIndex() == 0:  # Nie jest włączony seq_setup
            if dlg.hk_vn:  # Skróty klawiszowe vn włączone
                dlg.t_hk_vn = True  # Zapamiętanie stanu hk_vn
            dlg.hk_vn = False  # Wyłączenie skrótów klawiszowych do obsługi vn
    else:  # Wyłączenie trybu ustawień vn przez wyciśnięcie cfg_btn w p_vn
        vn_setup = False
        dlg.proj.mapLayersByName("vn_all")[0].removeSelection()
        dlg.p_pow.active = dlg.p_pow.t_active  # Ewentualne przywrócenie trybu powiatu sprzed zmiany
        # Próba (bo może być jeszcze nie podłączone) odłączenia sygnałów:
        try:
            dlg.p_vn.widgets["cmb_teamusers"].currentIndexChanged.disconnect(teamusers_cb_changed)
            dlg.proj.mapLayersByName("vn_all")[0].selectionChanged.disconnect(vn_sel_changed)
        except TypeError:
            print("Obiekt nie jest jeszcze podłączony.")
        dlg.p_vn.box.setCurrentIndex(0)  # zmiana strony p_vn
        vn_mode_changed(False)
        if dlg.seq_dock.box.currentIndex() == 0:  # Nie jest włączony seq_setup
            if dlg.t_hk_vn:  # Przed włączeniem trybu konfiguracyjnego były aktywne skróty klawiszowe
                dlg.hk_vn = True  # Ponowne włączenie skrótów klawiszowych do obsługi vn
                dlg.t_hk_vn = False
    pow_layer_update()
    vn_layer_update()

def vn_sel_changed():
    """Rekonfiguracja przycisków w zależności od stanu zaznaczenia vn'ów."""
    vn_layer = dlg.proj.mapLayersByName("vn_all")[0]
    value = True if vn_layer.selectedFeatureCount() > 0 else False
    dlg.p_vn.widgets["btn_vn_add"].setEnabled(value)
    dlg.p_vn.widgets["btn_vn_sub"].setEnabled(value)
    dlg.p_vn.widgets["btn_vn_unsel"].setEnabled(value)

def vn_layer_update():
    """Załadowanie vn z obszaru wybranych powiatów."""
    # print("[vn_layer_update]")
    with CfgPars() as cfg:
        params = cfg.uri()
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
        dlg.proj.layerTreeRoot().findLayer(dlg.proj.mapLayersByName(layer)[0].id()).setItemVisibilityChecked(True)
    for layer in hide_layers:
        dlg.proj.layerTreeRoot().findLayer(dlg.proj.mapLayersByName(layer)[0].id()).setItemVisibilityChecked(False)

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
        uri = URI_CONST + str(dlg.team_i) +'"."team_viewnet" (geom) sql= ' + str(value)
        layer = dlg.proj.mapLayersByName(key)[0]
        pg_layer_change(uri, layer)

    stage_refresh()  # Odświeżenie sceny

def data_export_init():
    """Odpalony po naciśnięciu przycisku 'data_export'."""
    if dlg.export_panel.isVisible():
        return
    export_path = db_attr_check("t_export_path")
    dlg.export_panel.export_path = export_path
    dlg.export_panel.show()

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

def db_attr_change(tbl, attr, val, sql_bns, user=True, quotes=False):
    """Zmiana atrybutu w db."""
    # print("[db_attr_change(", tbl, ",", attr, "):", val, "]")
    db = PgConn()
    # Aktualizacja atrybutu (attr) w tabeli (tbl) na wartość (val):
    if len(str(val)) == 0:
        val = 'Null'
    else:
        val = f"'{val}'" if quotes else val
    if user:
        sql = f"UPDATE {tbl} SET {attr} = {val}{SQL_1} {dlg.user_id}{sql_bns};"
    else:
        sql = f"UPDATE {tbl} SET {attr} = {val}{sql_bns};"
    if db:
        res = db.query_upd(sql)
        if res:
            return True
        else:
            return False
    else:
        return False

def pg_layer_change(uri, layer):
    """Zmiana zawartości warstwy postgres na podstawie uri"""
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
        if panel != _panel and panel != dlg.p_map:
            panel.setEnabled(not value)

def file_dialog(dir='', for_open=True, fmt='', is_folder=False):
    """Dialog z eksploratorem Windows. Otwieranie/tworzenie folderów i plików."""
    # options = QFileDialog.Options()
    # options |= QFileDialog.DontUseNativeDialog
    # options |= QFileDialog.DontUseCustomDirectoryIcons
    dialog = QFileDialog()
    # dialog.setOptions(options)
    # dialog.setFilter(dialog.filter() | QDir.Hidden)
    if is_folder:  # Otwieranie folderu
        dialog.setFileMode(QFileDialog.DirectoryOnly)
    else:  # Otwieranie pliku
        dialog.setFileMode(QFileDialog.AnyFile)
    # Otwieranie / zapisywanie:
    dialog.setAcceptMode(QFileDialog.AcceptOpen) if for_open else dialog.setAcceptMode(QFileDialog.AcceptSave)
    # Ustawienie filtrowania rozszerzeń plików:
    if fmt != '' and not is_folder:
        dialog.setDefaultSuffix(fmt)
        dialog.setNameFilters([f'{fmt} (*.{fmt})'])
    # Ścieżka startowa:
    if dir != '':
        dialog.setDirectory(str(dir))
    else:
        dialog.setDirectory(str(os.environ["HOMEPATH"]))
    # Przekazanie ścieżki folderu/pliku:
    if dialog.exec_() == QDialog.Accepted:
        path = dialog.selectedFiles()[0]
        return path
    else:
        return None

def sequences_load():
    """Załadowanie z db ustawień użytkownika, dotyczących sekwencyjnego wczytywania podkładów mapowych."""
    # print("[sequences_load]")
    for s in range(1, 4):
        seq = db_seq(s)  # Pobranie danych sekwencji
        if seq:  # Sekwencja nie jest pusta
            # Ustawienie parametru empty w przycisku sekwencji:
            dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].empty = False
            # Aktualizacja ilości podkładów sekwencji seqcfgbox'ie:
            dlg.seq_dock.widgets["scg_seq" + str(s)].cnt = len(seq)
        else:  # Sekwencja jest pusta
            # Ustawienie parametru empty w przycisku sekwencji:
            dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].empty = True
            # Aktualizacja ilości podkładów sekwencji seqcfgbox'ie:
            dlg.seq_dock.widgets["scg_seq" + str(s)].cnt = 0
            seq = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
        # Czyszczenie przycisku sekwencji z danych sekwencji:
        dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].maps.clear()
        # Aktualizacja seqcfg'ów:
        m = 0
        for map in seq:
            # Wczytanie danych do przycisku sekwencji:
            if map[0] > 0:  # Pominięcie w przycisku pustych podkładów
                dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].maps.append([map[0], map[1]])
            # Ustawienie w sekwencji atrybute ge (czy w sekwencji jest Google Earth Pro):
            if map[0] == 6 or map[0] == 11:
                dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].ge = True
            # Wczytanie danych do seqcfg'ów (obiektów przechowujących ustawienia podkładów mapowych z sekwencji):
            dlg.seq_dock.widgets["scg_seq" + str(s)].scgs["scg_" + str(m)].spinbox.value = map[1]  # Opóźnienie
            dlg.seq_dock.widgets["scg_seq" + str(s)].scgs["scg_" + str(m)].map = map[0]  # Id mapy
            m += 1
        # Odkrycie seq_dock'u:
        if not dlg.seq_dock.isVisible():
            dlg.seq_dock.show()

def db_seq(num):
    """Sprawdzenie, czy w tabeli basemaps z aktywnego teamu dla zalogowanego użytkownika są ustawienia dla sekwencji."""
    db = PgConn()
    sql = "SELECT map_id, i_delay_" + str(num) + " FROM team_" + str(dlg.team_i) + ".basemaps WHERE user_id = " + str(dlg.user_id) + " AND i_order_" + str(num) + " IS NOT NULL ORDER BY i_order_" + str(num) + " ASC;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            return res
        else:
            return False

def db_sequence_update(seq, list):
    """Aktualizacja sekwencji w db."""
    # print("[db_sequence_update]")
    if db_sequence_reset(seq):
        print("Wyczyszczono sekwencję w db.")
    else:
        print("Nie udało się wyczyścić sekwencji!")
        return
    db = PgConn()
    sql = "UPDATE team_" + str(dlg.team_i) + ".basemaps AS bm SET i_order_" + str(seq) + " = d.i_order_" + str(seq) + ", i_delay_" + str(seq) + " = d.i_delay_" + str(seq) + " FROM (VALUES %s) AS d (map_id, i_order_" + str(seq) + ", i_delay_" + str(seq) + ") WHERE bm.map_id = d.map_id AND bm.user_id = " + str(dlg.user_id) + ";"
    if db:
        db.query_exeval(sql, list)

def db_sequence_reset(seq):
    """Wyczyszczenie w db dotychczasowych ustawień sekwencji."""
    # print(f"[db_sequence_reset]: {seq}")
    db = PgConn()
    # Aktualizacja i_order_[seq] = NULL i i_delay)[seq] dla użytkownika w tabeli 'basemaps':
    sql = "UPDATE team_" + str(dlg.team_i) + ".basemaps SET i_order_" + str(seq) + " = NULL, i_delay_" + str(seq) + " = NULL WHERE user_id = " + str(dlg.user_id) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            return True
        else:
            return False
    else:
        return False

def next_map():
    """Przejście do następnej mapy w aktywnej sekwencji. Funkcja pod skrót klawiszowy."""
    if dlg.seq_dock.widgets["sqb_seq"].num > 0:
        dlg.seq_dock.widgets["sqb_seq"].next_map()

def prev_map():
    """Przejście do następnej mapy w aktywnej sekwencji. Funkcja pod skrót klawiszowy."""
    if dlg.seq_dock.widgets["sqb_seq"].num > 0:
        dlg.seq_dock.widgets["sqb_seq"].prev_map()

def seq(_num):
    """Aktywowanie wybranej sekwencji lub jej deaktywacja, jeśli już jest aktywna. Funkcja pod skrót klawiszowy."""
    if dlg.seq_dock.widgets["sqb_seq"].num == _num:  # Sekwencja jest aktywna, następuje deaktywacja
        dlg.seq_dock.widgets["sqb_seq"].num = 0
    else:  # Sekwencja zostaje aktywowana
        if dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(_num)].empty:  # Sekwencja jest pusta, przejście do ustawień
            dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(_num)].button.setChecked(False)
            dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(_num)].cfg_clicked()
        else:  # Sekwencja nie jest pusta, następuje jej aktywacja
            dlg.seq_dock.widgets["sqb_seq"].num = _num

def pow_export():
    """Eksport danych powiatu do bazy mdb, kart wyrobisk, zdjęć i załączników."""
    pow_grp = dlg.powiat_i
    pow_name = dlg.powiat_t
    pictures_export(pow_grp, pow_name)
    mdb_export(pow_grp, pow_name)
    card_export(pow_grp, pow_name)
    zal_export(pow_grp, pow_name)

def pictures_export(pow_grp, pow_name):
    """Eksport zdjęć wyrobisk potwierdzonych z danego powiatu, połączony z nadaniem im odpowiednich nazw."""
    source_path = f"C:{os.path.sep}nef{os.path.sep}punkty"
    dest_path = f"C:{os.path.sep}MOEK_2020{os.path.sep}FOTO{os.path.sep}{pow_name}_foto"
    if not os.path.isdir(dest_path):
        os.makedirs(dest_path, exist_ok=True)
    df = wyr_for_pict(pow_grp)
    for index in df.to_records():  # index[1]: wyr_id, index[2]: id_punkt
        wyr_source_path = os.path.join(source_path, str(index[1]))
        if not os.path.isdir(wyr_source_path):
            print(f"!!!!!!!!!!!!!!! Brak folderu ze zdjęciami dla wyrobiska {index[1]}")
            continue
        for cnt, filename in enumerate(os.listdir(wyr_source_path), 1):
            dst = f"{index[2]}_{str(cnt).zfill(2)}.jpg"
            shutil.copy2(os.path.join(wyr_source_path, filename), os.path.join(dest_path, dst))

def mdb_export(pow_grp, pow_name):
    """Export do mdb wyrobisk z danego powiatu."""
    dest_excel = f"C:{os.path.sep}MOEK_2020{os.path.sep}mdb_{pow_name}.xls"
    df = wyr_for_mdb(pow_grp)
    df['NADKL_MIN'] = pd.to_numeric(df['NADKL_MIN'], downcast='float')
    df['NADKL_MAX'] = pd.to_numeric(df['NADKL_MAX'], downcast='float')
    df['MIAZSZ_MIN'] = pd.to_numeric(df['MIAZSZ_MIN'], downcast='float')
    df['MIAZSZ_MAX'] = pd.to_numeric(df['MIAZSZ_MAX'], downcast='float')
    df['WYS_MIN'] = pd.to_numeric(df['WYS_MIN'], downcast='float')
    df['WYS_MAX'] = pd.to_numeric(df['WYS_MAX'], downcast='float')
    df['STAN_MIDAS'] = np.where((df['STAN_MIDAS'] == 'RW') | (df['STAN_MIDAS'] == 'RS'), 'R', df['STAN_MIDAS'])
    df['POW_M2'] = np.where(df['STAN_PNE'] == 'brak', np.nan, df['POW_M2'])
    df.to_excel(dest_excel, index=False, sheet_name='mdb_import')

def szkic_creator(pow_grp, pow_name):
    """Tworzy szkice sytuacyjne wyrobisk."""
    map_cm = 9.21  # Wymiar mapki w cm
    map_px = int(round(map_cm / 0.008465, 0))  # Wymiar mapki w px
    dest_path = f"C:{os.path.sep}MOEK_2021{os.path.sep}{pow_name}{os.path.sep}{pow_name}_karty_szkice"
    STYLE_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'styles' + os.path.sep
    if not os.path.isdir(dest_path):
        os.makedirs(dest_path, exist_ok=True)
    # Zdefiniowanie i symbolizacja warstw, które mają się znaleźć na szkicu sytuacyjnym:
    near_lyrs = []
    far_lyrs = []
    near_basemap = dlg.proj.mapLayersByName("Geoportal")[0]
    far_basemap = dlg.proj.mapLayersByName("OpenStreetMap")[0]
    lyr_names = ["midas_zloza", "midas_wybilansowane", "midas_obszary", "midas_tereny"]
    for lyr_name in lyr_names:
        lyr = dlg.proj.mapLayersByName(lyr_name)[0]
        near_lyrs.append(lyr)
        far_lyrs.append(lyr)
        lyr.loadNamedStyle(f'{STYLE_PATH}{lyr_name}_szkic.qml')
    near_lyrs.append(near_basemap)
    far_lyrs.append(far_basemap)
    df = wyr_for_pict(pow_grp)  # Stworzenie listy wyrobisk
    for index in df.to_records():
        # Wygenerowanie szkicu sytuacyjnego dla wszystkich wyrobisk z powiatu:
        wyr_lyr = wyr_to_lyr(index[1])  # Stworzenie warstwy z geometrią wyrobiska
        if not wyr_lyr.isValid():
            print(f"szkic_creator: warstwa z geometrią wyrobiska {index[1]} nie jest prawidłowa")
            continue
        # Dodanie warstwy z wyrobiskiem do listy pozostałych warstw:
        near_lyrs.insert(0, wyr_lyr)
        far_lyrs.insert(0, wyr_lyr)
        wyr_lyr.loadNamedStyle(f'{STYLE_PATH}wyr_szkic.qml')
        box = wyr_bbox(wyr_lyr)  # Określenie zasięgu przestrzennego wyrobiska
        if not box:
            print(f"szkic_creator: nie udało się określić zasięgu geometrii wyrobiska {index[1]}")
            continue
        near_val = max(box.width(), box.height())  # Wybór szerokości albo długości wyrobiska w m
        far_val = 2302  # Sztuczne ustawienie wymiaru, aby rozszerzyć widok mapki orientacyjnej do skali 1: 25 000
        near_m = scale_interval(near_val)  # Wartość podziałki w m dla mapki zasadniczej
        far_m = 1000  # Wartość podziałki w m dla mapki orientacyjnej
        if near_val < 92.1:  # Wyrobisko zbyt małe i przez to szkic byłby zbyt przybliżony, rozszerzamy widok do skali 1:2000
            near_val = 92.1
        near_ext = sketchmap_extent(box, near_val)  # Ustalenie zasięgu widoku mapki zasadniczej
        far_ext = sketchmap_extent(box, far_val)  # Ustalenie zasięgu widoku mapki orientacyjnej w skali 1:25 000
        near_scl = scale_width(map_cm, map_px, near_val, near_m)  # Długość podziałki liniowej w px
        far_scl = scale_width(map_cm, map_px, far_val, far_m)  # Długość podziałki liniowej w px
        near_img = img_create(map_px, map_px)  # Obiekt obrazka mapki zasadniczej
        far_img = img_create(map_px, map_px)  # Obiekt obrazka mapki orientacyjnej
        comp_img = img_create(map_px * 2, map_px)  # Obiekt obrazka szkicu orientacyjnego
        near_ms = ms_create(near_lyrs, near_ext, near_img.size())  # Obiekt mapki zasadniczej
        far_ms = ms_create(far_lyrs, far_ext, far_img.size())  # Obiekt mapki orientacyjnej
        map_drawing(map_px, near_m, near_scl, near_img, near_ms, True)  # Narysowanie mapki zasadniczej
        map_drawing(map_px, far_m, far_scl, far_img, far_ms, False)  # Narysowanie mapki orientacyjnej
        # Postprodukcja (wyostrzenie) podkładu z mapki orientacyjnej:
        data = far_img.constBits().asstring(far_img.byteCount())
        pil_img = Image.frombuffer('RGB', (far_img.width(), far_img.height()), data, 'raw', 'BGRX')
        pil_img = ImageEnhance.Brightness(pil_img).enhance(0.95)
        pil_img = ImageEnhance.Contrast(pil_img).enhance(1.5)
        pil_img = ImageEnhance.Sharpness(pil_img).enhance(4.0)
        far_img = ImageQt.ImageQt(pil_img)
        # pil_img.save(f"{dest_path}{os.path.sep}{index[2]}.png")
        # Rysowanie szkicu sytuacyjnego:
        src_rect = QRectF(0.0, 0.0, map_px, map_px)
        far_rect = QRectF(0.0, 0.0, map_px, map_px)
        near_rect = QRectF(map_px, 0.0, map_px, map_px)
        p = QPainter()
        p.setRenderHint(QPainter.Antialiasing)
        p.begin(comp_img)
        p.drawImage(far_rect, far_img, src_rect)
        p.drawImage(near_rect, near_img, src_rect)
        p.setPen(QPen(Qt.black, 4, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
        p.drawRect(2, 2, (map_px * 2) - 4, map_px - 4)
        p.drawLine(map_px, 0, map_px, map_px)
        p.setPen(QPen(Qt.black, 4, Qt.SolidLine, Qt.FlatCap, Qt.RoundJoin))
        title_rect = QRectF(831, 2, 514, 80)
        p.fillRect(title_rect, Qt.white)
        p.drawRect(title_rect)
        f = QFont()
        f.setPixelSize(40)
        p.setPen(Qt.black)
        p.setFont(f)
        title_rect.moveTop(0)
        p.drawText(title_rect, Qt.AlignCenter, "SZKIC LOKALIZACYJNY")
        p.end()
        comp_img.save(f"{dest_path}{os.path.sep}{index[2]}.png", "PNG")
        # Usunięcie warstwy z wyrobiskiem:
        del wyr_lyr
        near_lyrs = near_lyrs[1:]
        far_lyrs = far_lyrs[1:]
    for lyr_name in lyr_names:
        dlg.proj.mapLayersByName(lyr_name)[0].loadNamedStyle(f'{STYLE_PATH}{lyr_name}.qml')

def map_drawing(map_px, near_m, scl_px, img, ms, is_near):
    """Rysuje mapkę szkicu lokalizacyjnego. Jeśli is_near == True - rysowanie mapki zasadniczej, False - mapki orientacyjnej."""
    p = QPainter()
    p.setRenderHint(QPainter.Antialiasing)
    p.begin(img)
    # Rendering warstw i etykiet:
    render = QgsMapRendererCustomPainterJob(ms, p)
    render.start()
    render.waitForFinished()
    # Rysowanie podziałki liniowej:
    scl_path = QPainterPath()
    scl_start = 980 if is_near else 267
    y = 50 if is_near else 1052
    x1 = scl_start - scl_px  # Wspólrzędna X początku podziałki
    x2 = x1 + scl_px  # Wspólrzędna X końca podziałki
    scl_pg = scale_shape(x1, x2, y)  # Utworzenie kształtu podziałki
    scl_path.addPolygon(scl_pg)  # Dodanie kształtu do ścieżki
        # Utworzenie napisu dla podziałki liniowej:
    f = QFont()
    f.setPixelSize(24)
    f.setBold(True)
    # Dodanie napisu do ścieżki:
    if is_near:
        scl_path.addText(x2 + 10, 58, f, f"{near_m} m")
    else:
        scl_path.addText(x2 + 10, 1060, f, "1 km")
    p.setPen(QPen(Qt.white, 4, Qt.SolidLine, Qt.RoundCap))
    p.drawPath(scl_path)  # Narysowanie konturu (halo) podziałki białym kolorem
    p.fillPath(scl_path, Qt.black)  # Wypełnienie podziałki czarnym kolorem
        #  Utworzenie napisu informacyjnego o źródle podkładu:
    f.setBold(False)
    f.setPixelSize(28)
    src_path = QPainterPath()
    bm_name = "Geoportal" if is_near else "OpenStreetMap"
    src_path.addText(0, 1070, f, f"źródło: {bm_name}")
    x_off = int(round(map_px - src_path.boundingRect().width() - 30, 0))
    src_path.translate(x_off, 0)
    pen_color = Qt.black if is_near else Qt.white
    fill_color = Qt.white if is_near else Qt.black
    p.setPen(QPen(pen_color, 3, Qt.SolidLine, Qt.RoundCap))
    p.drawPath(src_path)
    p.fillPath(src_path, fill_color)
    p.end()

def scale_width(map_cm, map_px, m_val, a):
    """Zwraca długość podziałki liniowej w px."""
    scl_m = (m_val * 2) / map_cm  # Ilość metrów w 1 cm szkicu
    scl_cm = a / scl_m  # Długość ustalonego odcinka podziałki na szkicu podana w cm
    scl_px = int(round(scl_cm * map_px / map_cm, 0))  # Przeliczenie odcinka podziałki z cm na px
    return scl_px

def ms_create(lyrs, ext, img_size):
    """Zwraca obiekt mapki."""
    ms = QgsMapSettings()
    ms.setOutputDpi(300)
    ms.setLayers(lyrs)
    ms.setExtent(ext)
    ms.setOutputSize(img_size)
    ms.setDestinationCrs(lyrs[0].crs())
    return ms

def img_create(width_px, height_px):
    """Tworzy i konfiguruje obiekt obrazka mapki."""
    img = QImage(QSize(width_px, height_px), QImage.Format_RGB32)
    img.setDotsPerMeterX(11811.0236220472)
    img.setDotsPerMeterY(11811.0236220472)
    return img

def wyr_bbox(wyr_lyr):
    """Zwraca bbox wyrobiska."""
    if wyr_lyr.featureCount() > 0:
        for feat in wyr_lyr.getFeatures():
            return feat.geometry().boundingBox()

def sketchmap_extent(box, m_val):
    """Zwraca zakres widoku mapki szkicu sytuacyjnego"""
    w_off = (m_val * 2 - box.width())/2
    h_off = (m_val * 2 - box.height())/2
    return QgsRectangle(box.xMinimum() - w_off, box.yMinimum() - h_off, box.xMaximum() + w_off, box.yMaximum() + h_off)

def scale_interval(m_val):
    """Zwraca wartość odcinka podziałki na skali metrowej."""
    if m_val <= 25:
        return 5
    elif m_val <= 75:
        return 10
    elif m_val <= 250:
        return 50
    elif m_val <= 500:
        return 100
    else:
        return 500

def scale_shape(x1, x2, y):
    """Zwraca geometrię do narysowania skali metrowej."""
    h = 8.0  # Wysokość "wąsów" na podziałce w px
    pts = [
            (x1 - 1, y - h),
            (x1 + 1, y - h),
            (x1 + 1, y - 2),
            (x2 - 1, y - 2),
            (x2 - 1, y - h),
            (x2 + 1, y - h),
            (x2 + 1, y + h),
            (x2 - 1, y + h),
            (x2 - 1, y + 2),
            (x1 + 1, y + 2),
            (x1 + 1, y + h),
            (x1 - 1, y + h),
            (x1 - 1, y - h)
            ]
    return QPolygonF([QPointF(p[0], p[1]) for p in pts])

def wyr_to_lyr(wyr_id):
    """Tworzy warstwę tymczasową dla geometrii wyrobiska."""
    with CfgPars() as cfg:
        params = cfg.uri()
    uri = params + f'table="team_{dlg.team_i}"."wyr_geom" (geom) sql=wyr_id = {wyr_id}'
    return QgsVectorLayer(uri, "wyr_szkic", "postgres")

def card_export(pow_grp, pow_name):
    """Generator kart wyrobisk z danego powiatu."""
    doc_path = f"C:{os.path.sep}MOEK_2020{os.path.sep}{pow_name}{os.path.sep}{pow_name}_karty_docx"
    pdf_path = f"C:{os.path.sep}MOEK_2020{os.path.sep}{pow_name}{os.path.sep}{pow_name}_karty_pdf"
    dest_excel = f"C:{os.path.sep}MOEK_2020{os.path.sep}karty_{pow_name}.xlsx"
    temp_doc = f"C:{os.path.sep}MOEK_2020{os.path.sep}karta_szablon.docx"
    if not os.path.isdir(doc_path):
        os.makedirs(doc_path, exist_ok=True)
    if not os.path.isdir(pdf_path):
        os.makedirs(pdf_path, exist_ok=True)
    df = wyr_for_card(pow_grp)
    df['NADKL_MIN'] = pd.to_numeric(df['NADKL_MIN'], downcast='float')
    df['NADKL_MAX'] = pd.to_numeric(df['NADKL_MAX'], downcast='float')
    df['MIAZSZ_MIN'] = pd.to_numeric(df['MIAZSZ_MIN'], downcast='float')
    df['MIAZSZ_MAX'] = pd.to_numeric(df['MIAZSZ_MAX'], downcast='float')
    df['WYS_MIN'] = pd.to_numeric(df['WYS_MIN'], downcast='float')
    df['WYS_MAX'] = pd.to_numeric(df['WYS_MAX'], downcast='float')
    df['DLUG_MIN'] = pd.to_numeric(df['DLUG_MIN'], downcast='integer')
    df['DLUG_MAX'] = pd.to_numeric(df['DLUG_MAX'], downcast='integer')
    df['SZER_MIN'] = pd.to_numeric(df['SZER_MIN'], downcast='integer')
    df['SZER_MAX'] = pd.to_numeric(df['SZER_MAX'], downcast='integer')
    df = df.where(pd.notnull(df), None)
    df['STAN_MIDAS'] = np.where((df['STAN_MIDAS'] == 'RW') | (df['STAN_MIDAS'] == 'RS'), 'R', df['STAN_MIDAS'])
    df['ID'] = df['ID'].str.pad(width=5, side='left', fillchar=' ')
    df[['ID_0', 'ID_1', 'ID_2', 'ID_3', 'ID_4', 'ID_5', 'ID_6']] = df['ID'].str.split(pat ="", expand=True)
    df = df.drop(columns=['ID_0', 'ID_6'])
    df['DATA'] = df['DATA'].where(pd.notnull(df['DATA']), "2000-01-01")
    df['DATA'] = pd.to_datetime(df['DATA'])
    df['DD'] = np.where((df['DATA'].dt.day == 1) & (df['DATA'].dt.month == 1) & (df['DATA'].dt.year == 2000), None, df['DATA'].dt.day.astype('str').str.zfill(2))
    df['MM'] = np.where((df['DATA'].dt.day == 1) & (df['DATA'].dt.month == 1) & (df['DATA'].dt.year == 2000), None, df['DATA'].dt.month.astype('str').str.zfill(2))
    df['RR'] = np.where((df['DATA'].dt.day == 1) & (df['DATA'].dt.month == 1) & (df['DATA'].dt.year == 2000), None, df['DATA'].dt.year)
    df['GODZ'] = df['GODZ'].where(pd.notnull(df['GODZ']), "00:00:00")
    df['GODZ'] = pd.to_datetime(df['GODZ'], format='%H:%M:%S')
    df['GODZ_1'] = np.where((df['GODZ'].dt.hour == 0) & (df['GODZ'].dt.minute == 0), None, df['GODZ'].dt.hour.astype('str').str.zfill(2))
    df['GODZ_2'] = np.where((df['GODZ'].dt.hour == 0) & (df['GODZ'].dt.minute == 0), None, df['GODZ'].dt.minute.astype('str').str.zfill(2))
    df[['ID_P0', 'ID_P1', 'ID_P2', 'ID_P3', 'ID_P4', 'ID_P5', 'ID_P6', 'ID_P_', 'ID_P7', 'ID_P8', 'ID_P9', 'ID_P10']] = df['ID_PUNKT'].str.split(pat ="", expand=True)
    df = df.drop(columns=['ID_P0', 'ID_P_', 'ID_P10'])
    df['ID_ARKUSZ'] = df['ID_ARKUSZ'].fillna('        ')
    df[['ID_A0', 'ID_A1', 'ID_A2', 'ID_A3', 'ID_A4', 'ID_A_', 'ID_A5', 'ID_A6', 'ID_A7', 'ID_A8']] = df['ID_ARKUSZ'].str.split(pat ="", expand=True)
    df = df.drop(columns=['ID_A0', 'ID_A_', 'ID_A8'])
    df['POW_M2'] = np.where(df['STAN_PNE'] == 'brak', '–', df['POW_M2'])
    df['KOPALINY'] = np.where(df['KOPALINA_2'].isna(), df['KOPALINA'], df['KOPALINA'] + ' / ' + df['KOPALINA_2'])
    df['WIEKI'] = np.where(df['WIEK_2'].isna(), df['WIEK'], np.where(df['WIEK'] == df['WIEK_2'], df['WIEK'], df['WIEK'] + ' / ' + df['WIEK_2']))
    o_list = ['e', 'rb', 'p', 'op', 'k', 'czp', 'wg', 'el', 'r', 'i']
    for o in o_list:
        df[f'O_{o}'] = np.where((df['ODPADY_1'] == o) | (df['ODPADY_2'] == o) | (df['ODPADY_3'] == o) | (df['ODPADY_4'] == o), 1, 0)
    df = df.where(pd.notnull(df), None)
    for r_index, row in df.iterrows():
        cust_name = row['ID_PUNKT']
        tpl = DocxTemplate(temp_doc)
        jpg_path = f"{szkice_path}{os.path.sep}{cust_name}.png"
        if os.path.isfile(jpg_path):
            # Wczytanie szkicu lokalizacyjnego, jeśli jest:
            tpl.replace_pic("szkic.jpg", jpg_path)
        x = df.to_dict(orient='records')
        context = x
        tpl.render(context[r_index])
        tpl.save(f'{doc_path}{os.path.sep}{cust_name}.docx')
        word_app = client.Dispatch("Word.Application")
        doc = word_app.Documents.Open(f'{doc_path}{os.path.sep}{cust_name}.docx')
        doc.SaveAs(f'{pdf_path}{os.path.sep}{cust_name}.pdf', FileFormat=17)
        doc.Close()
    df.to_excel(dest_excel)

def zal_export(pow_grp, pow_name):
    """Export danych do załączników."""
    dest_excel = f"C:{os.path.sep}MOEK_2020{os.path.sep}zal1_3_{pow_name}.xlsx"
    wb = xls.Workbook(dest_excel)
    ws_1 = wb.add_worksheet('Załącznik 1')
    ws_3 = wb.add_worksheet('Załącznik 3')
    wss = []
    wss.append(ws_1)
    wss.append(ws_3)
    for ws in wss:
        ws.set_paper(8)
        ws.set_landscape()
        ws.center_horizontally()
        ws.set_margins(0.3, 0.3, 0.3, 0.3)
        ws.set_header(margin=0)
        ws.set_footer(margin=0)
    title_1 = "Załącznik 1. Zestawienie zinwentaryzowanych wyrobisk na terenie powiatu starachowickiego – stan na wrzesień 2020 r."
    title_3 = "Załącznik 3. Zestawienie miejsc zinwentaryzowanych w powiecie starachowickim we wrześniu 2020 r. wymagających pilnej interwencji"
    head_1 = "PUNKTY NIEKONCESJONOWANEJ EKSPLOATACJI"
    header = ['Lp.', 'ID PUNKTU', 'MIEJSCOWOŚĆ', 'GMINA', 'ID MIDAS', 'STAN ZAGOSPODAROWANIA ZŁOŻA WG MIDAS', 'STWIERDZONY STAN ZAGOSPODAROWANIA WYROBISKA', 'WYDOBYCIE OD', 'WYDOBYCIE DO', 'KOPALINA', 'WIEK', 'POW (m²)', 'ORIENTACYJNA SKALA EKSPLOATACJI', 'LOKALIZACJA POLA EKSPLOATACJI', 'OBECNOŚĆ ODPADÓW', 'RODZAJE ODPADÓW', 'REKULTYWACJA', 'ZAGROŻENIA', 'PROBLEM DO ZGŁOSZENIA', 'OPIS POWODU ZGŁOSZENIA', 'DATA WIZJI TERENOWEJ', 'DATA POPRZEDNIEJ WIZJI TERENOWEJ', 'UWAGI']
    col_widths = [1.86, 6.43, 8.71, 5.71, 3.86, 6.29, 8.29, 7.29, 7.29, 6.14, 5.86, 3.29, 10.43, 8.43, 6.71, 9.29, 9.71, 8.29, 7.43, 11.43, 7.43, 7.57, 28.86]
    cols = enumerate(col_widths)
    head_2 = "NIEZREKULTYWOWANE WYROBISKA, W KTÓRYCH NIE STWIERDZONO NIEKONCESJONOWANEJ EKSPLOATACJI"
    title_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 10, 'bold': True})
    header_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 6, 'bold': False, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#d9d9d9', 'border': 7})
    head_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 10, 'bold': False,'align': 'center', 'valign': 'vcenter', 'border': 7})
    cell_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 6, 'bold': False, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'border': 7})
    date_fm = wb.add_format({'num_format': 'dd.mm.yyyy', 'font_name': 'Times New Roman', 'font_size': 6, 'bold': False, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'border': 7})
    ws_1.merge_range(0, 0, 0, 22, title_1, title_fm)
    for col in cols:
        ws_1.set_column(col[0], col[0], col[1])
    ws_1.set_row(1, 8)
    ws_1.write_row(2, 0, header, header_fm)
    r = 2
    df = wyr_for_zal(pow_grp)
    odp_cols = ['ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4']
    df["ODPADY"] = df[odp_cols].apply(lambda x: '; '.join(x.dropna()), axis=1)
    df.drop(odp_cols, axis=1, inplace=True)
    df['POW_M2'] = np.where(df['STAN_PNE'] == 'brak wyrobiska', '–', df['POW_M2'])
    df['KOPALINA'] = np.where(df['KOPALINA_2'].isna(), df['KOPALINA'], df['KOPALINA'] + ' / ' + df['KOPALINA_2'])
    df['WIEK'] = np.where(df['WIEK_2'].isna(), df['WIEK'], np.where(df['WIEK'] == df['WIEK_2'], df['WIEK'], df['WIEK'] + ' / ' + df['WIEK_2']))
    df.drop(['KOPALINA_2', 'WIEK_2'], axis=1, inplace=True)
    df_cols = df.columns.tolist()
    df_cols = df_cols[:17] + df_cols[-1:] + df_cols[17:-1]
    df = df[df_cols]
    df_nopne = df[df['CZY_PNE'] == False]
    df_pne = df[~df.index.isin(df_nopne.index)]
    df_zal3 = df[df['ZGLOSZENIE'] != 'brak']
    if len(df_pne) > 0:
        df_pne = df_pne.reset_index(drop=True)
        df_pne.index += 1
        df_pne.drop(['CZY_PNE', 'CZY_ZLOZE', 'STAN_REKUL'], axis=1, inplace=True)
        r += 1
        ws_1.set_row(r, 19.5)
        ws_1.merge_range(r, 0, r, 22, head_1, head_fm)
        df_pne = df_pne.where(pd.notnull(df_pne), None)
        for index in df_pne.to_records():
            r += 1
            ws_1.write_row(r, 0, index, cell_fm)
            date_vals = (index[20], index[21])
            ws_1.write_row(r, 20, date_vals, date_fm)
    if len(df_nopne) > 0:
        df_nopne = df_nopne.reset_index(drop=True)
        df_nopne.index += 1
        df_nopne.drop(['CZY_PNE', 'CZY_ZLOZE', 'STAN_REKUL'], axis=1, inplace=True)
        r += 1
        ws_1.set_row(r, 19.5)
        ws_1.merge_range(r, 0, r, 22, head_2, head_fm)
        df_nopne = df_nopne.where(pd.notnull(df_nopne), None)
        for index in df_nopne.to_records():
            r += 1
            ws_1.write_row(r, 0, index, cell_fm)
            date_vals = (index[20], index[21])
            ws_1.write_row(r, 20, date_vals, date_fm)
    if len(df_zal3) > 0:
        df_zal3 = df_zal3.reset_index(drop=True)
        df_zal3.index += 1
        df_zal3.drop(['CZY_PNE', 'CZY_ZLOZE', 'STAN_REKUL'], axis=1, inplace=True)
        ws_3.merge_range(0, 0, 0, 22, title_3, title_fm)
        cols = enumerate(col_widths)
        for col in cols:
            ws_3.set_column(col[0], col[0], col[1])
        ws_3.set_row(1, 8)
        ws_3.write_row(2, 0, header, header_fm)
        r = 2
        df_zal3 = df_zal3.where(pd.notnull(df_zal3), None)
        for index in df_zal3.to_records():
            r += 1
            ws_3.write_row(r, 0, index, cell_fm)
            date_vals = (index[20], index[21])
            ws_3.write_row(r, 20, date_vals, date_fm)
    try:
        wb.close()
    except Exception as err:
        QMessageBox.warning(None, "Generator załączników", f"Plik {dest_excel} jest zablokowany dla zapisu. Sprawdź, czy nie jest otwarty - jeśli tak, zamknij go i ponów eksport.")

def wyr_for_pict(pow_grp):
    """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i wygenerowanymi numerami id_punkt."""
    db = PgConn()
    sql = f"SELECT wyr_id, concat(pow_id, '_', order_id) as id_punkt FROM team_{dlg.team_i}.wyr_prg WHERE pow_grp = '{pow_grp}' and order_id IS NOT NULL ORDER BY order_id;"
    if db:
        mdf = db.query_pd(sql, ['wyr_id', 'id_punkt'])
        if isinstance(mdf, pd.DataFrame):
            return mdf if len(mdf) > 0 else None
        else:
            return None

def wyr_for_card(pow_grp):
    """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i atrybutami potrzebnymi do wygenerowania kart."""
    db = PgConn()
    sql = f"SELECT COALESCE(w.t_teren_id, p.wyr_id::varchar) AS id, CONCAT(p.pow_id, '_', p.order_id) AS id_punkt, d.date_fchk, d.time_fchk, w.t_wn_id, p.t_mie_name, p.t_gmi_name, p.t_pow_name, p.t_woj_name, ST_X(w.centroid) as x_92, ST_Y(w.centroid) as y_92, CASE WHEN w.t_midas_id is null THEN false ELSE true END AS czy_zloze, w.t_midas_id, d.t_stan_midas, d.b_pne_zloze, d.b_pne_poza, d.t_stan_pne, d.t_zloze_od, d.t_zloze_do, d.t_wyr_od, d.t_wyr_do, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina AND d.wyr_id = p.wyr_id) AS kopalina, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina_2 AND d.wyr_id = p.wyr_id) AS kopalina_2, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek AND d.wyr_id = p.wyr_id) AS wiek, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek_2 AND d.wyr_id = p.wyr_id) AS wiek_2, d.n_nadkl_min, d.n_nadkl_max, d.n_miazsz_min, d.n_miazsz_max, d.i_dlug_min, d.i_dlug_max, d.i_szer_min, d.i_szer_max, d.n_wys_min, d.n_wys_max, d.i_area_m2, d.t_wyrobisko, d.t_zawodn, d.t_eksploat, d.t_wydobycie, d.t_odpady_1, d.t_odpady_2, d.t_odpady_3, d.t_odpady_4, d.t_wyp_odpady, d.t_odpady_opak, d.t_odpady_inne, d.t_rekultyw, d.t_dojazd, d.t_zagrozenia, d.t_zgloszenie, d.t_powod, d.i_ile_zalacz, w.t_notatki, d.t_autor FROM team_{dlg.team_i}.wyrobiska AS w INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE p.pow_grp = '{pow_grp}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
    if db:
        mdf = db.query_pd(sql, ['ID', 'ID_PUNKT', 'DATA', 'GODZ', 'ID_ARKUSZ', 'MIEJSCE', 'GMINA', 'POWIAT', 'WOJEWODZTWO', 'X_92', 'Y_92', 'CZY_ZLOZE', 'ID_MIDAS', 'STAN_MIDAS', 'PNE_ZLOZE', 'PNE_POZA', 'STAN_PNE', 'ZLOZE_OD', 'ZLOZE_DO', 'PNE_OD', 'PNE_DO', 'KOPALINA', 'KOPALINA_2', 'WIEK', 'WIEK_2', 'NADKL_MIN', 'NADKL_MAX', 'MIAZSZ_MIN', 'MIAZSZ_MAX', 'DLUG_MIN', 'DLUG_MAX', 'SZER_MIN', 'SZER_MAX', 'WYS_MIN', 'WYS_MAX', 'POW_M2', 'WYROBISKO', 'ZAWODN', 'EXPLOAT', 'WYDOBYCIE', 'ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4', 'WYP_ODPADY', 'O_OPAK', 'O_INNE', 'REKULTYW', 'DOJAZD', 'ZAGROZENIA', 'ZGLOSZENIE', 'POWOD', 'ILE_ZALACZ', 'UWAGI', 'AUTORZY'])
        if isinstance(mdf, pd.DataFrame):
            return mdf if len(mdf) > 0 else None
        else:
            return None

def wyr_for_mdb(pow_grp):
    """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i atrybutami potrzebnymi do eksportu mdb."""
    db = PgConn()
    sql = f"SELECT CONCAT(p.pow_id, '_', p.order_id) AS id_punkt, w.t_wn_id, CASE WHEN d.time_fchk IS NOT NULL THEN (d.date_fchk + d.time_fchk) ELSE d.date_fchk END AS data, p.t_mie_name, d.b_teren, d.b_pne, CASE COALESCE(w.t_midas_id, 'null_val') WHEN 'null_val' THEN false ELSE true END AS czy_zloze, w.t_midas_id, d.t_stan_midas, d.b_pne_zloze, d.b_pne_poza, d.t_stan_pne, d.t_zloze_od, d.t_zloze_do, d.t_wyr_od, d.t_wyr_do, d.t_kopalina, d.t_kopalina_2, d.t_wiek, d.t_wiek_2, d.n_nadkl_min, d.n_nadkl_max, d.n_miazsz_min, d.n_miazsz_max, d.i_dlug_min, d.i_dlug_max, d.i_szer_min, d.i_szer_max, d.n_wys_min, d.n_wys_max, d.i_area_m2, d.t_wyrobisko, d.t_zawodn, d.t_eksploat, d.t_wydobycie, d.t_wyp_odpady, d.t_odpady_1, d.t_odpady_2, d.t_odpady_3, d.t_odpady_4, d.t_stan_rekul, d.t_rekultyw, d.t_dojazd, d.t_zagrozenia, d.t_zgloszenie, d.t_powod, w.t_notatki, (SELECT t_autor FROM public.teams WHERE team_id = {dlg.team_i}), ST_X(w.centroid) as x_92, ST_Y(w.centroid) as y_92 FROM team_{dlg.team_i}.wyrobiska AS w INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE p.pow_grp = '{pow_grp}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
    if db:
        mdf = db.query_pd(sql, ['ID_PUNKT', 'ID_ARKUSZ', 'DATA', 'MIEJSCE', 'CZY_TEREN', 'CZY_PNE', 'CZY_ZLOZE', 'ID_MIDAS', 'STAN_MIDAS', 'PNE_ZLOZE', 'PNE_POZA', 'STAN_PNE', 'ZLOZE_OD', 'ZLOZE_DO', 'PNE_OD', 'PNE_DO', 'KOPALINA', 'KOPALINA_2', 'WIEK', 'WIEK_2', 'NADKL_MIN', 'NADKL_MAX', 'MIAZSZ_MIN', 'MIAZSZ_MAX', 'DLUG_MIN', 'DLUG_MAX', 'SZER_MIN', 'SZER_MAX', 'WYS_MIN', 'WYS_MAX', 'POW_M2', 'WYROBISKO', 'ZAWODN', 'EXPLOAT', 'WYDOBYCIE', 'WYP_ODPADY', 'ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4', 'STAN_REKUL', 'REKULTYW', 'DOJAZD', 'ZAGROZENIA', 'ZGLOSZENIE', 'POWOD', 'UWAGI', 'AUTOR', 'X_92', 'Y_92'])
        if isinstance(mdf, pd.DataFrame):
            return mdf if len(mdf) > 0 else None
        else:
            return None

def wyr_for_zal(pow_grp):
    """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i atrybutami potrzebnymi do załącznika nr 1."""
    db = PgConn()
    sql = f"SELECT CONCAT(p.pow_id, '_', p.order_id) AS id_punkt, p.t_mie_name, p.t_gmi_name, d.b_pne, CASE COALESCE(w.t_midas_id, 'null_val') WHEN 'null_val' THEN false ELSE true END AS czy_zloze, w.t_midas_id, (SELECT s.t_desc FROM public.sl_stan_midas AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_stan_midas AND d.wyr_id = p.wyr_id) AS stan_midas, (SELECT s.t_desc FROM public.sl_stan_pne AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_stan_pne AND d.wyr_id = p.wyr_id) AS stan_pne, d.t_wyr_od, d.t_wyr_do, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina AND d.wyr_id = p.wyr_id) AS kopalina, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina_2 AND d.wyr_id = p.wyr_id) AS kopalina_2, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek AND d.wyr_id = p.wyr_id) AS wiek, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek_2 AND d.wyr_id = p.wyr_id) AS wiek_2, d.i_area_m2, (SELECT s.t_desc FROM public.sl_eksploatacja AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_eksploat AND d.wyr_id = p.wyr_id) AS eksploatacja, (SELECT s.t_desc FROM public.sl_wydobycie AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wydobycie AND d.wyr_id = p.wyr_id) AS wydobycie, (SELECT s.t_desc FROM public.sl_wyp_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wyp_odpady AND d.wyr_id = p.wyr_id) AS wyp_odpady, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_1 AND d.wyr_id = p.wyr_id) AS odpady_1, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_2 AND d.wyr_id = p.wyr_id) AS odpady_2, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_3 AND d.wyr_id = p.wyr_id) AS odpady_3, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_4 AND d.wyr_id = p.wyr_id) AS odpady_4, d.t_stan_rekul, d.t_rekultyw, d.t_zagrozenia, (SELECT s.t_desc FROM public.sl_zgloszenie AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_zgloszenie AND d.wyr_id = p.wyr_id) AS zgloszenie, d.t_powod, d.date_fchk, CASE COALESCE(w.t_wn_id, 'null_val') WHEN 'null_val' THEN Null ELSE (SELECT e.data_kontrol FROM external.wn_pne AS e, team_{dlg.team_i}.wyrobiska AS w WHERE e.id_arkusz = w.t_wn_id AND w.wyr_id = p.wyr_id) END AS prev_date, w.t_notatki FROM team_{dlg.team_i}.wyrobiska AS w INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE p.pow_grp = '{pow_grp}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
    if db:
        mdf = db.query_pd(sql, ['ID_PUNKT', 'MIEJSCE', 'GMINA', 'CZY_PNE', 'CZY_ZLOZE', 'ID_MIDAS', 'STAN_MIDAS', 'STAN_PNE', 'PNE_OD', 'PNE_DO', 'KOPALINA', 'KOPALINA_2', 'WIEK', 'WIEK_2', 'POW_M2', 'EXPLOAT', 'WYDOBYCIE', 'WYP_ODPADY', 'ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4', 'STAN_REKUL', 'REKULTYW', 'ZAGROZENIA', 'ZGLOSZENIE', 'POWOD', 'DATE', 'PREV_DATE', 'UWAGI'])
        if isinstance(mdf, pd.DataFrame):
            return mdf if len(mdf) > 0 else None
        else:
            return None
