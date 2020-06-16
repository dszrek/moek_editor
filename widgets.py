# -*- coding: utf-8 -*-
import os

from PyQt5.QtWidgets import QWidget, QFrame, QToolButton, QComboBox, QListView, QLabel, QStackedWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor

from .main import vn_setup_mode
from .viewnet import change_done, vn_change, vn_pow_sel, vn_polysel, vn_add, vn_sub, vn_zoom

ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep

class MoekPanel(QFrame):
    """Nadrzędny obiekt panelu."""
    activated = pyqtSignal(bool)

    def __init__(self, title="", io_fn="", config=False, cfg_fn="", pages=1):
        super().__init__()
        self.setObjectName("pnl")
        shadow = QGraphicsDropShadowEffect(blurRadius=6, color=QColor(180, 180, 180), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow)
        self.bar = MoekBar(title=title, config=config)
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
        self.activated.connect(self.active_change)
        self.active = True
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
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
            print ("attr: ", str(attr), " val: ", str(val))

    def isActive(self):
        """Zwraca, czy panel jest w trybie active."""
        return True if self.active else False

    def active_change(self, value):
        """Zmiana trybu active."""
        if value:
            self.setStyleSheet("""
                               QFrame#pnl {background-color: white; border: none; border-radius: 6px}
                               QFrame#bar {background-color: transparent; border: none}
                               QFrame#box {background-color: transparent; border: none}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(37,84,161)}
                               """)
        else:
            self.setStyleSheet("""
                               QFrame#pnl {background-color: rgb(245,245,245); border: none; border-radius: 12px}
                               QFrame#bar {background-color: rgb(245,245,245); border: none; border-radius: 12px}
                               QFrame#box {background-color: rgb(245,245,245); border: none}
                               QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: normal; color: rgb(150,150,150)}
                               """)
        self.bar.io_btn.setChecked(value)
        self.box.setVisible(value)
        if self.config:
            self.bar.cfg_btn.setVisible(value)
            if self.bar.cfg_btn.isChecked():
                self.bar.cfg_btn.setChecked(False)
                self.bar.cfg_clicked()
        if len(self.io_fn) > 0:
            try:
                exec(self.io_fn)
            except:
                print("io_fn exception")

    def add_button(self, dict):
        _btn = MoekButton(size=dict["size"], name=dict["name"], enabled=True, checkable=dict["checkable"], tooltip=dict["tooltip"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_btn, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        btn_name = f'btn_{dict["name"]}'
        self.widgets[btn_name] = _btn

    def add_combobox(self, dict):
        print(dict)
        _cmb = MoekComboBox(name=dict["name"])
        exec('self.box.pages["page_' + str(dict["page"]) + '"].glay.addWidget(_cmb, dict["row"], dict["col"], dict["r_span"], dict["c_span"])')
        cmb_name = f'cmb_{dict["name"]}'
        self.widgets[cmb_name] = _cmb


class MoekBar(QFrame):
    """Belka panelu."""
    def __init__(self, title="", switch=True, config=False):
        super().__init__()
        self.setObjectName("bar")
        if switch:
            self.io_btn = MoekButton(name="io", enabled=True, checkable=True)
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
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.addWidget(self.io_btn)
        if len(title) > 0:
            hlay.addWidget(self.l_title)
        hlay.addItem(spacer)
        if config:
            hlay.addWidget(self.cfg_btn)
            self.cfg_btn.clicked.connect(self.cfg_clicked)
        self.setLayout(hlay)
        self.io_btn.clicked.connect(self.io_clicked)

    def io_clicked(self):
        """Zmiana trybu active po kliknięciu na przycisk io."""
        self.parent().active = self.io_btn.isChecked()

    def cfg_clicked(self):
        """Uruchomienie zdefiniowanej funkcji po kliknięciu na przycisk cfg."""
        exec(self.parent().cfg_fn)


class MoekGridBox(QFrame):
    """Zawartość panela w kompozycji GridBox."""
    def __init__(self):
        super().__init__()
        # self.setObjectName("box")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.glay = QGridLayout()
        self.glay.setContentsMargins(0, 2, 0, 5)
        self.glay.setSpacing(0)
        self.setLayout(self.glay)


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
    def __init__(self, size=25, name="", enabled=False, checkable=False, tooltip=""):
        super().__init__()
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
    def __init__(self, name=""):
        super().__init__()
        self.setStyleSheet("""
                            QComboBox {
                                border: 2px solid rgb(52, 132, 240);
                                padding: 0px 5px 0px 5px;
                                min-width: 1px;
                                min-height: 25px;
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
                                border: 2px solid rgb(52, 132, 240);
                                background-color: white;
                            }
                           """)
        self.addItem("Kamila Andrzejewska-Kubrak")
        self.addItem("Władysław Ślusarek")
        self.addItem("Dominik Szrek")
        self.findChild(QFrame).setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
