# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QGridLayout, QGraphicsDropShadowEffect, QSizePolicy
from PyQt5.QtGui import QColor
from qgis.core import QgsProject

from .classes import PgConn
from .main import block_panels
from .widgets import MoekButton, MoekCheckBox, MoekStackedBox, MoekCfgHSpinBox

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
                    dlg.p_map.add_checkbox(cat=r[1], name=r[2], enabled=r[5])
                    # Utworzenie listy nazw warstw z podkładami:
                    dlg.p_map.layers.append(r[3])
                    if r[4]:  # Dwie warstwy w rekordzie
                        dlg.p_map.layers.append(r[4])
                dlg.p_map.loaded = True  # Zapamiętanie, że checkbox'y już istnieją
            else:  # Checkbox'y już istnieją
                # Aktualizacja parametru setChecked w checkbox'ach:
                for r in res:
                    exec('dlg.p_map.widgets["chk_' + r[2] + '"].setChecked(r[5])')
            # Utworzenie listy włączonych (b_map_enabled) map z kategorii "sat" i "topo":
            dlg.p_map.sat = []
            dlg.p_map.topo = []
            dlg.p_map.sat = [r for r in res if r[1] == "sat" and r[5]]
            dlg.p_map.topo = [r for r in res if r[1] == "topo" and r[5]]

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
    cat_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("mappnl")
        shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setStyleSheet("""
                    QFrame#mappnl {background-color: white; border: none; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-top-right-radius: 22px; border-bottom-right-radius: 16px}
                    QFrame#box {background-color: transparent; border: none}
                    """)
        self.widgets = {}
        self.btns = MoekMapButtons()
        self.box = MoekStackedBox()
        self.box.setObjectName("box")
        self.box.pages = {}
        for p in range(3):
            _page = MoekMapsBox() if p > 0 else MoekCfgHSpinBox()
            page_id = f'page_{p}'
            self.box.pages[page_id] = _page
            self.box.addWidget(_page)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(6, 6, 6, 6)
        vlay.setSpacing(0)
        vlay.addWidget(self.btns)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        exit_btn_1 = MoekButton(name="exit")
        exit_btn_1.clicked.connect(self.exit_clicked)
        self.box.pages["page_1"].glay.addWidget(exit_btn_1, 0, 1, 1, 1)
        exit_btn_2 = MoekButton(name="exit")
        exit_btn_2.clicked.connect(self.exit_clicked)
        self.box.pages["page_2"].glay.addWidget(exit_btn_2, 0, 1, 1, 1)
        self.cat = ""
        self.loaded = False
        self.layers = []
        self.sat = []
        self.topo = []
        self.sat_cnt = int()
        self.topo_cnt = int()
        self.sat_act = 1
        self.topo_act = 1
        self.cat_changed.connect(self.cat_change)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cat":
            self.cat_changed.emit(val)

    def next_map(self):
        """Wyświetlenie następnej w kolejności mapy z aktywnej kategorii."""
        if self.cat == "sat" or self.cat == "snmt":
            self.sat_act = self.sat_act + 1 if self.sat_act < len(self.sat) else 1
        elif self.cat == "topo":
            self.topo_act = self.topo_act + 1 if self.topo_act < len(self.topo) else 1
        self.map_change()

    def prev_map(self):
        """Wyświetlenie poprzedniej w kolejności mapy z aktywnej kategorii."""
        if self.cat == "sat" or self.cat == "snmt":
            self.sat_act = self.sat_act - 1 if self.sat_act > 1 else len(self.sat)
        elif self.cat == "topo":
            self.topo_act = self.topo_act - 1 if self.topo_act > 1 else len(self.topo)
        self.map_change()

    def prevnext_update(self):
        """Pokazanie lub ukrycie prev_btn i next_btn w zależności od ilości włączonych map w danej kategorii."""
        if self.cat == "sat" or self.cat == "snmt":
            map_cnt = len(self.sat)
        elif self.cat == "topo":
            map_cnt = len(self.topo)
        elif self.cat == "nmt":
            map_cnt = 1
        if map_cnt > 1:
            self.box.pages["page_0"].label.contract()  # Skrocenie szerokości label'u przed pojawieniem się przycisków
        self.box.pages["page_0"].prev_btn.setVisible(True) if map_cnt > 1 else self.box.pages["page_0"].prev_btn.setVisible(False)
        self.box.pages["page_0"].next_btn.setVisible(True) if map_cnt > 1 else self.box.pages["page_0"].next_btn.setVisible(False)
        self.box.pages["page_0"].cfg_btn.setVisible(False) if self.cat == "nmt" else self.box.pages["page_0"].cfg_btn.setVisible(True)
        if map_cnt > 1 or self.cat == "nmt":
            self.box.pages["page_0"].hlay.setContentsMargins(0, 0, 0, 0)
        else:
            self.box.pages["page_0"].hlay.setContentsMargins(0, 0, 10, 0)

    def cat_change(self, value):
        """Zmiana kategorii mapy."""
        self.prevnext_update()
        self.map_change()
        if value == "sat":
            self.btns.sat_btn.button.setChecked(True)
            self.btns.sat_btn.line.setVisible(True)
            self.btns.nmt_btn.button.setChecked(False)
            self.btns.nmt_btn.line.setVisible(False)
            self.btns.topo_btn.button.setChecked(False)
            self.btns.topo_btn.line.setVisible(False)
            self.btns.map_snmt_btn.button.setChecked(False)
            self.btns.map_snmt_btn.line.setVisible(False)
        if value == "nmt":
            self.btns.sat_btn.button.setChecked(False)
            self.btns.sat_btn.line.setVisible(False)
            self.btns.nmt_btn.button.setChecked(True)
            self.btns.nmt_btn.line.setVisible(True)
            self.btns.topo_btn.button.setChecked(False)
            self.btns.topo_btn.line.setVisible(False)
            self.btns.map_snmt_btn.button.setChecked(False)
            self.btns.map_snmt_btn.line.setVisible(False)
        if value == "topo":
            self.btns.sat_btn.button.setChecked(False)
            self.btns.sat_btn.line.setVisible(False)
            self.btns.nmt_btn.button.setChecked(False)
            self.btns.nmt_btn.line.setVisible(False)
            self.btns.topo_btn.button.setChecked(True)
            self.btns.topo_btn.line.setVisible(True)
            self.btns.map_snmt_btn.button.setChecked(False)
            self.btns.map_snmt_btn.line.setVisible(False)
        if value == "snmt":
            self.btns.sat_btn.button.setChecked(True)
            self.btns.sat_btn.line.setVisible(False)
            self.btns.nmt_btn.button.setChecked(True)
            self.btns.nmt_btn.line.setVisible(False)
            self.btns.topo_btn.button.setChecked(False)
            self.btns.topo_btn.line.setVisible(False)
            self.btns.map_snmt_btn.button.setChecked(True)
            self.btns.map_snmt_btn.line.setVisible(True)

    def map_change(self):
        """Zmiana mapy."""
        if self.cat == "sat" or self.cat == "snmt":
            map_act = self.sat_act - 1
            map_name = self.sat[map_act][2]
            lyr_1 = self.sat[map_act][3]
            lyr_2 = self.sat[map_act][4]
        elif self.cat == "topo":
            map_act = self.topo_act - 1
            map_name = self.topo[map_act][2]
            lyr_1 = self.topo[map_act][3]
            lyr_2 = self.topo[map_act][4]
        elif self.cat == "nmt":
            lyr_1, lyr_2 = "", ""
        # Zmiana tytułu mapy wyświetlanego w spinbox'ie:
        if self.cat == "sat" or self.cat == "topo":
            self.box.pages["page_0"].label.setText(map_name)
        elif self.cat == "snmt":
            self.box.pages["page_0"].label.setText(map_name + " + ISOK")
        elif self.cat == "nmt":
            self.box.pages["page_0"].label.setText("Numeryczny model terenu (ISOK)")
        # Ustawienie widoczności warstw z podkładami mapowymi:
        for layer in self.layers:
            if layer == lyr_1 or layer == lyr_2:
                exec('QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("' + layer + '")[0].id()).setItemVisibilityChecked(True)')
            else:
                exec('QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("' + layer + '")[0].id()).setItemVisibilityChecked(False)')
        # Ustawienie widoczności warstwy ISOK:
        if self.cat == "nmt" or self.cat == "snmt":
            QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("ISOK")[0].id()).setItemVisibilityChecked(True)
        else:
            QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("ISOK")[0].id()).setItemVisibilityChecked(False)

    def add_checkbox(self, cat, name, enabled):
        """Dodanie checkbox'a do pojemnika wyboru map."""
        _chk = MoekCheckBox(name=name, checked=enabled)
        if cat == "sat":
            page = 1
            self.sat_cnt += 1
            row = self.sat_cnt - 1
        else:
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
    
    def exit_clicked(self):
        """Wyjście z ustawień wyboru map z aktywnej kategorii."""
        self.box.setCurrentIndex(0)  # Powrót do spinbox'a
        block_panels(self, False)  # Odblokowanie pozostałych paneli
        dlg.p_map.btns.setEnabled(True)  # Odblokowanie przycisków z p_map
        m_list = []
        blokada = True  # Zabezpieczenie przed odznaczeniem wszystkich map z kategorii
        if self.cat == "sat" or self.cat == "snmt":
            layout = self.box.pages["page_1"].glay
        else:
            layout = self.box.pages["page_2"].glay
        w_idx = layout.count()
        while w_idx > 0:
            w_idx -= 1
            widget = layout.itemAt(w_idx).widget()
            if isinstance(widget, MoekCheckBox):
                if widget.isChecked() and blokada:
                    blokada = False
                m_list.append((widget.text(), widget.isChecked()))
        if blokada:
            QMessageBox.warning(None, "Podkłady mapowe", "Zmiany nie zostały wprowadzone. Przynajmniej jedna mapa musi pozostać zaznaczona.")
            basemaps_load()  # Ponowne wczytanie wartości checkbox'ów
        else:
            db_basemaps_update(m_list)  # Aktualizacja b_map_enabled w db
            basemaps_load()  # Ponowne wczytanie wartości checkbox'ów
            # Przejscie do pierwszej wybranej mapy z aktualnej kategorii:
            if self.cat == "sat" or self.cat == "snmt":
                self.sat_act = 1
            else:
                self.topo_act = 1
            self.cat = self.cat  # Wzbudzenie sygnału cat_change


