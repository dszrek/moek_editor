# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QMessageBox
from PyQt5.QtGui import QColor
from qgis.core import QgsProject
from qgis.utils import iface

from .classes import PgConn
from .main import block_panels
from .widgets import MoekButton, MoekCheckBox, MoekStackedBox, MoekCfgHSpinBox
from .sequences import db_sequence_reset, sequences_load

dlg = None

def dlg_basemaps(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

def basemaps_load():
    """Wczytanie ustawień użytkownika dotyczących podkładów mapowych."""
    # print("[basemaps_load]")
    if not db_user_has_basemaps():  # Użytkownik nie ma zapisanych ustawień podkładów mapowych w db
        db_create_basemaps()
    db = PgConn()
    # Sprawdzenie, czy w tabeli basemaps z aktywnego teamu znajdują się ustawienia użytkownika:
    sql = "SELECT map_id, t_category, t_map_name, t_layer_1, t_layer_2, b_map_enabled FROM team_" + str(dlg.team_i) + ".basemaps WHERE user_id = " + str(dlg.user_id) + " ORDER BY map_id ASC;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            if not dlg.p_map.loaded:  # Checkbox'y z mapami jeszcze nie istnieją
                for r in res:
                    # Dodanie checkbox'ów z mapami do p_map:
                    if r[1] == "sat" or r[1] == "topo":
                        dlg.p_map.add_checkbox(cat=r[1], name=r[2], enabled=r[5])
                    # Utworzenie listy nazw warstw z podkładami:
                    if r[1] != "snmt":
                        dlg.p_map.layers.append(r[3])
                        if r[4]:  # Dwie warstwy w rekordzie
                            dlg.p_map.layers.append(r[4])
                    # Utworzenie zbiorczej listy podkładów mapowych:
                    dlg.p_map.all.append({"id":r[0], "cat":r[1],"name":r[2], "lyr_1":r[3], "lyr_2":r[4], "enabled":r[5]})
                dlg.p_map.loaded = True  # Zapamiętanie, że pobrano dane z db
                dlg.p_map.first_map("sat")  # Wstępne ustawienie podkładu mapowego na pierwszą dostępną pozycję z kategorii "sat"
            else:  # Checkbox'y już istnieją
                dlg.p_map.all.clear()  # Wyczyszczenie poprzedniej listy zbiorczej
                # Aktualizacja parametru setChecked w checkbox'ach:
                for r in res:
                    if r[1] == "sat" or r[1] == "topo":
                        exec('dlg.p_map.widgets["chk_' + r[2] + '"].setChecked(r[5])')
                    # Utworzenie zbiorczej listy podkładów mapowych:
                    dlg.p_map.all.append({"id":r[0], "cat":r[1],"name":r[2], "lyr_1":r[3], "lyr_2":r[4], "enabled":r[5]})
        else:
            print("Nie udało się wczytać ustawień basemaps użytkownika do list checkbox'ów!")

def db_user_has_basemaps():
    """Sprawdzenie, czy w tabeli basemaps z aktywnego teamu znajdują się ustawienia zalogowanego użytkownika."""
    # print("[db_user_has_basemaps]")
    db = PgConn()
    sql = "SELECT map_id FROM team_" + str(dlg.team_i) + ".basemaps WHERE user_id = " + str(dlg.user_id) + ";"
    if db:
        res = db.query_sel(sql, False)
        if res:
            return True
        else:
            print("W tabeli basemaps nie ma rekordów użytkownika.")
            return False

def db_create_basemaps():
    """Utworzenie dla użytkownika ustawień basemap w tabeli basemaps."""
    # print("[db_create_basemaps]")
    db = PgConn()
    sql = "INSERT INTO team_" + str(dlg.team_i) + ".basemaps(user_id, map_id, t_category, t_map_name, t_layer_1, t_layer_2, b_map_enabled) SELECT " + str(dlg.user_id) + ", map_id, t_category, t_map_name, t_layer_1, t_layer_2, true FROM public.basemaps"
    if db:
        res = db.query_upd(sql)
        if res:
            print("Dodano ustawienia użytkownika do tabeli basemaps.")

def db_basemaps_update(list):
    """Aktualizacja b_map_enabled w tabeli basemaps po zmianie checkbox'ów"""
    # print("[db_basemaps_update]")
    db = PgConn()
    sql = "UPDATE team_" + str(dlg.team_i) + ".basemaps AS bm SET b_map_enabled = d.b_map_enabled FROM (VALUES %s) AS d (t_map_name, b_map_enabled) WHERE bm.t_map_name = d.t_map_name AND bm.user_id = " + str(dlg.user_id) + ";"
    if db:
        db.query_exeval(sql, list)


class MoekMapPanel(QFrame):
    """Panel zarządzający wyświetalniem podkładów mapowych."""
    map_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("mappnl")
        shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setStyleSheet("""
                    QFrame#mappnl {background-color: white; border: none; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-top-right-radius: 22px; border-bottom-right-radius: 16px}
                    QFrame#box {background-color: transparent; border: none}
                    """)
        self.widgets = {}
        self.btns = MoekMapButtons(self)
        self.box = MoekStackedBox(self)
        self.box.setObjectName("box")
        self.box.pages = {}
        for p in range(3):
            _page = MoekMapsBox(self) if p > 0 else MoekCfgHSpinBox(self)
            page_id = f'page_{p}'
            self.box.pages[page_id] = _page
            self.box.addWidget(_page)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(6, 6, 6, 6)
        vlay.setSpacing(0)
        vlay.addWidget(self.btns)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        exit_btn_1 = MoekButton(self, name="exit")
        exit_btn_1.clicked.connect(self.exit_clicked)
        self.box.pages["page_1"].glay.addWidget(exit_btn_1, 0, 1, 1, 1)
        exit_btn_2 = MoekButton(self, name="exit")
        exit_btn_2.clicked.connect(self.exit_clicked)
        self.box.pages["page_2"].glay.addWidget(exit_btn_2, 0, 1, 1, 1)
        self.cat = ""
        self.map = int()
        self.loaded = False
        self.ge = False
        self.layers = []
        self.all = []
        self.map_changed.connect(self.map_change)
        self.sat_cnt = int()
        self.topo_cnt = int()

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "map":
            self.map_changed.emit(val)

    def map_change(self):
        """Zmiana podkładu mapowego."""
        self.cat_change()  # Zmiana kategorii, jeśli potrzebna
        # Zmiana wyświetlanego w spinbox'ie tytułu podkładu mapowego:
        self.box.pages["page_0"].label.setText(self.map_attr(self.map)["name"])
        if self.map == 6 or self.map == 11:  # Włączenie warstwy "Google Earth Pro"
            if not self.ge:
                # iface.mapCanvas().extentsChanged.connect(dlg.ge.extent_changed)
                dlg.ge.visible_changed(True)
                self.ge = True
                # print("warstwa GEP włączona")
        else:
            if self.ge:
                # iface.mapCanvas().extentsChanged.disconnect(dlg.ge.extent_changed)
                dlg.ge.visible_changed(False)
                self.ge = False
                # print("warstwa GEP wyłączona")
        # Ustawienie widoczności warstw z podkładami mapowymi:
        for layer in self.layers:
            if layer == self.map_attr(self.map)["lyr_1"] or layer == self.map_attr(self.map)["lyr_2"]:
                dlg.proj.layerTreeRoot().findLayer(dlg.proj.mapLayersByName(layer)[0].id()).setItemVisibilityChecked(True)
            else:
                dlg.proj.layerTreeRoot().findLayer(dlg.proj.mapLayersByName(layer)[0].id()).setItemVisibilityChecked(False)

    def cat_change(self):
        """Dostosowanie wiget'ów panelu mapowego do zmiany bieżącej kategorii."""
        if self.cat == self.map_attr(self.map)["cat"]:  # Kategoria się nie zmieniła
            return
        self.cat = self.map_attr(self.map)["cat"]  # Zmiana kategorii
        self.btns_update()  # Zmiana wyglądu przycisków
        self.spb_update()  # Aktualizacja spinbox'a

    def map_cnt(self):
        """Zwraca ilość włączonych podkładów mapowych w bieżącej kategorii."""
        return len([map for map in self.all if map["cat"] == self.cat and map["enabled"]])

    def btns_update(self):
        """Ustawienie stanu i wyglądu przycisków mapowych, w zależności od zmienionej kategorii podkładów mapowych."""
        for btn in self.btns.findChildren(MoekMapButton):
            if self.cat == "snmt" and (btn.name == "sat" or btn.name == "nmt"):
                btn.button.setChecked(True)
                btn.line.setVisible(False)
            else:
                val = True if self.cat == btn.name else False
                btn.button.setChecked(val)
                btn.line.setVisible(val)

    def map_attr(self, map_id):
        """Wyszukuje na liście wybrany podkład mapowy i zwraca słownik z jego parametrami."""
        for map in self.all:
            if map["id"] == map_id:
                return map

    def first_map(self, cat):
        """Ustawienie pierwszego dostępnego podkładu mapowego z wybranej kategorii."""
        self.map = [map for map in self.all if map["cat"] == cat and map["enabled"]][0]["id"]

    def spb_update(self):
        """Aktualizacja spinbox'a panelu mapowego."""
        if self.map_cnt() > 1:  # W danej kategorii jest więcej niż jeden podkład mapowy
            self.box.pages["page_0"].label.contract()  # Skrócenie szerokości label'u przed pojawieniem się przycisków
        # Ukrycie lub pokazanie przycisków:
        self.box.pages["page_0"].prev_btn.setVisible(True) if self.map_cnt() > 1 else self.box.pages["page_0"].prev_btn.setVisible(False)
        self.box.pages["page_0"].prev_btn.shown = True if self.map_cnt() > 1 else False
        self.box.pages["page_0"].next_btn.setVisible(True) if self.map_cnt() > 1 else self.box.pages["page_0"].next_btn.setVisible(False)
        self.box.pages["page_0"].next_btn.shown = True if self.map_cnt() > 1 else False
        self.box.pages["page_0"].cfg_btn.setVisible(False) if self.cat == "nmt" else self.box.pages["page_0"].cfg_btn.setVisible(True)
        self.box.pages["page_0"].cfg_btn.shown = False if self.cat == "nmt" else True
        # Dopasowanie marginesów spinbox'a:
        if self.map_cnt() > 1 or self.cat == "nmt":
            self.box.pages["page_0"].hlay.setContentsMargins(0, 0, 0, 0)
        else:
            self.box.pages["page_0"].hlay.setContentsMargins(0, 0, 10, 0)
        self.box.pages["page_0"].label.label_update()  # Aktualizacja label'u spinbox'a

    def prev_map(self):
        """Wyświetlenie poprzedniej w kolejności mapy z bieżącej kategorii."""
        m = self.cur_map() - 1 if self.cur_map() >= 0 else self.map_cnt()
        self.map = [map for map in self.all if map["cat"] == self.cat and map["enabled"]][m]["id"]

    def next_map(self):
        """Wyświetlenie następnej w kolejności mapy z bieżącej kategorii."""
        m = self.cur_map() + 1 if self.cur_map() < self.map_cnt() - 1 else 0
        self.map = [map for map in self.all if map["cat"] == self.cat and map["enabled"]][m]["id"]

    def cur_map(self):
        """Wyświetlenie następnej w kolejności mapy z bieżącej kategorii."""
        maps = [map for map in self.all if map["cat"] == self.cat and map["enabled"]]
        i = 0
        for map in maps:
            if map["id"] == self.map:
                return i
            else:
                i += 1

    def add_checkbox(self, cat, name, enabled):
        """Dodanie checkbox'a do odpowiedniego pojemnika wyboru map."""
        _chk = MoekCheckBox(self, name=name, checked=enabled)
        if cat == "sat":
            page = 1
            self.sat_cnt += 1
            row = self.sat_cnt - 1
        elif cat == "topo":
            page = 2
            self.topo_cnt += 1
            row = self.topo_cnt - 1
        exec('self.box.pages["page_' + str(page) + '"].glay.addWidget(_chk, ' + str(row) + ', 0, 1, 1)')
        chk_name = f'chk_{name}'
        self.widgets[chk_name] = _chk

    def cfg_clicked(self):
        """Wejście do ustawień wyboru map z aktywnej kategorii."""
        self.box.setCurrentIndex(1) if self.cat == "sat" or self.cat == "snmt" else self.box.setCurrentIndex(2)
        block_panels(self, True)  # Zablokowanie pozostałych paneli na czas wyboru map
        dlg.p_map.btns.setEnabled(False)  # Zablokowanie przycisków z p_map
        dlg.p_vn.widgets["sqb_seq"].num = 0  # Deaktywacja sekwencji
    
    def exit_clicked(self):
        """Wyjście z ustawień wyboru map z aktywnej kategorii."""
        m_list = []
        blokada = True  # Zabezpieczenie przed odznaczeniem wszystkich map z kategorii (musi być przynajmniej jedna)
        if self.cat == "sat" or self.cat == "snmt":
            layout = self.box.pages["page_1"].glay
            add_nmt = True
        else:
            layout = self.box.pages["page_2"].glay
            add_nmt = False
        w_idx = layout.count()
        while w_idx > 0:
            w_idx -= 1
            widget = layout.itemAt(w_idx).widget()
            if isinstance(widget, MoekCheckBox):
                if widget.isChecked() and blokada:
                    blokada = False
                m_list.append((widget.text(), widget.isChecked()))
                if add_nmt:  # Uwzględnienie w modyfikacjach kategorii "snmt"
                    m_list.append((widget.text() + " + ISOK", widget.isChecked()))
        if blokada:
            QMessageBox.warning(None, "Podkłady mapowe", "Zmiany nie zostały wprowadzone. Przynajmniej jedna mapa musi pozostać zaznaczona.")
            basemaps_load()  # Ponowne wczytanie wartości checkbox'ów
        else:
            # Podkłady, które zostają wyłączone:
            out_maps = [all["id"] for m in m_list for all in dlg.p_map.all if m[0] == all["name"] and not m[1]]
            # Ustalenie podkładów, które występują w sekwencjach:
            seq1_maps = [m[0] for m in dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_1"].maps]
            seq2_maps = [m[0] for m in dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_2"].maps]
            seq3_maps = [m[0] for m in dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_3"].maps]
            seq1_out = [i for i in seq1_maps if i  in out_maps]
            seq2_out = [i for i in seq2_maps if i  in out_maps]
            seq3_out = [i for i in seq3_maps if i  in out_maps]
            del1 = True if len(seq1_out) > 0 else False
            del2 = True if len(seq2_out) > 0 else False
            del3 = True if len(seq3_out) > 0 else False
            if del1 or del2 or del3:  # W ktorejś sekwencji zostaną usunięte podkłady
                m_text = f"Próbujesz wyłączyć podkład, który jest częścią sekwencji. Naciśnięcie Tak spowoduje wyczyszczenie tej sekwencji."
                reply = QMessageBox.question(iface.mainWindow(), "Kontynuować?", m_text, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    dlg.p_vn.bar.cfg_btn.setChecked(True)
                    return
                if del1:
                    db_sequence_reset(1)
                if del2:
                    db_sequence_reset(2)
                if del2:
                    db_sequence_reset(3)
                sequences_load()
            block_panels(self, False)  # Odblokowanie pozostałych paneli
            dlg.p_map.btns.setEnabled(True)  # Odblokowanie przycisków z p_map
            db_basemaps_update(m_list)  # Aktualizacja b_map_enabled w db
            basemaps_load()  # Ponowne wczytanie wartości checkbox'ów
            # Aktualizacje combobox'ów:
            dlg.p_vn.widgets["sab_seq" + str(1)].combobox_update(1)
            dlg.p_vn.widgets["sab_seq" + str(2)].combobox_update(2)
            dlg.p_vn.widgets["sab_seq" + str(3)].combobox_update(3)
            # Przejście do pierwszej wybranej mapy z aktualnej kategorii:
            self.first_map(self.cat)
            self.spb_update()  # Wymuszenie odświeżenia spinbox'a
            self.box.setCurrentIndex(0)  # Powrót do spinbox'a


class MoekMapButtons(QFrame):
    """Pojemnik z przyciskami panelu mapowego."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(50)
        self.sat_btn = MoekMapButton(self, name="sat", icon="map_sat", tooltip="fotomapy")
        self.nmt_btn = MoekMapButton(self, name="nmt", icon="map_nmt", tooltip="numeryczny model terenu")
        self.topo_btn = MoekMapButton(self, name="topo", icon="map_topo", tooltip="mapy topograficzne")
        self.ge_btn = MoekButton(self, size=50, name="ge", tooltip="pokaż widok mapy w Google Earth Pro")
        self.snmt_btn = MoekMapButton(self, name="snmt", icon="map_snmt", wsize=24, hsize=24, l=18)
        self.ge_btn.clicked.connect(self.ge_clicked)

    def setEnabled(self, value):
        """Ustawienie koloru linii w MoekMapButtons w zależności od parametru setEnabled."""
        super().setEnabled(value)
        mapbtns = self.findChildren(MoekMapButton)
        for mapbtn in mapbtns:
            mapbtn.set_style(True) if value else mapbtn.set_style(False)

    def resizeEvent(self, event):
        """Rozmieszczenie przycisków po zmianie szerokości panelu."""
        super().resizeEvent(event)
        w = self.width()
        w_4 = self.width() / 4
        b = 50
        marg = w_4 - b
        marg_2 = marg / 2
        self.sat_btn.setGeometry(0, 0, b, b)
        self.nmt_btn.setGeometry(w_4 + marg_2, 0, b, b)
        self.topo_btn.setGeometry(2 * w_4 + marg_2, 0, b, b)
        self.ge_btn.setGeometry(3 * w_4 + marg_2, 0, b, b)
        self.snmt_btn.setGeometry(w_4 - 12, 13, 24, 37)

    def ge_clicked(self):
        """Synchronizacja widoku QGIS'a i Google Earth Pro."""
        if dlg.p_map.ge:  # Warstwa z Google Earth Pro jest włączona
            dlg.ge.ge_sync()  # Synchronizacja widoków
        else:
            # print(f"4. q2ge")
            dlg.ge.q2ge(False)  # Pokazanie widoku QGIS'a w Google Earth Pro


class MoekMapButton(QFrame):
    """Przycisk panelu mapowego."""
    def __init__(self, *args, wsize=50, hsize=50, l=31, name="", icon="", checkable=True, tooltip=""):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.l = l
        self.name = name
        self.line = QWidget(self)
        self.line.setObjectName("ln")
        self.line.setFixedWidth(2)
        self.line.setVisible(False)
        self.button = MoekButton(self, size=wsize, hsize=hsize, name=name, icon=icon, checkable=checkable, tooltip=tooltip)
        self.button.clicked.connect(self.btn_clicked)
        self.set_style(True)

    def set_style(self, value):
        """Modyfikacja stylesheet przy zmianie parametru setEnabled."""
        if value:
            self.setStyleSheet("QWidget#ln {background-color: rgb(52, 132, 240)}")
        else:
            self.setStyleSheet("QWidget#ln {background-color: rgb(255, 255, 255)}")

    def resizeEvent(self, event):
        """Wyśrodkowanie linii po zmianie rozmiaru przycisku."""
        super().resizeEvent(event)
        self.line.setGeometry((self.width()/2)-1, 19, 2, self.l)
        self.button.setGeometry(0, 0, self.button.width(), self.button.height())

    def btn_clicked(self):
        """Zmiana kategorii map po wciśnięciu przycisku."""
        self.button.setChecked(True) if self.name == self.parent().parent().cat else self.button.setChecked(False)
        if self.name == "snmt" and dlg.p_map.map in range(2, 7):  # Wybranie odpowiedniej mapy sat do nmt
            dlg.p_map.map += 5
        elif self.name == "sat" and dlg.p_map.map in range(7, 12):  # Powrót do mapy sat bez nmt
            dlg.p_map.map -= 5
        else:
            self.parent().parent().first_map(cat=self.name)


class MoekMapsBox(QFrame):
    """Pojemnik na checkbox'y z basemap'ami."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("frm")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setStyleSheet("QFrame#frm {border: 2px solid rgb(52, 132, 240); border-radius: 14px}")
        self.glay = QGridLayout()
        self.glay.setContentsMargins(6, 6, 6, 6)
        self.glay.setSpacing(2)
        self.setLayout(self.glay)
