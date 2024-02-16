# -*- coding: utf-8 -*-
import os
import time as tm
import pandas as pd
import numpy as np
import datetime

from qgis.PyQt.QtWidgets import QApplication, QWidget, QMessageBox, QFrame, QToolButton, QPushButton, QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QCheckBox, QLabel, QProgressBar, QStackedWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect, QTableView, QAbstractItemView, QStyle, QStyleOptionComboBox
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal, QRegExp, QRect, QTimer
from qgis.PyQt.QtGui import QPen, QBrush, QIcon, QColor, QFont, QPainter, QPixmap, QPainterPath, QRegExpValidator, QStandardItemModel
from qgis.utils import iface

from .main import db_attr_change, vn_cfg, vn_setup_mode, powiaty_mode_changed, vn_mode_changed, pg_layer_change, get_wyr_ids, get_flag_ids, get_parking_ids, get_marsz_ids, wyr_layer_update, wn_layer_update, marsz_layer_update, sequences_load, db_sequence_update
from .maptools import wyr_point_lyrs_repaint
from .classes import PgConn, WDfModel, CmbDelegate
from .viewnet import vn_zoom

ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep

dlg = None

def dlg_widgets(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg


class MoekBoxPanel(QFrame):
    """Panel z belką i pojemnikiem ze stronami."""
    def __init__(self, *args, title="", switch=True, io_fn="", config=False, cfg_fn="", expand=False, exp_fn="", pages=1):
        super().__init__(*args)
        self.setObjectName("boxpnl")
        shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow)
        self.bar = MoekBar(self, title=title, switch=switch, config=config, expand=expand)
        self.box = MoekStackedBox(self)
        self.box.setObjectName("box")
        self.box.pages = {}
        for p in range(pages):
            _page = MoekGridBox(self)
            page_id = f'page_{p}'
            self.box.pages[page_id] = _page
            self.box.addWidget(_page)
        self.widgets = {}
        self.io_fn = io_fn
        self.cfg_fn = cfg_fn
        self.active = None
        self.config = config
        self.expand = expand
        self.exp_fn = exp_fn
        self.expanded = None
        self.state = None
        self.passing_void = False
        self.title = title
        # self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            if val is None:
                return
            if not self.passing_void:
                self.cfg_change()
            self.bar.io_btn.setChecked(val)
            if not val:
                self.box.setVisible(False)
            elif val and (self.expanded or not self.expand):
                self.box.setVisible(True)
            if self.expand:
                self.bar.exp_btn.setVisible(val)
            if self.config:
                self.bar.cfg_btn.setVisible(val)
                if self.bar.cfg_btn.isChecked():
                    self.bar.cfg_btn.setChecked(False)
                    self.bar.cfg_clicked()
        elif attr == "expanded":
            if val is None:
                return
            if not self.passing_void:
                self.cfg_change()
            try:
                if self.bar.exp_btn.isChecked() != val:
                    self.bar.exp_btn.setChecked(val)
                self.box.setVisible(True) if val else self.box.setVisible(False)
            except TypeError:
                print("expand exception")

    def io_clicked(self, value):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        self.active = value
        if len(self.io_fn) > 0:
            try:
                exec(self.io_fn)
            except TypeError:
                print("io_fn exception:", self.io_fn)

    def is_active(self):
        """Zwraca, czy panel jest w trybie active."""
        return True if self.active else False

    def cfg_change(self):
        """Wysyła do PanelManager'a informację o aktualnej wartości int oznaczającej stan panelu (active i expand)."""
        cur_state = self.get_state()
        if cur_state != self.state:
            try:
                dlg.cfg.set_val(name=self.exp_fn, val=self.get_state())
            except Exception as err:
                print(f"MoekBoxPanel[{self.title}]: {err}")

    def set_state(self, val):
        """Ustawia stan panelu na podstawie wartości int podanej przez PanelManager."""
        # Aktualizacja stanu panelu:
        if val != self.state:
            self.state = val
            self.passing_void = True
        else:   # Panel ma już ustawiony odpowiedni stan
            return
        if val == 0:
            self.active = False
        elif val == 1:
            self.active = True
            if self.expand:
                self.expanded = False
        elif val == 2:
            self.active = True
            if self.expand:
                self.expanded = True
        self.style_update()
        self.passing_void = False

    def get_state(self):
        """Zwraca wartość int określającą stan panelu (active i expand)."""
        val = 0
        if self.active:
            val += 1
            if self.expanded or not self.expand:
                val += 1
        return val

    def style_update(self):
        """Modyfikacja stylesheet przy zmianie trybu active lub enabled."""
        # Ustalenie wariantu stylu:
        case = self.get_state()
        if case == 2:  # Panel włączony i rozwinięty
            self.setStyleSheet("""
                               QFrame#boxpnl {background-color: white; border: none; border-top-left-radius: 16px; border-bottom-left-radius: 6px; border-top-right-radius: 6px; border-bottom-right-radius: 6px}
                               QFrame#bar {background-color: transparent; border: none}
                               QFrame#box {background-color: transparent; border: none}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(37,84,161)}
                               """)
        elif case == 1:  # Panel włączony i zwinięty
            self.setStyleSheet("""
                               QFrame#boxpnl {background-color: white; border: none; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-top-right-radius: 6px; border-bottom-right-radius: 6px}
                               QFrame#bar {background-color: transparent; border: none}
                               QFrame#box {background-color: transparent; border: none}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(37,84,161)}
                               """)
        elif case == 0:  # Panel wyłączony
            self.setStyleSheet("""
                               QFrame#boxpnl {background-color: rgb(245,245,245); border: none; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-top-right-radius: 6px; border-bottom-right-radius: 6px}
                               QFrame#bar {background-color: transparent; border: none}
                               QFrame#box {background-color: transparent; border: none}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(150,150,150)}
                               """)

    def add_button(self, dict):
        """Dodanie przycisku do pojemnika panelu."""
        icon_name = dict["icon"] if "icon" in dict else dict["name"]
        size = dict["size"] if "size" in dict else 0
        hsize = dict["hsize"] if "hsize" in dict else 0
        _btn = MoekButton(self, size=size, hsize=hsize, name=icon_name, checkable=dict["checkable"], tooltip=dict["tooltip"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_btn, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        btn_name = f'btn_{dict["name"]}'
        self.widgets[btn_name] = _btn

    def add_combobox(self, dict):
        """Dodanie combobox'a do pojemnika panelu."""
        _cmb = MoekComboBox(self, name=dict["name"], border=dict["border"], b_round=dict["b_round"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_cmb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        cmb_name = f'cmb_{dict["name"]}'
        self.widgets[cmb_name] = _cmb

    def add_lineedit(self, dict):
        """Dodanie lineedit'a do pojemnika panelu."""
        _led = CanvasLineEdit(self, name=dict["name"], border=dict["border"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_led, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        led_name = f'led_{dict["name"]}'
        self.widgets[led_name] = _led


class MoekBarPanel(QFrame):
    """Panel z pojemnikiem w belce."""

    def __init__(self, *args, title=None, title_off=None, switch=True, io_fn="", cfg_name="", spacing=0, wmargin=4, bmargin=None, grey_void=None, round=None, custom_width=0, grouped=False):
        super().__init__(*args)
        self.setObjectName("barpnl")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.setMinimumHeight(33)
        self.custom_width = custom_width
        if self.custom_width > 0:
            self.setMinimumWidth(self.custom_width)
            self.setMaximumWidth(self.custom_width)
        self.grouped = grouped
        if not self.grouped:
            shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
            self.setGraphicsEffect(shadow)
        self.grey_void = grey_void
        self.round = round
        _margin = bmargin if bmargin else [0, 0, 0, 0]
        self.box = MoekHBox(self, margins=_margin)
        self.box.widgets = {}
        self.switch = switch
        self.io_fn = io_fn
        self.cfg_name = cfg_name
        self.title = title
        self.title_off = title_off
        self.l_title = QLabel()
        self.l_title.setAlignment(Qt.AlignCenter)
        self.l_title.setObjectName("title")
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(wmargin, 0, wmargin, 0)
        self.hlay.setSpacing(spacing)
        if self.switch:
            _name = "io_blue" if self.grey_void else "io"
            self.io_btn = MoekButton(self, name=_name, checkable=True)
            self.io_btn.clicked.connect(self.io_clicked)
            self.hlay.addWidget(self.io_btn)
        if self.title or self.title_off:
            self.hlay.addWidget(self.l_title, stretch=1)
        self.hlay.addWidget(self.box, stretch=3)
        self.setLayout(self.hlay)
        self.passing_void = True
        self.active = True
        self.state = None
        self.passing_void = False
        self.style_update()

    def io_clicked(self):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        self.active = self.io_btn.isChecked()
        if len(self.io_fn) > 0:
            try:
                exec(self.io_fn)
            except TypeError:
                print("io_fn exception:", self.io_fn)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            if val is None:
                return
            if not self.passing_void:
                self.cfg_change()
            self.box.setVisible(val)
            if self.switch:
                self.io_btn.setChecked(val)
            if val:
                self.l_title.setText(self.title) if self.title else self.l_title.setText("")
                self.l_title.setVisible(True) if self.title else self.l_title.setVisible(False)
            else:
                alt_text = self.title if self.title else ""
                self.l_title.setText(self.title_off) if self.title_off else self.l_title.setText(alt_text)
                self.l_title.setVisible(True) if self.title_off or (not self.title_off and len(alt_text) > 0) else self.l_title.setVisible(False)

    def cfg_change(self):
        """Wysyła do PanelManager'a informację o aktualnej wartości int oznaczającej stan active panelu."""
        cur_state = 1 if self.active else 0
        if cur_state != self.state:
            try:
                dlg.cfg.set_val(name=self.cfg_name, val=cur_state)
            except Exception as err:
                print(f"MoekBarPanel[{self.title}]: {err}")

    def set_state(self, val):
        """Ustawia stan panelu na podstawie wartości int podanej przez PanelManager."""
        # Aktualizacja stanu panelu:
        if val != self.state:
            self.state = val
            self.passing_void = True
        else:   # Panel ma już ustawiony odpowiedni stan
            return
        self.active = True if val else False
        self.style_update()
        self.passing_void = False

    def is_active(self):
        """Zwraca, czy panel jest w trybie active."""
        return True if self.active else False

    def style_update(self):
        """Modyfikacja stylesheet przy zmianie trybu active."""
        # Wielkości zaokrągleń ramki panelu:
        if self.switch and not self.round:
            b_rad = [16, 16, 6, 6]
        elif self.round:
            b_rad = self.round
        else:
            b_rad = [6, 6, 6, 6]
        bgr_clr = "white" if self.grey_void else "rgb(245,245,245)"
        clr = "rgb(37,84,161)" if self.grey_void else "rgb(150,150,150)"
        if self.active:
            self.setStyleSheet("""
                               QFrame#barpnl {background-color: white; border: none; border-top-left-radius: """ + str(b_rad[0]) + """px; border-bottom-left-radius: """ + str(b_rad[1]) + """px; border-top-right-radius: """ + str(b_rad[2]) + """px; border-bottom-right-radius: """ + str(b_rad[3]) + """px}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(37,84,161)}
                               """)
        else:
            self.setStyleSheet("""
                               QFrame#barpnl {background-color: """ + str(bgr_clr) + """; border: none; border-top-left-radius: """ + str(b_rad[0]) + """px; border-bottom-left-radius: """ + str(b_rad[1]) + """px; border-top-right-radius: """ + str(b_rad[2]) + """px; border-bottom-right-radius: """ + str(b_rad[3]) + """px}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: """ + str(clr) + """}
                               """)

    def add_button(self, dict):
        """Dodanie przycisku do belki panelu."""
        icon_name = dict["icon"] if "icon" in dict else dict["name"]
        size = dict["size"] if "size" in dict else 0
        hsize = dict["hsize"] if "hsize" in dict else 0
        _btn = MoekButton(self, size=size, hsize=hsize, name=icon_name, checkable=dict["checkable"], tooltip=dict["tooltip"])
        self.box.lay.addWidget(_btn)
        btn_name = f'btn_{dict["name"]}'
        self.box.widgets[btn_name] = _btn

    def add_combobox(self, dict):
        """Dodanie combobox'a do belki panelu."""
        _cmb = MoekComboBox(self, name=dict["name"], height=dict["height"], border=dict["border"], b_round=dict["b_round"])
        self.box.lay.addWidget(_cmb)
        cmb_name = f'cmb_{dict["name"]}'
        self.box.widgets[cmb_name] = _cmb


class MoekGroupPanel(QFrame):
    """Panel łączący panele w jednej linii."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.setMinimumHeight(33)
        shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow)
        self.box = MoekHBox(self, spacing=0)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(0)
        self.hlay.addWidget(self.box)
        self.setLayout(self.hlay)

    def add_panel(self, dict):
        """Dodanie panelu do box'u."""
        self.box.lay.addWidget(dict["object"])


class MoekBar(QFrame):
    """Belka panelu z box'em."""
    def __init__(self, *args, title="", switch=True, config=False, expand=False):
        super().__init__(*args)
        self.setObjectName("bar")
        self.setMinimumHeight(33)
        if switch:
            self.io_btn = MoekButton(self, name="io", enabled=True, checkable=True)
            self.io_btn.clicked.connect(lambda: self.parent().io_clicked(self.io_btn.isChecked()))
        else:
            self.io_btn = MoekButton(self, name="io", enabled=False, checkable=True)
        if config:
            self.cfg_btn = MoekButton(self, name="cfg", checkable=True)
        if expand:
            self.exp_btn = MoekButton(self, name="exp", checkable=True)
        if len(title) > 0:
            self.l_title = QLabel()
            self.l_title.setObjectName("title")
            self.l_title.setText(title)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(4, 0, 4, 0)
        hlay.setSpacing(0)
        hlay.addWidget(self.io_btn)
        if len(title) > 0:
            hlay.addWidget(self.l_title)
        hlay.addItem(spacer)
        if config:
            hlay.addWidget(self.cfg_btn)
            self.cfg_btn.clicked.connect(self.cfg_clicked)
        if expand:
            hlay.addWidget(self.exp_btn)
            self.exp_btn.clicked.connect(self.exp_clicked)
        self.setLayout(hlay)

    def cfg_clicked(self):
        """Uruchomienie zdefiniowanej funkcji po kliknięciu na przycisk cfg."""
        exec(self.parent().cfg_fn)

    def exp_clicked(self):
        """Zwinięcie/rozwinięcie panelu po kliknięciu na przycisk exp."""
        self.parent().expanded = self.exp_btn.isChecked()


class CanvasPanelTitleBar(QFrame):
    """Belka panelu z box'em."""
    def __init__(self, *args, width, title="", back=False, font_size=12):
        super().__init__(*args)
        self.setObjectName("bar")
        self.setFixedHeight(34)
        self.back = back
        btn = "cp_back" if self.back else "cp_exit"
        self.exit_btn = MoekButton(self, name=btn, size=34, enabled=True, checkable=False)
        self.exit_btn.clicked.connect(self.exit_clicked)
        if len(title) > 0:
            self.l_title = PanelLabel(self, text=title, size=font_size)
            self.l_title.setFixedWidth(width - 34)
        self.setStyleSheet("""
                    QFrame#bar{background-color: rgba(60, 60, 60, 0.95); border: none}
                    QFrame#title {color: rgb(255, 255, 255); font-size: """ + str(font_size) + """pt; qproperty-alignment: AlignCenter}
                    """)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(0)
        if len(title) > 0:
            hlay.addWidget(self.l_title)
        hlay.addWidget(self.exit_btn)
        self.setLayout(hlay)

    def exit_clicked(self):
        if self.back:
            dlg.seq_dock.widgets["sqb_seq"].exit_setup()
        else:
            self.parent().exit_clicked()


class SplashScreen(QFrame):
    """Ekran ładowania wtyczki."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        shadow_1 = QGraphicsDropShadowEffect(blurRadius=24, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        shadow_2 = QGraphicsDropShadowEffect(blurRadius=16, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(300, 240)
        self.logo = MoekButton(self, name="splash_logo", size=120, checkable=False, enabled=False)
        self.logo.setGraphicsEffect(shadow_1)
        self.p_bar = QProgressBar(self)
        self.p_bar.setGraphicsEffect(shadow_2)
        self.p_bar.setFixedWidth(100)
        self.p_bar.setRange(0, 100)
        self.p_bar.setTextVisible(False)
        self.box = MoekVBox(self, spacing=0, margins=[0, 30, 0, 30])
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        hlay = QVBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(0)
        hlay.addWidget(self.box)
        self.setLayout(hlay)
        self.box.lay.addWidget(self.logo)
        self.box.lay.addWidget(self.p_bar)
        self.box.lay.setAlignment(self.logo, Qt.AlignCenter)
        self.box.lay.setAlignment(self.p_bar, Qt.AlignCenter)


class WyrCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi wyrobisk."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(516, 605)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        shadow_1 = QGraphicsDropShadowEffect(blurRadius=16, color=QColor(0, 0, 0, 220), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow_1)
        self.focus_void = True
        self.trigger_void = True
        self.p_heights = [498, 465, 498]
        self.mt_enabled = False
        self.bar = CanvasPanelTitleBar(self, title="Wyrobiska", width=self.width())
        self.list_box = MoekVBox(self, spacing=0)
        self.list_box.setFixedWidth(96)
        self.sp_id = CanvasHSubPanel(self, height=32, margins=[0, 0, 0, 0], spacing=0, color="255, 255, 255", alpha=0.71)
        self.list_box.lay.addWidget(self.sp_id)
        self.id_box = IdSpinBox(self, _obj="wyr", height=32, theme="light")
        self.sp_id.lay.addWidget(self.id_box)
        self.tv_wdf = WyrIdTableView(self)
        self.tv_wdf.setFixedWidth(96)
        self.list_box.lay.addWidget(self.tv_wdf)
        tv_wdf_widths = [10, 66]
        tv_wdf_headers = ['status', 'ID']
        self.wn_df = pd.DataFrame({'wyr_id': [1], 'wn_id': ['A']})  # Dataframe z połaczeniami wyrobisk z WN_PNE
        self.wdf = pd.DataFrame({'status': [1], 'wyr_id': [1]})  # Dataframe z danymi o wyrobiskach
        self.wdf_mdl = WDfModel(df=self.wdf, tv=self.tv_wdf, col_widths=tv_wdf_widths, col_names=tv_wdf_headers)
        self.tv_wdf.selectionModel().selectionChanged.connect(self.wdf_sel_change)
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.6); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(1)
        hlay.addWidget(self.list_box)
        hlay.addWidget(self.box)
        hlay.setAlignment(self.box, Qt.AlignTop)
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addLayout(hlay)
        self.setLayout(vlay)
        self.head = MoekHBox(self, spacing=1)
        self.box.lay.addWidget(self.head)
        self.head_left = MoekVBox(self)
        self.head.lay.addWidget(self.head_left)
        self.head_right = MoekVBox(self, spacing=1, alpha=0.71)
        self.head.lay.addWidget(self.head_right)
        self.sp_status = CanvasHSubPanel(self, height=32, margins=[2, 2, 2, 2], spacing=1, alpha=0.71)
        self.head_left.lay.addWidget(self.sp_status)
        self.order_box = IdSpinBox(self, _obj="order", width=90, le_width=46, height=28, max_len=3, validator="order", placeholder="001", theme="color")
        self.sp_status.lay.addWidget(self.order_box)
        self.order_drawer = OrderDrawer(self)
        self.sp_status.lay.addWidget(self.order_drawer)
        self.order_drawer.setVisible(False)  # Tymczasowe wyłączenie z uwagi na metodykę 2024 r.
        self.status_indicator = WyrStatusIndicator(self)
        self.sp_status.lay.addWidget(self.status_indicator)
        self.status_selector = WyrStatusSelector(self)
        self.sp_status.lay.addWidget(self.status_selector)
        self.separator_1 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.head_left.lay.addWidget(self.separator_1)
        self.sp_main = MoekHBox(self, margins=[0, 0, 0, 0], spacing=1)
        self.head_left.lay.addWidget(self.sp_main)
        self.hashbox = CanvasHSubPanel(self, height=32, margins=[2, 1, 2, 1], spacing=3, alpha=0.71)
        self.sp_main.lay.addWidget(self.hashbox)
        self.hash_icon = MoekButton(self, name="hash", size=30, checkable=False, enabled=False, tooltip="numer roboczy, terenowy")
        self.hashbox.lay.addWidget(self.hash_icon)
        self.hash = CanvasLineEdit(self, width=56, height=28, font_size=10, max_len=5, validator=None, theme="dark", fn=['db_attr_change(tbl="team_{dlg.team_i}.wyrobiska", attr="teren_id", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], placeholder="XXXXX")
        self.hashbox.lay.addWidget(self.hash)
        self.wn_picker = WyrWnPicker(self)
        self.sp_main.lay.addWidget(self.wn_picker)
        self.lokbox = CanvasHSubPanel(self, height=32, margins=[0, 0, 0, 0], alpha=0.71)
        self.sp_main.lay.addWidget(self.lokbox)
        self.lok = MoekButton(self, name="lok", size=30, checkable=False, enabled=True, tooltip = "lokalizacja wyrobiska")
        self.lokbox.lay.addWidget(self.lok)
        self.areabox = CanvasHSubPanel(self, height=32, margins=[2, 2, 2, 2], alpha=0.71)
        self.areabox.setFixedWidth(150)
        self.sp_main.lay.addWidget(self.areabox)
        self.area_icon = MoekButton(self, name="wyr_area", size=30, checkable=False, enabled=True, tooltip="powierzchnia wyrobiska")
        self.areabox.lay.addWidget(self.area_icon)
        spacer_1 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.areabox.lay.addItem(spacer_1)
        self.area_label = PanelLabel(self, text="", size=12)
        self.areabox.lay.addWidget(self.area_label)
        spacer_2 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.areabox.lay.addItem(spacer_2)
        self.wyr_edit = MoekButton(self, name="wyr_edit", size=32, checkable=False, tooltip="edytuj geometrię wyrobiska")
        self.wyr_edit.clicked.connect(lambda: dlg.mt.init("wyr_edit"))
        self.head_right.lay.addWidget(self.wyr_edit)
        self.wyr_del = MoekButton(self, name="trash", size=32, checkable=False, tooltip="usuń wyrobisko")
        self.wyr_del.clicked.connect(self.wyr_delete)
        self.head_right.lay.addWidget(self.wyr_del)
        self.separator_2 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.box.lay.addWidget(self.separator_2)
        self.tab_box = TabBox(self)
        self.box.lay.addWidget(self.tab_box)
        self.sb = CanvasStackedBox(self, alpha=0.71)
        self.sb.setFixedWidth(414)
        self.box.lay.addWidget(self.sb)
        self.sb.currentChanged.connect(self.page_change)
        self.has_midas = None
        self.locked = None
        self.pages = {}
        self.subpages = {}
        self.widgets = {}
        for p in range(3):
            _page = CanvasGridBox(self, height=self.p_heights[p], margins=[5, 4, 0, 2], spacing=0)
            page_id = f'page_{p}'
            self.pages[page_id] = _page
            self.sb.addWidget(_page)
        self.ssb = CanvasStackedBox(self)
        self.ssb.setFixedWidth(408)
        self.pages["page_1"].glay.glay.addWidget(self.ssb, 1, 0, 1, 1)
        for s in range(6):
            _subpage = CanvasGridBox(self, height=468, margins=[0, 6, 0, 0], spacing=0)
            subpage_id = f'subpage_{s}'
            self.subpages[subpage_id] = _subpage
            self.ssb.addWidget(_subpage)
        self.tab_box.cur_idx = 0
        self.dicts = [

                    {"name": "midas_id_0", "page": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 8, "validator": "id", "placeholder": None, "zero_allowed": True, "min_max": False, "width": 130, "val_width": 130, "val_width_2": None, "value_2": None, "sep_width": None, "sep_txt": None, "title_down": "ID ZŁOŻA (MIDAS)", "title_down_2": None, "title_left": None, "icon": None, "tooltip": "", "trigger": "trigger_midas()", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyrobiska", attr="midas_id", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)','wyr_point_lyrs_repaint()']]},

                    {"name": "stan_midas_0", "page": 0, "row": 0, "col": 4, "r_span": 1, "c_span": 8, "type": "combo", "list_width": 266, "width": 266, "val_width": None, "title_left": None, "title_down": "STAN ZAGOSPODAROWANIA ZŁOŻA WG MIDAS", "tbl_name": "sl_stan_midas", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_stan_midas", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "okres_zloze_0", "page": 0, "row": 1, "col": 0, "r_span": 1, "c_span": 12, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "zero_allowed": True, "min_max": False, "width": 402, "val_width": 133, "val_width_2": 132, "value_2": " ", "sep_width": 1, "sep_txt": "", "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji złoża:", "icon": None, "tooltip": "", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_zloze_od", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_zloze_do", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "pne_zloze_0", "page": 0, "row": 2, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 66, "width": 402, "val_width": 66, "title_left": "Eksploatacja bez koncesji (PNE) w granicach złoża / OG:", "title_down": None, "tbl_name": "sl_tak_nie", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="b_pne_zloze", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "pne_poza_0", "page": 0, "row": 3, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 66, "width": 402, "val_width": 66, "title_left": "Eksploatacja bez koncesji (PNE) poza granicami złoża / OG:", "title_down": None, "tbl_name": "sl_tak_nie", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="b_pne_poza", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "okres_eksp_0", "page": 0, "row": 4, "col": 0, "r_span": 1, "c_span": 12, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "zero_allowed": False, "min_max": False, "width": 402, "val_width": 133, "val_width_2": 132, "value_2": " ", "sep_width": 1, "sep_txt": "", "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji PNE:", "icon": None, "tooltip": "", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_od", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_do", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "notepad_0", "page": 0, "row": 5, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 82, "title": "NOTATKI", "trigger": None, "txt_limiter": True, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyrobiska", attr="t_notatki", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']},

                    {"name": "termin_1", "page": 1, "subpage": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 8, "type": "termin"},

                    {"name": "kopalina_wiek_1", "page": 1, "subpage": 0, "row": 0, "col": 4, "r_span": 1, "c_span": 8, "type": "kop_wiek"},

                    {"name": "pne_1", "page": 1, "subpage": 0, "row": 1, "col": 0, "r_span": 1, "c_span": 1, "type": "pne"},

                    {"name": "okres_eksp_1", "page": 1, "subpage": 0, "row": 1, "col": 1, "r_span": 1, "c_span": 11, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "zero_allowed": False, "min_max": False, "width": 368, "val_width": 134, "val_width_2": 131, "value_2": " ", "sep_width": 1, "sep_txt": "", "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji:", "icon": None, "tooltip": "", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_od", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_do", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "pne_poza_1", "page": 1, "subpage": 0, "row": 2, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 66, "width": 402, "val_width": 66, "title_left": "Eksploatacja bez koncesji (PNE) poza granicami złoża / OG:", "title_down": None, "tbl_name": "sl_tak_nie", "null_val": True, "trigger": "trigger_pne_poza(m=False)", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="b_pne_poza", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "dlug_1", "page": 1, "subpage": 0, "row": 3, "col": 0, "r_span": 1, "c_span": 4, "type": "text_2", "item": "ruler", "max_len": 4, "validator": "000", "placeholder": "000", "zero_allowed": False, "min_max": True, "width": 130, "val_width": 40, "val_width_2": 40, "value_2": " ", "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_dlug", "tooltip": "długość wyrobiska", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_dlug_min", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_dlug_max", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "szer_1", "page": 1, "subpage": 0, "row": 3, "col": 4, "r_span": 1, "c_span": 4, "type": "text_2", "item": "ruler", "max_len": 4, "validator": "000", "placeholder": "000", "zero_allowed": False, "min_max": True, "width": 130, "val_width": 40, "val_width_2": 40, "value_2": " ", "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_szer", "tooltip": "szerokość wyrobiska", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_szer_min", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_szer_max", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "wys_1", "page": 1, "subpage": 0, "row": 3, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 4, "validator": "00.0", "placeholder": "0.0", "zero_allowed": True, "min_max": True, "width": 130, "val_width": 40, "val_width_2": 40, "value_2": " ", "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_wys", "tooltip": "wysokość wyrobiska", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_wys_min", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill()'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_wys_max", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill()']]},

                    {"name": "nadkl_1", "page": 1, "subpage": 0, "row": 4, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 3, "validator": "00.0", "placeholder": "0.0", "zero_allowed": True, "min_max": True, "width": 130, "val_width": 40, "val_width_2": 40, "value_2": " ", "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_nadkl", "tooltip": "grubość nadkładu", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_nadkl_min", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill()'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_nadkl_max", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill()']]},

                    {"name": "miaz_1", "page": 1, "subpage": 0, "row": 5, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 4, "validator": "00.0", "placeholder": "0.0", "zero_allowed": True, "min_max": True, "width": 130, "val_width": 40, "val_width_2": 40, "value_2": " ", "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_miaz", "tooltip": "miąższość kopaliny", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_miazsz_min", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_miazsz_max", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "droga_1", "page": 1, "subpage": 0, "row": 4, "col": 4, "r_span": 1, "c_span": 4, "type": "combo", "list_width": 130, "width": 130, "val_width": None, "title_left": None, "title_down": "DOJAZD DO WYROBISKA", "tbl_name": "sl_dojazd", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_dojazd", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "rodz_wyr_1", "page": 1, "subpage": 0, "row": 5, "col": 0, "r_span": 1, "c_span": 4, "type": "combo", "list_width": 130, "width": 130, "val_width": None, "title_left": None, "title_down": "RODZAJ WYROBISKA", "tbl_name": "sl_wyrobisko", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyrobisko", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "hydro_1", "page": 1, "subpage": 0, "row": 5, "col": 4, "r_span": 1, "c_span": 4, "type": "combo", "list_width": 130, "width": 130, "val_width": None, "title_left": None, "title_down": "ZAWODNIENIE", "tbl_name": "sl_zawodnienie", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_zawodn", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "stan_1", "page": 1, "subpage": 0, "row": 4, "col": 0, "r_span": 1, "c_span": 4, "type": "combo", "list_width": 130, "width": 130, "val_width": None, "title_left": None, "title_down": "STAN WYROBISKA", "tbl_name": "sl_stan_pne", "null_val": True, "trigger": "trigger_wyrobisko()", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_stan_pne", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "eksploatacja_1", "page": 1, "subpage": 0, "row": 6, "col": 0, "r_span": 1, "c_span": 4, "type": "combo", "list_width": 130, "width": 130, "val_width": None, "title_left": None, "title_down": "% POW. OBECNIE EKSPLOAT.", "tbl_name": "sl_eksploatacja", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_eksploat", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "wydobycie_1", "page": 1, "subpage": 0, "row": 6, "col": 4, "r_span": 1, "c_span": 5, "type": "combo", "list_width": 164, "width": 164, "val_width": None, "title_left": None, "title_down": "POLE EKSPLOATACYJNE CZYNNE", "tbl_name": "sl_wydobycie", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wydobycie", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "fotki_1", "page": 1, "subpage": 0, "row": 6, "col": 9, "r_span": 1, "c_span": 3, "type": "text_2", "item": "line_edit", "max_len": 2, "validator": "000", "placeholder": "0", "zero_allowed": True, "min_max": False, "width": 96, "val_width": 24, "val_width_2": None, "value_2": None, "sep_width": None, "sep_txt": None, "title_down": " ", "title_down_2": None, "title_left": "Ilość zdjęć:", "icon": None, "tooltip": "", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_ile_zalacz", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "notepad_1", "page": 1, "subpage": 0, "row": 7, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 84, "title": "UWAGI POKONTROLNE", "trigger": None, "txt_limiter": True, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyrobiska", attr="t_notatki", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']},

                    {"name": "autor_1", "page": 1, "subpage": 0, "row": 8, "col": 0, "r_span": 1, "c_span": 12, "type": "autor"},

                    {"name": "midas_id_1", "page": 1, "subpage": 1, "row": 0, "col": 0, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 8, "validator": "id", "placeholder": None, "zero_allowed": True, "min_max": False, "width": 130, "val_width": 130, "val_width_2": None, "value_2": None, "sep_width": None, "sep_txt": None, "title_down": "ID ZŁOŻA (MIDAS)", "title_down_2": None, "title_left": None, "icon": None, "tooltip": "", "trigger": "trigger_midas()", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyrobiska", attr="midas_id", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)','wyr_point_lyrs_repaint()']]},

                    {"name": "stan_midas_1", "page": 1, "subpage": 1, "row": 0, "col": 4, "r_span": 1, "c_span": 8, "type": "combo", "list_width": 266, "width": 266, "val_width": None, "title_left": None, "title_down": "STAN ZAGOSPODAROWANIA ZŁOŻA WG MIDAS", "tbl_name": "sl_stan_midas", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_stan_midas", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "okres_zloze_1", "page": 1, "subpage": 1, "row": 1, "col": 0, "r_span": 1, "c_span": 12, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "zero_allowed": True, "min_max": False, "width": 402, "val_width": 132, "val_width_2": 133, "value_2": " ", "sep_width": 1, "sep_txt": "", "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji złoża:", "icon": None, "tooltip": "", "trigger": None, "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_zloze_od", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_zloze_do", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "pne_zloze_1", "page": 1, "subpage": 1, "row": 2, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 66, "width": 402, "val_width": 66, "title_left": "Eksploatacja bez koncesji (PNE) w granicach złoża / OG:", "title_down": None, "tbl_name": "sl_tak_nie", "null_val": True, "trigger": None, "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="b_pne_zloze", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "pne_poza_m_1", "page": 1, "subpage": 1, "row": 3, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 66, "width": 402, "val_width": 66, "title_left": "Eksploatacja bez koncesji (PNE) poza granicami złoża / OG:", "title_down": None, "tbl_name": "sl_tak_nie", "null_val": True, "trigger": "trigger_pne_poza(m=True)", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="b_pne_poza", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "zagrozenia_1", "page": 1, "subpage": 2, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 82, "title": "ZAGROŻENIA DLA ŚRODOWISKA, INFRASTRUKTURY, LUDZI", "trigger": "trigger_empty('zagrozenia', 2)", "txt_limiter": True, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyr_dane", attr="t_zagrozenia", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']},

                    {"name": "stan_rekul_1", "page": 1, "subpage": 3, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 160, "width": 402, "val_width": 160, "title_left": "Stan rekultywacji:", "title_down": None, "tbl_name": "sl_stan_rekul", "null_val": True, "trigger": "trigger_rekultywacja()", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_stan_rekul", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "rekultywacja_1", "page": 1, "subpage": 3, "row": 1, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 82, "title": "WYKONANY ZAKRES PRAC REKULTYWACYJNYCH", "trigger": "trigger_rekultywacja()", "txt_limiter": True, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyr_dane", attr="t_rekultyw", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']},

                    {"name": "wyp_odpady_1", "page": 1, "subpage": 4, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 160, "width": 402, "val_width": 160, "title_left": "Stan wypełnienia wyrobiska odpadami:", "title_down": "% POWIERZCHNI", "tbl_name": "sl_wyp_odp", "null_val": True, "trigger": "trigger_odpady()", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyp_odpady", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "odpady_1", "page": 1, "subpage": 4, "row": 1, "col": 0, "r_span": 1, "c_span": 12, "type": "odpady"},

                    {"name": "odpady_opak_1", "page": 1, "subpage": 4, "row": 2, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 22, "title": "RODZAJE ODPADÓW OPAKOWANIOWYCH", "trigger": None, "txt_limiter": False, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyr_dane", attr="t_odpady_opak", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']},

                    {"name": "odpady_inne_1", "page": 1, "subpage": 4, "row": 3, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 22, "title": "RODZAJE INNYCH ODPADÓW", "trigger": None, "txt_limiter": False, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyr_dane", attr="t_odpady_inne", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']},

                    {"name": "zgloszenie_1", "page": 1, "subpage": 5, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "combo", "list_width": 160, "width": 402, "val_width": 160, "title_left": "Zgłoszenie do OUG, Starosty lub WIOŚ, inne:", "title_down": None, "tbl_name": "sl_zgloszenie", "null_val": False, "trigger": "trigger_zgloszenie()", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_zgloszenie", val="{self.cur_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "powod_1", "page": 1, "subpage": 5, "row": 1, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 82, "title": "UZASADNIENIE ZGŁOSZENIA", "trigger": None, "txt_limiter": True, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyr_dane", attr="t_powod", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']},

                    {"name": "notepad_2", "page": 2, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "text_box", "height": 84, "title": "UWAGI POKONTROLNE / POWÓD ODRZUCENIA", "trigger": None, "txt_limiter": True, "fn": ['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.wyrobiska", attr="t_notatki", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")']}
                    ]

        for dict in self.dicts:
            if dict["type"] == "combo":
                _cmb = ParamBox(self, margins=True, item="combo", list_width=dict["list_width"], width=dict["width"], val_width=dict["val_width"], title_down=dict["title_down"], title_left=dict["title_left"], trigger=dict["trigger"], fn=dict["fn"])
                if "subpage" in dict:
                    exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_cmb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                else:
                    exec(f'self.pages["page_{dict["page"]}"].glay.glay.addWidget(_cmb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                cmb_name = f'cmb_{dict["name"]}'
                self.widgets[cmb_name] = _cmb
                self.sl_load(dict["tbl_name"], self.widgets[cmb_name].valbox_1, dict["null_val"])
            if dict["type"] == "text_2":
                _txt2 = ParamBox(self, margins=True, item=dict["item"], max_len=dict["max_len"], validator=dict["validator"], placeholder=dict["placeholder"], zero_allowed=dict["zero_allowed"], min_max=dict["min_max"], width=dict["width"], value_2=dict["value_2"], val_width=dict["val_width"], val_width_2=dict["val_width_2"], sep_width=dict["sep_width"], sep_txt=dict["sep_txt"], title_down=dict["title_down"], title_down_2=dict["title_down_2"], title_left=dict["title_left"], icon=dict["icon"], tooltip=dict["tooltip"], trigger=dict["trigger"], fn=dict["fn"])
                if "subpage" in dict:
                    exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_txt2, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                else:
                    exec(f'self.pages["page_{dict["page"]}"].glay.glay.addWidget(_txt2, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                txt2_name = f'txt2_{dict["name"]}'
                self.widgets[txt2_name] = _txt2
            if dict["type"] == "text_box":
                _tb = ParamTextBox(self, margins=True, height=dict["height"], width=402, edit=True, title=dict["title"], trigger=dict["trigger"], txt_limiter=dict["txt_limiter"], fn=dict["fn"])
                if "subpage" in dict:
                    exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_tb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                else:
                    exec(f'self.pages["page_{dict["page"]}"].glay.glay.addWidget(_tb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                tb_name = f'tb_{dict["name"]}'
                self.widgets[tb_name] = _tb
            if dict["type"] == "autor":
                _ab = AutorBox(self)
                exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_ab, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                ab_name = 'ab_1'
                self.widgets[ab_name] = _ab
            if dict["type"] == "kop_wiek":
                _kw = KopalinaWiekBox(self)
                exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_kw, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                kw_name = 'kw_1'
                self.widgets[kw_name] = _kw
            if dict["type"] == "termin":
                _gd = TerminBox(self)
                exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_gd, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                gd_name = 'gd_1'
                self.widgets[gd_name] = _gd
            if dict["type"] == "pne":
                _pn = PneBox(self)
                exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_pn, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                pn_name = 'pn_1'
                self.widgets[pn_name] = _pn
            if dict["type"] == "odpady":
                _os = OdpadySelector(self)
                exec(f'self.subpages["subpage_{dict["subpage"]}"].glay.glay.addWidget(_os, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                os_name = 'os_1'
                self.widgets[os_name] = _os
        self.cur_page = 0
        self.pow_all = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)

    def sl_load(self, tbl_name, cmb, null_val=True):
        """Załadowanie wartości słownikowych z db do combobox'a."""
        db = PgConn()
        sql = f"SELECT t_val, t_desc FROM public.{tbl_name};"
        if db:
            res = db.query_sel(sql, True)
            if res:
                if null_val:
                    cmb.addItem(f"", None)
                for r in res:
                    cmb.addItem(f"  {r[1]}  ", r[0])

    def values_update(self, _dict):
        """Aktualizuje wartości parametrów."""
        params = [
            {'type': 'text_box', 'name': 'notepad','value': _dict[7], 'pages': [0, 1, 2]},
            {'type': 'text_box', 'name': 'rekultywacja','value': _dict[30], 'pages': [1]},
            {'type': 'text_box', 'name': 'zagrozenia','value': _dict[32], 'pages': [1]},
            {'type': 'text_box', 'name': 'powod','value': _dict[34], 'pages': [1]},
            {'type': 'text_2', 'name': 'okres_eksp', 'value': _dict[5], 'value_2': _dict[6], 'pages': [0, 1]},
            {'type': 'text_2', 'name': 'dlug', 'value': _dict[8], 'value_2': _dict[9], 'pages': [1]},
            {'type': 'text_2', 'name': 'szer', 'value': _dict[10], 'value_2': _dict[11], 'pages': [1]},
            {'type': 'text_2', 'name': 'wys', 'value': _dict[12], 'value_2': _dict[13], 'pages': [1]},
            {'type': 'text_2', 'name': 'nadkl', 'value': _dict[14], 'value_2': _dict[15], 'pages': [1]},
            {'type': 'text_2', 'name': 'miaz', 'value': _dict[16], 'value_2': _dict[17], 'pages': [1]},
            {'type': 'combo', 'name': 'pne_zloze', 'value': _dict[47], 'pages': [0, 1]},
            {'type': 'combo', 'name': 'pne_poza', 'value': _dict[48], 'pages': [0, 1]},
            {'type': 'combo', 'name': 'pne_poza_m', 'value': _dict[48], 'pages': [1]},
            {'type': 'text_2', 'name': 'fotki', 'value': _dict[49], 'pages': [1]},
            {'type': 'text_2', 'name': 'okres_zloze', 'value': _dict[45], 'value_2': _dict[46], 'pages': [0, 1]},
            {'type': 'kw','values': [_dict[36], _dict[37], _dict[38], _dict[39]], 'pages': [1]},
            {'type': 'gd','values': [_dict[40], _dict[41], _dict[42]], 'pages': [1]},
            {'type': 'pn','value': _dict[56], 'pages': [1]},
            {'type': 'ab', 'name': 'autor', 'value': _dict[50], 'pages': [1]},
            {'type': 'combo', 'name': 'droga', 'value': _dict[31], 'pages': [1]},
            {'type': 'combo', 'name': 'hydro', 'value': _dict[19], 'pages': [1]},
            {'type': 'combo', 'name': 'eksploatacja', 'value': _dict[20], 'pages': [1]},
            {'type': 'combo', 'name': 'wydobycie', 'value': _dict[21], 'pages': [1]},
            {'type': 'combo', 'name': 'rodz_wyr', 'value': _dict[18], 'pages': [1]},
            {'type': 'combo', 'name': 'stan_rekul', 'value': _dict[29], 'pages': [1]},
            {'type': 'combo', 'name': 'wyp_odpady', 'value': _dict[22], 'pages': [1]},
            {'type': 'combo', 'name': 'zgloszenie', 'value': _dict[33], 'pages': [1]},
            {'type': 'os','values': [_dict[23], _dict[24], _dict[25], _dict[26], _dict[27], _dict[28]], 'pages': [1]},
            {'type': 'combo', 'name': 'stan_midas', 'value': _dict[44], 'pages': [0, 1]},
            {'type': 'text_2', 'name': 'midas_id', 'value': _dict[43], 'pages': [0, 1]},
            {'type': 'combo', 'name': 'stan', 'value': _dict[35], 'pages': [1]}
        ]
        for param in params:
            if not self.cur_page in param["pages"]:
                continue
            if param["type"] == "text_box":
                txt = self.param_parser(param["value"])
                exec(f'self.widgets["tb_{param["name"]}_{self.cur_page}"].value_change(txt)')
            if param["type"] == "text_2":
                param_1 = self.param_parser(param["value"])
                exec(f'self.widgets["txt2_{param["name"]}_{self.cur_page}"].value_change("value", param_1)')
                if "value_2" in param:
                    param_2 = self.param_parser(param["value_2"])
                    exec(f'self.widgets["txt2_{param["name"]}_{self.cur_page}"].value_change("value_2", param_2)')
            if param["type"] == "combo":
                param_val = self.param_parser(param["value"])
                exec(f'self.widgets["cmb_{param["name"]}_{self.cur_page}"].value_change("value", param_val)')
            if param["type"] == "ab":
                txt = self.param_parser(param["value"])
                exec(f'self.widgets["ab_1"].value_change(txt)')
            if param["type"] == "kw":
                exec(f'self.widgets["kw_1"].set_values({param["values"]})')
            if param["type"] == "gd":
                exec(f'self.widgets["gd_1"].set_values({param["values"]})')
            if param["type"] == "pn":
                exec(f'self.widgets["pn_1"].btn_val = {param["value"]}')
            if param["type"] == "os":
                exec(f'self.widgets["os_1"].set_values({param["values"]})')
        if self.trigger_void:
            self.trigger_void = False

    def param_parser(self, val, quote=False):
        """Zwraca wartość przerobioną na tekst (pusty, jeśli None)."""
        if quote:
            txt = f'"{val}"' if val != None else f'""'
        else:
            txt = f'{val}' if val != None else str()
        return txt

    def trigger_wyrobisko(self):
        """Wykonane po zmianie wartości combobox'u 'stan_1'."""
        val = self.widgets[f"cmb_stan_1"].valbox_1.cur_val
        bool_1 = False if val[1:-1] == "brak" else True
        bool_2 = False if val[1:-1] == "Z" or val[1:-1] == "brak" or val[1:-1] == "nd" or val == "Null" else True
        # Wyświetlenie powierzchni wyrobiska:
        area_txt = f"{dlg.obj.wyr_data[4]} m\u00b2 "
        dlg.wyr_panel.area_icon.setEnabled(True)
        dlg.wyr_panel.area_label.setText(area_txt)  # Aktualizacja powierzchni wyrobiska
        # Blokada combobox'ów w zależności, czy ustalono 't_stan_pne':
        self.widgets[f"cmb_rodz_wyr_{self.cur_page}"].set_enabled(bool_1)
        self.widgets[f"cmb_hydro_{self.cur_page}"].set_enabled(bool_1)
        self.widgets[f"cmb_droga_{self.cur_page}"].set_enabled(bool_1)
        self.widgets[f"cmb_eksploatacja_{self.cur_page}"].set_enabled(bool_2)
        self.widgets[f"cmb_wydobycie_{self.cur_page}"].set_enabled(bool_2)
        if val[1:-1] == "E":  # Wyrobisko eksploatowane
            if self.widgets[f"cmb_eksploatacja_{self.cur_page}"].valbox_1.cur_val == "'0'":
                self.widgets[f"cmb_eksploatacja_{self.cur_page}"].valbox_1.set_value(None, signal=True)
            if self.widgets[f"cmb_wydobycie_{self.cur_page}"].valbox_1.cur_val == "'brak'":
                self.widgets[f"cmb_wydobycie_{self.cur_page}"].valbox_1.set_value(None, signal=True)
            if not self.has_midas and self.widgets[f"cmb_pne_poza_{self.cur_page}"].valbox_1.cur_val != "'True'":
                self.widgets[f"cmb_pne_poza_{self.cur_page}"].valbox_1.set_value("True", signal=True)
        if val[1:-1] == "Z":  # Wyrobisko zaniechane
            if self.widgets[f"cmb_eksploatacja_{self.cur_page}"].valbox_1.cur_val != "0":
                self.widgets[f"cmb_eksploatacja_{self.cur_page}"].valbox_1.set_value("0", signal=True)
            if self.widgets[f"cmb_wydobycie_{self.cur_page}"].valbox_1.cur_val != "brak":
                self.widgets[f"cmb_wydobycie_{self.cur_page}"].valbox_1.set_value("brak", signal=True)
        if val[1:-1] == "nd":  # Nie dotyczy (koncesja)
            if self.widgets[f"cmb_eksploatacja_{self.cur_page}"].valbox_1.cur_val != None:
                self.widgets[f"cmb_eksploatacja_{self.cur_page}"].valbox_1.set_value(None, signal=True)
            if self.widgets[f"cmb_wydobycie_{self.cur_page}"].valbox_1.cur_val != None:
                self.widgets[f"cmb_wydobycie_{self.cur_page}"].valbox_1.set_value(None, signal=True)
        if val[1:-1] == "E" or val[1:-1] == "Z" or val[1:-1] == "nd" or val == "Null":
            # Odblokowanie wymiarów wyrobiska, jeśli zablokowane:
            p1_list = ["dlug", "szer"]
            p2_list = ["wys", "nadkl", "miaz"]
            b_teren = self.widgets["gd_1"].fchk_val  # Czy przeprowadzono kontrolę terenową?
            for p1 in p1_list:
                if not self.widgets[f"txt2_{p1}_{self.cur_page}"].is_enabled:
                    self.widgets[f"txt2_{p1}_{self.cur_page}"].set_enabled(True)
            for p2 in p2_list:
                if b_teren and not self.widgets[f"txt2_{p2}_{self.cur_page}"].is_enabled:
                    self.widgets[f"txt2_{p2}_{self.cur_page}"].set_enabled(True)
            if not self.widgets[f"cmb_pne_poza_{self.cur_page}"].isEnabled():
                self.widgets[f"cmb_pne_poza_{self.cur_page}"].setEnabled(True)
            if self.cur_page == 1:
                if not self.widgets[f"cmb_pne_poza_m_{self.cur_page}"].isEnabled():
                    self.widgets[f"cmb_pne_poza_m_{self.cur_page}"].setEnabled(True)
            if not self.widgets[f"cmb_pne_zloze_{self.cur_page}"].isEnabled():
                self.widgets[f"cmb_pne_zloze_{self.cur_page}"].setEnabled(True)
        elif val[1:-1] == "brak":  # Brak wyrobiska
            # Kasowanie i blokowanie wymiarów wyrobiska:
            txt_list = ["dlug", "szer", "wys", "nadkl", "miaz"]
            for t in txt_list:
                if self.widgets[f"txt2_{t}_{self.cur_page}"].valbox_1.cur_val:
                    self.widgets[f"txt2_{t}_{self.cur_page}"].valbox_1.value_change(None)
                if self.widgets[f"txt2_{t}_{self.cur_page}"].valbox_2.cur_val:
                    self.widgets[f"txt2_{t}_{self.cur_page}"].valbox_2.value_change(None)
                self.widgets[f"txt2_{t}_{self.cur_page}"].set_enabled(False)
            # Kasowanie i blokowanie parametrów wyrobiska:
            cmb_list = ["rodz_wyr", "hydro", "eksploatacja", "wydobycie", "droga"]
            for c in cmb_list:
                if self.widgets[f"cmb_{c}_{self.cur_page}"].valbox_1.cur_val != "Null":
                    self.widgets[f"cmb_{c}_{self.cur_page}"].valbox_1.set_value(None, signal=True)
            # Kasowanie odpadów:
            odp_val = self.widgets["cmb_wyp_odpady_1"].valbox_1.cur_val
            if odp_val != 'Null' and odp_val[1:-1] != '0':
                self.widgets["cmb_wyp_odpady_1"].valbox_1.set_value(None, signal=True)
            # Wyłączenie powierzchni wyrobiska:
            dlg.wyr_panel.area_icon.setEnabled(False)
            dlg.wyr_panel.area_label.setText("")
            # Automatyczne ustawienie 'pne_zloze' i 'pne_poza' na NIE:
            self.set_pne_to_false()
        # if val[1:-1] == "nd":
        #     self.set_pne_to_false()

    def trigger_midas(self):
        """Wykonywane po zmianie wartości textbox'u 'midas_id'."""
        val = self.widgets[f"txt2_midas_id_{self.cur_page}"].valbox_1.cur_val
        self.has_midas = True if val else False
        if self.cur_page == 1:
            # Kontrola podświetlenia tytułu zakładki:
            dlg.wyr_panel.tab_box.widgets["btn_1"].active = self.has_midas
            # Ustawienie widoczności cmb_pne_poza_m:
            self.widgets[f"cmb_pne_poza_m_{self.cur_page}"].setVisible(self.has_midas)
        # Ustawienie widoczności widgetów:
        self.widgets[f"cmb_stan_midas_{self.cur_page}"].setVisible(self.has_midas)
        self.widgets[f"txt2_okres_zloze_{self.cur_page}"].setVisible(self.has_midas)
        self.widgets[f"cmb_pne_zloze_{self.cur_page}"].setVisible(self.has_midas)
        if not self.has_midas:
            # Brak podanego midas_id - wyczyszczenie parametrów związanych ze złożami, jeśli są wypełnione:
            if self.widgets[f"cmb_stan_midas_{self.cur_page}"].valbox_1.cur_val != "Null":
                self.widgets[f"cmb_stan_midas_{self.cur_page}"].valbox_1.set_value(None, signal=True)
            if self.widgets[f"txt2_okres_zloze_{self.cur_page}"].valbox_1.cur_val:
                self.widgets[f"txt2_okres_zloze_{self.cur_page}"].valbox_1.value_change(None)
            if self.widgets[f"txt2_okres_zloze_{self.cur_page}"].valbox_2.cur_val:
                self.widgets[f"txt2_okres_zloze_{self.cur_page}"].valbox_2.value_change(None)
            # Odblokowanie cmb_pne_poza_1, jeśli jest zablokowane:
            if not self.widgets[f"cmb_pne_poza_{self.cur_page}"].isEnabled() and self.widgets[f"cmb_stan_1"].valbox_1.cur_val != "brak":
                self.widgets[f"cmb_pne_poza_{self.cur_page}"].setEnabled(True)
            # Sztywne ustawienie atrybutów PNE_ZLOZE i CZY_PNE, jeśli mają nieprawidłowe wartości:
            if self.widgets[f"cmb_pne_zloze_{self.cur_page}"].valbox_1.cur_val != "'False'":
                # PNE_ZLOZE = NIE
                self.widgets[f"cmb_pne_zloze_{self.cur_page}"].valbox_1.set_value("False", signal=True)
            if not self.widgets['pn_1'].btn_val:  # Wyrobisko nie powiązane ze złożem MUSI być PNE
                # CZY_PNE = TAK
                self.widgets['pn_1'].btn_val = True
                db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="b_pne", val=True, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        else:  # Wyrobisko jest powiązane ze złożem
            if not self.widgets['pn_1'].btn_val:  # Wyrobisko dotyczy ZŁOŻA NIEZREKULTYWOWANEGO (CZY_PNE = NIE)
                self.set_pne_to_false()
            else:  # Wyrobisko dotyczy PNE (CZY_PNE = TAK)
                self.widgets[f"cmb_pne_zloze_{self.cur_page}"].setEnabled(True)
                self.widgets[f"cmb_pne_poza_{self.cur_page}"].setEnabled(True)
                if self.cur_page == 1:
                    self.widgets[f"cmb_pne_poza_m_{self.cur_page}"].setEnabled(True)

    def set_pne_to_false(self):
        """Automatyczne ustawienie PNE_ZLOZE i PNE_POZA na wartość NIE."""
        if self.widgets[f"cmb_pne_zloze_{self.cur_page}"].valbox_1.cur_val != "'False'":
            self.widgets[f"cmb_pne_zloze_{self.cur_page}"].valbox_1.set_value("False", signal=True)
        if self.widgets[f"cmb_pne_poza_{self.cur_page}"].valbox_1.cur_val != "'False'":
            self.widgets[f"cmb_pne_poza_{self.cur_page}"].valbox_1.set_value("False", signal=True)
        self.widgets[f"cmb_pne_zloze_{self.cur_page}"].setEnabled(False)
        self.widgets[f"cmb_pne_poza_{self.cur_page}"].setEnabled(False)
        if self.cur_page == 1:
            if self.widgets[f"cmb_pne_poza_m_{self.cur_page}"].valbox_1.cur_val != "'False'":
                self.widgets[f"cmb_pne_poza_m_{self.cur_page}"].valbox_1.set_value("False")
            self.widgets[f"cmb_pne_poza_m_{self.cur_page}"].setEnabled(False)

    def trigger_rekultywacja(self):
        """Wykonywane po zmianie wartości combobox'u 'stan_rekul', albo textbox'u 'rekultywacja'."""
        val_1 = self.widgets["cmb_stan_rekul_1"].valbox_1.cur_val
        if not val_1:
            return
        val_2 = self.widgets["tb_rekultywacja_1"].txtbox.cur_val
        if val_1[1:-1] == 'tak' or val_1[1:-1] == 'w_t' or val_2:
            dlg.wyr_panel.tab_box.widgets["btn_3"].active = True
        else:
            dlg.wyr_panel.tab_box.widgets["btn_3"].active = False

    def trigger_zgloszenie(self):
        """Wykonywane po zmianie wartości combobox'u 'zgloszenie'."""
        val = self.widgets["cmb_zgloszenie_1"].valbox_1.cur_val
        if not val:
            return
        if val[1:-1] == 'brak':
            dlg.wyr_panel.tab_box.widgets["btn_5"].active = False
            self.widgets["tb_powod_1"].setVisible(False)
            if self.widgets["tb_powod_1"].txtbox.cur_val:
                self.widgets["tb_powod_1"].txtbox.cur_val = None
                self.widgets["tb_powod_1"].txtbox.db_update(txt_val=None, tbl=f"team_{dlg.team_i}.wyr_dane", attr="t_powod", sql_bns=f" WHERE wyr_id = {dlg.obj.wyr}")
        else:
            dlg.wyr_panel.tab_box.widgets["btn_5"].active = True
            self.widgets["tb_powod_1"].setVisible(True)

    def trigger_odpady(self):
        """Wykonywane po zmianie wartości combobox'u 'wyp_odpady'."""
        val = self.widgets["cmb_wyp_odpady_1"].valbox_1.cur_val
        if not val:
            return
        _bool = False if val == 'Null' or val[1:-1] == '0' else True
        dlg.wyr_panel.tab_box.widgets["btn_4"].active = _bool
        self.widgets["os_1"].setVisible(_bool)
        if not _bool:
            self.widgets["os_1"].clear_all()

    def trigger_pne_poza(self, m):
        """Wykonywane po zmianie 'cmb_pne_poza_1' (m=False) lub 'cmb_pne_poza_m_1' (m=True)."""
        if self.widgets["cmb_pne_poza_1"].valbox_1.cur_val != self.widgets["cmb_pne_poza_m_1"].valbox_1.cur_val:
            # Wartości w dwóch cmb są różne (po zmianie jednego, trzeba zaktualizować drugie)
            if m:  # Trzeba zaktualizować 'cmb_pne_poza_1' do wartości z 'cmb_pne_poza_m_1'
                val = self.widgets["cmb_pne_poza_m_1"].valbox_1.cur_val
                val = val[1:-1] if val != "Null" else None
                self.widgets[f"cmb_pne_poza_1"].valbox_1.set_value(val)
            else:  # Trzeba zaktualizować 'cmb_pne_poza_m_1' do wartości z 'cmb_pne_poza_1'
                val = self.widgets["cmb_pne_poza_1"].valbox_1.cur_val
                val = val[1:-1] if val != "Null" else None
                self.widgets[f"cmb_pne_poza_m_1"].valbox_1.set_value(val)

    def trigger_empty(self, tb_name, tab_idx):
        """Zmiana stanu 'active' dla przycisku tabbox'u po zmianie wartości paramtextbox'u'."""
        val = self.widgets[f"tb_{tb_name}_1"].txtbox.cur_val
        if val:
            dlg.wyr_panel.tab_box.widgets[f"btn_{tab_idx}"].active = True
        else:
            dlg.wyr_panel.tab_box.widgets[f"btn_{tab_idx}"].active = False

    def wdf_sel_change(self):
        """Zmiana zaznaczonego wiersza w tv_wdf."""
        sel_tv = self.tv_wdf.selectionModel()
        index = sel_tv.currentIndex()
        if index.row() == -1:
            # Nie ma zaznaczonego wiersza w tv_wdf
            return
        else:
            id = int(index.sibling(index.row(), 1).data())
            if id in dlg.obj.wyr_ids:
                if dlg.obj.wyr != id:
                    dlg.obj.wyr = id
                    dlg.obj.pan_to_object("wyr")
            else:
                dlg.obj.wyr = None

    def miaz_fill(self):
        """Uzupełnia wartość miąższości kopaliny jako różnicy wysokości i nadkładu. Dodatkowo kasuje wartość nadkładu, jeśli przewyższa wysokość."""
        wys_min_txt = dlg.wyr_panel.widgets["txt2_wys_1"].valbox_1.cur_val
        wys_max_txt = dlg.wyr_panel.widgets["txt2_wys_1"].valbox_2.cur_val
        nadkl_min_txt = dlg.wyr_panel.widgets["txt2_nadkl_1"].valbox_1.cur_val
        nadkl_max_txt = dlg.wyr_panel.widgets["txt2_nadkl_1"].valbox_2.cur_val
        if wys_min_txt == None or nadkl_min_txt == None:
            miaz_min = None
        else:
            wys_min = float(wys_min_txt)
            nadkl_min = float(nadkl_min_txt)
            miaz_min = wys_min - nadkl_min
            if miaz_min < 0.0:
                dlg.wyr_panel.widgets["txt2_nadkl_1"].valbox_1.value_change(None)
                return
        if wys_max_txt == None or nadkl_max_txt == None:
            miaz_max = None
        else:
            wys_max = float(wys_max_txt)
            nadkl_max = float(nadkl_max_txt)
            miaz_max = wys_max - nadkl_max
            if miaz_max < 0.0:
                dlg.wyr_panel.widgets["txt2_nadkl_1"].valbox_2.value_change(None)
                return
        # Sprawdzenie, czy nie ma potrzeby odwrócić wartości:
        if miaz_min and miaz_max and miaz_min > miaz_max:
            miaz_min, miaz_max = miaz_max, miaz_min
        dlg.wyr_panel.focus_void = True
        dlg.wyr_panel.widgets["txt2_miaz_1"].valbox_1.value_change(miaz_min)
        dlg.wyr_panel.widgets["txt2_miaz_1"].valbox_2.value_change(miaz_max)
        dlg.wyr_panel.focus_void = False

    def wdf_sel_update(self):
        """Aktualizacja zaznaczenia wiersza w tv_wdf."""
        index = self.tv_wdf.model().match(self.tv_wdf.model().index(0, 1), Qt.DisplayRole, str(dlg.obj.wyr))
        if index:
            self.tv_wdf.scrollTo(index[0])
            self.tv_wdf.setCurrentIndex(index[0])
        else:
            sel_tv = self.tv_wdf.selectionModel()
            sel_tv.clearCurrentIndex()
            sel_tv.clearSelection()
            self.tv_wdf.scrollToTop()

    def page_change(self, index):
        """Zmiana aktywnej strony stackedbox'a."""
        self.cur_page = index

    def exit_clicked(self):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        dlg.obj.wyr = None

    def wyr_delete(self):
        """Usunięcie wyrobiska z bazy danych."""
        m_text = "Wyrobisko wraz ze wszystkimi informacjami o nim zostanie trwale usunięte z bazy danych. Czy chcesz kontynuować?"
        reply = QMessageBox.question(iface.mainWindow(), "Kasowanie wyrobiska", m_text, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        db = PgConn()
        sql = "DELETE FROM team_" + str(dlg.team_i) + ".wyrobiska WHERE wyr_id = " + str(dlg.obj.wyr) + ";"
        if db:
            res = db.query_upd(sql)
            if res:
                dlg.obj.wyr = None
        # Aktualizacja listy wyrobisk w ObjectManager:
        dlg.obj.wyr_ids = get_wyr_ids()
        wyr_layer_update(False)


class BasemapCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi podkładów mapowych."""
    def __init__(self, *args, dlg):
        super().__init__(*args)
        self.dlg = dlg
        self.canvas = self.parent()
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(43)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.date_box = MoekHBox(self, margins=[5, 5, 5, 5])
        self.date_box.setObjectName("date_box")
        self.box = MoekHBox(self, margins=[5, 5, 5, 5])
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    QFrame#date_box{background-color: rgba(30, 30, 30, 0.6); border: none}
                    QFrame#box{background-color: rgba(30, 30, 30, 0.6); border: none}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(1)
        self.setLayout(self.lay)
        self.lay.addWidget(self.date_box)
        self.lay.setAlignment(self.date_box, Qt.AlignLeft | Qt.AlignVCenter)
        self.lay.addWidget(self.box)
        self.lay.setAlignment(self.box, Qt.AlignLeft)
        self.date_indicator = DateIndicator(self, dlg=self.dlg)
        self.date_box.lay.addWidget(self.date_indicator)
        self.date_box.lay.setAlignment(self.date_indicator, Qt.AlignLeft | Qt.AlignVCenter)
        self.date_selector = DateSelector(self, dlg=self.dlg)
        self.box.lay.addWidget(self.date_selector)
        self.box.lay.setAlignment(self.date_selector, Qt.AlignLeft | Qt.AlignVCenter)
        self.map = None
        self.t_void = False  # Blokada stopera zmiany zasięgu mapcanvas'u
        self.ge_sync = None  # Czy włączony jest tryb synchronizacji widoku QGIS w GEP
        self.rendering = False  # Czy mapcanvas jest w trakcie odświeżania?
        self.extent = None  # Zasięg geoprzestrzenny aktualnego widoku mapy
        self.timer = None  # Obiekt stopera zmiany zasięgu mapcanvas'u
        self.canvas.extentsChanged.connect(self.extent_changed)
        self.canvas.renderStarting.connect(lambda: self.render_changed(True))
        self.canvas.renderComplete.connect(lambda: self.render_changed(False))
        # self.canvas.mapCanvasRefreshed.connect(self.canvas_refreshed)
        self.date = None
        self.ga_date = None
        self.date_str = None
        self.date_uri = None
        self.ga_layer = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "map" and val != None:
            self.check_extent()
            if self.map == "Geoportal Archiwalny" and self.ga_date:
                self.date = self.ga_date
            elif self.map == "Google Earth Pro":
                self.dlg.ge.is_on = True
            else:
                self.dlg.ge.is_on = False
        elif attr == "extent" and not self.t_void:
            # print("extent")
            if self.ge_sync and self.map != "Google Earth Pro":
                self.dlg.ge.q2ge()  # Aktualizacja zasięgu widoku w GEP
            elif self.ge_sync or self.map == "Google Earth Pro":
                # self.dlg.ge.loaded = False
                # self.dlg.ge.load_status = None
                self.dlg.ge.q2ge()  # Aktualizacja zasięgu widoku w GEP
                # self.dlg.ge.start_updater()
                QTimer.singleShot(10, self.dlg.ge.start_updater)
                # self.dlg.ge.start_loader()  # Uruchomienie stopera ładowania
            elif self.ge_sync == False and self.map != "Google Earth Pro":
                self.dlg.ge.ge_probe()
            if self.map == "Geoportal":
                date_list = self.dates_from_extent(last=True)
                self.date_selector.dates = date_list
            elif self.map == "Geoportal Archiwalny":
                if self.canvas.scale() > 50001:
                    self.date_selector.dates = []
                    return
                date_list = self.dates_from_extent()
                self.date_selector.dates = date_list
            else:
                self.date_selector.dates = []
        elif attr == "date" and val != None:
            self.date_str = f"{val.year}-{str(val.month).zfill(2)}-{str(val.day).zfill(2)}"
            date_next = val + datetime.timedelta(days=1)
            self.date_uri = f"{date_next.year}-{str(date_next.month).zfill(2)}-{str(date_next.day).zfill(2)}"
            self.date_indicator.date = self.date_str
            if self.map == "Geoportal Archiwalny":
                self.ga_date_update()
            self.date_checked_update()

    # def canvas_refreshed(self):
    #     print("---------------[canvas_refreshed]---------------")

    def render_changed(self, flag):
        """Ustala status renderowania mapcanvas'u."""
        # print("[render_changed]")
        if self.rendering != flag:
            self.rendering = flag
        # if self.rendering:
        #     print("render start")

    def extent_changed(self):
        """Zmiana zasięgu geoprzestrzennego widoku mapy."""
        if self.t_void:
            # Wyjście z funkcji, jeśli stoper obecnie pracuje
            return
        # print("+++++++++++++++[extent_change start]+++++++++++++++")
        self.dlg.ge.update_timer_reset()
        self.dlg.ge.blocker = True
        # print("freeze start")
        self.t_void = True
        self.extent = self.canvas.extent()
        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.check_extent)
        self.timer.start()  # Odpalenie stopera

    def check_extent(self):
        """Sprawdzenie, czy zakres widoku mapy przestał się zmieniać."""
        if self.extent != self.canvas.extent():  # Zmienił się
            self.extent = self.canvas.extent()
        else:
            # Kasowanie stopera:
            if self.timer:
                self.timer.stop()
                self.timer = None
            self.t_void = False
            # self.dlg.ge.blocker = False
            print("+++++++++++++++[extent_change stop]+++++++++++++++")
            self.extent = self.canvas.extent()

    def dates_from_extent(self, last=False):
        x1 = self.extent.xMinimum()
        x2 = self.extent.xMaximum()
        y1 = self.extent.yMinimum()
        y2 = self.extent.yMaximum()
        x_dif = abs(x2 - x1)
        y_dif = abs(y2 - y1)
        x1 = x1 + x_dif/4
        x2 = x2 - x_dif/4
        y1 = y1 + y_dif/4
        y2 = y2 - y_dif/4
        extent_bound = f'ST_MakeEnvelope({x1}, {y1}, {x2}, {y2}, 2180)'
        db = PgConn()
        if last:
            sql = f"SELECT akt_data FROM external.skorowidz_geoportal AS s WHERE ST_Intersects(s.geom, {extent_bound}) ORDER BY akt_data DESC;"
        else:
            sql = f"SELECT akt_data FROM external.skorowidz_geoportal AS s WHERE ST_Intersects(s.geom, {extent_bound}) ORDER BY akt_data;"
        if db:
            res = db.query_sel(sql, False) if last else db.query_sel(sql, True)
            if res:
                if len(res) > 1:
                    return list(zip(*res))[0]
                else:
                    return list(res)
            else:
                return None

    def ga_date_update(self):
        """Aktualizacja URI dla warstwy Geoportal Archiwalny."""
        uri = f'IgnoreGetFeatureInfoUrl=1&IgnoreGetMapUrl=0&contextualWMSLegend=0&SmoothPixmapTransform=1&IgnoreReportedLayerExtents=1&crs=EPSG:2180&format=image/jpeg&layers=Raster&styles=&version=1.1.1&url=https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolutionTime?TIME={self.date_uri}T00%3A00%3A00.000%2B01%3A00'
        ga_layer = dlg.proj.mapLayersByName("Geoportal Archiwalny")[0]
        ga_layer.dataProvider().setDataSourceUri(uri)
        self.ga_date = self.date
        self.canvas.zoomScale(self.canvas.scale() + 0.001)  # Sposó☺b na odświeżenie warstwy, bez wyczyszczenia cache'u (białe tło w trakcie ładowania)

    def date_checked_update(self):
        """Aktualizacja stanów DateSelectorItem."""
        sync = False
        for widget in self.date_selector.widgets:
            if widget.date_str == self.date_str:
                widget.setChecked(True)
                sync = True
            else:
                widget.setChecked(False)
        if not sync:
            self.set_closest_date()

    def set_closest_date(self):
        """Wybór daty z listy dostępnych dat, która jest najbliższa do obecnie ustalonej."""
        date_list = self.date_selector.dates
        if len(date_list) == 0:
            return
        res = min(date_list, key=lambda sub: abs(sub - self.date))
        self.date = res
        self.date_checked_update()


class DateIndicator(QFrame):
    """Widget wyboru dat dla podkładu Geoportal Archiwalny."""
    def __init__(self, *args, dlg):
        super().__init__(*args)
        self.dlg = dlg
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(96, 33)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: 1px solid white}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(5, 5, 5, 5)
        self.lay.setSpacing(0)
        self.setLayout(self.lay)
        self.date_label = PanelLabel(self, size=11)
        self.lay.addWidget(self.date_label)
        self.lay.setAlignment(self.date_label, Qt.AlignCenter)
        self.date = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "date" and val != None:
            self.date_label.setText(val)


class DateSelector(QFrame):
    """Widget wyboru dat dla podkładu Geoportal Archiwalny."""
    def __init__(self, *args, dlg):
        super().__init__(*args)
        self.dlg = dlg
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(0, 33)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)
        self.setLayout(self.lay)
        self.widgets = []
        self.init_void = True
        self.d_cnt = 1
        self.dates = []
        # self.init_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "dates" and not self.init_void:
            d_cnt = len(val)
            # print(f"d_cnt: {d_cnt}, self.d_cnt: {self.d_cnt}")
            if d_cnt == 0 and self.d_cnt == 0:
                return
            elif d_cnt == 0 and self.d_cnt > 0:
                self.dlg.bm_panel.hide()
                self.dlg.bm_panel.setFixedWidth(110)
                self.clear_all_dates()
                self.d_cnt = 0
                return
            elif d_cnt == 1:# and self.d_cnt > 0:
                self.dlg.bm_panel.box.setVisible(False)
                self.dlg.bm_panel.setFixedWidth(110)
            if self.dlg.bm_panel.isHidden():
                self.dlg.bm_panel.show()
            if not self.dlg.bm_panel.box.isVisible() and d_cnt > 1:
                self.dlg.bm_panel.box.setVisible(True)
            self.clear_all_dates()
            for date in val:
                _date = DateSelectorItem(self, dlg=self.dlg, date=date)
                self.dlg.bm_panel.date_selector.lay.addWidget(_date)
                # self.lay.setAlignment(_date, Qt.AlignHCenter | Qt.AlignTop)
                self.widgets.append(_date)
            self.setFixedWidth(d_cnt * 48)
            self.dlg.bm_panel.setFixedWidth(117 + d_cnt * 48)
            self.d_cnt = d_cnt
            self.dlg.bm_panel.date_checked_update()

    def clear_all_dates(self):
        """Wyczyszczenie wszystkich obiektów dat."""
        for widget in self.widgets:
            widget.setParent(None)
            del widget
        self.widgets = []

    def btn_clicked(self, date):
        """Włączenie/wyłączenie powiatu po naciśnięciu przycisku."""
        self.dlg.bm_panel.date = date


class DateSelectorItem(QPushButton):
    """Guzik do wyboru daty aktualności podkładu Geoportal Archiwalny."""
    def __init__(self, *args, dlg, date):
        super().__init__(*args)
        self.dlg = dlg
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCheckable(True)
        self.setFixedSize(48, 33)
        self.setText(str(date.year))
        self.date = date
        self.date_str = f"{date.year}-{str(date.month).zfill(2)}-{str(date.day).zfill(2)}"
        if self.dlg.bm_panel.date_indicator.date == self.date_str:
            self.setChecked(True)
        self.setToolTip(self.date_str)
        self.setStyleSheet("""
                            QPushButton {
                                border: none;
                                background: transparent;
                                color: rgba(255, 255, 255, 0.8);
                                font-size: 10pt;
                                font-weight: normal;
                                padding-top: -2px;
                            }
                            QPushButton:checked {
                                border: 1px solid white;
                                background: transparent;
                                color: rgba(255, 255, 255, 1.0);
                                font-size: 10pt;
                                font-weight: normal;
                                padding-top: -2px;
                            }
                            QPushButton:hover {
                                border: none;
                                background: rgba(255, 255, 255, 0.4);
                                color: rgba(0, 0, 0, 1.0);
                                font-size: 10pt;
                                font-weight: normal;
                                padding-top: -2px;
                            }
                            QPushButton:hover:checked {
                                border: 1px solid white;
                                background: transparent;
                                color: rgba(255, 255, 255, 1.0);
                                font-size: 10pt;
                                font-weight: normal;
                                padding-top: -2px;
                            }
                            QToolTip {
                                border: 1px solid rgb(50, 50, 50);
                                padding: 5px;
                                background-color: rgb(30, 30, 30);
                                color: rgb(200, 200, 200);
                            }
                           """)
        self.clicked.connect(lambda: self.parent().btn_clicked(self.date))


class FlagCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi flag."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setFixedWidth(350)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        shadow_1 = QGraphicsDropShadowEffect(blurRadius=16, color=QColor(0, 0, 0, 220), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow_1)
        self.bar = CanvasPanelTitleBar(self, title="Flagi", width=self.width())
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.6); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    QFrame#sp{background-color: rgba(55, 55, 55, 0.71); border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        self.sp_main = CanvasHSubPanel(self, height=32, spacing=1)
        self.box.lay.addWidget(self.sp_main)
        self.idbox = CanvasHSubPanel(self, height=32, margins=[0, 0, 0, 0], spacing=0, alpha=0.71)
        self.sp_main.lay.addWidget(self.idbox)
        self.id_spinbox = IdSpinBox(self, _obj="flag", height=32)
        self.idbox.lay.addWidget(self.id_spinbox)
        self.hashbox = CanvasHSubPanel(self, height=32, margins=[2, 1, 2, 1], spacing=3, alpha=0.71)
        self.sp_main.lay.addWidget(self.hashbox)
        self.hash_icon = MoekButton(self, name="hash", size=30, checkable=False, enabled=False, tooltip="numer roboczy, terenowy")
        self.hashbox.lay.addWidget(self.hash_icon)
        self.hash = CanvasLineEdit(self, width=117, height=28, font_size=12, max_len=10, validator=None, theme="dark", fn=['db_attr_change(tbl="team_{dlg.team_i}.flagi", attr="teren_id", val="'"{self.sql_parser(self.cur_val)}"'", sql_bns=" WHERE id = {dlg.obj.flag}", user=False)'], placeholder="XXXXXXXXXX")
        self.hashbox.lay.addWidget(self.hash)
        self.toolbox = CanvasHSubPanel(self, height=32, margins=[0, 0, 0, 0], spacing=0, alpha=0.71)
        self.sp_main.lay.addWidget(self.toolbox)
        self.flag_tools = FlagTools(self)
        self.toolbox.lay.addWidget(self.flag_tools)
        self.separator_1 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.box.lay.addWidget(self.separator_1)
        self.sp_notepad = CanvasHSubPanel(self, height=102, alpha=0.71)
        self.sp_notepad.setObjectName("sp")
        self.box.lay.addWidget(self.sp_notepad)
        fn = ['self.db_update(txt_val=self.cur_val, tbl=f"team_{str(dlg.team_i)}.flagi", attr="t_notatki", sql_bns=f" WHERE id = {dlg.obj.flag}")']
        self.notepad_box = ParamTextBox(self, margins=True, height=82, width=332, edit=True, title="NOTATKI", fn=fn)
        self.sp_notepad.lay.addWidget(self.notepad_box)

    def exit_clicked(self):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        dlg.obj.flag = None


class ParkingCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi parkingów."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setFixedWidth(350)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        shadow_1 = QGraphicsDropShadowEffect(blurRadius=16, color=QColor(0, 0, 0, 220), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow_1)
        self.bar = CanvasPanelTitleBar(self, title="Miejsca parkowania", width=self.width())
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.6); border: none}
                    QFrame#box{background-color: rgba(55, 55, 55, 0.71); border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        self.sp_tools = CanvasHSubPanel(self, height=32, alpha=0.71)
        self.box.lay.addWidget(self.sp_tools)
        self.id_label = PanelLabel(self, text="  Id:", size=12)
        self.sp_tools.lay.addWidget(self.id_label)
        self.id_box = IdSpinBox(self, _obj="parking", height=30)
        self.sp_tools.lay.addWidget(self.id_box)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.sp_tools.lay.addItem(spacer)
        self.parking_tools = ParkingTools(self)
        self.sp_tools.lay.addWidget(self.parking_tools)

    def exit_clicked(self):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        dlg.obj.parking = None


class MarszCanvasPanel(QFrame):
    """Widget menu przyborne dla marszrut."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(112, 48)
        self.setObjectName("main")
        self.pointer = MoekPointer(self)
        self.pointer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.pointer.setFixedSize(12, 6)
        self.pointer.setObjectName("pointer")
        self.box = QFrame()
        self.box.setObjectName("box")
        self.box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    QFrame#box{background-color: rgba(20, 20, 20, 0.8); border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)
        vlay.addWidget(self.pointer)
        vlay.addWidget(self.box)
        vlay.setAlignment(self.pointer, Qt.AlignCenter)
        self.setLayout(vlay)
        self.marsz_continue = MoekButton(self, name="line_continue", size=34, tooltip="kontynuuj rysowanie marszruty")
        self.marsz_edit = MoekButton(self, name="line_edit", size=34, tooltip="edytuj linię marszruty")
        self.trash = MoekButton(self, name="marsz_trash", size=34, tooltip="usuń marszrutę")
        hlay = QHBoxLayout()
        hlay.setContentsMargins(4, 4, 4, 4)
        hlay.setSpacing(1)
        hlay.addWidget(self.marsz_continue)
        hlay.addWidget(self.marsz_edit)
        hlay.addWidget(self.trash)
        self.box.setLayout(hlay)
        self.marsz_continue.clicked.connect(lambda: dlg.mt.init("marsz_continue"))
        self.marsz_edit.clicked.connect(lambda: dlg.mt.init("marsz_edit"))
        self.trash.clicked.connect(self.marsz_delete)

    def marsz_delete(self):
        """Usunięcie marszruty z bazy danych."""
        db = PgConn()
        sql = "DELETE FROM team_" + str(dlg.team_i) + ".marsz WHERE marsz_id = " + str(dlg.obj.marsz) + ";"
        if db:
            res = db.query_upd(sql)
            if res:
                dlg.obj.marsz = None
        # Aktualizacja listy marszrut w ObjectManager:
        dlg.obj.marsz_ids = get_marsz_ids()
        marsz_layer_update()


class WnCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi punktów WN_PNE."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(350)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        shadow_1 = QGraphicsDropShadowEffect(blurRadius=16, color=QColor(0, 0, 0, 220), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow_1)
        self.bar = CanvasPanelTitleBar(self, title="WN_Kopaliny_PNE", width=self.width())
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.6); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    QFrame#sp{background-color: rgba(55, 55, 55, 0.71); border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        self.sp_id = CanvasHSubPanel(self, height=34)
        self.sp_id.setObjectName("sp")
        self.box.lay.addWidget(self.sp_id)
        self.separator_1 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.box.lay.addWidget(self.separator_1)
        self.top_margin = CanvasHSubPanel(self, height=8)
        self.top_margin.setObjectName("sp")
        self.box.lay.addWidget(self.top_margin)
        self.id_label = PanelLabel(self, text="   Id_arkusz:", size=11)
        self.sp_id.lay.addWidget(self.id_label)
        self.id_box = IdSpinBox(self, _obj="wn", width=134, height=32, max_len=8, validator="id_arkusz")
        self.sp_id.lay.addWidget(self.id_box)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.sp_id.lay.addItem(spacer)
        self.params_1 = CanvasHSubPanel(self, height=40, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_1.setObjectName("sp")
        self.box.lay.addWidget(self.params_1)
        self.kopalina = ParamBox(self, width=217, title_down="KOPALINA")
        self.params_1.lay.addWidget(self.kopalina)
        self.data_inw = ParamBox(self, width=103, title_down="DATA INWENTARYZACJI")
        self.params_1.lay.addWidget(self.data_inw)
        self.params_2 = CanvasHSubPanel(self, height=40, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_2.setObjectName("sp")
        self.box.lay.addWidget(self.params_2)
        self.wyrobisko = ParamBox(self, title_down="WYROBISKO")
        self.params_2.lay.addWidget(self.wyrobisko)
        self.zawodn = ParamBox(self, title_down="ZAWODNIENIE")
        self.params_2.lay.addWidget(self.zawodn)
        self.params_3 = CanvasHSubPanel(self, height=40, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_3.setObjectName("sp")
        self.box.lay.addWidget(self.params_3)
        self.eksploat = ParamBox(self, title_down="EKSPLOATACJA")
        self.params_3.lay.addWidget(self.eksploat)
        self.odpady = ParamBox(self, title_down="WYPEŁNIENIE ODPADAMI")
        self.params_3.lay.addWidget(self.odpady)
        self.params_4 = CanvasHSubPanel(self, height=40, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_4.setObjectName("sp")
        self.box.lay.addWidget(self.params_4)
        self.dlug_max = ParamBox(self, title_left="Długość maks. [m]:")
        self.params_4.lay.addWidget(self.dlug_max)
        self.szer_max = ParamBox(self, title_left="Szerokość maks. [m]:")
        self.params_4.lay.addWidget(self.szer_max)
        self.params_5 = CanvasHSubPanel(self, height=40, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_5.setObjectName("sp")
        self.box.lay.addWidget(self.params_5)
        self.wysokosc = ParamBox(self, width=328, value_2=" ", title_down="MIN", title_down_2="MAX", title_left="Wysokość wyrobiska [m]:")
        self.params_5.lay.addWidget(self.wysokosc)
        self.params_6 = CanvasHSubPanel(self, height=40, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_6.setObjectName("sp")
        self.box.lay.addWidget(self.params_6)
        self.nadklad = ParamBox(self, width=328, value_2=" ", title_down="MIN", title_down_2="MAX", title_left="Grubość nadkładu [m]:")
        self.params_6.lay.addWidget(self.nadklad)
        self.params_7 = CanvasHSubPanel(self, height=40, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_7.setObjectName("sp")
        self.box.lay.addWidget(self.params_7)
        self.miazsz = ParamBox(self, width=328, value_2=" ", title_down="MIN", title_down_2="MAX", title_left="Miąższość kopaliny [m]:")
        self.params_7.lay.addWidget(self.miazsz)
        self.params_8 = CanvasHSubPanel(self, height=98, margins=[8, 0, 8, 0], spacing=8, alpha=0.71)
        self.params_8.setObjectName("sp")
        self.box.lay.addWidget(self.params_8)
        self.uwagi = ParamTextBox(self, height=82, title="UWAGI")
        self.params_8.lay.addWidget(self.uwagi)
        self.bottom_margin = CanvasHSubPanel(self, height=4)
        self.bottom_margin.setObjectName("sp")
        self.box.lay.addWidget(self.bottom_margin)
        self.separator_2 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.box.lay.addWidget(self.separator_2)
        self.sp_pow = CanvasHSubPanel(self, height=34)
        self.sp_pow.setObjectName("sp")
        self.box.lay.addWidget(self.sp_pow)
        self.pow_selector = WnPowSelector(self)
        self.sp_pow.lay.addWidget(self.pow_selector)

    def values_update(self, _dict):
        """Aktualizuje wartości parametrów."""
        params = [
            [self.kopalina, "value", _dict[1]],
            [self.data_inw, "value", _dict[15]],
            [self.wyrobisko, "value", _dict[2]],
            [self.zawodn, "value", _dict[3]],
            [self.eksploat, "value", _dict[4]],
            [self.odpady, "value", _dict[5]],
            [self.dlug_max, "value", _dict[11]],
            [self.szer_max, "value", _dict[12]],
            [self.wysokosc, "value", _dict[13]],
            [self.wysokosc, "value_2", _dict[14]],
            [self.nadklad, "value", _dict[6]],
            [self.nadklad, "value_2", _dict[7]],
            [self.miazsz, "value", _dict[9]],
            [self.miazsz, "value_2", _dict[10]],
            [self.uwagi, _dict[16]]
        ]
        for param in params:
            if len(param) == 2:
                param[0].value_change(param[1])
            elif len(param) == 3:
                param[0].value_change(param[1], param[2])

    def pow_update(self, _list):
        """Aktualizuje ilość dostępnych powiatów dla punktu WN_PNE."""
        self.pow_selector.pow_update(_list)

    def exit_clicked(self):
        """Dezaktywuje punkt WN_PNE przy wyłączeniu canvaspanel'u."""
        dlg.obj.wn = None


class CanvasHSubPanel(QFrame):
    """Belka canvaspanel'u z box'em."""
    def __init__(self, *args, height, margins=[0, 0, 0, 0], spacing=0, color="55, 55, 55", disable_color="55, 55, 55", alpha=0.0, disable_void=True):
        super().__init__(*args)
        self.setObjectName("main")
        self.setFixedHeight(height)
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(""" + color + """, """ + str(alpha) + """); border: none}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.lay.setSpacing(spacing)
        self.setLayout(self.lay)
        self.alpha = alpha
        self.color = color
        self.disable_color = disable_color
        self.disable_void = disable_void

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        if self.disable_void:
            return
        self.setEnabled(_bool)
        self.children_enabled(_bool)
        self.set_style()

    def children_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        widgets = (self.lay.itemAt(i).widget() for i in range(self.lay.count()))
        for widget in widgets:
            if not widget:
                continue
            if isinstance(widget, (MoekButton, QProgressBar)):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)

    def set_style(self):
        """Modyfikacja stylesheet."""
        color = self.color if self.isEnabled() else self.disable_color
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(""" + color + """, """ + str(self.alpha) + """); border: none}
                    """)


class OdpadySelector(QFrame):
    """Widget wyboru rodzajów odpadów dla wyrobiska."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(402)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.lay = QGridLayout()
        self.lay.setContentsMargins(0, 6, 0, 6)
        self.lay.setSpacing(6)
        self.setLayout(self.lay)
        self.act_cnt = 0
        self.attr_void = True
        self.o1_val = None
        self.o2_val = None
        self.o3_val = None
        self.o4_val = None
        self.op_bool = None
        self.i_bool = None
        self.attr_void = False
        self.vals = []
        self.itms = {}
        self.btns = [
                {"row": 2, "col": 0, "r_span": 1, "c_span": 1, "item": "btn", "id": "e", "text": "eksploatacyjne"},
                {"row": 2, "col": 1, "r_span": 1, "c_span": 1, "item": "btn", "id": "rb", "text": "remontowo-budowlane"},
                {"row": 3, "col": 0, "r_span": 1, "c_span": 1, "item": "btn", "id": "p", "text": "przeróbcze"},
                {"row": 3, "col": 1, "r_span": 1, "c_span": 1, "item": "btn", "id": "op", "text": "opakowaniowe"},
                {"row": 4, "col": 0, "r_span": 1, "c_span": 1, "item": "btn", "id": "k", "text": "zmieszane komunalne"},
                {"row": 4, "col": 1, "r_span": 1, "c_span": 1, "item": "btn", "id": "czp", "text": "opony, części pojazdów"},
                {"row": 5, "col": 0, "r_span": 1, "c_span": 1, "item": "btn", "id": "wg", "text": "wielkogabarytowe"},
                {"row": 5, "col": 1, "r_span": 1, "c_span": 1, "item": "btn", "id": "r", "text": "zielone, biodegradowalne"},
                {"row": 6, "col": 0, "r_span": 1, "c_span": 1, "item": "btn", "id": "el", "text": "elektroodpady"},
                {"row": 6, "col": 1, "r_span": 1, "c_span": 1, "item": "btn", "id": "i", "text": "inne"}
            ]
        for widget in self.btns:
            if widget["item"] == "btn":
                _btn = OdpadySelectorItem(self, id=widget["id"], txt=widget["text"])
                exec(f'self.lay.addWidget(_btn, widget["row"], widget["col"], widget["r_span"], widget["c_span"])')
                btn_name = f'btn_{widget["id"]}'
                self.itms[btn_name] = _btn

    def set_values(self, val_list):
        """Ustawienie wartości przycisków i textbox'ów według danych z db."""
        temp_list = []
        temp_op = False
        temp_i = False
        self.act_cnt = 0
        self.vals = []
        self.attr_void = True
        for i in range(4):
            if val_list[i]:
                exec(f'self.o{i + 1}_val = val_list[i]')
                temp_list.append(val_list[i])
                self.act_cnt += 1
                if val_list[i] == "op":
                    temp_op = True
                if val_list[i] == "i":
                    temp_i = True
            else:
                exec(f'self.o{i + 1}_val = None')
        self.attr_void = False
        self.vals.extend(temp_list)
        txt = dlg.wyr_panel.param_parser(val_list[4], False)
        dlg.wyr_panel.widgets["tb_odpady_opak_1"].value_change(txt)
        self.op_bool = temp_op
        txt = dlg.wyr_panel.param_parser(val_list[5], False)
        dlg.wyr_panel.widgets["tb_odpady_inne_1"].value_change(txt)
        self.i_bool = temp_i
        for btn_name in self.itms:
            btn = self.itms[btn_name]
            if btn.id in temp_list:
                btn.setChecked(True)
                temp_list.remove(btn.id)
            else:
                btn.setChecked(False)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "op_bool" and not self.attr_void:
            dlg.wyr_panel.widgets["tb_odpady_opak_1"].setVisible(val)
            if not val and dlg.wyr_panel.widgets["tb_odpady_opak_1"].txtbox.cur_val:
                dlg.wyr_panel.widgets["tb_odpady_opak_1"].txtbox.value_change(None)
        if attr == "i_bool" and not self.attr_void:
            dlg.wyr_panel.widgets["tb_odpady_inne_1"].setVisible(val)
            if not val and dlg.wyr_panel.widgets["tb_odpady_inne_1"].txtbox.cur_val:
                dlg.wyr_panel.widgets["tb_odpady_inne_1"].txtbox.value_change(None)
        if attr == "o1_val" and not self.attr_void:
            val_sql = self.sql_parser(val)
            db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="t_odpady_1", val=val_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        if attr == "o2_val" and not self.attr_void:
            val_sql = self.sql_parser(val)
            db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="t_odpady_2", val=val_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        if attr == "o3_val" and not self.attr_void:
            val_sql = self.sql_parser(val)
            db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="t_odpady_3", val=val_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        if attr == "o4_val" and not self.attr_void:
            val_sql = self.sql_parser(val)
            db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="t_odpady_4", val=val_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)

    def sql_parser(self, val):
        """Zwraca wartość prawidłową dla formuły sql."""
        return f"'{val}'" if val else 'Null'

    def btn_clicked(self, _id):
        """Włączenie/wyłączenie powiatu po naciśnięciu przycisku."""
        btn = self.itms[f"btn_{_id}"]
        if self.act_cnt == 4 and btn.isChecked():  # Wszystkie dostępne guziki zajęte, blokada wciśnięcia przycisku
            btn.setChecked(False)
            return
        if btn.isChecked():
            # Włączono przycisk:
            self.act_cnt += 1
            self.vals.append(_id)
        else:
            # Wyłączono przycisk:
            self.act_cnt -= 1
            self.vals.remove(_id)
        if _id == "op":
            self.op_bool = btn.isChecked()
        if _id == "i":
            self.i_bool = btn.isChecked()
        self.odp_update()

    def odp_update(self):
        """Aktualizacja wartości rodzajów odpadów."""
        odp_vals = ["self.o1_val", "self.o2_val", "self.o3_val", "self.o4_val"]
        for i in range(4):
            new_val = self.vals[i] if i < len(self.vals) else None
            cur_val = eval(odp_vals[i])
            if cur_val != new_val:
                exec(f'{odp_vals[i]} = new_val')

    def clear_all(self):
        """Odznaczenie wszystkich przycisków po ustawieniu combobox'a na wartość 'brak' albo 'Null'."""
        for btn_name in self.itms:
            btn = self.itms[btn_name]
            if btn.isChecked():
                btn.setChecked(False)
                self.btn_clicked(btn.id)


