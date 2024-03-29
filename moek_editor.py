# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MoekEditor
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
import os.path
import time

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.utils import iface
from datetime import datetime

from .resources import resources

LIBS_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'libs' + os.path.sep

class MoekEditor:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MoekEditor_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&MOEK Editor')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'MoekEditor')
        self.toolbar.setObjectName(u'MoekEditor')

        #print "** INITIALIZING MoekEditor"

        self.plugin_is_active = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MoekEditor', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/moek_editor/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Edytor systemu MOEK'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        print("** CLOSING MoekEditor")

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashes
        # when closing the docked window:
        self.dockwidget = None
        self.plugin_is_active = False
        # Przywrócenie domyślnego tytułu okna QGIS:
        self.title_change(closing=True)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        print("** UNLOAD MoekEditor")

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&MOEK Editor'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def title_change(self, closing=False):
        """Zmiana tytułu okna QGIS."""
        title = iface.mainWindow().windowTitle()
        new_title = title.replace('| MOEK_Editor', '— QGIS') if closing else title.replace('— QGIS', '| MOEK_Editor')
        iface.mainWindow().setWindowTitle(new_title)

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""
        if not external_libs_exists():
            return

        from .moek_editor_dockwidget import MoekEditorDockWidget
        from .main import db_login, teams_load, teams_cb_changed

        self.start = time.perf_counter()
        if self.plugin_is_active: # Sprawdzenie, czy plugin jest już uruchomiony
            QMessageBox.information(None, "Informacja", "Wtyczka jest już uruchomiona")
            return  # Uniemożliwienie uruchomienia drugiej instancji pluginu

        # Logowanie użytkownika do bazy danych i pobranie wartości podstawowych zmiennych:
        user_id, user_name, team_i = db_login()
        if not user_id:
            return  # Użytkownik nie zalogował się poprawnie, przerwanie ładowania pluginu

        if not self.plugin_is_active:
            self.plugin_is_active = True

            #print "** STARTING MoekEditor"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = MoekEditorDockWidget(user_id, user_name, team_i)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # Załadowanie team'ów:
            if not teams_load():  # Nie udało się załadować team'ów użytkownika, przerwanie ładowania pluginu
                self.iface.removeDockWidget(self.dockwidget)
                return
        project_check = self.dockwidget.lyr.project_check()  # Utworzenie nowego projektu QGIS i załadowanie do niego warstw
        if not project_check:
            try:
                self.dockwidget.close()
            except Exception as err:
                print(f"moek_editor/run: {err}")
            return
        self.title_change()  # Zmiana tytułu okna QGIS
        self.dockwidget.splash_screen.p_bar.setMaximum(0)
        QgsApplication.processEvents()
        teams_cb_changed()  # Załadowanie powiatów
        # show the dockwidget
        # TODO: fix to allow choice of dock location
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.obj.init_void = False  # Odblokowanie ObjectManager'a
        self.dockwidget.button_conn()  # Podłączenie akcji przycisków
        self.dockwidget.mt.init("multi_tool")  # Aktywacja multi_tool'a
        self.dockwidget.bm_panel.date = datetime.now().date()#f"{datetime.now():%Y}-{datetime.now():%m}-{datetime.now():%d}"
        self.dockwidget.splash_screen.hide()
        self.dockwidget.show()
        self.dockwidget.side_dock.show()

        finish = time.perf_counter()
        print(f"Proces ładowania pluginu trwał {round(finish - self.start, 2)} sek.")

def external_libs_exists():
    """Sprawdzenie, czy są zainstalowane zewnętrzne biblioteki."""
    missing_libs = detect_missing_libs()
    if len(missing_libs) > 0:
        m_text = f'Brak zainstalowanych zewnętrznych bibliotek: {[x[0] for x in missing_libs]}. Są one niezbędne do działania wtyczki MOEK_Editor. Czy chcesz je teraz zainstalować?'
        reply = QMessageBox.question(None, "WellMatch", m_text, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return False
        else:
            missing_libs_install(missing_libs)
            return False
    else:
        return True

def detect_missing_libs():
    """Próba załadowania zewnętrznych bibliotek i zwrócenie listy niezainstalowanych."""
    missing_libs = []
    ext_libs = [
        ['win32ui', 'pywin32-304.0-cp39-cp39-win_amd64.whl'],
        ['six', 'six-1.16.0-py2.py3-none-any.whl'],
        ['lxml', 'lxml-4.9.1-cp39-cp39-win_amd64.whl'],
        ['jinja2', 'Jinja2-3.1.2-py3-none-any.whl'],
        ['markupsafe', 'MarkupSafe-2.1.1-cp39-cp39-win_amd64.whl'],
        ['docx', 'python_docx-0.8.11-py3-none-any.whl'],
        ['docxcompose', 'docxcompose-1.3.5-py3-none-any.whl'],
        ['docxtpl', 'docxtpl-0.16.0-py2.py3-none-any.whl'],
        ['xlsxwriter', 'XlsxWriter-3.0.3-py3-none-any.whl']
        ]
    for lib_name in ext_libs:
        try:
            exec(f"import {lib_name[0]}")
        except Exception as err:
            print(err)
            missing_libs.append(lib_name)
    return missing_libs

def missing_libs_install(lib_names):
    """Instaluje brakujące biblioteki zewnętrzne."""
    import subprocess
    for lib in lib_names:
        lib_path = f'{LIBS_PATH}{lib[1]}'
        lib_path = lib_path.replace("\\\\", "\\")
        print(lib_path)
        try:
            subprocess.check_call(['python', '-m', 'pip', 'install', lib_path, '--no-dependencies'])
        except Exception as err:
            QMessageBox.critical(None, "MOEK_Editor", f"Brak możliwości instalacji zewnętrznych bibliotek ({err}). Możesz zgłosić się o pomoc do autora - dszr@pgi.gov.pl")
            return
    QMessageBox.information(None, "MOEK_Editor", f"Wszystkie biblioteki zostały zainstalowane. Należy ponownie uruchomić program QGIS.")