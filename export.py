# -*- coding: utf-8 -*-
import os
import io
import subprocess
import shutil
import time as tm
import pandas as pd
import numpy as np
import xlsxwriter as xls
import datetime
import pythoncom

from collections import Counter
from threading import Thread
from PIL import Image, ImageQt, ImageEnhance
from win32com import client
from docxtpl import DocxTemplate
from qgis.core import QgsApplication, QgsVectorLayer, QgsGeometry, QgsFeature, QgsField, QgsVectorFileWriter, QgsWkbTypes, QgsPointXY, QgsRectangle, QgsMapSettings, QgsMapRendererCustomPainterJob, edit
from qgis.PyQt.QtWidgets import QFrame, QPushButton, QToolButton, QRadioButton, QButtonGroup, QProgressBar, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect, QMessageBox
from qgis.PyQt.QtCore import Qt, QVariant, QSize, QRectF, QPointF
from qgis.PyQt.QtGui import QIcon, QColor, QImage, QPainter, QPen, QFont, QPainterPath, QPolygonF

from .main import db_attr_change, file_dialog
from .widgets import CanvasPanelTitleBar, CanvasStackedBox, MoekCheckBox, MoekVBox, CanvasHSubPanel, ParamBox, MoekButton, PanelLabel, ParamTextBox, CanvasCheckBox, MoekDummy
from .classes import PgConn, CfgPars, run_in_main_thread

ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep

dlg = None

