# -*- coding: utf-8 -*-
import os
import pandas as pd

from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter
from qgis.PyQt.QtWidgets import QWidget, QMessageBox, QFrame, QToolButton, QPushButton, QComboBox, QLineEdit, QPlainTextEdit, QCheckBox, QLabel, QProgressBar, QStackedWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect, QTableView, QAbstractItemView
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal, QRegExp
from qgis.PyQt.QtGui import QIcon, QColor, QFont, QPainter, QPixmap, QPainterPath, QRegExpValidator
from qgis.utils import iface

from .main import db_attr_change, vn_cfg, vn_setup_mode, powiaty_mode_changed, vn_mode_changed, get_wyr_ids, get_flag_ids, get_parking_ids, get_marsz_ids, wyr_layer_update, wn_layer_update, marsz_layer_update, file_dialog
from .sequences import MoekSeqBox, MoekSeqAddBox, MoekSeqCfgBox
from .classes import PgConn, CfgPars, WDfModel

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
        self.setFixedWidth(500)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.heights = [268, 400, 225]
        self.mt_enabled = False
        self.cur_page = int()
        self.bar = CanvasPanelTitleBar(self, title="Wyrobiska", width=self.width())
        self.list_box = MoekVBox(self, spacing=1)
        self.list_box.setFixedWidth(96)
        self.sp_id = CanvasHSubPanel(self, height=34, margins=[0, 0, 0, 0], color="255, 255, 255", alpha=0.8)
        self.list_box.lay.addWidget(self.sp_id)
        self.id_box = IdSpinBox(self, _obj="wyr", theme="light")
        self.sp_id.lay.addWidget(self.id_box)
        self.tv_wdf = MoekTableView(self)
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
        self.sb.setFixedWidth(402)
        self.box.lay.addWidget(self.sb)
        self.pages = {}
        self.widgets = {}
        for p in range(3):
            _page = MoekGridBox(self, margins=[4, 4, 4, 2], spacing=1, theme="dark")
            page_id = f'page_{p}'
            self.pages[page_id] = _page
            self.sb.addWidget(_page)
        self.sb.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.sb.currentChanged.connect(self.page_change)
        self.height_change()  # Wstępne ustalenie wysokości panelu
        self.dicts = [
                    {"name": "okres_eksp_0", "page": 0, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "width": 386, "val_width": 120, "val_width_2": 120, "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji:", "icon": None, "tooltip": "", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_od", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)', 'db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_do", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)']},

                    {"name": "notepad_0", "page": 0, "row": 1, "col": 0, "r_span": 1, "c_span": 12, "type": "notepad"},


                    {"name": "okres_eksp_1", "page": 1, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "text_2", "item": "line_edit", "max_len": None, "validator": None, "placeholder": None, "width": 386, "val_width": 120, "val_width_2": 120, "title_down": "OD", "title_down_2": "DO", "title_left": "Okres eksploatacji:", "icon": None, "tooltip": "", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_od", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)', 'db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="t_wyr_do", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False, quotes=True)']},

                    {"name": "dlug_1", "page": 1, "row": 1, "col": 0, "r_span": 1, "c_span": 4, "type": "text_2", "item": "ruler", "max_len": 3, "validator": "000", "placeholder": "000", "width": 123, "val_width": 34, "val_width_2": 34, "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_dlug", "tooltip": "długość wyrobiska", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_dlug_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_dlug_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "szer_1", "page": 1, "row": 1, "col": 4, "r_span": 1, "c_span": 4, "type": "text_2", "item": "ruler", "max_len": 3, "validator": "000", "placeholder": "000", "width": 123, "val_width": 34, "val_width_2": 34, "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_szer", "tooltip": "szerokość wyrobiska", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_szer_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="i_szer_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "wys_1", "page": 1, "row": 1, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 4, "validator": "00.0", "placeholder": "0.0", "width": 123, "val_width": 34, "val_width_2": 34, "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_wys", "tooltip": "wysokość wyrobiska", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_wys_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_wys_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "nadkl_1", "page": 1, "row": 2, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 3, "validator": "00.0", "placeholder": "0.0", "width": 123, "val_width": 34, "val_width_2": 34, "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_nadkl", "tooltip": "grubość nadkładu", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_nadkl_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_nadkl_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "miaz_1", "page": 1, "row": 3, "col": 8, "r_span": 1, "c_span": 4, "type": "text_2", "item": "line_edit", "max_len": 3, "validator": "00.0", "placeholder": "0.0", "width": 123, "val_width": 34, "val_width_2": 34, "title_down": "MIN", "title_down_2": "MAX", "title_left": None, "icon": "wyr_miaz", "tooltip": "miąższość kopaliny", "fn": ['db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_miazsz_min", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)', 'db_attr_change(tbl="team_{dlg.team_i}.wyr_dane", attr="n_miazsz_max", val="'"{self.text()}"'", sql_bns=" WHERE wyr_id = {dlg.obj.wyr}", user=False)']},

                    {"name": "notepad_1", "page": 1, "row": 4, "col": 0, "r_span": 1, "c_span": 12, "type": "notepad"},


                    {"name": "notepad_2", "page": 2, "row": 0, "col": 0, "r_span": 1, "c_span": 12, "type": "notepad"}
                    ]
        for dict in self.dicts:
            if dict["type"] == "text_2":
                _txt2 = ParamBox(self, margins=True, item=dict["item"], max_len=dict["max_len"], validator=dict["validator"], placeholder=dict["placeholder"], width=dict["width"], value_2=" ", val_width=dict["val_width"], val_width_2=dict["val_width_2"], title_down=dict["title_down"], title_down_2=dict["title_down_2"], title_left=dict["title_left"], icon=dict["icon"], tooltip=dict["tooltip"], fn=dict["fn"])
                exec(f'self.pages["page_{dict["page"]}"].glay.addWidget(_txt2, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                txt2_name = f'txt2_{dict["name"]}'
                self.widgets[txt2_name] = _txt2
            elif dict["type"] == "notepad":
                _np = TextPadBox(self, height=110, obj="wyr", width=392)
                exec(f'self.pages["page_{dict["page"]}"].glay.addWidget(_np, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
                np_name = f'np_{dict["name"]}'
                self.widgets[np_name] = _np

    def values_update(self, _dict):
        """Aktualizuje wartości parametrów."""
        params = [
            {'type': 'notepad', 'value': _dict[7], 'pages': [0, 1, 2]},
            {'type': 'text_2', 'name': 'okres_eksp', 'value': _dict[5], 'value_2': _dict[6], 'pages': [0, 1]},
            {'type': 'text_2', 'name': 'dlug', 'value': _dict[8], 'value_2': _dict[9], 'pages': [1]},
            {'type': 'text_2', 'name': 'szer', 'value': _dict[10], 'value_2': _dict[11], 'pages': [1]},
            {'type': 'text_2', 'name': 'wys', 'value': _dict[12], 'value_2': _dict[13], 'pages': [1]},
            {'type': 'text_2', 'name': 'nadkl', 'value': _dict[14], 'value_2': _dict[15], 'pages': [1]},
            {'type': 'text_2', 'name': 'miaz', 'value': _dict[16], 'value_2': _dict[17], 'pages': [1]}
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

    def param_parser(self, val, quote=False):
        """Zwraca wartość przerobioną na tekst (pusty, jeśli None)."""
        if quote:
            txt = f'"{val}"' if val else f'""'
        else:
            txt = f'{val}' if val else f''
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
        self.idbox = CanvasLineEdit(self, width=90, height=30, max_len=8, validator="id_arkusz", theme="dark", fn="dlg.wyr_panel.wn_picker.wn_id_update(self.text())", placeholder="0001_001")
        self.lay.addWidget(self.idbox)
        self.wn_id = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "wn_id":
            self.idbox.setText(val) if val else self.idbox.setText("")
            self.wn_picker_empty.setVisible(False) if val else self.wn_picker_empty.setVisible(True)
            self.wn_picker_eraser.setVisible(True) if val else self.wn_picker_eraser.setVisible(False)
            self.idbox.text_changed()

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
    def __init__(self, *args, margins=False, width=160, height=24, item="label", val_width=40, val_width_2=40, value="", value_2=None, max_len=None, validator=None, placeholder=None, title_down=None, title_down_2=None, title_left=None, icon=None, tooltip="", fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.item = item
        self.width = width
        self.height = height if not margins else height + 8
        self.height_1 = height if not margins else height
        self.val_width = val_width + val_width_2 + 19 if value_2 else val_width
        self.val_width_1 = val_width if title_left or icon else self.width
        _height = self.height + 10 if title_down else self.height
        self.setFixedSize(width, _height)
        self.setStyleSheet(" QFrame {background-color: transparent; border: none} ")
        lay = QVBoxLayout()
        self.box = MoekGridBox(self, margins=[0, 0, 0, 0], spacing=0) # if margins else MoekGridBox(self, margins=[0, 0, 0, 0], spacing=0)
        lay.addWidget(self.box)
        lay.setContentsMargins(0, 4, 0, 4) if margins else lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.setLayout(lay)
        self.widgets = self.compositor(title_left, value_2, title_down, icon)
        for widget in self.widgets:
            if widget["item"] == "title_left":
                _width = self.width - self.val_width
                self.title_left = TextItemLabel(self, height=self.height_1, width=_width, font_size=8, text=title_left)
                self.box.glay.addWidget(self.title_left, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "icon":
                self.icon = MoekButton(self, name=icon, size=34, checkable=False, enabled=False, tooltip=tooltip)
                self.box.glay.addWidget(self.icon, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "valbox_1":
                if self.item == "label":
                    self.valbox_1 = TextItemLabel(self, height=self.height, width=self.val_width_1, bgr_alpha=0.15, text=value)
                elif self.item == "line_edit":
                    self.valbox_1 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, max_len=max_len, validator=validator, placeholder=placeholder, fn=fn[0])
                elif self.item == "ruler":
                    self.valbox_1 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, r_widget="ruler", max_len=max_len, validator=validator, placeholder=placeholder, fn=fn[0])
                self.box.glay.addWidget(self.valbox_1, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "valbox_2":
                if self.item == "label":
                    self.valbox_2 = TextItemLabel(self, height=self.height, width=self.val_width_1, bgr_alpha=0.15, text=value)
                elif self.item == "line_edit":
                    self.valbox_2 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, max_len=max_len, validator=validator, placeholder=placeholder, fn=fn[1])
                elif self.item == "ruler":
                    self.valbox_2 = CanvasLineEdit(self, width=self.val_width_1, height=self.height_1, font_size=8, r_widget="ruler", max_len=max_len, validator=validator, placeholder=placeholder, fn=fn[1])
                self.box.glay.addWidget(self.valbox_2, widget["row"], widget["col"], widget["r_span"], widget["c_span"])
            elif widget["item"] == "separator":
                self.separator = TextItemLabel(self, height=self.height_1, width=17, text="–")
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

    def compositor(self, title_left, value_2, title_down, icon):
        """Zwraca listę z ustawieniami kompozycji widgetów, w zależności od parametrów."""
        comp_val = 0
        comp_val = comp_val + 1 if title_left else comp_val
        comp_val = comp_val + 2 if value_2 else comp_val
        comp_val = comp_val + 4 if title_down else comp_val
        comp_val = comp_val + 8 if icon else comp_val
        if comp_val == 4:
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 1, "col": 0, "r_span": 1, "c_span": 1, "item": "line"},
                {"row": 2, "col": 0, "r_span": 1, "c_span": 1, "item": "titlebox_1"}
            ]
        elif comp_val == 1:
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "title_left"},
                {"row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 1, "col": 0, "r_span": 1, "c_span": 2, "item": "line"}
            ]
        elif comp_val == 7:
            widgets = [
                {"row": 0, "col": 0, "r_span": 1, "c_span": 1, "item": "title_left"},
                {"row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 0, "col": 2, "r_span": 1, "c_span": 1, "item": "separator"},
                {"row": 0, "col": 3, "r_span": 1, "c_span": 1, "item": "valbox_2"},
                {"row": 1, "col": 0, "r_span": 1, "c_span": 4, "item": "line"},
                {"row": 2, "col": 1, "r_span": 1, "c_span": 1, "item": "titlebox_1"},
                {"row": 2, "col": 3, "r_span": 1, "c_span": 1, "item": "titlebox_2"}
            ]
        elif comp_val == 14:
            widgets = [
                {"row": 0, "col": 0, "r_span": 3, "c_span": 1, "item": "icon"},
                {"row": 0, "col": 1, "r_span": 1, "c_span": 1, "item": "valbox_1"},
                {"row": 0, "col": 2, "r_span": 1, "c_span": 1, "item": "separator"},
                {"row": 0, "col": 3, "r_span": 1, "c_span": 1, "item": "valbox_2"},
                {"row": 1, "col": 1, "r_span": 1, "c_span": 3, "item": "line"},
                {"row": 2, "col": 1, "r_span": 1, "c_span": 1, "item": "titlebox_1"},
                {"row": 2, "col": 3, "r_span": 1, "c_span": 1, "item": "titlebox_2"}
            ]
        return widgets

    def value_change(self, attrib, value):
        """Zmienia wyświetlaną wartość parametru."""
        if attrib == "value":
            self.valbox_1.setText(str(value)) if value else self.valbox_1.setText("")
            if isinstance(self.valbox_1, CanvasLineEdit):
                self.valbox_1.text_changed()
        elif attrib == "value_2":
            self.valbox_2.setText(str(value)) if value else self.valbox_2.setText("")
            if isinstance(self.valbox_2, CanvasLineEdit):
                self.valbox_2.text_changed()


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
        fn = 'dlg.obj.set_object_from_input(self.text(), self.parent().obj)'
        self.idbox = CanvasLineEdit(self, width=self.width() - 44, height=self.height() - 4, max_len=self.max_len, validator=self.validator, fn=fn, theme=theme)
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
            self.idbox.setText(str(val)) if val else self.idbox.setText("")
            self.idbox.text_changed()

    def prev_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk prev_btn."""
        dlg.obj.object_prevnext(self.obj, False)

    def next_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk next_bnt."""
        dlg.obj.object_prevnext(self.obj, True)


class CanvasLineEdit(QLineEdit):
    """Lineedit z odpalaniem funkcji po zatwierdzeniu zmian tekstu."""
    def __init__(self, *args, width, height, r_widget=None, font_size=12, max_len=None, validator=None, placeholder=None, theme="dark", fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setFrame(False)
        self.font_size = font_size
        self.r_widget = r_widget
        if self.r_widget == "ruler":
            self.r_widget = MoekSlideButton(self, name="ruler", size=24, checkable=True)
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
        self.mt_enabled = False
        self.focused = False
        self.hover = False
        self.temp_val = None
        self.pressed = False

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
            self.set_style()

    def text_changed(self):
        """Sygnał zmiany wartości."""
        if self.placeholder and len(self.text()) == 0:
            self.setText(self.placeholder)
        self.set_style()

    def set_style(self):
        """Modyfikacja stylesheet przy hoveringu lub zmianie tekstu."""
        alpha = 0.3 if self.hover else 0.2
        if self.placeholder:
            font_color = "0, 0, 0, 0.3" if self.text() == self.placeholder and (not self.focused or self.mt_enabled) else self.color
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
        if self.placeholder and self.text() == self.placeholder:
                self.setText("")
                self.set_style()
        else:
            self.selectAll()
        self.temp_val = self.text()
        self.focused = True

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focused = False
        if self.validator == '00.0' and len(self.text()) > 0:
            val = self.numeric_formater()
            self.setText(str(val)) if val else self.setText(self.temp_val)
        self.val_change()

    def val_change(self):
        self.run_fn()
        self.text_changed()
        self.temp_val = None

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

    def numeric_formater(self):
        """Zamienia znak decymalny na kropkę i zaokrągla liczbę."""
        text = self.text().replace(",", ".")
        try:
            val = float(text)
        except ValueError:
            return None
        return round(val, 1)

    def run_fn(self):
        """Próba zmiany wartości przez odpalenie właściwej funkcji."""
        if self.fn:
            exec(eval("f'{}'".format(self.fn)))


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


class MoekTableView(QTableView):
    """Widget obsługujący dane tabelaryczne."""
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