class OdpadySelectorItem(QPushButton):
    """Guzik do wyboru rodzaju odpadów dla wyrobiska."""
    def __init__(self, *args, id, txt):
        super().__init__(*args)
        self.setCheckable(True)
        self.setFixedSize(198, 34)
        self.id = id
        self.setText(txt)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
                            QPushButton {
                                border: 2px dashed rgb(60, 60, 60);
                                background: transparent;
                                color: rgba(255, 255, 255, 0.4);
                                font-size: 8pt;
                                font-weight: normal;
                            }
                            QPushButton:hover {
                                border: 2px dashed rgb(60, 60, 60);
                                background: rgba(255, 255, 255, 0.05);
                                color: rgba(255, 255, 255, 0.5);
                                font-size: 8pt;
                                font-weight: normal;
                            }
                            QPushButton:checked {
                                border: 2px solid rgb(150, 150, 150);
                                background: rgba(255, 255, 255, 0.3);
                                color: rgba(255, 255, 255, 1.0);
                                font-size: 8pt;
                                font-weight: bold;
                            }
                            QPushButton:hover:checked {
                                border: 2px solid rgb(180, 180, 180);
                                background: rgba(255, 255, 255, 0.4);
                                color: rgba(255, 255, 255, 1.0);
                                font-size: 8pt;
                                font-weight: bold;
                            }
                            QPushButton:disabled {
                                border: none;
                                background: rgba(255, 255, 255, 0.1);
                                color: rgba(255, 255, 255, 0.2);
                                font-size: 8pt;
                                font-weight: normal;
                            }
                           """)
        self.clicked.connect(lambda: self.parent().btn_clicked(self.id))


class WnPowSelector(QFrame):
    """Belka wyboru aktywnych powiatów dla punktu WN_PNE."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(34)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(8, 2, 8, 2)
        self.lay.setSpacing(8)
        self.setLayout(self.lay)
        self.all_cnt = int()
        self.act_cnt = int()
        self.itms = {}
        for i in range(4):
            _itm = PowSelectorItem(self, _id=i)
            self.lay.addWidget(_itm)
            itm_name = f'pow_btn_{i}'
            self.itms[itm_name] = _itm

    def pow_update(self, _list):
        """Aktualizacja danych dotyczących aktywnych powiatów."""
        self.all_cnt = len(_list)
        self.act_cnt = 0
        for i in range(4):
            _bool = True if i < self.all_cnt else False
            widget = self.itms[f"pow_btn_{i}"]
            if widget:
                # Odsłania tyle guzików, ile jest powiatów:
                widget.setVisible(_bool)
                if _bool:
                    _act = _list[i][2]  # Czy powiat jest aktywny?
                    if _act:
                        # Zliczanie aktywnych powiatów:
                        self.act_cnt += 1
                    # Ustawienie guzików:
                    widget.setText(_list[i][0])
                    widget.setChecked(_act)
        # Wyłącza hovering, jeśli tylko jeden powiat dostępny:
        self.itms[f"pow_btn_0"].setEnabled(False) if self.all_cnt == 1 else self.itms[f"pow_btn_0"].setEnabled(True)

    def btn_clicked(self, _id):
        """Włączenie/wyłączenie powiatu po naciśnięciu przycisku."""
        btn = self.itms[f"pow_btn_{_id}"]
        if btn.isChecked():
            # Włączono powiat:
            self.act_cnt += 1
        else:
            # Wyłączono powiat:
            self.act_cnt -= 1
        # Sprawdzenie, czy wszystkie guziki zostały wyłączone:
        if self.act_cnt == 0:  # Jeden guzik musi być włączony, cofamy zmianę:
            self.act_cnt += 1
            btn.setChecked(True)
        else:
            self.db_update(btn)  # Aktualizacja db
            wn_layer_update()  # Aktualizacja warstwy wn_pne

    def db_update(self, btn):
        """Aktualizacja atrybutu 'b_active' w db."""
        id_arkusz = dlg.obj.wn
        pow_id = btn.text()
        b_active = 'true' if btn.isChecked() else 'false'
        db = PgConn()
        sql = f"UPDATE external.wn_pne_pow SET b_active = {b_active} WHERE id_arkusz = '{id_arkusz}' and pow_id = '{pow_id}';"
        if db:
            res = db.query_upd(sql)
            if not res:
                print(f"Nie udało się zmienić ustawienia powiatu {pow_id} dla punktu WN_PNE: {id_arkusz}")


