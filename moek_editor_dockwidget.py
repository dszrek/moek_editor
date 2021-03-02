# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MoekEditorDockWidget
                                 A QGIS plugin
 Wtyczka do obsługi systemu MOEK (PIG-PIB).
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-05-12
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Dominik Szrek / PIG-PIB
        email                : dszr@pgi.gov.pl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import Qt, QSize
from PyQt5.QtWidgets import QShortcut, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QPixmap
from qgis.core import QgsProject, QgsFeature
from qgis.utils import iface

from .classes import PgConn
from .maptools import MapToolManager, ObjectManager
from .main import vn_mode_changed
from .viewnet import change_done, vn_add, vn_sub, vn_zoom, hk_up_pressed, hk_down_pressed, hk_left_pressed, hk_right_pressed
from .widgets import MoekBoxPanel, MoekBarPanel, MoekButton, MoekSideDock, MoekBottomDock, MoekMenuFlag
from .basemaps import MoekMapPanel
from .sequences import prev_map, next_map, seq

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'moek_editor_dockwidget_base.ui'))
ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep
SELF = "self."

b_scroll = None

class MoekEditorDockWidget(QtWidgets.QDockWidget, FORM_CLASS):  #type: ignore

    closingPlugin = pyqtSignal()
    hk_vn_changed = pyqtSignal(bool)
    hk_seq_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(MoekEditorDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        self.iface = iface
        self.setupUi(self)

        p_team_widgets = [
                    {"item": "combobox", "name": "team_act", "height": 21, "border": 1, "b_round": "none"}
                    ]
        p_pow_widgets = [
                    {"item": "combobox", "name": "pow_act", "height": 21, "border": 1, "b_round": "none"}
                    ]
        p_map_widgets = []
        p_ext_widgets = [
                    {"item": "button", "name": "wn", "size": 47, "hsize": 25, "checkable": True, "tooltip": u'punkty WN_Kopaliny'},
                    {"item": "button", "name": "midas", "size": 47, "hsize": 25, "checkable": True, "tooltip": u'złoża i OTG z bazy MIDAS'},
                    {"item": "button", "name": "mgsp", "size": 47, "hsize": 25, "checkable": True, "tooltip": u'pkt. występowania kopaliny, złoża i OTG z bazy MGSP'},
                    {"item": "button", "name": "smgp", "size": 47, "hsize": 25, "checkable": True, "tooltip": u'wyrobiska z map SMGP'}
                    ]
        p_vn_widgets = [
                    {"page": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_sel", "size": 50, "checkable": True, "tooltip": u"wybierz pole"},
                    {"page": 0, "row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_zoom", "size": 50, "checkable": False, "tooltip": u"przybliż do pola"},
                    {"page": 0, "row": 0, "col": 2, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_done", "icon": "vn_doneT", "size": 50, "checkable": False, "tooltip": u'oznacz jako "SPRAWDZONE"'},
                    {"page": 0, "row": 0, "col": 3, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_doneF", "icon": "vn_doneTf", "size": 50, "checkable": False, "tooltip": u'oznacz jako "SPRAWDZONE" i idź do następnego'},
                    {"page": 0, "row": 1, "col": 0, "r_span": 1, "c_span": 4, "item": "seqbox", "name": "seq"},
                    {"page": 1, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "seqaddbox", "name": "sab_seq1", "id": 1, "height": 21, "border": 1, "b_round": "none"},
                    {"page": 1, "row": 1, "col": 0, "r_span": 1, "c_span": 1, "item": "seqcfgbox", "name": "scg_seq1", "id": 1, "height": 21, "border": 1, "b_round": "none"},
                    {"page": 2, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "seqaddbox", "name": "sab_seq2", "id":2, "height": 21, "border": 1, "b_round": "none"},
                    {"page": 2, "row": 1, "col": 0, "r_span": 1, "c_span": 1, "item": "seqcfgbox", "name": "scg_seq2", "id": 2, "height": 21, "border": 1, "b_round": "none"},
                    {"page": 3, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "seqaddbox", "name": "sab_seq3", "id":3, "height": 21, "border": 1, "b_round": "none"},
                    {"page": 3, "row": 1, "col": 0, "r_span": 1, "c_span": 1, "item": "seqcfgbox", "name": "scg_seq3", "id": 3, "height": 21, "border": 1, "b_round": "none"},
                    {"page": 4, "row": 0, "col": 1, "r_span": 1, "c_span": 3, "item": "combobox", "name": "teamusers", "border": 1, "b_round": "none"},
                    {"page": 4, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_powsel", "size": 50, "checkable": True, "tooltip": u"zaznacz pola siatki widoków znajdujące się w granicach wybranego powiatu"},
                    {"page": 4, "row": 1, "col": 0, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_polysel", "size": 50, "checkable": True, "tooltip": u"zaznacz pola znajdujące się w granicach narysowanego poligonu"},
                    {"page": 4, "row": 1, "col": 1, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_unsel", "size": 50, "checkable": False, "tooltip": u"wyczyść zaznaczenie pól siatki widoków"},
                    {"page": 4, "row": 1, "col": 2, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_add", "size": 50, "checkable": False, "tooltip": u"dodaj wybrane pola siatki widoków do zakresu poszukiwań wskazanego użytkownika"},
                    {"page": 4, "row": 1, "col": 3, "r_span": 1, "c_span": 1, "item": "button", "name": "vn_sub", "size": 50, "checkable": False, "tooltip": u"odejmij wybrane pola siatki widoków od zakresu poszukiwań wskazanego użytkownika"}
                    ]
        p_flag_widgets = [
                    {"page": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "button", "name": "flag_fchk", "size": 50, "checkable": True, "tooltip": u"dodaj flagę do kontroli terenowej"},
                    {"page": 0, "row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "button", "name": "flag_nfchk", "size": 50, "checkable": True, "tooltip": u"dodaj flagę bez kontroli terenowej"},
                    {"page": 0, "row": 0, "col": 2, "r_span": 1, "c_span": 1, "item": "button", "name": "flag_del", "size": 50, "checkable": True, "tooltip": u'usuń flagę'}
                    ]
        p_wyr_widgets = [
                    {"page": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "lineedit", "name": "wyr_id", "size": 50,  "height": 21, "border": 1},
                    {"page": 0, "row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "button", "name": "wyr_sel", "size": 50, "checkable": True, "tooltip": u"zaznacz wyrobisko"},
                    {"page": 0, "row": 1, "col": 0, "r_span": 1, "c_span": 1, "item": "button", "name": "wyr_add", "size": 50, "checkable": True, "tooltip": u"dodaj wyrobisko"},
                    {"page": 0, "row": 1, "col": 1, "r_span": 1, "c_span": 1, "item": "button", "name": "wyr_del", "size": 50, "checkable": True, "tooltip": u'usuń wyrobisko'}
                    ]
        p_auto_widgets = [
                    {"page": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "button", "name": "auto_add", "size": 50, "checkable": True, "tooltip": u"dodaj miejsce parkingowe"},
                    {"page": 0, "row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "button", "name": "auto_del", "size": 50, "checkable": True, "tooltip": u"usuń miejsce parkingowe"},
                    {"page": 0, "row": 0, "col": 2, "r_span": 1, "c_span": 1, "item": "button", "name": "marsz_add", "size": 50, "checkable": True, "tooltip": u'dodaj marszrutę'},
                    {"page": 0, "row": 0, "col": 3, "r_span": 1, "c_span": 1, "item": "button", "name": "marsz_del", "size": 50, "checkable": True, "tooltip": u'usuń marszrutę'}
                    ]

        self.p_team = MoekBarPanel(
                            title="Zespół:",
                            switch=False
                            )
        self.p_pow = MoekBarPanel(
                            title="Powiat:",
                            title_off="Wszystkie powiaty",
                            io_fn="powiaty_mode_changed(clicked=True)"
                            )
        self.p_map = MoekMapPanel()
        self.p_ext = MoekBarPanel(
                            title="",
                            switch=None,
                            spacing=8,
                            wmargin=0
                            )
        self.p_vn = MoekBoxPanel(
                            title="Siatka widoków",
                            io_fn="vn_mode_changed(clicked=True)",
                            config=True,
                            cfg_fn="vn_cfg()",
                            resize=True,
                            pages=5)
        self.p_flag = MoekBoxPanel(
                            title="Flagi",
                            io_fn="dlg.flag_visibility()")
        self.p_wyr = MoekBoxPanel(
                            title="Wyrobiska",
                            io_fn="dlg.wyr_visibility()")
        self.p_auto = MoekBoxPanel(
                            title="Komunikacja",
                            io_fn="dlg.auto_visibility()")

        self.panels = [self.p_team, self.p_pow, self.p_map, self.p_ext, self.p_vn]#, self.p_flag, self.p_wyr] #, self.p_auto]
        self.p_widgets = [p_team_widgets, p_pow_widgets, p_map_widgets, p_ext_widgets, p_vn_widgets]#, p_flag_widgets, p_wyr_widgets] #, p_auto_widgets]

        # Wczytanie paneli i ich widgetów do dockwidget'a:
        for (panel, widgets) in zip(self.panels, self.p_widgets):
            for widget in widgets:
                if widget["item"] == "button":
                    panel.add_button(widget)
                elif widget["item"] == "combobox":
                    panel.add_combobox(widget)
                elif widget["item"] == "lineedit":
                    panel.add_lineedit(widget)
                elif widget["item"] == "seqbox":
                    panel.add_seqbox(widget)
                elif widget["item"] == "seqaddbox":
                    panel.add_seqaddbox(widget)
                elif widget["item"] == "seqcfgbox":
                    panel.add_seqcfgbox(widget)
            self.vl_main.addWidget(panel)
            panel.resizeEvent = self.resize_panel
        self.frm_main.setLayout(self.vl_main)

        # Utworzenie bocznego docker'a z toolbox'ami:
        self.side_dock = MoekSideDock()
        # Utworzenie dolnego docker'a z toolbox'ami:
        self.bottom_dock = MoekBottomDock()

        tb_multi_tool_widgets = [
                    {"item": "button", "name": "multi_tool", "size": 50, "checkable": True, "tooltip": u"nawigacja i selekcja obiektów"},
                    {"item": "button", "name": "wyr_edit", "size": 50, "checkable": False, "tooltip": u"edycja granic wyrobiska"}
                    ]
        tb_add_widgets = [
                    {"item": "button", "name": "flag_fchk", "size": 50, "checkable": True, "tooltip": u"dodaj flagę do kontroli terenowej"},
                    {"item": "button", "name": "flag_nfchk", "size": 50, "checkable": True, "tooltip": u"dodaj flagę bez kontroli terenowej"},
                    {"item": "button", "name": "wyr_add_poly", "icon" : "wyr_add", "size": 50, "checkable": True, "tooltip": u"dodaj wyrobisko"}
                    ]
        tb_edit_tools_widgets = [
                    {"item": "button", "name": "edit_tool", "size": 50, "checkable": True, "tooltip": u"edycja geometrii wyrobiska"},
                    {"item": "button", "name": "edit_tool_add", "size": 50, "checkable": True, "tooltip": u"powiększ powierzchnię wyrobiska"},
                    {"item": "button", "name": "edit_tool_sub", "size": 50, "checkable": True, "tooltip": u"zmniejsz powierzchnię wyrobiska"}
                    ]
        tb_edit_separator_widgets = [
                    {"item": "dummy", "name": "presep", "size": 25}
                    ]
        tb_edit_exit_widgets = [
                    {"item": "button", "name": "cancel", "size": 50, "checkable": False, "tooltip": u"zrezygnuj ze zmian geometrii wyrobiska"},
                    {"item": "button", "name": "accept", "size": 50, "checkable": False, "tooltip": u"zatwierdź zmiany geometrii wyrobiska"}
                    ]
        toolboxes = [
                {"name": "multi_tool", "dock": "side", "background": "rgba(0, 0, 0, 0.6)", "widgets": tb_multi_tool_widgets},
                {"name": "add_object", "dock": "side", "background": "rgba(0, 128, 0, 0.6)", "widgets": tb_add_widgets},
                {"name": "edit_tools", "dock": "bottom", "background": "rgba(0, 0, 0, 0.6)", "widgets": tb_edit_tools_widgets},
                {"name": "edit_separator", "dock": "bottom", "background": "rgba(0, 0, 0, 0.0)", "widgets": tb_edit_separator_widgets},
                {"name": "edit_exit", "dock": "bottom", "background": "rgba(0, 0, 0, 0.6)", "widgets": tb_edit_exit_widgets}
                ]

        for toolbox in toolboxes:
            for key, val in toolbox.items():
                if key == "dock" and val == "side":
                    self.side_dock.add_toolbox(toolbox)
                if key == "dock" and val == "bottom":
                    self.bottom_dock.add_toolbox(toolbox)

        self.side_dock.move(1,0)
        self.side_dock.show()
        bottom_y = iface.mapCanvas().height() - 52
        self.bottom_dock.move(0, bottom_y)

        self.resizeEvent = self.resize_panel
        self.canvas = iface.mapCanvas()
        iface.mapCanvas().installEventFilter(self)

        # Wyłączenie messagebar'u:
        iface.messageBar().widgetAdded.connect(self.msgbar_blocker)

        self.__button_conn()
        self.ext_init()
        # self.p_flag.active = True
        # self.p_wyr.active = True
        # self.p_auto.active = True
        self.hk_vn_load()
        self.hk_seq_load()
        self.mt = MapToolManager(dlg=self, canvas=iface.mapCanvas())
        self.obj = ObjectManager(dlg=self, canvas=iface.mapCanvas())
        self.flag_menu = MoekMenuFlag()

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "hk_vn":
            self.hk_vn_changed.emit(val)
        if attr == "hk_seq":
            self.hk_seq_changed.emit(val)

    def msgbar_blocker(self, item):
        """Blokuje pojawianie się QGIS'owego messagebar'u."""
        iface.messageBar().clearWidgets()

    def eventFilter(self, obj, event):
        if obj is iface.mapCanvas() and event.type() == QEvent.Resize:
            self.resize_canvas()
        return super().eventFilter(obj, event)

    def resize_canvas(self):
        """Ustalenie pozycji dockerów po zmianie rozmiaru mapcanvas'u."""
        canvas = iface.mapCanvas()
        self.side_dock.setFixedHeight(canvas.height())
        self.side_dock.move(1,0)
        self.bottom_dock.setFixedWidth(canvas.width())
        self.bottom_dock.move(0, canvas.height() - 52)

    def resize_panel(self, event):
        """Ustalenie właściwych rozmiarów paneli i dockwidget'a."""
        global b_scroll
        w_max = 0
        h_sum = 0
        p_count = len(self.panels)
        h_header = 25
        h_margin = 8
        w_margin = 12
        w_scrollbar = 25
        # Ustalenie najszerszego panelu
        for panel in self.panels:
            if panel.rect().width() > w_max:
                w_max = panel.rect().width()
            h_sum += panel.rect().height()
        if w_max == 640:  # Szerokość bazowa przy tworzeniu widget'u
            return
        elif w_max < 208:  # Ustawienie minimalnej szerokości paneli
            w_max = 208
        # Wyrównanie szerokości paneli do najszerszego panelu
        for panel in self.panels:
            # TODO: panel.setMinimumWidth(w_max)
            panel.setFixedWidth(208)
        # Algorytm wykrywania i obsługi pionowego scrollbar'u
        dock_height = h_header + h_sum + (p_count * h_margin) - h_margin
        self.setMinimumHeight(dock_height)
        p_width = w_max + w_margin
        self.setMinimumWidth(p_width)
        _scroll = True if dock_height > self.rect().height() else False # scrollbar True/False
        if _scroll == b_scroll:  # scrollbar się nie zmienił
            return
        b_scroll = _scroll  # Aktualizacja flagi
        if b_scroll:  # Scrollbar się pojawił
            p_width = w_max + w_margin + w_scrollbar
            self.setMinimumWidth(p_width)
            self.resize(p_width, self.height())
        else:  # Scrollbar znikł
            self.setMinimumWidth(p_width)
            self.resize(p_width, self.height())
        iface.actionDraw().trigger()

    def hk_vn_load(self):
        """Załadowanie skrótów klawiszowych do obsługi vn."""
        hotkeys = {"hk_up": "Up", "hk_down": "Down", "hk_left": "Left", "hk_right": "Right", "hk_space": "Space"}
        for key, val in hotkeys.items():
            exec(SELF + key + " = QShortcut(Qt.Key_" + val + ", self)")
            exec(SELF + key + ".setEnabled(False)")
        self.hk_vn_active = False
        self.t_hk_vn = False
        self.hk_vn_changed.connect(self.hk_vn_change)

    def hk_vn_change(self):
        """Włączenie/wyłączenie skrótów klawiszowych do obsługi vn."""
        if self.hk_vn_active == self.hk_vn:  # hk_vn już ma odpowiednią wartość
            return
        hk_fn = {"hk_up": "hk_up_pressed",
                "hk_down": "hk_down_pressed",
                "hk_left": "hk_left_pressed",
                "hk_right": "hk_right_pressed",
                "hk_space": "lambda: change_done(True)"
                }
        io = "connect" if self.hk_vn else "disconnect"
        try:
            for key, val in hk_fn.items():
                # Aktywacja/deaktywacja skrótów klawiszowych:
                exec(SELF + key + ".setEnabled(self.hk_vn)")
                # Usunięcie nazwy funkcji z nawiasu przy odłączaniu skrótów klawiszowych:
                if not self.hk_vn:
                    val = ""
                # Podłączenie/odłączenie sygnału:
                exec(SELF + key + ".activated." + io + "(" + val + ")")
        except Exception as error:
            print(f"hotkeys exception ({key}): {error}")
        finally:
            self.hk_vn_active = self.hk_vn  # Zapamiętanie stanu hk_vn

    def hk_seq_load(self):
        """Załadowanie skrótów klawiszowych do obsługi sekwencji podkładów mapowych."""
        hotkeys = {"hk_1": "1", "hk_2": "2",  "hk_3": "3", "hk_tilde": "QuoteLeft", "hk_tab": "Tab"}
        for key, val in hotkeys.items():
            exec(SELF + key + " = QShortcut(Qt.Key_" + val + ", self)")
            exec(SELF + key + ".setEnabled(False)")
        self.hk_seq_active = False
        self.hk_seq_changed.connect(self.hk_seq_change)
        self.hk_seq = True

    def hk_seq_change(self):
        """Włączenie/wyłączenie skrótów klawiszowych do obsługi vn."""
        if self.hk_seq_active == self.hk_seq:  # hk_seq już ma odpowiednią wartość
            return
        hk_fn = {"hk_1": "lambda: seq(1)",
                "hk_2": "lambda: seq(2)",
                "hk_3": "lambda: seq(3)",
                "hk_tilde": "prev_map",
                "hk_tab": "next_map"}
        io = "connect" if self.hk_seq else "disconnect"
        try:
            for key, val in hk_fn.items():
                # Aktywacja/deaktywacja skrótów klawiszowych:
                exec(SELF + key + ".setEnabled(self.hk_seq)")
                # Usunięcie nazwy funkcji z nawiasu przy odłączaniu skrótów klawiszowych:
                if not self.hk_seq:
                    val = ""
                # Podłączenie/odłączenie sygnału:
                exec(SELF + key + ".activated." + io + "(" + val + ")")
        except Exception as error:
            print(f"hotkeys exception ({key}): {error}")
        finally:
            self.hk_seq_active = self.hk_seq  # Zapamiętanie stanu hk_seq

    def __button_conn(self):
        """Przyłączenia przycisków do funkcji."""
        self.p_vn.widgets["btn_vn_sel"].clicked.connect(lambda: self.mt.init("vn_sel"))
        self.p_vn.widgets["btn_vn_zoom"].pressed.connect(vn_zoom)
        self.p_vn.widgets["btn_vn_done"].pressed.connect(lambda: change_done(False))
        self.p_vn.widgets["btn_vn_doneF"].pressed.connect(lambda: change_done(True))
        self.p_vn.widgets["btn_vn_powsel"].clicked.connect(lambda: self.mt.init("vn_powsel"))
        self.p_vn.widgets["btn_vn_polysel"].clicked.connect(lambda: self.mt.init("vn_polysel"))
        self.p_vn.widgets["btn_vn_unsel"].pressed.connect(lambda: QgsProject.instance().mapLayersByName("vn_all")[0].removeSelection())
        self.p_vn.widgets["btn_vn_add"].pressed.connect(vn_add)
        self.p_vn.widgets["btn_vn_sub"].pressed.connect(vn_sub)
        # self.p_flag.widgets["btn_flag_fchk"].clicked.connect(lambda: self.mt.init("flt_add"))
        # self.p_flag.widgets["btn_flag_nfchk"].clicked.connect(lambda: self.mt.init("flf_add"))
        self.side_dock.toolboxes["tb_multi_tool"].widgets["btn_multi_tool"].clicked.connect(lambda: self.mt.init("multi_tool"))
        self.side_dock.toolboxes["tb_add_object"].widgets["btn_flag_fchk"].clicked.connect(lambda: self.mt.init("flt_add"))
        self.side_dock.toolboxes["tb_add_object"].widgets["btn_flag_nfchk"].clicked.connect(lambda: self.mt.init("flf_add"))
        # self.p_flag.widgets["btn_flag_del"].clicked.connect(lambda: self.mt.init("flag_del"))
        self.p_ext.box.widgets["btn_wn"].clicked.connect(lambda: self.ext_visibility(btn=self.p_ext.box.widgets["btn_wn"], grp=False, name="wn_kopaliny_pne"))
        self.p_ext.box.widgets["btn_midas"].clicked.connect(lambda: self.ext_visibility(btn=self.p_ext.box.widgets["btn_midas"], grp=True, name="MIDAS"))
        self.p_ext.box.widgets["btn_mgsp"].clicked.connect(lambda: self.ext_visibility(btn=self.p_ext.box.widgets["btn_mgsp"], grp=True, name="MGSP"))
        self.p_ext.box.widgets["btn_smgp"].clicked.connect(lambda: self.ext_visibility(btn=self.p_ext.box.widgets["btn_smgp"], grp=False, name="smgp_wyrobiska"))
        self.side_dock.toolboxes["tb_add_object"].widgets["btn_wyr_add_poly"].clicked.connect(lambda: self.mt.init("wyr_add_poly"))
        self.side_dock.toolboxes["tb_multi_tool"].widgets["btn_wyr_edit"].pressed.connect(lambda: self.mt.init("wyr_edit"))
        # self.p_wyr.widgets["btn_wyr_add"].clicked.connect(lambda: self.mt.init("wyr_add"))
        # self.p_wyr.widgets["btn_wyr_del"].clicked.connect(lambda: self.mt.init("wyr_del"))
        # self.p_auto.widgets["btn_auto_add"].clicked.connect(lambda: self.mt.init("auto_add"))
        # self.p_auto.widgets["btn_auto_del"].clicked.connect(lambda: self.mt.init("auto_del"))
        # self.p_auto.widgets["btn_marsz_add"].clicked.connect(lambda: self.mt.init("marsz_add"))
        # self.p_auto.widgets["btn_marsz_del"].clicked.connect(lambda: self.mt.init("marsz_del"))

    def button_cfg(self, btn, icon_name, size=50, tooltip=""):
        """Konfiguracja przycisków."""
        btn.setToolTip(tooltip)
        icon = QIcon()
        icon.addFile(ICON_PATH + icon_name + "_0.png", size=QSize(size, size), mode=QIcon.Normal, state=QIcon.Off)
        icon.addFile(ICON_PATH + icon_name + "_0_act.png", size=QSize(size, size), mode=QIcon.Active, state=QIcon.Off)
        icon.addFile(ICON_PATH + icon_name + "_0.png", size=QSize(size, size), mode=QIcon.Selected, state=QIcon.Off)
        if not btn.isEnabled():
            icon.addFile(ICON_PATH + icon_name + "_0_dis.png", size=QSize(size, size), mode=QIcon.Disabled, state=QIcon.Off)
        if btn.isCheckable():
            icon.addFile(ICON_PATH + icon_name + "_1.png", size=QSize(size, size), mode=QIcon.Normal, state=QIcon.On)
            icon.addFile(ICON_PATH + icon_name + "_1_act.png", size=QSize(size, size), mode=QIcon.Active, state=QIcon.On)
            icon.addFile(ICON_PATH + icon_name + "_1.png", size=QSize(size, size), mode=QIcon.Selected, state=QIcon.On)
        btn.setIcon(icon)

    def wyr_visibility(self):
        """Włączenie lub wyłączenie warstwy z wyrobiskami."""
        value = True if self.p_wyr.is_active() else False
        QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("wyrobiska")[0].id()).setItemVisibilityChecked(value)

    def flag_visibility(self):
        """Włączenie lub wyłączenie warstwy z flagami."""
        value = True if self.p_flag.is_active() else False
        QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("flagi_z_teren")[0].id()).setItemVisibilityChecked(value)
        QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("flagi_bez_teren")[0].id()).setItemVisibilityChecked(value)

    def auto_visibility(self):
        """Włączenie lub wyłączenie warstw auto i marsz."""
        value = True if self.p_auto.is_active() else False
        QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("parking")[0].id()).setItemVisibilityChecked(value)
        QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName("marsz")[0].id()).setItemVisibilityChecked(value)

    def ext_visibility(self, btn, grp, name):
        """Włączenie / wyłaczenie warstw z danymi zewnętrznymi."""
        if grp:
            QgsProject.instance().layerTreeRoot().findGroup(name).setItemVisibilityCheckedRecursive(btn.isChecked())
        else:
            QgsProject.instance().layerTreeRoot().findLayer(QgsProject.instance().mapLayersByName(name)[0].id()).setItemVisibilityChecked(btn.isChecked())

    def ext_init(self):
        """Początkowe ustawienia widoczności warstw danych zewnętrznych."""
        value = True
        for btns in self.p_ext.box.findChildren(MoekButton):
            btns.setChecked(value)
        self.ext_visibility(btn=self.p_ext.box.widgets["btn_wn"], grp=False, name="wn_kopaliny_pne")
        self.ext_visibility(btn=self.p_ext.box.widgets["btn_midas"], grp=True, name="MIDAS")
        self.ext_visibility(btn=self.p_ext.box.widgets["btn_mgsp"], grp=True, name="MGSP")
        self.ext_visibility(btn=self.p_ext.box.widgets["btn_smgp"], grp=False, name="smgp_wyrobiska")

    def closeEvent(self, event):
        # Deaktywacja skrótów klawiszowych:
        self.hk_vn = False
        self.hk_seq = False
        # Usunięcie połączenia z Google Earth Pro:
        self.ge = None
        # Odblokowanie messagebar'u:
        try:
            iface.messageBar().widgetAdded.disconnect(self.msgbar_blocker)
        except:
            pass
        try:
            iface.mapCanvas().children().remove(self.side_dock)
            self.side_dock.deleteLater()
        except:
            pass
        try:
            iface.mapCanvas().children().remove(self.bottom_dock)
            self.bottom_dock.deleteLater()
        except:
            pass
        try:
            iface.mapCanvas().removeEventFilter(self)
        except Exception as err:
            print(err)
        self.closingPlugin.emit()
        event.accept()
