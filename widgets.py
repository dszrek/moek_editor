# -*- coding: utf-8 -*-
import os

from PyQt5.QtWidgets import QWidget, QFrame, QToolButton, QComboBox, QListView, QLabel, QStackedWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor

from .main import vn_setup_mode, powiaty_mode_changed, vn_mode_changed
# from .viewnet import change_done, vn_change, vn_powsel, vn_polysel, vn_add, vn_sub, vn_zoom

ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep

dlg = None

def dlg_widgets(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

class MoekBoxPanel(QFrame):
    """Nadrzędny obiekt panelu."""
    activated = pyqtSignal(bool)
    blocked = pyqtSignal(bool)

    def __init__(self, title="", switch=True, io_fn="", config=False, cfg_fn="", pages=1):
        super().__init__()
        self.setObjectName("boxpnl")
        shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(180, 180, 180), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow)
        self.bar = MoekBar(title=title, switch=switch, config=config)
        self.box = MoekStackedBox()
        self.box.pages = {}
        for p in range(pages):
            _page = MoekGridBox()
            page_id = f'page_{p}'
            self.box.pages[page_id] = _page
            self.box.addWidget(_page)
        self.widgets = {}
        self.io_fn = io_fn
        self.cfg_fn = cfg_fn
        self.config = config
        self.active = True
        self.t_active = True
        self.activated.connect(self.active_change)
        self.block = False
        self.blocked.connect(self.block_change)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.set_style(True)
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
            self.activated.emit(val)
        elif attr == "block":
            self.blocked.emit(val)

    def io_clicked(self, value):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        print("io_clicked")
        self.active = value
        if len(self.io_fn) > 0:
            try:
                dlg.setUpdatesEnabled(False)
                exec(self.io_fn)
                dlg.setUpdatesEnabled(True)
            except TypeError:
                print("io_fn exception:", self.io_fn)

    def is_active(self):
        """Zwraca, czy panel jest w trybie active."""
        return True if self.active else False

    def set_style(self, value):
        """Modyfikacja stylesheet przy zmianie trybu active."""
        if value:
            self.setStyleSheet("""
                               QFrame#boxpnl {background-color: white; border: none; border-top-left-radius: 16px; border-bottom-left-radius: 6px; border-top-right-radius: 6px; border-bottom-right-radius: 6px}
                               QFrame#bar {background-color: transparent; border: none}
                               QFrame#box {background-color: transparent; border: none}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(37,84,161)}
                               """)
        else:
            self.setStyleSheet("""
                               QFrame#boxpnl {background-color: rgb(245,245,245); border: none; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-top-right-radius: 6px; border-bottom-right-radius: 6px}
                               QFrame#bar {background-color: transparent; border: none}
                               QFrame#box {background-color: transparent; border: none}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(150,150,150)}
                               """)

    def active_change(self, value):
        """Zmiana trybu active."""
        self.set_style(value)
        self.bar.io_btn.setChecked(value)
        self.box.setVisible(value)
        if self.config:
            self.bar.cfg_btn.setVisible(value)
            if self.bar.cfg_btn.isChecked():
                self.bar.cfg_btn.setChecked(False)
                self.bar.cfg_clicked()

    def block_change(self, value):
        """Zmiana trybu block."""
        self.bar.io_btn.setEnabled(not value)

    def add_button(self, dict):
        icon_name = dict["icon"] if "icon" in dict else dict["name"]
        _btn = MoekButton(size=dict["size"], name=icon_name, enabled=True, checkable=dict["checkable"], tooltip=dict["tooltip"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_btn, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        btn_name = f'btn_{dict["name"]}'
        self.widgets[btn_name] = _btn

    def add_combobox(self, dict):
        _cmb = MoekComboBox(name=dict["name"], border=dict["border"], b_round=dict["b_round"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_cmb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        cmb_name = f'cmb_{dict["name"]}'
        self.widgets[cmb_name] = _cmb

class MoekBarPanel(QFrame):
    """Nadrzędny obiekt panelu."""
    activated = pyqtSignal(bool)
    blocked = pyqtSignal(bool)

    def __init__(self, title="", title_off="", switch=True, io_fn=""):
        super().__init__()
        self.setObjectName("barpnl")
        self.setMinimumHeight(33)
        shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(180, 180, 180), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow)
        self.box = MoekHBox()
        self.box.widgets = {}
        self.switch = switch
        if self.switch:
            self.io_btn = MoekButton(name="io", enabled=True, checkable=True)
            self.io_btn.clicked.connect(self.io_clicked)
        else:
            self.io_btn = MoekButton(name="io", enabled=False)
        self.io_fn = io_fn
        self.active = True
        self.activated.connect(self.active_change)
        self.block = False
        self.blocked.connect(self.block_change)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.title = title
        self.title_off = title_off
        self.l_title = QLabel(self.title)
        self.l_title.setObjectName("title")
        self.set_style(True)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(4, 0, 4, 0)
        self.hlay.setSpacing(0)
        self.hlay.addWidget(self.io_btn)
        self.hlay.addWidget(self.l_title, stretch=1)
        self.hlay.addWidget(self.box, stretch=3)
        self.setLayout(self.hlay)

    def io_clicked(self):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        self.active = self.io_btn.isChecked()
        if len(self.io_fn) > 0:
            try:
                dlg.setUpdatesEnabled(False)
                exec(self.io_fn)
                dlg.setUpdatesEnabled(True)
            except TypeError:
                print("io_fn exception:", self.io_fn)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.activated.emit(val)
        elif attr == "block":
            self.blocked.emit(val)

    def is_active(self):
        """Zwraca, czy panel jest w trybie active."""
        return True if self.active else False

    def set_style(self, value):
        """Modyfikacja stylesheet przy zmianie trybu active."""
        if value:
            self.setStyleSheet("""
                               QFrame#barpnl {background-color: white; border: none; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-top-right-radius: 6px; border-bottom-right-radius: 6px}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(37,84,161)}
                               """)
        else:
            self.setStyleSheet("""
                               QFrame#barpnl {background-color: rgb(245,245,245); border: none; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-top-right-radius: 6px; border-bottom-right-radius: 6px}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(150,150,150)}
                               """)

    def active_change(self, value):
        """Zmiana trybu active."""
        self.set_style(value)
        self.box.setVisible(value)
        if value:
            self.l_title.setText(self.title)
        else:
            self.l_title.setText(self.title_off) if len(self.title_off) > 0 else self.l_title.setText(self.title)
        if self.switch:
            self.io_btn.setChecked(value)

    def block_change(self, value):
        """Zmiana trybu block."""
        self.io_btn.setEnabled(not value)

    def add_button(self, dict):
        _btn = MoekButton(size=dict["size"], name=dict["name"], enabled=True, checkable=dict["checkable"], tooltip=dict["tooltip"])
        self.box.hlay.addWidget(_btn)
        btn_name = f'btn_{dict["name"]}'
        self.box.widgets[btn_name] = _btn

    def add_combobox(self, dict):
        _cmb = MoekComboBox(name=dict["name"], height=dict["height"], border=dict["border"], b_round=dict["b_round"])
        self.box.hlay.addWidget(_cmb)
        cmb_name = f'cmb_{dict["name"]}'
        self.box.widgets[cmb_name] = _cmb


class MoekBar(QFrame):
    """Belka panelu z box'em."""
    def __init__(self, title="", switch=True, config=False):
        super().__init__()
        self.setObjectName("bar")
        self.setMinimumHeight(33)
        if switch:
            self.io_btn = MoekButton(name="io", enabled=True, checkable=True)
            self.io_btn.clicked.connect(lambda: self.parent().io_clicked(self.io_btn.isChecked()))
        else:
            self.io_btn = MoekButton(name="io", enabled=False, checkable=True)
        if config:
            self.cfg_btn = MoekButton(name="cfg", enabled=True, checkable=True)
        if len(title) > 0:
            self.l_title = QLabel()
            self.l_title.setObjectName("title")
            self.l_title.setText(title)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
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
        self.setLayout(hlay)

    def cfg_clicked(self):
        """Uruchomienie zdefiniowanej funkcji po kliknięciu na przycisk cfg."""
        exec(self.parent().cfg_fn)


class MoekGridBox(QFrame):
    """Zawartość panelu w kompozycji QGridLayout."""
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.glay = QGridLayout()
        self.glay.setContentsMargins(4, 2, 4, 4)
        self.glay.setSpacing(0)
        self.setLayout(self.glay)


class MoekHBox(QFrame):
    """Zawartość panelu w kompozycji QHBoxLayout."""
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(0)
        self.setLayout(self.hlay)


class MoekStackedBox(QStackedWidget):
    """Widget dzielący zawartość panela na strony."""
    def __init__(self):
        super().__init__()
        self.setObjectName("box")

    def sizeHint(self):
        return self.currentWidget().sizeHint()

    def minimumSizeHint(self):
        return self.currentWidget().minimumSizeHint()


class MoekButton(QToolButton):
    """Fabryka guzików."""
    def __init__(self, size=25, name="", visible=True, enabled=False, checkable=False, tooltip=""):
        super().__init__()
        self.setVisible(visible)
        self.setEnabled(enabled)
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFixedSize(size, size)
        self.setIconSize(QSize(size, size))
        self.setAutoRaise(True)
        self.setStyleSheet("QToolButton {border: none}")
        icon = QIcon()
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(size, size), mode=QIcon.Normal, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0_act.png", size=QSize(size, size), mode=QIcon.Active, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(size, size), mode=QIcon.Selected, state=QIcon.Off)
        if not self.isEnabled():
            icon.addFile(ICON_PATH + name + "_0_dis.png", size=QSize(size, size), mode=QIcon.Disabled, state=QIcon.Off)
        if self.isCheckable():
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(size, size), mode=QIcon.Normal, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1_act.png", size=QSize(size, size), mode=QIcon.Active, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(size, size), mode=QIcon.Selected, state=QIcon.On)
        self.setIcon(icon)


class MoekComboBox(QComboBox):
    """Fabryka combos'ów"""
    def __init__(self, name="", height=25, border=2, b_round="none"):
        super().__init__()
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
        self.findChild(QFrame).setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