class PowSelectorItem(QPushButton):
    """Guzik do wyboru aktywnych powiatów dla punktu WN_PNE."""
    def __init__(self, *args, _id):
        super().__init__(*args)
        self.setCheckable(True)
        self.id = _id
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
                            QPushButton {
                                border: 2px solid rgba(217, 0, 143, 0.4);
                                background: rgba(217, 0, 143, 0.2);
                                color: rgba(255, 255, 255, 0.6);
                                font-size: 11pt;
                            }
                            QPushButton:hover {
                                border: 2px solid rgba(217, 0, 143, 0.4);
                                background: rgba(217, 0, 143, 0.4);
                                color: rgba(255, 255, 255, 0.6);
                                font-size: 11pt;
                            }
                            QPushButton:checked {
                                border: 2px solid rgba(217, 0, 143, 1.0);
                                background: rgba(217, 0, 143, 0.7);
                                color: rgb(255, 255, 255);
                                font-size: 11pt;
                            }
                            QPushButton:hover:checked {
                                border: 2px solid rgba(217, 0, 143, 1.0);
                                background: rgba(217, 0, 143, 1.0);
                                color: rgb(255, 255, 255);
                                font-size: 11pt;
                            }
                            QPushButton:disabled {
                                border: 2px solid rgba(217, 0, 143, 1.0);
                                background: rgba(217, 0, 143, 0.7);
                                color: rgb(255, 255, 255);
                                font-size: 11pt;
                            }
                           """)
        self.clicked.connect(lambda: self.parent().btn_clicked(self.id))


class WyrStatusIndicator(QLabel):
    """Wyświetla status aktywnego wyrobiska."""
    def __init__(self, *args, text="NOWE WYROBISKO", color="153, 153, 153"):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.set_case(text, color)

    def set_case(self, text, color):
        """Ustala tekst i kolor kontrolki."""
        self.setStyleSheet("""
                    QLabel {
                        border: none;
                        background: rgba(""" + color + """, 0.8);
                        color: black;
                        font-size: 8pt;
                        font-weight: bold;
                    }
                    """)
        self.setText(text)

    def order_check(self):
        """Ustalenie order_id wyrobisk potwierdzonych we wszystkich powiatach."""
        # self.order_clear_not_green()  # wyczyszczenie order_id w wyrobiskach niepotwierdzonych
        odf = self.order_pd_load()
        odf = odf.sort_values(by=['pow_grp', 'Y_92'], ascending=[True, False])
        # Pogrupowanie wszystkich wyrobisk na powiaty:
        odf_pows = dict(tuple(odf.groupby('pow_grp')))
        odf_pows_list = [odf_pows[x] for x in odf_pows]
        # Działania na poszczególnych powiatach:
        for odf_pow in odf_pows_list:
            odf_pow = odf_pow.reset_index(drop=True)
            if odf_pow[odf_pow['order_lock'] == True].any().all():
                odf_pow = self.complex_numbering(odf_pow)
            else:
                odf_pow = self.simple_numbering(odf_pow)
            # Sprawdzenie, czy jest różnica pomiędzy ustaloną numeracją, a nową:
            not_same = np.any( odf_pow['order_id'].values != odf_pow['order_new'].values)
            if not_same:
                # Konieczność aktualizacji order_id w tym powiecie:
                udf = odf_pow[['wyr_id', 'pow_grp', 'order_new']]
                udf_list = udf.to_records(index=False).tolist()
                self.order_clear()
                self.order_update(udf_list)

    def simple_numbering(self, odf_pow):
        """Proste przenumerowanie wyrobisk w obrębie powiatu, jeśli nie ma zablokowanych numerów order_id."""
        # Podział na pasy o szerokości 3 km:
        odf_pow['row'] = odf_pow['Y_92'].diff(periods=1).abs().cumsum().fillna(0).div(3000).floordiv(1).astype(int)
        # Sortowanie po współrzędnej X wewnątrz pasów:
        odf_pow = odf_pow.sort_values(by=['row', 'X_92'], ascending=[True, True]).reset_index(drop=True)
        # Ponumerowanie wszystkich wyrobisk:
        odf_pow['order_new'] = odf_pow.index + 1
        odf_pow['order_new'] = odf_pow['order_new'].map(lambda x: f'{x:0>3}')
        return odf_pow

    def complex_numbering(self, odf_pow):
        """Zlożone przenumerowanie wyrobisk w obrębie powiatu, jeśli są zablokowane numery order_id"""
        odf_pow['order_new'] = 0
        odf_pow_locked = odf_pow[odf_pow['order_lock'] == True]
        odf_pow_locked['order_new'] = odf_pow_locked['order_id']
        odf_pow_unlocked = odf_pow[odf_pow['order_lock'] == False]
        order_locked_ids = sorted(odf_pow_locked['order_id'].astype(int).tolist())
        # Podział na pasy o szerokości 3 km:
        odf_pow_unlocked['row'] = odf_pow_unlocked['Y_92'].diff(periods=1).abs().cumsum().fillna(0).div(3000).floordiv(1).astype(int)
        # Sortowanie po współrzędnej X wewnątrz pasów:
        odf_pow_unlocked = odf_pow_unlocked.sort_values(by=['row', 'X_92'], ascending=[True, True])
        i = 0
        # Przenumerowanie odblokowanych wyrobisk:
        for index in odf_pow_unlocked.to_records():
            i += 1
            while i in order_locked_ids:
                i += 1
            odf_pow_unlocked.loc[index[0], 'order_new'] = i
        odf_pow_unlocked['order_new'] = odf_pow_unlocked['order_new'].map(lambda x: f'{x:0>3}')
        odf_pow_unlocked.drop(columns=['row'], inplace=True)
        odf_pow.update(odf_pow_unlocked)
        odf_pow.update(odf_pow_locked)
        odf_pow['wyr_id'] = odf_pow['wyr_id'].astype('int')
        return odf_pow

    def order_pd_load(self):
        """Zwraca dataframe z danymi wyrobisk potwierdzonych dla ustalenia order_id."""
        db = PgConn()
        sql = f"SELECT w.wyr_id, ST_X(w.centroid) as X_92, ST_Y(w.centroid) as Y_92, p.pow_grp, p.order_id, p.order_lock FROM team_{dlg.team_i}.wyr_prg AS p INNER JOIN team_{dlg.team_i}.wyrobiska AS w USING(wyr_id) WHERE w.b_confirmed IS TRUE;"
        if db:
            df = db.query_pd(sql, ['wyr_id' ,'X_92', 'Y_92', 'pow_grp', 'order_id', 'order_lock'])
            if isinstance(df, pd.DataFrame):
                return df
            else:
                return pd.DataFrame(columns=['wyr_id' ,'X_92', 'Y_92', 'pow_grp', 'order_id', 'order_lock'])

    def order_update(self, list):
        """Aktualizacja order_id w db."""
        db = PgConn()
        sql = f"UPDATE team_{dlg.team_i}.wyr_prg AS p SET order_id = u.order_id FROM (VALUES %s) AS u (wyr_id, pow_grp, order_id) WHERE p.wyr_id = u.wyr_id AND p.pow_grp = u.pow_grp;"
        if db:
            db.query_exeval(sql, list)

    def order_clear(self):
        """Wyczyszczenie order_id dla wyrobisk z bieżącego powiatu."""
        db = PgConn()
        sql = f"UPDATE team_{dlg.team_i}.wyr_prg SET order_id = Null WHERE pow_grp = '{dlg.powiat_i}' AND order_lock IS FALSE"
        if db:
            res = db.query_upd(sql)

    def order_clear_not_green(self):
        """Wyczyszczenie order_id i order_lock dla wyrobisk innych niż potwierdzone."""
        db = PgConn()
        sql = f"UPDATE team_{dlg.team_i}.wyr_prg AS a SET order_id = Null, order_lock = false FROM team_{dlg.team_i}.wyrobiska AS b WHERE a.wyr_id = b.wyr_id and b.b_confirmed = false"
        if db:
            res = db.query_upd(sql)


class WyrWnPicker(QFrame):
    """Belka przydziału WN_PNE dla wyrobiska."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(102, 32)
        self.setStyleSheet("QFrame#main{background-color: rgba(55, 55, 55, 0.71); border: none}")
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(2, 0, 2, 0)
        self.lay.setSpacing(2)
        self.setLayout(self.lay)
        self.wn_picker_empty = MoekButton(self, name="wyr_wn_empty", size=28, checkable=True, tooltip="wybierz z mapy punkt WN_PNE, który będzie powiązany z wyrobiskiem")
        self.lay.addWidget(self.wn_picker_empty)
        self.wn_picker_empty.clicked.connect(lambda: dlg.mt.init("wn_pick"))
        self.wn_picker_eraser = MoekButton(self, name="wyr_wn", size=28, checkable=False, tooltip="wyczyść powiązanie wyrobiska z punktem WN_PNE")
        self.lay.addWidget(self.wn_picker_eraser)
        self.wn_picker_eraser.clicked.connect(lambda: self.wn_id_update(None))
        self.idbox = CanvasLineEdit(self, width=68, height=28, font_size=10, max_len=8, validator="id_arkusz", theme="dark", fn=["dlg.wyr_panel.wn_picker.wn_id_update(self.text())"], placeholder="0001_001")
        self.lay.addWidget(self.idbox)
        self.lay.setAlignment(self.idbox, Qt.AlignVCenter)
        self.wn_id = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "wn_id":
            self.idbox.set_value(val)
            self.wn_picker_empty.setVisible(False) if val else self.wn_picker_empty.setVisible(True)
            self.wn_picker_eraser.setVisible(True) if val else self.wn_picker_eraser.setVisible(False)

    def wn_id_update(self, id):
        """Sprawdza istnienie wn_id na liście wn_ids i aktualizuje wn_id w db, jeśli potrzeba."""
        if id in dlg.obj.wn_ids or not id:
            self.db_update(id)  # Aktualizacja wn_id w db
        dlg.obj.wyr = dlg.obj.wyr  # Aktualizacja danych w wyr_panel

    def db_update(self, id):
        """Aktualizacja atrybutu 'wn_id' w db."""
        db = PgConn()
        if id:
            sql = f"UPDATE team_{dlg.team_i}.wyrobiska SET wn_id = '{id}' WHERE wyr_id = {dlg.obj.wyr}"
        else:
            sql = f"UPDATE team_{dlg.team_i}.wyrobiska SET wn_id = Null WHERE wyr_id = {dlg.obj.wyr}"
        if db:
            res = db.query_upd(sql)


