# coding=utf-8
"""DockWidget test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'dszr@pgi.gov.pl'
__date__ = '2020-05-12'
__copyright__ = 'Copyright 2020, Dominik Szrek / PIG-PIB'

import unittest

from qgis.PyQt.QtGui import QDockWidget

from moek_editor_dockwidget import MoekEditorDockWidget

from utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class MoekEditorDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.dockwidget = MoekEditorDockWidget(None)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test we can click OK."""
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(MoekEditorDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

