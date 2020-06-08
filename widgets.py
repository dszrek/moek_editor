# -*- coding: utf-8 -*-
import os

from PyQt5.QtWidgets import QToolButton, QFrame, QLabel, QHBoxLayout, QSizePolicy, QSpacerItem
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep

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