class WyrStatusSelector(QFrame):
    """Belka zmiany statusu wyrobiska."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(28, 28)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(2)
        self.setLayout(self.lay)
        self.valid_check = False
        self.itms = {}
        self.statuses = [
            {'id' : 2, 'name' : 'wyr_green_status', 'text' : 'WYROBISKO PO AKTUALIZACJI', 'layer': 'wyr_zielone', 'color' : '40, 170, 40', 'new' : False, 'confirmed' : True},
            {'id' : 1, 'name' : 'wyr_purple_status', 'text' : 'AKTUALIZOWANE WYROBISKO', 'layer': 'wyr_fioletowe', 'color' : '180, 40, 180', 'new' : False, 'confirmed' : False},
            {'id' : 0, 'name' : 'wyr_grey_status', 'text' : 'NOWE WYROBISKO', 'layer': 'wyr_szare', 'color' : '153, 153, 153', 'new' : True, 'confirmed' : False}
            ]
        for status in self.statuses:
            _itm = WyrStatusSelectorItem(self, name=status["name"], size=28, checkable=False, id=status["id"])
            self.lay.addWidget(_itm)
            itm_name = f'btn_{status["name"]}'
            self.itms[itm_name] = _itm
        self.case = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "case" and val != None:
            self.case_change()
            dlg.wyr_panel.tab_box.setVisible(True) if val == 1 else dlg.wyr_panel.tab_box.setVisible(False)
            dlg.wyr_panel.order_box.setVisible(True) if val > 0 and not dlg.wyr_panel.pow_all else dlg.wyr_panel.order_box.setVisible(False)
            if val == 1:
                dlg.wyr_panel.order_box.set_theme("purple")
            elif val == 2:
                dlg.wyr_panel.order_box.set_theme("green")
            # Tymczasowe wyłączenie order_drawer z uwagi na metodykę 2024 r.:
            # dlg.wyr_panel.order_drawer.setVisible(True) if val > 0 and not dlg.wyr_panel.pow_all else dlg.wyr_panel.order_drawer.setVisible(False)

    def set_case(self, new, confirmed):
        """Ustala 'case' na podstawie atrybutów wyrobiska."""
        if new:
            self.case = 0
        else:
            self.case = 2 if confirmed else 1

    def db_update(self, new, confirmed):
        """Aktualizacja atrybutów wyrobiska w db po zmianie statusu."""
        db = PgConn()
        sql = f"UPDATE team_{dlg.team_i}.wyrobiska SET b_new = {new}, b_confirmed = {confirmed} WHERE wyr_id = {dlg.obj.wyr}"
        if db:
            res = db.query_upd(sql)
            if res:
                return True
            else:
                return False
        else:
            return False

    def case_change(self):
        """Dostosowanie widoczności przycisków do aktualnego statusu wyrobiska."""
        if self.case == 0:
            for itm in self.itms.values():
                itm.setVisible(False)
        else:
            self.itms["btn_wyr_grey_status"].setVisible(False)
            self.itms["btn_wyr_purple_status"].setVisible(False) if self.case == 1 else self.itms["btn_wyr_purple_status"].setVisible(True)
            self.itms["btn_wyr_green_status"].setVisible(False) if self.case == 2 else self.itms["btn_wyr_green_status"].setVisible(True)
        # for itm in self.itms.values():
        #     itm.setVisible(False) if itm.id == self.case else itm.setVisible(True)
        for status in self.statuses:
            if status["id"] == self.case:
                dlg.wyr_panel.status_indicator.set_case(status["text"], status["color"])
                dlg.wyr_panel.sb.setCurrentIndex(status["id"])

    def btn_clicked(self, id):
        """Zmiana wartości 'case' i aktualizacja db po naciśnięciu przycisku."""
        old_id = self.case
        self.case = id
        for status in self.statuses:
            if status["id"] == self.case:
                result = self.db_update(status["new"], status["confirmed"])
                if result:
                    self.vis_check(status["layer"])
        if self.case == 1 or old_id == 1:
            wyr_layer_update(False)
        dlg.obj.wyr = dlg.obj.wyr

    def vis_check(self, lyr_name):
        """Włącza dany typ wyrobisk, jeśli nie jest włączony."""
        val = dlg.cfg.get_val(lyr_name)
        if val == 0:
            dlg.cfg.set_val(lyr_name, 1)


class WyrStatusSelectorItem(QToolButton):
    """Guzik do wyboru statusu wyrobiska."""
    def __init__(self, *args, id, size=25, hsize=0, name="", icon="", visible=True, enabled=True, checkable=False, tooltip=""):
        super().__init__(*args)
        self.setCheckable(False)
        self.id = id
        name = icon if len(icon) > 0 else name
        self.shown = visible  # Dubluje setVisible() - .isVisible() może zależeć od rodzica
        self.setVisible(visible)
        self.setEnabled(enabled)
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setAutoRaise(True)
        self.setStyleSheet("QToolButton {border: none}")
        self.set_icon(name, size, hsize)
        self.setMouseTracking(True)
        self.clicked.connect(lambda: self.parent().btn_clicked(self.id))

    def set_icon(self, name, size=25, hsize=0):
        """Ładowanie ikon do guzika."""
        if hsize == 0:
            wsize, hsize = size, size
        else:
            wsize = size
        self.setFixedSize(wsize, hsize)
        self.setIconSize(QSize(wsize, hsize))
        icon = QIcon()
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(wsize, hsize), mode=QIcon.Normal, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0_act.png", size=QSize(wsize, hsize), mode=QIcon.Active, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(wsize, hsize), mode=QIcon.Selected, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_dis.png", size=QSize(wsize, hsize), mode=QIcon.Disabled, state=QIcon.Off)
        if self.isCheckable():
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(wsize, hsize), mode=QIcon.Normal, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1_act.png", size=QSize(wsize, hsize), mode=QIcon.Active, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(wsize, hsize), mode=QIcon.Selected, state=QIcon.On)
        self.setIcon(icon)


class OrderDrawer(QFrame):
    """Wysuwane menu z przyciskami do ręcznego ustalania order_id."""

    def __init__(self, *args, height=28):
        super().__init__(*args)
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(1, height)
        self.setObjectName("main")
        self.v_line = QFrame(self)
        self.v_line.setFixedSize(1, height - 6)
        self.v_line.setObjectName("v_line")
        self.btn_edit = MoekButton(self, name="order_edit", size=16, checkable=True, tooltip="włącz tryb edycji ręcznego przypisania numeru dla tego wyrobiska", tooltip_on="wyłącz tryb edycji ręcznego przypisanie numeru dla tego wyrobiska")
        self.btn_edit.clicked.connect(self.order_edit_clicked)
        self.btn_lock = MoekButton(self, name="order_lock", size=16, checkable=True, tooltip="włącz ręczne przypisanie numeru dla tego wyrobiska", tooltip_on="wyłącz ręczne przypisanie numeru dla tego wyrobiska")
        self.btn_lock.clicked.connect(self.order_lock_clicked)
        self.v_line.setGeometry(0, 3, self.v_line.width(), self.v_line.height())
        self.btn_lock.setGeometry(-1, 6, self.btn_lock.width(), self.btn_lock.height())
        self.btn_edit.setGeometry(-17, 6, self.btn_edit.width(), self.btn_edit.height())
        self.set_style()
        self.attr_void = True
        self.slided = False
        self.locked = False
        self.edited = False
        self.attr_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "slided" and not self.attr_void:
            self.sliding()
        elif attr == "locked" and not self.attr_void:
            dlg.wyr_panel.order_box.locked = val
            if self.btn_lock.isChecked() != val:
                self.btn_lock.setChecked(val)
            # self.slided = val
            if not val and self.edited:
                self.edited = False
        elif attr == "edited" and not self.attr_void:
            dlg.wyr_panel.order_box.edited = val
            if self.btn_edit.isChecked() != val:
                self.btn_edit.setChecked(val)

    def set_style(self):
        """Modyfikacja stylesheet."""
        alpha = 0.6 if self.isEnabled() else 0.1
        self.setStyleSheet("""
                    QFrame#main {background-color: transparent; border: none}
                    QFrame#v_line {background-color: rgba(255, 255, 255, """ + str(alpha) + """); border: none}
                    """)

    def sliding(self):
        self.composer(slide=self.slided)

    def enterEvent(self, event):
        if self.isEnabled():
            self.slided = True

    def leaveEvent(self, event):
        # if not self.locked and self.slided:
        if self.slided:
            self.slided = False

    def order_edit_clicked(self):
        """Włączenie/wyłączenie edycji order_id."""
        self.edited = self.btn_edit.isChecked()
        if self.edited and not self.locked:
            self.locked = True

    def order_lock_clicked(self):
        """Zablokowanie/odblokowanie order_id."""
        self.locked = self.btn_lock.isChecked()
        if self.locked and not self.edited:
            self.edited = True
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_prg', attr='order_lock', val=self.locked, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        self.slided = False
        if not self.locked:
            self.attr_void = True
            wyr_layer_update(False)
            dlg.obj.wyr = dlg.obj.wyr
            self.attr_void = False

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        self.set_style()

    def composer(self, slide=False):
        """Ustalenie rozmieszczenia i widoczności widget'ów."""
        if slide:
            self.setFixedWidth(34)
            self.v_line.setGeometry(33, 3, self.v_line.width(), self.v_line.height())
            self.btn_lock.setGeometry(17, 6, self.btn_lock.width(), self.btn_lock.height())
            self.btn_edit.setGeometry(1, 6, self.btn_edit.width(), self.btn_edit.height())
        else:
            self.setFixedWidth(1)
            self.v_line.setGeometry(0, 3, self.v_line.width(), self.v_line.height())
            self.btn_lock.setGeometry(-1, 6, self.btn_lock.width(), self.btn_lock.height())
            self.btn_edit.setGeometry(-17, 6, self.btn_edit.width(), self.btn_edit.height())


class KopalinaWiekBox(QFrame):
    """Widget ustalania dla wyrobiska kopalin i ich wieku."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(268, 62)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.df_kopalina = self.sl_pd_load("sl_kopalina")
        self.df_wiek = self.sl_pd_load("sl_wiek")
        self.dicts = [
                    {"name": "self.kopalina_1", "width": 180, "attr": "kopalina", "title_down": None, "val_display": False},
                    {"name": "self.kopalina_2", "width": 180, "attr": "kopalina_2", "title_down": None, "val_display": False},
                    {"name": "self.wiek_1", "width": 66, "attr": "wiek", "title_down": None, "val_display": True},
                    {"name": "self.wiek_2", "width": 66, "attr": "wiek_2", "title_down": None, "val_display": True},
                    {"name": "self.kopalina_title", "width": 180, "attr": None, "title_down": "KOPALINA", "val_display": None},
                    {"name": "self.wiek_title", "width": 66, "attr": None, "title_down": "WIEK", "val_display": None},
                    ]
        for dict in self.dicts:
            if dict["attr"]:
                fn = ['dlg.wyr_panel.widgets["kw_1"].val_changed()']
                height = 22
                value = " "
            else:
                fn = None
                height = 1
                value = None
            _cmb = ParamBox(self, item="combo_tv", height=height, width=dict["width"], value=value, val_width=dict["width"], title_down=dict["title_down"], val_display=dict["val_display"], fn=fn)
            exec(f'{dict["name"]} = _cmb')
        self.drawer = KopalinaWiekDrawer(self)
        self.second = False
        self.val_void = True
        self.k1_val = None
        self.k2_val = None
        self.w1_val = None
        self.w2_val = None
        self.val_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "k1_val" and not self.val_void:
            self.kopalina_1.valbox_1.set_value(val)
        if attr == "k2_val" and not self.val_void:
            self.kopalina_2.valbox_1.set_value(val)
        if attr == "w1_val" and not self.val_void:
            self.wiek_1.valbox_1.set_value(val)
        if attr == "w2_val" and not self.val_void:
            self.wiek_2.valbox_1.set_value(val)

    def val_changed(self):
        """Zmieniono wartość jednego z combobox'ów."""
        cmb_vals = [
            ["self.k1_val", self.k1_val, self.kopalina_1.valbox_1.cur_val, "t_kopalina"],
            ["self.k2_val", self.k2_val, self.kopalina_2.valbox_1.cur_val, "t_kopalina_2"],
            ["self.w1_val", self.w1_val, self.wiek_1.valbox_1.cur_val, "t_wiek"],
            ["self.w2_val", self.w2_val, self.wiek_2.valbox_1.cur_val, "t_wiek_2"]
        ]
        for cmb_val in cmb_vals:
            new_val = None if cmb_val[2] == 'Null' else cmb_val[2][1:-1]
            if cmb_val[1] != new_val:
                exec(f'{cmb_val[0]} = new_val')
                val_sql = self.sql_parser(new_val)
                db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr=cmb_val[3], val=val_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
                self.composer()
                return

    def sql_parser(self, val):
        """Zwraca wartość prawidłową dla formuły sql."""
        return f"'{val}'" if val else 'Null'

    def set_values(self, val_list):
        """Ustawienie wartości combobox'ów i słowników przy wczytywaniu danych wyrobiska."""
        # Aktualizacja wartości słownikowych combobox'ów:
        sl_list = ["kopalina", "wiek"]
        for sl in sl_list:
            self.sl_update(sl)
        # Ustalenie aktualnych wartości combobox'ów:
        obj_list = ["self.k1_val", "self.k2_val", "self.w1_val", "self.w2_val"]
        for i in range(4):
            obj = obj_list[i]
            val = val_list[i]
            exec(f'{obj} = val')
        # Odkrycie dodatkowych pól, jeśli ich wartości nie są puste:
        self.second = True if self.k2_val or self.w2_val else False
        # Ustalenie kompozycji widget'ów w zależności od wartości combobox'ów:
        self.composer()

    def sl_update(self, attr_name):
        """Aktualizacja wartości słownikowych combobox'a."""
        for dict in self.dicts:
            if dict["attr"] == attr_name:
                tbl_name = f'sl_{dict["attr"]}'
                self.sl_load_ranked(tbl_name, attr_name)

    def sl_pd_load(self, tbl_name):
        """Zwraca wartości słownikowe do dataframe'u."""
        db = PgConn()
        sql = f"SELECT t_val, t_desc FROM public.{tbl_name};"
        if db:
            df = db.query_pd(sql, ['t_val' ,'t_desc'])
            if isinstance(df, pd.DataFrame):
                return df
            else:
                return pd.Dataframe(columns=['t_val' ,'t_desc'])

    def sl_load_ranked(self, tbl_name, attr_name):
        """Załadowanie wartości słownikowych z db do combobox'a."""
        c1_df, c2_df = self.get_pd_ranked(tbl_name, attr_name)
        self.cmb_populate(attr_name, c1_df, c2_df)

    def cmb_populate(self, attr_name, c1_df, c2_df):
        """Załadowanie wartości słownikowych do odpowiednich combobox'ów."""
        if attr_name == "kopalina":
            cmbs = [self.kopalina_1.valbox_1, self.kopalina_2.valbox_1]
        else:
            cmbs = [self.wiek_1.valbox_1, self.wiek_2.valbox_1]
        for cmb in cmbs:
            cmb.signal_off()
            cmb.clear()
            cmb.addItem(f"", None)
            if len(c1_df) > 0:
                c1_list = c1_df[['t_val', 't_desc']].to_records(index=False).tolist()
                for item in c1_list:
                    cmb.addItem(f"  {item[1]}  ", item[0])
            cmb.insertSeparator(cmb.count())
            if len(c2_df) > 0:
                c2_list = c2_df[['t_val', 't_desc']].to_records(index=False).tolist()
                for item in c2_list:
                    cmb.addItem(f"  {item[1]}  ", item[0])

    def get_pd_ranked(self, tbl_name, attr_name):
        """Załadowanie wartości słownikowych z db do dataframe'ów."""
        a1_df = self.get_attr_vals(tbl_name, f"t_{attr_name}")
        a2_df = self.get_attr_vals(tbl_name, f"t_{attr_name}_2")
        a12_df = pd.concat([a1_df,a2_df]).reset_index(drop=True)
        a12_df = a12_df['t_val'].value_counts().rename_axis('t_val').reset_index(name='cnt')
        a12_df.set_index('t_val', inplace=True)
        b_df = self.df_kopalina.copy() if attr_name == "kopalina" else self.df_wiek.copy()
        b_df.set_index('t_val', inplace=True)
        c_df = b_df.join(a12_df, how='left').reset_index()
        c_df['cnt'] = c_df['cnt'].fillna(0.0)
        c_df['temp'] = c_df['t_desc'].str.replace('ł', 'l').str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
        c_df = c_df.rename_axis('t_val').sort_values(by=['cnt', 'temp'], ascending=[False, True]).reset_index(drop=True)
        c_df = c_df.drop(['temp'], axis=1)
        c1_df = c_df[c_df['cnt'] > 0]
        c2_df = c_df[c_df['cnt'] == 0]
        return c1_df, c2_df

    def get_attr_vals(self, tbl_name, attr_name):
        """Zwraca wartości atrybutu z db."""
        db = PgConn()
        sql = f"SELECT {attr_name} FROM team_{dlg.team_i}.wyr_dane;"
        if db:
            temp_df = db.query_pd(sql, ['t_val'])
            if isinstance(temp_df, pd.DataFrame):
                return temp_df

    def plus_clicked(self):
        """Akcja po naciśnięciu przycisku 'plus_btn'."""
        self.second = True
        self.composer()

    def minus_clicked(self):
        """Akcja po naciśnięciu przycisku 'minus_btn'."""
        self.second = False
        self.k2_val = None
        self.w2_val = None
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr='t_kopalina_2', val='Null', sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr='t_wiek_2', val='Null', sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        self.composer()

    def composer(self):
        """Ustalenie rozmieszczenia i widoczności widget'ów."""
        _second = True if self.k2_val or self.w2_val or self.second else False
        _slide = True if self.drawer.slided else False
        _k1 = True if self.k1_val else False
        if not _slide:
            slide = False
        else:
            if _second:
                slide = True
            else:
                slide = True if _k1 else False
        w = 66 if slide else 85
        d = 241 if slide else 260
        self.drawer.setGeometry(d, 24, self.drawer.width(), self.drawer.height())
        self.kopalina_2.setGeometry(0, 24, self.kopalina_2.width(), self.kopalina_2.height())
        self.wiek_2.setGeometry(181, 24, self.wiek_2.width(), self.wiek_2.height())
        self.kopalina_title.setGeometry(0, 47, self.kopalina_title.width(), self.kopalina_title.height())
        self.wiek_title.setGeometry(181, 47, self.wiek_title.width(), self.wiek_title.height())
        if _second:
            # Druga kopalina (lub wiek) jest ustalona albo przycisk plusa został naciśnięty
            self.wiek_1.setFixedWidth(85)
            self.wiek_title.setFixedWidth(85)
            self.wiek_2.setFixedWidth(w)
            self.wiek_title.setFixedWidth(w)
            self.kopalina_1.setGeometry(0, 0, self.kopalina_1.width(), self.kopalina_1.height())
            self.wiek_1.setGeometry(181, 0, self.wiek_1.width(), self.wiek_1.height())
            self.kopalina_2.setVisible(True)
            self.wiek_2.setVisible(True)
            self.drawer.plus_btn.setVisible(False)
            self.drawer.minus_btn.setVisible(True)
        else:
            self.wiek_1.setFixedWidth(w)
            self.wiek_title.setFixedWidth(w)
            self.kopalina_1.setGeometry(0, 24, self.kopalina_1.width(), self.kopalina_1.height())
            self.wiek_1.setGeometry(181, 24, self.wiek_1.width(), self.wiek_1.height())
            self.kopalina_2.setVisible(False)
            self.wiek_2.setVisible(False)
            self.drawer.plus_btn.setVisible(True) if self.k1_val else self.drawer.plus_btn.setVisible(False)
            self.drawer.minus_btn.setVisible(False)


