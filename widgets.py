# -*- coding: utf-8 -*-
import os

from qgis.core import QgsVectorLayer, QgsVectorFileWriter
from qgis.PyQt.QtWidgets import QWidget, QMessageBox, QFrame, QToolButton, QPushButton, QComboBox, QLineEdit, QPlainTextEdit, QCheckBox, QLabel, QProgressBar, QStackedWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal, QRegExp
from qgis.PyQt.QtGui import QIcon, QColor, QFont, QPainter, QPixmap, QPainterPath, QRegExpValidator
from qgis.utils import iface

from .main import db_attr_change, vn_cfg, vn_setup_mode, powiaty_mode_changed, vn_mode_changed, get_wyr_ids, get_flag_ids, get_parking_ids, get_marsz_ids, wn_layer_update, file_dialog
from .sequences import MoekSeqBox, MoekSeqAddBox, MoekSeqCfgBox
from .classes import PgConn, CfgPars

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
        _led = MoekLineEdit(self, name=dict["name"], border=dict["border"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_led, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        led_name = f'led_{dict["name"]}'
        self.widgets[led_name] = _led

    def add_seqbox(self, dict):
        """Dodanie do pojemnika panelu custom widget'a służącego dp sekwencyjnego wczytywania podkładów mapowych."""
        _sqb = MoekSeqBox()
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_sqb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        sqb_name = f'sqb_{dict["name"]}'
        self.widgets[sqb_name] = _sqb

    def add_seqaddbox(self, dict):
        """Dodanie zawartości do dwóch pojemników na wiget'y używane do dodawania podkładów mapowych do sekwencji."""
        _sab = MoekSeqAddBox(id=dict["id"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_sab, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        sab_name = f'{dict["name"]}'
        self.widgets[sab_name] = _sab

    def add_seqcfgbox(self, dict):
        """Dodanie zawartości do dwóch pojemników ustawień sekwencyjnego wczytywania podkładów mapowych."""
        _scg = MoekSeqCfgBox(_id=dict["id"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_scg, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        scg_name = f'{dict["name"]}'
        self.widgets[scg_name] = _scg


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
    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
        self.setObjectName("main")
        shadow_1 = QGraphicsDropShadowEffect(blurRadius=24, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        shadow_2 = QGraphicsDropShadowEffect(blurRadius=16, color=QColor(140, 140, 140), xOffset=0, yOffset=0)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(300, 240)
        self.logo = MoekButton(name="splash_logo", size=120, checkable=False, enabled=False)
        self.logo.setGraphicsEffect(shadow_1)
        self.p_bar = QProgressBar()
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
    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setFixedWidth(350)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self.bar = CanvasPanelTitleBar(self, title="Wyrobiska", width=self.width())
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
        self.sp_main = CanvasHSubPanel(self, height=34)
        self.box.lay.addWidget(self.sp_main)
        self.id_box = IdSpinBox(self, _obj="wyr")
        self.id_label = PanelLabel(text="  Id:", size=12)
        self.sp_main.lay.addWidget(self.id_label)
        self.sp_main.lay.addWidget(self.id_box)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.sp_main.lay.addItem(spacer)
        # self.sp_area = CanvasHSubPanel(self, height=34)
        # self.box.lay.addWidget(self.sp_area)
        self.area_label = PanelLabel(text="", size=12)
        self.sp_main.lay.addWidget(self.area_label)
        # spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        # self.sp_area.box.lay.addItem(spacer)
        self.wyr_edit = MoekButton(self, name="wyr_edit", size=34, checkable=False)
        self.wyr_edit.clicked.connect(lambda: dlg.mt.init("wyr_edit"))
        self.sp_main.lay.addWidget(self.wyr_edit)
        self.wyr_del = MoekButton(self, name="trash", size=34, checkable=False)
        self.wyr_del.clicked.connect(self.wyr_delete)
        self.sp_main.lay.addWidget(self.wyr_del)
        self.sp_notepad = CanvasHSubPanel(self, height=110)
        self.box.lay.addWidget(self.sp_notepad)
        self.notepad_box = TextPadBox(self, height=110, obj="wyr")
        self.sp_notepad.lay.addWidget(self.notepad_box)

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


class FlagCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi flag."""
    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
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
        self.id_label = PanelLabel(text="  Id:", size=12)
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
    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
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
        self.id_label = PanelLabel(text="  Id:", size=12)
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
        self.setParent(iface.mapCanvas())
        self.setCursor(Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(112, 48)
        self.setObjectName("main")
        self.pointer = MoekPointer()
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
        self.marsz_continue = MoekButton(name="line_continue", size=34)
        self.marsz_edit = MoekButton(name="line_edit", size=34)
        self.trash = MoekButton(name="trash", size=34)
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
    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
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
        self.id_label = PanelLabel(text="   Id_arkusz:", size=11)
        self.sp_id.lay.addWidget(self.id_label)
        self.id_box = IdSpinBox(self, _obj="wn", width=125, max_len=8, validator="id_arkusz")
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

    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
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
    def __init__(self, *args, width, title=""):
        super().__init__(*args)
        self.setObjectName("bar")
        self.setFixedHeight(34)
        self.exit_btn = MoekButton(self, name="cp_exit", size=34, enabled=True, checkable=False)
        self.exit_btn.clicked.connect(self.exit_clicked)
        if len(title) > 0:
            self.l_title = PanelLabel(text=title, size=12)
            self.l_title.setFixedWidth(width - 34)
        self.setStyleSheet("""
                    QFrame#bar{background-color: rgba(0, 0, 0, 1.0); border: none}
                    QFrame#title {color: rgb(255, 255, 255); font-size: 12pt; qproperty-alignment: AlignCenter}
                    """)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(0)
        if len(title) > 0:
            hlay.addWidget(self.l_title)
        hlay.addWidget(self.exit_btn)
        self.setLayout(hlay)

    def exit_clicked(self):
        self.parent().exit_clicked()


class CanvasHSubPanel(QFrame):
    """Belka panelu z box'em."""
    def __init__(self, *args, height, margins=[0, 0, 0, 0], spacing=0, alpha=0.8):
        super().__init__(*args)
        self.setObjectName("main")
        self.setFixedHeight(height)
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, """ + str(alpha) + """); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        self.lay.setSpacing(spacing)
        self.setLayout(self.lay)


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
        print(_list)
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
        print(f"WN: {id_arkusz}, pow: {pow_id}, b_active: {b_active}")
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

    def __init__(self, *args, name):#, extension):
        super().__init__(*args)
        self.setCheckable(True)
        self.setChecked(False)
        self.name = name
        # self.extension = extension
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
    """Widget do wyświetlania wartości lub zakresu parametru wraz z opisem (nagłówkiem)."""
    def __init__(self, *args, width=160, height=24, val_width=40, val_width_2=40, value="", value_2=None, title_down=None, title_down_2=None, title_left=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.width = width
        self.height = height
        self.val_width = val_width + val_width_2 + 23 if value_2 else val_width
        _height = self.height + 10 if title_down else self.height
        self.setFixedSize(width, _height)
        self.vlay = QVBoxLayout()
        self.vlay.setContentsMargins(0, 0, 0, 0)
        self.vlay.setSpacing(0)
        self.setLayout(self.vlay)
        self.upper_box = MoekHBox()
        self.vlay.addWidget(self.upper_box)
        self.line = MoekHLine()
        self.vlay.addWidget(self.line)
        if title_left:
            _width = self.width - self.val_width
            self.title_left = TextItemLabel(self, height=self.height, width=_width, font_size=8, text=title_left)
            self.upper_box.lay.addWidget(self.title_left)
        val_width_1 = val_width if title_left else self.width
        self.valbox_1 = TextItemLabel(self, height=self.height, width=val_width_1, bgr_alpha=0.15, text=value)
        self.upper_box.lay.addWidget(self.valbox_1)
        if value_2:
            self.upper_sep = TextItemLabel(self, height=self.height, width=23, text="–")
            self.upper_box.lay.addWidget(self.upper_sep)
            self.valbox_2 = TextItemLabel(self, height=self.height, width=val_width_2, bgr_alpha=0.15, text=value_2)
            self.upper_box.lay.addWidget(self.valbox_2)
        if title_down:
            self.lower_box = MoekHBox()
            self.vlay.addWidget(self.lower_box)
            if title_left:
                self.lower_left = TextItemLabel(self, height=10, width=self.width - self.val_width, font_size=6, font_weight="bold", font_alpha=0.6, text="")
                self.lower_box.lay.addWidget(self.lower_left)
            self.titlebox_1 = TextItemLabel(self, height=10, width=val_width_1, align="left", font_size=6, font_weight="bold", font_alpha=0.6, text=title_down)
            self.lower_box.lay.addWidget(self.titlebox_1)
            if value_2:
                self.lower_sep = TextItemLabel(self, height=10, width=23, align="left", font_size=6, font_weight="bold", font_alpha=0.6, text=" ")
                self.lower_box.lay.addWidget(self.lower_sep)
                self.titlebox_2 = TextItemLabel(self, height=10, align="left", width=val_width_2, font_size=6, font_weight="bold", font_alpha=0.6, text=title_down_2)
                self.lower_box.lay.addWidget(self.titlebox_2)
        self.setStyleSheet(" QFrame {background-color: transparent; border: none} ")

    def value_change(self, attrib, value):
        """Zmienia wyświetlaną wartość parametru."""
        if attrib == "value":
            self.valbox_1.setText(str(value))
        elif attrib == "value_2":
            self.valbox_2.setText(str(value))


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
        self.line = MoekHLine()
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
    def __init__(self, *args, _obj, width=90, height=34, max_len=4, validator="id"):
        super().__init__(*args)
        self.obj = _obj
        self.max_len = max_len
        self.validator = validator
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.prev_btn = MoekButton(self, name="id_prev", size=22, hsize=34, checkable=False)
        self.prev_btn.clicked.connect(self.prev_clicked)
        self.next_btn = MoekButton(self, name="id_next", size=22, hsize=34, checkable=False)
        self.next_btn.clicked.connect(self.next_clicked)
        self.idbox = IdLineEdit(self, width=self.width() - 44, height=self.height() - 4, max_len=self.max_len, validator=self.validator)
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

    def prev_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk prev_btn."""
        dlg.obj.object_prevnext(self.obj, False)

    def next_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk next_bnt."""
        dlg.obj.object_prevnext(self.obj, True)


class IdLineEdit(QLineEdit):
    """Lineedit dla zarządzania id."""
    def __init__(self, *args, width, height, max_len, validator):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(width, height)
        self.setFrame(False)
        if max_len:
            self.setMaxLength(max_len)
        if validator == "id":
            self.setValidator(QRegExpValidator(QRegExp("[1-9][0-9]*") ))
        elif validator == "id_arkusz":
            self.setValidator(QRegExpValidator(QRegExp("[0-9][0-9][0-9][0-9]_[0-9][0-9][0-9]") ))
        self.hover_on(False)
        self.focused = False

    def hover_on(self, value):
        """Modyfikacja stylesheet przy hoveringu."""
        if value:
            self.setStyleSheet("QLineEdit {background-color: rgba(255, 255, 255, 0.2); color: white; font-size: 12pt; padding: 0px 0px 0px 2px; qproperty-alignment: AlignCenter}")
        else:
            self.setStyleSheet("QLineEdit {background-color: rgba(255, 255, 255, 0.1); color: white; font-size: 12pt; padding: 0px 0px 0px 2px; qproperty-alignment: AlignCenter}")

    def enterEvent(self, event):
        self.hover_on(True)

    def leaveEvent(self, event):
        self.hover_on(False)

    def focusInEvent(self, event):
        if not self.focused:
            self.focused = True
        else:
            super().focusInEvent(event)

    def mousePressEvent(self, event):
        if not self.focused:
            super().mousePressEvent(event)
            return
        else:
            self.selectAll()
            self.focused = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            dlg.obj.set_object_from_input(self.text(), self.parent().obj)
            self.clearFocus()
        else:
            super().keyPressEvent(event)


class TextPadBox(QFrame):
    """Moduł notatnika."""
    def __init__(self, *args, height, obj):
        super().__init__(*args)
        self.obj = obj
        self.setObjectName("main")
        self.setFixedHeight(height)
        self.setFixedWidth(self.parent().width())
        self.button_box = MoekHBox(self, margins=[5,0,15,0], spacing=2)
        self.button_box.setFixedWidth(self.parent().width())
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
        self.textpad = TextPad(self, width=self.width(), height=self.height() - 34)
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
    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
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
        _tb = MoekToolBox(self, background=dict["background"], direction="vertical")
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
    def __init__(self):
        super().__init__()
        self.setParent(iface.mapCanvas())
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
        _tb = MoekToolBox(self, background=dict["background"], direction="horizontal")
        self.box.lay.addWidget(_tb)
        tb_name = f'tb_{dict["name"]}'
        for widget in dict["widgets"]:
            if widget["item"] == "button":
                _tb.add_button(widget)
            if widget["item"] == "dummy":
                _tb.add_dummy(widget)
        self.toolboxes[tb_name] = _tb


class MoekToolBox(QFrame):
    """Toolbox, do którego button'y ładowane są w wybranej orientacji."""
    def __init__(self,*args, background, direction):
        super().__init__(*args)
        self.direction = direction
        self.widgets = {}
        self.setObjectName("main")
        if self.direction == "horizontal":
            self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.setFixedHeight(51)
            self.box = MoekHBox(self)
            lay = QHBoxLayout()
            lay.setContentsMargins(1, 1, 1, 0)
        else:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
            self.setFixedWidth(51)
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


class MoekGridBox(QFrame):
    """Zawartość panelu w kompozycji QGridLayout."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("gbox")
        # self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.glay = QGridLayout()
        self.glay.setContentsMargins(4, 2, 4, 4)
        self.glay.setSpacing(0)
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
    def __init__(self, *args, text="", size=10):
        super().__init__(*args)
        self.setWordWrap(False)
        self.setStyleSheet("QLabel {color: rgb(255, 255, 255); font-size: " + str(size) + "pt; qproperty-alignment: AlignCenter}")
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
