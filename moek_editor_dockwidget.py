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
from qgis.PyQt.QtCore import Qt
from PyQt5.QtWidgets import QShortcut
from qgis.PyQt.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from qgis.core import QgsProject
from qgis.utils import iface

from .viewnet import change_done, vn_change, vn_zoom, hk_up_pressed, hk_down_pressed, hk_left_pressed, hk_right_pressed
from .classes import IdentMapTool

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'moek_editor_dockwidget_base.ui'))
ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep
SELF = "self."

class MoekEditorDockWidget(QtWidgets.QDockWidget, FORM_CLASS):  #type: ignore

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(MoekEditorDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        self.setupUi(self)

        self.__button_init()
        self.__button_conn()

        hotkeys = {'hk_up': 'Up', 'hk_down': 'Down', 'hk_left': 'Left', 'hk_right': 'Right', 'hk_space': 'Space'}

        for key, val in hotkeys.items():
            exec(SELF + key + " = QShortcut(Qt.Key_" + val + ", iface.mainWindow())")

    def toggle_hk(self, enabled):
        hotkeys = {'hk_up': 'hk_up_pressed',
                   'hk_down': 'hk_down_pressed',
                   'hk_left': 'hk_left_pressed',
                   'hk_right': 'hk_right_pressed',
                   'hk_space': 'lambda: change_done(True)'}  #partial(change_done, True)'}
        io = "connect" if enabled else "disconnect"
        try:
            for key, val in hotkeys.items():
                exec(SELF + key + ".setEnabled(enabled)")
                exec(SELF + key + ".activated." + io + "(" + val + ")")
        except Exception as error:
            print("hotkeys exception: {}".format(error))

    def __button_init(self):
        """Konfiguracja przycisków."""
        self.button_cfg(self.btn_sel,'vn_sel.png', checkable=True, tooltip=u'wybierz pole')
        self.button_cfg(self.btn_zoom,'vn_zoom.png', checkable=False, tooltip=u'przybliż do pola')
        self.button_cfg(self.btn_done,'vn_doneT.png', checkable=False, tooltip=u'oznacz jako "SPRAWDZONE"')
        self.button_cfg(self.btn_doneF,'vn_doneTf.png', checkable=False, tooltip=u'oznacz jako "SPRAWDZONE" i idź do następnego')

    def __button_conn(self):
        """Przyłączenia przycisków do funkcji."""
        self.btn_sel.clicked.connect(lambda: self.ident_mt_init("vn_user", vn_change))
        self.btn_zoom.pressed.connect(vn_zoom)
        self.btn_done.pressed.connect(lambda: change_done(False))
        self.btn_doneF.pressed.connect(lambda: change_done(True))

    def button_cfg(self, btn, icon_name, **kwargs):
        """Konfiguracja przycisków."""
        icon = QIcon()
        icon.addPixmap(QPixmap(ICON_PATH + icon_name))
        btn.setIcon(icon)
        if kwargs:
            for key, val in kwargs.items():
                if key == "enabled":
                    btn.setEnabled(val)
                if key == "checkable":
                    btn.setCheckable(val)
                if key == "tooltip":
                    btn.setToolTip(val)

    def ident_mt_init(self, layer_name, callback):
        """Initializacja maptool'a do identyfikacji obiektu na określonej warstwie."""
        canvas = self.iface.mapCanvas()
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if self.btn_sel.isChecked() is False:
            canvas.unsetMapTool(self.maptool)
            return
        self.maptool = IdentMapTool(canvas, layer)
        self.maptool.identified.connect(callback)
        canvas.setMapTool(self.maptool)

    def closeEvent(self, event):
        self.toggle_hk(False)  # Deaktywacja skrótów klawiszowych
        self.closingPlugin.emit()
        event.accept()