class KopalinaWiekDrawer(QFrame):
    """Wysuwane menu dla KopalinaWiekBox'u."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(26, 23)
        self.setObjectName("main")
        self.plus_btn = MoekButton(self, name="kw_plus", size=17, tooltip="dodaj drugą kopalinę")
        self.plus_btn.clicked.connect(self.parent().plus_clicked)
        self.minus_btn = MoekButton(self, name="kw_minus", size=17, tooltip="usuń drugą kopalinę")
        self.minus_btn.clicked.connect(self.parent().minus_clicked)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(6, 0, 0, 0)
        hlay.setSpacing(0)
        hlay.addWidget(self.plus_btn)
        hlay.setAlignment(self.plus_btn, Qt.AlignVCenter)
        hlay.addWidget(self.minus_btn)
        hlay.setAlignment(self.minus_btn, Qt.AlignVCenter)
        self.setLayout(hlay)
        self.slide_void = True
        self.slided = False
        self.slide_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "slided" and not self.slide_void:
            self.sliding()

    def set_style(self):
        """Modyfikacja stylesheet."""
        alpha = 0.6 if self.isEnabled() else 0.1
        self.setStyleSheet("""
                    QFrame#main {background-color: transparent; border: none}
                    QFrame#line {background-color: rgba(255, 255, 255, """ + str(alpha) + """); border: none}
                    """)

    def sliding(self):
        self.parent().composer()

    def enterEvent(self, event):
        if self.isEnabled():
            self.slided = True

    def leaveEvent(self, event):
        self.slided = False

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        self.set_style()


class AutorBox(QFrame):
    """Widget do wpisywania autorstwa karty wyrobiska."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(404, 38)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        fn = [['dlg.wyr_panel.widgets["ab_1"].value_changed()']]
        self.txtbox = ParamBox(self, margins=True, height=24, item="line_edit_left", width=402, value=" ", val_width=402, title_down="KARTA WYROBISKA OPRACOWANA PRZEZ", max_len=255, fn=fn)
        self.drawer = CopyPasteDrawer(self, height=24)
        self.drawer.set_enabled(True)
        self.composer()
        self.val_void = True
        self.txt_val = None
        self.val_void = False
        self.txt_copy = self.txt_load()

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "txt_val" and not self.val_void:
            self.drawer.val_copy.setToolTip(f"kopiuj: {val}") if val else self.drawer.val_copy.setToolTip(f"brak tekstu do skopiowania")
            self.drawer.val_copy.setEnabled(True) if val else self.drawer.val_copy.setEnabled(False)
        if attr == "txt_copy":
            self.drawer.val_paste.setToolTip(f"wklej: {val}") if val else self.drawer.val_paste.setToolTip(f"brak tekstu do wklejenia")
            self.drawer.val_paste.setEnabled(True) if val else self.drawer.val_paste.setEnabled(False)

    def txt_load(self):
        """Załadowanie wartości 'autor_copy' z db."""
        db = PgConn()
        sql = f"SELECT autor_copy FROM public.team_users WHERE team_id = {dlg.team_i} and user_id = {dlg.user_id};"
        if db:
            res = db.query_sel(sql, False)
            if res:
                return res[0]

    def value_change(self, val):
        """Zmienia wyświetlany tekst."""
        self.txtbox.valbox_1.cur_val = val
        self.txt_val = val

    def value_changed(self):
        """Zatwierdzono zmianę wartości tekstowej parambox'u."""
        self.txt_val = self.txtbox.valbox_1.cur_val
        txt_sql = self.sql_parser(self.txt_val)
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="t_autor", val=txt_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)

    def sql_parser(self, val):
        """Zwraca wartość prawidłową dla formuły sql."""
        return f"'{val}'" if val else 'Null'

    def val_copy(self):
        """Aktualizacja wartości 'autor_copy' zapisanej w db."""
        self.txt_copy = self.txt_val
        db_attr_change(tbl=f'public.team_users', attr='autor_copy', val=f"'{self.txt_copy}'", sql_bns=f' WHERE team_id = {dlg.team_i} AND user_id = {dlg.user_id}', user=False)

    def val_paste(self):
        """Wklejenie wartości 'val_copy' i zapisanie zmian w db."""
        self.txt_val = self.txt_copy
        self.txtbox.valbox_1.cur_val = self.txt_val
        txt_sql = self.sql_parser(self.txt_val)
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="t_autor", val=txt_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)

    def composer(self, slide=False):
        """Ustalenie rozmieszczenia i widoczności widget'ów."""
        t_width = 368 if slide else 402
        d_x = 363 if slide else 397
        self.txtbox.setFixedWidth(t_width)
        self.drawer.setGeometry(d_x, 4, self.drawer.width(), self.drawer.height())


class PneBox(QFrame):
    """Widget ustalania dla wyrobiska atrybutu 'b_pne' ('CZY_PNE')."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(34, 44)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.pne_btn = MoekButton(self, name="pne", size=34, hsize=26, checkable=False, tooltip="CZY_PNE = TAK")
        self.zl_btn = MoekButton(self, name="zl_nrekul", size=187, hsize=26, checkable=False, tooltip="CZY_PNE = NIE")
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(0)
        hlay.addWidget(self.pne_btn)
        hlay.addWidget(self.zl_btn)
        self.setLayout(hlay)
        self.pne_btn.clicked.connect(self.btn_clicked)
        self.zl_btn.clicked.connect(self.btn_clicked)
        self.val_void = True
        self.btn_val = False
        self.cur_val = None
        self.val_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "btn_val" and not self.val_void:
            if val != self.cur_val:
                self.cur_val = val
                if val:  # Wyrobisko jest związane z PNE
                    self.pne_btn.setVisible(True)
                    self.zl_btn.setVisible(False)
                    self.setFixedWidth(34)
                    dlg.wyr_panel.subpages["subpage_0"].glay.glay.addWidget(dlg.wyr_panel.widgets["pn_1"], 1, 0, 1, 1)
                    dlg.wyr_panel.subpages["subpage_0"].glay.glay.addWidget(dlg.wyr_panel.widgets["txt2_okres_eksp_1"], 1, 1, 1, 11)
                    dlg.wyr_panel.widgets["txt2_okres_eksp_1"].setVisible(True)
                else:  # Wyrobisko jest związane ze złożem niezrekultywowanym
                    self.pne_btn.setVisible(False)
                    self.zl_btn.setVisible(True)
                    self.setFixedWidth(402)
                    dlg.wyr_panel.subpages["subpage_0"].glay.glay.removeWidget(dlg.wyr_panel.widgets["txt2_okres_eksp_1"])
                    dlg.wyr_panel.widgets["txt2_okres_eksp_1"].setVisible(False)
                    dlg.wyr_panel.subpages["subpage_0"].glay.glay.addWidget(dlg.wyr_panel.widgets["pn_1"], 1, 0, 1, 12)

    def btn_clicked(self):
        """Aktualizacja wartości 'b_pne' w tabeli 'wyr_dane'."""
        if not dlg.wyr_panel.has_midas:
            self.btn_val = True  # Jeżeli wyrobisko nie jest powiązane ze złożem, musi być PNE
            QMessageBox.warning(None, "MOEK_Editor", f"Jeżeli wyrobisko nie jest powiązane ze złożem, musi być PNE. Wypełnij ID złoża w zakładce MIDAS, jeżeli chcesz ustawić atrybut CZY_PNE na wartość NIE (co będzie oznaczało, że wyrobisko dotyczy złoża niezrekultywowanego).")
            return
        self.btn_val = not self.btn_val
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="b_pne", val=self.btn_val, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        dlg.wyr_panel.trigger_midas()
        # Wyczyszczenie PNE_OD i PNE_DO, jeśli są wypełnione oraz CZY_PNE = NIE:
        if not self.btn_val and dlg.wyr_panel.widgets["txt2_okres_eksp_1"].valbox_1.cur_val:
            dlg.wyr_panel.widgets["txt2_okres_eksp_1"].valbox_1.value_change(None)
        if not self.btn_val and dlg.wyr_panel.widgets["txt2_okres_eksp_1"].valbox_2.cur_val:
            dlg.wyr_panel.widgets["txt2_okres_eksp_1"].valbox_2.value_change(None)
        # Ustawienie stanu wyrobiska na "zaniechany", jeśli wyrobisko dotyczy złoża niezrekultywowanego:
        if self.btn_val and dlg.wyr_panel.widgets["cmb_stan_1"].valbox_1.cur_val != "Z":
            dlg.wyr_panel.widgets["cmb_stan_1"].valbox_1.set_value("Z", signal=True)


class TerminBox(QFrame):
    """Widget ustalania dla wyrobiska godziny i daty kontroli terenowej, albo oznaczenia braku kontroli terenowej."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(130, 62)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.clock = MoekButton(self, name="clock", size=27, tooltip="godzina rozpoczęcia kontroli terenowej")
        self.calendar = MoekButton(self, name="calendar", size=27, tooltip="data przeprowadzenia kontroli terenowej")
        self.fchk = MoekButton(self, name="fchk", size=34, hsize=26, checkable=True, tooltip="nie przeprowadzono kontroli terenowej", tooltip_on="przeprowadzono kontrolę terenową")
        self.fchk.clicked.connect(self.fchk_clicked)
        self.dicts = [
                    {"name": "self.th", "width": 28, "title_down": "GG", "max_len": 2, "validator": "hours", "zero_allowed": True},
                    {"name": "self.tm", "width": 28, "title_down": "MM", "max_len": 2, "validator": "minutes", "zero_allowed": True},
                    {"name": "self.dd", "width": 28, "title_down": "DD", "max_len": 2, "validator": "days", "zero_allowed": False},
                    {"name": "self.dm", "width": 28, "title_down": "MM", "max_len": 2, "validator": "months", "zero_allowed": False},
                    {"name": "self.dy", "width": 36, "title_down": "RRRR", "max_len": 4, "validator": "years", "zero_allowed": False}
                    ]
        for dict in self.dicts:
            fn = [['dlg.wyr_panel.widgets["gd_1"].val_changed()']]
            _txt2 = ParamBox(self, item="line_edit", max_len=dict["max_len"], validator=dict["validator"], height=18, down_height=10, width=dict["width"], value=" ", val_width=dict["width"], title_down=dict["title_down"], zero_allowed=dict["zero_allowed"], fn=fn)
            exec(f'{dict["name"]} = _txt2')
        self.drawer = CopyPasteDrawer(self)
        self.composer()
        self.val_void = True
        self.t_val = None
        self.d_val = None
        self.th_val = None
        self.tm_val = None
        self.dd_val = None
        self.dm_val = None
        self.dy_val = None
        self.fchk_val = False
        self.val_void = False
        self.d_copy = self.date_load()

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "th_val" and not self.val_void:
            self.th.valbox_1.set_value(val)
        if attr == "tm_val" and not self.val_void:
            self.tm.valbox_1.set_value(val)
        if attr == "dd_val" and not self.val_void:
            self.dd.valbox_1.set_value(val)
        if attr == "dm_val" and not self.val_void:
            self.dm.valbox_1.set_value(val)
        if attr == "dy_val" and not self.val_void:
            self.dy.valbox_1.set_value(val)
        if attr == "fchk_val" and not self.val_void:
            if self.fchk.isChecked != val:
                self.fchk.setChecked(val)
            self.enable_fn(val)
            # if not val and self.t_val:
            #     self.time_reset()
            # if not val and self.d_val:
            #     self.date_reset()
        if attr == "d_val" and not self.val_void:
            self.drawer.val_copy.setToolTip(f"kopiuj datę: {val}") if val else self.drawer.val_copy.setToolTip(f"brak daty do skopiowania")
            self.drawer.val_copy.setEnabled(True) if val else self.drawer.val_copy.setEnabled(False)
        if attr == "d_copy":
            self.drawer.val_paste.setToolTip(f"wklej datę: {val}") if val else self.drawer.val_paste.setToolTip(f"brak daty do wklejenia")
            self.drawer.val_paste.setEnabled(True) if val else self.drawer.val_paste.setEnabled(False)

    def date_load(self):
        """Załadowanie wartości daty z db."""
        db = PgConn()
        sql = f"SELECT date_copy FROM public.team_users WHERE team_id = {dlg.team_i} and user_id = {dlg.user_id};"
        if db:
            res = db.query_sel(sql, False)
            if res:
                return res[0]

    def enable_fn(self, _bool):
        """Włączenie/wyłączenie poszczególnych elementów box'u i innych parambox'ów, w zależności czy przeprowadzono kontrolę terenową."""
        # inner_widgets = [self.clock, self.calendar, self.th, self.tm, self.dd, self.dm, self.dy, self.drawer]
        outer_widgets = [dlg.wyr_panel.widgets["txt2_wys_1"], dlg.wyr_panel.widgets["txt2_nadkl_1"], dlg.wyr_panel.widgets["txt2_miaz_1"]]
        # for widget in inner_widgets:
        #     if isinstance(widget, MoekButton):
        #         widget.setEnabled(_bool)
        #     else:
        #         widget.set_enabled(_bool)
        for widget in outer_widgets:
            widget.set_enabled(_bool)
            if not _bool and widget.valbox_1.cur_val:
                widget.valbox_1.set_value(None)
            if not _bool and widget.valbox_2.cur_val:
                widget.valbox_2.set_value(None)

    def val_changed(self):
        """Zmieniono wartość jednej z części godziny lub daty."""
        part_vals = [
            ["self.th_val", self.th.valbox_1.text(), "time"],
            ["self.tm_val", self.tm.valbox_1.text(), "time"],
            ["self.dd_val", self.dd.valbox_1.text(), "date"],
            ["self.dm_val", self.dm.valbox_1.text(), "date"],
            ["self.dy_val", self.dy.valbox_1.text(), "date"]
        ]
        for part_val in part_vals:
            if len(part_val[1]) == 0:
                # Konwersja pustej wartości:
                new_val = None
            else:
                new_val = part_val[1]
            cur_val = eval(part_val[0])
            if cur_val != new_val:
                # Aktualizacja zmienionej wartości:
                exec(f'{part_val[0]} = new_val')
                if part_val[2] == "time":
                    # Zmieniono część czasu:
                    if (part_val[0] == "self.th_val" and not self.th_val) or (part_val[0] == "self.tm_val" and not self.tm_val):
                        # Reset czasu po zmianie wartości na "pustą":
                        self.time_reset()
                        return
                    if self.th_val and self.tm_val:
                        # Wszystkie części są uzupełnione - ustalenie czasu:
                        try:
                            self.t_val = datetime.time(int(self.th_val), int(self.tm_val))
                        except ValueError:
                            return
                    t_sql = self.sql_parser(self.t_val)
                    db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="time_fchk", val=t_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
                    self.focus_switcher(part_val[0], part_val[2])
                    return
                else:
                    # Zmieniono część daty:
                    if self.dd_val and self.dm_val and (not self.dy_val and part_val[0] != "self.dy_val"):
                        # Autouzupełnienie roku:
                        self.dy_val = f"20{dlg.team_t[-2:]}"
                    if (part_val[0] == "self.dd_val" and not self.dd_val) or (part_val[0] == "self.dm_val" and not self.dm_val) or (part_val[0] == "self.dy_val" and not self.dy_val):
                        # Reset daty po zmianie wartości na "pustą":
                        self.date_reset()
                        return
                    if self.dy_val and self.dm_val and self.dd_val:
                        # Wszystkie części są uzupełnione - ustalenie daty:
                        try:
                            self.d_val = datetime.date(int(self.dy_val), int(self.dm_val), int(self.dd_val))
                        except ValueError:
                            return
                    d_sql = self.sql_parser(self.d_val)
                    db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="date_ctrl", val=d_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
                    self.focus_switcher(part_val[0], part_val[2])
                    return

    def sql_parser(self, val):
        """Zwraca wartość prawidłową dla formuły sql."""
        return f"'{val}'" if val else 'Null'

    def focus_switcher(self, obj_txt, cat):
        """Przejście do kolejnego pustego parambox'a."""
        if cat == "time":
            val_list = ["self.th_val", "self.tm_val"]
            obj_list = ["self.th.valbox_1", "self.tm.valbox_1"]
            txt_list = [self.th.valbox_1.text(), self.tm.valbox_1.text()]
        elif cat == "date":
            val_list = ["self.dd_val", "self.dm_val", "self.dy_val"]
            obj_list = ["self.dd.valbox_1", "self.dm.valbox_1", "self.dy.valbox_1"]
            txt_list = [self.dd.valbox_1.text(), self.dm.valbox_1.text(), self.dy.valbox_1.text()]
        idx = -1
        i = -1
        for val in val_list:
            i += 1
            if val == obj_txt:
                idx = i
                break
        if idx == -1:
            return
        if idx == 0:
            if len(txt_list[1]) == 0:
                exec(f"{obj_list[1]}.setFocus()")
        elif idx == 1:
            if len(txt_list[0]) == 0:
                exec(f"{obj_list[0]}.setFocus()")

    def time_reset(self):
        """Kasowanie wartości czasu."""
        self.t_val = None
        self.th_val = None
        self.tm_val = None
        t_sql = self.sql_parser(self.t_val)
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="time_fchk", val=t_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)

    def date_reset(self):
        """Kasowanie wartości daty."""
        self.d_val = None
        self.dd_val = None
        self.dm_val = None
        self.dy_val = None
        d_sql = self.sql_parser(self.d_val)
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="date_ctrl", val=d_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)

    def set_values(self, val_list):
        """Ustawienie wartości parambox'ów według danych z db."""
        # Ustalenie aktualnych wartości godziny i daty:
        if val_list[0]:
            self.t_val = val_list[0]
            self.th_val = str(self.t_val.hour).zfill(2)
            self.tm_val = str(self.t_val.minute).zfill(2)
        else:
            self.t_val = None
            self.th_val = None
            self.tm_val = None
        if val_list[1]:
            self.d_val = val_list[1]
            self.dd_val = str(self.d_val.day).zfill(2)
            self.dm_val = str(self.d_val.month).zfill(2)
            self.dy_val = str(self.d_val.year)
        else:
            self.d_val = None
            self.dd_val = None
            self.dm_val = None
            self.dy_val = None
        self.fchk_val = True if val_list[2] else False

    def fchk_clicked(self):
        """Aktualizacja wartości 'b_teren' w tabeli 'wyr_dane'."""
        self.fchk_val = self.fchk.isChecked()
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="b_teren", val=self.fchk_val, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)

    def val_copy(self):
        """Aktualizacja wartości 'val_copy' zapisanej w db."""
        self.d_copy = self.d_val
        db_attr_change(tbl=f'public.team_users', attr='date_copy', val=f"'{self.d_copy}'", sql_bns=f' WHERE team_id = {dlg.team_i} AND user_id = {dlg.user_id}', user=False)

    def val_paste(self):
        """Wklejenie wartości 'val_copy' i zapisanie zmian w db."""
        self.d_val = self.d_copy
        self.dd_val = str(self.d_val.day).zfill(2)
        self.dm_val = str(self.d_val.month).zfill(2)
        self.dy_val = str(self.d_val.year)
        d_sql = self.sql_parser(self.d_val)
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr="date_ctrl", val=d_sql, sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)

    def composer(self, slide=False):
        """Ustalenie rozmieszczenia i widoczności widget'ów."""
        if slide:
            self.clock.setGeometry(3, 0, self.clock.width(), self.clock.height())
            self.calendar.setVisible(False)
            self.th.setGeometry(34, 0, self.th.width(), self.th.height())
            self.tm.setGeometry(63, 0, self.tm.width(), self.tm.height())
            self.dd.setGeometry(0, 29, self.dd.width(), self.dd.height())
            self.dm.setGeometry(29, 29, self.dm.width(), self.dm.height())
            self.dy.setGeometry(58, 29, self.dy.width(), self.dy.height())
            self.fchk.setGeometry(94, 0, self.fchk.width(), self.fchk.height())
            self.drawer.setGeometry(89, 29, self.drawer.width(), self.drawer.height())
        else:
            self.clock.setGeometry(3, 0, self.clock.width(), self.clock.height())
            self.calendar.setVisible(True)
            self.calendar.setGeometry(3, 29, self.calendar.width(), self.calendar.height())
            self.th.setGeometry(34, 0, self.th.width(), self.th.height())
            self.tm.setGeometry(63, 0, self.tm.width(), self.tm.height())
            self.dd.setGeometry(34, 29, self.dd.width(), self.dd.height())
            self.dm.setGeometry(63, 29, self.dm.width(), self.dm.height())
            self.dy.setGeometry(92, 29, self.dy.width(), self.dy.height())
            self.fchk.setGeometry(94, 0, self.fchk.width(), self.fchk.height())
            self.drawer.setGeometry(123, 29, self.drawer.width(), self.drawer.height())


class CopyPasteDrawer(QFrame):
    """Wysuwane menu z przyciskami do kopiowania i wklejania wartości."""
    def __init__(self, *args, height=18):
        super().__init__(*args)
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(42, height)
        self.setObjectName("main")
        self.v_line = QFrame(self)
        self.v_line.setFixedSize(1, height - 6)
        self.v_line.setObjectName("v_line")
        self.val_copy = MoekButton(self, name="val_copy", size=16, checkable=False, tooltip="")
        self.val_copy.clicked.connect(self.val_copy_clicked)
        self.val_paste = MoekButton(self, name="val_paste", size=16, checkable=False, tooltip="")
        self.val_paste.clicked.connect(self.val_paste_clicked)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(6, 0, 0, 0)
        hlay.setSpacing(2)
        hlay.addWidget(self.v_line)
        hlay.setAlignment(self.v_line, Qt.AlignVCenter)
        hlay.addWidget(self.val_copy)
        hlay.setAlignment(self.val_copy, Qt.AlignVCenter)
        hlay.addWidget(self.val_paste)
        hlay.setAlignment(self.val_paste, Qt.AlignVCenter)
        self.setLayout(hlay)
        self.slide_void = True
        self.slided = False
        self.slide_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "slided" and not self.slide_void:
            self.sliding()

    def set_style(self):
        """Modyfikacja stylesheet."""
        alpha = 0.6 if self.isEnabled() else 0.1
        self.setStyleSheet("""
                    QFrame#main {background-color: transparent; border: none}
                    QFrame#v_line {background-color: rgba(255, 255, 255, """ + str(alpha) + """); border: none}
                    """)

    def sliding(self):
        self.parent().composer(slide=self.slided)

    def enterEvent(self, event):
        if self.isEnabled():
            self.slided = True

    def leaveEvent(self, event):
        self.slided = False

    def val_copy_clicked(self):
        """Skopiowanie wartości daty do db."""
        self.parent().val_copy()

    def val_paste_clicked(self):
        """Wklejenie wartości skopiowanej daty."""
        self.parent().val_paste()

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        self.set_style()


class FlagTools(QFrame):
    """Menu przyborne dla flag."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(96, 32)
        self.setObjectName("main")
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.flag_move = MoekButton(self, name="move", size=32, checkable=True, tooltip="zmień lokalizację flagi")
        self.flag_chg = MoekButton(self, name="flag_chg_nfchk", size=32)
        self.flag_del = MoekButton(self, name="trash", size=32, tooltip="usuń flagę")
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(0)
        hlay.addWidget(self.flag_move)
        hlay.addWidget(self.flag_chg)
        hlay.addWidget(self.flag_del)
        self.setLayout(hlay)
        self.fchk = False
        self.flag_move.clicked.connect(self.init_move)
        self.flag_chg.clicked.connect(self.flag_fchk_change)
        self.flag_del.clicked.connect(self.flag_delete)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "fchk":
            self.flag_chg.set_icon(name="flag_chg_nfchk", size=32) if val else self.flag_chg.set_icon(name="flag_chg_fchk", size=32)
            self.flag_chg.set_tooltip("ustaw flagę bez kontroli terenowej") if val else self.flag_chg.set_tooltip("ustaw flagę z kontrolą terenową")

    def init_move(self):
        """Zmiana lokalizacji flagi."""
        dlg.obj.flag_hide(True)
        dlg.mt.init("flag_move")

    def flag_fchk_change(self):
        """Zmiana rodzaju flagi."""
        table = f"team_{str(dlg.team_i)}.flagi"
        bns = f" WHERE id = {dlg.obj.flag}"
        db_attr_change(tbl=table, attr="b_fieldcheck", val=not self.fchk, sql_bns=bns, user=False)
        self.fchk = not self.fchk
        # Włączenie tego rodzaju flag, jeśli są wyłączone:
        name = "flagi_z_teren" if self.fchk else "flagi_bez_teren"
        val = dlg.cfg.get_val(name)
        if val == 0:
            dlg.cfg.set_val(name, 1)
        dlg.proj.mapLayersByName("flagi_bez_teren")[0].triggerRepaint()
        dlg.proj.mapLayersByName("flagi_z_teren")[0].triggerRepaint()
        dlg.obj.flag_ids = get_flag_ids(dlg.cfg.flag_case())  # Aktualizacja listy flag w ObjectManager
        dlg.obj.list_position_check("flag")  # Aktualizacja pozycji na liście obecnie wybranej flagi

    def flag_delete(self):
        """Usunięcie flagi z bazy danych."""
        db = PgConn()
        sql = "DELETE FROM team_" + str(dlg.team_i) + ".flagi WHERE id = " + str(dlg.obj.flag) + ";"
        if db:
            res = db.query_upd(sql)
            if res:
                dlg.obj.flag = None
        # Aktualizacja listy flag w ObjectManager:
        dlg.obj.flag_ids = get_flag_ids(dlg.cfg.flag_case())


class ParkingTools(QFrame):
    """Menu przyborne dla parkingów."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(96, 32)
        self.setObjectName("main")
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.parking_chg = MoekButton(self, name="parking_before", size=32)
        self.parking_move = MoekButton(self, name="move", size=32, checkable=True, tooltip="zmień lokalizację miejsca parkowania")
        self.parking_del = MoekButton(self, name="trash", size=32, tooltip="usuń miejsce parkowania")
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(1)
        hlay.addWidget(self.parking_chg)
        hlay.addWidget(self.parking_move)
        hlay.addWidget(self.parking_del)
        self.setLayout(hlay)
        self.status = 0
        self.parking_chg.clicked.connect(self.parking_status_change)
        self.parking_move.clicked.connect(self.init_move)
        self.parking_del.clicked.connect(self.parking_delete)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "status":
            self.parking_chg.set_icon(name="parking_after", size=32) if val == 0 else self.parking_chg.set_icon(name="parking_before", size=32)
            self.parking_chg.set_tooltip("oznacz miejsce parkowania jako nieodwiedzone") if val else self.parking_chg.set_tooltip("potwierdź odwiedzenie miejsca parkingowego")

    def init_move(self):
        """Zmiana lokalizacji parkingu."""
        dlg.obj.parking_hide(True)
        dlg.mt.init("parking_move")

    def parking_status_change(self):
        """Zmiana statusu parkingu."""
        table = f"team_{str(dlg.team_i)}.parking"
        bns = f" WHERE id = {dlg.obj.parking}"
        self.status = 0 if self.status == 1 else 1
        db_attr_change(tbl=table, attr="i_status", val=self.status, sql_bns=bns, user=False)
        # Włączenie tego rodzaju parkingów, jeśli są wyłączone:
        name = "parking_planowane" if self.status == 0 else "parking_odwiedzone"
        val = dlg.cfg.get_val(name)
        if val == 0:
            dlg.cfg.set_val(name, 1)
        dlg.obj.parking_ids = get_parking_ids(dlg.cfg.parking_case())  # Aktualizacja listy flag w ObjectManager
        dlg.obj.list_position_check("parking")  # Aktualizacja pozycji na liście obecnie wybranego parkingu
        dlg.proj.mapLayersByName("parking_planowane")[0].triggerRepaint()
        dlg.proj.mapLayersByName("parking_odwiedzone")[0].triggerRepaint()

    def parking_delete(self):
        """Usunięcie parkingu z bazy danych."""
        db = PgConn()
        sql = "DELETE FROM team_" + str(dlg.team_i) + ".parking WHERE id = " + str(dlg.obj.parking) + ";"
        if db:
            res = db.query_upd(sql)
            if res:
                dlg.obj.parking = None
        # Aktualizacja listy parkingów w ObjectManager:
        dlg.obj.parking_ids = get_parking_ids(dlg.cfg.parking_case())


class TabBox(QFrame):
    """Widget wyświetlający przyciski do przełączania subpage'y w formularzu wyrobiska."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(412, 28)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)
        self.setLayout(self.lay)
        self.setStyleSheet(" QFrame {background-color: transparent; border: none} ")
        self.widgets = {}
        self.btns = [
            {"index": 0, "title": "CHARAKTERYSTYKA", "active": True},
            {"index": 1, "title": "MIDAS", "active": False},
            {"index": 2, "title": "ZAGROŻENIA", "active": False},
            {"index": 3, "title": "REKULTYWACJA", "active": False},
            {"index": 4, "title": "ODPADY", "active": False},
            {"index": 5, "title": "ZGŁOSZENIE", "active": False}
        ]
        for btn in self.btns:
            _btn = TabButton(self, index=btn["index"], title=btn["title"], active=btn["active"])
            exec(f'self.lay.addWidget(_btn)')
            btn_idx = f'btn_{btn["index"]}'
            self.widgets[btn_idx] = _btn
        spacer = MoekDummy(width=1, height=28, color="rgba(20, 20, 20, 0.71)", spacer="horizontal")
        self.lay.addWidget(spacer)
        self.cur_idx = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cur_idx" and val != None:
            self.parent().parent().ssb.setCurrentIndex(val)
            self.btns_state()

    def btns_state(self):
        """Aktualizacja stanów przycisków."""
        for btn in self.btns:
            if btn["index"] == self.cur_idx:
                self.widgets[f'btn_{btn["index"]}'].setChecked(True)
            else:
                self.widgets[f'btn_{btn["index"]}'].setChecked(False)


class TabButton(QPushButton):
    """Przyciski menu w TabBox'ie."""
    def __init__(self, *args, index, title, active):
        super().__init__(*args)
        self.index = index
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFixedHeight(28)
        self.setText(title)
        self.setCheckable(True)
        self.active = active
        self.set_style()
        self.clicked.connect(self.state_changed)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.set_style()

    def state_changed(self):
        """Aktualizacja bieżącego indeksu tabbox'u po naciśnięciu przycisku."""
        self.parent().cur_idx = self.index

    def set_style(self):
        """Modyfikacja stylesheet."""
        alpha_sub = 0.0 if self.active else 0.5
        self.setStyleSheet("""
                            QPushButton {
                                font-size: 6pt;
                                font-weight: bold;
                                color: rgba(255, 255, 255, """ + str(0.8 - alpha_sub) + """);
                                background-color: rgba(20, 20, 20, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            QPushButton:hover {
                                font-size: 6pt;
                                font-weight: bold;
                                color: rgba(255, 255, 255, """ + str(1.0 - alpha_sub) + """);
                                background-color: rgba(20, 20, 20, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            QPushButton:checked {
                                font-size: 6pt;
                                font-weight: bold;
                                color: rgba(255, 255, 255, """ + str(1.0 - alpha_sub) + """);
                                background-color: rgba(55, 55, 55, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            """)