class MoekMapButtons(QFrame):
    """Pojemnik z przyciskami panelu mapowego."""
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(50)
        self.sat_btn = MoekMapButton(self, name="sat", icon="map_sat", tooltip="fotomapy")
        self.nmt_btn = MoekMapButton(self, name="nmt", icon="map_nmt", tooltip="numeryczny model terenu")
        self.topo_btn = MoekMapButton(self, name="topo", icon="map_topo", tooltip="mapy topograficzne")
        self.ge_btn = MoekButton(self, size=50, name="ge", tooltip="pokaż widok mapy w Google Earth Pro")
        self.map_snmt_btn = MoekMapButton(self, name="snmt", icon="map_snmt", wsize=24, hsize=24, l=18)
    
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
        self.map_snmt_btn.setGeometry(w_4 - 12, 13, 24, 37)


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
        self.set_style(True)
        self.button = MoekButton(self, size=wsize, hsize=hsize, name=name, icon=icon, checkable=checkable, tooltip=tooltip)
        self.button.clicked.connect(self.btn_clicked)

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
        self.parent().parent().cat = self.name


class MoekMapsBox(QFrame):
    """Pojemnik na checkbox'y z basemap'ami."""
    def __init__(self):
        super().__init__()
        self.setObjectName("frm")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setStyleSheet("QFrame#frm {border: 2px solid rgb(52, 132, 240); border-radius: 14px}")
        self.glay = QGridLayout()
        self.glay.setContentsMargins(6, 6, 6, 6)
        self.glay.setSpacing(2)
        self.setLayout(self.glay)
