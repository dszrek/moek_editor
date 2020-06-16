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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(28)
        self.setMaximumHeight(28)
        self.setStyleSheet("""
                           QFrame#bar {background-color: rgb(0,122,204); border: 1px solid white}
                           QLabel#title {font-family: Segoe UI; font-size: 8pt; font-weight: bold; color: white}
                           """)
        if switch:
            self.io_btn = MoekButton(icon_name="io", enabled=True, checkable=True)
        else:
            self.io_btn = MoekButton(icon_name="io", enabled=False, checkable=True)
        if config:
            self.cfg_btn = MoekButton(icon_name="cfg", enabled=True, checkable=True)
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
        print("io_clicked")

    def cfg_clicked(self):
        print("cfg_clicked")

class MoekButton(QToolButton):
    """Fabryka guzików."""
    def __init__(self, icon_name="", enabled=False, checkable=False):
        super().__init__()
        self.setEnabled(enabled)
        self.setCheckable(checkable)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(26, 26)
        self.setAutoRaise(True)
        self.setStyleSheet("QToolButton {border: none}")
        icon = QIcon()
        icon.addFile(ICON_PATH + icon_name + "_0.png", size=QSize(26, 26), mode=QIcon.Normal, state=QIcon.Off)
        icon.addFile(ICON_PATH + icon_name + "_0_act.png", size=QSize(26, 26), mode=QIcon.Active, state=QIcon.Off)
        icon.addFile(ICON_PATH + icon_name + "_0.png", size=QSize(26, 26), mode=QIcon.Selected, state=QIcon.Off)
        if not self.isEnabled():
            icon.addFile(ICON_PATH + icon_name + "_0_dis.png", size=QSize(26, 26), mode=QIcon.Disabled, state=QIcon.Off)
        if self.isCheckable():
            icon.addFile(ICON_PATH + icon_name + "_1.png", size=QSize(26, 26), mode=QIcon.Normal, state=QIcon.On)
            icon.addFile(ICON_PATH + icon_name + "_1_act.png", size=QSize(26, 26), mode=QIcon.Active, state=QIcon.On)
            icon.addFile(ICON_PATH + icon_name + "_1.png", size=QSize(26, 26), mode=QIcon.Selected, state=QIcon.On)
        self.setIcon(icon)