class ParamBox(QFrame):
    """Widget do wyświetlania wartości lub zakresu parametru wraz z opisem (nagłówkiem).
    item: label, line_edit, ruler."""
    def __init__(self, *args, margins=False, list_width = 200, width=160, height=22, down_height=12, item="label", val_width=40, val_width_2=40, value=" ", value_2=None, sep_width=17, sep_txt="–", max_len=None, validator=None, placeholder=None, zero_allowed=False, min_max=False, title_down=None, title_down_2=None, title_left=None, icon=None, tooltip="", val_display=False, trigger=None, fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.item = item
        _width = width
        _height = height
        down_height = down_height if title_down else 0
        margin_height = 8 if margins else 0
        all_height = _height + 1 + down_height + margin_height
        self.val_width = val_width + val_width_2 + sep_width if value_2 else val_width
        self.val_width_1 = val_width if title_left or icon else _width
        self.val_width_2 = val_width_2 if title_left or icon else _width
        self.focus_switch = False
        self.setFixedSize(width, all_height)
        self.is_enabled = True
        self.min_max = min_max
        self.setStyleSheet(" QFrame {background-color: transparent; border: none} ")
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 4, 0, 4) if margins else lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.setLayout(lay)
        self.box = MoekGridBox(self, margins=[0, 0, 0, 0], spacing=0)
        lay.addWidget(self.box)
        self.widgets = self.composer(value, value_2, title_left, title_down, icon)
        for widget in self.widgets:
            if widget["item"] == "title_left":
                _width = _width - self.val_width
                self.title_left = TextItemLabel(self, height=_height, width=_width, font_size=8, text=title_left)
                self.box.glay.addWidget(self.title_left, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "icon":
                self.icon = MoekButton(self, name=icon, size=34, checkable=False, enabled=True, tooltip=tooltip)
                self.box.glay.addWidget(self.icon, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "valbox_1":
                if self.item == "label":
                    self.valbox_1 = TextItemLabel(self, height=_height, width=self.val_width_1, bgr_alpha=0.15, text=value)
                elif self.item == "line_edit":
                    self.valbox_1 = CanvasLineEdit(self, width=self.val_width_1, height=_height, font_size=8, max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, trigger=trigger, fn=fn[0])
                elif self.item == "line_edit_left":
                    self.valbox_1 = CanvasLineEdit(self, width=self.val_width_1, height=_height, font_size=8, align="AlignLeft", max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, trigger=trigger, fn=fn[0])
                elif self.item == "ruler":
                    self.valbox_1 = CanvasLineEdit(self, width=self.val_width_1, height=_height, font_size=8, r_widget="ruler", max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, fn=fn[0])
                elif self.item == "combo":
                    self.valbox_1 = CanvasArrowlessComboBox(self, width=list_width, height=_height, font_size=8, trigger=trigger, fn=fn)
                elif self.item == "combo_tv":
                    self.valbox_1 = CanvasArrowlessComboBox(self, height=_height, font_size=8, tv=True, val_display=val_display, trigger=trigger, fn=fn)
                self.box.glay.addWidget(self.valbox_1, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "valbox_2":
                if self.item == "label":
                    self.valbox_2 = TextItemLabel(self, height=_height, width=self.val_width_2, bgr_alpha=0.15, text=value)
                elif self.item == "line_edit":
                    self.valbox_2 = CanvasLineEdit(self, width=self.val_width_2, height=_height, font_size=8, max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, fn=fn[1])
                    self.focus_switch = True
                elif self.item == "ruler":
                    self.valbox_2 = CanvasLineEdit(self, width=self.val_width_2, height=_height, font_size=8, r_widget="ruler", max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, fn=fn[1])
                    self.focus_switch = True
                self.box.glay.addWidget(self.valbox_2, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "separator":
                self.separator = TextItemLabel(self, height=_height, width=sep_width, text=sep_txt)
                self.box.glay.addWidget(self.separator, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "line":
                self.line = MoekHLine(self)
                self.box.glay.addWidget(self.line, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "titlebox_1":
                self.titlebox_1 = TextItemLabel(self, height=down_height, width=self.val_width_1, align="left", font_size=6, font_weight="bold", font_alpha=0.6, text=title_down)
                self.box.glay.addWidget(self.titlebox_1, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "titlebox_2":
                self.titlebox_2 = TextItemLabel(self, height=down_height, align="left", width=val_width_2, font_size=6, font_weight="bold", font_alpha=0.6, text=title_down_2)
                self.box.glay.addWidget(self.titlebox_2, widget["row"], widget["col"], widget["r_span"], widget["c_span"])

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.is_enabled = _bool
        widgets = (self.box.glay.itemAt(i).widget() for i in range(self.box.glay.count()))
        for widget in widgets:
            if not widget:
                continue
            if isinstance(widget, MoekButton):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)

    def composer(self, value, value_2, title_left, title_down, icon):
        """Zwraca listę z ustawieniami kompozycji widgetów, w zależności od parametrów."""
        comp_val = 0
        comp_val = comp_val + 1 if value else comp_val
        comp_val = comp_val + 2 if value_2 else comp_val
        comp_val = comp_val + 4 if title_left else comp_val
        comp_val = comp_val + 8 if title_down else comp_val
        comp_val = comp_val + 16 if icon else comp_val
        if comp_val == 9:  # 1
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 1, "col": 0, "r_span": 1, "c_span": 1, "item": "line"},
                {"row": 2, "col": 0, "r_span": 1, "c_span": 1, "item": "titlebox_1"}
            ]
        elif comp_val == 5:  # 2
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "title_left"},
                {"row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 1, "col": 0, "r_span": 1, "c_span": 2, "item": "line"}
            ]
        elif comp_val == 15:  # 3
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "title_left"},
                {"row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 0, "col": 2, "r_span": 1, "c_span": 1, "item": "separator"},
                {"row": 0, "col": 3, "r_span": 1, "c_span": 1, "item": "valbox_2"},
                {"row": 1, "col": 0, "r_span": 1, "c_span": 4, "item": "line"},
                {"row": 2, "col": 1, "r_span": 1, "c_span": 1, "item": "titlebox_1"},
                {"row": 2, "col": 3, "r_span": 1, "c_span": 1, "item": "titlebox_2"}
            ]
        elif comp_val == 27:  # 4
            widgets = [
                {"row": 0, "col": 0, "r_span": 3, "c_span": 1, "item": "icon"},
                {"row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 0, "col": 2, "r_span": 1, "c_span": 1, "item": "separator"},
                {"row": 0, "col": 3, "r_span": 1, "c_span": 1, "item": "valbox_2"},
                {"row": 1, "col": 1, "r_span": 1, "c_span": 3, "item": "line"},
                {"row": 2, "col": 1, "r_span": 1, "c_span": 1, "item": "titlebox_1"},
                {"row": 2, "col": 3, "r_span": 1, "c_span": 1, "item": "titlebox_2"}
            ]
        elif comp_val == 1:  # 5
            widgets = [
                {"row": 0, "col": 0, "r_span": 3, "c_span": 4, "item": "valbox_1"}
            ]
        elif comp_val == 8:  # 6
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 4, "item": "line"},
                {"row": 1, "col": 0, "r_span": 2, "c_span": 4, "item": "titlebox_1"}
            ]
        elif comp_val == 13:  # 7
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "title_left"},
                {"row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 1, "col": 0, "r_span": 1, "c_span": 2, "item": "line"},
                {"row": 2, "col": 1, "r_span": 1, "c_span": 1, "item": "titlebox_1"}
            ]
        return widgets

    def value_change(self, attrib, val):
        """Zmienia wyświetlaną wartość parametru."""
        if attrib == "value":
            if isinstance(self.valbox_1, (CanvasLineEdit, CanvasArrowlessComboBox)):
                self.valbox_1.set_value(val)
            else:
                self.valbox_1.setText(str(val)) if val else self.valbox_1.setText("")
        elif attrib == "value_2":
            if isinstance(self.valbox_2, CanvasLineEdit):
                self.valbox_2.set_value(val)
            else:
                self.valbox_2.setText(str(val)) if val else self.valbox_2.setText("")

    def focus_switcher(self, val):
        """Ustawia focus na lineedit z pustą wartością, po zatwierdzeniu wartości w innym lineedit z tego parambox'u."""
        if not self.focus_switch:
            return
        if self.valbox_1.cur_val == val and not self.valbox_2.cur_val:
            if not dlg.wyr_panel.focus_void:
                self.valbox_2.setFocus()
        elif self.valbox_2.cur_val == val and not self.valbox_1.cur_val:
            if not dlg.wyr_panel.focus_void:
                self.valbox_1.setFocus()

    def minmax_check(self):
        """Sprawdza, czy wartości min i max nie są odwrócone oraz zamienia je, jeśli trzeba."""
        if not self.min_max:
            return
        val_1 = self.valbox_1.cur_val
        val_2 = self.valbox_2.cur_val
        if val_1 == None or val_2 == None:
            return
        if float(val_1) > float(val_2):
            dlg.wyr_panel.focus_void = True
            self.valbox_1.value_change(val_2)
            self.valbox_2.value_change(val_1)
            dlg.wyr_panel.focus_void = False


class ParamTextBox(QFrame):
    """Widget do wyświetlania i edycji parametru tekstowego (np. uwagi) wraz z nagłówkiem i opcjonalnym licznikiem użytch znaków."""
    def __init__(self, *args, margins=False, width=328, height=80, down_height=12, title=None, edit=False, trigger=None, txt_limiter=False, centered=False, fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setObjectName("main")
        _width = width
        _height = height
        down_height = down_height if title else 0
        margin_height = 8 if margins else 0
        all_height = _height + 1 + down_height + margin_height
        self.setFixedSize(width, all_height)
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 4, 0, 4) if margins else lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.setLayout(lay)
        self.box = MoekVBox(self, margins=[0, 0, 0, 0], spacing=0)
        lay.addWidget(self.box)
        self.txtbox = TextBox(self, height=_height, width=_width, edit=edit, trigger=trigger, txt_limiter=txt_limiter, centered=centered, fn=fn)
        self.box.lay.addWidget(self.txtbox)
        self.line = MoekHLine(self)
        self.box.lay.addWidget(self.line)
        self.txt_limiter = txt_limiter
        if title:
            self.title = title
            self.titlebox = TextItemLabel(self, height=down_height, width=_width, align="left", font_size=6, font_weight="bold", font_alpha=0.6, text=title)
            self.box.lay.addWidget(self.titlebox)
        self.setStyleSheet(" QFrame#main{background-color: transparent; border: none} ")

    def counter_update(self, cnt):
        """Aktualizacja licznika użytych znaków."""
        self.titlebox.setText(f"{self.title}  ({cnt} / 255)")

    def value_change(self, val):
        """Zmienia wyświetlany tekst."""
        self.txtbox.cur_val = val

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        widgets = (self.box.lay.itemAt(i).widget() for i in range(self.box.lay.count()))
        for widget in widgets:
            widget.set_enabled(_bool)


class TextBox(QTextEdit):
    """Wyświetla tekst z możliwością edycji i opcjonalnym liczeniem użytych znaków."""
    def __init__(self, *args, width, height, edit, trigger, fn, txt_limiter=False, centered=False):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignCenter)
        self.txt_limiter = txt_limiter
        self.fn = fn
        self.edit = edit
        self.trigger = trigger
        self.centered = centered
        self.setReadOnly(not self.edit)
        if not self.edit:
            self.viewport().setCursor(Qt.ArrowCursor)
        self.hover = False
        self.focus = False
        self.attr_void = True
        self.cur_val = None
        self.attr_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "hover":
            if hasattr(self, "focus"):
                self.set_style()
        if attr == "focus":
            if hasattr(self, "hover"):
                self.set_style()
        if attr == "cur_val" and not self.attr_void:
            self.value_changed()
            if self.txt_limiter:
                self.counter_update()
            if self.trigger:
                exec(f'dlg.wyr_panel.{self.trigger}')

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie widget'u poleceniem zewnętrznym."""
        self.setEnabled(_bool)
        self.set_style()

    def set_value(self, val):
        """Próba zmiany wartości."""
        if not val or len(str(val)) == 0:  # Wartość Null
            self.cur_val = None
        else:
            self.cur_val = val

    def db_update(self, txt_val, tbl, attr, sql_bns):
        """Aktualizacja wartości w db."""
        if not txt_val:
            sql_text = "NULL"
        else:
            txt = txt_val.replace("'", "''")
            sql_text = f"'{txt}'"
        db_attr_change(tbl=tbl, attr=attr, val=sql_text, sql_bns=sql_bns, user=False)

    def value_changed(self):
        """Aktualizacja tekstu po zmianie wartości."""
        self.setPlainText(self.cur_val) if self.cur_val else self.clear()
        self.set_style()

    def set_style(self):
        """Modyfikacja stylesheet."""
        self.setAlignment(Qt.AlignCenter) if self.centered else self.setAlignment(Qt.AlignLeft)
        if self.isEnabled():
            alpha = 0.3 if self.hover or self.focus else 0.2
            color = "white"
        else:
            alpha = 0.1
            color = "grey"
        self.setStyleSheet("""
                            QTextEdit {
                            border: none;
                            background-color: rgba(255, 255, 255, """ + str(alpha) + """);
                            color: """ + color + """;
                            font-size: 8pt;
                            }
                            QScrollBar:vertical {
                                border: none;
                                background: transparent;
                                width: 14px;
                                margin: 4px 3px 4px 3px;
                            }
                            QScrollBar::handle:vertical {
                                min-height: 30px;
                                border: none;
                                border-radius: 4px;
                                background-color: rgba(0, 0, 0, 0.4);
                            }
                            QScrollBar::add-line:vertical {
                                height: 0px;
                                subcontrol-position: bottom;
                                subcontrol-origin: margin;
                            }
                            QScrollBar::sub-line:vertical {
                                height: 0 px;
                                subcontrol-position: top;
                                subcontrol-origin: margin;
                            }
                            """)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.isEnabled() and self.edit:
            self.hover = True

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self.edit:
            self.hover = False

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.edit:
            self.focus = True

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.edit:
            return
        self.focus = False
        self.value_change(self.toPlainText())

    def value_change(self, txt):
        self.set_value(txt)
        if self.fn:
            self.run_fn()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.clearFocus()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        if self.txt_limiter:
            self.counter_update()

    def counter_update(self):
        """Odświeża licznik wykorzystanych znaków."""
        self.parent().parent().counter_update(len(self.toPlainText()))

    def run_fn(self):
        """Odpalenie funkcji po zmianie wartości."""
        for fn in self.fn:
            try:
                exec(eval("f'{}'".format(fn)))
            except Exception as err:
                print(f"[run_fn] Błąd zmiany wartości: {err}")


class TextItemLabel(QLabel):
    """Widget do wyświetlania nagłówka parametru obiektu."""
    def __init__(self, *args, width=118, height=24, text="", align="center", font_size=10, font_weight="normal", font_alpha=1.0, bgr_alpha=0.0):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setText(text)
        self.align = align
        self.font_size = font_size
        self.font_weight = font_weight
        self.font_alpha = font_alpha
        self.bgr_alpha = bgr_alpha
        self.set_style()

    def set_style(self):
        """Modyfikacja stylesheet."""
        font_alpha = self.font_alpha if self.isEnabled() else 0.1
        padding = "0px 0px 0px 0px" if self.align == "center" else "0px 6px 0px 0px"
        self.setAlignment(Qt.AlignCenter) if self.align == "center" else self.setAlignment(Qt.AlignLeft| Qt.AlignVCenter)
        self.setStyleSheet(f"""
                            background-color: rgba(255, 255, 255, {self.bgr_alpha});
                            color: rgba(255, 255, 255, {font_alpha});
                            font-size: {self.font_size}pt;
                            font-weight: {self.font_weight};
                            padding: {padding};
                            """)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie widget'u poleceniem zewnętrznym."""
        self.setEnabled(_bool)
        self.set_style()


class MoekHLine(QFrame):
    """Linia pozioma."""
    def __init__(self, *args, px=1):
        super().__init__(*args)
        self.setFixedHeight(px)
        self.set_style()

    def set_style(self):
        """Modyfikacja stylesheet."""
        alpha = 0.6 if self.isEnabled() else 0.1
        self.setStyleSheet(f"""
                            background-color: rgba(255, 255, 255, {alpha});
                            """)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie widget'u poleceniem zewnętrznym."""
        self.setEnabled(_bool)
        self.set_style()


class IdSpinBox(QFrame):
    """Widget z centralnie umieszczonym labelem i przyciskami zmiany po jego obu stronach."""
    def __init__(self, *args, _obj, width=90, le_width=None, height=34, max_len=4, validator="id", placeholder=None, theme="dark"):
        super().__init__(*args)
        self.obj = _obj
        self.max_len = max_len
        self.validator = validator
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        if theme == "color":
            theme = "light"  # Potrzebne dla prev_btn i next_btn
            self.setStyleSheet(" QFrame#main {background-color: rgba(40, 170, 40, 204); border: none} ")
        else:
            self.setStyleSheet(" QFrame#main {background-color: transparent; border: none} ")
        self.prev_btn = MoekButton(self, name=f"id_prev_{theme}", size=22, hsize=height, checkable=False)
        self.prev_btn.clicked.connect(self.prev_clicked)
        self.next_btn = MoekButton(self, name=f"id_next_{theme}", size=22, hsize=height, checkable=False)
        self.next_btn.clicked.connect(self.next_clicked)
        fn = ['dlg.obj.set_object_from_input(self.text(), self.parent().obj)']
        w = le_width if le_width else self.width() - 44
        self.idbox = CanvasLineEdit(self, width=w, height=self.height() - 4, max_len=self.max_len, validator=self.validator, placeholder=placeholder, null_allowed=False, fn=fn, theme=theme)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(0)
        self.hlay.addWidget(self.prev_btn)
        self.hlay.addWidget(self.idbox)
        self.hlay.addWidget(self.next_btn)
        self.setLayout(self.hlay)
        self.id = None
        self.attr_void = True
        self.locked = False
        self.edited = False
        self.attr_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "id":
            self.idbox.set_value(str(val))
        if attr == "locked" and not self.attr_void:
            self.idbox.locked = val
        if attr == "edited" and not self.attr_void:
            self.idbox.edited = val
            self.prev_btn.setEnabled(not val)
            self.next_btn.setEnabled(not val)

    def set_theme(self, theme):
        """Zmiana kolorystyki widgetu."""
        if theme == "green":
            self.setStyleSheet(" QFrame#main {background-color: rgba(40, 170, 40, 204); border: none} ")
        elif theme == "purple":
            self.setStyleSheet(" QFrame#main {background-color: rgba(180, 40, 180, 204); border: none} ")
        else:
            self.setStyleSheet(" QFrame#main {background-color: transparent; border: none} ")

    def prev_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk prev_btn."""
        dlg.obj.object_prevnext(self.obj, False)

    def next_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk next_bnt."""
        dlg.obj.object_prevnext(self.obj, True)


class CanvasLineEdit(QLineEdit):
    """Lineedit z odpalaniem funkcji po zatwierdzeniu zmian tekstu."""
    def __init__(self, *args, width, height, r_widget=None, font_size=12, align="AlignCenter", max_len=None, validator=None, placeholder=None, zero_allowed=False, null_allowed=True, theme="dark", trigger=None, fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setFrame(False)
        self.font_size = font_size
        self.align = align
        self.r_widget = r_widget
        if self.r_widget == "ruler":
            self.r_widget = MoekSlideButton(self, name="ruler", size=24, checkable=True)
        self.max_len = max_len
        if max_len:
            self.setMaxLength(max_len)
        self.validator = validator
        if self.validator == "id":
            self.setValidator(QRegExpValidator(QRegExp("[1-9][0-9]*")))
        elif self.validator == "id_arkusz":
            self.setValidator(QRegExpValidator(QRegExp("[0-1]([0-9]|[_])*")))
        elif self.validator == "000" or self.validator == "order":
            self.setValidator(QRegExpValidator(QRegExp("[0-9]*")))
        elif self.validator == "00.0":
            self.setValidator(QRegExpValidator(QRegExp("([0-9]|[,]|[.])*")))
        elif self.validator == "hours":
            self.setValidator(QRegExpValidator(QRegExp("^([1-9]|0[1-9]|1[0-9]|2[0-3])")))
        elif self.validator == "minutes":
            self.setValidator(QRegExpValidator(QRegExp("^[0]?[0-9]$|^[1-5]?[0-9]$")))
        elif self.validator == "days":
            self.setValidator(QRegExpValidator(QRegExp("^[0]?[1-9]$|^[1-2]?[0-9]$|^[3][0-1]$")))
        elif self.validator == "months":
            self.setValidator(QRegExpValidator(QRegExp("^[0]?[1-9]$|^[1][0-2]$")))
        elif self.validator == "years":
            self.setValidator(QRegExpValidator(QRegExp("^1[8-9]$|^2[0-3]$|^201[8-9]$|^202[0-3]$")))
        self.color = "255, 255, 255" if theme == "dark" else "0, 0, 0"
        self.attr_void = True
        self.locked = False
        self.edited = False
        self.attr_void = False
        self.trigger = trigger
        self.fn = fn
        self.placeholder = placeholder
        self.zero_allowed = zero_allowed
        self.null_allowed = null_allowed
        self.mt_enabled = False
        self.focused = False
        self.hover = False
        self.grey = False
        self.numerical = False
        self.cur_val = None

    def resizeEvent(self, event):
        """Ustawienie lokalizacji doadtkowych przycisków po zmianie rozmiaru lineedit'u."""
        if self.r_widget:
            offset = 18 if self.r_widget.slided or self.r_widget.isChecked() else 0
            self.r_widget.setGeometry(self.width() - 6 - offset, (self.height()/2) - (self.r_widget.height()/2), self.r_widget.width(), self.r_widget.height())
        super().resizeEvent(event)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "hover":
            if hasattr(self, "grey"):
                self.set_style()
        if attr == "grey":
            if hasattr(self, "hover"):
                self.set_style()
        if attr == "cur_val":
            if val == None:
                self.numerical = False
            self.value_changed()
        if (attr == "edited" or attr == "locked") and not self.attr_void:
            self.set_style()

    def sql_parser(self, val):
        """Zwraca wartość prawidłową dla formuły sql."""
        if val:
            result = val if self.numerical else f"'{val}'"
        else:
            result = 'Null'
        return result

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie widget'u poleceniem zewnętrznym."""
        self.setEnabled(_bool)
        self.set_style()

    def set_value(self, val):
        """Próba zmiany wartości."""
        if not val or val == 'None' or val == '' or len(str(val)) == 0:  # Wartość Null
            if str(val) != "0.0":
                self.cur_val = None if self.null_allowed else self.cur_val
                return
        if self.validator == "00.0" or self.validator == "000" or self.validator == "order":
            # Próba konwersji tekstu na wartość float:
            num_val = self.numeric_formater(str(val))
            self.numerical = True if num_val != -1 else False
            if num_val != -1:
                self.cur_val = str(num_val)
                if self.validator != "order":
                    return
            else:
                self.cur_val = self.cur_val
                return
        if self.validator == "years":
            if len(val) == 2:
                # Uzupełnienie wartości roku do formatu 4-cyfrowego:
                val = '20' + val
            elif len(val) == 1 or len(val) == 3:
                # Wartość roku niepełna:
                self.cur_val = self.cur_val
                return
            if int(val) >= 2018 and int(val) <= 2023:
                # Ograniczenie wartości roku do przedziału 2018-2023:
                self.cur_val = val
            else:
                self.cur_val = self.cur_val
                return
        # Dodanie zer do formatu dwu- lub trzycyfrowego:
        lead_zeros = [("order", 3), ("hours", 2), ("minutes", 2), ("days", 2), ("months", 2)]
        for lz in lead_zeros:
            if self.validator == lz[0]:
                if int(val) == 0 and lz[0] not in ["minutes", "hours"]:
                    # Uniemożliwienie ustalenia wartości 0:
                    self.cur_val = self.cur_val
                    return
                self.cur_val = str(val).zfill(lz[1])
                return
        self.cur_val = val

    def value_changed(self):
        """Aktualizacja tekstu lineedit'u po zmianie wartości."""
        self.set_grey()
        self.setText(self.placeholder) if self.placeholder and self.cur_val == None else self.setText(self.cur_val)
        if self.trigger and hasattr(dlg, "wyr_panel"):
            exec(f'dlg.wyr_panel.{self.trigger}')
        if isinstance(self.parent().parent(), ParamBox):
            if self.cur_val != None:
                self.parent().parent().focus_switcher(self.cur_val)
            if not dlg.wyr_panel.focus_void:
                self.parent().parent().minmax_check()

    def set_grey(self):
        """Ustalenie, czy wartość powinna zostać wyszarzona."""
        if not self.placeholder:
            self.grey = False
            return
        if self.cur_val:
            self.grey = False
            return
        # Wartość jest równa placeholder'owi:
        if self.focused:# and not self.mt_enabled:
            self.grey = False
            return
        if self.numerical and int(self.cur_val) == 0 and self.zero_allowed:
            self.grey = False
            return
        self.grey = True

    def set_style(self):
        """Modyfikacja stylesheet przy hoveringu lub zmianie tekstu."""
        if self.isEnabled():
            alpha = 0.3 if self.hover else 0.2
        else:
            alpha = 0.1
        if self.placeholder:
            font_color = "0, 0, 0, 0.3" if self.grey else self.color
        else:
            font_color = self.color
        if self.locked and not self.edited:
            border = "1px solid black"
        elif self.edited:
            border = "1px solid red"
        else:
            border = "none"
        self.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(""" + self.color + """, """ + str(alpha) + """);
                        color: rgba(""" + font_color + """);
                        font-size: """ + str(self.font_size) + """pt;
                        border: """ + border + """;
                        padding: 0px 0px 2px 2px;
                        qproperty-alignment: """ + str(self.align) + """;
                        }
                    """)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.isEnabled():
            self.hover = True

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hover = False

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused = True
        if self.grey:
                self.setText("")
                self.grey = False
        else:
            self.selectAll()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focused = False
        self.value_change(self.text())

    def value_change(self, txt):
        self.set_value(txt)
        if self.fn:
            self.run_fn()

    def mousePressEvent(self, event):
        if self.focused:
            self.focused = False
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.clearFocus()
        else:
            super().keyPressEvent(event)

    def numeric_formater(self, val):
        """Zwraca liczbę przekonwertowaną z wartości tekstowej. Jeśli tekst nie spełnia wymagań, to zwraca -1."""
        if val == None:
            return -1
        text = val.replace(",", ".")
        try:
            num_val = float(text)
        except ValueError:
            return -1
        if self.validator == "00.0" and ((self.max_len == 3 and num_val >= 10) or (self.max_len == 4 and num_val >= 100)):
            # Przepełnienie pola liczbowego:
            return -1
        if num_val == 0 and not self.zero_allowed:
            # Wartość nie może być zerem
            return -1
        if self.validator == "000":
            return int(num_val)
        elif self.validator == "00.0":
            return round(num_val, 1)

    def run_fn(self):
        """Odpalenie funkcji po zmianie wartości."""
        for fn in self.fn:
            try:
                exec(eval("f'{}'".format(fn)))
            except Exception as err:
                print(f"[run_fn] Błąd zmiany wartości: {err}")


class TextPadBox(QFrame):
    """Moduł notatnika."""
    def __init__(self, *args, height, obj, width=None):
        super().__init__(*args)
        self.obj = obj
        self.setObjectName("main")
        self.setFixedHeight(height)
        _width = self.parent().width() if not width else width
        self.setFixedWidth(_width)
        self.button_box = MoekHBox(self, margins=[5,0,15,0], spacing=2)
        self.button_box.setFixedWidth(_width)
        self.button_box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.clear_btn = MoekButton(self, name="textpad_clear", size=34, checkable=False)
        self.revert_btn = MoekButton(self, name="textpad_revert", size=34, checkable=False)
        self.accept_btn = MoekButton(self, name="textpad_accept", size=34, checkable=False)
        self.button_box.lay.addWidget(self.clear_btn)
        self.button_box.lay.addItem(spacer)
        self.button_box.lay.addWidget(self.revert_btn)
        self.button_box.lay.addWidget(self.accept_btn)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)
        self.textpad = TextPad(self, width=self.width() - 6, height=self.height() - 34)
        vlay.addWidget(self.textpad)
        vlay.addWidget(self.button_box)
        vlay.setAlignment(self.button_box, Qt.AlignCenter)
        self.setLayout(vlay)
        self.backup_text = ""
        self.clear_btn.clicked.connect(self.text_clear)
        self.revert_btn.clicked.connect(self.text_revert)
        self.accept_btn.clicked.connect(self.text_change)

    def set_text(self, text):
        """Aktualizacja textpadbox'u po zmianie tekstu."""
        self.backup_text = text
        self.textpad.setPlainText(text) if text else self.textpad.clear()
        if self.textpad.doc.isModified():
            self.textpad.doc.setModified(False)
        else:
            self.textpad.modified(False)

    def get_text(self):
        """Zwraca aktualny tekst z textpad'u."""
        text = self.textpad.toPlainText()
        return None if text == "" else self.textpad.toPlainText()

    def text_change(self):
        """Aktywuje zmianę tekstu."""
        dlg.obj.set_object_text(self.obj)

    def text_clear(self):
        """Czyści textpad z tekstu (bez zmian w bazie danych)."""
        self.textpad.clear()
        if not self.backup_text and not self.textpad.doc.isModified():
            self.textpad.modified(False)

    def text_revert(self):
        """Przywraca pierwotny tekst do textpad'u (bez zmian w bazie danych)."""
        self.textpad.setPlainText(self.backup_text)
        if not self.backup_text and not self.textpad.doc.isModified():
            self.textpad.modified(False)


class TextPad(QPlainTextEdit):
    """Edytor tekstu do wprowadzania notatek."""
    def __init__(self, *args, width, height):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setBackgroundVisible(False)
        self.hover_on(False)
        self.doc = self.document()
        self.doc.modificationChanged.connect(self.modified)
        self.doc.contentsChanged.connect(self.changed)

    def modified(self, changed):
        """Odpala się po zmianie self.doc.setModified()."""
        self.parent().accept_btn.setEnabled(changed)
        self.parent().revert_btn.setEnabled(changed)

    def changed(self):
        """Odpala się po zmianie zawartości textpad'u."""
        self.parent().clear_btn.setEnabled(False) if self.doc.isEmpty() else self.parent().clear_btn.setEnabled(True)

    def hover_on(self, value):
        """Modyfikacja stylesheet przy hoveringu."""
        if value:
            self.setStyleSheet("QPlainTextEdit {background-color: rgba(255, 255, 255, 0.6); color: white; font-size: 10pt; padding: 0px 0px 0px 0px}")
        else:
            self.setStyleSheet("QPlainTextEdit {background-color: rgba(255, 255, 255, 0.1); color: white; font-size: 10pt; padding: 0px 0px 0px 0px}")


class MoekSideDock(QFrame):
    """Boczny panel zagnieżdżony w mapcanvas'ie, do którego ładowane są toolboxy."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(51)
        self.setFixedHeight(iface.mapCanvas().height())
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        self.toolboxes = {}
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(2)
        vlay.addWidget(self.box)
        vlay.setAlignment(self.box, Qt.AlignCenter)
        self.setLayout(vlay)

    def add_toolbox(self, dict):
        """Dodanie toolbox'a do pojemnika dock'a."""
        _tb = MoekToolBox(self, size=dict["size"], background=dict["background"], direction="vertical")
        self.box.lay.addWidget(_tb)
        tb_name = f'tb_{dict["name"]}'
        for widget in dict["widgets"]:
            if widget["item"] == "button":
                _tb.add_button(widget)
            if widget["item"] == "dummy":
                _tb.add_dummy(widget)
        self.toolboxes[tb_name] = _tb


class MoekBottomDock(QFrame):
    """Dolny panel zagnieżdżony w mapcanvas'ie, do którego ładowane są toolboxy."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(51)
        self.setFixedWidth(iface.mapCanvas().width())
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.box = MoekHBox(self)
        self.box.setObjectName("box")
        self.box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        self.toolboxes = {}
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(2)
        hlay.addWidget(self.box)
        hlay.setAlignment(self.box, Qt.AlignCenter)
        self.setLayout(hlay)

    def add_toolbox(self, dict):
        """Dodanie toolbox'a do pojemnika dock'a."""
        _tb = MoekToolBox(self, size=dict["size"], background=dict["background"], direction="horizontal")
        self.box.lay.addWidget(_tb)
        tb_name = f'tb_{dict["name"]}'
        for widget in dict["widgets"]:
            if widget["item"] == "button":
                _tb.add_button(widget)
            if widget["item"] == "dummy":
                _tb.add_dummy(widget)
        self.toolboxes[tb_name] = _tb


