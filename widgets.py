# -*- coding: utf-8 -*-
import os
import pandas as pd

from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter
from qgis.PyQt.QtWidgets import QApplication, QWidget, QSpinBox, QMessageBox, QFrame, QToolButton, QPushButton, QComboBox, QLineEdit, QPlainTextEdit, QCheckBox, QLabel, QProgressBar, QStackedWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect, QTableView, QAbstractItemView, QStyle, QStyleOptionComboBox
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal, QRegExp, QRect, QTimer
from qgis.PyQt.QtGui import QPen, QBrush, QIcon, QColor, QFont, QPainter, QPixmap, QPainterPath, QRegExpValidator, QStandardItemModel
from qgis.utils import iface

from .main import db_attr_change, vn_cfg, vn_setup_mode, powiaty_mode_changed, vn_mode_changed, get_wyr_ids, get_flag_ids, get_parking_ids, get_marsz_ids, wyr_layer_update, wn_layer_update, marsz_layer_update, file_dialog, sequences_load, db_sequence_update
from .classes import PgConn, CfgPars, WDfModel, CmbDelegate
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
        self.setFixedWidth(516)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.heights = [268, 460, 225]
        self.mt_enabled = False
        self.cur_page = int()
        self.bar = CanvasPanelTitleBar(self, title="Wyrobiska", width=self.width())
        self.list_box = MoekVBox(self, spacing=1)
        self.list_box.setFixedWidth(96)
        self.sp_id = CanvasHSubPanel(self, height=34, margins=[0, 0, 0, 0], color="255, 255, 255", alpha=0.8)
        self.list_box.lay.addWidget(self.sp_id)
        self.id_box = IdSpinBox(self, _obj="wyr", theme="light")
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
                    QFrame#main{background-color: rgba(0, 0, 0, 0.4); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(2)
        hlay.addWidget(self.list_box)
        hlay.addWidget(self.box)
        hlay.setAlignment(self.box, Qt.AlignTop)
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(2)
        vlay.addWidget(self.bar)
        vlay.addLayout(hlay)
        self.setLayout(vlay)
        self.sp_main = CanvasHSubPanel(self, margins=[4, 0, 0, 0], spacing=2, height=34)
        self.box.lay.addWidget(self.sp_main)
        self.wn_picker = WyrWnPicker(self)
        self.sp_main.lay.addWidget(self.wn_picker)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.sp_main.lay.addItem(spacer)
        self.area_icon = MoekButton(self, name="wyr_area", size=34, checkable=False, enabled=False, tooltip="powierzchnia wyrobiska")
        self.sp_main.lay.addWidget(self.area_icon)
        self.area_label = PanelLabel(self, text="", size=12)
        self.sp_main.lay.addWidget(self.area_label)
        self.wyr_edit = MoekButton(self, name="wyr_edit", size=34, checkable=False)
        self.wyr_edit.clicked.connect(lambda: dlg.mt.init("wyr_edit"))
        self.sp_main.lay.addWidget(self.wyr_edit)
        self.wyr_del = MoekButton(self, name="trash", size=34, checkable=False)
        self.wyr_del.clicked.connect(self.wyr_delete)
        self.sp_main.lay.addWidget(self.wyr_del)
        self.sp_status = CanvasHSubPanel(self, height=34, margins=[4, 2, 4, 4], spacing=4)
        self.box.lay.addWidget(self.sp_status)
        self.status_indicator = WyrStatusIndicator(self)
        self.sp_status.lay.addWidget(self.status_indicator)
        self.status_selector = WyrStatusSelector(self, width=68)
        self.sp_status.lay.addWidget(self.status_selector)
        self.separator_1 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.box.lay.addWidget(self.separator_1)
        self.sb = MoekStackedBox(self)
        self.sb.setFixedWidth(412)
        self.box.lay.addWidget(self.sb)
        self.pages = {}
        self.widgets = {}
        for p in range(3):
            _page = MoekGridBox(self, margins=[4, 4, 0, 2], spacing=0, theme="dark")
            page_id = f'page_{p}'
            self.pages[page_id] = _page
            self.sb.addWidget(_page)
        self.sb.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.sb.currentChanged.connect(self.page_change)
        self.height_change()  # Wstępne ustalenie wysokości panelu
        self.dicts = [
                    {"name": "okres_eksp_0", "page": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "zero_allowed": False, "width": 402, "val_width": 125, "val_width_2": 125, "sep_width": 1, "sep_txt": "", "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji:", "icon": None, "tooltip": "", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_od", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_do", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)']]},

                    {"name": "notepad_0", "page": 0, "row": 1, "col": 0, "r_span": 1, "c_span": 12, "type": "notepad"},

                    {"name": "kopalina_wiek_1", "page": 1, "row": 0, "col": 4, "r_span": 2, "c_span": 8, "type": "kop_wiek"},

                    {"name": "okres_eksp_1", "page": 1, "row": 2, "col": 0, "r_span": 1, "c_span": 12, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "zero_allowed": False, "width": 402, "val_width": 130, "val_width_2": 130, "sep_width": 6, "sep_txt": "", "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji:", "icon": None, "tooltip": "", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_od", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_do", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)']]},

                    {"name": "dlug_1", "page": 1, "row": 3, "col": 0, "r_span": 1, "c_span": 4, "type": "text_2", "item": "ruler", "max_len": 3, "validator": "000", "placeholder": "000", "zero_allowed": False, "width": 130, "val_width": 40, "val_width_2": 40, "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_dlug", "tooltip": "długość wyrobiska", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_dlug_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_dlug_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "szer_1", "page": 1, "row": 3, "col": 4, "r_span": 1, "c_span": 4, "type": "text_2", "item": "ruler", "max_len": 3, "validator": "000", "placeholder": "000", "zero_allowed": False, "width": 130, "val_width": 40, "val_width_2": 40, "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_szer", "tooltip": "szerokość wyrobiska", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_szer_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_szer_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "wys_1", "page": 1, "row": 3, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 4, "validator": "00.0", "placeholder": "0.0", "zero_allowed": True, "width": 130, "val_width": 40, "val_width_2": 40, "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_wys", "tooltip": "wysokość wyrobiska", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_wys_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill("min")'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_wys_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill("max")']]},

                    {"name": "nadkl_1", "page": 1, "row": 4, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 3, "validator": "00.0", "placeholder": "0.0", "zero_allowed": True, "width": 130, "val_width": 40, "val_width_2": 40, "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_nadkl", "tooltip": "grubość nadkładu", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_nadkl_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill("min")'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_nadkl_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'dlg.wyr_panel.miaz_fill("max")']]},

                    {"name": "miaz_1", "page": 1, "row": 5, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 3, "validator": "00.0", "placeholder": "0.0", "zero_allowed": True, "width": 130, "val_width": 40, "val_width_2": 40, "sep_width": 16, "sep_txt": "–", "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_miaz", "tooltip": "miąższość kopaliny", "fn": [['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_miazsz_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)'], ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_miazsz_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']]},

                    {"name": "droga_1", "page": 1, "row": 4, "col": 0, "r_span": 1, "c_span": 4, "type": "combo", "width": 130, "title_down": "DOJAZD DO WYROBISKA", "tbl_name": "sl_dojazd", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_dojazd", val="{self.data_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "rodz_wyr_1", "page": 1, "row": 5, "col": 0, "r_span": 1, "c_span": 4, "type": "combo", "width": 130, "title_down": "RODZAJ WYROBISKA", "tbl_name": "sl_wyrobisko", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyrobisko", val="{self.data_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "hydro_1", "page": 1, "row": 4, "col": 4, "r_span": 1, "c_span": 4, "type": "combo", "width": 130, "title_down": "ZAWODNIENIE", "tbl_name": "sl_zawodnienie", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_zawodn", val="{self.data_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "stan_1", "page": 1, "row": 5, "col": 4, "r_span": 1, "c_span": 4, "type": "combo", "width": 130, "title_down": "STAN WYROBISKA", "tbl_name": "sl_stan_pne", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_stan_pne", val="{self.data_val}", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "notepad_1", "page": 1, "row": 6, "col": 0, "r_span": 1, "c_span": 12, "type": "notepad"},

                    {"name": "notepad_2", "page": 2, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "notepad"}
                    ]

        for dict in self.dicts:
            if dict["type"] == "combo":
                _cmb = ParamBox(self, margins=True, item="combo", width=dict["width"], val_width=dict["width"], title_down=dict["title_down"], fn=dict["fn"])
                exec(f'self.pages["page_{dict["page"]}"].glay.addWidget(_cmb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                cmb_name = f'cmb_{dict["name"]}'
                self.widgets[cmb_name] = _cmb
                self.sl_load(dict["tbl_name"], self.widgets[cmb_name].valbox_1)
            if dict["type"] == "text_2":
                _txt2 = ParamBox(self, margins=True, item=dict["item"], max_len=dict["max_len"], validator=dict["validator"], placeholder=dict["placeholder"], zero_allowed=dict["zero_allowed"], width=dict["width"], value_2=" ", val_width=dict["val_width"], val_width_2=dict["val_width_2"], sep_width=dict["sep_width"], sep_txt=dict["sep_txt"], title_down=dict["title_down"], title_down_2=dict["title_down_2"], title_left=dict["title_left"], icon=dict["icon"], tooltip=dict["tooltip"], fn=dict["fn"])
                exec(f'self.pages["page_{dict["page"]}"].glay.addWidget(_txt2, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                txt2_name = f'txt2_{dict["name"]}'
                self.widgets[txt2_name] = _txt2
            if dict["type"] == "notepad":
                _np = TextPadBox(self, height=110, obj="wyr", width=392)
                exec(f'self.pages["page_{dict["page"]}"].glay.addWidget(_np, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                np_name = f'np_{dict["name"]}'
                self.widgets[np_name] = _np
            if dict["type"] == "kop_wiek":
                _kw = KopalinaWiekBox(self)
                exec(f'self.pages["page_{dict["page"]}"].glay.addWidget(_kw, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                kw_name = 'kw_1'
                self.widgets[kw_name] = _kw

    def sl_load(self, tbl_name, cmb):
        """Załadowanie wartości słownikowych z db do combobox'a."""
        db = PgConn()
        sql = f"SELECT t_val, t_desc FROM public.{tbl_name};"
        if db:
            res = db.query_sel(sql, True)
            if res:
                cmb.addItem(f"", None)
                for r in res:
                    cmb.addItem(f"  {r[1]}  ", r[0])

    def values_update(self, _dict):
        """Aktualizuje wartości parametrów."""
        params = [
            {'type': 'notepad', 'value': _dict[7], 'pages': [0, 1, 2]},
            {'type': 'text_2', 'name': 'okres_eksp', 'value': _dict[5], 'value_2': _dict[6], 'pages': [0, 1]},
            {'type': 'text_2', 'name': 'dlug', 'value': _dict[8], 'value_2': _dict[9], 'pages': [1]},
            {'type': 'text_2', 'name': 'szer', 'value': _dict[10], 'value_2': _dict[11], 'pages': [1]},
            {'type': 'text_2', 'name': 'wys', 'value': _dict[12], 'value_2': _dict[13], 'pages': [1]},
            {'type': 'text_2', 'name': 'nadkl', 'value': _dict[14], 'value_2': _dict[15], 'pages': [1]},
            {'type': 'text_2', 'name': 'miaz', 'value': _dict[16], 'value_2': _dict[17], 'pages': [1]},
            {'type': 'kw','values': [_dict[36], _dict[37], _dict[38], _dict[39]], 'pages': [1]},
            {'type': 'combo', 'name': 'droga', 'value': _dict[31], 'pages': [1]},
            {'type': 'combo', 'name': 'hydro', 'value': _dict[19], 'pages': [1]},
            {'type': 'combo', 'name': 'stan', 'value': _dict[35], 'pages': [1]},
            {'type': 'combo', 'name': 'rodz_wyr', 'value': _dict[18], 'pages': [1]}
        ]
        for param in params:
            if not self.cur_page in param["pages"]:
                continue
            if param["type"] == "notepad":
                txt = self.param_parser(param["value"], True)
                exec(f'self.widgets["np_notepad_{self.cur_page}"].set_text({txt})')
            if param["type"] == "text_2":
                param_1 = self.param_parser(param["value"])
                param_2 = self.param_parser(param["value_2"])
                exec(f'self.widgets["txt2_{param["name"]}_{self.cur_page}"].value_change("value", param_1)')
                exec(f'self.widgets["txt2_{param["name"]}_{self.cur_page}"].value_change("value_2", param_2)')
            if param["type"] == "combo":
                param_val = self.param_parser(param["value"])
                exec(f'self.widgets["cmb_{param["name"]}_{self.cur_page}"].value_change("value", param_val)')
            if param["type"] == "kw":
                exec(f'self.widgets["kw_1"].set_values({param["values"]})')

    def param_parser(self, val, quote=False):
        """Zwraca wartość przerobioną na tekst (pusty, jeśli None)."""
        if quote:
            txt = f'"{val}"' if val != None else f'""'
        else:
            txt = f'{val}' if val != None else f''
        return txt

    def get_notepad(self):
        """Zwraca referencję do notepad_box'a z odpowiedniej strony."""
        return self.widgets[f"np_notepad_{self.cur_page}"]

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

    def miaz_fill(self, min_max):
        """Uzupełnia wartość miąższości kopaliny jako różnicy wysokości i nadkładu."""
        wys_txt = dlg.wyr_panel.widgets["txt2_wys_1"].valbox_1.text() if min_max == "min" else dlg.wyr_panel.widgets["txt2_wys_1"].valbox_2.text()
        nadkl_txt = dlg.wyr_panel.widgets["txt2_nadkl_1"].valbox_1.cur_val if min_max == "min" else dlg.wyr_panel.widgets["txt2_nadkl_1"].valbox_2.cur_val
        if wys_txt == None or nadkl_txt == None:
            miaz_val = ""
        else:
            wys_val = float(wys_txt)
            nadkl_val = float(nadkl_txt)
            miaz_val = wys_val - nadkl_val
            if miaz_val < 0.0:
                miaz_val = ""
            else:
                miaz_val = str(miaz_val)
        dlg.wyr_panel.widgets["txt2_miaz_1"].valbox_1.set_value(miaz_val) if min_max == "min" else dlg.wyr_panel.widgets["txt2_miaz_1"].valbox_2.set_value(miaz_val)
        dlg.wyr_panel.widgets["txt2_miaz_1"].valbox_1.run_fn() if min_max == "min" else dlg.wyr_panel.widgets["txt2_miaz_1"].valbox_2.run_fn()


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
        self.height_change()  # Aktualizacja wysokości dock'u

    def height_change(self):
        """Zmiana wysokości dock'u i aktualizacja pozycji na mapcanvas'ie."""
        self.setFixedHeight(self.heights[self.cur_page])

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


class FlagCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi flag."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setFixedWidth(350)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.bar = CanvasPanelTitleBar(self, title="Flagi", width=self.width())
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.4); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        self.sp_tools = CanvasHSubPanel(self, height=34)
        self.box.lay.addWidget(self.sp_tools)
        self.id_label = PanelLabel(self, text="  Id:", size=12)
        self.sp_tools.lay.addWidget(self.id_label)
        self.id_box = IdSpinBox(self, _obj="flag")
        self.sp_tools.lay.addWidget(self.id_box)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.sp_tools.lay.addItem(spacer)
        self.flag_tools = FlagTools(self)
        self.sp_tools.lay.addWidget(self.flag_tools)
        self.sp_notepad = CanvasHSubPanel(self, height=110)
        self.box.lay.addWidget(self.sp_notepad)
        self.notepad_box = TextPadBox(self, height=110, obj="flag")
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
        self.bar = CanvasPanelTitleBar(self, title="Miejsca parkowania", width=self.width())
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.4); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        self.sp_tools = CanvasHSubPanel(self, height=34)
        self.box.lay.addWidget(self.sp_tools)
        self.id_label = PanelLabel(self, text="  Id:", size=12)
        self.sp_tools.lay.addWidget(self.id_label)
        self.id_box = IdSpinBox(self, _obj="parking")
        self.sp_tools.lay.addWidget(self.id_box)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.sp_tools.lay.addItem(spacer)
        self.parking_tools = ParkingTools(self)
        self.sp_tools.lay.addWidget(self.parking_tools)
        # self.sp_notepad = CanvasHSubPanel(self, height=110)
        # self.box.lay.addWidget(self.sp_notepad)
        # self.notepad_box = TextPadBox(self, height=110, obj="flag")
        # self.sp_notepad.lay.addWidget(self.notepad_box)

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
                    QFrame#box{background-color: rgba(0,0,0,0.6); border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)
        vlay.addWidget(self.pointer)
        vlay.addWidget(self.box)
        vlay.setAlignment(self.pointer, Qt.AlignCenter)
        self.setLayout(vlay)
        self.marsz_continue = MoekButton(self, name="line_continue", size=34)
        self.marsz_edit = MoekButton(self, name="line_edit", size=34)
        self.trash = MoekButton(self, name="trash", size=34)
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
        self.bar = CanvasPanelTitleBar(self, title="WN_Kopaliny_PNE", width=self.width())
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.4); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        self.sp_id = CanvasHSubPanel(self, height=34)
        self.box.lay.addWidget(self.sp_id)
        self.separator_1 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.box.lay.addWidget(self.separator_1)
        self.top_margin = CanvasHSubPanel(self, height=8)
        self.box.lay.addWidget(self.top_margin)
        self.id_label = PanelLabel(self, text="   Id_arkusz:", size=11)
        self.sp_id.lay.addWidget(self.id_label)
        self.id_box = IdSpinBox(self, _obj="wn", width=134, max_len=8, validator="id_arkusz")
        self.sp_id.lay.addWidget(self.id_box)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.sp_id.lay.addItem(spacer)
        self.params_1 = CanvasHSubPanel(self, height=44, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_1)
        self.kopalina = ParamBox(self, width=217, title_down="KOPALINA")
        self.params_1.lay.addWidget(self.kopalina)
        self.data_inw = ParamBox(self, width=103, title_down="DATA INWENTARYZACJI")
        self.params_1.lay.addWidget(self.data_inw)
        self.params_2 = CanvasHSubPanel(self, height=44, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_2)
        self.wyrobisko = ParamBox(self, title_down="WYROBISKO")
        self.params_2.lay.addWidget(self.wyrobisko)
        self.zawodn = ParamBox(self, title_down="ZAWODNIENIE")
        self.params_2.lay.addWidget(self.zawodn)
        self.params_3 = CanvasHSubPanel(self, height=44, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_3)
        self.eksploat = ParamBox(self, title_down="EKSPLOATACJA")
        self.params_3.lay.addWidget(self.eksploat)
        self.odpady = ParamBox(self, title_down="WYPEŁNIENIE ODPADAMI")
        self.params_3.lay.addWidget(self.odpady)
        self.params_4 = CanvasHSubPanel(self, height=44, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_4)
        self.dlug_max = ParamBox(self, title_left="Długość maks. [m]:")
        self.params_4.lay.addWidget(self.dlug_max)
        self.szer_max = ParamBox(self, title_left="Szerokość maks. [m]:")
        self.params_4.lay.addWidget(self.szer_max)
        self.params_5 = CanvasHSubPanel(self, height=44, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_5)
        self.wysokosc = ParamBox(self, width=328, value_2=" ", title_down="MIN", title_down_2="MAX", title_left="Wysokość wyrobiska [m]:")
        self.params_5.lay.addWidget(self.wysokosc)
        self.params_6 = CanvasHSubPanel(self, height=44, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_6)
        self.nadklad = ParamBox(self, width=328, value_2=" ", title_down="MIN", title_down_2="MAX", title_left="Grubość nadkładu [m]:")
        self.params_6.lay.addWidget(self.nadklad)
        self.params_7 = CanvasHSubPanel(self, height=44, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_7)
        self.miazsz = ParamBox(self, width=328, value_2=" ", title_down="MIN", title_down_2="MAX", title_left="Miąższość kopaliny [m]:")
        self.params_7.lay.addWidget(self.miazsz)
        self.params_8 = CanvasHSubPanel(self, height=90, margins=[8, 0, 8, 0], spacing=8)
        self.box.lay.addWidget(self.params_8)
        self.uwagi = ParamTextBox(self, title="UWAGI")
        self.params_8.lay.addWidget(self.uwagi)
        self.bottom_margin = CanvasHSubPanel(self, height=4)
        self.box.lay.addWidget(self.bottom_margin)
        self.separator_2 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.box.lay.addWidget(self.separator_2)
        self.sp_pow = CanvasHSubPanel(self, height=34)
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


class ExportCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi eksportu danych."""
    path_changed = pyqtSignal(str)

    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(500)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.bar = CanvasPanelTitleBar(self, title="Eksport danych", width=self.width())
        self.box = MoekVBox(self)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.4); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(1)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        self.path_box = CanvasHSubPanel(self, height=44, margins=[5, 5, 5, 5], spacing=5)
        self.box.lay.addWidget(self.path_box)
        self.path_pb = ParamBox(self, width=445, title_down="FOLDER EKSPORTU")
        self.path_box.lay.addWidget(self.path_pb)
        self.path_btn = MoekButton(self, name="export_path", size=34, checkable=False)
        self.path_btn.clicked.connect(self.set_path)
        self.path_box.lay.addWidget(self.path_btn)
        self.sp_ext = CanvasHSubPanel(self, height=46, margins=[0, 10, 0, 2])
        self.box.lay.addWidget(self.sp_ext)
        self.export_btn = MoekButton(self, name="export", size=34, checkable=False, enabled=False)
        self.export_btn.clicked.connect(self.layers_export)
        self.export_selector = ExportSelector(self, width=445)
        self.sp_ext.lay.addWidget(self.export_selector)
        self.sp_ext.lay.addWidget(self.export_btn)
        self.sp_progress = CanvasHSubPanel(self, height=8, margins=[5, 2, 5, 0], spacing=8)
        self.box.lay.addWidget(self.sp_progress)
        self.p_bar = QProgressBar()
        self.p_bar.setFixedHeight(6)
        self.p_bar.setRange(0, 100)
        self.p_bar.setTextVisible(False)
        self.p_bar.setVisible(False)
        self.sp_progress.lay.addWidget(self.p_bar)
        self.bottom_margin = CanvasHSubPanel(self, height=4)
        self.box.lay.addWidget(self.bottom_margin)
        self.pow_bbox = None
        self.pow_all = None
        self.path_void = None
        self.case_void = True
        self.case = 0
        self.export_path = None
        self.path_changed.connect(self.path_change)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "export_path":
            self.path_changed.emit(val)
            self.path_void = False if val else True
        if attr == "case":
            self.case_void = False if val else True
        if attr == "path_void" or attr == "case_void":
            try:
                self.export_btn.setEnabled(False) if self.path_void or self.case_void else self.export_btn.setEnabled(True)
            except:
                pass

    def pow_reset(self):
        """Kasuje zawartość zmiennych 'self.pow_bbox' i 'self.pow_all' po zmianie team'u."""
        self.pow_bbox = None
        self.pow_all = None

    def path_change(self, path):
        """Zmiana ścieżki eksportu danych."""
        if path and not os.path.isdir(path):
            self.export_path = None
            self.path_void = True
            return
        self.path_pb.value_change("value","") if not path else self.path_pb.value_change("value", path)
        db_path = "Null" if not path else f"'{path}'"
        table = f"public.team_users"
        bns = f" WHERE team_id = {dlg.team_i} and user_id = {dlg.user_id}"
        db_attr_change(tbl=table, attr="t_export_path", val=db_path, sql_bns=bns, user=False)

    def set_path(self):
        """Ustawia ścieżkę do folderu eksportu przez okno dialogowe menedżera plików."""
        path = file_dialog(is_folder=True)
        if path:
            self.export_path = path

    def exit_clicked(self):
        """Wyłączenie panelu po naciśnięciu na przycisk X."""
        dlg.export_panel.hide()

    def layers_export(self):
        """Eksport danych na dysk lokalny."""
        with CfgPars() as cfg:
            PARAMS = cfg.uri()
        file_types = []
        if self.case in [1, 3, 5, 7]:
            file_types.append({'driver' : 'GPKG', 'folder' : 'geopackage', 'extension' : '.gpkg'})
        if self.case in [2, 3, 6, 7]:
            file_types.append({'driver' : 'KML', 'folder' : 'kml', 'extension' : '.kml'})
        if self.case in [4, 5, 6, 7]:
            file_types.append({'driver' : 'ESRI Shapefile', 'folder' : 'shapefiles', 'extension' : '.shp'})
        lyrs = [
            {'lyr_name' : 'midas_zloza', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_zloza', 'tbl_sql' : '"external"."midas_zloza"', 'key' : 'id', 'n_field' : 'id_zloza', 'd_field' : 'nazwa_zloz'},
            {'lyr_name' : 'midas_wybilansowane', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_wybilansowane', 'tbl_sql' : '"external"."midas_wybilansowane"', 'key' : 'id1', 'n_field' : 'id', 'd_field' : 'nazwa'},
            {'lyr_name' : 'midas_obszary', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_obszary', 'tbl_sql' : '"external"."midas_obszary"', 'key' : 'id', 'n_field' : 'id_zloz', 'd_field' : 'nazwa'},
            {'lyr_name' : 'midas_tereny', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_tereny', 'tbl_sql' : '"external"."midas_tereny"', 'key' : 'id1', 'n_field' : 'id_zloz', 'd_field' : 'nazwa'},
            {'lyr_name' : 'wn_pne', 'spatial_filter': 'id_all', 'tbl_name' : f'team_{dlg.team_i}.wn_pne', 'tbl_sql' : f'"external"."wn_pne"', 'key' : 'id_arkusz', 'n_field' : 'id_arkusz', 'd_field' : 'uwagi'},
            {'lyr_name' : 'parking', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."parking" (geom) sql=', 'n_field' : 'id', 'd_field' : 'description', 'fields' : [0, 3]},
            {'lyr_name' : 'marsz', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."marsz" (geom) sql=', 'n_field' : 'id', 'd_field' : 'i_status', 'fields' : [0, 2, 3]},
            {'lyr_name' : 'wyr_point', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."wyrobiska" (centroid) sql=', 'n_field' : 'wyr_id', 'd_field' : 't_notatki', 'fields' : [0, 6, 13]},
            {'lyr_name' : 'wyr_poly', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."wyr_geom" (geom) sql=', 'n_field' : 'wyr_id', 'd_field' : 'Description', 'fields' : [0]},
            {'lyr_name' : 'flagi_z_teren', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."flagi" (geom) sql=b_fieldcheck = True', 'n_field' : 'id', 'd_field' : 't_notatki', 'fields' : [0, 3, 4]},
            {'lyr_name' : 'flagi_bez_teren', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."flagi" (geom) sql=b_fieldcheck = False', 'n_field' : 'id', 'd_field' : 't_notatki', 'fields' : [0, 3, 4]}
        ]
        i_max = len(lyrs) * len(file_types) + 1
        self.p_bar.setVisible(True)
        i = 1
        self.p_bar.setValue(i * 100 / i_max)
        QgsApplication.processEvents()
        if not self.pow_bbox:
            self.set_pow_bbox()
            self.set_pow_all()
        i += 1
        self.p_bar.setValue(i * 100 / i_max)
        QgsApplication.processEvents()
        for ft in file_types:
            self.folder_create(ft["folder"])
        for l_dict in lyrs:
            if l_dict["spatial_filter"] == "pow_all":
                ids = self.spatial_filtering(l_dict["tbl_name"], l_dict["key"])
                f_lyr = self.filtered_layer(l_dict["lyr_name"], l_dict["tbl_sql"], l_dict["key"], ids)
            elif l_dict["spatial_filter"] == "id_all":
                ids = self.get_ids_from_table(l_dict["tbl_name"], l_dict["key"])
                f_lyr = self.filtered_layer(l_dict["lyr_name"], l_dict["tbl_sql"], l_dict["key"], ids)
            elif not l_dict["spatial_filter"]:
                raw_uri = l_dict["uri"]
                uri = eval("f'{}'".format(raw_uri))
                f_lyr = QgsVectorLayer(uri, l_dict["lyr_name"], "postgres")
            for ft in file_types:
                dest_path = f'{self.export_path}/{ft["folder"]}/{l_dict["lyr_name"]}{ft["extension"]}'
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = ft["driver"]
                options.fileEncoding = 'utf-8'
                if "fields" in l_dict:
                    options.attributes = l_dict["fields"]
                options.datasourceOptions = [f"NameField={l_dict['n_field']}", f"DescriptionField={l_dict['d_field']}"]
                QgsVectorFileWriter.writeAsVectorFormatV2(layer=f_lyr, fileName=dest_path, transformContext=dlg.proj.transformContext(), options=options)
                i += 1
                self.p_bar.setValue(i * 100 / i_max)
                QgsApplication.processEvents()
        self.p_bar.setVisible(False)

    def folder_create(self, folder):
        """Tworzy folder o podanej nazwie, jeśli nie istnieje."""
        if not os.path.isdir(f"{self.export_path}{os.path.sep}{folder}"):
            os.makedirs(f"{self.export_path}{os.path.sep}{folder}")

    def get_ids_from_table(self, tbl_name, key):
        """Zwraca listę id z podanej tabeli."""
        db = PgConn()
        sql = f"SELECT {key} FROM {tbl_name} ORDER BY {key};"
        if db:
            res = db.query_sel(sql, True)
            if res:
                if len(res) > 1:
                    return list(zip(*res))[0]
                else:
                    return list(res[0])
            else:
                return []

    def filtered_layer(self, lyr_name, tbl_name, key, ids):
        """Zwraca warstwę z obiektami na podstawie listy numerów ID."""
        with CfgPars() as cfg:
            params = cfg.uri()
        sql = f"{key} IN ({str(ids)[1:-1]})"
        uri = f'{params} table={tbl_name} (geom) sql={sql}'
        lyr = QgsVectorLayer(uri, lyr_name, "postgres")
        return lyr

    def spatial_filtering(self, tbl_name, key):
        """Zwraca listę z numerami ID obiektów z podanej tabeli, które występują w obrębie powiatów zespołu."""
        f_list = []
        with CfgPars() as cfg:
            params = cfg.uri()
        table = f'"(SELECT {key}, geom FROM {tbl_name})"'
        _key = f'"{key}"'
        sql = "ST_Intersects(ST_SetSRID(ST_GeomFromText('" + str(self.pow_bbox.asWkt()) + "'), 2180), geom)"
        uri = f'{params} key={_key} table={table} (geom) sql={sql}'
        lyr_pow = QgsVectorLayer(uri, "feat_bbox", "postgres")
        feats = lyr_pow.getFeatures()
        for feat in feats:
            if feat.geometry().intersects(self.pow_all):
                f_list.append(feat.attribute(key))
        del lyr_pow
        return f_list

    def set_pow_bbox(self):
        """Zwraca do zmiennej self.pow_bbox geometrię bbox powiatów zespołu."""
        with CfgPars() as cfg:
            params = cfg.uri()
        table = f'(SELECT row_number() over () AS id, * FROM (select ST_Union(ST_Envelope(geom)) geom from team_{dlg.team_i}.powiaty) AS sq)'
        key = "id"
        uri = f'{params} key="{key}" table="{table}" (geom) sql='
        lyr = QgsVectorLayer(uri, "temp_pow_bbox", "postgres")
        if not lyr.isValid():
            print(f"set_pow_bbox: warstwa z geometrią nie jest prawidłowa")
            return
        geom = None
        feats = lyr.getFeatures()
        for feat in feats:
            geom = feat.geometry()
        del lyr
        self.pow_bbox = geom if geom.isGeosValid() else None

    def set_pow_all(self):
        """Zwraca do zmiennej self.pow_all złączoną geometrię powiatów zespołu."""
        with CfgPars() as cfg:
            params = cfg.uri()
        table = f'(SELECT row_number() over () AS id, * FROM (select ST_Union(geom) geom from team_{dlg.team_i}.powiaty) AS sq)'
        key = "id"
        uri = f'{params} key="{key}" table="{table}" (geom) sql='
        lyr = QgsVectorLayer(uri, "temp_pow_all", "postgres")
        if not lyr.isValid():
            print(f"set_pow_all: warstwa z geometrią nie jest prawidłowa")
            return
        geom = None
        feats = lyr.getFeatures()
        for feat in feats:
            geom = feat.geometry()
        del lyr
        self.pow_all = geom if geom.isGeosValid() else None


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
                    QFrame#bar{background-color: rgba(0, 0, 0, 1.0); border: none}
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


class CanvasHSubPanel(QFrame):
    """Belka canvaspanel'u z box'em."""
    def __init__(self, *args, height, margins=[0, 0, 0, 0], spacing=0, color="0, 0, 0", alpha=0.8):
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


class CanvasStackedSubPanel(QStackedWidget):
    """Subpanel ze stronami."""
    def __init__(self, *args, height, margins=[0, 0, 0, 0], spacing=0, alpha=0.8):
        super().__init__(*args)
        self.setObjectName("main")

        def minimumSizeHint(self):
            self.setMinimumHeight(self.currentWidget().minimumSizeHint().height())
            self.setMaximumHeight(self.currentWidget().minimumSizeHint().height())
            return self.currentWidget().minimumSizeHint()

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
                           """)
        self.clicked.connect(lambda: self.parent().btn_clicked(self.id))


class ExportSelector(QFrame):
    """Belka wyboru typów danych do eksportu."""
    def __init__(self, *args, width):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(34)
        self.setFixedWidth(width)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(4)
        self.setLayout(self.lay)
        self.valid_check = False
        self.itms = {}
        self.file_types = [
            {'name' : 'gpkg', 'multiplier' : 1},
            {'name' : 'kml', 'multiplier' : 2},
            {'name' : 'shp', 'multiplier' : 4}
            ]
        for file_type in self.file_types:
            _itm = ExportSelectorItem(self, name=file_type["name"])
            self.lay.addWidget(_itm)
            itm_name = f'btn_{file_type["name"]}'
            self.itms[itm_name] = _itm

    def btn_clicked(self):
        """Zmiana wartości 'case' po naciśnięciu przycisku."""
        case = 0
        for i_dict in self.file_types:
            btn = self.itms[f'btn_{i_dict["name"]}']
            val = 1 if btn.isChecked() else 0
            case = case + (val * i_dict["multiplier"])
        self.parent().parent().parent().case = case


class ExportSelectorItem(QPushButton):
    """Guzik do wyboru aktywnych typów danych do eksportu."""
    # checked_changed = pyqtSignal(bool)

    def __init__(self, *args, name):
        super().__init__(*args)
        self.setCheckable(True)
        self.setChecked(False)
        self.name = name
        self.setText(self.name)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
                            QPushButton {
                                border: 1px solid rgba(255, 255, 255, 0.4);
                                background: rgba(255, 255, 255, 0.2);
                                color: rgba(255, 255, 255, 1.0);
                                font-size: 11pt;
                            }
                            QPushButton:hover {
                                border: 1px solid rgba(255, 255, 255, 0.4);
                                background: rgba(255, 255, 255, 0.4);
                                color: rgba(255, 255, 255, 1.0);
                                font-size: 11pt;
                            }
                            QPushButton:checked {
                                border: 1px solid rgba(255, 255, 255, 0.8);
                                background: rgba(255, 255, 255, 0.6);
                                color: rgb(0, 0, 0);
                                font-size: 11pt;
                            }
                            QPushButton:hover:checked {
                                border: 1px solid rgba(255, 255, 255, 1.0);
                                background: rgba(255, 255, 255, 1.0);
                                color: rgb(0, 0, 0);
                                font-size: 11pt;
                            }
                            QPushButton:disabled {
                                border: 1px solid rgba(255, 255, 255, 1.0);
                                background: rgba(255, 255, 255, 0.7);
                                color: rgb(255, 255, 255);
                                font-size: 11pt;
                           """)
        self.clicked.connect(self.parent().btn_clicked)


class WyrStatusIndicator(QLabel):
    """Wyświetla status aktywnego wyrobiska."""
    def __init__(self, *args, text="WYROBISKO PRZED KONTROLĄ", color="153, 153, 153"):
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


class WyrWnPicker(QFrame):
    """Belka przydziału WN_PNE dla wyrobiska."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(30)
        self.setFixedWidth(123)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(3)
        self.setLayout(self.lay)
        self.wn_picker_empty = MoekButton(self, name="wyr_wn_empty", size=30, checkable=True)
        self.lay.addWidget(self.wn_picker_empty)
        self.wn_picker_empty.clicked.connect(lambda: dlg.mt.init("wn_pick"))
        self.wn_picker_eraser = MoekButton(self, name="wyr_wn", size=30, checkable=False)
        self.lay.addWidget(self.wn_picker_eraser)
        self.wn_picker_eraser.clicked.connect(lambda: self.wn_id_update(None))
        self.idbox = CanvasLineEdit(self, width=90, height=30, max_len=8, validator="id_arkusz", theme="dark", fn=["dlg.wyr_panel.wn_picker.wn_id_update(self.text())"], placeholder="0001_001")
        self.lay.addWidget(self.idbox)
        self.wn_id = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "wn_id":
            self.idbox.set_value(val)
            self.wn_picker_empty.setVisible(False) if val else self.wn_picker_empty.setVisible(True)
            self.wn_picker_eraser.setVisible(True) if val else self.wn_picker_eraser.setVisible(False)

    def wn_id_update(self, id):
        """Sprawdza istnienie wn_id na liście wn_ids i aktualizuje t_wn_id w db, jeśli potrzeba."""
        if id in dlg.obj.wn_ids or not id:
            self.db_update(id)  # Aktualizacja wn_id w db
        dlg.obj.wyr = dlg.obj.wyr  # Aktualizacja danych w wyr_panel

    def db_update(self, id):
        """Aktualizacja atrybutu 't_wn_id' w db."""
        db = PgConn()
        if id:
            sql = f"UPDATE team_{dlg.team_i}.wyrobiska SET t_wn_id = '{id}' WHERE wyr_id = {dlg.obj.wyr}"
        else:
            sql = f"UPDATE team_{dlg.team_i}.wyrobiska SET t_wn_id = Null WHERE wyr_id = {dlg.obj.wyr}"
        if db:
            res = db.query_upd(sql)


class WyrStatusSelector(QFrame):
    """Belka zmiany statusu wyrobiska."""
    def __init__(self, *args, width):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(28)
        self.setFixedWidth(60)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(4)
        self.setLayout(self.lay)
        self.valid_check = False
        self.itms = {}
        self.statuses = [
            {'id' : 1, 'name' : 'wyr_green_status', 'text' : 'WYROBISKO POTWIERDZONE', 'layer': 'wyr_potwierdzone', 'color' : '40, 170, 40', 'after_fchk' : True, 'confirmed' : True},
            {'id' : 2, 'name' : 'wyr_red_status', 'text' : 'WYROBISKO ODRZUCONE', 'layer': 'wyr_odrzucone', 'color' : '224, 0, 0', 'after_fchk' : True, 'confirmed' : False},
            {'id' : 0, 'name' : 'wyr_grey_status', 'text' : 'WYROBISKO PRZED KONTROLĄ', 'layer': 'wyr_przed_teren', 'color' : '153, 153, 153', 'after_fchk' : False, 'confirmed' : False}
            ]
        for status in self.statuses:
            _itm = WyrStatusSelectorItem(self, name=status["name"], size=28, checkable=False, id=status["id"])
            self.lay.addWidget(_itm)
            itm_name = f'btn_{status["name"]}'
            self.itms[itm_name] = _itm

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "case":
            self.case_change()

    def set_case(self, after_fchk, confirmed):
        """Ustala 'case' na podstawie atrybutów wyrobiska."""
        if not after_fchk:
            self.case = 0
        else:
            self.case = 1 if confirmed else 2

    def db_update(self, after_fchk, confirmed):
        """Aktualizacja atrybutów wyrobiska w db po zmianie statusu."""
        db = PgConn()
        sql = f"UPDATE team_{dlg.team_i}.wyrobiska SET b_after_fchk = {after_fchk}, b_confirmed = {confirmed} WHERE wyr_id = {dlg.obj.wyr}"
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
        for itm in self.itms.values():
            itm.setVisible(False) if itm.id == self.case else itm.setVisible(True)
        for status in self.statuses:
            if status["id"] == self.case:
                dlg.wyr_panel.status_indicator.set_case(status["text"], status["color"])
                dlg.wyr_panel.sb.setCurrentIndex(status["id"])

    def btn_clicked(self, id):
        """Zmiana wartości 'case' i aktualizacja db po naciśnięciu przycisku."""
        self.case = id
        for status in self.statuses:
            if status["id"] == self.case:
                result = self.db_update(status["after_fchk"], status["confirmed"])
                if result:
                    self.vis_check(status["layer"])
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


class KopalinaWiekBox(QFrame):
    """Widget ustalania dla wyrobiska kopalin i ich wieku."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(266, 62)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.df_kopalina = self.sl_pd_load("sl_kopalina")
        self.df_wiek = self.sl_pd_load("sl_wiek")
        self.plus_btn = MoekButton(self, name="kw_plus", size=17)
        self.plus_btn.clicked.connect(self.plus_clicked)
        self.minus_btn = MoekButton(self, name="kw_minus", size=17)
        self.minus_btn.clicked.connect(self.minus_clicked)
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
                height = 23
                value = " "
            else:
                fn = None
                height = 1
                value = None
            _cmb = ParamBox(self, item="combo_tv", height=height, width=dict["width"], value=value, val_width=dict["width"], title_down=dict["title_down"], val_display=dict["val_display"], fn=fn)
            exec(f'{dict["name"]} = _cmb')
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
            ["self.k1_val", self.k1_val, self.kopalina_1.valbox_1.data_val, "t_kopalina"],
            ["self.k2_val", self.k2_val, self.kopalina_2.valbox_1.data_val, "t_kopalina_2"],
            ["self.w1_val", self.w1_val, self.wiek_1.valbox_1.data_val, "t_wiek"],
            ["self.w2_val", self.w2_val, self.wiek_2.valbox_1.data_val, "t_wiek_2"]
        ]
        for cmb_val in cmb_vals:
            new_val = None if cmb_val[2] == 'Null' else cmb_val[2][1:-1]
            if cmb_val[1] != new_val:
                print(f"{cmb_val[0]}: {cmb_val[1]} -> {cmb_val[2]}")
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
            if len(df) > 0:
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
            return temp_df

    def plus_clicked(self):
        """Akcja po naciśnięciu przycisku 'plus_btn'."""
        self.composer(add_second=True)

    def minus_clicked(self):
        """Akcja po naciśnięciu przycisku 'minus_btn'."""
        self.k2_val = None
        self.w2_val = None
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr='t_kopalina_2', val='Null', sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        db_attr_change(tbl=f'team_{dlg.team_i}.wyr_dane', attr='t_wiek_2', val='Null', sql_bns=f' WHERE wyr_id = {dlg.obj.wyr}', user=False)
        self.composer()

    def composer(self, add_second=False):
        """Ustalenie rozmieszczenia i widoczności widget'ów."""
        if self.k2_val or self.w2_val or add_second:  # Druga kopalina (lub wiek) jest ustalona albo przycisk plusa został naciśnięty
            self.kopalina_1.setGeometry(0, 0, self.kopalina_1.width(), self.kopalina_1.height())
            self.wiek_1.setGeometry(181, 0, self.wiek_1.width(), self.wiek_1.height())
            self.kopalina_2.setGeometry(0, 24, self.kopalina_2.width(), self.kopalina_2.height())
            self.wiek_2.setGeometry(181, 24, self.wiek_2.width(), self.wiek_2.height())
            self.kopalina_title.setGeometry(0, 47, self.kopalina_title.width(), self.kopalina_title.height())
            self.wiek_title.setGeometry(181, 47, self.wiek_title.width(), self.wiek_title.height())
            self.minus_btn.setGeometry(249, 27, self.minus_btn.width(), self.minus_btn.height())
            self.kopalina_2.setVisible(True)
            self.wiek_2.setVisible(True)
            self.plus_btn.setVisible(False)
            self.minus_btn.setVisible(True)
        else:
            self.kopalina_1.setGeometry(0, 24, self.kopalina_1.width(), self.kopalina_1.height())
            w = 66 if self.k1_val else 85
            self.wiek_1.setFixedWidth(w)
            self.wiek_title.setFixedWidth(w)
            self.wiek_1.setGeometry(181, 24, self.wiek_1.width(), self.wiek_1.height())
            self.wiek_title.setGeometry(181, 47, self.wiek_title.width(), self.wiek_title.height())
            self.kopalina_title.setGeometry(0, 47, self.kopalina_title.width(), self.kopalina_title.height())
            self.plus_btn.setGeometry(249, 27, self.plus_btn.width(), self.plus_btn.height())
            self.kopalina_2.setVisible(False)
            self.wiek_2.setVisible(False)
            self.plus_btn.setVisible(True) if self.k1_val else self.plus_btn.setVisible(False)
            self.minus_btn.setVisible(False)

class FlagTools(QFrame):
    """Menu przyborne dla flag."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(104, 34)
        self.setObjectName("main")
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.flag_move = MoekButton(self, name="move", size=34, checkable=True)
        self.flag_chg = MoekButton(self, name="flag_chg_nfchk", size=34)
        self.flag_del = MoekButton(self, name="trash", size=34)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(1)
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
            self.flag_chg.set_icon(name="flag_chg_nfchk", size=34) if val else self.flag_chg.set_icon(name="flag_chg_fchk", size=34)

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
        self.setFixedSize(104, 34)
        self.setObjectName("main")
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.parking_chg = MoekButton(self, name="parking_before", size=34)
        self.parking_move = MoekButton(self, name="move", size=34, checkable=True)
        self.parking_del = MoekButton(self, name="trash", size=34)
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
            self.parking_chg.set_icon(name="parking_before", size=34) if val == 0 else self.parking_chg.set_icon(name="parking_after", size=34)

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


class ParamBox(QFrame):
    """Widget do wyświetlania wartości lub zakresu parametru wraz z opisem (nagłówkiem).
    item: label, line_edit, ruler."""
    def __init__(self, *args, margins=False, width=160, height=24, item="label", val_width=40, val_width_2=40, value=" ", value_2=None, sep_width=17, sep_txt="–", max_len=None, validator=None, placeholder=None, zero_allowed=False, title_down=None, title_down_2=None, title_left=None, icon=None, tooltip="", val_display=False, fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.item = item
        self._width = width
        self._height = height if not margins else height + 8
        self.height_1 = height if not margins else height
        self.val_width = val_width + val_width_2 + sep_width if value_2 else val_width
        self.val_width_1 = val_width if title_left or icon else self._width
        _height = self._height + 10 if title_down else self._height
        self.setFixedSize(width, _height)
        self.setStyleSheet(" QFrame {background-color: transparent; border: none} ")
        lay = QVBoxLayout()
        self.box = MoekGridBox(self, margins=[0, 0, 0, 0], spacing=0)
        lay.addWidget(self.box)
        lay.setContentsMargins(0, 4, 0, 4) if margins else lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.setLayout(lay)
        self.widgets = self.composer(value, value_2, title_left, title_down, icon)
        for widget in self.widgets:
            if widget["item"] == "title_left":
                _width = self._width - self.val_width
                self.title_left = TextItemLabel(self, height=self.height_1, width=_width, font_size=8, text=title_left)
                self.box.glay.addWidget(self.title_left, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "icon":
                self.icon = MoekButton(self, name=icon, size=34, checkable=False, enabled=False, tooltip=tooltip)
                self.box.glay.addWidget(self.icon, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "valbox_1":
                if self.item == "label":
                    self.valbox_1 = TextItemLabel(self, height=self._height, width=self.val_width_1, bgr_alpha=0.15, text=value)
                elif self.item == "line_edit":
                    self.valbox_1 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, fn=fn[0])
                elif self.item == "ruler":
                    self.valbox_1 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, r_widget="ruler", max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, fn=fn[0])
                elif self.item == "combo":
                    self.valbox_1 = CanvasArrowlessComboBox(self, border=0, height=23, font_size=8, fn=fn)
                elif self.item == "combo_tv":
                    self.valbox_1 = CanvasArrowlessComboBox(self, border=0, height=23, font_size=8, tv=True, val_display=val_display, fn=fn)
                self.box.glay.addWidget(self.valbox_1, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "valbox_2":
                if self.item == "label":
                    self.valbox_2 = TextItemLabel(self, height=self._height, width=self.val_width_1, bgr_alpha=0.15, text=value)
                elif self.item == "line_edit":
                    self.valbox_2 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, fn=fn[1])
                elif self.item == "ruler":
                    self.valbox_2 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, r_widget="ruler", max_len=max_len, validator=validator, placeholder=placeholder, zero_allowed=zero_allowed, fn=fn[1])
                self.box.glay.addWidget(self.valbox_2, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "separator":
                self.separator = TextItemLabel(self, height=self.height_1, width=sep_width, text=sep_txt)
                self.box.glay.addWidget(self.separator, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "line":
                self.line = MoekHLine(self)
                self.box.glay.addWidget(self.line, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "titlebox_1":
                self.titlebox_1 = TextItemLabel(self, height=10, width=self.val_width_1, align="left", font_size=6, font_weight="bold", font_alpha=0.6, text=title_down)
                self.box.glay.addWidget(self.titlebox_1, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "titlebox_2":
                self.titlebox_2 = TextItemLabel(self, height=10, align="left", width=val_width_2, font_size=6, font_weight="bold", font_alpha=0.6, text=title_down_2)
                self.box.glay.addWidget(self.titlebox_2, widget["row"], widget["col"], widget["r_span"], widget["c_span"])

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
        return widgets

    def value_change(self, attrib, val):
        """Zmienia wyświetlaną wartość parametru."""
        if attrib == "value":
            if isinstance(self.valbox_1, CanvasLineEdit):
                self.valbox_1.set_value(val)
            elif isinstance(self.valbox_1, CanvasArrowlessComboBox):
                self.valbox_1.set_value(val)
            else:
                self.valbox_1.setText(str(val)) if val else self.valbox_1.setText("")
        elif attrib == "value_2":
            if isinstance(self.valbox_2, CanvasLineEdit):
                self.valbox_2.set_value(val)
            else:
                self.valbox_2.setText(str(val)) if val else self.valbox_2.setText("")


class ParamTextBox(QFrame):
    """Widget do wyświetlania parametru tekstowego (np. uwagi) wraz z nagłówkiem."""
    def __init__(self, *args, width=328, height=80, title=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.width = width
        self.height = height
        _height = self.height + 10 if title else self.height
        self.setFixedSize(width, _height)
        self.vlay = QVBoxLayout()
        self.vlay.setContentsMargins(0, 0, 0, 0)
        self.vlay.setSpacing(0)
        self.setLayout(self.vlay)
        self.txtbox = TextViewer(self, height=self.height, width=self.width)
        self.vlay.addWidget(self.txtbox)
        self.line = MoekHLine(self)
        self.vlay.addWidget(self.line)
        if title:
            self.titlebox = TextItemLabel(self, height=10, width=self.width, align="left", font_size=6, font_weight="bold", font_alpha=0.6, text=title)
            self.vlay.addWidget(self.titlebox)
        self.setStyleSheet(" QFrame {background-color: transparent; border: none} ")

    def value_change(self, value):
        """Zmienia wyświetlany tekst."""
        self.txtbox.setPlainText(value) if value else self.txtbox.clear()


class TextViewer(QPlainTextEdit):
    """Wyświetla tekst bez możliwości edycji."""
    def __init__(self, *args, width, height):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setBackgroundVisible(False)
        self.setReadOnly(True)
        self.setStyleSheet("QPlainTextEdit {background-color: rgba(255, 255, 255, 0.1); color: white; font-size: 8pt; padding: 0px 0px 0px 0px}")


class TextItemLabel(QLabel):
    """Widget do wyświetlania nagłówka parametru obiektu."""
    def __init__(self, *args, width=118, height=24, text="", align="center", font_size=10, font_weight="normal", font_alpha=1.0, bgr_alpha=0.0):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setText(text)
        if align == "center":
            self.setAlignment(Qt.AlignCenter)
            self.setStyleSheet(f" background-color: rgba(255, 255, 255, {bgr_alpha}); color: rgba(255, 255, 255, {font_alpha}); font-size: {font_size}pt; font-weight: {font_weight}; padding: 0px 0px 0px 0px ")
        elif align == "left":
            self.setAlignment(Qt.AlignLeft)
            self.setStyleSheet(f" background-color: rgba(255, 255, 255, {bgr_alpha}); color: rgba(255, 255, 255, {font_alpha}); font-size: {font_size}pt; font-weight: {font_weight}; padding: 0px 6px 0px 0px ")


class MoekHLine(QFrame):
    """Linia pozioma."""
    def __init__(self, *args, px=1):
        super().__init__(*args)
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(px)
        self.setStyleSheet("QFrame {background-color: rgba(255, 255, 255, 0.6)}")


class IdSpinBox(QFrame):
    """Widget z centralnie umieszczonym labelem i przyciskami zmiany po jego obu stronach."""
    def __init__(self, *args, _obj, width=90, height=34, max_len=4, validator="id", theme="dark"):
        super().__init__(*args)
        self.obj = _obj
        self.max_len = max_len
        self.validator = validator
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.prev_btn = MoekButton(self, name=f"id_prev_{theme}", size=22, hsize=34, checkable=False)
        self.prev_btn.clicked.connect(self.prev_clicked)
        self.next_btn = MoekButton(self, name=f"id_next_{theme}", size=22, hsize=34, checkable=False)
        self.next_btn.clicked.connect(self.next_clicked)
        fn = ['dlg.obj.set_object_from_input(self.text(), self.parent().obj)']
        self.idbox = CanvasLineEdit(self, width=self.width() - 44, height=self.height() - 4, max_len=self.max_len, validator=self.validator, null_allowed=False, fn=fn, theme=theme)
        self.setStyleSheet(" QFrame#main {background-color: transparent; border: none} ")
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(0)
        self.hlay.addWidget(self.prev_btn)
        self.hlay.addWidget(self.idbox)
        self.hlay.addWidget(self.next_btn)
        self.setLayout(self.hlay)
        self.id = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "id":
            self.idbox.set_value(str(val))

    def prev_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk prev_btn."""
        dlg.obj.object_prevnext(self.obj, False)

    def next_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk next_bnt."""
        dlg.obj.object_prevnext(self.obj, True)


class CanvasLineEdit(QLineEdit):
    """Lineedit z odpalaniem funkcji po zatwierdzeniu zmian tekstu."""
    def __init__(self, *args, width, height, r_widget=None, font_size=12, max_len=None, validator=None, placeholder=None, zero_allowed=False, null_allowed=True, theme="dark", fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setFrame(False)
        self.font_size = font_size
        self.r_widget = r_widget
        if self.r_widget == "ruler":
            self.r_widget = MoekSlideButton(self, name="ruler", size=24, checkable=True)
        self.max_len = max_len
        if max_len:
            self.setMaxLength(max_len)
        self.validator = validator
        if self.validator == "id":
            self.setValidator(QRegExpValidator(QRegExp("[1-9][0-9]*") ))
        elif self.validator == "id_arkusz":
            self.setValidator(QRegExpValidator(QRegExp("[0-1]([0-9]|[_])*") ))
        elif self.validator == "000":
            self.setValidator(QRegExpValidator(QRegExp("[0-9]*") ))
        elif self.validator == "00.0":
            self.setValidator(QRegExpValidator(QRegExp("([0-9]|[,]|[.])*") ))
        self.color = "255, 255, 255" if theme == "dark" else "0, 0, 0"
        self.fn = fn
        self.placeholder = placeholder
        self.zero_allowed = zero_allowed
        self.null_allowed = null_allowed
        self.mt_enabled = False
        self.focused = False
        self.hover = False
        self.temp_val = None
        self.pressed = False
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

    def set_value(self, val):
        """Próba zmiany wartości."""
        if len(str(val)) == 0:  # Wartość Null
            self.cur_val = None if self.null_allowed else self.cur_val
            return
        if self.validator == '00.0' or self.validator == '000':
            # Próba konwersji tekstu na wartość float:
            num_val = self.numeric_formater(val)
            self.numerical = True if num_val != -1 else False
            if num_val != -1:
                self.cur_val = str(num_val)
            else:
                self.cur_val = self.cur_val
        else:
            self.cur_val = val

    def value_changed(self):
        """Aktualizacja tekstu lineedit'u po zmianie wartości."""
        self.set_grey()
        self.setText(self.placeholder) if self.placeholder and self.cur_val == None else self.setText(self.cur_val)

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
        alpha = 0.3 if self.hover else 0.2
        if self.placeholder:
            font_color = "0, 0, 0, 0.3" if self.grey else self.color
        else:
            font_color = self.color
        self.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(""" + self.color + """, """ + str(alpha) + """);
                        color: rgba(""" + font_color + """);
                        font-size: """ + str(self.font_size) + """pt;
                        border: none;
                        padding: 0px 0px 2px 2px;
                        qproperty-alignment: AlignCenter;
                        }
                    """)

    def enterEvent(self, event):
        super().enterEvent(event)
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
        self.set_value(self.text())
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
        self.set_style(0.8)

    def page_change(self, index):
        """Zmiana aktywnej strony stackedbox'a."""
        self.cur_page = index
        alpha = 0.4 if index > 0 else 0.8
        self.set_style(alpha)  # Ustalenie przezroczystości tła seq_dock'a
        self.height_change()  # Aktualizacja wysokości dock'u

    def set_style(self, alpha):
        """Zmiana przezroczystości tła w zależności od aktualnej strony stackedbox'a."""
        self.setStyleSheet("""
            QFrame#main{background-color: rgba(0, 0, 0, """ + str(alpha) + """); border: none}
            QFrame#box{background-color: transparent; border: none}
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
        print(f'seq_ge: {self.sqb_btns["sqb_" + str(self.num)].ge}, is_ge: {dlg.ge.is_ge}')
        if self.sqb_btns["sqb_" + str(self.num)].ge:  # W sekwencji jest Google Earth Pro
            print(f"+++++++++++++++++++++++++  1  +++++++++++++++++++++++++++++")
            dlg.ge.q2ge(player=True, back=True)
        elif dlg.ge.is_ge:  # Google Earth Pro jest włączony
            print(f"+++++++++++++++++++++++++  2  +++++++++++++++++++++++++++++")
            dlg.ge.q2ge(player=True, back=True)
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
                        QFrame#main {background-color: rgba(0, 0, 0, 0.8); border: none}
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
                               QFrame#box {background-color: rgba(0, 0, 0, 0.8); border: none}
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
                                background-color: rgba(255, 255, 255, 0.6);
                            }
                            QScrollBar:vertical {
                                border: 0px solid #999999;
                                background: transparent;
                                width: 14px;
                                margin: 4px 3px 4px 3px;
                            }
                            QScrollBar::handle:vertical {
                                min-height: 30px;
                                border: 0px solid red;
                                border-radius: 4px;
                                background-color: rgba(0, 0, 0, 0.6);
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
    def __init__(self, *args, margins=[4, 2, 4, 4], spacing=0, theme=None):
        super().__init__(*args)
        self.setObjectName("gbox")
        # self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        alpha = 0.0 if not theme else 0.8
        self.setStyleSheet("""
                    QFrame#gbox{background-color: rgba(0, 0, 0 , """ + str(alpha) + """); border: none}
                    """)
        self.glay = QGridLayout()
        self.glay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.glay.setSpacing(spacing)
        self.setLayout(self.glay)


class MoekHBox(QFrame):
    """Zawartość panelu w kompozycji QHBoxLayout."""
    def __init__(self, *args, margins=[0, 0, 0, 0], spacing=0):
        super().__init__(*args)
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.lay.setSpacing(spacing)
        self.setLayout(self.lay)


class MoekVBox(QFrame):
    """Zawartość toolbox'a w kompozycji QVBoxLayout."""
    def __init__(self, *args, margins=[0, 0, 0, 0], spacing=0):
        super().__init__(*args)
        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.lay = QVBoxLayout()
        self.lay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.lay.setSpacing(spacing)
        self.setLayout(self.lay)


class MoekStackedBox(QStackedWidget):
    """Widget dzielący zawartość panelu na strony."""
    def __init__(self, *args):
        super().__init__(*args)

    def minimumSizeHint(self):
        self.setMinimumHeight(self.currentWidget().minimumSizeHint().height())
        self.setMaximumHeight(self.currentWidget().minimumSizeHint().height())
        return self.currentWidget().minimumSizeHint()


class MoekButton(QToolButton):
    """Fabryka guzików."""
    def __init__(self, *args, size=25, hsize=0, name="", icon="", visible=True, enabled=True, checkable=False, tooltip=""):
        super().__init__(*args)
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
        self.setCursor(Qt.ArrowCursor)

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
        self.slided = True

    def leaveEvent(self, event):
        self.slided = False


class MoekDummy(QFrame):
    """Pusty obiekt zajmujący określoną przestrzeń."""
    def __init__(self, *args, width, height):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.box = MoekHBox(self)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
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
        painter.fillPath(path, QColor(0, 0, 0, 153))
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

        self.setStyleSheet("""
                            QComboBox {
                                border: """ + str(border) + """px solid rgb(52, 132, 240);
                                """ + B_CSS + """
                                padding: 0px 5px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                color: rgb(52, 132, 240);
                                font-size: 8pt;
                            }
                            QComboBox:disabled {
                                border: """ + str(border) + """px solid rgb(150, 150, 150);
                                """ + B_CSS + """
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
                            QComboBox::item:selected {
                                padding-left: 0px;
                                background-color: rgb(52, 132, 240);
                                color: white;
                            }
                            QComboBox::item:!selected {
                                background-color: white;
                                color: rgb(52, 132, 240);
                            }
                            QComboBox:on {
                                padding-top: 3px;
                                padding-left: 4px;
                                background-color: rgb(52, 132, 240);
                                color: white;
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
                                background-color: white;
                            }
                            QComboBox QAbstractItemView::item {
                                padding-top: 3px;
                                padding-left: 4px;
                                border: """ + str(border) + """px solid rgb(52, 132, 240);
                                background-color: white;
                            }
                           """)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_NoSystemBackground | Qt.WA_TranslucentBackground | Qt.WA_PaintOnScreen)


class CanvasArrowlessComboBox(QComboBox):
    """Fabryka rozwijanych bez strzałki."""
    def __init__(self, *args, name="", height=24, border=1, font_size=8, icon_disable=False, b_round="none", tv=False, val_display=False, fn=None):
        super().__init__(*args)
        if b_round == "right":
            B_CSS = "border-top-right-radius: 3px; border-bottom-right-radius: 3px;"
        elif b_round == "all":
            B_CSS = "border-radius: 6px;"
        else:
            B_CSS = ""
        if icon_disable:
            icon = "none"
            icon_dis = "none"
        else:
            icon_path_txt = ICON_PATH.replace("\\", "/")
            icon = f"url('{icon_path_txt}down_arrow_dark.png')"
            icon_dis = f"url('{icon_path_txt}down_arrow_dark_dis.png')"
        self.setFixedHeight(height)
        self.data_val = None
        self.val_display = val_display
        self.fn = fn
        if tv:
            popup = 0
            self.setMaxVisibleItems(20)
            model = QStandardItemModel()
            self.setModel(model)
            de = CmbDelegate(self)
            self.view().setItemDelegate(de)
            self.view().setFixedWidth(200)
        else:
            popup = 1
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
                                combobox-popup: """ + str(popup) + """;
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
                            QComboBox::item:selected {
                                min-height: 34px;
                                padding-left: 0px;
                                background-color: rgba(255, 255, 255, 0.8);
                                color: black;
                            }
                            QComboBox::item:!selected {
                                min-height: 34px;
                                background-color: rgba(255, 255, 255, 0.2);
                                color: white;
                            }
                            QComboBox::indicator {
                                background-color:transparent;
                                selection-background-color:transparent;
                                color:transparent;
                                selection-color:transparent;
                            }
                            QComboBox:on {
                                padding-top: 3px;
                                padding-left: 4px;
                                background-color: rgba(255, 255, 255, 0.2);
                                color: black;
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
                            QComboBox QAbstractItemView {
                                border: """ + str(border) + """px solid rgb(255, 255, 255);
                                background-color: transparent;
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
                                    color: white;
                                    background-color: transparent;
                                }
                                QListView::item:hover{
                                    color: black;
                                    background-color: rgb(204, 204, 204);
                                }
                                QListView::item:selected {
                                    padding-left: 0px;
                                    color: black;
                                    background-color: rgb(204, 204, 204);
                                }
                                QListView::item:!selected {
                                    background-color: transparent;
                                    color: white;
                                }
                                QScrollBar:vertical {
                                    border: 0px solid #999999;
                                    background:transparent;
                                    width: 14px;
                                    margin: 4px 3px 4px 3px;
                                }
                                QScrollBar::handle:vertical {
                                    min-height: 30px;
                                    border: 0px solid red;
                                    border-radius: 4px;
                                    background-color: rgba(255, 255, 255, 0.6);
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
        else:
            self.view().window().setStyleSheet("background-color: rgba(0, 0, 0, 0.0)")

    def paintEvent(self, event):
        p = QPainter()
        p.begin(self)
        option = QStyleOptionComboBox()
        option.initFrom(self)
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        if option.state & QStyle.State_MouseOver:
            brush.setColor(QColor(255, 255, 255, 75))
        elif option.state & ~QStyle.State_MouseOver:
            brush.setColor(QColor(255, 255, 255, 50))
        p.fillRect(self.rect(), brush)
        style = QApplication.style()
        if self.val_display:
            text = "" if self.itemData(self.currentIndex()) == None else self.itemData(self.currentIndex())
        else:
            text = self.currentText()
        style.drawItemText(p, self.rect(), Qt.AlignCenter, self.palette(), self.isEnabled(), text)
        p.end()

    def set_value(self, val):
        """Ustawienie aktualnej wartości z db."""
        # Próba (bo może być jeszcze nie podłączony) odłączenia sygnału zmiany aktualnego indeksu combobox'a:
        self.signal_off()
        if val and len(val) == 0:  # Wartość Null
            val = None
        idx = self.findData(val, flags=Qt.MatchExactly)
        if idx >= 0:
            self.setCurrentIndex(idx)
            self.index_changed(idx, True)
        # Ponowne podpięcie sygnału zmiany indeksu:
        self.currentIndexChanged.connect(self.index_changed)

    def index_changed(self, index, fn_void=False):
        """Zmiana wartości przez użytkownika."""
        if self.itemData(index) == None:
            self.data_val = "Null"
        else:
            self.data_val = f"'{self.itemData(index)}'"
        if self.fn and not fn_void:
            self.run_fn()

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
        icon_path_txt = ICON_PATH.replace("\\", "/")
        icon = f"url('{icon_path_txt}down_arrow_dark.png')"
        icon_dis = f"url('{icon_path_txt}down_arrow_dark_dis.png')"

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
                                background-color: rgba(255, 255, 255, 0.8);
                                color: black;
                            }
                            QComboBox::item:!selected {
                                min-height: 34px;
                                background-color: rgba(255, 255, 255, 0.2);
                                color: white;
                            }
                            QComboBox:on {
                                padding-top: 3px;
                                padding-left: 4px;
                                background-color: rgba(255, 255, 255, 0.2);
                                color: black;
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
                                image: """ + icon + """);
                            }
                            QComboBox::down-arrow:disabled {
                                image: """ + icon_dis + """);
                            }
                            QComboBox QAbstractItemView {
                                border: """ + str(border) + """px solid rgb(255, 255, 255);
                                background-color: transparent;
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


class PanelLabel(QLabel):
    """Fabryka napisów do canvpaneli."""
    def __init__(self, *args, text="", color="255, 255, 255", size=10):
        super().__init__(*args)
        self.setWordWrap(False)
        self.setStyleSheet("QLabel {color: rgb(" + color + "); font-size: " + str(size) + "pt; qproperty-alignment: AlignCenter}")
        self.setText(text)


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