def dlg_export(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg


class ExportCanvasPanel(QFrame):
    """Zagnieżdżony w mapcanvas'ie panel do obsługi eksportu danych."""

    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(500)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        shadow_1 = QGraphicsDropShadowEffect(blurRadius=16, color=QColor(0, 0, 0, 220), xOffset=0, yOffset=0)
        self.setGraphicsEffect(shadow_1)
        self.bar = CanvasPanelTitleBar(self, title="Eksport danych", width=self.width())
        self.box = MoekVBox(self, spacing=1)
        self.box.setObjectName("box")
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(0, 0, 0, 0.6); border: none}
                    QFrame#box{background-color: transparent; border: none}
                    """)
        vlay = QVBoxLayout()
        vlay.setContentsMargins(3, 3, 3, 3)
        vlay.setSpacing(0)
        vlay.addWidget(self.bar)
        vlay.addWidget(self.box)
        self.setLayout(vlay)
        separator_1 = CanvasHSubPanel(self, height=1)
        self.box.lay.addWidget(separator_1)
        self.path_box = CanvasHSubPanel(self, height=44, margins=[5, 5, 5, 5], spacing=5, alpha=0.71, disable_void=False)
        self.box.lay.addWidget(self.path_box)
        self.path_pb = ParamBox(self, width=445, title_down="FOLDER EKSPORTU")
        self.path_box.lay.addWidget(self.path_pb)
        self.path_btn = MoekButton(self, name="export_path", size=34, checkable=False, tooltip="wybierz folder, do którego zostaną wyeksportowane dane")
        self.path_btn.clicked.connect(lambda: self.set_path(True))
        self.path_box.lay.addWidget(self.path_btn)
        separator_2 = CanvasHSubPanel(self, height=1)
        self.box.lay.addWidget(separator_2)

        self.content_box = MoekVBox(self)
        self.box.lay.addWidget(self.content_box)
        self.tab_box = ExportTabBox(self)
        self.content_box.lay.addWidget(self.tab_box)

        self.sb = CanvasStackedBox(self)
        self.sb.setFixedWidth(494)
        self.content_box.lay.addWidget(self.sb)
        self.sb.currentChanged.connect(self.stacked_change)
        self.page_0 = MoekVBox(self)
        self.sb.addWidget(self.page_0)
        self.page_1 = MoekVBox(self)
        self.sb.addWidget(self.page_1)

        self.fchk_box = CanvasHSubPanel(self, height=445, margins=[5, 5, 5, 5], alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.page_0.lay.addWidget(self.fchk_box)
        self.fchk_selector = FchkExportSelector(self)
        self.fchk_box.lay.addWidget(self.fchk_selector)
        self.sp_ext = CanvasHSubPanel(self, height=44, margins=[5, 5, 5, 5], alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.page_0.lay.addWidget(self.sp_ext)
        self.fchk_type_selector = TypeFchkExportSelector(self, width=484)
        self.sp_ext.lay.addWidget(self.fchk_type_selector)

        self.pow_header_box = CanvasHSubPanel(self, height=32, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.page_1.lay.addWidget(self.pow_header_box)
        self.pow_header_label = PanelLabel(self, text="")
        self.pow_header_box.lay.addWidget(self.pow_header_label)
        separator_2 = CanvasHSubPanel(self, height=1)
        self.page_1.lay.addWidget(separator_2)
        self.mdb_box = MoekVBoxGreyed(self)
        self.page_1.lay.addWidget(self.mdb_box)
        self.mdb_chkbox = CanvasCheckBoxPanel(title="Baza danych", validator="dlg.export_panel.mdb_validator()", raport="dlg.export_panel.mdb_raport()")
        self.mdb_box.lay.addWidget(self.mdb_chkbox)
        self.mdb_options_box = CanvasHSubPanel(self, height=28, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.mdb_box.lay.addWidget(self.mdb_options_box)
        self.mdb_options = MdbOptionBar(self)
        self.mdb_options_box.lay.addWidget(self.mdb_options)
        separator_3 = CanvasHSubPanel(self, height=1, alpha=0.2)
        self.page_1.lay.addWidget(separator_3)
        self.zal_box = MoekVBoxGreyed(self)
        self.page_1.lay.addWidget(self.zal_box)
        self.zal_chkbox = CanvasCheckBoxPanel(title="Załączniki", validator="dlg.export_panel.zal_validator()")
        self.zal_box.lay.addWidget(self.zal_chkbox)
        self.zal1_box1 = CanvasHSubPanel(self, height=28, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.zal_box.lay.addWidget(self.zal1_box1)
        self.zal1_box2 = CanvasHSubPanel(self, height=28, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.zal_box.lay.addWidget(self.zal1_box2)
        self.zal1_1 = PanelLabel(self, text="Załącznik 1. Zestawienie zinwentaryzowanych wyrobisk na terenie", color="170, 170, 170", size=9)
        self.zal1_box1.lay.addWidget(self.zal1_1)
        spacer_1a = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.zal1_box2.lay.addItem(spacer_1a)
        self.zal1_2 = ParamTextBox(self, width=277, height=22, edit=True, centered=True, fn=['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.powiaty", attr="t_zal_1", sql_bns=f" WHERE pow_id = CAST({dlg.powiat_i} AS varchar)")', 'dlg.export_panel.zal_update()'])
        self.zal1_box2.lay.addWidget(self.zal1_2)
        self.zal1_3 = PanelLabel(self, text="– stan na", color="170, 170, 170", size=9)
        self.zal1_box2.lay.addWidget(self.zal1_3)
        self.zal1_4 = ParamTextBox(self, width=87, height=22, edit=True, centered=True, fn=['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.powiaty", attr="t_zal_2", sql_bns=f" WHERE pow_id = CAST({dlg.powiat_i} AS varchar)")', 'dlg.export_panel.zal_update()'])
        self.zal1_box2.lay.addWidget(self.zal1_4)
        self.zal1_5 = PanelLabel(self, text=f" 20{dlg.team_t[-2:]} r.", color="170, 170, 170", size=9)
        self.zal1_box2.lay.addWidget(self.zal1_5)
        spacer_1b = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.zal1_box2.lay.addItem(spacer_1b)
        separator_4 = CanvasHSubPanel(self, height=1, alpha=0.2)
        self.page_1.lay.addWidget(separator_4)
        self.zal3_box1 = CanvasHSubPanel(self, height=28, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.zal_box.lay.addWidget(self.zal3_box1)
        self.zal3_box2 = CanvasHSubPanel(self, height=28, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.zal_box.lay.addWidget(self.zal3_box2)
        self.zal3_box3 = CanvasHSubPanel(self, height=28, margins=[5, 0, 5, 5], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.zal_box.lay.addWidget(self.zal3_box3)
        self.zal3_1 = PanelLabel(self, text="Załącznik 3. Zestawienie miejsc zinwentaryzowanych w", color="170, 170, 170", size=9)
        self.zal3_box1.lay.addWidget(self.zal3_1)
        spacer_2a = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.zal3_box2.lay.addItem(spacer_2a)
        self.zal3_2 = ParamTextBox(self, width=425, height=22, edit=True, centered=True, fn=['self.db_update(txt_val=self.cur_val, tbl=f"team_{dlg.team_i}.powiaty", attr="t_zal_3", sql_bns=f" WHERE pow_id = CAST({dlg.powiat_i} AS varchar)")', 'dlg.export_panel.zal_update()'])
        self.zal3_box2.lay.addWidget(self.zal3_2)
        self.zal3_3 = PanelLabel(self, text=f"20{dlg.team_t[-2:]} r.", color="170, 170, 170", size=9)
        self.zal3_box2.lay.addWidget(self.zal3_3)
        spacer_2b = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.zal3_box2.lay.addItem(spacer_2b)
        self.zal3_4 = PanelLabel(self, text="wymagających pilnej interwencji", color="170, 170, 170", size=9)
        self.zal3_box3.lay.addWidget(self.zal3_4)
        self.card_box = MoekVBoxGreyed(self)
        self.page_1.lay.addWidget(self.card_box)
        self.card_chkbox = CanvasCheckBoxPanel(title="Karty wyrobisk", validator="dlg.export_panel.card_validator()")
        self.card_box.lay.addWidget(self.card_chkbox)
        self.szkice_box = CanvasHSubPanel(self, height=33, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.card_box.lay.addWidget(self.szkice_box)
        self.szkice_options = SzkicOptionBar(self)
        self.szkice_box.lay.addWidget(self.szkice_options)
        separator_5 = CanvasHSubPanel(self, height=1, alpha=0.2)
        self.page_1.lay.addWidget(separator_5)
        self.photo_box = MoekVBoxGreyed(self)
        self.page_1.lay.addWidget(self.photo_box)
        self.photo_chkbox = CanvasCheckBoxPanel(title="Zdjęcia terenowe", validator="dlg.export_panel.photo_validator()", raport="dlg.export_panel.photo_raport()")
        self.photo_box.lay.addWidget(self.photo_chkbox)
        self.photo_path_box = CanvasHSubPanel(self, height=44, margins=[5, 0, 5, 10], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.photo_box.lay.addWidget(self.photo_path_box)
        self.photo_pb = ParamBox(self, width=445, title_down="FOLDER ZE ZDJĘCIAMI TERENOWYMI")
        self.photo_path_box.lay.addWidget(self.photo_pb)
        self.photo_btn = MoekButton(self, name="export_path", size=34, checkable=False, tooltip="wybierz folder, w którym znajdują się zdjęcia terenowe")
        self.photo_btn.clicked.connect(lambda: self.set_path(False))
        self.photo_path_box.lay.addWidget(self.photo_btn)
        self.photo_options_box = CanvasHSubPanel(self, height=56, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.photo_box.lay.addWidget(self.photo_options_box)
        self.photo_options = PhotoOptionBar(self)
        self.photo_options_box.lay.addWidget(self.photo_options)
        separator_6 = CanvasHSubPanel(self, height=1, alpha=0.0)
        self.content_box.lay.addWidget(separator_6)

        self.export_box = CanvasHSubPanel(self, height=44, margins=[5, 5, 5, 5], spacing=5, alpha=0.91, disable_color="40, 40, 40", disable_void=False)
        self.box.lay.addWidget(self.export_box)
        self.pp_bar = ExportProgressBar(self)
        self.export_box.lay.addWidget(self.pp_bar)
        self.export_data_btn = MoekButton(self, name="export", size=34, checkable=True, enabled=False, tooltip="rozpocznij eksport danych dla powiatu")
        self.export_data_btn.clicked.connect(self.data_export)
        self.export_box.lay.addWidget(self.export_data_btn)

        self.tab_box.cur_idx = 0

        self.pow_bbox = None
        self.pow_all = None
        self.init_void = True
        self.path_void = None
        self.pow_case_void = False
        self.fchk_case = 0
        self.red_warning = False
        self.export_path = None
        self.photo_path = None
        self.check_path = None
        self.szkice_path = None
        self.fchk_path = None
        self.raport_path = None
        self.zal_pbs = []
        self.zal_pbs.append(self.zal1_2)
        self.zal_pbs.append(self.zal1_4)
        self.zal_pbs.append(self.zal3_2)
        self.zal1_txt = None
        self.zal3_txt = None
        self.zal_txts = []
        self.init_void = False
        self.photo_state = None
        self.mdb_state = None
        self.zal_state = None
        self.card_state = None
        self.p1_df = pd.DataFrame(columns=['wyr_id', 'id_punkt'])
        self.p2_df = pd.DataFrame(columns=['wyr_id', 'id_punkt'])
        self.p3_df = pd.DataFrame(columns=['wyr_id', 'id_punkt', 'pc', 'db'])
        self.m1_df = pd.DataFrame(columns=['wyr_id', 'id_punkt'])
        self._ppbar_enabled = run_in_main_thread(self.pp_bar.bar.setVisible)
        self._ppbar_progress = run_in_main_thread(self.pp_bar.bar.setValue)
        self._ppbar_text = run_in_main_thread(self.pp_bar.bar.setFormat)
        self._databtn_checked = run_in_main_thread(self.export_data_btn.setChecked)
        self._databtn_tooltip = run_in_main_thread(self.export_data_btn.set_tooltip)
        self._print = run_in_main_thread(print)
        self.exporting = False
        self.exp_queue = []

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "export_path" and not self.init_void and not self.pow_case_void:
            self.path_change(path_txt=val, team=True)
            self.path_void = False if val else True
            self.init_chkboxs()
        if attr == "photo_path" and not self.init_void:
            self.path_change(path_txt=val, team=False)
        if attr == "fchk_case" and not self.init_void:
            self.export_btn_enabler()
        if attr == "path_void" and val != None:
            self.content_box.set_enabled(not val)
            self.export_box.set_enabled(False) if val else self.export_box.set_enabled(True)
            self.check_path = f"{self.export_path}{os.path.sep}{dlg.powiat_t}{os.path.sep}raport końcowy{os.path.sep}raporty_błędów" if not val else None
            self.szkice_path = f"{self.export_path}{os.path.sep}{dlg.powiat_t}{os.path.sep}raport końcowy{os.path.sep}szkice_lokalizacyjne" if not val else None
        if attr == "zal_txts" and not self.init_void:
            self.zal_validator()
        if attr == "red_warning":
            self.export_btn_enabler()
        if attr == "exporting":
            self.path_box.set_enabled(not val)
            self.content_box.set_enabled(not val)

    def export_btn_enabler(self):
        """Włącza / wyłacza przycisk eksportu w zależności od spełnionych reguł."""
        if self.tab_box.cur_idx == 0:
            if self.fchk_case == 0:
                # Nie wybrano żadnego z typów plików do eksportu
                self.export_data_btn.setEnabled(False)
            else:
                # Jakiś rodzaj pliku jest wybrany - sprawdzamy, czy jakieś checkbox'y są zaznaczone
                self.export_data_btn.setEnabled(True) if self.fchk_selector.chk_cnt > 0 else self.export_data_btn.setEnabled(False)
        elif self.tab_box.cur_idx == 1:
            self.export_data_btn.setEnabled(False) if self.red_warning else self.export_data_btn.setEnabled(True)

    def init_chkboxs(self):
        """Włączenie wszystkich elementów eksportu dla powiatu (przy uruchamianiu export_panel)."""
        self.pow_case_void = True
        if self.pp_bar.active:  # Schowanie progressbar'u, jeśli go widać
            self.pp_bar.active = False
        self.path_check(self.path_from_db("t_export_path"), True)
        self.export_btn_enabler()
        if self.tab_box.cur_idx == 1:
            self.path_check(self.path_from_db("t_photo_path"), False)
            _bool = True if self.export_path else False
            self.mdb_chkbox.checkbox_update()
            self.zal_chkbox.checkbox_update()
            self.card_chkbox.checkbox_update()
            self.photo_chkbox.checkbox_update()
            self.check_red_warning()
        self.pow_case_void = False

    def stacked_change(self):
        """Ustalenie stanu przycisku eksportu przy zmianie aktualnej zakładki."""
        if self.tab_box.cur_idx == 0:
            self.export_btn_enabler()
        elif self.tab_box.cur_idx == 1:
            self.init_chkboxs()

    def resize_panel(self):
        """Ustala wysokość panelu w zależności od trybu powiatu."""
        self.setFixedHeight(658)
        dlg.resize_canvas()

    def exit_clicked(self):
        """Wyłączenie panelu po naciśnięciu na przycisk X."""
        if self.exporting:
            self.export_ending()
        dlg.export_panel.hide()

    def path_from_db(self, column):
        """Zwraca ścieżkę do danego elementu z db."""
        db = PgConn()
        sql = f"SELECT {column} FROM public.team_users WHERE team_id = {dlg.team_i} and user_id = {dlg.user_id};"
        if db:
            res = db.query_sel(sql, False)
            if res:
                return res[0]
            else:
                return None
        else:
            return None

    def path_check(self, _path, team):
        """Sprawdza, czy trzeba zaktualizować self.export_path lub self.photo_path."""
        path = None
        if _path:
            path = self.valid_path(_path)
        if team:
            self.export_path = path
        else:
            self.photo_path = path

    def valid_path(self, path):
        """Zwraca ścieżkę, jeśli istnieje."""
        if os.path.isdir(path):
            return path
        else:
            return None

    def path_change(self, path_txt="", team=True):
        """Zmiana ścieżki eksportu danych."""
        pb = self.path_pb if team else self.photo_pb
        pb.value_change("value","") if not path_txt else pb.value_change("value", path_txt)
        db_attr = "t_export_path" if team else "t_photo_path"
        db_path = "Null" if not path_txt else f"'{path_txt}'"
        table = f"public.team_users"
        bns = f" WHERE team_id = {dlg.team_i} and user_id = {dlg.user_id}"
        db_attr_change(tbl=table, attr=db_attr, val=db_path, sql_bns=bns, user=False)

    def set_path(self, team):
        """Ustawia ścieżkę do folderu eksportu danych zespołu lub zdjęć terenowych przez okno dialogowe menedżera plików."""
        path = file_dialog(is_folder=True)
        if not path:
            return
        if team:
            self.export_path = path
        else:
            self.photo_path = path
            self.photo_validator()

    def check_red_warning(self):
        """Sprawdza, czy któryś notyfikator zgłasza czerwony alarm, co zablokuje przycisk exportu danych dla powiatu."""
        # print("[check_red_warning]")
        red_warning = False
        chkboxs = [self.mdb_chkbox, self.photo_chkbox]
        for chkbox in chkboxs:
            if chkbox.checked and chkbox.warning.case == 2:
                red_warning = True
        self.red_warning = red_warning

    def mdb_validator(self):
        """Ocenia poprawność danych dotyczące bazy danych."""
        # print("[mdb_validator]")
        self.m1_df = self.empty_date_check()  # Wyrobiska, które mają puste daty kontroli terenowej
        if len(self.m1_df) > 0:
            print(self.m1_df)
            self.mdb_chkbox.warning.set_tooltip("otwórz raport")
            self.mdb_chkbox.warning.case = 2
            return
        self.mdb_chkbox.warning.case = 0
        self.mdb_chkbox.warning.set_tooltip(None)

    def zal_validator(self):
        """Ocenia poprawność danych dotyczące załączników."""
        # print(f"[zal_validator]")
        self.zal_title_parser()
        if not self.zal_txts or None in self.zal_txts:
            self.zal_chkbox.warning.case = 1
            self.zal_chkbox.warning.set_tooltip("uzupełnij teksty tytułów załączników")
        else:
            self.zal_chkbox.warning.case = 0
            self.zal_chkbox.warning.set_tooltip(None)

    def card_validator(self):
        """Ocenia poprawność danych dotyczące kart wyrobisk."""
        if not self.szkice_path:
            self.card_chkbox.warning.case = 0
            self.card_chkbox.warning.set_tooltip("")
            return
        if not os.path.isdir(self.szkice_path):
            self.card_chkbox.warning.case = 1
            self.card_chkbox.warning.set_tooltip("brak szkiców lokalizacyjnych - mogą zostać wygenerowane w trakcie tworzenia kart wyrobisk")
            self.szkice_options.radio_1.setChecked(True)
            self.szkice_options.radio_2.setEnabled(False)
            return
        if not self.szkice_wyr_equal():
            self.card_chkbox.warning.case = 1
            self.card_chkbox.warning.set_tooltip("lista zapisanych szkiców jest niepełna - aby uniknąć błędów, szkice należy wygenerować od nowa")
            self.szkice_options.radio_1.setChecked(True)
            self.szkice_options.radio_2.setEnabled(False)
            return
        self.card_chkbox.warning.case = 0
        self.card_chkbox.warning.set_tooltip("")
        self.szkice_options.radio_2.setChecked(True)

    def photo_validator(self):
        """Ocenia poprawność danych dotyczące zdjęć."""
        # print("[photo_validator]")
        if not self.photo_path:
            print("Brak ścieżki dostępu do zdjęć terenowych")
            self.photo_chkbox.warning.set_tooltip("ustal ścieżkę dostępu do folderu ze zdjęciami terenowymi")
            self.photo_chkbox.warning.case = 2
            return
        self.photo_check()
        if len(self.p1_df) > 0 or len(self.p2_df) > 0 or len(self.p3_df) > 0:
            self.photo_chkbox.warning.set_tooltip("otwórz raport")
            print(self.p1_df)
            print(self.p2_df)
            print(self.p3_df)
            self.photo_chkbox.warning.case = 1
            return
        self.photo_chkbox.warning.set_tooltip(None)
        self.photo_chkbox.warning.case = 0

    def photo_raport(self):
        """Tworzy raport błędów występujących w zdjęciach terenowych."""
        # print("[photo_raport]")
        checks = [
            {'obj': self.p1_df, 'title': 'Wyrobiska, które nie mają folderów ze zdjęciami na dysku', 'headers': ['wyr_id', 'id_punkt'], 'widths': [8, 12]},
            {'obj': self.p2_df, 'title': 'Wyrobiska, które nie mają zadeklarowanej ilości zdjęć w bazie danych', 'headers': ['wyr_id', 'id_punkt'], 'widths': [8, 12]},
            {'obj': self.p3_df, 'title': 'Wyrobiska, które nie mają takich samych ilości zdjęć na dysku, co zadeklarowanych w bazie danych', 'headers': ['wyr_id', 'id_punkt', 'dysk', 'baza'], 'widths': [8, 12, 8, 8]}
            ]
        self.create_raport_xlsx("foto", checks)

    def mdb_raport(self):
        """Tworzy raport błędów występujących w bazie danych."""
        # print("[mdb_raport]")
        checks = [
            {'obj': self.m1_df, 'title': 'Wyrobiska, które nie mają ustalonych dat przeprowadzenia kontroli terenowej', 'headers': ['wyr_id', 'id_punkt'], 'widths': [8, 12]}
            ]
        # Wypełnienie tabelek i otworzenie raportu:
        self.create_raport_xlsx("mdb", checks)

    def szkice_wyr_equal(self):
        """Sprawdza, czy ilość szkiców zgadza się z ilością wyrobisk."""
        db_list = self.id_punkt_from_db()
        files_list = [f[:-4] for f in list(os.walk(self.szkice_path))[0][2] if f.lower().endswith('.png')]
        return True if Counter(db_list) == Counter(files_list) else False

    def id_punkt_from_db(self):
        """Zwraca listę z id_punkt dla potwierdzonych wyrobisk z bazy danych."""
        db = PgConn()
        sql = f"SELECT concat(p.pow_id, '_', p.order_id) as id_punkt FROM team_{dlg.team_i}.wyr_prg AS p INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON p.wyr_id=d.wyr_id WHERE p.pow_grp = '{dlg.powiat_i}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
        if db:
            res = db.query_sel(sql, True)
            if res:
                if len(res) > 1:
                    return list(list(zip(*res))[0])
                else:
                    return list(res[0])
            else:
                return []

    def create_raport_xlsx(self, name, checks):
        """Tworzy plik excel'a dla raportu."""
        if not self.check_path:
            return
        if not os.path.isdir(self.check_path):
            # Utworzenie folderu powiatu, jeśli nie istnieje
            os.makedirs(self.check_path)
        tmstmp = datetime.datetime.now().strftime("%y%m%d_%H%M")
        filename = f"raport_{name}_{tmstmp}.xlsx"
        dest_excel = f"{self.check_path}{os.path.sep}{filename}"
        # Utworzenie skoroszytu excel i jego sformatowanie:
        wb = xls.Workbook(dest_excel)
        ws = wb.add_worksheet(f'{dlg.powiat_t}')
        ws.set_paper(9)
        ws.set_portrait()
        ws.set_margins(0.3, 0.3, 0.3, 0.3)
        ws.set_header(margin=0)
        ws.set_footer(margin=0)
        title_format = wb.add_format({'font_color': 'white', 'bg_color': 'black', 'text_wrap': True, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': 'white'})
        cell_format = wb.add_format({'text_wrap': False, 'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        # Ustawienie wysokości rzędów z tytułami:
        ws.set_row(0, 70)
        ws.set_row(1, 25)
        col_num_all = 0
        # Generator tabelek:
        for check in checks:
            if len(check["obj"]) == 0:
                # Dany "check" nie posiada danych - pomijamy
                continue
            col_num = col_num_all
            col_cnt = len(check['headers'])
            col_list = [[check['headers'][i], check['widths'][i]] for i in range(0, col_cnt)]
            # Wstawienie tytułu:
            if col_cnt > 1:
                ws.merge_range(0, col_num_all, 0, col_num_all + col_cnt - 1, check["title"], title_format)
            else:
                ws.write(0, col_num_all, check["title"], title_format)
            # Ustawienie szerokości kolumn i wstawienie nagłówków:
            for col in col_list:
                ws.set_column(col_num, col_num, col[1])
                ws.write(1, col_num, col[0], title_format)
                col_num += 1
            # Uzupełnienie wierszy danymi:
            r = 1
            for index in check["obj"].to_records():
                r += 1
                for i in range(0, col_cnt):
                    ws.write(r, col_num_all + i, index[i + 1], cell_format)
            # Dodanie kolumny rozdzielającej i zmiana numeru kolumny bieżącej:
            col_num_all += col_cnt
            ws.set_column(col_num_all, col_num_all, 2)
            col_num_all += 1
        wb.close()  # Zapis pliku
        os.system(f'start EXCEL.EXE "{dest_excel}"')  # Otwarcie Excel'a z raportem

    def photo_check(self):
        self.p1_df = pd.DataFrame(columns=['wyr_id', 'id_punkt'])  # Wyrobiska, które nie mają folderów ze zdjęciami na dysku
        self.p2_df = pd.DataFrame(columns=['wyr_id', 'id_punkt'])  # Wyrobiska, które nie mają zadeklarowanej ilości zdjęć w db
        self.p3_df = pd.DataFrame(columns=['wyr_id', 'id_punkt', 'pc', 'db'])  # Wyrobiska, które nie mają takich samych ilości zdjęć na dysku, co zadeklarowanych w db
        df = self.wyr_for_pict()
        for index in df.to_records():  # index[1]: wyr_id, index[2]: id_punkt, index[3]: foto_cnt
            wyr_source_path = os.path.join(self.photo_path, str(index[1]))
            if pd.isnull(index[3]):
                tdf = pd.DataFrame([[index[1], index[2]]], columns=['wyr_id', 'id_punkt'])
                self.p2_df = pd.concat([self.p2_df, tdf], ignore_index=True)
                index[3] = 0
            if not os.path.isdir(wyr_source_path) and index[3] > 0:
                tdf = pd.DataFrame([[index[1], index[2]]], columns=['wyr_id', 'id_punkt'])
                self.p1_df = pd.concat([self.p1_df, tdf], ignore_index=True)
                continue
            if os.path.isdir(wyr_source_path):
                files = [f[:-4] for f in list(os.walk(wyr_source_path))[0][2] if f.lower().endswith('.jpg')]
            else:
                files = []
            if index[3] != len(files):
                tdf = pd.DataFrame([[index[1], index[2], len(files), int(index[3])]], columns=['wyr_id', 'id_punkt', 'pc', 'db'])
                tdf = tdf.fillna("-")
                self.p3_df = pd.concat([self.p3_df, tdf], ignore_index=True)

    def empty_date_check(self):
        """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i pustym atrybutem daty."""
        db = PgConn()
        sql = f"SELECT d.wyr_id, concat(p.pow_id, '_', p.order_id) as id_punkt FROM team_{dlg.team_i}.wyr_dane AS d INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON d.wyr_id=p.wyr_id WHERE p.pow_grp = '{dlg.powiat_i}' and p.order_id IS NOT NULL AND d.date_ctrl IS NULL ORDER BY d.wyr_id;"
        if db:
            mdf = db.query_pd(sql, ['wyr_id', 'id_punkt'])
            if isinstance(mdf, pd.DataFrame):
                return mdf if len(mdf) > 0 else pd.DataFrame(columns=['wyr_id', 'id_punkt'])
            else:
                return pd.DataFrame(columns=['wyr_id', 'id_punkt'])

    def zal_update(self):
        """Wczytanie do paramtextbox'ów wartości fragmentów tekstów tytułów załączników z db."""
        # print("[zal_update]")
        self.zal_txts = self.zal_load()
        zals = zip(self.zal_pbs, self.zal_txts)
        for zal in zals:
            txt = self.param_parser(zal[1])
            zal[0].value_change(txt)

    def zal_load(self):
        """Zwraca wartości fragmentów tytułów załączników z db."""
        db = PgConn()
        sql = f"SELECT t_zal_1, t_zal_2, t_zal_3 FROM team_{dlg.team_i}.powiaty WHERE pow_id = '{dlg.powiat_i}';"
        if db:
            res = db.query_sel(sql, False)
            if res:
                return [res[0], res[1], res[2]]
            else:
                return [None, None, None]
        else:
            return [None, None, None]

    def param_parser(self, val, quote=False):
        """Zwraca wartość przerobioną na tekst (pusty, jeśli None)."""
        if quote:
            txt = f'"{val}"' if val != None else f'""'
        else:
            txt = f'{val}' if val != None else str()
        return txt

    def zal_title_parser(self):
        """Ustala tytuły załączników."""
        empty_txt = " ............... "
        temp_txts = []
        if not self.zal_txts:
            temp_txts.extend([empty_txt for i in range(3)])
        else:
            for zal_txt in self.zal_txts:
                if zal_txt:
                    temp_txts.append(zal_txt)
                else:
                    temp_txts.append(empty_txt)
        self.zal1_txt = f"Załącznik 1. Zestawienie zinwentaryzowanych wyrobisk na terenie {temp_txts[0]} – stan na {temp_txts[1]} 20{dlg.team_t[-2:]} r."
        self.zal3_txt = f"Załącznik 3. Zestawienie miejsc zinwentaryzowanych w {temp_txts[2]} 20{dlg.team_t[-2:]} r. wymagających pilnej interwencji"

    def pow_reset(self):
        """Kasuje zawartość zmiennych 'self.pow_bbox' i 'self.pow_all' po zmianie team'u."""
        self.pow_bbox = None
        self.pow_all = None

    def pow_update(self):
        """Aktualizuje wygląd panelu w zależności od ustalonego trybu powiatu."""
        if dlg.wyr_panel.pow_all:
            self.tab_box.cur_idx = 0
            self.tab_box.widgets["btn_1"].setVisible(False)
        else:
            self.tab_box.widgets["btn_1"].setVisible(True)
            self.pow_header_label.setText(f"Eksport danych – powiat {dlg.powiat_t} [{dlg.powiat_i}]:")
            self.mdb_chkbox.chkbox.setText(f"Baza danych ({dlg.powiat_t}_wyrobiska zarejestrowane.kml)")
            self.mdb_options.chkbox.setText(f"{dlg.powiat_t}_punkty odrzucone.kml")
            self.zal1_5.setText(f"20{dlg.team_t[-2:]} r.")
            self.zal3_3.setText(f"20{dlg.team_t[-2:]} r.")
        self.resize_panel()

    def folder_create(self, folder=None, tms=None):
        """Tworzy folder o podanej nazwie, jeśli nie istnieje."""
        if not tms:
            tms = datetime.datetime.now().strftime("%y%m%d_%H%M")
        if folder:
            path = f"{os.path.normpath(self.export_path)}{os.path.sep}{dlg.powiat_t}{os.path.sep}kontrola terenowa{os.path.sep}{tms}"
            if os.path.isdir(f"{path}{os.path.sep}{folder}"):
                #  Folder już istnieje - trzeba stworzyć folder z dodatkowym sufix'em
                i = 1
                while os.path.isdir(f"{path}_{i}{os.path.sep}{folder}"):
                    i += 1
                path = f"{path}_{i}"
            os.makedirs(f"{path}{os.path.sep}{folder}", exist_ok=True)
            self.fchk_path = path
        else:
            path = f"{os.path.normpath(self.export_path)}{os.path.sep}{dlg.powiat_t}{os.path.sep}raport końcowy{os.path.sep}{tms}"
            if os.path.isdir(path):
                #  Folder już istnieje - trzeba stworzyć folder z dodatkowym sufix'em
                i = 1
                while os.path.isdir(f"{path}_{i}"):
                    i += 1
                path = f"{path}_{i}"
            os.makedirs(path, exist_ok=True)
            self.raport_path = path

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

    def data_export(self):
        """Puszczenie odpowiedniej funkcji w zależności od aktualnie aktywnej zakładki."""
        self._print("[data_export]")
        if self.export_data_btn.isChecked():
            self.export_data_btn.set_tooltip("przerwij eksport danych")
            self.exporting = True
            self.create_export_queue()
            if self.tab_box.cur_idx == 0:
                t = Thread(target=self.fieldcheck_export)
                t.start()
            elif self.tab_box.cur_idx == 1:
                self.powdata_export()
        else:
            # self._databtn_tooltip("rozpocznij eksport danych")
            self.exporting = False

    def fieldcheck_export(self):
        """Eksport danych zespołu do kontroli terenowej na dysk lokalny."""
        pythoncom.CoInitialize()
        with CfgPars() as cfg:
            PARAMS = cfg.uri()
        file_types = []
        if self.fchk_case in [1, 3, 5, 7]:
            file_types.append({'driver' : 'GPKG', 'folder' : 'geopackage', 'extension' : '.gpkg'})
        if self.fchk_case in [2, 3, 6, 7]:
            file_types.append({'driver' : 'KML', 'folder' : 'kml', 'extension' : '.kml'})
        if self.fchk_case in [4, 5, 6, 7]:
            file_types.append({'driver' : 'ESRI Shapefile', 'folder' : 'shapefiles', 'extension' : '.shp'})
        all_lyrs = [
            {'lyr_name' : 'wyr_point', 'spatial_filter': None, 'uri' : '{PARAMS} key="row_num" table="(SELECT row_number() OVER (ORDER BY w.wyr_id) AS row_num, w.wyr_id, w.teren_id as roboczy_id, w.wn_id as wn_id, w.midas_id as midas_id, d.t_wyr_od AS wyr_od, d.t_wyr_do AS wyr_do, d.t_zloze_od AS zloze_od, d.t_zloze_do AS zloze_do, w.t_notatki as notatki, d.i_area_m2 as pow_m2, w.centroid AS point FROM team_{dlg.team_i}.wyrobiska w INNER JOIN team_{dlg.team_i}.wyr_dane d ON w.wyr_id = d.wyr_id)" (point) sql=', 'n_field' : 'wyr_id', 'd_field' : 't_notatki', 'fields': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
            {'lyr_name' : 'wyr_poly', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."wyr_geom" (geom) sql=', 'n_field' : 'wyr_id', 'd_field' : 'Description', 'fields' : [0]},
            {'lyr_name' : 'flagi_z_teren', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."flagi" (geom) sql=b_fieldcheck = True', 'n_field' : 'id', 'd_field' : 't_notatki', 'fields' : [0, 3, 4]},
            {'lyr_name' : 'flagi_bez_teren', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."flagi" (geom) sql=b_fieldcheck = False', 'n_field' : 'id', 'd_field' : 't_notatki', 'fields' : [0, 3, 4]},
            {'lyr_name' : 'midas_zloza', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_zloza', 'tbl_sql' : '"external"."midas_zloza"', 'key' : 'id', 'n_field' : 'id_zloza', 'd_field' : 'nazwa_zloz'},
            {'lyr_name' : 'midas_wybilansowane', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_wybilansowane', 'tbl_sql' : '"external"."midas_wybilansowane"', 'key' : 'id1', 'n_field' : 'id', 'd_field' : 'nazwa'},
            {'lyr_name' : 'midas_obszary', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_obszary', 'tbl_sql' : '"external"."midas_obszary"', 'key' : 'id', 'n_field' : 'id_zloz', 'd_field' : 'nazwa'},
            {'lyr_name' : 'midas_tereny', 'spatial_filter': 'pow_all', 'tbl_name' : 'external.midas_tereny', 'tbl_sql' : '"external"."midas_tereny"', 'key' : 'id1', 'n_field' : 'id_zloz', 'd_field' : 'nazwa'},
            {'lyr_name' : 'wn_pne', 'spatial_filter': 'id_all', 'tbl_name' : f'team_{dlg.team_i}.wn_pne', 'tbl_sql' : f'"external"."wn_pne"', 'key' : 'id_arkusz', 'n_field' : 'id_arkusz', 'd_field' : 'uwagi'},
            {'lyr_name' : 'parking', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."parking" (geom) sql=', 'n_field' : 'id', 'd_field' : 'description', 'fields' : [0, 3]},
            {'lyr_name' : 'marsz', 'spatial_filter': None, 'uri' : '{PARAMS} table="team_{dlg.team_i}"."marsz" (geom) sql=', 'n_field' : 'id', 'd_field' : 'i_status', 'fields' : [0, 2, 3]}
        ]
        lyrs = []
        for lyr in all_lyrs:
            if lyr['lyr_name'] in self.exp_queue:
                lyrs.append(lyr)
        i_max = len(lyrs) * len(file_types) + 1
        self._ppbar_enabled(True)  # Pokazanie progressbar'u
        i = 1
        self._ppbar_progress(i * 100 / i_max)
        self._ppbar_text(f"Eksport danych dla kontroli terenowej")
        if not self.pow_bbox:
            self.set_pow_bbox()
            self.set_pow_all()
        self._ppbar_progress(i * 100 / i_max)
        tms = datetime.datetime.now().strftime("%y%m%d_%H%M")
        for ft in file_types:
            self.folder_create(ft["folder"], tms)
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
                if not self.exporting:
                    self.export_ending()
                    return
                dest_path = f'{self.fchk_path}{os.path.sep}{ft["folder"]}{os.path.sep}{l_dict["lyr_name"]}{ft["extension"]}'
                self._ppbar_text(f'{l_dict["lyr_name"]}')
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = ft["driver"]
                options.fileEncoding = 'utf-8'
                if "fields" in l_dict:
                    options.attributes = l_dict["fields"]
                options.datasourceOptions = [f"NameField={l_dict['n_field']}", f"DescriptionField={l_dict['d_field']}"]
                QgsVectorFileWriter.writeAsVectorFormatV2(layer=f_lyr, fileName=dest_path, transformContext=dlg.proj.transformContext(), options=options)
                i += 1
                self._ppbar_progress(i * 100 / i_max)
        self.export_ending(self.fchk_path)

    def powdata_export(self):
        """Eksport danych powiatu na dysk lokalny. Uruchamia się po naciśnięciu przycisku 'export_data_btn'."""
        if len(self.exp_queue) == 0:
            # Nie ma czego eksportować
            self.export_ending()
            return
        # Stworzenie folderu eksportu:
        self.folder_create()
        self._ppbar_enabled(True)  # Pokazanie progressbar'u
        # Puszczenie funkcji eksportu w wydzielonym wątku:
        t = Thread(target=self.run_in_thread)
        t.start()

    def run_in_thread(self):
        """Uruchomienie elementów eksportu w wydzielonym wątku."""
        pythoncom.CoInitialize()
        for exp in self.exp_queue:
            self._print(f"thread -> {exp}")
            exec(f"self.{exp}_export()")
        if self.exporting:
            self.export_ending(self.raport_path)

    def export_ending(self, path=None):
        """Zakończenie eksportu danych dla powiatu."""
        if self.exporting:
            self.exporting = False
        self._ppbar_enabled(False)
        self._ppbar_progress(0)
        self._ppbar_text("")
        self._databtn_checked(False)
        self._databtn_tooltip("rozpocznij eksport danych")
        if path:
            self.open_explorer(path)

    def open_explorer(self, path):
        """Otwiera menadżer plików ze ścieżką eksportu."""
        explorer_path = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
        if os.path.isdir(path):
            subprocess.run([explorer_path, path])

    def create_export_queue(self):
        """Tworzy listę elemnentów eksportu w oparciu o stan checkbox'ów."""
        self._print("[create_export_queue]")
        self.exp_queue = []
        if self.tab_box.cur_idx == 0:
            exp_list = [
                (['wyr_point', 'wyr_poly'], self.fchk_selector.chkboxes["chkbox_wyr"]),
                ('flagi_z_teren', self.fchk_selector.chkboxes["chkbox_flagi_z_teren"]),
                ('flagi_bez_teren', self.fchk_selector.chkboxes["chkbox_flagi_bez_teren"]),
                ('midas_zloza', self.fchk_selector.chkboxes["chkbox_midas_zloza"]),
                ('midas_wybilansowane', self.fchk_selector.chkboxes["chkbox_midas_wybilansowane"]),
                ('midas_obszary', self.fchk_selector.chkboxes["chkbox_midas_obszary"]),
                ('midas_tereny', self.fchk_selector.chkboxes["chkbox_midas_tereny"]),
                ('midas_wn_pne', self.fchk_selector.chkboxes["chkbox_wn_pne"]),
                ('parking', self.fchk_selector.chkboxes["chkbox_parking"]),
                ('marsz', self.fchk_selector.chkboxes["chkbox_marsz"])
                ]
        elif self.tab_box.cur_idx == 1:
            exp_list = [
                ('mdb', self.mdb_chkbox.chkbox),
                ('zal', self.zal_chkbox),
                ('card', self.card_chkbox),
                ('photo', self.photo_chkbox)
                ]
        for exp in exp_list:
            _bool = exp[1].checked if isinstance(exp[1], CanvasCheckBoxPanel) else exp[1].isChecked()
            if _bool:
                if type(exp[0]) == list:
                    self.exp_queue.extend(exp[0])
                else:
                    self.exp_queue.append(exp[0])

    def photo_export(self):
        """Eksport zdjęć wyrobisk potwierdzonych z danego powiatu, połączony z nadaniem im odpowiednich nazw."""
        if not self.exporting:
            return
        self._print(f"[photo_export]")
        dest_path = f"{self.raport_path}{os.path.sep}zdjęcia_terenowe"
        if not os.path.isdir(dest_path):
            os.makedirs(dest_path, exist_ok=True)
        temp_path = f"{self.photo_path}{os.path.sep}temp"
        df = self.wyr_for_pict()
        wyr_cnt = len(df)
        if not wyr_cnt or wyr_cnt == 0:
            return
        i = 0
        for index in df.to_records():  # index[1]: wyr_id, index[2]: id_punkt, index[3]: foto_cnt
            if not self.exporting:
                self.export_ending()
                return
            i += 1
            self._ppbar_progress(i * 100 / wyr_cnt)
            self._ppbar_text(f"Eksport zdjęć terenowych")
            wyr_source_path = os.path.join(self.photo_path, str(index[1]))
            wyr_temp_path = os.path.join(temp_path, str(index[1]))
            if not os.path.isdir(wyr_source_path):
                continue
            files = [f for f in os.listdir(wyr_source_path) if f.lower().endswith('.jpg')]
            for cnt, filename in enumerate(files, 1):
                if not self.exporting:
                    return
                dst_name = f"{index[2]}_{str(cnt).zfill(2)}.jpg"
                # self.photo_optimize(filename, wyr_source_path, dest_path, dst)
                if self.photo_options.radio_tak.isChecked():
                    # Włączona optymalizacja wielkości plików
                    if os.path.isfile(os.path.join(wyr_temp_path, filename)):
                        # W folderze tymczasowym jest już zoptymalizowany plik - zostanie wykorzystany
                        shutil.copy2(os.path.join(wyr_temp_path, filename), os.path.join(dest_path, dst_name))
                    else:
                        # Brak pliku w folderze tymczasowym - wykonujemy optymalizację
                        self.photo_optimize(filename, wyr_source_path, wyr_temp_path, dest_path, dst_name)
                else:
                    shutil.copy2(os.path.join(wyr_source_path, filename), os.path.join(dest_path, dst_name))

    def photo_optimize(self, filename, wyr_source_path, wyr_temp_path, dest_path, dst_name):
        """Optymalizuje wielkość zdjęcia i zapisuje go w folderze eksportu."""
        TRG_SIZE = 2000000  # Limit wielkości pliku - 2 MB
        img = Image.open(f"{os.path.join(wyr_source_path, filename)}")
        # load exif data
        exif_dict = img.getexif()
        exif_bytes = exif_dict.tobytes()
        if self.file_size(img) <= TRG_SIZE:
            # Plik zajmie mniej niż 2 MB - można go zapisać
            img.save(f"{os.path.join(dest_path, dst_name)}", "JPEG", quality=80, optimize=True, progressive=True, exif=exif_bytes)
            if self.photo_options.temp_on:
                # Włączona opcja tworzenia plików tymczasowych - zapisanie pliku do późniejszego wykorzystania
                if not os.path.isdir(wyr_temp_path):
                    os.makedirs(wyr_temp_path, exist_ok=True)
                shutil.copy2(os.path.join(dest_path, dst_name), os.path.join(os.path.normpath(wyr_temp_path), filename))
            img.close()
            return
        # Plik zajmuje za dużo miejsca - trzeba zwiększyć kompresję lub/i zmniejszyć rozdzielczość
        if self.file_size(img, 60) > TRG_SIZE:
            # Zwiększenie kompresji nie wystarczy - należy zmniejszyć rozdzielczość
            img = self.photo_resize(img, TRG_SIZE)
        # Ustalenie optymalnej kompresji:
        q = self.photo_quality(img, TRG_SIZE)
        # Zapisanie pliku zdjęcia na dysku:
        img.save(f"{os.path.join(dest_path, dst_name)}", "JPEG", quality=q, optimize=True, progressive=True, exif=exif_bytes)
        if self.photo_options.temp_on:
            # Włączona opcja tworzenia plików tymczasowych - zapisanie pliku do późniejszego wykorzystania
            if not os.path.isdir(wyr_temp_path):
                os.makedirs(wyr_temp_path, exist_ok=True)
            shutil.copy2(os.path.join(dest_path, dst_name), os.path.join(os.path.normpath(wyr_temp_path), filename))
        img.close()

    def photo_resize(self, img, TRG_SIZE):
        """Pomniejsza rozdzielczość zdjęcia, aby osiągnąć limit rozmiaru pliku przy kompresji 60."""
        img_out = img
        w, h = img.size  # Oryginalne wymiary zdjęcia
        mpx = w * h / 1000000  # Ilość megapikseli zdjęcia
        mpx_min = 0  # Minimalna ilość megapikseli zdjęcia
        mpx_max = mpx  # Maksymalna ilość megapikseli zdjęcia
        w_low = 0  # Ustalona szerokość pomniejszonego zdjęcia
        while mpx_max - mpx_min > 1:
            mpx_new = mpx_min + ((mpx_max - mpx_min) / 2)
            w_new = int(round(w * mpx_new / mpx, 0))  # Nowa szerokość zdjęcia pomniejszona do mpx_new megapikseli
            h_new = int(round(h * mpx_new / mpx, 0))  # Nowa wysokość zdjęcia pomniejszona do mpx_new megapikseli
            temp_img = img.resize((w_new, h_new))  # Przeskalowanie zdjęcia
            file_size = self.file_size(temp_img, 60)  # Ustalenie rozmiaru pliku
            if file_size <= TRG_SIZE:
                if w_new > w_low:
                    img_out = temp_img
                mpx_min = mpx_new
            else:
                mpx_max = mpx_new
            self._print(f"[{w_new}x{h_new}] {file_size} KB | min: {mpx_min}, max: {mpx_max}, new: {mpx_new}, dif: {mpx_max - mpx_min}")
        self._print("======================================")
        return img_out

    def photo_quality(self, img, TRG_SIZE):
        """Zwraca zdjęcie pomniejszone, które będzie zajmowało mniej niż TRG_SIZE."""
        q_min = 60
        q_max = 80
        while q_max - q_min > 1:
            q = q_min + int(round((q_max - q_min) / 2))
            file_size = self.file_size(img, q)
            if file_size <= TRG_SIZE:
                q_min = q
            else:
                q_max = q
            print(f"[q: {q}] {file_size} KB | min: {q_min}, max: {q_max}, dif: {q_max - q_min}")
        self._print("__________________________________________")
        return q

    def file_size(self, img, quality=80):
        """Zwraca wielkość pliku w KB."""
        buffer = io.BytesIO()
        img.save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
        return buffer.getbuffer().nbytes

    def mdb_export(self):
        """Export do kml wyrobisk z danego powiatu."""
        if not self.exporting:
            self.export_ending()
            return
        self.export_kml_green()
        if self.mdb_options.chkbox.isChecked():
            self.export_kml_red()

    def export_kml_green(self):
        """Eksport kml'a z zarejestrowanymi wyrobiskami."""
        self._ppbar_progress(50) if self.mdb_options.chkbox.isChecked() else self._ppbar_progress(100)
        self._ppbar_text("Eksport pliku bazy danych - wyrobiska zarejestrowane")
        # Przygotowanie danych:
        df = self.wyr_for_kml_green()
        df['DATA'] = df['DATA'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['NADKL_MIN'] = pd.to_numeric(df['NADKL_MIN'], downcast='float')
        df['NADKL_MAX'] = pd.to_numeric(df['NADKL_MAX'], downcast='float')
        df['MIAZSZ_MIN'] = pd.to_numeric(df['MIAZSZ_MIN'], downcast='float')
        df['MIAZSZ_MAX'] = pd.to_numeric(df['MIAZSZ_MAX'], downcast='float')
        df['WYS_MIN'] = pd.to_numeric(df['WYS_MIN'], downcast='float')
        df['WYS_MAX'] = pd.to_numeric(df['WYS_MAX'], downcast='float')
        df['STAN_MIDAS'] = np.where((df['STAN_MIDAS'] == 'RW') | (df['STAN_MIDAS'] == 'RS'), 'R', df['STAN_MIDAS'])
        df['POW_M2'] = np.where(df['STAN_PNE'] == 'brak', np.nan, df['POW_M2'])
        df['ZAGROZENIA'] = df['ZAGROZENIA'].fillna('brak')
        # Eksport do .kml:
        attribs = [
            QgsField('NAMEFIELD', QVariant.String, "string", 10),
            QgsField('ID_PUNKT', QVariant.String, "string", 10),
            QgsField('ID_ARKUSZ', QVariant.String, "string", 8),
            QgsField('DATA', QVariant.DateTime, "datetime"),
            QgsField('MIEJSCE', QVariant.String, "string", 100),
            QgsField('CZY_TEREN', QVariant.Bool, "bool"),
            QgsField('CZY_PNE', QVariant.Bool, "bool"),
            QgsField('CZY_ZLOZE', QVariant.Bool, "bool"),
            QgsField('ID_MIDAS', QVariant.String, "string", 8),
            QgsField('STAN_MIDAS', QVariant.String, "string", 255),
            QgsField('PNE_ZLOZE', QVariant.Bool, "bool"),
            QgsField('PNE_POZA', QVariant.Bool, "bool"),
            QgsField('STAN_PNE', QVariant.String, "string", 255),
            QgsField('ZLOZE_OD', QVariant.String, "string", 50),
            QgsField('ZLOZE_DO', QVariant.String, "string", 50),
            QgsField('PNE_OD', QVariant.String, "string", 50),
            QgsField('PNE_DO', QVariant.String, "string", 50),
            QgsField('KOPALINA', QVariant.String, "string", 60),
            QgsField('KOPALINA_2', QVariant.String, "string", 60),
            QgsField('WIEK', QVariant.String, "string", 30),
            QgsField('WIEK_2', QVariant.String, "string", 30),
            QgsField('NADKL_MIN', QVariant.Double, "double", 2, 1),
            QgsField('NADKL_MAX', QVariant.Double, "double", 2, 1),
            QgsField('MIAZSZ_MIN', QVariant.Double, "double", 2, 1),
            QgsField('MIAZSZ_MAX', QVariant.Double, "double", 2, 1),
            QgsField('DLUG_MIN', QVariant.Double, "double", 4, 0),
            QgsField('DLUG_MAX', QVariant.Double, "double", 4, 0),
            QgsField('SZER_MIN', QVariant.Double, "double", 4, 0),
            QgsField('SZER_MAX', QVariant.Double, "double", 4, 0),
            QgsField('WYS_MIN', QVariant.Double, "double", 2, 1),
            QgsField('WYS_MAX', QVariant.Double, "double", 2, 1),
            QgsField('POW_M2', QVariant.Double, "double", 10, 0),
            QgsField('WYROBISKO', QVariant.String, "string", 50),
            QgsField('ZAWODN', QVariant.String, "string", 50),
            QgsField('EXPLOAT', QVariant.String, "string", 50),
            QgsField('WYDOBYCIE', QVariant.String, "string", 25),
            QgsField('WYP_ODPADY', QVariant.String, "string", 50),
            QgsField('ODPADY_1', QVariant.String, "string", 50),
            QgsField('ODPADY_2', QVariant.String, "string", 50),
            QgsField('ODPADY_3', QVariant.String, "string", 50),
            QgsField('ODPADY_4', QVariant.String, "string", 50),
            QgsField('STAN_REKUL', QVariant.String, "string", 50),
            QgsField('REKULTYW', QVariant.String, "string", 255),
            QgsField('DOJAZD', QVariant.String, "string", 255),
            QgsField('ZAGROZENIA', QVariant.String, "string"),
            QgsField('ZGLOSZENIE', QVariant.String, "string", 255),
            QgsField('POWOD', QVariant.String, "string"),
            QgsField('UWAGI', QVariant.String, "string"),
            QgsField('AUTOR', QVariant.String, "string", 255)
            ]
        lyr = QgsVectorLayer("Point?crs=epsg:2180&field=fid:integer", "kml", "memory")
        lyr.setCustomProperty("skipMemoryLayersCheck", 1)
        pr = lyr.dataProvider()
        pr.addAttributes(attribs)
        lyr.updateFields()
        with edit(lyr):
            i = 0
            for index in df.values.tolist():
                i += 1
                attr_val = index[:-2]
                attr_val.insert(0, i)
                attr_val = [None if pd.isnull(item) else item for item in attr_val]
                xy_val = index[-2:]
                feat = QgsFeature(lyr.fields())
                feat.setAttributes(attr_val)
                feat.setGeometry(QgsGeometry().fromPointXY(QgsPointXY(xy_val[0], xy_val[1])))
                pr.addFeature(feat)
        lyr.updateExtents()
        # Zapisanie warstwy do .kml:
        dest_path = f"{self.raport_path}{os.path.sep}{dlg.powiat_t}_wyrobiska zarejestrowane.kml"
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "KML"
        options.fileEncoding = 'utf-8'
        options.layerName = "PNE"
        options.datasourceOptions = [f"NameField=NAMEFIELD"]
        QgsVectorFileWriter.writeAsVectorFormatV2(layer=lyr, fileName=dest_path, transformContext=dlg.proj.transformContext(), options=options)
        lyr = None

    def export_kml_red(self):
        """Eksport kml'a z punktami odrzuconymi."""
        self._ppbar_progress(100)
        self._ppbar_text("Eksport pliku bazy danych - punkty odrzucone")
        # Przygotowanie danych:
        df = self.wyr_for_kml_red()
        # Eksport do .kml:
        attribs = [
            QgsField('NAMEFIELD', QVariant.Int, "integer"),
            QgsField('DESCRIPTIONFIELD', QVariant.String, "string"),
            QgsField('wyr_id', QVariant.Int, "integer"),
            QgsField('wn_id', QVariant.String, "string", 8),
            QgsField('midas_id', QVariant.String, "string", 8),
            QgsField('pne_od', QVariant.String, "string", 50),
            QgsField('pne_do', QVariant.String, "string", 50),
            QgsField('zloze_od', QVariant.String, "string", 50),
            QgsField('zloze_do', QVariant.String, "string", 50),
            QgsField('notatki', QVariant.String, "string")
            ]
        lyr = QgsVectorLayer("Point?crs=epsg:2180&field=fid:integer", "kml", "memory")
        lyr.setCustomProperty("skipMemoryLayersCheck", 1)
        pr = lyr.dataProvider()
        pr.addAttributes(attribs)
        lyr.updateFields()
        with edit(lyr):
            i = 0
            for index in df.values.tolist():
                i += 1
                attr_val = index[:-2]
                attr_val.insert(0, i)
                attr_val = [None if pd.isnull(item) else item for item in attr_val]
                xy_val = index[-2:]
                feat = QgsFeature(lyr.fields())
                feat.setAttributes(attr_val)
                feat.setGeometry(QgsGeometry().fromPointXY(QgsPointXY(xy_val[0], xy_val[1])))
                pr.addFeature(feat)
        lyr.updateExtents()
        # Zapisanie warstwy do .kml:
        dest_path = f"{self.raport_path}{os.path.sep}{dlg.powiat_t}_punkty odrzucone.kml"
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "KML"
        options.fileEncoding = 'utf-8'
        # options.layerName = "PNE"
        options.datasourceOptions = ["NameField=NAMEFIELD", "DescriptionField=DESCRIPTIONFIELD"]
        QgsVectorFileWriter.writeAsVectorFormatV2(layer=lyr, fileName=dest_path, transformContext=dlg.proj.transformContext(), options=options)
        lyr = None

    def zal_export(self):
        """Export danych do załączników."""
        if not self.exporting:
            self.export_ending()
            return
        self._ppbar_progress(100)
        self._ppbar_text(f"Eksport załączników")
        df = self.wyr_for_zal()
        odp_cols = ['ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4']
        df["ODPADY"] = df[odp_cols].apply(lambda x: '; '.join(x.dropna()), axis=1)
        df.drop(odp_cols, axis=1, inplace=True)
        df['POW_M2'] = np.where(df['STAN_PNE'] == 'brak wyrobiska', '–', df['POW_M2'])
        df['KOPALINA'] = np.where(df['KOPALINA_2'].isna(), df['KOPALINA'], df['KOPALINA'] + ' / ' + df['KOPALINA_2'])
        df['WIEK'] = np.where(df['WIEK_2'].isna(), df['WIEK'], np.where(df['WIEK'] == df['WIEK_2'], df['WIEK'], df['WIEK'] + ' / ' + df['WIEK_2']))
        df.drop(['KOPALINA_2', 'WIEK_2'], axis=1, inplace=True)
        df_cols = df.columns.tolist()
        df_cols = df_cols[:17] + df_cols[-1:] + df_cols[17:-1]
        df = df[df_cols]
        df_nopne = df[df['CZY_PNE'] == False]
        df_nopne_cols = df_nopne.columns.tolist()
        df_nopne_cols = df_nopne_cols[:8] + df_nopne_cols[10:]
        df_nopne = df_nopne[df_nopne_cols]
        df_pne = df[~df.index.isin(df_nopne.index)]
        df_pne_cols = df_pne.columns.tolist()
        df_pne_cols = df_pne_cols[:10] + df_pne_cols[12:]
        df_pne = df_pne[df_pne_cols]
        df_zal3 = df[df['ZGLOSZENIE'] != 'brak']
        df_zal3['OD'] = np.where(df_zal3['CZY_PNE'] == True, df_zal3['PNE_OD'], df_zal3['ZLOZE_OD'])
        df_zal3['DO'] = np.where(df_zal3['CZY_PNE'] == True, df_zal3['PNE_DO'], df_zal3['ZLOZE_DO'])
        df_zal3_cols = df_zal3.columns.tolist()
        df_zal3_cols = df_zal3_cols[:8] + df_zal3_cols[-2:] + df_zal3_cols[12:-2]
        df_zal3 = df_zal3[df_zal3_cols]
        zal3 = True if len(df_zal3) > 0 else False
        dest_excel = f"{self.raport_path}{os.path.sep}zal1_3_{dlg.powiat_t}.xlsx" if zal3 else f"{self.raport_path}{os.path.sep}zal1_{dlg.powiat_t}.xlsx"
        wb = xls.Workbook(dest_excel)
        wss = []
        ws_1 = wb.add_worksheet('Załącznik 1')
        wss.append(ws_1)
        if zal3:
            ws_3 = wb.add_worksheet('Załącznik 3')
            wss.append(ws_3)
        for ws in wss:
            ws.set_paper(8)
            ws.set_landscape()
            ws.center_horizontally()
            ws.set_margins(0.3, 0.3, 0.3, 0.3)
            ws.set_header(margin=0)
            ws.set_footer(margin=0)
        head_1 = "PUNKTY NIEKONCESJONOWANEJ EKSPLOATACJI"
        header = ['Lp.', 'ID PUNKTU', 'MIEJSCOWOŚĆ', 'GMINA', 'ID MIDAS', 'STAN ZAGOSPODAROWANIA ZŁOŻA WG MIDAS', 'STWIERDZONY STAN ZAGOSPODAROWANIA WYROBISKA', 'WYDOBYCIE OD', 'WYDOBYCIE DO', 'KOPALINA', 'WIEK', 'POW (m²)', 'ORIENTACYJNA SKALA EKSPLOATACJI', 'LOKALIZACJA POLA EKSPLOATACJI', 'OBECNOŚĆ ODPADÓW', 'RODZAJE ODPADÓW', 'REKULTYWACJA', 'ZAGROŻENIA', 'PROBLEM DO ZGŁOSZENIA', 'OPIS POWODU ZGŁOSZENIA', 'DATA WIZJI TERENOWEJ', 'DATA POPRZEDNIEJ WIZJI TERENOWEJ', 'UWAGI']
        col_widths = [1.86, 6.43, 8.71, 5.71, 3.86, 6.29, 8.29, 7.29, 7.29, 6.14, 5.86, 3.29, 10.43, 8.43, 6.71, 9.29, 9.71, 8.29, 7.43, 11.43, 7.43, 7.57, 28.86]
        cols = enumerate(col_widths)
        head_2 = "NIEZREKULTYWOWANE WYROBISKA, W KTÓRYCH NIE STWIERDZONO NIEKONCESJONOWANEJ EKSPLOATACJI"
        title_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 10, 'bold': True})
        header_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 6, 'bold': False, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#d9d9d9', 'border': 7})
        head_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 10, 'bold': False,'align': 'center', 'valign': 'vcenter', 'border': 7})
        cell_fm = wb.add_format({'font_name': 'Times New Roman', 'font_size': 6, 'bold': False, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'border': 7})
        date_fm = wb.add_format({'num_format': 'dd.mm.yyyy', 'font_name': 'Times New Roman', 'font_size': 6, 'bold': False, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'border': 7})
        ws_1.merge_range(0, 0, 0, 22, self.zal1_txt, title_fm)
        for col in cols:
            ws_1.set_column(col[0], col[0], col[1])
        ws_1.set_row(1, 8)
        ws_1.write_row(2, 0, header, header_fm)
        r = 2
        if len(df_pne) > 0:
            df_pne = df_pne.reset_index(drop=True)
            df_pne.index += 1
            df_pne.drop(['CZY_PNE', 'CZY_ZLOZE', 'STAN_REKUL'], axis=1, inplace=True)
            r += 1
            ws_1.set_row(r, 19.5)
            ws_1.merge_range(r, 0, r, 22, head_1, head_fm)
            df_pne = df_pne.where(pd.notnull(df_pne), None)
            for index in df_pne.to_records():
                r += 1
                ws_1.write_row(r, 0, index, cell_fm)
                date_vals = (index[20], index[21])
                ws_1.write_row(r, 20, date_vals, date_fm)
        if len(df_nopne) > 0:
            df_nopne = df_nopne.reset_index(drop=True)
            df_nopne.index += 1
            df_nopne.drop(['CZY_PNE', 'CZY_ZLOZE', 'STAN_REKUL'], axis=1, inplace=True)
            r += 1
            ws_1.set_row(r, 19.5)
            ws_1.merge_range(r, 0, r, 22, head_2, head_fm)
            df_nopne = df_nopne.where(pd.notnull(df_nopne), None)
            for index in df_nopne.to_records():
                r += 1
                ws_1.write_row(r, 0, index, cell_fm)
                date_vals = (index[20], index[21])
                ws_1.write_row(r, 20, date_vals, date_fm)
        if len(df_zal3) > 0:
            df_zal3 = df_zal3.reset_index(drop=True)
            df_zal3.index += 1
            df_zal3.drop(['CZY_PNE', 'CZY_ZLOZE', 'STAN_REKUL'], axis=1, inplace=True)
            ws_3.merge_range(0, 0, 0, 22, self.zal3_txt, title_fm)
            cols = enumerate(col_widths)
            for col in cols:
                ws_3.set_column(col[0], col[0], col[1])
            ws_3.set_row(1, 8)
            ws_3.write_row(2, 0, header, header_fm)
            r = 2
            df_zal3 = df_zal3.where(pd.notnull(df_zal3), None)
            for index in df_zal3.to_records():
                r += 1
                ws_3.write_row(r, 0, index, cell_fm)
                date_vals = (index[20], index[21])
                ws_3.write_row(r, 20, date_vals, date_fm)
        try:
            wb.close()
        except Exception as err:
            QMessageBox.warning(None, "Generator załączników", f"Plik {dest_excel} jest zablokowany dla zapisu. Sprawdź, czy nie jest otwarty - jeśli tak, zamknij go i ponów eksport.")

    def card_export(self):
        """Generator kart wyrobisk z danego powiatu."""
        if not self.exporting:
            self.export_ending()
            return
        doc_path = f"{self.raport_path}{os.path.sep}karty_terenowe{os.path.sep}docx"
        pdf_path = f"{self.raport_path}{os.path.sep}karty_terenowe{os.path.sep}pdf"
        dest_excel = f"{self.raport_path}{os.path.sep}karty_terenowe{os.path.sep}karty_{dlg.powiat_t}.xlsx"
        temp_doc = f"{os.path.dirname(os.path.realpath(__file__))}{os.path.sep}resources{os.path.sep}karta_szablon.docx"
        if not os.path.isdir(doc_path):
            os.makedirs(doc_path, exist_ok=True)
        if not os.path.isdir(pdf_path):
            os.makedirs(pdf_path, exist_ok=True)
        if self.szkice_options.radio_1.isChecked():
            if os.path.isdir(self.szkice_path):
                # Istnieje folder ze szkicami, który trzeba wyczyścić dla nowych szkiców
                shutil.rmtree(self.szkice_path, ignore_errors=True, onerror=None)
            os.makedirs(self.szkice_path, exist_ok=True)
            self.szkic_creator()
        df = self.wyr_for_card()
        df['NADKL_MIN'] = pd.to_numeric(df['NADKL_MIN'], downcast='float')
        df['NADKL_MAX'] = pd.to_numeric(df['NADKL_MAX'], downcast='float')
        df['MIAZSZ_MIN'] = pd.to_numeric(df['MIAZSZ_MIN'], downcast='float')
        df['MIAZSZ_MAX'] = pd.to_numeric(df['MIAZSZ_MAX'], downcast='float')
        df['WYS_MIN'] = pd.to_numeric(df['WYS_MIN'], downcast='float')
        df['WYS_MAX'] = pd.to_numeric(df['WYS_MAX'], downcast='float')
        df['DLUG_MIN'] = pd.to_numeric(df['DLUG_MIN'], downcast='integer')
        df['DLUG_MAX'] = pd.to_numeric(df['DLUG_MAX'], downcast='integer')
        df['SZER_MIN'] = pd.to_numeric(df['SZER_MIN'], downcast='integer')
        df['SZER_MAX'] = pd.to_numeric(df['SZER_MAX'], downcast='integer')
        df = df.where(pd.notnull(df), None)
        df['STAN_MIDAS'] = np.where((df['STAN_MIDAS'] == 'RW') | (df['STAN_MIDAS'] == 'RS'), 'R', df['STAN_MIDAS'])
        df['ID'] = df['ID'].str.pad(width=5, side='left', fillchar=' ')
        df[['ID_0', 'ID_1', 'ID_2', 'ID_3', 'ID_4', 'ID_5', 'ID_6']] = df['ID'].str.split(pat ="", expand=True)
        df = df.drop(columns=['ID_0', 'ID_6'])
        df['DATA'] = df['DATA'].where(pd.notnull(df['DATA']), "2000-01-01")
        df['DATA'] = pd.to_datetime(df['DATA'])
        df['DD'] = np.where((df['DATA'].dt.day == 1) & (df['DATA'].dt.month == 1) & (df['DATA'].dt.year == 2000), None, df['DATA'].dt.day.astype('str').str.zfill(2))
        df['MM'] = np.where((df['DATA'].dt.day == 1) & (df['DATA'].dt.month == 1) & (df['DATA'].dt.year == 2000), None, df['DATA'].dt.month.astype('str').str.zfill(2))
        df['RR'] = np.where((df['DATA'].dt.day == 1) & (df['DATA'].dt.month == 1) & (df['DATA'].dt.year == 2000), None, df['DATA'].dt.year)
        df['GODZ'] = df['GODZ'].where(pd.notnull(df['GODZ']), "00:00:00")
        df['GODZ'] = pd.to_datetime(df['GODZ'], format='%H:%M:%S')
        df['GODZ_1'] = np.where((df['GODZ'].dt.hour == 0) & (df['GODZ'].dt.minute == 0), None, df['GODZ'].dt.hour.astype('str').str.zfill(2))
        df['GODZ_2'] = np.where((df['GODZ'].dt.hour == 0) & (df['GODZ'].dt.minute == 0), None, df['GODZ'].dt.minute.astype('str').str.zfill(2))
        df[['ID_P0', 'ID_P1', 'ID_P2', 'ID_P3', 'ID_P4', 'ID_P5', 'ID_P6', 'ID_P_', 'ID_P7', 'ID_P8', 'ID_P9', 'ID_P10']] = df['ID_PUNKT'].str.split(pat ="", expand=True)
        df = df.drop(columns=['ID_P0', 'ID_P_', 'ID_P10'])
        df['ID_ARKUSZ'] = df['ID_ARKUSZ'].fillna('        ')
        df[['ID_A0', 'ID_A1', 'ID_A2', 'ID_A3', 'ID_A4', 'ID_A_', 'ID_A5', 'ID_A6', 'ID_A7', 'ID_A8']] = df['ID_ARKUSZ'].str.split(pat ="", expand=True)
        df = df.drop(columns=['ID_A0', 'ID_A_', 'ID_A8'])
        df['POW_M2'] = np.where(df['STAN_PNE'] == 'brak', '–', df['POW_M2'])
        df['KOPALINY'] = np.where(df['KOPALINA_2'].isna(), df['KOPALINA'], df['KOPALINA'] + ' / ' + df['KOPALINA_2'])
        df['WIEKI'] = np.where(df['WIEK_2'].isna(), df['WIEK'], np.where(df['WIEK'] == df['WIEK_2'], df['WIEK'], df['WIEK'] + ' / ' + df['WIEK_2']))
        df['ZAGROZENIA'] = df['ZAGROZENIA'].fillna('brak')
        o_list = ['e', 'rb', 'p', 'op', 'k', 'czp', 'wg', 'el', 'r', 'i']
        for o in o_list:
            df[f'O_{o}'] = np.where((df['ODPADY_1'] == o) | (df['ODPADY_2'] == o) | (df['ODPADY_3'] == o) | (df['ODPADY_4'] == o), 1, 0)
        df = df.where(pd.notnull(df), None)
        wyr_cnt = len(df)
        i = 0
        for r_index, row in df.iterrows():
            if not self.exporting:
                self.export_ending()
                return
            i += 1
            self._ppbar_progress(i * 100 / wyr_cnt)
            self._ppbar_text("Eksport kart wyrobisk")
            cust_name = row['ID_PUNKT']
            tpl = DocxTemplate(temp_doc)
            if not self.szkice_options.radio_3.isChecked():
                png_path = f"{self.szkice_path}{os.path.sep}{cust_name}.png"
                tpl.replace_pic("szkic.jpg", png_path)
            x = df.to_dict(orient='records')
            context = x
            tpl.render(context[r_index])
            tpl.save(f'{doc_path}{os.path.sep}{cust_name}.docx')
            word_app = client.Dispatch("Word.Application")
            doc = word_app.Documents.Open(f'{doc_path}{os.path.sep}{cust_name}.docx')
            doc.SaveAs(f'{pdf_path}{os.path.sep}{cust_name}.pdf', FileFormat=17)
            doc.Close()
        df = df.drop(df.columns[55:], axis=1)
        df.to_excel(dest_excel)

    def szkic_creator(self):
        """Tworzy szkice sytuacyjne wyrobisk."""
        map_cm = 9.21  # Wymiar mapki w cm
        map_px = int(round(map_cm / 0.008465, 0))  # Wymiar mapki w px
        STYLE_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'styles' + os.path.sep
        # Zdefiniowanie i symbolizacja warstw, które mają się znaleźć na szkicu sytuacyjnym:
        near_lyrs = []
        far_lyrs = []
        near_basemap = dlg.proj.mapLayersByName("Geoportal")[0]
        far_basemap = dlg.proj.mapLayersByName("OpenStreetMap")[0]
        lyr_names = ["midas_zloza", "midas_wybilansowane", "midas_obszary", "midas_tereny"]
        for lyr_name in lyr_names:
            lyr = dlg.proj.mapLayersByName(lyr_name)[0]
            near_lyrs.append(lyr)
            far_lyrs.append(lyr)
            lyr.loadNamedStyle(f'{STYLE_PATH}{lyr_name}_szkic.qml')
        near_lyrs.append(near_basemap)
        far_lyrs.append(far_basemap)
        df = self.wyr_for_szkic(dlg.powiat_i)  # Stworzenie listy wyrobisk
        wyr_cnt = len(df)
        i = 0
        for index in df.to_records():
            # Wygenerowanie szkiców sytuacyjnych dla wszystkich wyrobisk z powiatu:
            if not self.exporting:
                self.export_ending()
                return
            i += 1
            self._ppbar_progress(i * 100 / wyr_cnt)
            self._ppbar_text("Generowanie szkiców lokalizacyjnych")
            wyr_far = self.wyr_to_lyr(index[1], index[3], "far")  # Stworzenie warstwy z geometrią wyrobiska dla dalekiego szkicu
            wyr_near = self.wyr_to_lyr(index[1], index[3], "near")  # Stworzenie warstwy z geometrią wyrobiska dla bliskiego szkicu
            if not wyr_far.isValid() and not wyr_near.isValid():
                self._print(f"szkic_creator: warstwa z geometrią wyrobiska {index[1]} nie jest prawidłowa")
                continue
            wyr_lyrs = []
            wyr_lyrs.append(wyr_far)
            wyr_lyrs.append(wyr_near)
            for wyr_lyr in wyr_lyrs:
                wyr_lyr.loadNamedStyle(f'{STYLE_PATH}poly_szkic.qml')
                feats = wyr_lyr.getFeatures()
                for feat in feats:
                    geom = feat.geometry()
                    if geom.type() == QgsWkbTypes.PointGeometry:
                        circle = geom.buffer(10., 20)
                        feat.setGeometry(circle)
                        wyr_lyr.loadNamedStyle(f'{STYLE_PATH}point_szkic.qml')
            # Dodanie warstwy z wyrobiskiem do listy pozostałych warstw:
            near_lyrs.insert(0, wyr_near)
            far_lyrs.insert(0, wyr_far)
            box = self.wyr_bbox(wyr_lyr)  # Określenie zasięgu przestrzennego wyrobiska
            if not box:
                self._print(f"szkic_creator: nie udało się określić zasięgu geometrii wyrobiska {index[1]}")
                continue
            near_val = max(box.width(), box.height())  # Wybór szerokości albo długości wyrobiska w m
            far_val = 2302  # Sztuczne ustawienie wymiaru, aby rozszerzyć widok mapki orientacyjnej do skali 1: 25 000
            near_m = self.scale_interval(near_val)  # Wartość podziałki w m dla mapki zasadniczej
            far_m = 1000  # Wartość podziałki w m dla mapki orientacyjnej
            if near_val < 92.1:  # Wyrobisko zbyt małe i przez to szkic byłby zbyt przybliżony, rozszerzamy widok do skali 1:2000
                near_val = 92.1
            near_ext = self.sketchmap_extent(box, near_val)  # Ustalenie zasięgu widoku mapki zasadniczej
            far_ext = self.sketchmap_extent(box, far_val)  # Ustalenie zasięgu widoku mapki orientacyjnej w skali 1:25 000
            near_scl = self.scale_width(map_cm, map_px, near_val, near_m)  # Długość podziałki liniowej w px
            far_scl = self.scale_width(map_cm, map_px, far_val, far_m)  # Długość podziałki liniowej w px
            near_img = self.img_create(map_px, map_px)  # Obiekt obrazka mapki zasadniczej
            far_img = self.img_create(map_px, map_px)  # Obiekt obrazka mapki orientacyjnej
            comp_img = self.img_create(map_px * 2, map_px)  # Obiekt obrazka szkicu orientacyjnego
            near_ms = self.ms_create(near_lyrs, near_ext, near_img.size())  # Obiekt mapki zasadniczej
            far_ms = self.ms_create(far_lyrs, far_ext, far_img.size())  # Obiekt mapki orientacyjnej
            self.map_drawing(map_px, near_m, near_scl, near_img, near_ms, True)  # Narysowanie mapki zasadniczej
            self.map_drawing(map_px, far_m, far_scl, far_img, far_ms, False)  # Narysowanie mapki orientacyjnej
            # Postprodukcja (wyostrzenie) podkładu z mapki orientacyjnej:
            data = far_img.constBits().asstring(far_img.byteCount())
            pil_img = Image.frombuffer('RGB', (far_img.width(), far_img.height()), data, 'raw', 'BGRX')
            pil_img = ImageEnhance.Brightness(pil_img).enhance(0.95)
            pil_img = ImageEnhance.Contrast(pil_img).enhance(1.5)
            pil_img = ImageEnhance.Sharpness(pil_img).enhance(4.0)
            far_img = ImageQt.ImageQt(pil_img)
            # pil_img.save(f"{dest_path}{os.path.sep}{index[2]}.png")
            # Rysowanie szkicu sytuacyjnego:
            src_rect = QRectF(0.0, 0.0, map_px, map_px)
            far_rect = QRectF(0.0, 0.0, map_px, map_px)
            near_rect = QRectF(map_px, 0.0, map_px, map_px)
            p = QPainter()
            p.setRenderHint(QPainter.Antialiasing)
            p.begin(comp_img)
            p.drawImage(far_rect, far_img, src_rect)
            p.drawImage(near_rect, near_img, src_rect)
            p.setPen(QPen(Qt.black, 4, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
            p.drawRect(2, 2, (map_px * 2) - 4, map_px - 4)
            p.drawLine(map_px, 0, map_px, map_px)
            p.setPen(QPen(Qt.black, 4, Qt.SolidLine, Qt.FlatCap, Qt.RoundJoin))
            title_rect = QRectF(831, 2, 514, 80)
            p.fillRect(title_rect, Qt.white)
            p.drawRect(title_rect)
            f = QFont()
            f.setPixelSize(40)
            p.setPen(Qt.black)
            p.setFont(f)
            title_rect.moveTop(0)
            p.drawText(title_rect, Qt.AlignCenter, "SZKIC LOKALIZACYJNY")
            p.end()
            comp_img.save(f"{self.szkice_path}{os.path.sep}{index[2]}.png", "PNG")
            comp_img = None
            # Usunięcie warstw z wyrobiskami:
            del wyr_far
            del wyr_near
            near_lyrs = near_lyrs[1:]
            far_lyrs = far_lyrs[1:]
        for lyr_name in lyr_names:
            dlg.proj.mapLayersByName(lyr_name)[0].loadNamedStyle(f'{STYLE_PATH}{lyr_name}.qml')

    def map_drawing(self, map_px, near_m, scl_px, img, ms, is_near):
        """Rysuje mapkę szkicu lokalizacyjnego. Jeśli is_near == True - rysowanie mapki zasadniczej, False - mapki orientacyjnej."""
        p = QPainter()
        p.setRenderHint(QPainter.Antialiasing)
        p.begin(img)
        # Rendering warstw i etykiet:
        render = QgsMapRendererCustomPainterJob(ms, p)
        render.start()
        render.waitForFinished()
        # Rysowanie podziałki liniowej:
        scl_path = QPainterPath()
        scl_start = 980 if is_near else 267
        y = 50 if is_near else 1052
        x1 = scl_start - scl_px  # Wspólrzędna X początku podziałki
        x2 = x1 + scl_px  # Wspólrzędna X końca podziałki
        scl_pg = self.scale_shape(x1, x2, y)  # Utworzenie kształtu podziałki
        scl_path.addPolygon(scl_pg)  # Dodanie kształtu do ścieżki
        # Utworzenie napisu dla podziałki liniowej:
        f = QFont()
        f.setPixelSize(24)
        f.setBold(True)
        # Dodanie napisu do ścieżki:
        if is_near:
            scl_path.addText(x2 + 10, 58, f, f"{near_m} m")
        else:
            scl_path.addText(x2 + 10, 1060, f, "1 km")
        p.setPen(QPen(Qt.white, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(scl_path)  # Narysowanie konturu (halo) podziałki białym kolorem
        p.fillPath(scl_path, Qt.black)  # Wypełnienie podziałki czarnym kolorem
        #  Utworzenie napisu informacyjnego o źródle podkładu:
        f.setBold(False)
        f.setPixelSize(28)
        src_path = QPainterPath()
        bm_name = "Geoportal" if is_near else "OpenStreetMap"
        src_path.addText(0, 1070, f, f"źródło: {bm_name}")
        x_off = int(round(map_px - src_path.boundingRect().width() - 30, 0))
        src_path.translate(x_off, 0)
        pen_color = Qt.black if is_near else Qt.white
        fill_color = Qt.white if is_near else Qt.black
        p.setPen(QPen(pen_color, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(src_path)
        p.fillPath(src_path, fill_color)
        p.end()

    def scale_width(self, map_cm, map_px, m_val, a):
        """Zwraca długość podziałki liniowej w px."""
        scl_m = (m_val * 2) / map_cm  # Ilość metrów w 1 cm szkicu
        scl_cm = a / scl_m  # Długość ustalonego odcinka podziałki na szkicu podana w cm
        scl_px = int(round(scl_cm * map_px / map_cm, 0))  # Przeliczenie odcinka podziałki z cm na px
        return scl_px

    def ms_create(self, lyrs, ext, img_size):
        """Zwraca obiekt mapki."""
        ms = QgsMapSettings()
        ms.setOutputDpi(300)
        ms.setLayers(lyrs)
        ms.setExtent(ext)
        ms.setOutputSize(img_size)
        ms.setDestinationCrs(lyrs[0].crs())
        return ms

    def img_create(self, width_px, height_px):
        """Tworzy i konfiguruje obiekt obrazka mapki."""
        img = QImage(QSize(width_px, height_px), QImage.Format_RGB32)
        img.setDotsPerMeterX(11811.0236220472)
        img.setDotsPerMeterY(11811.0236220472)
        return img

    def wyr_bbox(self, wyr_lyr):
        """Zwraca bbox wyrobiska."""
        if wyr_lyr.featureCount() > 0:
            for feat in wyr_lyr.getFeatures():
                return feat.geometry().boundingBox()

    def sketchmap_extent(self, box, m_val):
        """Zwraca zakres widoku mapki szkicu sytuacyjnego"""
        w_off = (m_val * 2 - box.width())/2
        h_off = (m_val * 2 - box.height())/2
        return QgsRectangle(box.xMinimum() - w_off, box.yMinimum() - h_off, box.xMaximum() + w_off, box.yMaximum() + h_off)

    def scale_interval(self, m_val):
        """Zwraca wartość odcinka podziałki na skali metrowej."""
        if m_val <= 25:
            return 5
        elif m_val <= 75:
            return 10
        elif m_val <= 250:
            return 50
        elif m_val <= 500:
            return 100
        else:
            return 500

    def scale_shape(self, x1, x2, y):
        """Zwraca geometrię do narysowania skali metrowej."""
        h = 8.0  # Wysokość "wąsów" na podziałce w px
        pts = [
                (x1 - 1, y - h),
                (x1 + 1, y - h),
                (x1 + 1, y - 2),
                (x2 - 1, y - 2),
                (x2 - 1, y - h),
                (x2 + 1, y - h),
                (x2 + 1, y + h),
                (x2 - 1, y + h),
                (x2 - 1, y + 2),
                (x1 + 1, y + 2),
                (x1 + 1, y + h),
                (x1 - 1, y + h),
                (x1 - 1, y - h)
                ]
        return QPolygonF([QPointF(p[0], p[1]) for p in pts])

    def wyr_to_lyr(self, wyr_id, stan_pne, near_far):
        """Tworzy warstwę tymczasową dla geometrii wyrobiska."""
        with CfgPars() as cfg:
            params = cfg.uri()
        if stan_pne == "brak":
            # Brak wyrobiska - wykorzystujemy geometrię punktową:
            uri = params + f'table="team_{dlg.team_i}"."wyrobiska" (centroid) sql=wyr_id = {wyr_id}'
            point_lyr = QgsVectorLayer(uri, "wyr_szkic", "postgres")
            if self.geom_check(point_lyr):
                return point_lyr
            else:
                return None
        else:
            # Geometria punktowa:
            uri_point = params + f'table="team_{dlg.team_i}"."wyrobiska" (centroid) sql=wyr_id = {wyr_id}'
            point_lyr = QgsVectorLayer(uri_point, "wyr_szkic", "postgres")
            # Geometria poligonalna:
            uri_poly = params + f'table="team_{dlg.team_i}"."wyr_geom" (geom) sql=wyr_id = {wyr_id}'
            poly_lyr = QgsVectorLayer(uri_poly, "wyr_szkic", "postgres")
            if near_far == "near":  # Bliski szkic - zwracamy geometrię poligonową:
                if self.geom_check(poly_lyr):
                    return poly_lyr
                else:
                    return self.lyr_if_valid(point_lyr)
            else:  # Daleki szkic - sprawdzamy wymiary geometrii i na tej podstawie zwracamy geometrię punktową albo poligonalną
                return self.point_or_poly(point_lyr, poly_lyr)

    def geom_check(self, lyr):
        """Zwraca, czy warstwa ma poprawną geometrię."""
        if not lyr.isValid():
            return False
        geom = None
        feats = lyr.getFeatures()
        for feat in feats:
            geom = feat.geometry()
        if geom.isGeosValid():
            return True

    def point_or_poly(self, point_lyr, poly_lyr):
        """Zwraca geometrię punktową lub poligonową w zależności od wymiarów wyrobiska."""
        if not self.geom_check(poly_lyr):
            return self.lyr_if_valid(point_lyr)
        geom = None
        feats = poly_lyr.getFeatures()
        for feat in feats:
            geom = feat.geometry()
        bbox = geom.boundingBox()
        if bbox.height() < 100 or bbox.width() < 100:
            return self.lyr_if_valid(point_lyr)
        else:
            return poly_lyr

    def lyr_if_valid(self, lyr):
        """Zwraca geometrię punktową, jeśli jest poprawna."""
        if self.geom_check(lyr):
            return lyr
        else:
            return None

    def wyr_for_pict(self):
        """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i wygenerowanymi numerami id_punkt."""
        db = PgConn()
        sql = f"SELECT p.wyr_id, concat(p.pow_id, '_', p.order_id) as id_punkt, d.i_ile_zalacz FROM team_{dlg.team_i}.wyr_prg AS p INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON p.wyr_id=d.wyr_id WHERE pow_grp = '{dlg.powiat_i}' and order_id IS NOT NULL ORDER BY order_id;"
        if db:
            mdf = db.query_pd(sql, ['wyr_id', 'id_punkt', 'foto_cnt'])
            if isinstance(mdf, pd.DataFrame):
                return mdf if len(mdf) > 0 else None
            else:
                return None

    def wyr_for_szkic(self, pow_grp):
        """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i wygenerowanymi numerami id_punkt."""
        db = PgConn()
        sql = f"SELECT p.wyr_id, concat(p.pow_id, '_', p.order_id) as id_punkt, d.t_stan_pne as stan_pne FROM team_{dlg.team_i}.wyr_prg AS p INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON p.wyr_id=d.wyr_id WHERE p.pow_grp = '{pow_grp}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
        if db:
            mdf = db.query_pd(sql, ['wyr_id', 'id_punkt', 'stan_pne'])
            if isinstance(mdf, pd.DataFrame):
                return mdf if len(mdf) > 0 else None
            else:
                return None

    def wyr_for_card(self):
        """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i atrybutami potrzebnymi do wygenerowania kart."""
        db = PgConn()
        sql = f"SELECT COALESCE(w.teren_id, p.wyr_id::varchar) AS id, CONCAT(p.pow_id, '_', p.order_id) AS id_punkt, d.date_ctrl, d.time_fchk, w.wn_id, p.t_mie_name, p.t_gmi_name, p.t_pow_name, p.t_woj_name, ST_X(w.centroid) as x_92, ST_Y(w.centroid) as y_92, CASE WHEN w.midas_id is null THEN false ELSE true END AS czy_zloze, w.midas_id, d.t_stan_midas, d.b_pne_zloze, d.b_pne_poza, d.t_stan_pne, d.t_zloze_od, d.t_zloze_do, d.t_wyr_od, d.t_wyr_do, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina AND d.wyr_id = p.wyr_id) AS kopalina, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina_2 AND d.wyr_id = p.wyr_id) AS kopalina_2, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek AND d.wyr_id = p.wyr_id) AS wiek, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek_2 AND d.wyr_id = p.wyr_id) AS wiek_2, d.n_nadkl_min, d.n_nadkl_max, d.n_miazsz_min, d.n_miazsz_max, d.i_dlug_min, d.i_dlug_max, d.i_szer_min, d.i_szer_max, d.n_wys_min, d.n_wys_max, d.i_area_m2, d.t_wyrobisko, d.t_zawodn, d.t_eksploat, d.t_wydobycie, d.t_odpady_1, d.t_odpady_2, d.t_odpady_3, d.t_odpady_4, d.t_wyp_odpady, d.t_odpady_opak, d.t_odpady_inne, d.t_rekultyw, d.t_dojazd, d.t_zagrozenia, d.t_zgloszenie, d.t_powod, d.i_ile_zalacz, w.t_notatki, d.t_autor FROM team_{dlg.team_i}.wyrobiska AS w INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE p.pow_grp = '{dlg.powiat_i}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
        if db:
            mdf = db.query_pd(sql, ['ID', 'ID_PUNKT', 'DATA', 'GODZ', 'ID_ARKUSZ', 'MIEJSCE', 'GMINA', 'POWIAT', 'WOJEWODZTWO', 'X_92', 'Y_92', 'CZY_ZLOZE', 'ID_MIDAS', 'STAN_MIDAS', 'PNE_ZLOZE', 'PNE_POZA', 'STAN_PNE', 'ZLOZE_OD', 'ZLOZE_DO', 'PNE_OD', 'PNE_DO', 'KOPALINA', 'KOPALINA_2', 'WIEK', 'WIEK_2', 'NADKL_MIN', 'NADKL_MAX', 'MIAZSZ_MIN', 'MIAZSZ_MAX', 'DLUG_MIN', 'DLUG_MAX', 'SZER_MIN', 'SZER_MAX', 'WYS_MIN', 'WYS_MAX', 'POW_M2', 'WYROBISKO', 'ZAWODN', 'EXPLOAT', 'WYDOBYCIE', 'ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4', 'WYP_ODPADY', 'O_OPAK', 'O_INNE', 'REKULTYW', 'DOJAZD', 'ZAGROZENIA', 'ZGLOSZENIE', 'POWOD', 'ILE_ZALACZ', 'UWAGI', 'AUTORZY'])
            if isinstance(mdf, pd.DataFrame):
                return mdf if len(mdf) > 0 else None
            else:
                return None

    def wyr_for_kml_green(self):
        """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i atrybutami potrzebnymi do eksportu mdb."""
        db = PgConn()
        sql = f"SELECT CONCAT(p.pow_id, '_', p.order_id) AS namefield, CONCAT(p.pow_id, '_', p.order_id) AS id_punkt, w.wn_id, CASE WHEN d.time_fchk IS NOT NULL THEN (d.date_ctrl + d.time_fchk) ELSE d.date_ctrl END AS data, p.t_mie_name, d.b_teren, d.b_pne, CASE COALESCE(w.midas_id, 'null_val') WHEN 'null_val' THEN false ELSE true END AS czy_zloze, w.midas_id, d.t_stan_midas, d.b_pne_zloze, d.b_pne_poza, d.t_stan_pne, d.t_zloze_od, d.t_zloze_do, d.t_wyr_od, d.t_wyr_do, d.t_kopalina, d.t_kopalina_2, d.t_wiek, d.t_wiek_2, d.n_nadkl_min, d.n_nadkl_max, d.n_miazsz_min, d.n_miazsz_max, d.i_dlug_min, d.i_dlug_max, d.i_szer_min, d.i_szer_max, d.n_wys_min, d.n_wys_max, d.i_area_m2, d.t_wyrobisko, d.t_zawodn, d.t_eksploat, d.t_wydobycie, d.t_wyp_odpady, d.t_odpady_1, d.t_odpady_2, d.t_odpady_3, d.t_odpady_4, d.t_stan_rekul, d.t_rekultyw, d.t_dojazd, d.t_zagrozenia, d.t_zgloszenie, d.t_powod, w.t_notatki, (SELECT t_autor FROM public.teams WHERE team_id = {dlg.team_i}), ST_X(w.centroid) as x_92, ST_Y(w.centroid) as y_92 FROM team_{dlg.team_i}.wyrobiska AS w INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE p.pow_grp = '{dlg.powiat_i}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
        if db:
            mdf = db.query_pd(sql, ['NAMEFIELD', 'ID_PUNKT', 'ID_ARKUSZ', 'DATA', 'MIEJSCE', 'CZY_TEREN', 'CZY_PNE', 'CZY_ZLOZE', 'ID_MIDAS', 'STAN_MIDAS', 'PNE_ZLOZE', 'PNE_POZA', 'STAN_PNE', 'ZLOZE_OD', 'ZLOZE_DO', 'PNE_OD', 'PNE_DO', 'KOPALINA', 'KOPALINA_2', 'WIEK', 'WIEK_2', 'NADKL_MIN', 'NADKL_MAX', 'MIAZSZ_MIN', 'MIAZSZ_MAX', 'DLUG_MIN', 'DLUG_MAX', 'SZER_MIN', 'SZER_MAX', 'WYS_MIN', 'WYS_MAX', 'POW_M2', 'WYROBISKO', 'ZAWODN', 'EXPLOAT', 'WYDOBYCIE', 'WYP_ODPADY', 'ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4', 'STAN_REKUL', 'REKULTYW', 'DOJAZD', 'ZAGROZENIA', 'ZGLOSZENIE', 'POWOD', 'UWAGI', 'AUTOR', 'X_92', 'Y_92'])
            if isinstance(mdf, pd.DataFrame):
                return mdf if len(mdf) > 0 else None
            else:
                return None

    def wyr_for_kml_red(self):
        """Zwraca dataframe z wyrobiskami/punktami odrzuconymi z danego powiatu."""
        db = PgConn()
        sql = f"SELECT w.wyr_id AS namefield, w.t_notatki AS descriptionfield, w.wyr_id AS wyr_id, w.wn_id AS wn_id, w.midas_id AS midas_id, d.t_wyr_od AS pne_od, d.t_wyr_do AS pne_do, d.t_zloze_od AS zloze_od, d.t_zloze_do AS zloze_do, w.t_notatki AS notatki, ST_X(w.centroid) as x_92, ST_Y(w.centroid) as y_92 FROM team_{dlg.team_i}.wyrobiska AS w INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE p.pow_grp = '{dlg.powiat_i}' and p.order_id IS NULL ORDER BY w.wyr_id;"
        if db:
            mdf = db.query_pd(sql, ['NAMEFIELD', 'DESCRIPTIONFIELD', 'wyr_id', 'wn_id', 'midas_id', 'pne_od', 'pne_do', 'zloze_od', 'zloze_do', 'notatki', 'X_92', 'Y_92'])
            if isinstance(mdf, pd.DataFrame):
                return mdf if len(mdf) > 0 else None
            else:
                return None

    def wyr_for_zal(self):
        """Zwraca dataframe z potwierdzonymi wyrobiskami z danego powiatu i atrybutami potrzebnymi do załącznika nr 1."""
        db = PgConn()
        sql = f"SELECT CONCAT(p.pow_id, '_', p.order_id) AS id_punkt, p.t_mie_name, p.t_gmi_name, d.b_pne, CASE COALESCE(w.midas_id, 'null_val') WHEN 'null_val' THEN false ELSE true END AS czy_zloze, w.midas_id, (SELECT s.t_desc FROM public.sl_stan_midas AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_stan_midas AND d.wyr_id = p.wyr_id) AS stan_midas, (SELECT s.t_desc FROM public.sl_stan_pne AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_stan_pne AND d.wyr_id = p.wyr_id) AS stan_pne, d.t_wyr_od, d.t_wyr_do, d.t_zloze_od, d.t_zloze_do, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina AND d.wyr_id = p.wyr_id) AS kopalina, (SELECT s.t_desc FROM public.sl_kopalina AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_kopalina_2 AND d.wyr_id = p.wyr_id) AS kopalina_2, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek AND d.wyr_id = p.wyr_id) AS wiek, (SELECT s.t_desc FROM public.sl_wiek AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wiek_2 AND d.wyr_id = p.wyr_id) AS wiek_2, d.i_area_m2, (SELECT s.t_desc FROM public.sl_eksploatacja AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_eksploat AND d.wyr_id = p.wyr_id) AS eksploatacja, (SELECT s.t_desc FROM public.sl_wydobycie AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wydobycie AND d.wyr_id = p.wyr_id) AS wydobycie, (SELECT s.t_desc FROM public.sl_wyp_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_wyp_odpady AND d.wyr_id = p.wyr_id) AS wyp_odpady, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_1 AND d.wyr_id = p.wyr_id) AS odpady_1, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_2 AND d.wyr_id = p.wyr_id) AS odpady_2, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_3 AND d.wyr_id = p.wyr_id) AS odpady_3, (SELECT s.t_desc FROM public.sl_rodz_odp AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_odpady_4 AND d.wyr_id = p.wyr_id) AS odpady_4, d.t_stan_rekul, d.t_rekultyw, d.t_zagrozenia, (SELECT s.t_desc FROM public.sl_zgloszenie AS s, team_{dlg.team_i}.wyr_dane AS d WHERE s.t_val = d.t_zgloszenie AND d.wyr_id = p.wyr_id) AS zgloszenie, d.t_powod, d.date_ctrl, CASE COALESCE(w.wn_id, 'null_val') WHEN 'null_val' THEN Null ELSE (SELECT e.data_kontrol FROM external.wn_pne AS e, team_{dlg.team_i}.wyrobiska AS w WHERE e.id_arkusz = w.wn_id AND w.wyr_id = p.wyr_id) END AS prev_date, w.t_notatki FROM team_{dlg.team_i}.wyrobiska AS w INNER JOIN team_{dlg.team_i}.wyr_dane AS d ON w.wyr_id=d.wyr_id INNER JOIN team_{dlg.team_i}.wyr_prg AS p ON w.wyr_id=p.wyr_id WHERE p.pow_grp = '{dlg.powiat_i}' and p.order_id IS NOT NULL ORDER BY p.order_id;"
        if db:
            mdf = db.query_pd(sql, ['ID_PUNKT', 'MIEJSCE', 'GMINA', 'CZY_PNE', 'CZY_ZLOZE', 'ID_MIDAS', 'STAN_MIDAS', 'STAN_PNE', 'PNE_OD', 'PNE_DO', 'ZLOZE_OD', 'ZLOZE_DO', 'KOPALINA', 'KOPALINA_2', 'WIEK', 'WIEK_2', 'POW_M2', 'EXPLOAT', 'WYDOBYCIE', 'WYP_ODPADY', 'ODPADY_1', 'ODPADY_2', 'ODPADY_3', 'ODPADY_4', 'STAN_REKUL', 'REKULTYW', 'ZAGROZENIA', 'ZGLOSZENIE', 'POWOD', 'DATE', 'PREV_DATE', 'UWAGI'])
            if isinstance(mdf, pd.DataFrame):
                return mdf if len(mdf) > 0 else None
            else:
                return None


class ExportTabBox(QFrame):
    """Widget wyświetlający przyciski do przełączania subpage'y w export_panel."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(494, 34)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)
        self.setLayout(self.lay)
        self.setStyleSheet(" QFrame {background-color: transparent; border: none} ")
        self.widgets = {}
        self.btns = [
            {"index": 0, "title": "   Kontrola terenowa   ", "active": True},
            {"index": 1, "title": "   Opracowanie końcowe   ", "active": True}
            ]
        for btn in self.btns:
            _btn = ExportTabButton(self, index=btn["index"], title=btn["title"], active=btn["active"])
            self.lay.addWidget(_btn)
            btn_idx = f'btn_{btn["index"]}'
            self.widgets[btn_idx] = _btn
        spacer = MoekDummy(width=1, height=34, color="rgba(20, 20, 20, 0.71)", spacer="horizontal")
        self.lay.addWidget(spacer)
        self.cur_idx = None

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cur_idx" and val != None:
            self.parent().parent().parent().sb.setCurrentIndex(val)
            self.btns_state()

    def btns_state(self):
        """Aktualizacja stanów przycisków."""
        for btn in self.btns:
            if btn["index"] == self.cur_idx:
                self.widgets[f'btn_{btn["index"]}'].setChecked(True)
            else:
                self.widgets[f'btn_{btn["index"]}'].setChecked(False)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        widgets = (self.lay.itemAt(i).widget() for i in range(self.lay.count()))
        for widget in widgets:
            if not widget:
                continue
            if isinstance(widget, (ExportTabButton, ExportTabButton, MoekDummy)):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)


class ExportTabButton(QPushButton):
    """Przyciski menu w TabBox'ie."""
    def __init__(self, *args, index, title, active):
        super().__init__(*args)
        self.index = index
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFixedHeight(34)
        self.setText(title)
        self.setCheckable(True)
        self.active = active
        self.set_style()
        self.clicked.connect(self.state_changed)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.set_style()

    def state_changed(self):
        """Aktualizacja bieżącego indeksu tabbox'u po naciśnięciu przycisku."""
        self.parent().cur_idx = self.index

    def set_style(self):
        """Modyfikacja stylesheet."""
        alpha_sub = 0.0 if self.active else 0.5
        self.setStyleSheet("""
                            QPushButton {
                                font-size: 8pt;
                                font-weight: bold;
                                color: rgba(255, 255, 255, """ + str(0.8 - alpha_sub) + """);
                                background-color: rgba(20, 20, 20, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            QPushButton:hover {
                                font-size: 8pt;
                                font-weight: bold;
                                color: rgba(255, 255, 255, """ + str(1.0 - alpha_sub) + """);
                                background-color: rgba(20, 20, 20, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            QPushButton:disabled {
                                font-size: 8pt;
                                font-weight: bold;
                                color: rgba(55, 55, 55, """ + str(1.0 - alpha_sub) + """);
                                background-color: rgba(20, 20, 20, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            QPushButton::checked:disabled {
                                font-size: 8pt;
                                font-weight: bold;
                                color: rgba(120, 120, 120, """ + str(1.0 - alpha_sub) + """);
                                background-color: rgba(40, 40, 40, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            QPushButton:checked {
                                font-size: 8pt;
                                font-weight: bold;
                                color: rgba(255, 255, 255, """ + str(1.0 - alpha_sub) + """);
                                background-color: rgba(55, 55, 55, 0.71);
                                border: none;
                                padding: 6px;
                                text-align: center;
                            }
                            """)


class FchkExportSelector(QFrame):
    """Belka z przyciskami do zaznaczania/odznaczania wszystkich elementów eksportu do kontroli terenowej."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.lay = QGridLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(5)
        self.setLayout(self.lay)
        self.select_all = AllSelectorItem(self, txt="Zaznacz wszystko", select=True)
        self.select_all.clicked
        self.deselect_all = AllSelectorItem(self, txt="Odznacz wszystko", select=False)
        self.lay.addWidget(self.select_all, 0, 0, 1, 1)
        self.lay.addWidget(self.deselect_all, 0, 1, 1, 1)
        self.chkboxes = {}
        itms = [
            {'row' : 1, 'name' : 'wyr', 'txt' : 'Wyrobiska (wyr_point, wyr_poly)', 'lyr' : ['wyr_point', 'wyr_poly']},
            {'row' : 2, 'name' : 'flagi_z_teren', 'txt' : 'Flagi z kontrolą terenową (flagi_z_teren)', 'lyr' : ['flagi_z_teren']},
            {'row' : 3, 'name' : 'flagi_bez_teren', 'txt' : 'Flagi bez kontroli terenowej (flagi_bez_teren)', 'lyr' : ['flagi_bez_teren']},
            {'row' : 4, 'name' : 'midas_zloza', 'txt' : 'Złoża (midas_zloza)', 'lyr' : ['midas_zloza']},
            {'row' : 5, 'name' : 'midas_wybilansowane', 'txt' : 'Złoża wybilansowane (midas_wybilansowane)', 'lyr' : ['midas_wybilansowane']},
            {'row' : 6, 'name' : 'midas_obszary', 'txt' : 'Obszary górnicze (midas_obszary)', 'lyr' : ['midas_obszary']},
            {'row' : 7, 'name' : 'midas_tereny', 'txt' : 'Tereny górnicze (midas_tereny)', 'lyr' : ['midas_tereny']},
            {'row' : 8, 'name' : 'wn_pne', 'txt' : 'PNE z WN Kopaliny (wn_pne)', 'lyr' : ['wn_pne']},
            {'row' : 9, 'name' : 'parking', 'txt' : 'Miejsca parkingowe (parking)', 'lyr' : ['parking']},
            {'row' : 10, 'name' : 'marsz', 'txt' : 'Marszruty (marsz)', 'lyr' : ['marsz']}
            ]
        for itm in itms:
            _itm = CanvasCheckBox(self, name=itm["txt"], checked=True)
            self.lay.addWidget(_itm, itm["row"], 0, 1, 2)
            _itm.clicked.connect(self.btn_clicked)
            itm_name = f'chkbox_{itm["name"]}'
            self.chkboxes[itm_name] = _itm
        self.init_void = True
        self.chk_cnt = 10
        self.init_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "chk_cnt" and not self.init_void:
            dlg.export_panel.export_btn_enabler()

    def btn_clicked(self):
        """Aktualizuje liczbę zaznaczonych checkbox'ów po naciśnięciu któregoś z nich."""
        cnt = 0
        for chkbox in self.chkboxes:
            _chkbox = self.chkboxes[chkbox]
            if _chkbox.isChecked():
                cnt += 1
        self.chk_cnt = cnt

    def all_clicked(self, _bool):
        """Ustawienie stanu wszystkich checkbox'ów po naciśnięciu przycisku."""
        for chkbox in self.chkboxes:
            _chkbox = self.chkboxes[chkbox]
            _chkbox.setChecked(_bool)
        self.chk_cnt = 10 if _bool else 0

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        widgets = (self.lay.itemAt(i).widget() for i in range(self.lay.count()))
        for widget in widgets:
            widget.set_enabled(_bool)


class AllSelectorItem(QPushButton):
    """Guzik do wyboru aktywnych typów danych do eksportu."""
    def __init__(self, *args, txt, select):
        super().__init__(*args)
        self.setCheckable(False)
        self.setChecked(False)
        self.setText(txt)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(34)
        self.setStyleSheet("""
                            QPushButton {
                                border: 1px solid rgb(154, 154, 154);
                                background: rgba(255, 255, 255, 0.2);
                                color: rgb(255, 255, 255);
                                font-size: 10pt;
                            }
                            QPushButton:hover {
                                border: 1px solid rgb(180, 180, 180);
                                background: rgba(255, 255, 255, 0.4);
                                color: rgb(255, 255, 255);
                                font-size: 10pt;
                            }
                            QPushButton:disabled {
                                border: 1px solid rgb(80, 80, 80);
                                background: rgba(80, 80, 80, 0.2);
                                color: rgb(100, 100, 100);
                                font-size: 10pt;
                            }
                           """)
        self.clicked.connect(lambda: self.parent().all_clicked(select))

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)


class TypeFchkExportSelector(QFrame):
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
        self.lay.setSpacing(5)
        self.setLayout(self.lay)
        self.valid_check = False
        self.itms = {}
        self.file_types = [
            {'name' : 'gpkg', 'multiplier' : 1},
            {'name' : 'kml', 'multiplier' : 2},
            {'name' : 'shp', 'multiplier' : 4}
            ]
        for file_type in self.file_types:
            _itm = TypeFchkExportSelectorItem(self, name=file_type["name"])
            self.lay.addWidget(_itm)
            itm_name = f'btn_{file_type["name"]}'
            self.itms[itm_name] = _itm

    def btn_clicked(self):
        """Zmiana wartości 'fchk_case' po naciśnięciu przycisku."""
        case = 0
        for i_dict in self.file_types:
            btn = self.itms[f'btn_{i_dict["name"]}']
            val = 1 if btn.isChecked() else 0
            case = case + (val * i_dict["multiplier"])
        dlg.export_panel.fchk_case = case

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        widgets = (self.lay.itemAt(i).widget() for i in range(self.lay.count()))
        for widget in widgets:
            widget.set_enabled(_bool)


class TypeFchkExportSelectorItem(QPushButton):
    """Guzik do wyboru aktywnych typów danych do eksportu."""
    def __init__(self, *args, name):
        super().__init__(*args)
        self.setCheckable(True)
        self.setChecked(False)
        self.name = name
        self.setText(self.name)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
                            QPushButton {
                                border: 1px solid rgb(154, 154, 154);
                                background: rgba(255, 255, 255, 0.2);
                                color: rgb(255, 255, 255);
                                font-size: 11pt;
                            }
                            QPushButton:hover {
                                border: 1px solid rgb(180, 180, 180);
                                background: rgba(255, 255, 255, 0.4);
                                color: rgb(255, 255, 255);
                                font-size: 11pt;
                            }
                            QPushButton:checked {
                                border: 1px solid rgb(240, 240, 240);
                                background: rgba(255, 255, 255, 0.6);
                                color: rgb(0, 0, 0);
                                font-size: 11pt;
                            }
                            QPushButton:hover:checked {
                                border: 1px solid rgb(255, 255, 255);
                                background: rgb(255, 255, 255);
                                color: rgb(0, 0, 0);
                                font-size: 11pt;
                            }
                            QPushButton:disabled {
                                border: 1px solid rgb(80, 80, 80);
                                background: rgba(80, 80, 80, 0.2);
                                color: rgb(100, 100, 100);
                                font-size: 11pt;
                            }
                           """)
        self.clicked.connect(self.parent().btn_clicked)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)


class WarningNotificator(QFrame):
    """Belka zmiany statusu wyrobiska."""
    def __init__(self, *args, raport=None):
        super().__init__(*args)
        self.setObjectName("main")
        self.setCursor(Qt.WhatsThisCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(28, 28)
        self.setStyleSheet("""
                            QFrame#main{
                                background-color: transparent;
                                border: none
                            }
                            QToolTip {
                                border: 1px solid rgb(50, 50, 50);
                                padding: 5px;
                                background-color: rgb(30, 30, 30);
                                color: rgb(200, 200, 200);
                            }
                        """)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)
        self.setLayout(self.lay)
        self.valid_check = False
        self.itms = {}
        self.statuses = [
            {'id' : 1, 'name' : 'warning_blue'},
            {'id' : 2, 'name' : 'warning_red'},
            {'id' : 0, 'name' : 'warning_red'}
            ]
        for status in self.statuses:
            _itm = WarningNotificatorItem(self, name=status["name"], size=28, checkable=False, id=status["id"])
            self.lay.addWidget(_itm)
            itm_name = f'btn_wrn_{status["id"]}'
            self.itms[itm_name] = _itm
        self.case = 0
        self.active = False
        self.excel = False
        self.raport = raport

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.setVisible(val)
        elif attr == "case":
            self.case_change()
        elif attr == "excel":
            self.setCursor(Qt.PointingHandCursor) if val else self.setCursor(Qt.WhatsThisCursor)

    def case_change(self):
        """Dostosowanie widoczności przycisków do aktualnego statusu notyfikatora."""
        for itm in self.itms.values():
            itm.setVisible(True) if itm.id == self.case and self.case != 0 else itm.setVisible(False)
        # Sprawdzenie, czy nie trzeba zmienić blokadę przycisku eksportu danych dla powiatu:
        if not self.parent().init_void:
            if dlg.export_panel.tab_box.cur_idx == 1:
                dlg.export_panel.check_red_warning()

    def set_enabled(self, _bool):
        self.active =_bool

    def set_tooltip(self, txt):
        """Ustawienie tooltip'a."""
        self.setToolTip(txt)
        self.excel = True if txt == "otwórz raport" else False

    def btn_clicked(self):
        if self.raport and self.excel:
            exec(self.raport)


class WarningNotificatorItem(QToolButton):
    """Guzik do wyboru statusu wyrobiska."""
    def __init__(self, *args, id, size=28, hsize=0, name="", icon="", visible=True, enabled=True, checkable=False, tooltip=""):
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
        self.clicked.connect(lambda: self.parent().btn_clicked())

    def set_icon(self, name, size=32, hsize=0):
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
        self.setIcon(icon)


class PhotoOptionBar(QFrame):
    """Belka z radiobutton'ami opcji optymalizacji rozmiarów zdjęć."""
    def __init__(self, *args):
        super().__init__(*args)
        self. setObjectName("main")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label = PanelLabel(self, text="Optymalizacja wielkości plików:", color="170, 170, 170", size=9)
        self.radio_tak = QRadioButton(text="Tak (Zalecane, wolniej)", parent=self)
        self.radio_nie = QRadioButton(text="Nie (Szybciej)", parent=self)
        self.radio_tak.toggled.connect(self.chkbox_enable)
        self.temp_chkbox = CanvasCheckBox(self, name="Twórz pliki tymczasowe (Przyspiesza kolejne eksporty)", font=8)
        self.temp_chkbox.stateChanged.connect(self.chkbox_change)
        self.glay = QGridLayout()
        self.glay.setContentsMargins(15, 0, 15, 5)
        self.glay.setSpacing(0)
        self.glay.addWidget(self.label, 0, 0)
        self.glay.addWidget(self.radio_tak, 0, 1)
        self.glay.addWidget(self.radio_nie, 0, 2)
        self.glay.addWidget(self.temp_chkbox, 1, 1, 1, 2)
        self.group = QButtonGroup()
        self.group.setExclusive(True)
        self.group.addButton(self.radio_tak)
        self.group.addButton(self.radio_nie)
        self.setLayout(self.glay)
        self.temp_on = False
        self.temp_chkbox.setChecked(True)
        self.radio_tak.setChecked(True)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    QRadioButton {
                        color: rgb(170, 170, 170);
                        font-size: 8pt;
                        spacing: 2px;
                    }
                    QRadioButton:disabled {
                        color: rgba(170, 170, 170, 0.4);
                    }
                    QRadioButton::indicator {
                        width: 25px;
                        height: 25px;
                    }
                    QRadioButton::indicator:unchecked {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_0.png');
                    }
                    QRadioButton::indicator:unchecked:hover {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_0_act.png');
                    }
                    QRadioButton::indicator:unchecked:pressed {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_1_act.png');
                    }
                    QRadioButton::indicator:checked {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_1.png');
                    }
                    QRadioButton::indicator:checked:hover {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_1_act.png');
                    }
                    QRadioButton::indicator:checked:pressed {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_0_act.png');
                    }
                    QRadioButton::indicator:disabled {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_dis.png');
                    }
                    """)

    def chkbox_enable(self, _bool):
        """Włącza/wyłącza self.photo_temp_chkbox."""
        self.temp_chkbox.set_enabled(_bool)
        self.set_temp()

    def chkbox_change(self, state):
        """Zmiana stanu self.temp_chkbox."""
        self.set_temp()

    def set_temp(self):
        """Ustala wartość self.temp_on."""
        self.temp_on = True if self.radio_tak.isChecked() and self.temp_chkbox.isChecked() else False

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        widgets = (self.glay.itemAt(i).widget() for i in range(self.glay.count()))
        for widget in widgets:
            if not widget:
                continue
            if isinstance(widget, QRadioButton):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)


class MdbOptionBar(QFrame):
    """Belka z checkboxem eksportowania kml'a z odrzuconymi wyrobiskami."""
    def __init__(self, *args):
        super().__init__(*args)
        self. setObjectName("main")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label = PanelLabel(self, text="Dodatkowo:", color="170, 170, 170", size=9)
        self.chkbox = CanvasCheckBox(self, name="Wyrobiska odrzucone", font=8)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 5)
        self.hlay.setSpacing(0)
        spacer_1 = QSpacerItem(32, 1, QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.hlay.addItem(spacer_1)
        self.hlay.addWidget(self.label)
        spacer_2 = QSpacerItem(10, 1, QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.hlay.addItem(spacer_2)
        self.hlay.addWidget(self.chkbox)
        spacer_3 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.hlay.addItem(spacer_3)
        self.setLayout(self.hlay)
        self.chkbox.setChecked(True)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        widgets = (self.hlay.itemAt(i).widget() for i in range(self.hlay.count()))
        for widget in widgets:
            if not widget:
                continue
            if isinstance(widget, QRadioButton):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)


class SzkicOptionBar(QFrame):
    """Belka z radiobutton'ami opcji generowania szkiców lokalizacyjnych."""
    def __init__(self, *args):
        super().__init__(*args)
        self. setObjectName("main")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label = PanelLabel(self, text="Szkice lokalizacyjne:", color="170, 170, 170", size=9)
        self.radio_1 = QRadioButton(text="Stwórz nowe", parent=self)
        self.radio_2 = QRadioButton(text="Wykorzystaj istniejące", parent=self)
        self.radio_3 = QRadioButton(text="Karty bez szkiców", parent=self)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 5)
        self.hlay.setSpacing(0)
        spacer_1 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.hlay.addItem(spacer_1)
        self.hlay.addWidget(self.label)
        spacer_2 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.hlay.addItem(spacer_2)
        self.hlay.addWidget(self.radio_1)
        self.hlay.addWidget(self.radio_2)
        self.hlay.addWidget(self.radio_3)
        spacer_3 = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.hlay.addItem(spacer_3)
        self.group = QButtonGroup()
        self.group.setExclusive(True)
        self.group.addButton(self.radio_1)
        self.group.addButton(self.radio_2)
        self.group.addButton(self.radio_3)
        self.setLayout(self.hlay)
        self.radio_1.setChecked(True)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    QRadioButton {
                        color: rgb(170, 170, 170);
                        font-size: 8pt;
                        spacing: 2px;
                    }
                    QRadioButton:disabled {
                        color: rgba(170, 170, 170, 0.4);
                    }
                    QRadioButton::indicator {
                        width: 25px;
                        height: 25px;
                    }
                    QRadioButton::indicator:unchecked {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_0.png');
                    }
                    QRadioButton::indicator:unchecked:hover {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_0_act.png');
                    }
                    QRadioButton::indicator:unchecked:pressed {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_1_act.png');
                    }
                    QRadioButton::indicator:checked {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_1.png');
                    }
                    QRadioButton::indicator:checked:hover {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_1_act.png');
                    }
                    QRadioButton::indicator:checked:pressed {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_0_act.png');
                    }
                    QRadioButton::indicator:disabled {
                        image: url('""" + ICON_PATH.replace("\\", "/") + """cp_radio_dis.png');
                    }
                    """)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.setEnabled(_bool)
        widgets = (self.hlay.itemAt(i).widget() for i in range(self.hlay.count()))
        for widget in widgets:
            if not widget:
                continue
            if isinstance(widget, QRadioButton):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)


class CanvasCheckBoxPanel(CanvasHSubPanel):
    """Belka canvaspanel'u z checkboxem i notyfikatorem."""
    def __init__(self, *args, title="", validator=None, raport=None):
        super().__init__(*args, height=38, margins=[5, 0, 5, 0], spacing=5, alpha=0.71, disable_color="40, 40, 40", disable_void=False)
        self.setObjectName("main")
        self.setFixedHeight(38)
        self.chkbox = CanvasCheckBox(self, name=title)
        self.chkbox.setChecked(True)
        self.chkbox.stateChanged.connect(self.chkbox_change)
        self.lay.addWidget(self.chkbox)
        spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.lay.addItem(spacer)
        self.init_void = True
        self.warning = WarningNotificator(self, raport=raport)
        self.lay.addWidget(self.warning)
        self.validator = validator
        self.checked = True
        self.init_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "checked" and not self.init_void:
            if self.chkbox.isChecked() != val:
                self.init_void = True
                self.chkbox.setChecked(val)
                self.init_void = False
            self.parent().greyed = not val
            if not val:
                self.warning.case = 0
            if self.validator:
                exec(self.validator)
            if dlg.export_panel.tab_box.cur_idx == 1:
                dlg.export_panel.check_red_warning()

    def chkbox_change(self):
        self.checked = self.chkbox.isChecked()

    def checkbox_update(self):
        if self.validator:
                exec(self.validator)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        widgets = (self.lay.itemAt(i).widget() for i in range(self.lay.count()))
        for widget in widgets:
            if not widget:
                continue
            elif isinstance(widget, (MoekButton, QProgressBar)):
                widget.setEnabled(_bool)
            elif isinstance(widget, CanvasCheckBox):
                if self.parent().greyed and not dlg.export_panel.path_void:
                    widget.setEnabled(True)
                else:
                    widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)
        self.set_style()

    def set_style(self):
        """Modyfikacja stylesheet."""
        if self.isEnabled():
            try:
                color = self.color if not self.parent().greyed and not dlg.export_panel.path_void else self.disable_color
            except:
                color = self.color
        else:
            color = self.disable_color
        self.setStyleSheet("""
                    QFrame#main{background-color: rgba(""" + color + """, """ + str(self.alpha) + """); border: none}
                    """)


class MoekVBoxGreyed(MoekVBox):
    """Kontener, w którym poza checkboxem występują elementy mogące zostać wyszarzone (kiedy checkbox jest odznaczony)."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.greyed = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "greyed":
            self.set_enabled(not val)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        if self.greyed and _bool:
            _bool = False
        widgets = (self.lay.itemAt(i).widget() for i in range(self.lay.count()))
        for widget in widgets:
            if isinstance(widget, (MoekButton, QProgressBar)):
                widget.setEnabled(_bool)
            else:
                widget.set_enabled(_bool)


class ExportProgressBar(QFrame):
    """Progressbar eksportu danych powiatu."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("main")
        self.setFixedSize(445, 34)
        self.bar = QProgressBar(self)
        self.bar.setFixedHeight(34)
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(True)
        hlay = QHBoxLayout()
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(0)
        hlay.addWidget(self.bar)
        self.setLayout(hlay)
        self.setStyleSheet("""
                    QFrame#main{background-color: transparent; border: none}
                    """)
        self.active = False
        self.progress = 0
        self.text = str()

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.bar.setVisible(val)
        elif attr == "text":
            self.bar.setFormat(val)
        elif attr == "progress":
            if not isinstance(val, (int, float)):
                self.bar.setValue(0)
            else:
                self.bar.setValue(val)

    def set_enabled(self, _bool):
        """Włączenie/wyłączenie elementów widget'u zewnętrznym poleceniem."""
        self.bar.active = _bool

    def set_progress(self, val):
        """Ustawia wartość progress."""
        self.progress = val

    def set_text(self, val):
        """Ustawia wartość progress."""
        self.text = val