class MoekLeftBottomDock(QFrame):
    """Dolny lewy panel zagnieżdżony w mapcanvas'ie, do którego ładowany jest toolbox z sekwencjami podkładów."""
    # page_changed = pyqtSignal(int)
    def __init__(self, *args, pages=1):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(248, 78)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.box = MoekStackedBox(self)
        self.box.setObjectName("box")
        self.box.pages = {}
        for p in range(pages):
            if p == 0:
                _page = MoekGridBox(self, margins=[13, 9, 10, 9], spacing=0)
            else:
                _page = MoekGridBox(self, margins=[3, 3, 3, 3], spacing=1)
            page_id = f'page_{p}'
            self.box.pages[page_id] = _page
            self.box.addWidget(_page)
        self.box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.cur_page = int()
        self.box.currentChanged.connect(self.page_change)
        self.widgets = {}
        self.heights = [78, 0, 0, 0]
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)
        vlay.addWidget(self.box)
        vlay.setAlignment(self.box, Qt.AlignTop)
        self.setLayout(vlay)
        self.set_style(0.37)

    def page_change(self, index):
        """Zmiana aktywnej strony stackedbox'a."""
        self.cur_page = index
        alpha = 0.8 if index > 0 else 0.37
        self.set_style(alpha)  # Ustalenie przezroczystości tła seq_dock'a
        self.height_change()  # Aktualizacja wysokości dock'u

    def set_style(self, alpha):
        """Zmiana przezroczystości tła w zależności od aktualnej strony stackedbox'a."""
        self.setStyleSheet("""
            QFrame#main{background-color: rgba(30, 30, 30, """ + str(alpha) + """); border: none}
            QFrame#box{background-color: rgba(30, 30, 30, """ + str(alpha) + """); border: none}
            """)

    def height_change(self):
        """Zmiana wysokości dock'u i aktualizacja pozycji na mapcanvas'ie."""
        self.setFixedHeight(self.heights[self.cur_page])
        bottom_y = dlg.canvas.height() - self.height() - 53
        self.move(53, bottom_y)

    def add_seqbar(self, dict):
        """Dodanie do pojemnika panelu custom widget'a belki tytułowej."""
        _stb = CanvasPanelTitleBar(self, title=dict["title"], width=self.width(), back=True, font_size=10)
        self.box.pages[f'page_{dict["page"]}'].glay.addWidget(_stb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])
        stb_name = f'stb_{dict["name"]}'
        self.widgets[stb_name] = _stb

    def add_seqbox(self, dict):
        """Dodanie do pojemnika panelu custom widget'a służącego do sekwencyjnego wczytywania podkładów mapowych."""
        _sqb = MoekSeqBox(self)
        self.box.pages[f'page_{dict["page"]}'].glay.addWidget(_sqb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])
        sqb_name = f'sqb_{dict["name"]}'
        self.widgets[sqb_name] = _sqb

    def add_seqaddbox(self, dict):
        """Dodanie zawartości do dwóch pojemników na wiget'y używane do dodawania podkładów mapowych do sekwencji."""
        _sab = MoekSeqAddBox(self, id=dict["id"])
        self.box.pages[f'page_{dict["page"]}'].glay.addWidget(_sab, dict["row"], dict["col"], dict["r_span"], dict["c_span"])
        sab_name = f'{dict["name"]}'
        self.widgets[sab_name] = _sab

    def add_seqcfgbox(self, dict):
        """Dodanie zawartości do dwóch pojemników ustawień sekwencyjnego wczytywania podkładów mapowych."""
        _scg = MoekSeqCfgBox(self, _id=dict["id"])
        self.box.pages[f'page_{dict["page"]}'].glay.addWidget(_scg, dict["row"], dict["col"], dict["r_span"], dict["c_span"])
        scg_name = f'{dict["name"]}'
        self.widgets[scg_name] = _scg


class MoekToolBox(QFrame):
    """Toolbox, do którego button'y ładowane są w wybranej orientacji."""
    def __init__(self,*args, size, background, direction):
        super().__init__(*args)
        self.direction = direction
        self.widgets = {}
        self.setObjectName("main")
        if self.direction == "horizontal":
            self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.setFixedHeight(size)
            self.box = MoekHBox(self)
            lay = QHBoxLayout()
            lay.setContentsMargins(1, 1, 1, 0)
        else:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
            self.setFixedWidth(size)
            self.box = MoekVBox(self)
            lay = QVBoxLayout()
            lay.setContentsMargins(0, 1, 1, 1)
        self.box.setObjectName("box")
        self.box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setStyleSheet("""
                    QFrame#main{background-color: """ + background + """; border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        lay.setSpacing(0)
        lay.addWidget(self.box)
        self.setLayout(lay)

    def add_button(self, dict):
        """Dodanie przycisku do toolbox'a."""
        icon_name = dict["icon"] if "icon" in dict else dict["name"]
        size = dict["size"] if "size" in dict else 0
        hsize = dict["hsize"] if "hsize" in dict else 0
        _btn = MoekButton(self, size=size, hsize=hsize, name=icon_name, checkable=dict["checkable"], tooltip=dict["tooltip"])
        self.box.lay.addWidget(_btn)
        btn_name = f'btn_{dict["name"]}'
        self.widgets[btn_name] = _btn

    def add_dummy(self, dict):
        """Dodanie pustego obiektu do toolbox'a."""
        size = dict["size"] if "size" in dict else 0
        if self.direction == "horizontal":
            _dmm = MoekDummy(self, width=size, height=50)
        else:
            _dmm = MoekDummy(self, width=50, height=size)
        self.box.lay.addWidget(_dmm)
        dmm_name = f'dmm_{dict["name"]}'
        self.widgets[dmm_name] = _dmm

    def add_seqbox(self, dict):
        """Dodanie do pojemnika panelu custom widget'a służącego dp sekwencyjnego wczytywania podkładów mapowych."""
        _sqb = MoekSeqBox()
        self.box.lay.addWidget(_sqb)
        sqb_name = f'sqb_{dict["name"]}'
        self.widgets[sqb_name] = _sqb


class MoekCfgHSpinBox(QFrame):
    """Widget z centralnie umieszczonym labelem i przyciskami zmiany po jego obu stronach + przycisk konfiguracyjny."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("frm")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.prev_btn = MoekButton(self, name="prev", checkable=False)
        self.prev_btn.clicked.connect(self.prev_clicked)
        self.next_btn = MoekButton(self, name="next", checkable=False)
        self.next_btn.clicked.connect(self.next_clicked)
        self.label = MoekSpinLabel(self)
        self.label.setObjectName("lbl")
        self.cfg_btn = MoekButton(self, name="vcfg", size=17, checkable=False)
        self.cfg_btn.clicked.connect(self.cfg_clicked)
        self.setStyleSheet("""
                    QFrame#frm {border: 2px solid rgb(52, 132, 240); border-radius: 14px}
                    QFrame#lbl {color: rgb(52, 132, 240); qproperty-alignment: AlignCenter}
                    """)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(0)
        self.hlay.addWidget(self.prev_btn, 1)
        self.hlay.addWidget(self.label, 10)
        self.hlay.addWidget(self.cfg_btn, 1)
        self.hlay.addWidget(self.next_btn, 1)
        self.setLayout(self.hlay)

    def cfg_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk cfg."""
        self.parent().parent().cfg_clicked()

    def prev_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk prev_btn."""
        self.parent().parent().prev_map()

    def next_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk next_bnt."""
        self.parent().parent().next_map()

    def resizeEvent(self, e):
        """Zmiana szerokości spinbox'a - aktualizacja labela w spinbox'ie."""
        super().resizeEvent(e)
        self.findChildren(MoekSpinLabel)[0].label_update()


class MoekSeqBox(QFrame):
    """Pojemnik z przyciskami obsługującymi sekwencyjne wczytywanie podkładów mapowych."""
    i_changed = pyqtSignal()
    num_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.timer = None
        self.period = 0  # Całkowity czas
        self.lasted = 0  # Upłynięty czas
        self.tick = 0  # Interwał odświeżania progressbar'a
        self.tack = 0  # Wartość dla progressbar'a
        self.seq_ctrl = MoekSeqCtrlButton(self)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(4)
        self.hlay.addWidget(self.seq_ctrl)
        self.sqb_btns = {}
        for r in range(1, 4):
            _sqb = MoekSeqButton(self, num=r)
            self.hlay.addWidget(_sqb)
            sqb_name = f'sqb_{r}'
            self.sqb_btns[sqb_name] = _sqb
        self.setLayout(self.hlay)
        self.num_changed.connect(self.num_change)
        self.i_changed.connect(self.i_change)
        self.num = 0  # Numer aktywnej sekwencji (0 - brak aktywnej sekwencji)
        self.i = 0  # Liczba porządkowa aktualnego podkładu mapowego w aktywnej sekwencji

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "i":
            self.i_changed.emit()
        elif attr == "num":
            self.num_changed.emit(val)

    def enter_setup(self, seq):
        """Przejście do strony ustawień którejś sekwencji."""
        self.player_reset()  # Wyłączenie player'a, jeśli działa
        dlg.seq_dock.widgets["sab_seq" + str(seq)].combobox_update(seq)  # Aktualizacja combobox'a
        dlg.seq_dock.box.setCurrentIndex(seq)  # Przełączenie panelu na stronę ustawień sekwencji
        if dlg.p_vn.box.currentIndex() == 0:  # Nie jest włączony vn_setup
            if dlg.hk_vn:  # Skróty klawiszowe vn włączone
                dlg.t_hk_vn = True  # Zapamiętanie stanu hk_vn
            dlg.hk_vn = False  # Wyłączenie skrótów klawiszowych do obsługi vn
        dlg.hk_seq = False  # Wyłączenie skrótów klawiszowych do obsługi sekwencji

    def exit_setup(self):
        """Zamknięcie strony ustawień dla którejś sekwencji."""
        sid = dlg.seq_dock.box.currentIndex()
        scb = dlg.seq_dock.widgets["scg_seq" + str(sid)]  # Referencja seqcfgbox'a
        if scb.cnt == 1:  # Nie może być tylko jednego podkładu mapowego w sekwencji
            m_text = "Aby zapisać zmiany w sekwencji, należy wybrać conajmniej 2 podkłady. Naciśnięcie Tak spowoduje wyjście z ustawień bez zapisania zmian."
            reply = QMessageBox.question(iface.mainWindow(), "Kontynuować?", m_text, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            else:
                self.post_setup()
                return
        # Utworzenie listy z ustawieniami sekwencji:
        scgs = dlg.seq_dock.widgets["scg_seq" + str(sid)].findChildren(MoekSeqCfg)  # Referencje do seqcfg'ów
        m_list = []
        order = 0
        for scg in scgs:
            if scg.map > 0:
                m_list.append((scg.map, order, scg.spinbox.value))
                order += 1
        # Aktualizacja sekwencji w db:
        db_sequence_update(sid, m_list)
        self.post_setup()

    def post_setup(self):
        """Wykonywane przy wyjściu z trybu konfiguracyjnego sekwencji."""
        sequences_load()  # Przeładowanie ustawień sekwencji
        dlg.seq_dock.widgets["sqb_seq"].num = 0  # Deaktywacja sekwencji
        dlg.seq_dock.box.setCurrentIndex(0)  # Przejście do strony głównej panelu
        if dlg.p_vn.box.currentIndex() == 0:  # Nie jest włączony vn_setup
            if dlg.t_hk_vn:  # Przed włączeniem trybu konfiguracyjnego były aktywne skróty klawiszowe
                dlg.hk_vn = True  # Ponowne włączenie skrótów klawiszowych do obsługi vn
                dlg.t_hk_vn = False
        dlg.hk_seq = True  # Wyłączenie skrótów klawiszowych do obsługi sekwencji

    def i_change(self):
        """Zmiana bieżącego podkładu mapowego w aktywnej sekwencji."""
        try:
            self.change_map()
        except KeyError:
            pass
        self.seq_ctrl.seq_dial.active = self.i  # Aktualizacja kontrolki (kolory prostokącików)

    def num_change(self):
        """Zmiana aktywnej sekwencji."""
        self.i = 0  # Przejście do pierwszej mapy z sekwencji
        seqbtns = self.findChildren(MoekSeqButton)  # Referencje do przycisków sekwencji
        # Aktualizacja wyglądu przycisków:
        for seqbtn in seqbtns:
            seqbtn.active = True if seqbtn.num == self.num else False
        self.seq_ctrl.setEnabled(False) if self.num == 0 else self.seq_ctrl.setEnabled(True)
        self.player_reset()

    def change_map(self):
        """Zmiana podkładu mapowego."""
        map_id = self.sqb_btns["sqb_" + str(self.num)].maps[self.i][0]
        dlg.p_map.map = map_id

    def player(self):
        """Odtwarzanie sekwencyjnego wczytywania podkładów mapowych."""
        # print(f"[player]")
        if self.num == 0:
            # Brak aktywnej sekwencji
            self.player_reset()
            return
        # Przerwanie poprzedniego sekwencyjnego wczytywania, jeśli jeszcze trwa:
        if self.timer:
            self.timer.stop()
            self.timer = None
        try:
            self.sqb_btns["sqb_" + str(self.num)].progbar.value = 0
        except Exception as err:
            print(f"player: {err}")
        vn_zoom(player=True)  # Przybliżenie widoku mapy do nowego vn'a
        # print(f'seq_ge: {self.sqb_btns["sqb_" + str(self.num)].ge}, is_ge: {dlg.ge.is_ge}')
        # if self.sqb_btns["sqb_" + str(self.num)].ge:  # W sekwencji jest Google Earth Pro
        #     print(f"+++++++++++++++++++++++++  1  +++++++++++++++++++++++++++++")
        #     dlg.ge.q2ge(player=True, back=True)
        # elif dlg.ge.is_ge:  # Google Earth Pro jest włączony
        #     print(f"+++++++++++++++++++++++++  2  +++++++++++++++++++++++++++++")
        #     dlg.ge.q2ge(player=True, back=True)
        self.i = 0  # Przejście do pierwszego podkładu mapowego z sekwencji
        delay = self.sqb_btns["sqb_" + str(self.num)].maps[self.i][1]  # Pobranie opóźnienia
        self.set_timer(delay)  # Uruchomienie stopera

    def set_timer(self, period):
        """Ustawienie i odpalenie funkcji odmierzającej czas."""
        # print(f"[set_timer]")
        self.period = period  # Całkowity czas
        self.tick = period / 10  # Interwał odświeżania progressbar'a
        self.tack = 0  # Wartość dla progressbar'a
        self.lasted = 0.0  # Czas, który już minął
        dlg.ge.player = True  # Przekazanie do GESync informacji o aktywacji player'a
        # Stworzenie stopera i jego odpalenie:
        self.timer = QTimer(self, interval=self.tick * 1000)
        self.timer.timeout.connect(self.run_timer)
        self.timer.start()  # Odpalenie stopera

    def run_timer(self):
        """Funkcja odmierzająca czas."""
        # print(f"[run_timer]")
        if self.num == 0:
            # Brak aktywnej sekwencji
            self.player_reset()
            return
        self.lasted += self.tick
        self.tack += 1
        # Odświeżenie progressbar'a:
        try:
            self.sqb_btns["sqb_" + str(self.num)].progbar.value = self.tack
        except:
            self.player_reset()
            return
        if self.lasted >= self.period:  # Czas dobiegł końca
            if self.timer:
                # Kasowanie licznika:
                self.timer.stop()
                self.timer = None
            dlg.ge.player = False  # Przekazanie do GESync informacji o wyłączeniu player'a
            self.sqb_btns["sqb_" + str(self.num)].progbar.value = 0
            if self.i < len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1:
                self.next_map(player=True)  # Wczytanie kolejnego podkładu

    def prev_map(self):
        """Wczytanie poprzedniego podkładu mapowego z sekwencji."""
        if self.i > 0:  # Można się jeszcze cofnąć w sekwencji
            self.i -= 1  # Przejście do poprzedniego podkładu mapowego
        else:  # Przejście do ostatniego podkładu mapowego z aktywnej sekwencji
            self.i = len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1

    def next_map(self, player=False):
        """Wczytanie kolejnego podkładu mapowego z sekwencji."""
        if self.i < len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1:  # Pozostał jeszcze conajmniej jeden podkład do wczytania
            self.i += 1  # Przejście do następnego podkładu mapowego
            # Odpalenie stopera, jeśli uruchomiony jest player:
            if player and self.i < len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1:
                delay = self.sqb_btns["sqb_" + str(self.num)].maps[self.i][1]
                self.set_timer(delay)  # Odpalenie stopera
        else:  # Powrót do początku sekwencji
            self.i = 0

    def player_reset(self):
        """Powrót do wartości zerowych progbar'ów na wypadek zawieszenia player'a."""
        for i in range(1, 4):
            self.sqb_btns["sqb_" + str(i)].progbar.value = 0
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.period = 0  # Całkowity czas
        self.lasted = 0  # Upłynięty czas
        self.tick = 0  # Interwał odświeżania progressbar'a
        self.tack = 0  # Wartość dla progressbar'a


class MoekSeqAddBox(QFrame):
    """Pojemnik na wiget'y używane do dodawania podkładów mapowych do sekwencji."""
    def __init__(self, *args, id):
        super().__init__(*args)
        self.id = id
        self.setFixedHeight(34)
        self.setObjectName("main")
        self.combobox = CanvasComboBox(self)
        self.add_btn = MoekButton(self, name="add", size=26)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(4, 4, 4, 4)
        self.hlay.setSpacing(4)
        self.hlay.addWidget(self.combobox, 10)
        self.hlay.addWidget(self.add_btn, 1)
        self.setLayout(self.hlay)
        self.maps = []
        self.add_btn.clicked.connect(self.add_basemap)
        self.setStyleSheet("""
                        QFrame#main {background-color: rgba(55, 55, 55, 0.8); border: none}
                        """)

    def combobox_update(self, _id):
        """Aktualizacja combobox'a o listę dostępnych i jeszcze nieaktywnych podkładów mapowych."""
        # print(f"combobox_update: {_id}")
        scg = dlg.seq_dock.widgets["scg_seq" + str(_id)].findChildren(MoekSeqCfg)  # Referencje seqcfg'ów
        # Lista wszystkich włączonych podkładów mapowych:
        maps = [map["id"] for map in dlg.p_map.all if map["enabled"]]
        # Lista numerów podkładów, które już są dodane do sekwencji:
        scg_maps = [s.map for s in scg]
        # Lista numerów podkładów, które powinny znaleźć się w combobox'ie:
        avail_maps = list(set(maps) - set(scg_maps))
        # Lista z danymi do zasilenia combobox'a:
        cmb_list = [[map["id"], map["name"]] for map in dlg.p_map.all if map["id"] in avail_maps]
        self.combobox.clear()
        # Populacja combobox'a:
        for m in cmb_list:
            self.combobox.addItem("   " + m[1], m[0])

    def add_basemap(self):
        """Dodanie wybranego w combobox'ie podkładu mapowego do pojemnika ustawień sekwencji."""
        map_id = self.combobox.currentData(Qt.UserRole)
        scb = dlg.seq_dock.widgets["scg_seq" + str(self.id)]  # Referencja seqcfgbox'a
        sid = scb.cnt  # Numer seqcfg'a, który będzie populowany
        scg = scb.scgs["scg_" + str(sid)]  # Referencja seqcfg'a
        scg.spinbox.value = 1  # Ustalenie opóźnienia nowoaktywowanego seqcfg'a
        scg.map = map_id  # Ustalenie mapy dla nowoaktywowanego seqcfg'a
        scb.cnt += 1  # Dodanie do aktywnych jednego seqcfg'a z puli seqcfbox'a
        # Wczytanie danych do przycisku sekwencji:
        dlg.seq_dock.widgets["sqb_seq"].sqb_btns["sqb_" + str(self.id)].maps.append([scg.map, scg.spinbox.value])


class MoekSeqCfgBox(QFrame):
    """Pojemnik na wybrane podkłady mapowe w trybie ustawień sekwencji."""
    cnt_changed = pyqtSignal(int)

    def __init__(self, *args, _id):
        super().__init__(*args)
        self.id = _id
        self.vlay = QVBoxLayout()
        self.vlay.setContentsMargins(0, 0, 0, 0)
        self.vlay.setSpacing(0)
        self.scgs = {}
        for c in range(5):
            _scg = MoekSeqCfg(self, _id=c)
            self.vlay.addWidget(_scg)
            scg_name = f'scg_{c}'
            self.scgs[scg_name] = _scg
        self.setLayout(self.vlay)
        self.cnt = int()
        self.cnt_changed.connect(self.cnt_change)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cnt":
            self.cnt_changed.emit(val)

    def cnt_change(self):
        """Zmiana ilości aktywnych seqcfg'ów w seqcfgbox'ie."""
        # Ustalenie wysokości seq_dock w zależności od ilości widocznych seqcfg'ów:
        height = 76 + 36 * self.cnt
        dlg.seq_dock.heights[self.id] = height
        dlg.seq_dock.height_change()
        c = 0
        for scg in self.scgs:
            # Wyświetlenie odpowiedniej liczby seqcfg'ów:
            self.scgs["scg_" + str(c)].setVisible(True) if c < self.cnt else self.scgs["scg_" + str(c)].setVisible(False)
            # Ustawienie atrybutu last na ostatnim aktywnym seqcfg'u:
            if c == self.cnt - 1:
                self.scgs["scg_" + str(c)].last = True
            else:
                self.scgs["scg_" + str(c)].last = False
            c += 1
        sab = dlg.seq_dock.widgets["sab_seq" + str(self.id)]  # Referencja seqaddbox'a
        sab.combobox_update(self.id)  # Aktualizacja combobox'a
        # Uniemożliwienie dodania do sekwencji więcej niż 5 podkładów mapowych:
        sab.add_btn.setEnabled(False) if self.cnt == 5 else sab.add_btn.setEnabled(True)


class MoekSeqCtrlButton(QFrame):
    """Przycisk-kontrolka sterujący sekwencją podkładów mapowych."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setFixedSize(60, 60)
        self.seq_dial = MoekSeqDial(self)
        self.seq_prev = MoekButton(self, size=30, hsize=60, name="seq_prev")
        self.seq_next = MoekButton(self, size=30, hsize=60, name="seq_next")
        self.seq_dial.setGeometry(0, 0, 60, 60)
        self.seq_prev.setGeometry(0, 0, 30, 60)
        self.seq_next.setGeometry(30, 0, 30, 60)
        self.seq_prev.clicked.connect(self.prev_clicked)
        self.seq_next.clicked.connect(self.next_clicked)

    def changeEvent(self, event):
        """Ustawienie widoczności wskaźników kontrolki (kolorowe prostokąciki) w zależności od stanu przycisku."""
        self.seq_dial.setVisible(True) if self.isEnabled() else self.seq_dial.setVisible(False)

    def prev_clicked(self):
        """Naciśnięcie przycisku przejścia do następnego podkładu w sekwencji."""
        self.parent().prev_map()

    def next_clicked(self):
        """Naciśnięcie przycisku przejścia do poprzedniego podkładu w sekwencji."""
        self.parent().next_map()


class MoekSeqButton(QFrame):
    """Przycisk obsługujący sekwencyjne wczytywanie podkładów mapowych."""
    empty_changed = pyqtSignal()
    activated = pyqtSignal(bool)

    def __init__(self, *args, num):
        super().__init__(*args)
        self.num = num
        self.empty = None
        self.setFixedSize(50, 50)
        self.progbar = MoekSeqProgressBar(self)
        self.progbar.setGeometry(0, 0, 50, 50)
        self.button = MoekButton(self, name="seq" + str(num), size=25, checkable=True)
        self.button.setFixedSize(25, 25)
        self.button.setGeometry(12.5, 12.5, 25, 25)
        self.button.clicked.connect(self.btn_clicked)
        self.cfg_btn = MoekButton(self, name="seq_cfg", icon="seqcfg", size=17, checkable=False)
        self.cfg_btn.setFixedSize(17, 17)
        self.cfg_btn.setGeometry(12, 29, 17, 17)
        self.maps = []
        self.ge = False
        self.empty_changed.connect(self.empty_change)
        self.activated.connect(self.active_change)
        self.cfg_btn.clicked.connect(self.cfg_clicked)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "empty":
            self.empty_changed.emit()
        elif attr == "active":
            self.activated.emit(val)

    def active_change(self, value):
        """Zmiana trybu active."""
        self.progbar.active = True if value else False
        self.button.setChecked(True) if value else self.button.setChecked(False)
        if value:
            # Aktualizacja ilości wskaźników na kontrolce (prostokącików):
            self.parent().seq_ctrl.seq_dial.all = len(self.maps)
        if self.empty:
            self.button.set_icon("seq_empty")
            self.cfg_btn.set_icon("seqcfg")
        else:
            self.button.set_icon("seq" + str(self.num))
            self.cfg_btn.set_icon("seqcfg1") if value else self.cfg_btn.set_icon("seqcfg0")

    def empty_change(self):
        # print(f"empty_change: {self.empty}")
        """Zmiana wypełnienia sekwencji (są lub nie ma podkładów)."""
        self.set_style(False) if self.empty else self.set_style(True)

    def set_style(self, value):
        """Modyfikacja stylu przycisku przy zmianie atrybutu empty."""
        self.button.set_icon("seq" + str(self.num)) if value else self.button.set_icon("seq_empty")
        if value:
            self.cfg_btn.setEnabled(True)
            self.cfg_btn.set_icon("seqcfg1") if self.active else self.cfg_btn.set_icon("seqcfg0")
        else:
            self.cfg_btn.setEnabled(False)

    def btn_clicked(self):
        """Zmiana kategorii map po wciśnięciu przycisku lub wejście do ustawień, jeśli sekwencja jest pusta."""
        if self.button.isChecked():
            if self.empty:
                self.button.setChecked(False)
                self.cfg_clicked()  # Wejście do ustawień sekwencji
            else:
                self.parent().num = self.num  # Aktywacja sekwencji
        else:
            self.parent().num = 0  # Deaktywacja sekwencji

    def cfg_clicked(self):
        """Wejście do trybu ustawień sekwencji."""
        dlg.seq_dock.widgets["sqb_seq"].enter_setup(self.num)

class MoekSeqDial(QWidget):
    """Wskaźnik kolejności i ilości podkładów mapowych w sekwencji."""
    active_changed = pyqtSignal(int)
    all_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.setFixedSize(60, 60)
        self.active_changed.connect(self.dial_change)
        self.all_changed.connect(self.dial_change)
        self.active = 0
        self.all = 0
        self.modified = False
        self.pixmap = QPixmap()
        self.r = [
                    [
                    [24, 4], [32, 4]
                    ],
                    [
                    [21, 4], [28, 4], [35, 4]
                    ],
                    [
                    [21, 3], [26, 3], [31, 3], [36, 3]
                    ],
                    [
                    [21, 2], [25, 2], [29, 2], [33, 2], [37, 2]
                    ]
                ]

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.active_changed.emit(val)
        elif attr == "all":
            self.all_changed.emit(val)

    def dial_change(self):
        """Zmiana trybu active."""
        self.modified = True
        self.update()

    def paintEvent(self, e):
        """Funkcja rysująca."""
        if self.modified:
            _pixmap = QPixmap(self.size())
            _pixmap.fill(Qt.transparent)
            painter = QPainter(_pixmap)
            brush = QBrush()
            brush.setColor(QColor(255, 255, 255, 128))
            brush.setStyle(Qt.SolidPattern)
            for r in range(self.all):
                _list = self.r[self.all - 2][r]
                _rect = QRect(_list[0], 24, _list[1], 12)
                painter.fillRect(_rect, brush)
            brush.setColor(QColor(255, 192, 0, 255))
            _list = self.r[self.all - 2][self.active]
            _rect = QRect(_list[0], 24, _list[1], 12)
            painter.fillRect(_rect, brush)
            self.pixmap = _pixmap
            self.modified = False
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap)


class MoekSeqProgressBar(QWidget):
    """Wskaźnik upływu czasu przy zmianie mapy podczas sekwencyjnego wczytywania podkładów mapowych."""
    activated = pyqtSignal(bool)
    value_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.setFixedSize(50, 50)
        self.value = 0
        self.min_value = 0
        self.max_value = 10
        self.start_angle = 26
        self.end_angle = 26
        self.arcWidth = 5
        self.bg_color = QColor()
        self.pg_color = QColor()
        self.activated.connect(self.active_change)
        self.value_changed.connect(self.repaint)
        self.active = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.activated.emit(val)
        elif attr == "value":
            self.value_changed.emit(val)

    def active_change(self, value):
        """Zmiana trybu active."""
        self.bg_color = QColor(255, 192, 0, 77) if value else QColor(255, 255, 255, 77)
        self.pg_color = QColor(255, 192, 0) if value else QColor(255, 255, 255)
        self.repaint()

    def paintEvent(self, e):
        """Funkcja rysująca."""
        width = self.width()
        height = self.height()

        painter = QPainter()
        painter.begin(self)
        painter.translate(width/2-0.5, height/2-0.5)
        radius = 22 - self.arcWidth
        painter.setBrush(Qt.NoBrush)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(self.arcWidth)
        pen.setCapStyle(Qt.RoundCap)
        pen.setColor(self.bg_color)

        angle_all = 360.0 - self.start_angle - self.end_angle
        angle_current = angle_all * ((self.value - self.min_value) / (self.max_value - self.min_value))
        angle_other = angle_all - angle_current
        rect = QRect(-radius, -radius, radius * 2, radius * 2)

        painter.setPen(pen)
        painter.drawArc(rect, (270 - self.start_angle - angle_current - angle_other) * 16, angle_all * 16)
        pen.setColor(self.pg_color)
        painter.setPen(pen)
        painter.drawArc(rect, (270 - self.start_angle - angle_current) * 16, angle_current * 16)
        painter.setBrush(self.bg_color) if self.parent().empty else painter.setBrush(self.pg_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse (-3, 14, 6, 6)
        painter.end()


class MoekSeqCfg(QFrame):
    """Obiekt listy wybranych podkładów mapowych w trybie ustawień sekwencji."""
    map_changed = pyqtSignal()
    last_changed = pyqtSignal()

    def __init__(self, *args, _id):
        super().__init__(*args)
        self.id = _id
        self.setObjectName("box")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setFixedHeight(36)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(3, 0, 5, 0)
        self.hlay.setSpacing(4)
        self.order = MoekOrder(self)
        self.label = MoekSeqLabel(self)
        self.label.setObjectName("lbl")
        self.spinbox = MoekSeqSpinBox(self)
        self.del_btn = MoekButton(self, name="del", size=24)
        self.hlay.addWidget(self.order)
        self.hlay.addWidget(self.label)
        self.hlay.addWidget(self.spinbox)
        self.hlay.addWidget(self.del_btn)
        self.setLayout(self.hlay)
        self.map = int()
        self.last = False
        self.del_btn.clicked.connect(self.del_clicked)
        self.map_changed.connect(self.map_change)
        self.last_changed.connect(self.last_change)
        self.setStyleSheet("""
                               QFrame#box {background-color: rgba(55, 55, 55, 0.8); border: none}
                               QFrame#lbl {color: rgb(255, 255, 255); qproperty-alignment: AlignCenter}
                               """)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "map":
            self.map_changed.emit()
        elif attr == "last":
            self.last_changed.emit()

    def resizeEvent(self, e):
        """Zmiana szerokości seqcfg'a - aktualizacja labela w seqcfg'u."""
        super().resizeEvent(e)
        self.findChildren(MoekSeqLabel)[0].label_update()

    def map_change(self):
        """Zmiana mapy w seqcfg'u."""
        for map in dlg.p_map.all:
            if map["id"] == self.map:
                self.label.setText(map["name"])

    def del_clicked(self):
        """Wyczyszczenie wybranego seqcfg'u."""
        seqcfgs = []  # Lista z danymi z pozostałych po kasowaniu seqcfg'ów
        # Zapamiętanie danych z pozostałych po kasowaniu seqcfg'ów:
        for scg in self.parent().findChildren(MoekSeqCfg):
            if scg.id != self.id:
                seqcfgs.append([scg.map, scg.spinbox.value])
        # Czyszczenie wszystkich seqcfg'ów:
        for scg in self.parent().findChildren(MoekSeqCfg):
            scg.map, scg.spinbox.value = 0, 0
        # Wczytanie danych do nowych seqcfg'ów:
        for i in range(self.parent().cnt - 1):
            self.parent().scgs["scg_" + str(i)].spinbox.value = seqcfgs[i][1]
            self.parent().scgs["scg_" + str(i)].map = seqcfgs[i][0]
        self.parent().cnt -= 1  # Aktualizacja ilości aktywnych seqcfg'ów

    def last_change(self):
        """Dostosowanie przycisków zmiany kolejności."""
        self.order.way = "up" if self.last else "both"
        if self.id == 0 and self.parent().cnt > 1:
            self.order.way = "down"
        elif self.id == 0 and self.parent().cnt <= 1:
            self.order.way = "none"


class MoekOrder(QFrame):
    """Przycisk-kontrolka wiget'u obsługującego sekwencyjne wczytywanie podkładów mapowych."""
    way_changed = pyqtSignal(str)

    def __init__(self, *args, way="both"):
        super().__init__(*args)
        self.setFixedSize(24, 24)
        self.up_btn = MoekButton(self, name="order_up", size=24, hsize=12)
        self.down_btn = MoekButton(self, name="order_down", size=24, hsize=12)
        self.up_btn.setGeometry(0, 1, 24, 12)
        self.down_btn.setGeometry(0, 12, 24, 12)
        self.way_changed.connect(self.way_change)
        self.way = way
        self.up_btn.clicked.connect(lambda: self.order_change(way="up"))
        self.down_btn.clicked.connect(lambda: self.order_change(way="down"))

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "way":
            self.way_changed.emit(val)

    def way_change(self):
        """Działanie przycisków góra/dół w zależności od atrybutu way."""
        if self.way == "both":
            self.up_btn.setEnabled(True)
            self.down_btn.setEnabled(True)
        elif self.way == "up":
            self.up_btn.setEnabled(True)
            self.down_btn.setEnabled(False)
        elif self.way == "down":
            self.up_btn.setEnabled(False)
            self.down_btn.setEnabled(True)
        elif self.way == "none":
            self.up_btn.setEnabled(False)
            self.down_btn.setEnabled(False)

    def order_change(self, way):
        """Zamiana kolejności dwóch sąsiadujących seqcfg'ów."""
        bid = self.parent().parent().id
        id_1 = self.parent().id
        id_2 = id_1 - 1 if way == "up" else id_1 + 1
        map_1 = dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].map
        delay_1 = dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].spinbox.value
        map_2 = dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].map
        delay_2 = dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].spinbox.value
        dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].spinbox.value = delay_2
        dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].spinbox.value = delay_1
        dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].map = map_2
        dlg.seq_dock.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].map = map_1


