#!/usr/bin/python
import pandas as pd
import math

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.gui import QgsMapToolIdentify, QgsMapTool, QgsRubberBand
from qgis.core import QgsSettings, QgsGeometry, QgsVectorLayer, QgsFeature, QgsWkbTypes, QgsPointXY, QgsExpression, QgsExpressionContextUtils, QgsCoordinateReferenceSystem, QgsFeatureRequest, QgsRectangle, QgsPointLocator, edit
from qgis.PyQt.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QKeySequence, QCursor
from qgis.utils import iface
from itertools import combinations

from .classes import PgConn, CfgPars, threading_func
from .viewnet import vn_change, vn_powsel, vn_polysel
from .main import wyr_powiaty_change, marsz_powiaty_change, wyr_layer_update, parking_layer_update, marsz_layer_update, db_attr_change, get_wyr_ids, get_flag_ids, get_parking_ids, get_marsz_ids, wdf_update

dlg = None

def dlg_maptools(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg


class ObjectManager:
    """Menedżer obiektów."""
    def __init__(self, dlg, canvas):
        self.init_void = True
        self.dlg = dlg  # Referencja do wtyczki
        self.canvas = canvas  # Referencja do mapy
        self.flag_clicked = False
        self.parking_clicked = False
        self.marsz_clicked = False
        self.wyr_clicked = False
        self.flag_ids = []
        self.flag = None
        self.flag_data = []
        self.flag_hidden = None
        self.parking_ids = []
        self.parking = None
        self.parking_data = []
        self.parking_hidden = None
        self.marsz_ids = []
        self.marsz = None
        self.marsz_data = []
        self.wyr_ids = []
        self.wyr = None
        self.wyr_data = []
        self.order_ids = []
        self.order = None
        self.wn_ids = []
        self.wn = None
        self.wn_data = []
        self.wn_pow = []
        self.p_vn = False
        self.init_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if self.init_void:  # Blokada przed odpalaniem podczas ładowania wtyczki
            return
        if attr == "flag":
            # Zmiana aktualnej flagi:
            QgsExpressionContextUtils.setProjectVariable(dlg.proj, 'flag_sel', val)
            self.flag_hidden = None
            if val:
                self.flag_data = self.flag_update()
                self.list_position_check("flag")
                self.dlg.flag_panel.flag_tools.fchk = self.flag_data[1]  # Aktualizacja przycisku fchg
                self.dlg.flag_panel.hash.set_value(self.flag_data[2])  # Aktualizacja teren_id
                txt = self.param_parser(self.flag_data[3])
                self.dlg.flag_panel.notepad_box.value_change(txt)  # Aktualizacja tekstu notatki
                if self.wn:
                    # Wyłączenie panelu wn, jeśli jest włączony:
                    self.wn = None
                if self.parking:
                    # Wyłączenie panelu miejsc parkingowych, jeśli jest włączony:
                    self.parking = None
            if self.dlg.mt.mt_name == "flag_move":
                self.dlg.mt.init("multi_tool")
            self.dlg.flag_panel.id_spinbox.id = val if val else None
            self.dlg.flag_panel.show() if val else self.dlg.flag_panel.hide()
        elif attr == "flag_hidden":
            # Zmiana flagi ukrytej (aktywowana przy przenoszeniu flagi):
            QgsExpressionContextUtils.setProjectVariable(dlg.proj, 'flag_hidden', val)
            dlg.proj.mapLayersByName("flagi_bez_teren")[0].triggerRepaint()
            dlg.proj.mapLayersByName("flagi_z_teren")[0].triggerRepaint()
        elif attr == "flag_ids":
            # Zmiana listy dostępnych flag:
            flag_check = self.list_position_check("flag")
            if not flag_check:
                self.flag = None
        elif attr == "wyr":
            # Zmiana aktualnego wyrobiska:
            QgsExpressionContextUtils.setProjectVariable(dlg.proj, 'wyr_sel', val)
            wyr_point_lyrs_repaint()
            dlg.proj.mapLayersByName("wyr_poly")[0].triggerRepaint()
            wdf_update()
            if dlg.mt.mt_name == "wn_pick" or dlg.wyr_panel.mt_enabled:
                dlg.mt.init("multi_tool")
            if val:
                self.wyr_data = self.wyr_update()
                self.list_position_check("wyr")
                area_txt = f"{self.wyr_data[4]} m\u00b2 "
                self.dlg.wyr_panel.lok.set_tooltip(f'<html><head/><body><p style="text-indent:11px; margin:4px">MIEJSCOWOŚĆ: &nbsp;{self.wyr_data[52]}</p><p style="text-indent: 53px; margin:4px">GMINA: &nbsp;{self.wyr_data[53]}</p><p style="text-indent: 48px; margin:4px">POWIAT: &nbsp;{self.wyr_data[54]}</p><p style="text-indent: 0px; margin:4px">WOJEWÓDZTWO: &nbsp;{self.wyr_data[55]}</p></body></html>')
                # self.dlg.wyr_panel.lok.set_tooltip(f'<html><head/><body><p>&nbsp;&nbsp;&nbsp;MIEJSCOWOŚĆ &nbsp;{self.wyr_data[52]}<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;GMINA &nbsp;{self.wyr_data[53]}<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;POWIAT &nbsp;{self.wyr_data[54]}<br>WOJEWÓDZTWO &nbsp;{self.wyr_data[55]}</p></body></html>')
                self.dlg.wyr_panel.hash.set_value(self.wyr_data[51])  # Aktualizacja teren_id
                self.dlg.wyr_panel.area_label.setText(area_txt)  # Aktualizacja powierzchni wyrobiska
                self.dlg.wyr_panel.status_selector.set_case(self.wyr_data[1], self.wyr_data[2])  # Aktualizacja statusu wyrobiska
                self.dlg.wyr_panel.wn_picker.wn_id = self.wyr_data[3]  # Aktualizacja wn_id
                self.dlg.wyr_panel.wdf_sel_update()  # Aktualizacja zaznaczenia wiersza w tv_wdf
                dlg.wyr_panel.focus_void = True
                self.dlg.wyr_panel.values_update(self.wyr_data)  # Aktualizacja atrybutów
                dlg.wyr_panel.focus_void = False
            self.dlg.wyr_panel.show() if val else self.dlg.wyr_panel.hide()
            self.dlg.wyr_panel.id_box.id = val if val else None
            if dlg.wyr_panel.status_selector.case == 1:
                self.set_order_id()
        elif attr == "wyr_ids":
            # Zmiana listy dostępnych wyrobisk:
            wyr_check = self.list_position_check("wyr")
            if not wyr_check:
                self.wyr = None
        elif attr == "wn":
            # Zmiana aktualnego punktu WN_PNE:
            dlg.wn_panel.hide()
            QgsExpressionContextUtils.setProjectVariable(dlg.proj, 'wn_sel', val)
            dlg.proj.mapLayersByName("wn_pne")[0].triggerRepaint()
            if val:
                self.wn_data = self.wn_update()
                self.wn_pow = self.wn_pow_update()
                self.list_position_check("wn")
                if self.flag:
                    # Wyłączenie panelu flagi, jeśli jest włączony:
                    self.flag = None
                if self.parking:
                    # Wyłączenie panelu miejsc parkowania, jeśli jest włączony:
                    self.parking = None
                dlg.wn_panel.values_update(self.wn_data)
                dlg.wn_panel.pow_update(self.wn_pow)
            dlg.wn_panel.id_box.id = val if val else None
            dlg.wn_panel.show() if val else dlg.wn_panel.hide()
        elif attr == "order" and val:
            self.list_position_check("order")
            dlg.wyr_panel.order_box.id = val
        elif attr == "order_ids" and val:
            self.set_order_id()
        elif attr == "wn_ids":
            # Zmiana listy dostępnych punktów WN_PNE:
            wn_check = self.list_position_check("wn")
            if not wn_check:
                self.wn = None
        elif attr == "parking":
            # Zmiana aktualnego parkingu:
            QgsExpressionContextUtils.setProjectVariable(dlg.proj, 'parking_sel', val)
            self.parking_hidden = None
            if val:
                self.parking_data = self.parking_update()
                self.list_position_check("parking")
                self.dlg.parking_panel.parking_tools.status = self.parking_data[1]  # Aktualizacja przycisku status
                if self.wn:
                    # Wyłączenie panelu wn, jeśli jest włączony:
                    self.wn = None
                if self.flag:
                    # Wyłączenie panelu flagi, jeśli jest włączony:
                    self.flag = None
            if self.dlg.mt.mt_name == "parking_move":
                self.dlg.mt.init("multi_tool")
            self.dlg.parking_panel.id_box.id = val if val else None
            self.dlg.parking_panel.show() if val else self.dlg.parking_panel.hide()
        elif attr == "parking_hidden":
            # Zmiana parkingu ukrytego (aktywowany przy przenoszeniu parkingu):
            QgsExpressionContextUtils.setProjectVariable(dlg.proj, 'parking_hidden', val)
            dlg.proj.mapLayersByName("parking_planowane")[0].triggerRepaint()
            dlg.proj.mapLayersByName("parking_odwiedzone")[0].triggerRepaint()
        elif attr == "parking_ids":
            # Zmiana listy dostępnych parkingów:
            parking_check = self.list_position_check("parking")
            if not parking_check:
                self.parking = None
        elif attr == "marsz":
            # Zmiana aktualnej marszruty:
            QgsExpressionContextUtils.setProjectVariable(dlg.proj, 'marsz_sel', val)
            if val:
                self.marsz_data = self.marsz_update()
            else:
                dlg.marsz_panel.hide()
            dlg.proj.mapLayersByName("marszruty")[0].triggerRepaint()

    def flag_hide(self, _bool):
        """Ukrywa lub pokazuje zaznaczoną flagę."""
        if _bool:
            self.flag_hidden = self.flag
        else:
            self.flag_hidden = None

    def parking_hide(self, _bool):
        """Ukrywa lub pokazuje zaznaczony parking."""
        if _bool:
            self.parking_hidden = self.parking
        else:
            self.parking_hidden = None

    def obj_change(self, obj_data, loc):
        """Zmiana zaznaczenia obiektu."""
        lyr_name = obj_data[0]
        if lyr_name == "wyr_point":
            self.wyr = obj_data[1][0]
        elif lyr_name == "flagi_z_teren" or lyr_name == "flagi_bez_teren":
            if self.flag != obj_data[1][0]:
                self.flag = obj_data[1][0]
        elif lyr_name == "parking_planowane" or lyr_name == "parking_odwiedzone":
            if self.parking != obj_data[1][0]:
                self.parking = obj_data[1][0]
        elif lyr_name == "marszruty":
            if self.marsz != obj_data[1][0]:
                self.marsz = obj_data[1][0]
            self.marsz_menu_show(loc)
        elif lyr_name == "wn_pne":
            self.wn = obj_data[1][0]

    def clear_sel(self):
        """Odznaczenie wybranych flag, wyrobisk, parkingów, marszrut i punktów WN_PNE."""
        if self.flag:
            self.flag = None
        if self.parking:
            self.parking = None
        if self.marsz:
            self.marsz = None
        if self.wyr:
            self.wyr = None
        if self.order:
            self.order = None
        if self.wn:
            self.wn = None

    def marsz_menu_show(self, loc):
        """Umiejscawia i wyświetla menu kontekstowe marszrut na linii przy kursorze."""
        extent = iface.mapCanvas().extent()
        geom = loc
        x_map = round(extent.xMaximum()) - round(extent.xMinimum())
        y_map = round(extent.yMaximum()) - round(extent.yMinimum())
        xp = round(geom.x()) - round(extent.xMinimum())
        yp = round(extent.yMaximum()) - round(geom.y())
        x_scr = round(xp * iface.mapCanvas().width() / x_map)
        y_scr = round(yp * iface.mapCanvas().height() / y_map)
        dlg.marsz_panel.move(x_scr - 56, y_scr)
        dlg.marsz_panel.show()

    def edit_mode(self, enabled):
        """Zmiana ui pod wpływem włączenia/wyłączenia PolyEditMapTool."""
        dlg.wyr_panel.hide() if enabled else dlg.wyr_panel.show()
        dlg.side_dock.hide() if enabled else dlg.side_dock.show()
        dlg.bottom_dock.show() if enabled else dlg.bottom_dock.hide()
        dlg.proj.layerTreeRoot().findLayer(dlg.proj.mapLayersByName("wyr_point")[0].id()).setItemVisibilityChecked(not enabled)
        dlg.proj.layerTreeRoot().findGroup("vn").setItemVisibilityChecked(not enabled)
        dlg.p_team.setEnabled(not enabled)
        dlg.p_pow.setEnabled(not enabled)
        dlg.p_vn.setEnabled(not enabled)
        if enabled:
            if self.flag:
                # Schowanie flag_panel:
                dlg.flag_panel.hide()
            if self.parking:
                # Schowanie parking_panel:
                dlg.parking_panel.hide()
            if dlg.p_vn.is_active():
                # Wyłączenie skrótów klawiszowych viewnet:
                self.p_vn = True
                dlg.hk_vn = False
        else:
            if self.flag:
                # Ponowne pokazanie flag_panel:
                dlg.flag_panel.show()
            if self.parking:
                # Ponowne pokazanie parking_panel:
                dlg.parking_panel.show()
            if self.p_vn:
                # Ponowne włączenie skrótów klawiszowych viewnet:
                self.p_vn = False
                dlg.hk_vn = True

    def param_parser(self, val):
        """Zwraca wartość przerobioną na tekst (pusty, jeśli None)."""
        return f'{val}' if val != None else f''

    def object_prevnext(self, _obj, next):
        """Aktywuje kolejny obiekt z listy."""
        if _obj == "flag":
            obj = "self.flag"
            ids = self.flag_ids
            val = self.flag
            is_int = True
        elif _obj == "parking":
            obj = "self.parking"
            ids = self.parking_ids
            val = self.parking
            is_int = True
        elif _obj == "wyr":
            obj = "self.wyr"
            ids = self.wyr_ids
            val = self.wyr
            is_int = True
        elif _obj == "order":
            obj = "self.wyr"
            ids = [i[1] for i in self.order_ids]
            val = self.wyr
            is_int = True
            _obj = "wyr"
        elif _obj == "wn":
            obj = "self.wn"
            ids = self.wn_ids
            val = self.wn
            is_int = False
        else:
            return
        cur_id_idx = ids.index(val)  # Pozycja na liście aktualnego obiektu
        exec_val = ids[cur_id_idx + 1] if next else ids[cur_id_idx - 1]  # Wartość następna / poprzednia
        exec(f"{obj} = {exec_val}") if is_int else exec(f"{obj} = '{exec_val}'")  # Zmiana aktualnego obiektu
        self.pan_to_object(_obj)  # Centrowanie widoku mapy na nowy obiekt

    def flag_update(self):
        """Zwraca dane flagi."""
        db = PgConn()
        sql = "SELECT id, b_fieldcheck, t_teren_id, t_notatki FROM team_" + str(dlg.team_i) + ".flagi WHERE id = " + str(self.flag) + ";"
        if db:
            res = db.query_sel(sql, False)
            if not res:
                print(f"Nie udało się wczytać danych flagi: {self.flag}")
                return None
            else:
                return res

    def parking_update(self):
        """Zwraca dane parkingu."""
        db = PgConn()
        sql = "SELECT id, i_status FROM team_" + str(dlg.team_i) + ".parking WHERE id = " + str(self.parking) + ";"
        if db:
            res = db.query_sel(sql, False)
            if not res:
                print(f"Nie udało się wczytać danych parkingu: {self.parking}")
                return None
            else:
                return res

    def marsz_update(self):
        """Zwraca dane marszruty."""
        db = PgConn()
        sql = "SELECT marsz_id, marsz_m, marsz_t FROM team_" + str(dlg.team_i) + ".marsz WHERE marsz_id = " + str(self.marsz) + ";"
        if db:
            res = db.query_sel(sql, False)
            if not res:
                print(f"Nie udało się wczytać danych marszruty: {self.marsz}")
                return None
            else:
                return res

    def wyr_update(self):
        """Zwraca dane wyrobiska."""
        db = PgConn()
        if dlg.wyr_panel.pow_all:
            sql = "SELECT w.wyr_id, w.b_after_fchk, w.b_confirmed, w.t_wn_id, d.i_area_m2, d.t_wyr_od, d.t_wyr_do, w.t_notatki, d.i_dlug_min, d.i_dlug_max, d.i_szer_min, d.i_szer_max, d.n_wys_min, d.n_wys_max, d.n_nadkl_min, d.n_nadkl_max, d.n_miazsz_min, d.n_miazsz_max, d.t_wyrobisko, d.t_zawodn, d.t_eksploat, d.t_wydobycie, d.t_wyp_odpady, d.t_odpady_1, d.t_odpady_2, d.t_odpady_3, d.t_odpady_4, d.t_odpady_opak, d.t_odpady_inne, d.t_stan_rekul, d.t_rekultyw, d.t_dojazd, d.t_zagrozenia, d.t_zgloszenie, d.t_powod, d.t_stan_pne, d.t_kopalina, d.t_kopalina_2, d.t_wiek, d.t_wiek_2, d.time_fchk, d.date_fchk, d.b_teren, w.t_midas_id, d.t_stan_midas, d.t_zloze_od, d.t_zloze_do, d.b_pne_zloze, d.b_pne_poza, d.i_ile_zalacz, d.t_autor, w.t_teren_id, p.t_mie_name, p.t_gmi_name, p.t_pow_name, p.t_woj_name FROM team_" + str(dlg.team_i) + ".wyr_dane AS d INNER JOIN team_" + str(dlg.team_i) + ".wyrobiska AS w USING(wyr_id) WHERE wyr_id = '" + str(self.wyr) + "' INNER JOIN team_" + str(dlg.team_i) + ".wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE w.wyr_id = '" + str(self.wyr) + "' AND p.pow_grp = '" + str(dlg.powiat_i) + "';"
        else:
            sql = "SELECT w.wyr_id, w.b_after_fchk, w.b_confirmed, w.t_wn_id, d.i_area_m2, d.t_wyr_od, d.t_wyr_do, w.t_notatki, d.i_dlug_min, d.i_dlug_max, d.i_szer_min, d.i_szer_max, d.n_wys_min, d.n_wys_max, d.n_nadkl_min, d.n_nadkl_max, d.n_miazsz_min, d.n_miazsz_max, d.t_wyrobisko, d.t_zawodn, d.t_eksploat, d.t_wydobycie, d.t_wyp_odpady, d.t_odpady_1, d.t_odpady_2, d.t_odpady_3, d.t_odpady_4, d.t_odpady_opak, d.t_odpady_inne, d.t_stan_rekul, d.t_rekultyw, d.t_dojazd, d.t_zagrozenia, d.t_zgloszenie, d.t_powod, d.t_stan_pne, d.t_kopalina, d.t_kopalina_2, d.t_wiek, d.t_wiek_2, d.time_fchk, d.date_fchk, d.b_teren, w.t_midas_id, d.t_stan_midas, d.t_zloze_od, d.t_zloze_do, d.b_pne_zloze, d.b_pne_poza, d.i_ile_zalacz, d.t_autor, w.t_teren_id, p.t_mie_name, p.t_gmi_name, p.t_pow_name, p.t_woj_name, p.order_id FROM team_" + str(dlg.team_i) + ".wyrobiska AS w INNER JOIN team_" + str(dlg.team_i) + ".wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_" + str(dlg.team_i) + ".wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE w.wyr_id = '" + str(self.wyr) + "' AND p.pow_grp = '" + str(dlg.powiat_i) + "';"
        if db:
            res = db.query_sel(sql, False)
            if not res:
                print(f"Nie udało się wczytać danych wyrobiska: {self.wyr}")
                return None
            else:
                return res

    def wn_update(self):
        """Zwraca dane punktu WN_PNE."""
        db = PgConn()
        sql = "SELECT e.id_arkusz, e.kopalina, e.wyrobisko, e.zawodn, e.eksploat, e.wyp_odpady, e.nadkl_min, e.nadkl_max, e.nadkl_sr, e.miazsz_min, e.miazsz_max, e.dlug_max, e.szer_max, e.wys_min, e.wys_max, e.data_kontrol, e.uwagi, (SELECT COUNT(*) FROM external.wn_pne_pow AS p WHERE e.id_arkusz = p.id_arkusz AND p.b_active = true) AS i_pow_cnt, t.t_notatki FROM external.wn_pne AS e INNER JOIN team_" + str(dlg.team_i) + ".wn_pne AS t USING(id_arkusz) WHERE id_arkusz = '" + str(self.wn) + "';"
        if db:
            res = db.query_sel(sql, False)
            if not res:
                print(f"Nie udało się wczytać danych punktu WN_PNE: {self.wn}")
                return None
            else:
                return res

    def wn_pow_update(self):
        """Zwraca dane o powiatach punktu WN_PNE."""
        db = PgConn()
        sql = "SELECT pow_id, t_pow_name, b_active FROM external.wn_pne_pow WHERE id_arkusz = '" + str(self.wn) + "';"
        if db:
            res = db.query_sel(sql, True)
            if not res:
                print(f"Nie udało się wczytać danych punktu WN_PNE: {self.wn}")
                return None
            else:
                return res

    def set_object_from_input(self, _id, _obj):
        """Próba zmiany aktualnej flagi, wyrobiska, parkingu lub WN_PNE po wpisaniu go w idbox'ie."""
        if _obj == "flag":
            obj = "self.flag"
            ids = self.flag_ids
            id_box = "dlg.flag_panel.id_spinbox.id"
            is_int = True
        elif _obj == "parking":
            obj = "self.parking"
            ids = self.parking_ids
            id_box = "dlg.parking_panel.id_box.id"
            is_int = True
        elif _obj == "wyr":
            obj = "self.wyr"
            ids = self.wyr_ids
            id_box = "dlg.wyr_panel.id_box.id"
            is_int = True
        elif _obj == "order":
            self.set_wyr_id(_id)
            return
        elif _obj == "wn":
            obj = "self.wn"
            ids = self.wn_ids
            id_box = "dlg.wn_panel.id_box.id"
            is_int = False
        else:
            return
        if is_int:
            _id = int(_id)
        if _id in ids:
            exec(f"{obj} = {_id}") if is_int else exec(f"{obj} = '{_id}'")  # Zmiana aktualnego obiektu
            self.pan_to_object(_obj)
        else:
            exec(id_box + ' = ' + obj)

    def set_order_id(self):
        """Ustawia wartość order_box'a po zmianie wyrobiska."""
        for ord in self.order_ids:
            if ord[1] == self.wyr:
                self.order = ord[0]
                return

    def set_wyr_id(self, _order):
        """Zmienia wyrobisko po zmianie order_id w box'ie"""
        for ord in self.order_ids:
            if ord[0] == _order:
                self.wyr = ord[1]
                self.pan_to_object("wyr")
                return
        self.order = self.order

    def list_position_check(self, _obj):
        """Sprawdza pozycję flagi, wyrobiska, parking lub punktu WN_PNE na liście."""
        if _obj == "flag":
            obj = "self.flag"
            val = self.flag
            ids = self.flag_ids
            id_box = dlg.flag_panel.id_spinbox
        elif _obj == "parking":
            obj = "self.parking"
            val = self.parking
            ids = self.parking_ids
            id_box = dlg.parking_panel.id_box
        elif _obj == "wyr":
            obj = "self.wyr"
            val = self.wyr
            ids = self.wyr_ids
            id_box = dlg.wyr_panel.id_box
        elif _obj == "order":
            obj = "self.order"
            val = self.order
            ids = [i[0] for i in self.order_ids]
            id_box = dlg.wyr_panel.order_box
        elif _obj == "wn":
            obj = "self.wn"
            val = self.wn
            ids = self.wn_ids
            id_box = dlg.wn_panel.id_box
        else:
            return False
        if not ids or not val:
            return False
        obj_cnt = len(ids)
        try:
            cur_id_idx = ids.index(val)  # Pozycja na liście aktualnego obiektu
        except Exception as err:
            print(f"list_position_check: {err}")
            return False
        if cur_id_idx == 0:  # Pierwsza pozycja na liście
            id_box.prev_btn.setEnabled(False)
        else:
            id_box.prev_btn.setEnabled(True)
        if cur_id_idx == obj_cnt - 1:  # Ostatnia pozycja na liście
            id_box.next_btn.setEnabled(False)
        else:
            id_box.next_btn.setEnabled(True)
        return True

    def pan_to_object(self, _obj):
        """Centruje widok mapy na wybrany obiekt."""
        if _obj == "flag":
            if self.flag_data[1]:
                point_lyr = dlg.proj.mapLayersByName("flagi_z_teren")[0]
            else:
                point_lyr = dlg.proj.mapLayersByName("flagi_bez_teren")[0]
            feats = point_lyr.getFeatures(f'"id" = {self.flag}')
        elif _obj == "parking":
            if self.parking_data[1]:
                point_lyr = dlg.proj.mapLayersByName("parking_odwiedzone")[0]
            else:
                point_lyr = dlg.proj.mapLayersByName("parking_planowane")[0]
            feats = point_lyr.getFeatures(f'"id" = {self.parking}')
        elif _obj == "wyr":
            point_lyr = dlg.proj.mapLayersByName("wyr_point")[0]
            feats = point_lyr.getFeatures(f'"wyr_id" = {self.wyr}')
        elif _obj == "wn":
            point_lyr = dlg.proj.mapLayersByName("wn_pne")[0]
            feats = point_lyr.getFeatures(QgsFeatureRequest(QgsExpression('"id_arkusz"=' + "'" + str(self.wn) + "'")))
        try:
            feat = list(feats)[0]
        except Exception as err:
            print(f"pan: {err}")
            return
        point = feat.geometry()
        self.canvas.zoomToFeatureExtent(point.boundingBox())


class MapToolManager:
    """Menedżer maptool'ów."""
    def __init__(self, dlg, canvas):
        self.maptool = None  # Instancja klasy maptool'a
        self.mt_name = None  # Nazwa maptool'a
        self.params = {}  # Słownik z parametrami maptool'a
        self.dlg = dlg  # Referencja do wtyczki
        self.canvas = canvas  # Referencja do mapy
        self.old_button = None
        self.feat_backup = None
        self.canvas.mapToolSet.connect(self.maptool_change)
        self.tool_kinds = (MultiMapTool, IdentMapTool, PointPickerMapTool, PointDrawMapTool, LineDrawMapTool, PolyDrawMapTool, LineEditMapTool, PolyEditMapTool, LineContinueMapTool, RulerMapTool)
        self.maptools = [
            # {"name" : "edit_poly", "class" : PolyEditMapTool, "lyr" : ["flagi_z_teren", "flagi_bez_teren", "wn_pne", "wyrobiska"], "fn" : obj_sel},
            {"name" : "multi_tool", "class" : MultiMapTool, "button" : self.dlg.side_dock.toolboxes["tb_multi_tool"].widgets["btn_multi_tool"],"fn" : obj_sel},
            {"name" : "vn_sel", "class" : IdentMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_sel"], "lyr" : ["vn_user"], "fn" : vn_change},
            {"name" : "vn_powsel", "class" : IdentMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_powsel"], "lyr" : ["powiaty"], "fn" : vn_powsel},
            {"name" : "vn_polysel", "class" : PolyDrawMapTool, "button" : self.dlg.p_vn.widgets["btn_vn_polysel"], "fn" : vn_polysel, "extra" : [(0, 0, 255, 128), (0, 0, 255, 80)]},
            {"name" : "flt_add", "class" : PointDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_flag_fchk"], "fn" : flag_add, "extra" : ['true']},
            {"name" : "flf_add", "class" : PointDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_flag_nfchk"], "fn" : flag_add, "extra" : ['false']},
            {"name" : "flag_move", "class" : PointDrawMapTool, "button" : self.dlg.flag_panel.flag_tools.flag_move, "fn" : flag_move, "extra" : []},
            {"name" : "wyr_add_poly", "class" : PolyDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_wyr_add_poly"], "fn" : wyr_add_poly, "extra" : [(0, 255, 0, 128), (0, 255, 0, 80)]},
            {"name" : "wyr_edit", "class" : PolyEditMapTool, "button" : self.dlg.wyr_panel.wyr_edit, "lyr" : ["wyr_poly"], "fn" : wyr_poly_change, "extra" : ["wyr_id"]},
            {"name" : "wn_pick", "class" : PointPickerMapTool, "button" : self.dlg.wyr_panel.wn_picker.wn_picker_empty, "lyr" : ["wn_pne"], "fn" : wn_pick, "extra" : [["wn_pne"]]},
            {"name" : "parking_add", "class" : PointDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_parking"], "fn" : parking_add, "extra" : []},
            {"name" : "parking_move", "class" : PointDrawMapTool, "button" : self.dlg.parking_panel.parking_tools.parking_move, "fn" : parking_move, "extra" : []},
            {"name" : "marsz_add", "class" : LineDrawMapTool, "button" : self.dlg.side_dock.toolboxes["tb_add_object"].widgets["btn_marsz"], "fn" : marsz_add, "extra" : [[255, 255, 0, 255],["marszruty", "parking_planowane", "parking_odwiedzone"]]},
            {"name" : "marsz_edit", "class" : LineEditMapTool, "button" : self.dlg.marsz_panel.marsz_edit, "lyr" : ["marszruty"], "fn" : marsz_line_change, "extra" : ["marsz_id",["marszruty", "parking_planowane", "parking_odwiedzone"]]},
            {"name" : "marsz_continue", "class" : LineContinueMapTool, "button" : self.dlg.marsz_panel.marsz_continue, "lyr" : ["marszruty"], "fn" : marsz_line_continue, "extra" : ["marsz_id"]},
            {"name" : "dlug_min", "class" : RulerMapTool, "button" : self.dlg.wyr_panel.widgets["txt2_dlug_1"].valbox_1.r_widget, "lyr" : ["wyr_poly"], "fn" : ruler_meas},
            {"name" : "dlug_max", "class" : RulerMapTool, "button" : self.dlg.wyr_panel.widgets["txt2_dlug_1"].valbox_2.r_widget, "lyr" : ["wyr_poly"], "fn" : ruler_meas},
            {"name" : "szer_min", "class" : RulerMapTool, "button" : self.dlg.wyr_panel.widgets["txt2_szer_1"].valbox_1.r_widget, "lyr" : ["wyr_poly"], "fn" : ruler_meas},
            {"name" : "szer_max", "class" : RulerMapTool, "button" : self.dlg.wyr_panel.widgets["txt2_szer_1"].valbox_2.r_widget, "lyr" : ["wyr_poly"], "fn" : ruler_meas}
        ]

    def maptool_change(self, new_tool, old_tool):
        if not new_tool and not old_tool:
            # Jeśli wyłączany jest maptool o klasie QgsMapToolIdentify,
            # event jest puszczany dwukrotnie (pierwszy raz z wartościami None, None)
            return
        try:
            dlg.marsz_panel.setVisible(False)
        except:
            pass
        if not isinstance(new_tool, (self.tool_kinds)) and self.mt_name:
            # Reset ustawień MapToolManager'a, jeśli został wybrany maptool spoza wtyczki
            self.maptool = None
            self.mt_name = None
            self.params = {}
        if self.old_button:
            try:
                self.old_button.setChecked(False)
            except:
                pass
        try:  # Maptool może nie mieć atrybutu '.button()'
            self.old_button = new_tool.button()
        except:
            self.old_button = None

    def init(self, maptool, extra=None):
        """Zainicjowanie zmiany maptool'a."""
        if maptool == "multi_tool" and self.mt_name == "multi_tool":  # Zablokowanie próby wyłączenia multi_tool'a
            self.dlg.side_dock.toolboxes["tb_multi_tool"].widgets["btn_multi_tool"].setChecked(True)
            return
        if not self.mt_name:  # Nie ma obecnie uruchomionego maptool'a
            self.tool_on(maptool, extra)  # Włączenie maptool'a
        else:
            mt_old = self.mt_name
            if mt_old != maptool:  # Inny maptool był włączony
                self.tool_on(maptool, extra)  # Włączenie nowego maptool'a
            else:
                self.tool_on("multi_tool")

    def tool_on(self, maptool, extra=None):
        """Włączenie maptool'a."""
        self.params = self.dict_name(maptool)  # Wczytanie parametrów maptool'a
        if "lyr" in self.params:
            lyr = lyr_ref(self.params["lyr"])
        if self.params["class"] == MultiMapTool:
            self.maptool = self.params["class"](self.canvas, self.params["button"])
            self.maptool.identified.connect(self.params["fn"])
        elif self.params["class"] == IdentMapTool:
            self.maptool = self.params["class"](self.canvas, lyr, self.params["button"])
            self.maptool.identified.connect(self.params["fn"])
        elif self.params["class"] == PointPickerMapTool:
            self.maptool = self.params["class"](self.canvas, lyr, self.params["button"], self.params["extra"][0])
            self.maptool.picked.connect(self.params["fn"])
        elif self.params["class"] == PolyEditMapTool:
            geom = self.get_lyr_geom(lyr[0], self.params["extra"])
            self.poly_to_layers(geom)
            self.maptool = self.params["class"](self.canvas, lyr[0], self.params["button"])
            self.maptool.ending.connect(self.params["fn"])
        elif self.params["class"] == LineEditMapTool:
            geom = self.get_lyr_geom(lyr[0], self.params["extra"])
            self.line_to_layers(geom)
            self.maptool = self.params["class"](self.canvas, lyr[0], self.params["button"], dlg.obj.marsz, self.params["extra"][1])
            self.maptool.ending.connect(self.params["fn"])
            dlg.obj.marsz = None
        elif self.params["class"] == LineContinueMapTool:
            geom = self.get_lyr_geom(lyr[0], self.params["extra"])
            self.line_to_layers(geom)
            self.maptool = self.params["class"](self.canvas, lyr[0], self.params["button"], dlg.obj.marsz)
            self.maptool.ending.connect(self.params["fn"])
            dlg.obj.marsz = None
        elif self.params["class"] == PointDrawMapTool:
            self.maptool = self.params["class"](self.canvas, self.params["button"], self.params["extra"])
            self.maptool.drawn.connect(self.params["fn"])
        elif self.params["class"] == LineDrawMapTool:
            if extra:
                self.maptool = self.params["class"](self.canvas, self.params["button"], self.params["extra"], extra)
            else:
                self.maptool = self.params["class"](self.canvas, self.params["button"], self.params["extra"], None)
            self.maptool.drawn.connect(self.params["fn"])
        elif self.params["class"] == RulerMapTool:
            self.maptool = self.params["class"](self.canvas, self.params["lyr"], self.params["button"])
            self.maptool.measured.connect(self.params["fn"])
        elif self.params["class"] == PolyDrawMapTool:
            self.maptool = self.params["class"](self.canvas, self.params["button"], self.params["extra"])
            self.maptool.drawn.connect(self.params["fn"])
        self.canvas.setMapTool(self.maptool)
        self.mt_name = self.params["name"]

    def dict_name(self, maptool):
        """Wyszukuje na liście wybrany toolmap na podstawie nazwy i zwraca słownik z jego parametrami."""
        for tool in self.maptools:
            if tool["name"] == maptool:
                return tool

    def get_lyr_geom(self, lyr, extra):
        """Zwraca geometrię aktywnego obiektu z podanej warstwy."""
        if extra[0] == "wyr_id":
            obj_id = dlg.obj.wyr
        elif extra[0] == "marsz_id":
            obj_id = dlg.obj.marsz
        feats = lyr.getFeatures(f'"{extra[0]}" = {obj_id}')
        try:
            feat = list(feats)[0]
        except Exception as err:
            print(f"{err}")
            return None
        if isinstance(feat, QgsFeature):
            geom = self.feat_caching(lyr, feat)
            if isinstance(geom, QgsGeometry):
                return geom
            else:
                return None
        else:
            return None

    def feat_caching(self, lyr, feat):
        """Przenosi podaną geometrię do zmiennej backup'owej i czyści ją z warstwy źródłowej."""
        self.feat_backup = feat
        geom = self.feat_backup.geometry()
        with edit(lyr):
            feat.clearGeometry()
            try:
                lyr.updateFeature(feat)
            except Exception as err:
                print(err)
                self.feat_backup = None
                return None
        return geom

    def poly_to_layers(self, geom):
        """Rozkłada geometrię poligonalną na części pierwsze i przenosi je do warstw tymczasowych."""
        edit_lyr = dlg.proj.mapLayersByName("edit_poly")[0]
        back_lyr = dlg.proj.mapLayersByName("backup_poly")[0]
        lyrs = [edit_lyr, back_lyr]
        for lyr in lyrs:
            dp = lyr.dataProvider()
            dp.truncate()
            if not geom:
                return
            pg = 0  # Numer poligonu
            with edit(lyr):  # Ekstrakcja poligonów
                for poly in geom.asMultiPolygon():
                    feat = QgsFeature(lyr.fields())
                    feat.setAttribute("part", pg)
                    feat.setGeometry(QgsGeometry.fromPolygonXY(poly))
                    dp.addFeature(feat)
                    # lyr.updateExtents()
                    pg += 1

    def line_to_layers(self, geom):
        """Przenosi geometrię liniową do warstwy tymczasowej."""
        if not geom:
            return
        edit_lyr = dlg.proj.mapLayersByName("edit_line")[0]
        back_lyr = dlg.proj.mapLayersByName("backup_line")[0]
        lyrs = [edit_lyr, back_lyr]
        for lyr in lyrs:
            dp = lyr.dataProvider()
            dp.truncate()
            with edit(lyr):
                feat = QgsFeature(lyr.fields())
                feat.setGeometry(geom)
                dp.addFeature(feat)


class DummyMapTool(QgsMapTool):
    """Pusty maptool przekazujący informacje o przycisku innego maptool'a."""
    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)

    def button(self):
        return self._button


class LineContinueMapTool(QgsMapTool):
    """Maptool do wyboru początku geometrii liniowej, której rysowanie będzie kontynuowane."""
    cursor_changed = pyqtSignal(str)
    ending = pyqtSignal(QgsVectorLayer, object, int, object, bool, bool)

    def __init__(self, canvas, layer, button, _id):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.layer = layer
        self.id = _id
        self.geom = None
        self.init_extent = self.canvas.extent()
        self.dragging = False
        self.accepted = False
        self.canceled = False
        self.lrb = None
        self.vrb = None
        self.node_hover = None
        self.start_node = None
        self.end_node = None
        self.node_presel = None
        self.node_idx = -1
        self.prev_node = None
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "open_hand"
        self.edit_layer = dlg.proj.mapLayersByName("edit_line")[0]
        self.backup_layer = dlg.proj.mapLayersByName("backup_line")[0]
        self.snap_settings()
        self.rbs_create()
        self.rbs_populate()
        self.zoom_to_geom()  # Przybliżenie widoku mapy do geometrii

    def zoom_to_geom(self):
        """Przybliżenie widoku mapy do granic geometrii."""
        # Określenie zasięgu warstwy:
        box = None
        for feat in self.edit_layer.getFeatures():
            if not box:
                box = feat.geometry().boundingBox()
            else:
                box.combineExtentWith(feat.geometry().boundingBox())
        # Określenie nowego zasięgu widoku mapy:
        w_off = box.width() * 0.4
        h_off = box.height() * 0.4
        ext = QgsRectangle(box.xMinimum() - w_off,
                            box.yMinimum() - h_off,
                            box.xMaximum() + w_off,
                            box.yMaximum() + h_off
                            )
        self.canvas.setExtent(ext)

    def snap_settings(self):
        """Zmienia globalne ustawienia snappingu."""
        s = QgsSettings()
        s.setValue('/qgis/digitizing/default_snap_type', 'VertexAndSegment')
        s.setValue('/qgis/digitizing/search_radius_vertex_edit', 12)
        s.setValue('/qgis/digitizing/search_radius_vertex_edit_unit', 'Pixels')

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor],
                    ["arrow", Qt.CrossCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        self.vrb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.vrb.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.vrb.setColor(QColor(0, 0, 0, 255))
        self.vrb.setFillColor(QColor(255, 255, 0, 128))
        self.vrb.setIconSize(10)
        self.vrb.setVisible(False)

        self.lrb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.lrb.setWidth(3)
        self.lrb.setColor(QColor(255, 255, 0, 64))
        self.lrb.setFillColor(QColor(255, 255, 0, 28))
        self.lrb.setVisible(True)

        self.node_hover = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_hover.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_hover.setColor(QColor(0, 0, 0, 255))
        self.node_hover.setFillColor(QColor(255, 255, 0, 255))
        self.node_hover.setIconSize(14)
        self.node_hover.addPoint(QgsPointXY(0, 0), False)
        self.node_hover.setVisible(False)

    def rbs_populate(self):
        """Załadowanie linii i punktów do rubberband'ów."""
        feats = self.edit_layer.getFeatures()
        for feat in feats:
            geom = feat.geometry().asPolyline()
            self.vrb.addPoint(geom[0])
            self.vrb.addPoint(geom[-1])
            self.start_node = geom[0]
            self.end_node = geom[-1]
            for part in geom:
                self.lrb.addPoint(part)
            break

    def snap_to_layer(self, event, lyr):
        """Zwraca wyniki przyciągania do wierzchołków i krawędzi."""
        self.canvas.snappingUtils().setCurrentLayer(lyr)
        v = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Vertex)
        return v

    def canvasMoveEvent(self, event):
        map_point = self.toMapCoordinates(event.pos())
        if event.buttons() == Qt.LeftButton:
            # Panning mapy:
            if not self.dragging:
                self.dragging = True
                self.cursor = "closed_hand"
            self.canvas.panAction(event)
        elif event.button() == Qt.NoButton:
            v = self.snap_to_layer(event, self.edit_layer)
            if v.type() == 1:  # Kursor nad punktem marszruty
                if v.point() == self.start_node or v.point() == self.end_node:
                    self.cursor = "arrow"
                    self.node_hover.movePoint(v.point(), 0)
                    self.node_hover.setVisible(True)
                    self.node_presel = v.point()
            else:
                self.cursor = "open_hand"
                self.node_presel = None
                self.node_hover.setVisible(False)

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.dragging:
                if self.node_presel:
                    self.accepted = True
                    self.accept_changes()  # Zatwierdzenie wyboru końcówki linii
            else:
                # Zakończenie panningu mapy:
                self.cursor = "open_hand"
                self.canvas.panActionEnd(event.pos())
                self.dragging = False

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.canceled = True
            self.accept_changes(cancel=True)

    def geom_update(self):
        """Aktualizacja geometrii liniowej po wybraniu początkowego wierzchołka."""
        if not self.lrb:  # Nie ma geometrii
            return None
        if self.node_presel == self.end_node:
            return self.lrb.asGeometry()
        elif self.node_presel == self.start_node:
            geom = self.lrb.asGeometry()
            nodes = geom.asPolyline()
            nodes.reverse()
            rev_geom = QgsGeometry.fromPolylineXY(nodes)
            return rev_geom
        else:
            return None

    def geom_from_backup(self):
        """Zwraca geometrię z warstwy 'backup_line'."""
        feat_cnt = self.backup_layer.featureCount()
        if feat_cnt == 0:
            return None
        else:
            feats = self.backup_layer.getFeatures()
            for feat in feats:
                geom = feat.geometry()
                return geom

    def rbs_clear(self):
        """Wyczyszczenie zawartości i usunięcie rubberband'ów."""
        if self.lrb:
            self.canvas.scene().removeItem(self.lrb)
            self.lrb = None
        if self.vrb:
            self.canvas.scene().removeItem(self.vrb)
            self.vbr = None
        if self.node_hover:
            self.canvas.scene().removeItem(self.node_hover)
            self.node_hover = None
        self.canvas.refresh()

    def accept_changes(self, cancel=False, deactivated=False):
        """Zakończenie edycji geometrii i zaakceptowanie wprowadzonych zmian, albo przywrócenie stanu pierwotnego (cancel=True)."""
        if not cancel:
            self.geom = self.geom_update()
        if cancel or not self.geom:
            self.geom = self.geom_from_backup()
            self.canvas.setExtent(self.init_extent)
        self.rbs_clear()
        self.edit_layer.dataProvider().truncate()
        self.edit_layer.triggerRepaint()
        self.backup_layer.dataProvider().truncate()
        self.backup_layer.triggerRepaint()
        self.ending.emit(self.layer, self.geom, self.id, self.init_extent, cancel, deactivated)

    def deactivate(self):
        """Zakończenie działania maptool'a."""
        super().deactivate()
        if not self.accepted:
            self.accept_changes(deactivated=True)


class LineEditMapTool(QgsMapTool):
    """Maptool do edytowania geometrii liniowej."""
    cursor_changed = pyqtSignal(str)
    node_selected = pyqtSignal(bool)
    ending = pyqtSignal(QgsVectorLayer, object, int, bool)

    def __init__(self, canvas, layer, button, _id, extra):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.layer = layer
        self.lyrs = extra
        self.id = _id
        self.dragging = False
        self.moving = False
        self.snapping = False
        self.geom = None
        self.init_extent = self.canvas.extent()
        self.lrb = None
        self.vrb = None
        self.line_helper = None
        self.node_hover = None
        self.node_selector = None
        self.edge_hover = None
        self.start_point = None
        self.snap_point = None
        self.node_presel = None
        self.node_sel = False
        self.node_idx = -1
        self.prev_node = None
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "open_hand"
        self.node_selected.connect(self.node_sel_change)
        self.edit_layer = dlg.proj.mapLayersByName("edit_line")[0]
        self.backup_layer = dlg.proj.mapLayersByName("backup_line")[0]
        self.snap_settings()
        self.rbs_create()
        self.rbs_populate()
        self.zoom_to_geom()  # Przybliżenie widoku mapy do geometrii

    def zoom_to_geom(self):
        """Przybliżenie widoku mapy do granic geometrii."""
        # Określenie zasięgu warstwy:
        box = None
        for feat in self.edit_layer.getFeatures():
            if not box:
                box = feat.geometry().boundingBox()
            else:
                box.combineExtentWith(feat.geometry().boundingBox())
        # Określenie nowego zasięgu widoku mapy:
        w_off = box.width() * 0.4
        h_off = box.height() * 0.4
        ext = QgsRectangle(box.xMinimum() - w_off,
                            box.yMinimum() - h_off,
                            box.xMaximum() + w_off,
                            box.yMaximum() + h_off
                            )
        self.canvas.setExtent(ext)

    def snap_settings(self):
        """Zmienia globalne ustawienia snappingu."""
        s = QgsSettings()
        s.setValue('/qgis/digitizing/default_snap_type', 'VertexAndSegment')
        s.setValue('/qgis/digitizing/search_radius_vertex_edit', 12)
        s.setValue('/qgis/digitizing/search_radius_vertex_edit_unit', 'Pixels')

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)
        if attr == "node_sel":
            self.node_selected.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor],
                    ["cross", Qt.CrossCursor],
                    ["move", Qt.SizeAllCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def node_sel_change(self, _bool):
        """Zmiana zaznaczonego node'a."""
        if not self.node_selector:
            return
        if _bool:
            self.node_idx = self.get_node_index()
            self.node_selector.movePoint(self.node_presel, 0)
            self.node_selector.setVisible(True)
        else:
            self.node_idx = -1
            self.node_selector.setVisible(False)

    def get_node_index(self):
        """Zwraca index punktu znajdującego się pod node_selector'em."""
        rb_geom = self.vrb.asGeometry()
        i = 0
        for part in rb_geom.constParts():
            p_geom = QgsPointXY(part.x(), part.y())
            if self.node_presel == p_geom:
                return i
            i += 1
        return -1

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        self.vrb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.vrb.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.vrb.setColor(QColor(255, 255, 0, 255))
        self.vrb.setFillColor(QColor(255, 255, 0, 255))
        self.vrb.setIconSize(8)
        self.vrb.setVisible(False)

        self.lrb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.lrb.setWidth(2)
        self.lrb.setColor(QColor(255, 255, 0, 255))
        self.lrb.setFillColor(QColor(255, 255, 0, 28))
        self.lrb.setVisible(True)

        self.line_helper = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.line_helper.setWidth(2)
        self.line_helper.setColor(QColor(255, 255, 0, 255))
        self.line_helper.setLineStyle(Qt.DotLine)
        self.line_helper.setVisible(False)

        self.edge_hover = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.edge_hover.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.edge_hover.setColor(QColor(0, 0, 0, 255))
        self.edge_hover.setFillColor(QColor(255, 255, 0, 255))
        self.edge_hover.setIconSize(6)
        self.edge_hover.addPoint(QgsPointXY(0, 0), False)
        self.edge_hover.setVisible(False)

        self.node_hover = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_hover.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_hover.setColor(QColor(0, 0, 0, 255))
        self.node_hover.setFillColor(QColor(255, 255, 0, 255))
        self.node_hover.setIconSize(12)
        self.node_hover.addPoint(QgsPointXY(0, 0), False)
        self.node_hover.setVisible(False)

        self.node_selector = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_selector.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_selector.setColor(QColor(0, 0, 0, 255))
        self.node_selector.setFillColor(QColor(255, 255, 0, 255))
        self.node_selector.setIconSize(14)
        self.node_selector.addPoint(QgsPointXY(0, 0), False)
        self.node_selector.setVisible(False)

    def rbs_populate(self):
        """Załadowanie linii i punktów do rubberband'ów."""
        feats = self.edit_layer.getFeatures()
        for feat in feats:
            geom = feat.geometry().asPolyline()
            for part in geom:
                self.lrb.addPoint(part)
                self.vrb.addPoint(part)
            break

    def snap_to_layer(self, event, lyr):
        """Zwraca wyniki przyciągania do wierzchołków i krawędzi."""
        self.canvas.snappingUtils().setCurrentLayer(lyr)
        v = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Vertex)
        e = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Edge)
        return v, e

    @threading_func
    def find_nearest_feature(self, pos):
        """Zwraca najbliższy od kursora obiekt na wybranych warstwach."""
        pos = self.toLayerCoordinates(self.layer, pos)
        scale = iface.mapCanvas().scale()
        tolerance = scale / 250
        search_rect = QgsRectangle(pos.x() - tolerance,
                                  pos.y() - tolerance,
                                  pos.x() + tolerance,
                                  pos.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(search_rect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        lyrs = self.get_lyrs()
        if self.lyrs:
            for lyr in lyrs:
                for feat in lyr.getFeatures(request):
                    return lyr
        else:
            return None

    def get_lyrs(self):
        """Zwraca listę włączonych warstw z obiektami."""
        lyrs = []
        for _list in dlg.lyr.lyr_vis:
            if _list[1] and _list[0] in self.lyrs:
                lyr = dlg.proj.mapLayersByName(_list[0])[0]
                lyrs.append(lyr)
        return lyrs

    def canvasMoveEvent(self, event):
        map_point = self.toMapCoordinates(event.pos())
        snap_type = None
        if event.buttons() == Qt.LeftButton:
            if self.node_presel:
                # Przesunięcie wierzchołka:
                if not self.moving:
                    self.node_sel = True
                    self.dragging = False
                    self.moving = True
                    self.cursor = "move"
                    self.line_create()
                th = self.find_nearest_feature(event.pos())
                result = th.get()
                snap_type = None
                if result:
                    v, e = self.snap_to_layer(event, result)
                    snap_type = v.type() + e.type()
                    if snap_type == 1 or snap_type == 3:  # Kursor nad vertexem marszruty albo parkingu
                        self.snap_point = v.point()
                        self.snapping = True
                    elif snap_type == 2:  # Kursor nad linią marszruty
                        self.snap_point = e.point()
                        self.snapping = True
                    else:
                        self.snap_point = map_point
                        self.snapping = False
                else:
                    self.snap_point = map_point
                    self.snapping = False
                self.node_selector.movePoint(self.snap_point)
                self.line_helper.movePoint(1, self.snap_point)
            elif self.edge_hover.isVisible() and not self.moving:
                # Szybkie dodanie wierzchołka:
                self.node_add(self.snap_point)
                self.geom_refresh()
                self.node_presel = self.snap_point
                self.selector_update()
            else:
                # Panning mapy:
                if not self.dragging:
                    self.dragging = True
                    self.cursor = "closed_hand"
                self.canvas.panAction(event)
        elif event.button() == Qt.NoButton and not self.dragging:
            v, e = self.snap_to_layer(event, self.edit_layer)
            snap_type = v.type() + e.type()
            if snap_type == 2:  # Kursor nad linią marszruty
                self.cursor = "cross"
                self.edge_hover.movePoint(e.point(), 0)
                self.edge_hover.setVisible(True)
                self.node_hover.setVisible(False)
                self.node_presel = None
                self.snap_point = e.point()
                if self.prev_node != e.edgePoints()[0]:
                    self.prev_node = e.edgePoints()[0]
            elif snap_type == 3:  # Kursor nad wierzchołkiem marszruty
                self.cursor = "cross"
                self.node_hover.movePoint(v.point(), 0)
                self.node_hover.setVisible(True)
                self.edge_hover.setVisible(False)
                self.node_presel = v.point()
            else:
                self.cursor = "open_hand"
                self.node_presel = None
                self.node_hover.setVisible(False)
                self.edge_hover.setVisible(False)

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = self.toMapCoordinates(event.pos())

    def canvasDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self.dragging:
            if self.edge_hover.isVisible():
                # Dodanie nowego wierzchołka:
                geom = self.edge_hover.asGeometry()
                p_list = list(geom.vertices())
                p_last = len(p_list) - 1
                self.node_add(p_list[p_last])
                self.geom_refresh()

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.moving and not self.dragging:
                if self.node_presel:
                    self.node_sel = True  # Zaznaczenie wierzchołka
                else:
                    self.node_sel = False  # Odznaczenie wierzchołka
            elif self.moving:
                # Przemieszczenie wierzchołka:
                map_point = self.snap_point if self.snapping else self.toMapCoordinates(event.pos())
                self.lrb.movePoint(self.node_idx, map_point)
                self.snapping = False
                self.geom_refresh()
                self.selector_update()
                self.moving = False
            elif self.dragging:
                # Zakończenie panningu mapy:
                self.cursor = "open_hand"
                self.canvas.panActionEnd(event.pos())
                self.dragging = False
        if event.button() == Qt.RightButton:
            self.accept_changes()

    def keyReleaseEvent(self, event):
        if self.node_sel and not self.moving and event.key() == Qt.Key_Delete:
            # Skasowanie wierzchołka:
            self.node_delete()
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept_changes()
        if event.key() == Qt.Key_Escape:
            if self.moving:
                self.moving = False
                self.geom_refresh()
                self.selector_update()
            else:
                self.accept_changes(cancel=True)

    def geom_refresh(self):
        """Aktualizacja warstwy edycji i rubberband'ów po zmianie geometrii."""
        self.geom = self.geom_update()  # Aktualizacja geometrii na warstwie
        self.rbs_clear()  # Skasowanie rubberband'ów
        self.rbs_create()  # Utworzenie nowych rubberband'ów
        self.rbs_populate()  # Załadowanie geometrii do rubberband'ów

    def selector_update(self):
        """Przywrócenie node_selector'a po ponownym wczytaniu rubberband'ów."""
        if self.node_idx < 0:
            return
        geom = self.vrb.asGeometry()
        node = list(geom.vertices())[self.node_idx]
        self.node_selector.movePoint(QgsPointXY(node.x(), node.y()))
        self.node_selector.setVisible(True)

    def node_add(self, point):
        """Utworzenie nowego wierzchołka na linii."""
        new_node = QgsPointXY(point.x(), point.y())
        rb = self.vrb
        geom = rb.asGeometry()
        p_list = list(geom.vertices())
        self.vrb.reset(QgsWkbTypes.PointGeometry)
        self.lrb.reset(QgsWkbTypes.LineGeometry)
        for i in range(len(p_list)):
            node = QgsPointXY(p_list[i].x(), p_list[i].y())
            if node == self.prev_node:
                self.vrb.addPoint(node)
                self.lrb.addPoint(node)
                self.vrb.addPoint(new_node)
                self.lrb.addPoint(new_node)
                self.node_idx = i + 1
            else:
                self.vrb.addPoint(node)
                self.lrb.addPoint(node)

    def node_delete(self):
        """Usuwa zaznaczony wierzchołek linii."""
        if self.node_idx < 0:
            print("brak zaznaczonego wierzchołka")
            return
        if self.vrb.numberOfVertices() > 2:
            self.vrb.removePoint(self.node_idx, True)
            self.lrb.removePoint(self.node_idx, True)
            if self.node_idx > self.vrb.numberOfVertices() - 1:
                self.node_idx = self.node_idx - 1
            self.geom_refresh()
            self.selector_update()

    def line_create(self):
        """Utworzenie i wyświetlenie linii pomocniczej przy przesuwaniu wierzchołka."""
        node = self.node_idx  # ID wybranego wierzchołka
        node_cnt = self.vrb.numberOfVertices() - 1  # Ilość wierzchołków w linii
        if node == 0:  # Zaznaczony jest pierwszy wierzchołek
            picked_nodes = [node + 1, node]
        elif node == node_cnt:  # Zaznaczony jest ostatni wierzchołek
            picked_nodes = [node - 1, node]
        else:
            picked_nodes = [node -1, node, node + 1]
        line_points = self.get_points_from_indexes(picked_nodes)
        self.line_helper.reset(QgsWkbTypes.LineGeometry)
        for p in line_points:
            self.line_helper.addPoint(p)
        self.line_helper.setVisible(True)

    def get_points_from_indexes(self, nodes):
        """Zwraca punkty linii na podstawie ich indeksów."""
        pts = []
        geom = self.vrb.asGeometry()
        p_list = list(geom.vertices())
        for node in nodes:
            pt = p_list[node]
            pts.append(QgsPointXY(pt.x(), pt.y()))
        return pts

    def geom_update(self):
        """Aktualizacja geometrii liniowej po jej zmianie."""
        self.edit_layer.dataProvider().truncate()
        if not self.lrb:  # Nie ma geometrii
            return None
        # Załadowanie aktualnej geometrii do warstwy edit_line:
        with edit(self.edit_layer):
            geom = self.lrb.asGeometry()
            feat = QgsFeature(self.edit_layer.fields())
            feat.setGeometry(geom)
            self.edit_layer.addFeature(feat)
        return geom

    def geom_from_backup(self):
        """Zwraca geometrię z warstwy 'backup_line'."""
        feat_cnt = self.backup_layer.featureCount()
        if feat_cnt == 0:
            return None
        else:
            feats = self.backup_layer.getFeatures()
            for feat in feats:
                geom = feat.geometry()
                return geom

    def rbs_clear(self):
        """Wyczyszczenie zawartości i usunięcie rubberband'ów."""
        if self.lrb:
            self.canvas.scene().removeItem(self.lrb)
            self.lrb = None
        if self.vrb:
            self.canvas.scene().removeItem(self.vrb)
            self.vbr = None
        if self.node_hover:
            self.canvas.scene().removeItem(self.node_hover)
            self.node_hover = None
        if self.edge_hover:
            self.canvas.scene().removeItem(self.edge_hover)
            self.edge_hover = None
        if self.line_helper:
            self.canvas.scene().removeItem(self.line_helper)
            self.line_helper = None
        if self.node_selector:
            self.canvas.scene().removeItem(self.node_selector)
            self.node_selector = None
        self.canvas.refresh()

    def accept_changes(self, cancel=False, deactivated=False):
        """Zakończenie edycji geometrii i zaakceptowanie wprowadzonych zmian, albo przywrócenie stanu pierwotnego (cancel=True)."""
        if cancel:
            self.geom = self.geom_from_backup()
        elif not cancel and not self.geom:
            self.geom = self.geom_update()
        self.rbs_clear()
        self.edit_layer.dataProvider().truncate()
        self.edit_layer.triggerRepaint()
        self.backup_layer.dataProvider().truncate()
        self.backup_layer.triggerRepaint()
        self.canvas.setExtent(self.init_extent)
        self.ending.emit(self.layer, self.geom, self.id, deactivated)

    def deactivate(self):
        """Zakończenie działania maptool'a."""
        super().deactivate()
        self.accept_changes(cancel=True, deactivated=True)


class PolyEditMapTool(QgsMapTool):
    """Maptool do edytowania poligonalnej geometrii wyrobiska."""
    mode_changed = pyqtSignal(str)
    cursor_changed = pyqtSignal(str)
    node_selected = pyqtSignal(bool)
    area_hover = pyqtSignal(int)
    valid_changed = pyqtSignal(bool)
    ending = pyqtSignal(QgsVectorLayer, object)

    def __init__(self, canvas, layer, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.layer = layer
        self.start_point = None
        self.dragging = False
        self.moving = False
        self.refreshing = False
        self.drawing = False
        self.interrupted = False
        self.move_void = False
        self.snap_void = False
        self.geom = None
        self.init_extent = self.canvas.extent()
        self.area_rbs = []
        self.vertex_rbs = []
        self.valid_checker = None
        self.node_valider = None
        self.area_valider = None
        self.line_helper = None
        self.node_hover = None
        self.node_selector = None
        self.edge_marker = None
        self.area_marker = None
        self.area_painter = None
        self.a_temp = -1
        self.area_idx = -1
        self.part_idx = -1
        self.node_presel = []
        self.node_sel = False
        self.node_idx = (-1, -1)
        self.prev_node = None
        self.change_is_valid = True
        self.valid_changed.connect(self.valid_change)
        self.flash = 0
        self.edit_layer = dlg.proj.mapLayersByName("edit_poly")[0]
        self.backup_layer = dlg.proj.mapLayersByName("backup_poly")[0]
        self.snap_settings()
        self.rbs_create()
        self.rbs_populate()
        self.mode_changed.connect(self.mode_change)
        self.mode = "edit"
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "open_hand"
        self.node_selected.connect(self.node_sel_change)
        self.area_hover.connect(self.area_hover_change)
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool"].clicked.connect(self.edit_clicked)
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_add"].clicked.connect(self.add_clicked)
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_sub"].clicked.connect(self.sub_clicked)
        dlg.bottom_dock.toolboxes["tb_edit_exit"].widgets["btn_accept"].clicked.connect(self.accept_changes)
        dlg.bottom_dock.toolboxes["tb_edit_exit"].widgets["btn_cancel"].clicked.connect(lambda: self.accept_changes(True))
        dlg.obj.edit_mode(True)  # Zmiana ui przy wejściu do trybu edycji geometrii wyrobiska
        self.zoom_to_geom()  # Przybliżenie widoku mapy do geometrii wyrobiska

    def zoom_to_geom(self):
        """Przybliżenie widoku mapy do granic wyrobiska."""
        # Sprawdzenie, czy na warstwie 'edit_poly' są poligony:
        feat_cnt = self.edit_layer.featureCount()
        if feat_cnt == 0:
            # Panning mapy do centroidu wyrobiska:
            point_lyr = dlg.proj.mapLayersByName("wyr_point")[0]
            feats = point_lyr.getFeatures(f'"wyr_id" = {dlg.obj.wyr}')
            try:
                feat = list(feats)[0]
            except Exception as err:
                print(f"maptools/zoom_to_geom: {err}")
                return
            point = feat.geometry()
            self.canvas.zoomToFeatureExtent(point.boundingBox())
            dlg.bottom_dock.toolboxes["tb_edit_exit"].widgets["btn_accept"].setEnabled(False)
            return
        # Określenie zasięgu warstwy:
        box = None
        for feat in self.edit_layer.getFeatures():
            if not box:
                box = feat.geometry().boundingBox()
            else:
                box.combineExtentWith(feat.geometry().boundingBox())
        # Określenie nowego zasięgu widoku mapy:
        w_off = box.width() * 0.4
        h_off = box.height() * 0.4
        ext = QgsRectangle(box.xMinimum() - w_off,
                            box.yMinimum() - h_off,
                            box.xMaximum() + w_off,
                            box.yMaximum() + h_off
                            )
        self.canvas.setExtent(ext)

    def snap_settings(self):
        """Zmienia globalne ustawienia snappingu."""
        s = QgsSettings()
        s.setValue('/qgis/digitizing/default_snap_type', 'VertexAndSegment')
        s.setValue('/qgis/digitizing/search_radius_vertex_edit', 12)
        s.setValue('/qgis/digitizing/search_radius_vertex_edit_unit', 'Pixels')

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)
        if attr == "mode":
            self.mode_changed.emit(val)
        if attr == "area_idx":
            self.area_hover.emit(val)
        if attr == "node_sel":
            self.node_selected.emit(val)
        if attr == "change_is_valid":
            self.valid_changed.emit(val)

    def mode_change(self, mode_name):
        """Zmiana trybu maptool'a."""
        modes = [
                ["edit", dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool"]],
                ["add", dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_add"]],
                ["sub", dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_sub"]]
                ]
        accept_btn = dlg.bottom_dock.toolboxes["tb_edit_exit"].widgets["btn_accept"]
        cancel_btn = dlg.bottom_dock.toolboxes["tb_edit_exit"].widgets["btn_cancel"]
        if self.area_painter:
            self.area_painter.reset(QgsWkbTypes.PolygonGeometry)
        else:
            self.area_painter = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            self.area_painter.setColor(QColor(0, 255, 0, 128))
            self.area_painter.setFillColor(QColor(0, 255, 0, 80))
            self.area_painter.setWidth(1)
            self.area_painter.setVisible(False)
        self.node_idx = (-1, -1)
        self.node_sel = False
        self.start_point = None
        for mode in modes:
            if mode[0] == mode_name and not mode[1].isChecked():
                mode[1].setChecked(True)
            elif mode[0] != mode_name:
                mode[1].setChecked(False)
            if mode_name == "add":
                self.area_painter.setColor(QColor(0, 255, 0, 128))
                self.area_painter.setFillColor(QColor(0, 255, 0, 80))
                accept_btn.setEnabled(False)
            elif mode_name == "sub":
                self.area_painter.setColor(QColor(255, 0, 0, 128))
                self.area_painter.setFillColor(QColor(255, 0, 0, 80))
                accept_btn.setEnabled(False)
            elif mode_name == "edit" and self.vertex_rbs:
                accept_btn.setEnabled(True)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["arrow", Qt.ArrowCursor],
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor],
                    ["cross", Qt.CrossCursor],
                    ["move", Qt.SizeAllCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def edit_clicked(self):
        """Kliknięcie na przycisk btn_edit_tool."""
        btn = dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool"]
        if btn.isChecked():
            self.mode = "edit"
        else:
            self.mode = "edit"

    def add_clicked(self):
        """Kliknięcie na przycisk btn_edit_tool_add."""
        btn = dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_add"]
        if btn.isChecked():
            self.mode = "add"
        else:
            self.mode = "edit"

    def sub_clicked(self):
        """Kliknięcie na przycisk btn_edit_tool_sub."""
        btn = dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_sub"]
        if btn.isChecked():
            self.mode = "sub"
        else:
            self.mode = "edit"

    def node_sel_change(self, _bool):
        """Zmiana zaznaczonego node'a."""
        if not self.node_selector:
            return
        if _bool:
            self.node_idx = self.get_node_index()
            self.node_selector.movePoint(self.node_presel[0], 0)
            self.node_selector.setVisible(True)
        else:
            self.node_idx = (-1, -1)
            self.node_selector.setVisible(False)
        self.area_hover_change(self.area_idx)

    def selector_update(self):
        """Przywrócenie node_selector'a po ponownym wczytaniu rubberband'ów."""
        if self.node_idx[0] < 0:
            return
        geom = self.vertex_rbs[self.node_idx[0]].asGeometry()
        node = list(geom.vertices())[self.node_idx[1]]
        self.node_selector.movePoint(QgsPointXY(node.x(), node.y()))
        self.node_selector.setVisible(True)

    def area_hover_change(self, part):
        """Zmiana podświetlenia poligonów."""
        if part < 0:
            self.area_marker.setVisible(False)
        else:
            self.area_marker.reset(QgsWkbTypes.PolygonGeometry)
            try:
                self.area_marker.addGeometry(self.area_rbs[part].asGeometry())
                self.area_marker.setVisible(True)
            except Exception as err:
                print(err)
        for i in range(len(self.vertex_rbs)):
            if self.node_idx[0] == i or self.area_idx == i:
                self.vertex_rbs[i].setVisible(True)
            else:
                self.vertex_rbs[i].setVisible(False)

    def valid_change(self, _bool):
        """Zmiana poprawności geometrii rubberband'a, w trakcie przemieszczania wierzchołka lub rysowania area_painter'a."""
        if self.mode == "edit":
            self.line_helper.setColor(QColor(255, 255, 0, 255)) if _bool else self.line_helper.setColor(QColor(255, 0, 0, 255))
            self.node_selector.setFillColor(QColor(255, 255, 0, 255)) if _bool else self.node_selector.setFillColor(QColor(255, 0, 0, 255))
        elif self.mode == "add":
            self.area_painter.setFillColor(QColor(0, 255, 0, 80)) if _bool else self.area_painter.setFillColor(QColor(0, 0, 0, 80))
        elif self.mode == "sub":
            self.area_painter.setFillColor(QColor(255, 0, 0, 80)) if _bool else self.area_painter.setFillColor(QColor(0, 0, 0, 80))

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        for i in range(self.edit_layer.featureCount()):
            _vrb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
            _vrb.setIcon(QgsRubberBand.ICON_CIRCLE)
            _vrb.setColor(QColor(255, 255, 0, 0))
            _vrb.setFillColor(QColor(255, 255, 0, 128))
            _vrb.setIconSize(10)
            _vrb.setVisible(False)
            self.vertex_rbs.append(_vrb)
            _arb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            _arb.setWidth(1)
            _arb.setColor(QColor(255, 255, 0, 255))
            _arb.setFillColor(QColor(255, 255, 0, 28))
            _arb.setVisible(True)
            self.area_rbs.append(_arb)

        self.valid_checker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.valid_checker.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.valid_checker.setColor(QColor(0, 0, 0, 0))
        self.valid_checker.setFillColor(QColor(0, 0, 0, 0))
        self.valid_checker.setIconSize(1)
        self.valid_checker.setVisible(False)

        self.line_helper = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.line_helper.setWidth(2)
        self.line_helper.setColor(QColor(255, 255, 0, 255))
        self.line_helper.setLineStyle(Qt.DotLine)
        self.line_helper.setVisible(False)

        self.area_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.area_marker.setWidth(2)
        self.area_marker.setColor(QColor(255, 255, 0, 255))
        self.area_marker.setFillColor(QColor(255, 255, 0, 0))
        self.area_marker.setVisible(False)

        self.edge_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.edge_marker.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.edge_marker.setColor(QColor(0, 0, 0, 255))
        self.edge_marker.setFillColor(QColor(255, 255, 0, 255))
        self.edge_marker.setIconSize(6)
        self.edge_marker.addPoint(QgsPointXY(0, 0), False)
        self.edge_marker.setVisible(False)

        self.node_hover = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_hover.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_hover.setColor(QColor(0, 0, 0, 255))
        self.node_hover.setFillColor(QColor(255, 255, 0, 128))
        self.node_hover.setIconSize(10)
        self.node_hover.addPoint(QgsPointXY(0, 0), False)
        self.node_hover.setVisible(False)

        self.node_selector = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_selector.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.node_selector.setColor(QColor(0, 0, 0, 255))
        self.node_selector.setFillColor(QColor(255, 255, 0, 255))
        self.node_selector.setIconSize(12)
        self.node_selector.addPoint(QgsPointXY(0, 0), False)
        self.node_selector.setVisible(False)

        if not self.area_painter:
            self.area_painter = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            self.area_painter.setColor(QColor(0, 255, 0, 128))
            self.area_painter.setFillColor(QColor(0, 255, 0, 80))
            self.area_painter.setWidth(1)
            self.area_painter.setVisible(False)

        self.node_valider = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_valider.setIcon(QgsRubberBand.ICON_FULL_DIAMOND)
        self.node_valider.setColor(QColor(255, 0, 0, 255))
        self.node_valider.setFillColor(QColor(0, 0, 0, 255))
        self.node_valider.setIconSize(12)
        self.node_valider.setVisible(False)

        self.area_valider = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.area_valider.setColor(QColor(255, 0, 0, 255))
        self.area_valider.setFillColor(QColor(0, 0, 0, 255))
        self.area_valider.setWidth(3)
        self.area_valider.setVisible(False)

    def rbs_populate(self):
        """Załadowanie poligonów i punktów do rubberband'ów."""
        for i in range(len(self.area_rbs)):
            geom = self.get_geom_from_part(i)
            poly = geom.asPolygon()[0]
            for j in range(len(poly) - 1):
                self.area_rbs[i].addPoint(poly[j])
                self.vertex_rbs[i].addPoint(poly[j])
            self.vertex_rbs[i].setVisible(False)

    def snap_to_layer(self, event):
        """Zwraca wyniki przyciągania do wierzchołków, krawędzi i powierzchni."""
        self.canvas.snappingUtils().setCurrentLayer(self.edit_layer)
        v = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Vertex)
        e = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Edge)
        a = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Area)
        return v, e, a

    def canvasMoveEvent(self, event):
        if self.move_void:  # Blokada pojedynczego sygnału poruszania myszką
            self.move_void = False
            return
        if self.interrupted:  # Blokada do momentu zwolnienia przycisku myszy
            return
        v, e, a = self.snap_to_layer(event)
        snap_type = v.type() + e.type() + a.type()
        map_point = self.toMapCoordinates(event.pos())
        if event.buttons() == Qt.LeftButton and not self.refreshing:
            if self.drawing:
                # Umożliwienie panningu mapy podczas rysowania area_painter'a:
                dist = QgsGeometry().fromPointXY(self.start_point).distance(QgsGeometry().fromPointXY(map_point))
                dist_scale = dist / self.canvas.scale() * 1000
                if dist_scale > 6.0:
                    self.dragging = True
                    self.cursor = "closed_hand"
                    self.canvas.panAction(event)
            elif self.node_presel and self.mode == "edit":
                # Przesunięcie wierzchołka:
                if not self.moving:
                    # Wejście do trybu przesuwania wierzchołka:
                    self.change_is_valid = True
                    self.node_sel = True
                    self.moving = True
                    self.dragging = False
                    self.cursor = "move"
                    self.valid_checker_create()
                    self.line_create()
                self.node_selector.movePoint(map_point)
                self.line_helper.movePoint(1, map_point)
                self.valid_check(map_point)
            elif self.edge_marker.isVisible() and not self.moving and self.mode == "edit":
                # Szybkie dodanie wierzchołka:
                self.node_add(e.point())
                self.geom_refresh(True)
                self.node_presel = [e.point(), self.node_idx[1]]
                self.selector_update()
            elif not self.drawing and not self.moving:
                # Panning mapy:
                self.dragging = True
                self.cursor = "closed_hand"
                self.canvas.panAction(event)
        elif (event.button() == Qt.NoButton and not self.dragging) or self.refreshing:
            # Odświeżanie rubberband'ów po zmianie geometrii:
            if self.refreshing:
                self.mouse_move_emit(True)
                self.refreshing = False
            if self.drawing and not self.dragging and self.area_painter.numberOfVertices() > 0:
                # Odświeżenie area_painter:
                if self.snap_void:  # Zapobiega usunięciu punktu utworzonego z przyciąganiem
                    self.snap_void = False
                else:
                    self.area_painter.removeLastPoint(0)
                self.area_painter.addPoint(map_point)
                # Sprawdzenie, czy aktualna geometria area_painter'a i topologia z innymi poligonami są poprawne:
                if self.area_painter.numberOfVertices() > 2:
                    self.valid_check(None, area_rb=self.area_painter, poly_check=False, node_check=True)
            # Aktualizacja hoveringu myszy względem poligonów:
            if self.a_temp != a.featureId():
                self.a_temp = a.featureId()
                self.part_idx = self.get_part_from_id(a.featureId())
                self.area_idx = -1
            if snap_type == 0:  # Kursor poza poligonami, brak obiektów do przyciągnięcia
                if self.mode == "edit" and self.cursor != "open_hand":
                    self.cursor = "open_hand"
                if self.node_presel:
                    self.node_presel = []
                self.node_hover.setVisible(False) #if self.node_sel else self.node_hover.setVisible(False)
                self.edge_marker.setVisible(False)
                if self.area_idx != -1:
                    self.area_idx = -1
            elif snap_type == 4:  # Kursor w obrębie poligonu
                if self.mode == "edit" and self.cursor != "open_hand":
                    self.cursor = "open_hand"
                if self.node_presel:
                    self.node_presel = []
                self.node_hover.setVisible(False)
                self.edge_marker.setVisible(False)
                if self.area_idx != self.part_idx:
                    self.area_idx = self.part_idx
            elif snap_type == 5 or snap_type == 7:  # Wierzchołek do przyciągnięcia
                if self.mode == "edit" and self.cursor != "arrow":
                    self.cursor = "arrow"
                self.node_presel = [v.point(), e.featureId()]
                self.node_hover.movePoint(v.point(), 0)
                self.node_hover.setVisible(True)
                self.edge_marker.setVisible(False)
                if self.area_idx != self.part_idx:
                    self.area_idx = self.part_idx
            elif snap_type == 6:  # Krawędź do przyciągnięcia
                if self.cursor != "cross":
                    self.cursor = "cross"
                    if self.prev_node != e.edgePoints()[0]:
                        self.prev_node = e.edgePoints()[0]
                if self.node_presel:
                    self.node_presel = []
                self.edge_marker.movePoint(e.point(), 0)
                if self.mode == "edit":
                    self.edge_marker.setVisible(True)
                self.node_hover.setVisible(False)
                if self.area_idx != self.part_idx:
                    self.area_idx = self.part_idx
            if self.mode != "edit" and self.cursor != "cross":
                self.cursor = "cross"

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.mode != "edit":
                self.start_point = self.toMapCoordinates(event.pos())
                if not self.drawing:
                    self.drawing = True
                    self.change_is_valid = True
                if self.node_presel:
                    self.area_painter.removeLastPoint(0)
                    snapped_point = self.node_presel[0]
                    self.area_painter.addPoint(snapped_point)
                    self.snap_void = True
                else:
                    self.area_painter.addPoint(self.toMapCoordinates(event.pos()))
        elif event.button() == Qt.RightButton:
            if self.drawing:
                if not self.snap_void:
                    self.area_painter.removeLastPoint(0)
                if self.area_painter.numberOfVertices() > 2:
                    self.valid_check(None, area_rb=self.area_painter, poly_check=False, node_check=True)
                    self.area_drawn()
                self.geom_refresh(True)
                self.drawing = False
                self.mode = "edit"

    def canvasReleaseEvent(self, event):
        if self.interrupted:  # Zdjęcie blokady po zwolnieniu przycisku myszy
            self.interrupted = False
            return
        if event.button() == Qt.LeftButton:
            if not self.moving and not self.dragging and not self.drawing:
                if self.node_presel:
                    self.node_sel = True  # Zaznaczenie wierzchołka
                else:
                    self.node_sel = False  # Odzaznaczenie wierzchołka
            # Przemieszczenie wierzchołka:
            elif self.moving:
                map_point = self.toMapCoordinates(event.pos())
                if self.change_is_valid:
                    self.vertex_rbs[self.node_idx[0]].movePoint(self.node_idx[1], map_point)
                else:
                    self.change_is_valid = True
                self.geom_refresh()
                self.selector_update()
                self.moving = False
            # Zakończenie panningu mapy:
            elif self.dragging:
                # Panning podczas rysowania area_painter'a:
                if self.drawing and self.area_painter.numberOfVertices() > 0:
                    self.area_painter.removeLastPoint(0)
                    self.cursor = "cross"
                else:
                    self.cursor = "open_hand"
                self.canvas.panActionEnd(event.pos())
                self.dragging = False

    def canvasDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self.dragging and self.mode == "edit":
            if self.edge_marker.isVisible():
                # Ustalenie lokalizacji nowego wierzchołka:
                geom = self.edge_marker.asGeometry()
                p_list = list(geom.vertices())
                p_last = len(p_list) - 1
                self.node_add(p_list[p_last])
                self.geom_refresh()

    def keyReleaseEvent(self, event):
        if self.node_sel and not self.moving and event.key() == Qt.Key_Delete:
            # Skasowanie wierzchołka:
            self.vertex_delete()
        elif self.moving and event.key() == Qt.Key_Escape:
            # Przerwanie przemieszczenia wierzchołka:
            self.interrupted = True
            self.moving = False
            self.geom_refresh(True)
            self.selector_update()
            self.mouse_move_emit()
        elif self.drawing and not self.dragging and self.area_painter.numberOfVertices() > 1 and (event.matches(QKeySequence.Undo) or event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace):
            # Usunięcie ostatnio narysowanego wierzchołka area_painter'a:
            self.area_painter.removeLastPoint()
            self.mouse_move_emit()
        elif self.mode != "edit" and not self.dragging and event.key() == Qt.Key_Escape:
            # Wyjście z trybu rysowania do trybu edycji:
            self.geom_refresh()
            self.drawing = False
            self.mode = "edit"

    def mouse_move_emit(self, after=False):
        """Sposób na odpalenie canvasMoveEvent."""
        cursor = QCursor()
        pos = self.canvas.mouseLastXY()
        global_pos = self.canvas.mapToGlobal(pos)
        if after:
            # Blokada canvasMoveEvent, żeby przypadkiem nie przemieścić nowego wierzchołka:
            self.move_void = True
            # Przywrócenie pierwotnej pozycji kursora:
            cursor.setPos(global_pos.x() + 2, global_pos.y() + 2)
        else:
            # Nieznaczne przesunięcie kursora, żeby odpalić canvasMoveEvent:
            self.refreshing = True
            cursor.setPos(global_pos.x(), global_pos.y())

    def area_drawn(self):
        if not self.change_is_valid:
            return
        new_poly = self.area_painter.asGeometry()
        overlaps = self.area_overlap_check(new_poly)
        if self.mode == "add":
            if len(overlaps[0]) == 0:  # Geometria area_painter nie przecina się z żadnym poligonem
                if len(overlaps[1]) > 0:
                    # Geometria area_painter dotyka wierzchołkiem(-kami) choć jeden poligon -
                    # prowadzi to do powstania błędnej topologii - rezygnacja z dodawania obszaru
                    pass
                else:
                    # Geometria area_painter nie dotyka żadnego poligonu-
                    # rysowanie nowego poligonu:
                    self.part_add(new_poly)
            else:
                # Geometria area_painter łączy się z przynajmniej jednym poligonem -
                # łączenie poligonów z listy overlaps i area_painter w jeden poligon:
                self.parts_combine(new_poly, overlaps[0])
        elif self.mode == "sub" and len(overlaps[0]) > 0:
            # Geometria area_painter nakłada się na przynajmniej jeden poligon -
            # wyłączenie z poligonów z listy overlaps powierzchni area_painter:
            self.parts_difference(new_poly, overlaps[0])

    def part_add(self, new_poly):
        """Dodanie nowego poligonu do geometrii."""
        _vrb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.vertex_rbs.append(_vrb)
        poly = new_poly.asPolygon()[0]
        i = len(self.vertex_rbs) - 1
        for j in range(len(poly) - 1):
            self.vertex_rbs[i].addPoint(poly[j])

    def parts_combine(self, new_poly, overlaps):
        """Utworzenie nowej geometrii z połączenia wybranych poligonów i aktualizacja listy vertex_rbs."""
        combined_poly = self.polygon_from_parts(new_poly, overlaps)
        if not combined_poly:
            print("Wystąpił błąd przy złączaniu geometrii!")
            return
        # Usunięcie rubberband'ów z listy 'overlaps':
        self.remove_overlapped_rbs(overlaps)
        # Utworzenie rubberband'a ze złączonej geometrii:
        self.part_add(combined_poly)

    def parts_difference(self, sub_poly, overlaps):
        """Utworzenie nowej geometrii z wycięcia powierzchni area_painter'a z wybranych poligonów i aktualizacja listy vertex_rbs."""
        changed = []
        for i in range(len(self.area_rbs)):
            if i in overlaps:  # Poligon znajduje się na liście
                poly = self.area_rbs[i].asGeometry()
                try:
                    new_poly = poly.difference(sub_poly)
                except Exception as err:
                    print(err)
                    return
                changed.append(new_poly)
        # Usunięcie rubberband'ów z listy 'overlaps':
        self.remove_overlapped_rbs(overlaps)
        # Utworzenie nowych rubberband'ów z przyciętych poligonów:
        for geom in changed:
            if not geom:
                continue
            new_geom = geom.asGeometryCollection()
            for poly in new_geom:
                if poly.type() == QgsWkbTypes.PolygonGeometry:
                    self.part_add(poly)

    def remove_overlapped_rbs(self, overlaps):
        """Usuwa area- i vertex_rbs z listy 'overlaps'."""
        for i in sorted(overlaps, reverse=True):
            self.area_rbs[i].reset(QgsWkbTypes.PolygonGeometry)
            del self.area_rbs[i]  # Usunięcie area rubberband'a z listy
            self.vertex_rbs[i].reset(QgsWkbTypes.PointGeometry)
            del self.vertex_rbs[i]  # Usunięcie vertex rubberband'a z listy

    def polygon_from_parts(self, new_poly, overlaps):
        """Złączenie geometrii area_painter i poligonów o id podanych na liście 'overlaps'."""
        for i in range(len(self.area_rbs)):
            if i in overlaps:  # Poligon znajduje się na liście
                poly = self.area_rbs[i].asGeometry()
                # Sprawdzenie, czy geometria jest poprawna:
                err = poly.validateGeometry()
                if not err:
                    new_poly = new_poly.combine(poly)
                else:
                    return None
        return new_poly

    def segments_from_polygon(self, poly):
        """Zwraca listę boków poligonu."""
        segments = []
        poly = poly.asPolygon()[0]
        for i in range(len(poly) - 1):
            line = QgsGeometry().fromPolylineXY([poly[i], poly[i + 1]])
            segments.append(line)
        return segments

    def line_from_polygon(self, poly):
        """Zwraca linię z poligonu."""
        poly = poly.asPolygon()[0]
        line = QgsGeometry().fromPolylineXY(poly)
        return line

    def valid_check(self, map_point, remove=False, area_rb=None, poly_check=True, node_check=False):
        """Sprawdza, czy geometria po przemieszczeniu wierzchołka jest prawidłowa lub nachodzi na inny poligon."""
        is_valid = True  # Wstępne założenie, że geometria jest poprawna
        # Kasowanie poprzednich stanów rubberband'ów:
        self.node_valider.reset(QgsWkbTypes.PointGeometry)
        self.area_valider.reset(QgsWkbTypes.PolygonGeometry)
        if not area_rb:  # Nie wskazano rubberband'a do walidacji - użyty jest valid_checker
            # Aktualizacja geometrii valid_checker'a:
            if remove:
                self.valid_checker.removePoint(map_point, True)
            else:
                self.valid_checker.movePoint(self.node_idx[1], map_point)
            rb = self.valid_checker.asGeometry()
            rb_geom = self.get_geom_from_vertex_rb(rb)
        else:
            rb_geom = area_rb.asGeometry()
            rb = self.get_nodes_from_area_rb(rb_geom)
        # Sprawdzenie, czy nowa geometria jest poprawna:
        rb_check = self.rubberband_check(rb_geom)
        if not rb_check:  # Nowa geometria nie jest poprawna - pokazanie błędnych punktów
            # Stworzenie listy z wierzchołkami valid_checker'a:
            rb_nodes = []
            nodes = rb.constParts() if not area_rb else rb
            for node in nodes:
                rb_nodes.append(QgsPointXY(node.x(), node.y()))
            # Stworzenie listy z liniami boków valid_checker'a:
            segments = self.segments_from_polygon(rb_geom)
            # Sprawdzenie, czy któreś linie się przecinają -
            # wykluczone są przecięcia na wierzchołkach:
            pairs = list(combinations(segments, 2))
            for p in pairs:
                intersect_geom = p[0].intersection(p[1])
                if intersect_geom and intersect_geom.type() == QgsWkbTypes.PointGeometry:
                    if not intersect_geom.asPoint() in rb_nodes:
                        # Pokazanie błędnych przecięć:
                        self.node_valider.addPoint(intersect_geom.asPoint())
            is_valid = False
            rb_geom = rb_geom.makeValid()  # Inaczej nie będzie można spawdzić przecięcia z innymi poligonami
        # Sprawdzenie, czy nowa geometria styka się z innymi poligonami tylko na wierzchołkach:
        if node_check:
            if self.mode != "sub":
                overlaps = self.area_overlap_check(rb_geom)
            else:
                overlaps = self.line_overlap_check(rb_geom)
            # Area_painter styka się z innymi poligonami wyłącznie na wierzchołkach:
            if len(overlaps[1]) > 0:
                # Pokazanie nałożonych wierzchołków:
                for point in overlaps[1]:
                    self.node_valider.addPoint(point.asPoint())
                is_valid = False
        # Sprawdzenie, czy nowa geometria przecina się z innymi poligonami:
        if poly_check:
            for i in range(len(self.area_rbs)):
                if i == self.node_idx[0]:  # Wykluczenie aktualnie edytowanego poligonu
                    continue
                poly = self.area_rbs[i].asGeometry()
                overlap_geom = rb_geom.intersection(poly).asGeometryCollection()
                for geom in overlap_geom:
                    if geom and geom.type() == QgsWkbTypes.PolygonGeometry:
                        # Pokazanie błędnych powierzchni:
                        self.area_valider.addGeometry(geom)
                        is_valid = False
        self.change_is_valid = is_valid

    def rubberband_check(self, geom):
        """Zwraca geometrię, jesli jest poprawna."""
        return geom if geom.isGeosValid() else None

    def area_overlap_check(self, new_poly):
        """Zwraca id poligonów, które przecinają się ich powierzchniami z geometrią area_painter'a i listę wierzchołków, jeśli są jedynymi połączeniami z danym poligonem."""
        overlaps = []
        touches = []
        for i in range(len(self.area_rbs)):
            poly = self.area_rbs[i].asGeometry()
            overlap_geom = new_poly.intersection(poly).asGeometryCollection()
            appended = False
            for geom in overlap_geom:
                if geom.type() == QgsWkbTypes.PolygonGeometry or geom.type() == QgsWkbTypes.LineGeometry:
                    if geom and not appended:
                        appended = True
                        overlaps.append(i)
                elif geom.type() == QgsWkbTypes.PointGeometry:
                    if geom:
                        touches.append(geom)
        return overlaps, touches

    def line_overlap_check(self, new_poly):
        """Zwraca id poligonów, które przecinają się ich liniami z geometrią area_painter'a i listę wierzchołków, jeśli są jedynymi połączeniami z danym poligonem."""
        overlaps = []
        touches = []
        for i in range(len(self.area_rbs)):
            poly = self.area_rbs[i].asGeometry()
            polyline = self.line_from_polygon(poly)
            overlap_geom = new_poly.intersection(polyline).asGeometryCollection()
            appended = False
            for geom in overlap_geom:
                if geom.type() == QgsWkbTypes.LineGeometry:
                    if geom and not appended:
                        appended = True
                        overlaps.append(i)
                elif geom.type() == QgsWkbTypes.PointGeometry:
                    if geom:
                        touches.append(geom)
        return overlaps, touches

    def node_add(self, point):
        """Utworzenie nowego wierzchołka w poligonie."""
        new_node = QgsPointXY(point.x(), point.y())
        rb = self.vertex_rbs[self.area_idx]
        geom = rb.asGeometry()
        p_list = list(geom.vertices())
        rb.reset(QgsWkbTypes.PointGeometry)
        for i in range(len(p_list)):
            node = QgsPointXY(p_list[i].x(), p_list[i].y())
            if node == self.prev_node:
                rb.addPoint(node)
                rb.addPoint(new_node)
                self.node_idx = (self.area_idx, i + 1)
            else:
                rb.addPoint(node)

    def valid_checker_create(self):
        """Tworzy tymczasową kopię rubberband'a, którego wierzchołek będzie przesuwany."""
        if self.valid_checker:
            self.valid_checker.reset(QgsWkbTypes.PointGeometry)
        for i in range(self.vertex_rbs[self.node_idx[0]].numberOfVertices()):
            self.valid_checker.addPoint(self.vertex_rbs[self.node_idx[0]].getPoint(0, i))
        self.valid_checker.setVisible(False)

    def line_create(self):
        """Utworzenie i wyświetlenie linii pomocniczej przy przesuwaniu wierzchołka."""
        part = self.node_idx[0]
        node = self.node_idx[1]
        node_cnt = self.vertex_rbs[part].numberOfVertices() - 1
        if node == 0:  # Zaznaczony jest pierwszy wierzchołek
            picked_nodes = [node_cnt, node, node + 1]
        elif node == node_cnt:  # Zaznaczony jest ostatni wierzchołek
            picked_nodes = [node - 1, node, 0]
        else:
            picked_nodes = [node -1, node, node + 1]
        line_points = self.get_points_from_indexes(part, picked_nodes)
        self.line_helper.reset(QgsWkbTypes.LineGeometry)
        for p in line_points:
            self.line_helper.addPoint(p)
        self.line_helper.setVisible(True)

    def geom_refresh(self, no_move=False):
        """Aktualizacja warstwy i rubberband'ów po zmianie geometrii."""
        self.geom_update()  # Aktualizacja geometrii na warstwie
        self.rbs_clear()  # Skasowanie rubberband'ów
        self.rbs_create()  # Utworzenie nowych rubberband'ów
        self.rbs_populate()  # Załadowanie geometrii do rubberband'ów
        if no_move:
            self.area_hover_change(self.area_idx)
        else:
            self.mouse_move_emit()  # Sztuczne odpalenie canvasMoveEvent, żeby odpowiednio wyświetlić rubberband'y

    def get_part_from_id(self, id):
        """Zwraca atrybut 'part' poligonu o numerze id."""
        for feat in self.edit_layer.getFeatures():
            if feat.id() == id:
                return feat.attribute("part")
        return None

    def get_geom_from_id(self, id):
        """Zwraca geometrię poligonu o numerze id."""
        for feat in self.edit_layer.getFeatures():
            if feat.id() == id:
                return feat.geometry()
        return None

    def get_geom_from_part(self, part):
        """Zwraca geometrię poligonu o numerze atrybutu 'part'."""
        feats = self.edit_layer.getFeatures(f'"part" = {part}')
        try:
            feat = list(feats)[0]
        except:
            return None
        return feat.geometry()

    def get_node_index(self):
        """Zwraca index punktu i poligonu, znajdującego się pod node_selector'em."""
        i = 0
        point = self.node_presel[0]
        for rb in self.vertex_rbs:
            j = 0
            rb_geom = rb.asGeometry()
            for part in rb_geom.constParts():
                p_geom = QgsPointXY(part.x(), part.y())
                if point == p_geom:
                    return i, j
                j += 1
            i += 1
        return -1, -1

    def get_geom_from_vertex_rb(self, rb):
        """Zwraca geometrię zbudowaną z punktów rubberband'u."""
        pts = []
        for part in rb.constParts():
            pts.append((part.x(), part.y()))
        poly = QgsGeometry.fromPolygonXY([[QgsPointXY(pair[0], pair[1]) for pair in pts]])
        return poly

    def get_nodes_from_vertex_rb(self, rb):
        """Zwraca punkty z punktowego rubberband'u."""
        pts = []
        for part in rb.constParts():
            pts.append(part)
        return pts

    def get_nodes_from_area_rb(self, rb):
        """Zwraca punkty z poligonalnego rubberband'u."""
        pts = []
        for vertex in rb.vertices():
            pts.append(vertex)
        return pts

    def get_points_from_indexes(self, part, nodes):
        """Zwraca punkty wybranego poligonu na podstawie ich indeksów."""
        pts = []
        geom = self.vertex_rbs[part].asGeometry()
        p_list = list(geom.vertices())
        for node in nodes:
            pt = p_list[node]
            pts.append(QgsPointXY(pt.x(), pt.y()))
        return pts

    def vertex_delete(self):
        """Usuwa zaznaczony wierzchołek poligonu."""
        if self.node_idx[0] < 0:
            print("brak zaznaczonego wierzchołka")
            return
        if self.vertex_rbs[self.node_idx[0]].numberOfVertices() > 3:
            self.valid_checker_create()
            self.valid_check(self.node_idx[1], remove=True, node_check=True)
            if self.change_is_valid:
                self.vertex_rbs[self.node_idx[0]].removePoint(self.node_idx[1], True)
                self.after_vertex_delete()
            else:
                self.move_is_valid = True
                self.selector_update()
                self.line_create()
                self.line_helper.setFillColor(QColor(255, 0, 0, 255))
                self.line_helper.removePoint(1, True)
                self.node_flasher()
        else:
            self.vertex_rbs[self.node_idx[0]].reset(QgsWkbTypes.PointGeometry)
            del self.vertex_rbs[self.node_idx[0]]
            self.node_idx = (-1, -1)
            self.node_sel = False
            self.geom_refresh(True)

    def after_vertex_delete(self):
        """Aktualizacja rubberband'ów po próbie usunięcia wierzchołka."""
        # Zmiana numeru zaznaczonego wierzchołka, jeśli został usunięty ostatni:
        if self.node_idx[1] > self.vertex_rbs[self.node_idx[0]].numberOfVertices() - 1:
            self.node_idx = (self.node_idx[0], self.node_idx[1] - 1)
        self.geom_refresh(True)
        self.selector_update()

    def node_flasher(self):
        """Efekt graficzny mrugania punktu."""
        # Przerwanie poprzedniego flash'a, jeśli jeszcze trwa:
        try:
            self.timer.stop()
            self.timer.deleteLater()
        except:
            pass
        # Stworzenie stopera i jego odpalenie:
        self.timer = QTimer(self, interval=150)
        self.timer.timeout.connect(self.flash_change)
        self.timer.start()  # Odpalenie stopera

    def flash_change(self):
        """Zmienia kolor node_selector'a."""
        if self.flash > 1:
            self.flash = 0
            self.timer.stop()
            self.timer.deleteLater()
            self.after_vertex_delete()
            return
        else:
            self.flash += 1
            self.node_selector.setVisible(True) if (self.flash % 2) == 0 else self.node_selector.setVisible(False)

    def geom_update(self):
        """Aktualizacja geometrii poligonów po jej zmianie."""
        self.edit_layer.dataProvider().truncate()
        if not self.vertex_rbs:  # Nie ma poligonów
            return None
        # Załadowanie aktualnej geometrii do warstwy edit_poly:
        geom_list = []
        with edit(self.edit_layer):
            for i in range(len(self.vertex_rbs)):
                geom = self.get_geom_from_vertex_rb(self.vertex_rbs[i].asGeometry())
                feat = QgsFeature(self.edit_layer.fields())
                feat.setAttribute("part", i)
                feat.setGeometry(geom)
                self.edit_layer.addFeature(feat)
                geom_list.append(geom)
        if not geom_list:
            self.geom = None
        if len(geom_list) > 1:
            self.geom = QgsGeometry.collectGeometry(geom_list)
        else:
            self.geom = geom_list[0]
        return self.geom

    def geom_from_backup(self):
        """Zwraca geometrię z warstwy 'edit_poly_backup'."""
        feat_cnt = self.backup_layer.featureCount()
        if feat_cnt == 0:
            self.geom = None
        else:
            geom_list = []
            feats = self.backup_layer.getFeatures()
            for feat in feats:
                geom = feat.geometry()
                geom_list.append(geom)
            if len(geom_list) > 1:
                self.geom = QgsGeometry.collectGeometry(geom_list)
            else:
                self.geom = geom_list[0]
        return self.geom

    def accept_changes(self, cancel=False):
        """Zakończenie edycji geometrii wyrobiska i zaakceptowanie wprowadzonych zmian, albo przywrócenie stanu pierwotnego (cancel=True)."""
        self.interrupted = True
        if cancel:
            self.geom = self.geom_from_backup()
        elif not cancel and not self.geom:
            self.geom = self.geom_update()
        self.rbs_clear()
        self.edit_layer.dataProvider().truncate()
        self.edit_layer.triggerRepaint()
        self.backup_layer.dataProvider().truncate()
        self.backup_layer.triggerRepaint()
        self.buttons_disconnect()
        self.canvas.setExtent(self.init_extent)
        dlg.obj.edit_mode(False)
        self.ending.emit(self.layer, self.geom)

    def buttons_disconnect(self):
        """Odłączenie przycisków."""
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool"].clicked.disconnect()
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_add"].clicked.disconnect()
        dlg.bottom_dock.toolboxes["tb_edit_tools"].widgets["btn_edit_tool_sub"].clicked.disconnect()
        dlg.bottom_dock.toolboxes["tb_edit_exit"].widgets["btn_accept"].clicked.disconnect()
        dlg.bottom_dock.toolboxes["tb_edit_exit"].widgets["btn_cancel"].clicked.disconnect()

    def rbs_clear(self):
        """Wyczyszczenie zawartości i usunięcie rubberband'ów."""
        for a in self.area_rbs:
            a.reset(QgsWkbTypes.PolygonGeometry)
        for v in self.vertex_rbs:
            v.reset(QgsWkbTypes.PointGeometry)
        self.area_rbs = []
        self.vertex_rbs = []
        if self.valid_checker:
            self.valid_checker.reset(QgsWkbTypes.PointGeometry)
            self.valid_checker = None
        if self.node_valider:
            self.node_valider.reset(QgsWkbTypes.PointGeometry)
            self.node_valider = None
        if self.area_valider:
            self.area_valider.reset(QgsWkbTypes.PolygonGeometry)
            self.area_valider = None
        if self.line_helper:
            self.line_helper.reset(QgsWkbTypes.LineGeometry)
            self.line_helper = None
        if self.node_hover:
            self.node_hover.reset(QgsWkbTypes.PointGeometry)
            self.node_hover = None
        if self.node_selector:
            self.node_selector.reset(QgsWkbTypes.PointGeometry)
            self.node_selector = None
        if self.edge_marker:
            self.edge_marker.reset(QgsWkbTypes.PointGeometry)
            self.edge_marker = None
        if self.area_marker:
            self.area_marker.reset(QgsWkbTypes.PolygonGeometry)
            self.area_marker = None
        if self.area_painter:
            self.area_painter.reset(QgsWkbTypes.PolygonGeometry)
            self.area_painter = None


class MultiMapTool(QgsMapToolIdentify):
    """Domyślny maptool łączący funkcje nawigacji po mapie i selekcji obiektów."""
    identified = pyqtSignal(object, object, object)
    cursor_changed = pyqtSignal(str)

    def __init__(self, canvas, button):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.layer = QgsVectorLayer()
        self.layer.setCrs(QgsCoordinateReferenceSystem(2180))
        self.dragging = False
        self.sel = False
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "open_hand"

    def button(self):
        return self._button

    @threading_func
    def findFeatureAt(self, pos):
        pos = self.toLayerCoordinates(self.layer, pos)
        scale = iface.mapCanvas().scale()
        tolerance = scale / 250
        search_rect = QgsRectangle(pos.x() - tolerance,
                                  pos.y() - tolerance,
                                  pos.x() + tolerance,
                                  pos.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(search_rect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        lyrs = self.get_lyrs()
        if lyrs:
            for lyr in lyrs:
                for feat in lyr.getFeatures(request):
                    return feat
        else:
            return None

    def get_lyrs(self):
        """Zwraca listę włączonych warstw z obiektami."""
        lyrs = []
        for _list in dlg.lyr.lyr_vis:
            if _list[1]:
                lyr = dlg.proj.mapLayersByName(_list[0])[0]
                lyrs.append(lyr)
        return lyrs

    @threading_func
    def ident_in_thread(self, x, y):
        """Zwraca wynik identyfikacji przeprowadzonej poza wątkiem głównym QGIS'a."""
        lyrs = self.get_lyrs()
        scale = iface.mapCanvas().scale()
        self.setCanvasPropertiesOverrides(scale / 250)
        return self.identify(x, y, self.TopDownStopAtFirst, lyrs, self.VectorLayer)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["arrow", Qt.ArrowCursor],
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def canvasMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.dragging = True
            self.cursor = "closed_hand"
            self.canvas.panAction(event)
            if dlg.obj.marsz:
                dlg.obj.marsz = None
        elif event.buttons() == Qt.NoButton and not self.dragging:
            th = self.findFeatureAt(event.pos())
            feat = th.get()
            if feat == None:
                if self.sel:
                    self.cursor = "open_hand"
                    self.sel = False
            else:
                if not self.sel:
                    self.cursor = "arrow"
                    self.sel = True

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.canvas.panActionEnd(event.pos())
            self.dragging = False
            self.cursor = "open_hand"
        elif event.button() == Qt.LeftButton and not self.dragging:
            th = self.ident_in_thread(event.x(), event.y())
            result = th.get()
            if len(result) > 0:
                if result[0].mLayer.geometryType() == QgsWkbTypes.PointGeometry:
                    self.identified.emit(result[0].mLayer, result[0].mFeature, None)
                    if dlg.obj.marsz:
                        dlg.obj.marsz = None
                elif result[0].mLayer.geometryType() == QgsWkbTypes.LineGeometry:
                    self.point_from_line(event, result[0].mLayer, result[0].mFeature)
            else:
                self.identified.emit(None, None, None)
                if dlg.obj.marsz:
                    dlg.obj.marsz = None
        elif event.button() == Qt.RightButton and not self.dragging:
            if dlg.obj.marsz:
                dlg.obj.marsz = None

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if dlg.obj.marsz:
            dlg.obj.marsz = None

    def point_from_line(self, event, layer, feature):
        """Wyznacza najbliższy od kursora punkt na linii."""
        self.canvas.snappingUtils().setCurrentLayer(layer)
        e = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Edge)
        if e.type() == 2:
            self.identified.emit(layer, feature, e.point())
        else:
            self.identified.emit(None, None, None)


class IdentMapTool(QgsMapToolIdentify):
    """Maptool do zaznaczania obiektów z wybranej warstwy."""
    identified = pyqtSignal(object, object)

    def __init__(self, canvas, layer, button):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.setCursor(Qt.CrossCursor)

    def button(self):
        return self._button

    def canvasReleaseEvent(self, event):
        result = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, self.layer, self.VectorLayer)
        if len(result) > 0:
            self.identified.emit(result[0].mLayer, result[0].mFeature)
        else:
            self.identified.emit(None, None)


class PointPickerMapTool(QgsMapToolIdentify):
    """Maptool do wspomaganego wybierania obiektu z wybranej warstwy."""
    picked = pyqtSignal(object, object)
    cursor_changed = pyqtSignal(str)

    def __init__(self, canvas, layer, button, extra):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.dragging = False
        self.accepted = False
        self.canceled = False
        self.deactivated = False
        self.lyrs = layer
        self.lyr_names = extra
        self.temp_point = None
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "cross"
        self.marker = None
        self.rbs_create()

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["cross", Qt.CrossCursor],
                    ["closed_hand", Qt.ClosedHandCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        self.marker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.marker.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.marker.setColor(QColor(255, 255, 255, 255))
        self.marker.setFillColor(QColor(0, 0, 0, 32))
        self.marker.setIconSize(30)
        self.marker.addPoint(QgsPointXY(0, 0), False)
        self.marker.setVisible(False)

    def snap_to_layer(self, event, layer):
        """Zwraca wyniki przyciągania do wierzchołków i krawędzi."""
        self.canvas.snappingUtils().setCurrentLayer(layer)
        v = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Vertex)
        return v

    @threading_func
    def find_nearest_feature(self, pos):
        """Zwraca najbliższy od kursora obiekt na wybranych warstwach."""
        pos = self.toLayerCoordinates(self.lyrs[0], pos)
        scale = iface.mapCanvas().scale()
        tolerance = scale / 250
        search_rect = QgsRectangle(pos.x() - tolerance,
                                  pos.y() - tolerance,
                                  pos.x() + tolerance,
                                  pos.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(search_rect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        lyrs = self.get_lyrs()
        if self.lyr_names:
            for lyr in lyrs:
                for feat in lyr.getFeatures(request):
                    return lyr
        else:
            return None

    def get_lyrs(self):
        """Zwraca listę włączonych warstw z obiektami."""
        lyrs = []
        for _list in dlg.lyr.lyr_vis:
            if _list[1] and _list[0] in self.lyr_names:
                lyr = dlg.proj.mapLayersByName(_list[0])[0]
                lyrs.append(lyr)
        return lyrs

    def canvasMoveEvent(self, event):
        map_point = self.toMapCoordinates(event.pos())
        if event.buttons() == Qt.LeftButton:
            self.dragging = True
            self.cursor = "closed_hand"
            self.canvas.panAction(event)
        if event.buttons() == Qt.NoButton:
            if self.cursor != "cross":
                self.cursor = "cross"
            th = self.find_nearest_feature(event.pos())
            result = th.get()
            snap_type = None
            if result:
                v = self.snap_to_layer(event, result)
                snap_type = v.type()
                if snap_type == 1:  # Kursor nad vertexem
                    self.marker.movePoint(v.point(), 0)
                    self.temp_point = v.point()
                    self.marker.setVisible(True)
                else:
                    self.marker.setVisible(False)
                    self.temp_point = map_point
            else:
                self.marker.setVisible(False)
                self.temp_point = map_point

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:  # Zakończenie panningu mapy
                self.cursor = "cross"
                self.canvas.panActionEnd(event.pos())
                self.dragging = False
                return
            self.accepted = True
            result = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, self.lyrs, self.VectorLayer)
            self.accept_changes(result)
        elif event.button() == Qt.RightButton:
            self.canceled = True
            self.accept_changes(cancel=True)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.canceled = True
            self.accept_changes(cancel=True)

    def accept_changes(self, result=None, cancel=False, deactivated=False):
        """Zakończenie wybierania obiektu punktowego."""
        if not cancel and not deactivated:
            if len(result) > 0:
                self.picked.emit(result[0].mLayer, result[0].mFeature)
            else:
                self.picked.emit(None, None)
        else:
            self.picked.emit(None, None)
        if self.marker:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None

    def deactivate(self):
        """Zakończenie działania maptool'a."""
        super().deactivate()
        print("deactivated")
        if not self.canceled and not self.accepted:
            self.accept_changes(deactivated=True)


class PointDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów punktowych."""
    drawn = pyqtSignal(object, object)

    def __init__(self, canvas, button, extra):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        self.extra = extra
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.setCursor(Qt.CrossCursor)

    def button(self):
        return self._button

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = self.toMapCoordinates(event.pos())
            self.drawn.emit(point, self.extra)
        else:
            self.drawn.emit(None, None)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.drawn.emit(None, None)


class LineDrawMapTool(QgsMapTool):
    """Maptool do rysowania liniowego obiektu marszruty."""
    drawn = pyqtSignal(object, object, bool, bool)
    cursor_changed = pyqtSignal(str)

    def __init__(self, canvas, button, extra, cont_list):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        self.color = QColor(extra[0][0], extra[0][1], extra[0][2], extra[0][3])
        self.accepted = False
        self.canceled = False
        self.deactivated = False
        self.geom = None
        self.new = True
        self.id = None
        self.init_extent = None
        self.rb = None
        self.temp_rb = None
        self.snap_marker = None
        self.start_point = None
        self.temp_point = None
        self.drawing = False
        self.dragging = False
        self.layer = None
        self.lyrs = extra[1]
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "cross"
        self.rbs_create()
        if cont_list:  # Kontynuowanie rysowania
            self.new = False
            self.id = cont_list[0]
            self.geom = cont_list[1]
            self.init_extent = cont_list[2]
            self.geom_load(self.geom)

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        self.snap_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.snap_marker.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.snap_marker.setColor(QColor(0, 0, 0, 255))
        self.snap_marker.setFillColor(QColor(255, 255, 0, 255))
        self.snap_marker.setIconSize(10)
        self.snap_marker.addPoint(QgsPointXY(0, 0), False)
        self.snap_marker.setVisible(False)

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["cross", Qt.CrossCursor],
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def snap_to_layer(self, event, layer):
        """Zwraca wyniki przyciągania do wierzchołków i krawędzi."""
        self.canvas.snappingUtils().setCurrentLayer(layer)
        v = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Vertex)
        e = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Edge)
        return v, e

    @threading_func
    def find_nearest_feature(self, pos):
        """Zwraca najbliższy od kursora obiekt na wybranych warstwach."""
        pos = self.toLayerCoordinates(self.layer, pos)
        scale = iface.mapCanvas().scale()
        tolerance = scale / 250
        search_rect = QgsRectangle(pos.x() - tolerance,
                                  pos.y() - tolerance,
                                  pos.x() + tolerance,
                                  pos.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(search_rect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        lyrs = self.get_lyrs()
        if self.lyrs:
            for lyr in lyrs:
                for feat in lyr.getFeatures(request):
                    return lyr
        else:
            return None

    def get_lyrs(self):
        """Zwraca listę włączonych warstw z obiektami."""
        lyrs = []
        for _list in dlg.lyr.lyr_vis:
            if _list[1] and _list[0] in self.lyrs:
                lyr = dlg.proj.mapLayersByName(_list[0])[0]
                lyrs.append(lyr)
        return lyrs

    def canvasMoveEvent(self, event):
        map_point = self.toMapCoordinates(event.pos())
        if event.buttons() == Qt.LeftButton:
            if self.drawing:
                # Umożliwienie panningu mapy podczas rysowania:
                dist = QgsGeometry().fromPointXY(self.start_point).distance(QgsGeometry().fromPointXY(map_point))
                dist_scale = dist / self.canvas.scale() * 1000
                if dist_scale > 6.0:
                    self.dragging = True
                    self.cursor = "closed_hand"
                    self.canvas.panAction(event)
            elif not self.drawing:
                # Panning mapy:
                self.dragging = True
                self.cursor = "closed_hand"
                self.canvas.panAction(event)
        if event.buttons() == Qt.NoButton:
            if self.cursor != "cross":
                self.cursor = "cross"
            th = self.find_nearest_feature(event.pos())
            result = th.get()
            snap_type = None
            if result:
                v, e = self.snap_to_layer(event, result)
                snap_type = v.type() + e.type()
                if snap_type == 1 or snap_type == 3:  # Kursor nad vertexem marszruty albo parkingu
                    self.snap_marker.movePoint(v.point(), 0)
                    self.temp_point = v.point()
                    self.snap_marker.setVisible(True)
                elif snap_type == 2:  # Kursor nad linią marszruty
                    self.snap_marker.movePoint(e.point(), 0)
                    self.temp_point = e.point()
                    self.snap_marker.setVisible(True)
                else:
                    self.snap_marker.setVisible(False)
                    self.temp_point = map_point
            else:
                self.snap_marker.setVisible(False)
                self.temp_point = map_point
            if self.temp_rb and self.drawing:
                self.temp_rb.movePoint(self.temp_point)

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = self.toMapCoordinates(event.pos())

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:  # Zakończenie panningu mapy
                self.cursor = "cross"
                self.canvas.panActionEnd(event.pos())
                self.dragging = False
                return
            if not self.drawing:  # Rozpoczęcie rysowania
                self.drawing_start()
            self.vertex_add(event.pos())
        elif event.button() == Qt.RightButton:
            if self.rb.numberOfVertices() > 1:
                self.accepted = True
                self.accept_changes()
            else:
                self.canceled = True
                self.accept_changes(cancel=True)

    def keyReleaseEvent(self, event):
        if self.drawing and not self.dragging and event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.last_vertex_remove()
            event.ignore()
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.rb.numberOfVertices() > 1:
                self.accepted = True
                self.accept_changes()
            else:
                self.canceled = True
                self.accept_changes(cancel=True)
        if event.key() == Qt.Key_Escape:
            self.canceled = True
            self.accept_changes(cancel=True)

    def geom_load(self, geom):
        """Ładuje geometrię liniową do rubberband'ów."""
        self.drawing_start()
        p_list = list(geom.vertices())
        for i in range(len(p_list)):
            node = QgsPointXY(p_list[i].x(), p_list[i].y())
            self.rb.addPoint(node)
            if i == len(p_list) - 1:
                self.temp_rb.addPoint(node)

    def drawing_start(self):
        """Inicjuje rubberband'y do rysowania linii."""
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rb.setWidth(3)
        self.rb.setColor(self.color)
        self.rb.setVisible(True)
        self.temp_rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.temp_rb.setWidth(3)
        self.temp_rb.setColor(self.color)
        self.temp_rb.setLineStyle(Qt.DotLine)
        self.temp_rb.setVisible(True)
        self.drawing = True

    def drawing_stop(self):
        """Usuwa rubberband'y ze sceny."""
        if self.rb:
            self.canvas.scene().removeItem(self.rb)
            self.rb = None
        if self.temp_rb:
            self.canvas.scene().removeItem(self.temp_rb)
            self.temp_rb = None
        if self.snap_marker:
            self.canvas.scene().removeItem(self.snap_marker)
            self.snap_marker = None
        self.drawing = False
        dlg.proj.mapLayersByName("marszruty")[0].triggerRepaint()

    def vertex_add(self, canvas_pt):
        """Dodaje wierzchołek do linii marszruty i aktualizuje rubberband'y."""
        self.rb.addPoint(self.temp_point)
        self.temp_rb.reset(QgsWkbTypes.LineGeometry)
        self.temp_rb.addPoint(self.temp_point)

    def last_vertex_remove(self):
        """Kasuje ostatnio dodany wierzchołek linii marszruty i aktualizuje rubberband'y."""
        if not self.drawing:
            return
        band_size = self.rb.numberOfVertices()
        temp_band_size = self.temp_rb. numberOfVertices()
        if band_size < 1:
            return
        self.rb.removePoint(-1)
        if band_size > 1:
            if temp_band_size > 1:
                point = self.rb.getPoint(0, band_size - 2)
                self.temp_rb.movePoint(temp_band_size - 2, point)
        else:
            self.temp_rb.reset(QgsWkbTypes.LineGeometry)

    def accept_changes(self, cancel=False, deactivated=False):
        """Zakończenie edycji geometrii i zaakceptowanie wprowadzonych zmian, albo przywrócenie stanu pierwotnego."""
        if self.rb:
            if self.rb.numberOfVertices() > 1 and not cancel and not deactivated:
                self.geom = self.rb.asGeometry()
        self.drawing_stop()
        if self.init_extent:
            self.canvas.setExtent(self.init_extent)
        self.accepted = True
        self.drawn.emit(self.geom, self.id, cancel, deactivated)

    def deactivate(self):
        """Zakończenie działania maptool'a."""
        super().deactivate()
        if not self.accepted:
            self.accept_changes(deactivated=True)


class PolyDrawMapTool(QgsMapTool):
    """Maptool do rysowania obiektów poligonalnych."""
    cursor_changed = pyqtSignal(str)
    valid_changed = pyqtSignal(bool)
    drawn = pyqtSignal(object)

    def __init__(self, canvas, button, extra):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self._button = button
        self.color = QColor(extra[0][0], extra[0][1], extra[0][2], extra[0][3])
        self.fillcolor = QColor(extra[1][0], extra[1][1], extra[1][2], extra[1][3])
        if not self._button.isChecked():
            self._button.setChecked(True)
        self.area_painter = None
        self.node_valider = None
        self.drawing = False
        self.dragging = False
        self.refreshing = False
        self.start_point = None
        self.change_is_valid = True
        self.valid_changed.connect(self.valid_change)
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "cross"
        self.rbs_create()

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)
        if attr == "change_is_valid":
            self.valid_changed.emit(val)

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        self.area_painter = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.area_painter.setColor(self.color)
        self.area_painter.setFillColor(self.fillcolor)
        self.area_painter.setWidth(1)
        self.area_painter.setVisible(False)

        self.node_valider = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.node_valider.setIcon(QgsRubberBand.ICON_FULL_DIAMOND)
        self.node_valider.setColor(QColor(255, 0, 0, 255))
        self.node_valider.setFillColor(QColor(0, 0, 0, 255))
        self.node_valider.setIconSize(12)
        self.node_valider.setVisible(False)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor],
                    ["cross", Qt.CrossCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def valid_change(self, _bool):
        """Zmiana poprawności geometrii rubberband'a w trakcie rysowania area_painter'a."""
        self.area_painter.setFillColor(self.fillcolor) if _bool else self.area_painter.setFillColor(QColor(0, 0, 0, 80))

    def canvasMoveEvent(self, event):
        map_point = self.toMapCoordinates(event.pos())
        if event.buttons() == Qt.LeftButton and not self.refreshing:
            if self.drawing:
                # Umożliwienie panningu mapy podczas rysowania area_painter'a:
                dist = QgsGeometry().fromPointXY(self.start_point).distance(QgsGeometry().fromPointXY(map_point))
                dist_scale = dist / self.canvas.scale() * 1000
                if dist_scale > 6.0:
                    self.dragging = True
                    self.cursor = "closed_hand"
                    self.canvas.panAction(event)
            elif not self.drawing:
                # Panning mapy:
                self.dragging = True
                self.cursor = "closed_hand"
                self.canvas.panAction(event)
        elif event.button() == Qt.NoButton or self.refreshing:
            if self.refreshing:
                self.mouse_move_emit(True)
                self.refreshing = False
            if self.drawing and not self.dragging and self.area_painter.numberOfVertices() > 0:
                # Odświeżenie area_painter:
                self.area_painter.removeLastPoint(0)
                self.area_painter.addPoint(map_point)
                # Sprawdzenie, czy aktualna geometria area_painter'a i topologia z innymi poligonami są poprawne:
                if self.area_painter.numberOfVertices() > 2:
                    self.valid_check()

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = self.toMapCoordinates(event.pos())
            if not self.drawing:
                self.drawing = True
                self.change_is_valid = True
            self.area_painter.addPoint(self.toMapCoordinates(event.pos()))

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            # Zakończenie panningu mapy:
            if self.drawing and self.area_painter.numberOfVertices() > 0:
                self.area_painter.removeLastPoint(0)
                self.cursor = "cross"
            self.canvas.panActionEnd(event.pos())
            self.dragging = False
        elif event.button() == Qt.RightButton:
            self.area_painter.removeLastPoint(0)
            if self.area_painter.numberOfVertices() > 2:
                self.valid_check()
                self.drawn.emit(self.area_painter.asGeometry()) if self.change_is_valid else self.drawn.emit(None)
                self.reset()
            else:
                self.reset()
                self.drawn.emit(None)

    def keyReleaseEvent(self, event):
        if self.drawing and not self.dragging and self.area_painter.numberOfVertices() > 1 and (event.matches(QKeySequence.Undo) or event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace):
            # Usunięcie ostatnio narysowanego wierzchołka area_painter'a:
            self.area_painter.removeLastPoint()
            self.mouse_move_emit()
        if event.key() == Qt.Key_Escape:
            # Przerwanie rysowania i wyłączenie maptool'a
            self.reset()
            self.drawn.emit(None)

    def mouse_move_emit(self, after=False):
        """Sposób na odpalenie canvasMoveEvent."""
        cursor = QCursor()
        pos = self.canvas.mouseLastXY()
        global_pos = self.canvas.mapToGlobal(pos)
        if after:
            # Przywrócenie pierwotnej pozycji kursora:
            cursor.setPos(global_pos.x() + 2, global_pos.y() + 2)
        else:
            # Nieznaczne przesunięcie kursora, żeby odpalić canvasMoveEvent:
            self.refreshing = True
            cursor.setPos(global_pos.x(), global_pos.y())

    def valid_check(self):
        """Sprawdza, czy geometria area_painter'a jest prawidłowa."""
        is_valid = True  # Wstępne założenie, że geometria jest poprawna
        # Kasowanie poprzedniego stanu node_valider'a:
        self.node_valider.reset(QgsWkbTypes.PointGeometry)
        # Przygotowanie geometrii valid_checker'a:
        rb_geom = self.area_painter.asGeometry()
        nodes = self.get_nodes_from_area_rb(rb_geom)
        # Sprawdzenie, czy nowa geometria jest poprawna:
        rb_check = self.rubberband_check(rb_geom)
        if not rb_check:  # Nowa geometria nie jest poprawna - pokazanie błędnych punktów
            # Stworzenie listy z wierzchołkami valid_checker'a:
            rb_nodes = []
            for node in nodes:
                rb_nodes.append(QgsPointXY(node.x(), node.y()))
            # Stworzenie listy z liniami boków valid_checker'a:
            segments = self.segments_from_polygon(rb_geom)
            # Sprawdzenie, czy któreś linie się przecinają -
            # wykluczone są przecięcia na wierzchołkach:
            pairs = list(combinations(segments, 2))
            for p in pairs:
                intersect_geom = p[0].intersection(p[1])
                if intersect_geom and intersect_geom.type() == QgsWkbTypes.PointGeometry:
                    if not intersect_geom.asPoint() in rb_nodes:
                        # Pokazanie błędnych przecięć:
                        self.node_valider.addPoint(intersect_geom.asPoint())
            is_valid = False
        self.change_is_valid = is_valid

    def rubberband_check(self, geom):
        """Zwraca geometrię, jesli jest poprawna."""
        return geom if geom.isGeosValid() else None

    def get_nodes_from_area_rb(self, rb):
        """Zwraca punkty z poligonalnego rubberband'u."""
        pts = []
        for vertex in rb.vertices():
            pts.append(vertex)
        return pts

    def segments_from_polygon(self, poly):
        """Zwraca listę boków poligonu."""
        segments = []
        poly = poly.asPolygon()[0]
        for i in range(len(poly) - 1):
            line = QgsGeometry().fromPolylineXY([poly[i], poly[i + 1]])
            segments.append(line)
        return segments

    def reset(self):
        self.rbs_clear()

    def deactivate(self):
        self.rbs_clear()

    def rbs_clear(self):
        """Wyczyszczenie zawartości i usunięcie rubberband'ów."""
        if self.node_valider:
            self.node_valider.reset(QgsWkbTypes.PointGeometry)
            self.node_valider = None
        if self.area_painter:
            self.area_painter.reset(QgsWkbTypes.PolygonGeometry)
            self.area_painter = None


class RulerMapTool(QgsMapTool):
    """Maptool do odmierzania odległości."""
    measured = pyqtSignal(int, object)
    cursor_changed = pyqtSignal(str)

    def __init__(self, canvas, lyr, button):
        QgsMapTool.__init__(self, canvas)
        dlg.wyr_panel.mt_enabled = True
        self.canvas = canvas
        self._button = button
        self.accepted = False
        self.canceled = False
        self.deactivated = False
        self.rb_point = None
        self.rb_line = None
        self.rb_halo = None
        self.pan_point = None
        self.temp_point = None
        self.drawing = False
        self.dragging = False
        self.layer = dlg.proj.mapLayersByName(lyr[0])[0]
        self.cursor_changed.connect(self.cursor_change)
        self.cursor = "cross"
        self.rbs_create()

    def rbs_create(self):
        """Stworzenie rubberband'ów."""
        self.rb_point = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.rb_point.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.rb_point.setColor(QColor(255, 255, 255, 255))
        self.rb_point.setFillColor(QColor(0, 0, 255, 255))
        self.rb_point.setIconSize(8)
        self.rb_point.addPoint(QgsPointXY(0, 0), False)
        self.rb_point.setVisible(True)

    def button(self):
        return self._button

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cursor":
            self.cursor_changed.emit(val)

    def cursor_change(self, cur_name):
        """Zmiana cursora maptool'a."""
        cursors = [
                    ["cross", Qt.CrossCursor],
                    ["open_hand", Qt.OpenHandCursor],
                    ["closed_hand", Qt.ClosedHandCursor]
                ]
        for cursor in cursors:
            if cursor[0] == cur_name:
                self.setCursor(cursor[1])
                break

    def snap_to_layer(self, event, layer):
        """Zwraca wyniki przyciągania do wierzchołków i krawędzi."""
        self.canvas.snappingUtils().setCurrentLayer(layer)
        e = self.canvas.snappingUtils().snapToCurrentLayer(event.pos(), QgsPointLocator.Edge)
        return e

    @threading_func
    def find_nearest_feature(self, pos):
        """Zwraca najbliższy od kursora obiekt na wybranych warstwach."""
        pos = self.toLayerCoordinates(self.layer, pos)
        scale = iface.mapCanvas().scale()
        tolerance = scale / 250
        search_rect = QgsRectangle(pos.x() - tolerance,
                                  pos.y() - tolerance,
                                  pos.x() + tolerance,
                                  pos.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(search_rect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        for feat in self.layer.getFeatures(request):
            return self.layer

    def canvasMoveEvent(self, event):
        map_point = self.toMapCoordinates(event.pos())
        if event.buttons() == Qt.LeftButton:
            if self.drawing:
                # Umożliwienie panningu mapy podczas rysowania:
                dist = QgsGeometry().fromPointXY(self.pan_point).distance(QgsGeometry().fromPointXY(map_point))
                dist_scale = dist / self.canvas.scale() * 1000
                if dist_scale > 6.0:
                    self.dragging = True
                    self.cursor = "closed_hand"
                    self.canvas.panAction(event)
            elif not self.drawing:
                # Panning mapy:
                self.dragging = True
                self.cursor = "closed_hand"
                self.canvas.panAction(event)
        if event.buttons() == Qt.NoButton:
            if self.cursor != "cross":
                self.cursor = "cross"
            th = self.find_nearest_feature(event.pos())
            result = th.get()
            snap_type = None
            if result:
                e = self.snap_to_layer(event, result)
                snap_type = e.type()
                if snap_type == 2:  # Kursor nad linią marszruty
                    self.temp_point = e.point()
                else:
                    self.temp_point = map_point
                if self.rb_point:
                    self.rb_point.movePoint(self.temp_point)
            else:
                self.temp_point = map_point
                if self.rb_point:
                    self.rb_point.movePoint(self.temp_point)
            if self.rb_line and self.drawing:
                self.rb_line.movePoint(self.temp_point)
                self.rb_halo.movePoint(self.temp_point)

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pan_point = self.toMapCoordinates(event.pos())

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:  # Zakończenie panningu mapy
                self.cursor = "cross"
                self.canvas.panActionEnd(event.pos())
                self.dragging = False
                return
            if not self.drawing:  # Rozpoczęcie rysowania
                self.drawing_start()
                self.vertex_add()
            else:
                self.accepted = True
                self.accept_changes()

    def keyReleaseEvent(self, event):
        if self.drawing and not self.dragging and event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.last_vertex_remove()
        if event.key() == Qt.Key_Escape:
            self.canceled = True
            self.accept_changes(cancel=True)

    def drawing_start(self):
        """Inicjuje rubberband'y do rysowania linii i punktów."""
        self.rb_halo = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rb_halo.setWidth(3)
        self.rb_halo.setColor(QColor(255, 255, 255, 255))
        self.rb_halo.setVisible(True)
        self.rb_line = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rb_line.setWidth(2)
        self.rb_line.setLineStyle(Qt.DotLine)
        self.rb_line.setColor(QColor(0, 0, 255, 255))
        self.rb_line.setVisible(True)
        if self.rb_point:
            self.canvas.scene().removeItem(self.rb_point)
            self.rb_point = None
        self.rbs_create()
        self.rb_point.addPoint(self.temp_point)
        self.drawing = True

    def drawing_stop(self):
        """Usuwa rubberband'y ze sceny."""
        if self.rb_point:
            self.canvas.scene().removeItem(self.rb_point)
            self.rb_point = None
        if self.rb_line:
            self.canvas.scene().removeItem(self.rb_line)
            self.rb_line = None
        if self.rb_halo:
            self.canvas.scene().removeItem(self.rb_halo)
            self.rb_halo = None
        self.drawing = False

    def vertex_add(self):
        """Dodaje wierzchołek do linii i aktualizuje rubberband'y."""
        self.rb_point.addPoint(self.temp_point)
        self.rb_line.addPoint(self.temp_point)
        self.rb_halo.addPoint(self.temp_point)

    def last_vertex_remove(self):
        """Kasuje ostatnio dodany wierzchołek linii i aktualizuje rubberband'y."""
        if not self.drawing:
            return
        self.rb_point.removePoint(-1)
        self.rb_point.movePoint(self.temp_point)
        self.rb_line.removePoint(-1)
        self.rb_halo.removePoint(-1)
        self.drawing = False

    def accept_changes(self, cancel=False, deactivated=False):
        """Zakończenie edycji geometrii i zaakceptowanie wprowadzonych zmian, albo przywrócenie stanu pierwotnego."""
        length = 0
        if self.rb_line:
            if self.rb_line.numberOfVertices() == 2 and not cancel and not deactivated:
                length = int(self.rb_line.asGeometry().length())
        self.drawing_stop()
        self.accepted = True
        if not deactivated:
            dlg.wyr_panel.mt_enabled = False
            self.measured.emit(length, self._button)

    def deactivate(self):
        """Zakończenie działania maptool'a."""
        super().deactivate()
        if not self.accepted:
            dlg.wyr_panel.mt_enabled = False
            self.accept_changes(deactivated=True)
            self._button.sliding(deactivate=True)


# ========== Funkcje:

def obj_sel(layer, feature, loc):
    """Przekazuje do menedżera obiektów dane nowowybranego obiektu (nazwa warstwy i atrybuty obiektu)."""
    if layer:
        dlg.obj.obj_change([layer.name(), feature.attributes()], loc)

def flag_add(point, extra):
    """Utworzenie nowego obiektu flagi."""
    dlg.mt.init("multi_tool")
    if not point:
        return
    is_fchk = extra[0]
    fl_pow = fl_valid(point)
    if not fl_pow:
        QMessageBox.warning(None, "Tworzenie flagi", "Flagę można postawić wyłącznie na obszarze wybranego (aktywnego) powiatu/ów.")
        return
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".flagi(user_id, pow_grp, b_fieldcheck, geom) VALUES (" + str(dlg.user_id) + ", " + str(fl_pow) + ", " + is_fchk + ", ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180))"
    if db:
        res = db.query_upd(sql)
        if not res:
            print("Nie udało się dodać flagi.")
        else:
            # Włączenie tego rodzaju flag, jeśli są wyłączone:
            name = "flagi_z_teren" if is_fchk == "true" else "flagi_bez_teren"
            val = dlg.cfg.get_val(name)
            if val == 0:
                dlg.cfg.set_val(name, 1)
    dlg.proj.mapLayersByName("flagi_bez_teren")[0].triggerRepaint()
    dlg.proj.mapLayersByName("flagi_z_teren")[0].triggerRepaint()
    dlg.obj.flag_ids = get_flag_ids(dlg.cfg.flag_case())  # Aktualizacja listy flag w ObjectManager
    dlg.obj.list_position_check("flag")  # Aktualizacja pozycji na liście obecnie wybranej flagi

def flag_move(point, extra):
    """Zmiana lokalizacji flagi."""
    dlg.mt.init("multi_tool")
    if not point:
        dlg.obj.flag_hide(False)
        return
    fl_pow = fl_valid(point)
    if not fl_pow:
        QMessageBox.warning(None, "Zmiana lokalizacji flagi", "Flagę można postawić wyłącznie na obszarze wybranego (aktywnego) powiatu/ów.")
        dlg.obj.flag_hide(False)
        return
    table = f"team_{str(dlg.team_i)}.flagi"
    bns = f" WHERE id = {dlg.obj.flag}"
    p_pow = point_pow(point)
    pow = f"'{p_pow}'" if p_pow else "Null"
    geom = f"ST_SetSRID(ST_MakePoint({str(point.x())}, {str(point.y())}), 2180)"
    attr_chg = db_attr_change(tbl=table, attr="geom", val=geom, sql_bns=bns, user=False)
    if not attr_chg:
        print("Nie zmieniono lokalizacji flagi")
    attr_chg = db_attr_change(tbl=table, attr="pow_grp", val=pow, sql_bns=bns, user=False)
    if not attr_chg:
        print("Nie zaktualizowano powiatu flagi")
    dlg.obj.flag_hide(False)

def fl_valid(point):
    """Sprawdzenie, czy flaga znajduje się wewnątrz wybranego powiatu/ów."""
    db = PgConn()
    if dlg.p_pow.is_active():  # Tryb pojedynczego powiatu
        sql = "SELECT p.pow_grp FROM team_" + str(dlg.team_i) + ".powiaty AS p WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180), p.geom) AND p.pow_grp = '" + str(dlg.powiat_i) + "';"
    else:
        sql = "SELECT p.pow_grp FROM team_" + str(dlg.team_i) + ".powiaty AS p WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180), p.geom);"
    if db:
        res = db.query_sel(sql, False)
        if res:
            return res[0]

def area_measure(geom):
    """Zwraca zaokrągloną wartość powierzchni wyrobiska w metrach kwadratowych."""
    try:
        area = geom.area()
    except Exception as err:
        print(f"Nie udało się obliczyć powierzchni wyrobiska: {err}")
        return 0
    area_rounded = int(round(area / 10, 0) * 10) if area <= 1000 else int(round(area / 100, 0) * 100)
    return area_rounded

def wyr_point_add(point):
    """Utworzenie centroidu nowego obiektu wyrobiska."""
    if isinstance(point, QgsGeometry):
        point = point.asPoint()
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".wyrobiska(wyr_id, user_id, wyr_sys, centroid) SELECT nextval, " + str(dlg.user_id) + ", concat('" + str(dlg.team_i) + "_', nextval), ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180) FROM (SELECT nextval(pg_get_serial_sequence('team_" + str(dlg.team_i) + ".wyrobiska', 'wyr_id')) nextval) q RETURNING wyr_id"
    if db:
        res = db.query_upd_ret(sql)
        if not res:
            print(f"Nie udało się stworzyć centroidu wyrobiska.")
            return None
        else:
            # Włączenie wyrobisk przed kontrolą terenową, jeśli są wyłączone:
            val = dlg.cfg.get_val("wyr_przed_teren")
            if val == 0:
                dlg.cfg.set_val("wyr_przed_teren", 1)
            return res

def wyr_add_poly(geom, wyr_id=None):
    """Utworzenie nowego obiektu wyrobiska."""
    dlg.mt.init("multi_tool")
    if not geom:
        return
    lyr_poly = dlg.proj.mapLayersByName("wyr_poly")[0]
    fields = lyr_poly.fields()
    feature = QgsFeature()
    feature.setFields(fields)
    feature.setGeometry(geom)
    if not wyr_id:
        wyr_id = wyr_point_add(geom.centroid())
        if not wyr_id:
            return
    feature.setAttribute('wyr_id', wyr_id)
    with edit(lyr_poly):
        try:
            lyr_poly.addFeature(feature)
        except Exception as err:
            print(f"maptools/wyr_add_poly: {err}")
            return
    lyr_poly.triggerRepaint()
    wyr_powiaty_change(wyr_id, geom, new=True)
    wyr_add_dane(wyr_id)
    wyr_point_update(wyr_id, geom)
    dlg.obj.wyr_ids = get_wyr_ids()  # Aktualizacja listy wyrobisk w ObjectManager
    dlg.obj.list_position_check("wyr")  # Aktualizacja pozycji na liście obecnie wybranego wyrobiska

def wyr_add_dane(wyr_id):
    """Tworzy rekord dla nowego wyrobiska w tabeli 'wyr_dane' i uzupełnia atrybut i_area_m2."""
    db = PgConn()
    sql = f"INSERT INTO team_{dlg.team_i}.wyr_dane(wyr_id) VALUES ({wyr_id})"
    if db:
        res = db.query_upd(sql)
        if not res:
            print("Nie udało się dodać rekordu w tabeli 'wyr_dane'.")

def wyr_point_update(wyr_id, geom):
    """Aktualizacja punktowego obiektu wyrobiska."""
    # Aktualizacja warstw z wyrobiskami:
    wyr_layer_update(False)
    # Aktualizacja bieżącego punktu wyrobiska:
    temp_lyr = False
    lyr_point = dlg.proj.mapLayersByName("wyr_point")[0]
    area = area_measure(geom)
    feats = lyr_point.getFeatures(f'"wyr_id" = {wyr_id}')
    try:
        feat = list(feats)[0]
    except Exception as err:
        print(f"maptools/wyr_point_update[0]: {err}")
        print("Geometria wyrobiska leży poza aktywnymi powiatami?")
        dlg.obj.wyr = None
        # Stworzenie tymczasowej warstwy ze wszystkimi punktami wyrobisk zespołu:
        temp_lyr = True
        with CfgPars() as cfg:
            params = cfg.uri()
        table = '"team_' + str(dlg.team_i) + '"."wyrobiska"'
        uri = f'{params} table={table} (centroid) sql='
        lyr_point = QgsVectorLayer(uri, "temp_wyr_point", "postgres")
        feats = lyr_point.getFeatures(f'"wyr_id" = {wyr_id}')
        try:
            feat = list(feats)[0]
        except Exception as err:
            print(f"maptools/wyr_point_update[1]: {err}")
            print(f"Nieudana próba aktualizacji wyrobiska {wyr_id}")
            del lyr_point
            return
    with edit(lyr_point):
        feat.setGeometry(geom.centroid())
        try:
            lyr_point.updateFeature(feat)
        except Exception as err:
            print(f"maptools/wyr_point_update[2]: {err}")
    db_attr_change(tbl=f"team_{dlg.team_i}.wyr_dane", attr="i_area_m2", val=area, sql_bns=f" WHERE wyr_id = {wyr_id}", user=False)
    wyr_point_lyrs_repaint()
    if temp_lyr:
        del lyr_point
    dlg.wyr_panel.wn_df = pd.DataFrame(columns=dlg.wyr_panel.wn_df.columns)  # Wyczyszczenie dataframe'a z połączeniami wyrobiska-wn_pne
    dlg.obj.wyr = dlg.obj.wyr  # Aktualizacja danych wyrobiska

def wyr_point_lyrs_repaint():
    """Odświeża widok punktowych warstw wyrobisk."""
    lyrs_names = ['wyr_przed_teren', 'wyr_potwierdzone', 'wyr_odrzucone', 'wyr_point']
    for lyr_name in lyrs_names:
        dlg.proj.mapLayersByName(lyr_name)[0].triggerRepaint()

def parking_add(point, extra):
    """Utworzenie nowego obiektu parkingu."""
    dlg.mt.init("multi_tool")
    if not point:
        return
    p_pow = point_pow(point)
    if not p_pow:
        p_pow = "Null"
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".parking(user_id, pow_grp, i_status, geom) VALUES (" + str(dlg.user_id) + ", " + str(p_pow) + ", 0, ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180))"
    if db:
        res = db.query_upd(sql)
        if not res:
            print("Nie udało się dodać parkingu.")
        else:
            # Włączenie tego rodzaju parkingu, jeśli są wyłączone:
            val = dlg.cfg.get_val("parking_planowane")
            if val == 0:
                dlg.cfg.set_val("parking_planowane", 1)
    dlg.proj.mapLayersByName("parking_planowane")[0].triggerRepaint()
    dlg.proj.mapLayersByName("parking_odwiedzone")[0].triggerRepaint()
    dlg.obj.parking_ids = get_parking_ids(dlg.cfg.parking_case())  # Aktualizacja listy parkingów w ObjectManager
    dlg.obj.list_position_check("parking")  # Aktualizacja pozycji na liście obecnie wybranego parkingu

def parking_move(point, extra):
    """Zmiana lokalizacji parkingu."""
    dlg.mt.init("multi_tool")
    if not point:
        dlg.obj.parking_hide(False)
        return
    p_pow = point_pow(point)
    table = f"team_{str(dlg.team_i)}.parking"
    bns = f" WHERE id = {dlg.obj.parking}"
    geom = f"ST_SetSRID(ST_MakePoint({str(point.x())}, {str(point.y())}), 2180)"
    pow = f"'{p_pow}'" if p_pow else "Null"
    attr_chg = db_attr_change(tbl=table, attr="geom", val=geom, sql_bns=bns, user=False)
    if not attr_chg:
        print("Nie zmieniono lokalizacji parkingu")
    attr_chg = db_attr_change(tbl=table, attr="pow_grp", val=pow, sql_bns=bns, user=False)
    if not attr_chg:
        print("Nie zaktualizowano powiatu parkingu")
    dlg.obj.parking_hide(False)
    parking_layer_update()

def point_pow(point):
    """Zwraca numer powiatu, na którym występuje obiekt."""
    db = PgConn()
    sql = "SELECT p.pow_grp FROM team_" + str(dlg.team_i) + ".powiaty AS p WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(" + str(point.x()) + ", " + str(point.y()) + "), 2180), p.geom);"
    if db:
        res = db.query_sel(sql, False)
        if res:
            return res[0]

def marsz_add(geom, _id, cancel, deactivated):
    """Utworzenie nowego obiektu marszruty."""
    lyr_line = dlg.proj.mapLayersByName("marszruty")[0]
    if _id:
        # Linia marszruty była kontynuowana - trzeba ją zaktualizować, nie dodawać
        marsz_line_change(lyr_line, geom, _id, deactivated)
        return
    if not deactivated:
        dlg.mt.init("multi_tool")
    if not geom:
        return
    marsz_m = length_measure(geom)
    marsz_t = length_time(marsz_m)
    db = PgConn()
    sql = f"INSERT INTO team_{dlg.team_i}.marsz(marsz_id, user_id, marsz_m, marsz_t, geom) SELECT nextval, {dlg.user_id}, {marsz_m}, {marsz_t}, ST_SetSRID(ST_GeomFromText('{geom.asWkt()}'), 2180) FROM (SELECT nextval(pg_get_serial_sequence('team_{dlg.team_i}.marsz', 'marsz_id')) nextval) q RETURNING marsz_id"
    if db:
        res = db.query_upd_ret(sql)
        if not res:
            print(f"Nie udało się stworzyć marszruty.")
        else:
            # Włączenie warstwy z marszrutami, jeśli jest wyłączona:
            val = dlg.cfg.get_val("marszruty")
            if val == 0:
                dlg.cfg.set_val("marszruty", 1)
    marsz_powiaty_change(res, geom, new=True)
    dlg.obj.marsz_ids = get_marsz_ids()  # Aktualizacja listy marszrut w ObjectManager
    marsz_layer_update()

def length_measure(geom):
    """Zwraca zaokrągloną wartość długości marszruty w metrach."""
    length = geom.length()
    length_rounded = int(round(length / 10, 0)) * 10 if length <= 1000 else int(round(length / 100, 0) * 100)
    return length_rounded

def length_time(length):
    """Zwraca zaokrągloną wartość czasu przejścia marszruty w sekundach."""
    time = length * 3600 / 4500
    return int(round(time, 0))

def marsz_del(layer, feature):
    """Usunięcie wybranego obiektu marszruty."""
    dlg.mt.init("multi_tool")
    if layer:
        fid = feature.attributes()[layer.fields().indexFromName('marsz_id')]
    else:
        return
    db = PgConn()
    sql = "DELETE FROM team_" + str(dlg.team_i) + ".marsz WHERE marsz_id = " + str(fid) + ";"
    if db:
        res = db.query_upd(sql)
        if not res:
            print("Nie udało się usunąć marszruty.")
    dlg.proj.mapLayersByName("marszruty")[0].triggerRepaint()

def lyr_ref(lyr):
    """Zwraca referencje warstw na podstawie ich nazw."""
    layer = []
    for l in lyr:
        layer.append(dlg.proj.mapLayersByName(l)[0])
    return layer

def wyr_poly_change(lyr, geom):
    dlg.mt.init("multi_tool")
    if not geom:
        return
    wyr_id = dlg.obj.wyr
    feats = lyr.getFeatures(f'"wyr_id" = {wyr_id}')
    try:
        feat = list(feats)[0]
    except Exception as err:
        print(err)
        print(f"Tworzenie wpisu w 'pow_geom' dla wyrobiska {wyr_id}")
        wyr_add_poly(geom, wyr_id)
        return
    with edit(lyr):
        feat.setGeometry(geom)
        try:
            lyr.updateFeature(feat)
        except Exception as err:
            print(err)
            return
    wyr_powiaty_change(wyr_id, geom)
    wyr_point_update(wyr_id, geom)

def marsz_line_change(lyr, geom, marsz_id, deactivated=False):
    if not deactivated:
        dlg.mt.init("multi_tool")
    if not geom or not marsz_id:
        return
    feats = lyr.getFeatures(f'"marsz_id" = {marsz_id}')
    try:
        feat = list(feats)[0]
    except Exception as err:
        print(err)
        marsz_add(geom)
        return
    with edit(lyr):
        marsz_m = length_measure(geom)
        marsz_t = length_time(marsz_m)
        feat.setAttribute('marsz_m', marsz_m)
        feat.setAttribute('marsz_t', marsz_t)
        feat.setGeometry(geom)
        try:
            lyr.updateFeature(feat)
        except Exception as err:
            print(err)
            return
    marsz_powiaty_change(marsz_id, geom)
    marsz_layer_update()

def marsz_line_continue(lyr, geom, marsz_id, init_extent, cancel=False, deactivated=False):
    if not cancel and not deactivated:
        dlg.mt.init("marsz_add", [marsz_id, geom, init_extent])
    else:
        marsz_line_change(lyr, geom, marsz_id, deactivated)

def wn_pick(layer, feature):
    dlg.mt.init("multi_tool")
    if not feature:
        return
    dlg.wyr_panel.wn_picker.wn_id_update(feature["id_arkusz"])

def ruler_meas(length, button):
    dlg.mt.init("multi_tool")
    button.sliding()
    if length == 0:
        return
    elif length <= 10:
        length_rounded = length
    elif length < 50:  # Zaokrąglanie co 5
        length_rounded = int(math.floor((length + 2.5) / 5) * 5)
    else:
        length_rounded = int(round(length / 10, 0) * 10)
    button.parent().value_change(length_rounded)