class MoekSeqSpinBox(QFrame):
    """Widget z centralnie umieszczonym labelem i przyciskami zmiany po jego obu stronach + przycisk konfiguracyjny."""
    value_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("frm")
        self.setFixedSize(26, 25)
        self.label = QLabel(self)
        self.label.setObjectName("lbl")
        self.label.setGeometry(2, -1, 12, 25)
        self.spinner = MoekSpinner(self)
        self.spinner.setGeometry(13, 1, 12, 25)
        self.set_style(True)
        self.min = 1
        self.max = 9
        self.value_changed.connect(self.value_change)
        self.value = 1

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "value":
            self.value_changed.emit(val)

    def setEnabled(self, value):
        super().setEnabled(value)
        self.label.setVisible(value)
        self.spinner.setVisible(value)
        self.set_style(value)

    def set_style(self, value):
        """Modyfikacja stylesheet przy zmianie setEnabled."""
        if value:
            self.setStyleSheet("""
                    QFrame#frm {border: none; border-radius: 0px}
                    QFrame#lbl {color: rgb(255, 255, 255); font-size: 10pt; font-weight: normal; qproperty-alignment: AlignCenter}
                    """)
        else:
            self.setStyleSheet("""
                    QFrame#frm {border: none; border-radius: 0px}
                    """)

    def value_change(self):
        """Zmiana wartości spinbox'a."""
        self.spinner.down_btn.setEnabled(False) if self.value == self.min else self.spinner.down_btn.setEnabled(True)
        self.spinner.up_btn.setEnabled(False) if self.value == self.max else self.spinner.up_btn.setEnabled(True)
        self.label.setText(str(self.value))


class MoekSpinner(QFrame):
    """Przycisk-kontrolka wiget'u obsługującego sekwencyjne wczytywanie podkładów mapowych."""
    def __init__(self, *args, size="S"):
        super().__init__(*args)
        self.setFixedSize(12, 24)
        self.up_btn = MoekButton(self, name="up" + size, size=12)
        self.down_btn = MoekButton(self, name="down" + size, size=12)
        self.vlay = QVBoxLayout()
        self.vlay.setContentsMargins(0, 0, 0, 0)
        self.vlay.setSpacing(0)
        self.vlay.addWidget(self.up_btn)
        self.vlay.addWidget(self.down_btn)
        self.setLayout(self.vlay)
        self.up_btn.clicked.connect(self.up_clicked)
        self.down_btn.clicked.connect(self.down_clicked)

    def up_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk prev_btn."""
        self.parent().value += 1

    def down_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk next_bnt."""
        self.parent().value -= 1


class MoekSeqLabel(QLabel):
    """Fabryka napisów."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(25)
        self.setWordWrap(True)
        self.contract()

    def contract(self):
        """Skrócenie szerokości label'u przed pojawieniem się przycisków."""
        self.setFixedWidth(self.width() - 92)

    def setText(self, text):
        """Aktualizacja po zmianie tekstu."""
        super().setText(text)
        self.label_update()

    def label_update(self):
        """Aktualizacja labela po modyfikacji seqbox'a."""
        lbl_width = self.label_width()
        self.setFixedWidth(lbl_width)
        self.font_resize(lbl_width)

    def label_width(self):
        """Zwraca dostępną szerokość dla label'u."""
        btns_width = 92
        spb_width = self.parent().width()
        if spb_width == 640:  # Szerokość bazowa przy tworzeniu widget'u
            spb_width = 196  # Formatowanie do minimalnej szerokości
        # Ustalenie szerokości label'u:
        return spb_width - btns_width

    def font_resize(self, l_w):
        """Zmniejszenie rozmiaru czcionki, jeśli napis się nie mieści."""
        f_size = 9
        marg = 2
        f = QFont("Segoe UI", f_size)
        f.setPointSize(f_size)
        self.setFont(f)
        f_w = self.fontMetrics().boundingRect(self.text()).width() + marg
        while l_w < f_w:
            f_size -= 1
            f.setPointSize(f_size)
            self.setFont(f)
            f_w = self.fontMetrics().boundingRect(self.text()).width() + marg
            if f_size == 6:  # Ograniczenie zmniejszenia czcionki
                return


class WyrIdTableView(QTableView):
    """Widget obsługujący listę numerów id wyrobisk."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(100)
        self.setStyleSheet("""
                            QTableView {
                                selection-background-color: transparent;
                                background-color: rgba(200, 200, 200, 0.71);
                            }
                            QScrollBar:vertical {
                                border: 0px solid #999999;
                                background: transparent;
                                width: 14px;
                                margin: 4px 3px 4px 3px;
                            }
                            QScrollBar::handle:vertical {
                                min-height: 60px;
                                border: 0px solid red;
                                border-radius: 4px;
                                background-color: rgba(55, 55, 55, 0.6);
                            }
                            QScrollBar::add-line:vertical {
                                height: 0px;
                                subcontrol-position: bottom;
                                subcontrol-origin: margin;
                            }
                            QScrollBar::sub-line:vertical {
                                height: 0 px;
                                subcontrol-position: top;
                                subcontrol-origin: margin;
                            }
                        """)
        self.setShowGrid(False)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)


class MoekGridBox(QFrame):
    """Zawartość panelu w kompozycji QGridLayout."""
    def __init__(self, *args, margins=[4, 2, 4, 4], spacing=0):
        super().__init__(*args)
        self.setObjectName("gbox")
        self.setStyleSheet("""
                    QFrame#gbox{background-color: transparent; border: none}
                    """)
        self.glay = QGridLayout()
        self.glay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.glay.setSpacing(spacing)
        self.setLayout(self.glay)


class CanvasGridBox(QFrame):
    """Zawartość panelu z wertykalnym spacer'em."""
    def __init__(self, *args, height=None, margins=[4, 2, 4, 4], spacing=0):
        super().__init__(*args)
        self.setObjectName("box")
        if height:
            self.setFixedHeight(height)
        self.setStyleSheet("""
                    QFrame#box{background-color: transparent; border: none}
                    """)
        self.vlay = QVBoxLayout()
        self.vlay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.vlay.setSpacing(spacing)
        self.glay = MoekGridBox(self, margins=[0, 0, 0, 0], spacing=0)
        self.vlay.addWidget(self.glay)
        spacer = QSpacerItem(1, 1, QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.vlay.addItem(spacer)
        self.setLayout(self.vlay)


class MoekHBox(QFrame):
    """Zawartość panelu w kompozycji QHBoxLayout."""
    def __init__(self, *args, margins=[0, 0, 0, 0], spacing=0, color="55, 55, 55", alpha=0.0):
        super().__init__(*args)
        self.setObjectName("main")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(""" + color + """, """ + str(alpha) + """); border: none}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.lay.setSpacing(spacing)
        self.setLayout(self.lay)


class MoekVBox(QFrame):
    """Zawartość toolbox'a w kompozycji QVBoxLayout."""
    def __init__(self, *args, margins=[0, 0, 0, 0], spacing=0, color="55, 55, 55", alpha=0.0):
        super().__init__(*args)
        self.setObjectName("main")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(""" + color + """, """ + str(alpha) + """); border: none}
                    """)
        self.lay = QVBoxLayout()
        self.lay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.lay.setSpacing(spacing)
        self.setLayout(self.lay)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        widgets = (self.lay.itemAt(i).widget() for i in range(self.lay.count()))
        for widget in widgets:
            if isinstance(widget, (MoekButton, QProgressBar)):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)


class MoekStackedBox(QStackedWidget):
    """Widget dzielący zawartość panelu na strony."""
    def __init__(self, *args):
        super().__init__(*args)

    def minimumSizeHint(self):
        self.setMinimumHeight(self.currentWidget().minimumSizeHint().height())
        self.setMaximumHeight(self.currentWidget().minimumSizeHint().height())
        return self.currentWidget().minimumSizeHint()


class CanvasStackedBox(QStackedWidget):
    """Widget dzielący zawartość panelu na strony."""
    def __init__(self, *args, color="55, 55, 55", alpha=0.0):
        super().__init__(*args)
        self.setStyleSheet("""QStackedWidget {
                                background-color: rgba(""" + str(color) + """, """ + str(alpha) + """);
                                border: none;
                            }"""
                            )

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        widgets = (self.widget(i) for i in range(self.count()))
        for widget in widgets:
            if isinstance(widget, (MoekButton, QProgressBar)):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)

class MoekButton(QToolButton):
    """Fabryka guzików."""
    def __init__(self, *args, size=25, hsize=0, name="", icon="", visible=True, enabled=True, checkable=False, tooltip="", tooltip_on=None):
        super().__init__(*args)
        name = icon if len(icon) > 0 else name
        self.name = name
        self.shown = visible  # Dubluje setVisible() - .isVisible() może zależeć od rodzica
        self.setVisible(visible)
        self.setEnabled(enabled)
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.tooltip_on = tooltip_on
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setAutoRaise(True)
        self.setStyleSheet("""
                            QToolButton {
                                border: none;
                            }
                            QToolTip {
                                border: 1px solid rgb(50, 50, 50);
                                padding: 5px;
                                background-color: rgb(30, 30, 30);
                                color: rgb(200, 200, 200);
                            }
                        """)
        self.set_icon(name, size, hsize)
        self.setMouseTracking(True)
        self.setCursor(Qt.ArrowCursor)
        if self.tooltip_on:
            self.tooltip = tooltip
            self.toggled.connect(self.toggle)

    def toggle(self, checked):
        """Aktualizacja tooltip'u po zmianie stanu przycisku."""
        self.setToolTip(self.tooltip_on) if checked else self.setToolTip(self.tooltip)

    def set_tooltip(self, txt):
        """Ustawienie tooltip'a."""
        self.setToolTip(txt)

    def set_icon(self, name, size=25, hsize=0):
        """Ładowanie ikon do guzika."""
        if hsize == 0:
            wsize, hsize = size, size
        else:
            wsize = size
        self.setFixedSize(wsize, hsize)
        self.setIconSize(QSize(wsize, hsize))
        icon = QIcon()
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(wsize, hsize), mode=QIcon.Normal, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0_act.png", size=QSize(wsize, hsize), mode=QIcon.Active, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(wsize, hsize), mode=QIcon.Selected, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_dis.png", size=QSize(wsize, hsize), mode=QIcon.Disabled, state=QIcon.Off)
        if self.isCheckable():
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(wsize, hsize), mode=QIcon.Normal, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1_act.png", size=QSize(wsize, hsize), mode=QIcon.Active, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(wsize, hsize), mode=QIcon.Selected, state=QIcon.On)
        self.setIcon(icon)


class MoekSlideButton(MoekButton):
    """Guzik wysuwający się przy hoveringu."""
    def __init__(self, *args, size=25, hsize=0, name="", icon="", visible=True, enabled=True, checkable=False, tooltip=""):
        super().__init__(*args, size=size, hsize=hsize, name=name, icon=icon, visible=visible, enabled=enabled, checkable=checkable, tooltip=tooltip)
        self.slided = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "slided":
            self.sliding()

    def sliding(self, deactivate=False):
        offset = 18 if self.slided or (self.isChecked() and not deactivate) else 0
        self.setGeometry(self.parent().width() - 6 - offset, (self.parent().height()/2) - (self.height()/2), self.width(), self.height())

    def enterEvent(self, event):
        if self.parent().parent().parent().is_enabled:
            self.slided = True

    def leaveEvent(self, event):
        self.slided = False


class MoekDummy(QFrame):
    """Pusty obiekt zajmujący określoną przestrzeń."""
    def __init__(self, *args, width, height, color=None, spacer=None):
        super().__init__(*args)
        self.setObjectName("main")
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        if not spacer:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.setFixedSize(width, height)
        else:
            if spacer == "horizontal":
                w, h = QSizePolicy.Expanding, QSizePolicy.Fixed
                self.setFixedHeight(height)
            else:
                w, h = QSizePolicy.Fixed, QSizePolicy.Expanding
                self.setFixedWidth(width)
            self.setSizePolicy(w, h)
            self.spacer = QSpacerItem(1, 1, w, h)
            self.lay.addItem(self.spacer)
        b_color = color if color else "transparent"
        self.setStyleSheet("""
                    QFrame#main{background-color: """ + str(b_color) + """; border: none}
                    """)


class MoekPointer(QWidget):
    """Trójkątna strzałka wyświetlana w tle innego widget'a."""

    def __init__(self, *args):
        super().__init__(*args)
        self.setFixedSize(12, 6)
        self.pixmap = QPixmap()

    def paintEvent(self, e):
        """Funkcja rysująca."""
        _pixmap = QPixmap(self.size())
        _pixmap.fill(QColor(0,0,0,0))
        painter = QPainter(_pixmap)
        path = QPainterPath()
        path.moveTo(0,6)
        path.lineTo(12,6)
        path.lineTo(6,0)
        path.lineTo(5,0)
        path.closeSubpath()
        painter.fillPath(path, QColor(20, 20, 20, 204))
        self.pixmap = _pixmap
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap)


class MoekComboBox(QComboBox):
    """Fabryka rozwijanych."""
    def __init__(self, *args, name="", height=25, border=2, b_round="none"):
        super().__init__(*args)
        if b_round == "right":
            B_CSS = "border-top-right-radius: 3px; border-bottom-right-radius: 3px;"
        elif b_round == "all":
            B_CSS = "border-radius: 6px;"
        else:
            B_CSS = ""
        self.setMaxVisibleItems(20)
        model = QStandardItemModel()
        self.setModel(model)
        de = CmbDelegate(self)
        self.view().setItemDelegate(de)
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("""
                    QComboBox {
                        border: """ + str(border) + """px solid rgb(52, 132, 240);
                        """ + B_CSS + """
                        padding: 0px 5px 0px 5px;
                        min-width: 1px;
                        min-height: """ + str(height) + """px;
                        color: rgb(52, 132, 240);
                        font-size: 8pt;
                        combobox-popup: 0;
                    }
                    QComboBox:disabled {
                        """ + B_CSS + """
                        border: """ + str(border) + """px solid rgb(140, 140, 140);
                        padding: 0px 5px 0px 5px;
                        min-width: 1px;
                        min-height: """ + str(height) + """px;
                        color: rgb(140, 140, 140);
                        font-size: 8pt;
                    }
                    QComboBox::indicator {
                        background-color:transparent;
                        selection-background-color:transparent;
                        color:transparent;
                        selection-color:transparent;
                    }
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: center right;
                        width: 12px;
                        right: 5px;
                        border: none;
                        background: transparent;
                    }
                    QComboBox::down-arrow {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """down_arrow.png');
                    }
                    QComboBox::down-arrow:disabled {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """down_arrow_dis.png');
                    }
                    QComboBox QAbstractItemView {
                        border: """ + str(border) + """px solid rgb(52, 132, 240);
                        outline: none;
                        background-color: white;
                    }
                    """)
        self.view().window().setStyleSheet("""
                        QListView::item{
                            border: none;
                            padding-left: 5px;
                            min-width: 300px;
                            margin: 0px;
                            height: 24px;
                            color: rgb(52, 132, 240);
                            background-color: white;
                            show-decoration-selected: 0;
                            font-size: 8pt;
                        }
                        QListView::item:selected {
                            color: white;
                            background-color: rgb(52, 132, 240);
                        }
                        QListView::item:!selected {
                            background-color: white;
                            color: rgb(52, 132, 240);
                        }
                    """)


class CanvasArrowlessComboBox(QComboBox):
    """Fabryka rozwijanych bez strzałki."""
    def __init__(self, *args, name="", width=200, height=24, border=1, font_size=8, icon_disable=False, b_round="none", tv=False, val_display=False, trigger=None, fn=None):
        super().__init__(*args)
        if b_round == "right":
            B_CSS = "border-top-right-radius: 3px; border-bottom-right-radius: 3px;"
        elif b_round == "all":
            B_CSS = "border-radius: 6px;"
        else:
            B_CSS = ""
        self.setFixedHeight(height)
        self.cur_val = None
        self.val_display = val_display
        self.trigger = trigger
        self.fn = fn
        # if tv:
        popup = 0
        self.setMaxVisibleItems(20)
        model = QStandardItemModel()
        self.setModel(model)
        de = CmbDelegate(self)
        self.view().setItemDelegate(de)
        self.view().setFixedWidth(width)
        # else:
        #     popup = 1
        self.setStyleSheet("""
                            QComboBox {
                                """ + B_CSS + """
                                padding: 0px 5px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                color: white;
                                background-color: rgba(255, 255, 255, 0.2);
                                font-size: """ + str(font_size) + """pt;
                                combobox-popup: """ + str(popup) + """;
                            }
                            QComboBox:disabled {
                                """ + B_CSS + """
                                padding: 0px 0px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                color: rgb(140, 140, 140);
                                font-size: """ + str(font_size) + """pt;
                            }
                            QComboBox::item:selected {
                                min-height: 34px;
                                padding-left: 0px;
                                background-color: rgba(255, 255, 255, 0.4);
                                color: black;
                            }
                            QComboBox::item:!selected {
                                min-height: 34px;
                                background-color: rgb(30, 30, 30);
                                color: rgb(200, 200, 200);
                            }
                            QComboBox::indicator {
                                background-color:transparent;
                                selection-background-color:transparent;
                                color:transparent;
                                selection-color:transparent;
                            }
                            QComboBox QAbstractItemView {
                                border: """ + str(border) + """px solid rgb(50, 50, 50);
                                background-color: rgb(30, 30, 30);
                                box-shadow: transparent;
                            }
                           """)
        if tv:
            self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.view().setFrameShape(QFrame.NoFrame)
            self.view().setStyleSheet("""
                                QListView::item{
                                    min-width: 300px;
                                    margin: 0px;
                                    height: 24px;
                                    color: rgb(200, 200, 200);
                                    background-color: rgb(30, 30, 30);
                                }
                                QListView::item:hover{
                                    color: black;
                                    background-color: rgba(255, 255, 255, 0.4);
                                }
                                QListView::item:selected {
                                    padding-left: 0px;
                                    color: black;
                                    background-color: rgba(255, 255, 255, 0.4);
                                }
                                QListView::item:!selected {
                                    background-color: rgb(30, 30, 30);
                                    color: rgb(200, 200, 200);
                                }
                                QScrollBar:vertical {
                                    border: none;
                                    background: rgb(30, 30, 30);
                                    width: 14px;
                                    margin: 4px 3px 4px 3px;
                                }
                                QScrollBar::handle:vertical {
                                    min-height: 30px;
                                    border: 0px solid red;
                                    border-radius: 4px;
                                    background-color: rgba(255, 255, 255, 0.4);
                                }
                                QScrollBar::add-line:vertical {
                                    height: 0px;
                                    subcontrol-position: bottom;
                                    subcontrol-origin: margin;
                                }
                                QScrollBar::sub-line:vertical {
                                    height: 0px;
                                    subcontrol-position: top;
                                    subcontrol-origin: margin;
                                }
                            """)
        else:
            self.view().window().setStyleSheet("""
                                QListView::item{
                                    min-width: 300px;
                                    margin: 0px;
                                    height: 24px;
                                    color: rgb(200, 200, 200);
                                    background-color: rgb(30, 30, 30);
                                }
                                QListView::item:hover{
                                    color: black;
                                    background-color: rgba(255, 255, 255, 0.4);
                                }
                                QListView::item:selected {
                                    padding-left: 0px;
                                    color: black;
                                    background-color: rgba(255, 255, 255, 0.4);
                                }
                                QListView::item:!selected {
                                    background-color: rgb(30, 30, 30);
                                    color: rgb(200, 200, 200);
                                }
                                """)

    def paintEvent(self, event):
        p = QPainter()
        p.begin(self)
        option = QStyleOptionComboBox()
        option.initFrom(self)
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        if option.state & QStyle.State_Enabled:
            if option.state & QStyle.State_MouseOver:
                brush.setColor(QColor(255, 255, 255, 75))
            elif option.state & ~QStyle.State_MouseOver:
                brush.setColor(QColor(255, 255, 255, 50))
        else:
            brush.setColor(QColor(255, 255, 255, 25))
        p.fillRect(self.rect(), brush)
        style = QApplication.style()
        if self.val_display:
            text = "" if self.itemData(self.currentIndex()) == None else self.itemData(self.currentIndex())
        else:
            text = self.currentText()
        style.drawItemText(p, self.rect(), Qt.AlignCenter, self.palette(), self.isEnabled(), text)
        p.end()

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie widget'u poleceniem zewnętrznym."""
        self.setEnabled(_bool)

    def set_value(self, val, signal=False):
        """Ustawienie aktualnej wartości z db."""
        if not signal:
            # Próba (bo może być jeszcze nie podłączony) odłączenia sygnału zmiany aktualnego indeksu combobox'a:
            self.signal_off()
        if not val or (val and len(val) == 0):  # Wartość Null
            idx = 0
        else:
            idx = self.findData(val, flags=Qt.MatchExactly)
        if idx >= 0:
            self.setCurrentIndex(idx)
            self.index_changed(idx, True)
        if not signal:
            # Ponowne podpięcie sygnału zmiany indeksu:
            self.currentIndexChanged.connect(self.index_changed)

    def index_changed(self, index, fn_void=False):
        """Zmiana wartości przez użytkownika."""
        if self.itemData(index) == None:
            self.cur_val = "Null"
        else:
            self.cur_val = f"'{self.itemData(index)}'"
        if self.trigger:
            exec(f'dlg.wyr_panel.{self.trigger}')
        if self.fn and not fn_void:
            self.run_fn()

    def signal_on(self):
        """Włączenie sygnału zmiany indeksu."""
        try:
            self.currentIndexChanged.disconnect(self.index_changed)
        except TypeError:
            pass

    def signal_off(self):
        """Wyłączenie sygnału zmiany indeksu."""
        try:
            self.currentIndexChanged.disconnect(self.index_changed)
        except TypeError:
            pass

    def run_fn(self):
        """Odpalenie funkcji po zmianie wartości."""
        for fn in self.fn:
            try:
                exec(eval("f'{}'".format(fn)))
            except Exception as err:
                print(f"[run_fn] Błąd zmiany wartości: {err}")


class CanvasComboBox(QComboBox):
    """Fabryka rozwijanych."""
    def __init__(self, *args, name="", height=24, border=1, font_size=8, b_round="none"):
        super().__init__(*args)
        if b_round == "right":
            B_CSS = "border-top-right-radius: 3px; border-bottom-right-radius: 3px;"
        elif b_round == "all":
            B_CSS = "border-radius: 6px;"
        else:
            B_CSS = ""

        self.setStyleSheet("""
                            QComboBox {
                                border: """ + str(border) + """px solid rgb(255, 255, 255);
                                """ + B_CSS + """
                                padding: 0px 5px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                color: white;
                                background-color: rgba(255, 255, 255, 0.2);
                                font-size: """ + str(font_size) + """pt;
                            }
                            QComboBox:disabled {
                                border: """ + str(border) + """px solid rgb(150, 150, 150);
                                """ + B_CSS + """
                                padding: 0px 0px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                color: rgb(140, 140, 140);
                                font-size: """ + str(font_size) + """pt;
                            }
                            QComboBox::indicator {
                                background-color:transparent;
                                selection-background-color:transparent;
                                color:transparent;
                                selection-color:transparent;
                            }
                            QComboBox::item:selected {
                                min-height: 34px;
                                padding-left: 0px;
                                background-color: rgba(255, 255, 255, 0.4);
                                color: black;
                            }
                            QComboBox::item:!selected {
                                min-height: 34px;
                                background-color: rgb(30, 30, 30);
                                color: rgb(200, 200, 200);
                            }
                            QComboBox::drop-down {
                                subcontrol-origin: padding;
                                subcontrol-position: center right;
                                width: 12px;
                                right: 5px;
                                border: none;
                                background: transparent;
                                background-color: transparent;
                            }
                            QComboBox::down-arrow {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """down_arrow_dark.png');
                            }
                            QComboBox::down-arrow:disabled {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """down_arrow_dark_dis.png');
                            }
                            QComboBox QAbstractItemView {
                                border: """ + str(border) + """px solid rgb(120, 120, 120);
                                background-color: rgb(30, 30, 30);
                                box-shadow: transparent;
                            }
                           """)
        self.view().window().setStyleSheet("background-color: rgba(0, 0, 0, 0.0)")
        self.view().window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.view().window().setAttribute(Qt.WA_NoSystemBackground | Qt.WA_TranslucentBackground | Qt.WA_PaintOnScreen | Qt.WA_OpaquePaintEvent)


class MoekLineEdit(QLineEdit):
    """Fabryka wpisywanych."""
    def __init__(self, *args, name="", height=25, border=2):
        super().__init__(*args)
        self.setReadOnly(True)
        self.setStyleSheet("""
                            QLineEdit {
                                border: """ + str(border) + """px solid rgb(52, 132, 240);
                                padding: 0px 5px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                background: white;
                                font-size: 8pt;
                            }
                            QLineEdit:read-only {
                                background: white;
                            }
                           """)


class MoekCheckBox(QCheckBox):
    """Fabryka pstryczków."""
    def __init__(self, *args, name="", checked=False):
        super().__init__(*args)
        self.setText(name)
        self.setChecked(checked)
        self.setStyleSheet("""
                            QCheckBox {
                                border: none;
                                background: none;
                                color: rgb(52, 132, 240);
                                font-size: 10pt;
                                spacing: 3px;
                            }
                            QCheckBox:focus {
                                border: none;
                                outline: none;
                            }
                            QCheckBox::indicator {
                                width: 25px;
                                height: 25px;
                            }
                            QCheckBox::indicator:unchecked {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_0.png');
                            }
                            QCheckBox::indicator:unchecked:hover {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_0_act.png');
                            }
                            QCheckBox::indicator:checked {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_1.png');
                            }
                            QCheckBox::indicator:checked:hover {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_1_act.png');
                            }
                           """)


class CanvasCheckBox(QCheckBox):
    """Fabryka pstryczków w canvaspanelach."""
    def __init__(self, *args, name="", checked=False, font=10, fn=None):
        super().__init__(*args)
        self.setText(name)
        self.setChecked(checked)
        self.fn = fn
        self.stateChanged.connect(self.run_fn)
        self.setStyleSheet("""
                            QCheckBox {
                                border: none;
                                background: none;
                                color: rgb(170, 170, 170);
                                font-size: """ + str(font) + """pt;
                                spacing: 3px;
                            }
                            QCheckBox:disabled {
                                border: none;
                                background: none;
                                color: rgb(80, 80, 80);
                                font-size: 10pt;
                                spacing: 3px;
                            }
                            QCheckBox:focus {
                                border: none;
                                outline: none;
                            }
                            QCheckBox::indicator {
                                width: 25px;
                                height: 25px;
                            }
                            QCheckBox::indicator:unchecked {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_grey_0.png');
                            }
                            QCheckBox::indicator:unchecked:hover {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_grey_0_act.png');
                            }
                            QCheckBox::indicator:checked {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_grey_1.png');
                            }
                            QCheckBox::indicator:checked:hover {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_grey_1_act.png');
                            }
                            QCheckBox::indicator:disabled {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """checkbox_grey_dis.png');
                            }
                           """)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)

    def run_fn(self):
        """Odpalenie funkcji po zmianie wartości."""
        if not self.fn:
            return
        for fn in self.fn:
            try:
                exec(eval("f'{}'".format(fn)))
            except Exception as err:
                print(f"[run_fn] Błąd zmiany wartości: {err}")


class PanelLabel(QLabel):
    """Fabryka napisów do canvpaneli."""
    def __init__(self, *args, text="", color="255, 255, 255", disable_color="80, 80, 80", size=10, bold=False):
        super().__init__(*args)
        self.setWordWrap(False)
        self.setText(text)
        self.color = color
        self.disable_color = disable_color
        self.size = size
        self.bold = bold
        self.set_style()

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        self.set_style()

    def set_style(self):
        """Modyfikacja stylesheet."""
        color = self.color if self.isEnabled() else self.disable_color
        weight = "bold" if self.bold else "normal"
        self.setStyleSheet("QLabel {color: rgb(" + color + "); font-size: " + str(self.size) + "pt; font-weight: " + weight + "; qproperty-alignment: AlignCenter}")


class MoekSpinLabel(QLabel):
    """Fabryka napisów."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(25)
        self.setWordWrap(False)
        self.contract()

    def contract(self):
        """Skrócenie szerokości label'u przed pojawieniem się przycisków."""
        self.setFixedWidth(self.width() - 67)

    def setText(self, text):
        """Aktualizacja po zmianie tekstu."""
        super().setText(text)
        self.label_update()

    def label_update(self):
        """Aktualizacja labela po modyfikacji spinbox'a."""
        lbl_width = self.label_width()
        self.setFixedWidth(lbl_width)
        self.font_resize(lbl_width)

    def label_width(self):
        """Zwraca dostępną szerokość dla label'u."""
        btns_width = 0
        spb_width = self.parent().width()
        if spb_width == 640:  # Szerokość bazowa przy tworzeniu widget'u
            spb_width = 121  # Formatowanie do minimalnej szerokości
        # Ustalenie łącznej szerokości wyświetlanych przycisków:
        btns = self.parent().findChildren(MoekButton)
        for btn in btns:
            if btn.isVisible() or btn.shown:
                btns_width += btn.width()
        # Ustalenie szerokości label'u:
        return spb_width - btns_width

    def font_resize(self, l_w):
        """Zmniejszenie rozmiaru czcionki, jeśli napis się nie mieści."""
        f_size = 10
        marg = 10
        f = QFont("Segoe UI", f_size)
        f.setPointSize(f_size)
        self.setFont(f)
        f_w = self.fontMetrics().boundingRect(self.text()).width() + marg
        while l_w < f_w:
            f_size -= 1
            f.setPointSize(f_size)
            self.setFont(f)
            f_w = self.fontMetrics().boundingRect(self.text()).width() + marg
            if f_size == 6:  # Ograniczenie zmniejszenia czcionki
                return
