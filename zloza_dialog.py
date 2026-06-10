# -*- coding: utf-8 -*-
import os
import datetime
import pandas as pd

from qgis.core import QgsApplication, QgsRectangle, QgsFeature, QgsExpressionContextUtils
from qgis.PyQt.QtCore import Qt, QModelIndex
from qgis.PyQt.QtGui import QTextCursor
from qgis.PyQt.QtWidgets import QDialog, QTextEdit, QSizePolicy, QSpacerItem, QFrame, QLabel
from qgis.PyQt import uic

from .classes import ZlozaDFM, KopalinyDFM, DokDFM, PgConn, CfgPars
from .main import active_pow_listed, pg_layer_change, stage_refresh, db_attr_change
from .widgets import ParamBox


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'zloza_dialog.ui'))

class ZlozaDialog(QDialog, FORM_CLASS):
    """Okno dialogowe do zarządzania złożami."""
    def __init__(self, plg, parent=None):
        super(ZlozaDialog, self).__init__(parent)
        self.plg = plg
        self.dlg = self.plg.dockwidget
        self.proj = plg.proj
        self.canvas = plg.canvas
        self.setupUi(self)
        self.init_void = True
        self.zl_id = None
        self.zl_checked = None
        self.zl_exclusion = None
        self.is_excluded_show = False
        self.zl_stanzag = None
        self.frm_details.setVisible(False)
        self.frm_dok.setVisible(False)
        self.frm_filter.setVisible(False)
        self.frm_exclusion.setVisible(False)
        self.frm_kop.setVisible(True)
        self.btn_kop.setVisible(False)
        self.sep_line_1.setVisible(True)
        self.sep_line_2.setVisible(False)
        self.btn_refresh.clicked.connect(self.df_zloza_update)
        self.btn_exclude.clicked.connect(self.zl_exclude_change)
        self.btn_checked.clicked.connect(self.zl_checked_change)
        self.btn_exclusion_add.clicked.connect(self.exclusion_add)
        self.cmb_stanzag.currentIndexChanged.connect(self.stanzag_changed)
        self.df_zloza = pd.DataFrame(columns=['check', 'midas_id', 'kopalina gł.', 'kop_tooltip', 'stan zag. wg MIDAS', 'stan zag.', 'stan_tooltip', 'źr. geometrii', 'wył.'])
        self.df_kopaliny = pd.DataFrame(columns=['kop_typ_id', '', 'typ kopaliny', 'ranga kopaliny', 'stan zagospodarowania'])
        self.df_dok = pd.DataFrame(columns=['cbdg_id', 'tytuł', 'rok', 'nr inw.', 'nr kat.', 'rep_inw', 'rep_kat'])
        self.init_tv_zloza()
        self.init_tv_kopaliny()
        self.init_tv_dok()
        self.init_exclusion()
        self.init_notes()
        self.init_history()
        self.init_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "zl_id" and not self.init_void:
            # Przekazanie id wybranego złoża do modelu tableview'u:
            self.mdl_zloza.sel_id = val
            if not val:
                return
            # Aktualizacja 'tv_kopaliny':
            sql = f"SELECT DISTINCT ON (k.sys_typ_id) k.sys_typ_id, k.kop_typ_id, s.t_kop_typ_symbol, s.t_kop_typ_nazwa, k.t_kop_ranga, k.t_stan_zag FROM zloza.zl_kopaliny AS k INNER JOIN zloza.sl_kop_typ AS s ON s.kop_typ_id = k.kop_typ_id WHERE k.midas_id = {val} ORDER BY k.sys_typ_id"
            cols = ['sys_typ_id', 'kop_typ_id', '', 'typ kopaliny', 'ranga kopaliny', 'stan zagospodarowania']
            df = self.df_from_db(sql, cols) if val else pd.DataFrame(columns=['kop_typ_id', '', 'typ kopaliny', 'ranga kopaliny', 'stan zagospodarowania'])
            df = df.sort_values(by=['ranga kopaliny']).reset_index(drop=True)
            self.df_kopaliny = df
            # Ukrycie 'frm_dok':
            self.frm_dok.setVisible(False)
            # Aktualizacja zawartości 'frm_head':
            l_zl = self.get_zloze_name(val) if val else None
            self.l_zl.setText(f"[{l_zl[0]}] {l_zl[1]}" if val else "")
            # Aktualizacja 'frm_history':
            self.zl_history_update()
            # Aktualizacja 'txt_notes':
            self.zl_notes_update()
            # Ustawienie widoczności'frm_details':
            self.frm_details.setVisible(False) if val == None else self.frm_details.setVisible(True)
        elif attr == "df_zloza" and not self.init_void:
            # Aktualizacja zawartości 'tv_zloza' po zmianie w 'df_zloza':
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            self.mdl_zloza.setDataFrame(val)
            QgsApplication.restoreOverrideCursor()
        elif attr == "df_kopaliny" and not self.init_void:
            # Aktualizacja zawartości 'tv_kopaliny' po zmianie w 'df_kopaliny':
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            self.mdl_kopaliny.setDataFrame(val)
            QgsApplication.restoreOverrideCursor()
        elif attr == "df_dok" and not self.init_void:
            # Aktualizacja zawartości 'tv_dok' po zmianie 'df_zloza':
            self.mdl_dok.setDataFrame(val)
        elif attr == "zl_checked" and not self.init_void:
            # Aktualizacja stanu zatwierdzenia analizy złoża:
            self.set_checked_state(val)
        elif attr == "zl_exclusion" and not self.init_void:
            # Aktualizacja stanu widget'ów z 'frm_exclusion':
            self.set_exclude_state(val)
        elif attr == "zl_stanzag" and not self.init_void:
            # Aktualizacja stanu 'cmb_stanzag':
            self.cmb_void = True
            if not val:
                self.cmb_stanzag.setCurrentText("stan zagosp. zgodny z MIDAS")
                self.cmb_stanzag.setStyleSheet("QComboBox{padding-left:18; background-color: rgb(225, 225, 225); selection-background-color: rgb(0, 120, 215)}")
            else:
                self.cmb_stanzag.setCurrentText(val)
                self.cmb_stanzag.setStyleSheet("QComboBox{padding-left:18; background-color: rgb(60, 170, 255); selection-background-color: rgb(0, 120, 215)}")
            self.cmb_void = False

    def init_tv_zloza(self):
        """Utworzenie tableview'a 'tv_zloza'."""
        self.mdl_zloza = ZlozaDFM(df=self.df_zloza, tv=self.tv_zloza)
        self.tv_zloza.selectionModel().selectionChanged.connect(self.tv_zloza_change)

    def init_tv_kopaliny(self):
        """Utworzenie tableview'a 'tv_kopaliny'."""
        self.mdl_kopaliny = KopalinyDFM(df=self.df_kopaliny, tv=self.tv_kopaliny)
        # self.tv_kopaliny.selectionModel().selectionChanged.connect(self.tv_kopaliny_change)

    def init_tv_dok(self):
        """Utworzenie tableview'a 'tv_dok'."""
        self.mdl_dok = DokDFM(df=self.df_dok, tv=self.tv_dok)
        self.tv_dok.clicked.connect(self.open_dok_folder)

    def init_exclusion(self):
        """Utworzenie widget'ów z 'frm_exclusion'."""
        # Ustawienie combobox'a:
        causes = [
            "Eksploatacja podziemna.",
            "Brak możliwości zlokalizowania złoża."
        ]
        self.cmb_exclusion.addItems(causes)
        # Ustawienie textedit:
        fn = ['self.db_update(txt_val=self.cur_val, tbl="zloza.main", attr="t_exclusion", sql_bns=f" WHERE midas_id = {self.zl_id}")']
        self.txt_exclusion = ZlozaTextBox(zl_dlg=self, editable=True, fn=fn)
        self.frm_exclusion.layout().addWidget(self.txt_exclusion)
        spacer = QSpacerItem(1, 2000, QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.frm_exclusion.layout().addItem(spacer)

    def init_notes(self):
        """Utworzenie widget'ów z 'frm_notes'."""
        fn = ['self.db_update(txt_val=self.cur_val, tbl="zloza.main", attr="t_notatki", sql_bns=f" WHERE midas_id = {self.zl_id}")']
        self.txt_notes = ZlozaTextBox(zl_dlg=self, editable=True, fn=fn)
        self.frm_notes.layout().addWidget(self.txt_notes)

    def init_history(self):
        """Utworzenie widget'ów z 'frm_history'."""
        date_info = [
            ("date_dok_s", "data udokumentowania złoża", 0),
            ("date_kon_s", "data ustanowienia koncesji", 1),
            ("date_kon_exp", "termin ważności koncesji", 2),
            ("date_kon_e", "data wygaśnięcia koncesji", 3),
            ("date_dok_e", "data wybilansowania złoża", 4),
        ]
        for date_key, label_text, column in date_info:
            date_widget = ZlozaDateBox(self.plg, date_key)
            self.frm_dates.layout().addWidget(date_widget, 1, column)
            self.frm_dates.layout().setAlignment(date_widget, Qt.AlignCenter)
            label = QLabel()
            label.setText(label_text)
            label.setAlignment(Qt.AlignCenter)
            self.frm_dates.layout().addWidget(label, 0, column)
            self.frm_dates.layout().setAlignment(label, Qt.AlignCenter)
            # Utworzenie dynamicznych atrybutów z dostępem w obrębie klasy:
            setattr(self, f"l_{date_key}", label)
            setattr(self, date_key, date_widget)

    def init_stanzag(self):
        """Wczytanie wartości 't_stan_zag' z tabeli 'zloza.main' i ustawienie wg niej combobox'a."""
        if not self.zl_id:
            return
        sql = f"SELECT t_stan_zag FROM zloza.main WHERE midas_id = {self.zl_id}"
        self.zl_stanzag = self.db_select(sql)[0]

    def stanzag_changed(self):
        """Zmiana wartości 't_stan_zag' w bazie danych."""
        if self.cmb_void:
            return
        self.zl_stanzag = None if self.cmb_stanzag.currentText() == "stan zagosp. zgodny z MIDAS" else self.cmb_stanzag.currentText()
        sql_val = "NULL" if self.zl_stanzag == None else f"'{self.zl_stanzag}'"
        sql = f"UPDATE zloza.main SET t_stan_zag = {sql_val} WHERE midas_id = {self.zl_id}"
        result = self.db_update(sql)
        if not result:
            print(f"Błąd zmiany wartości 't_stan_zag' dla złoża {self.zl_id} w tabeli 'zloza.main'.")
        self.df_zloza_update()

    def open_dok_folder(self):
        """Otworzenie eksploratora plików ze ścieżką do dokumentacji, jeśli jest dostępna."""
        sel_tv = self.tv_dok.selectionModel()
        index = sel_tv.currentIndex()
        dok_num = self.mdl_dok.data(index, "ClickRole")
        if dok_num:
            self.plg.scraper.open_dok_folder(dok_num)

    def tv_zloza_change(self):
        """Zmiana selekcji wiersza w 'tv_zloza'."""
        sel_tv = self.tv_zloza.selectionModel()
        index = sel_tv.currentIndex()
        # Aktualizacja zaznaczonego wiersza w 'tv_zloza':
        if index.row() != -1:
            zl_id = int(index.sibling(index.row(), 1).data())
            if zl_id != self.zl_id:
                self.zl_id = zl_id
            self.zl_checked = index.sibling(index.row(), 0).data()  # WARNING: Należy zaktualizować numer kolumny, jeśli struktura 'tv_zloza' ulegnie zmianie
            self.zl_exclusion = index.sibling(index.row(), 8).data()  # WARNING: Należy zaktualizować numer kolumny, jeśli struktura 'tv_zloza' ulegnie zmianie
            self.init_stanzag()
        else:
            self.zl_id = None
            self.zl_exclusion = None
        self.zl_lyr_update()

    def get_zl_ids(self):
        """Zwraca listę złóż z obszaru podanych powiatów."""
        pows = False if self.dlg.p_pow.is_active() else active_pow_listed()
        db = PgConn()
        extras = f" WHERE pow_id IN ({str(pows)[1:-1]})" if pows else f" WHERE pow_id = '{self.plg.dockwidget.powiat_i}'"
        sql = "SELECT DISTINCT midas_id FROM zloza.zl_powiaty" + extras + " ORDER BY midas_id;"
        if db:
            res = db.query_sel(sql, True)
            if res:
                if len(res) > 1:
                    return list(zip(*res))[0]
                else:
                    return list(res[0])
            else:
                return None

    def zl_exclude_change(self):
        """Zmiana wartości 'b_exclusion' aktualnego złoża w tabeli 'zloza.main'."""
        if self.zl_id == None:
            return
        val = 'true' if self.zl_exclusion == 'False' else 'false'
        sql = f"UPDATE zloza.main SET b_exclusion = {val} WHERE midas_id = {self.zl_id}"
        result = self.db_update(sql)
        if not result:
            print(f"Błąd przy próbie zmiany 'b_exclusion' dla złoża {self.zl_id} w tabeli 'zloza_main'.")
        # Reset 'b_checked', jeśli złoże zostało wyłączone:
        if self.zl_exclusion == 'False':
            sql = f"UPDATE zloza.main SET b_checked = false WHERE midas_id = {self.zl_id}"
            result = self.db_update(sql)
            if not result:
                print(f"Błąd przy próbie zmiany 'b_checked' dla złoża {self.zl_id} w tabeli 'zloza_main'.")
        self.df_zloza_update()

    def zl_checked_change(self):
        """Zmiana wartości 'b_checked' aktualnego złoża w tabeli 'zloza.main'."""
        if self.zl_id == None:
            return
        val = 'true' if self.zl_checked == '0' else 'false'
        sql = f"UPDATE zloza.main SET b_checked = {val} WHERE midas_id = {self.zl_id}"
        result = self.db_update(sql)
        if not result:
            print(f"Błąd przy próbie zmiany 'b_checked' dla złoża {self.zl_id} w tabeli 'zloza_main'")
        self.df_zloza_update()

    def set_checked_state(self, state):
        """Ustawienie UI w zależności od 'zl_checked'."""
        # Ustalenie stylu 'btn_checked':
        if state == '1':  # Analiza jest zakończona
            self.btn_checked.setStyleSheet("QPushButton {background-color: rgb(160, 255, 100)}")
            self.btn_checked.setText("Analiza zakończona")
        else:
            self.btn_checked.setStyleSheet("QPushButton {}")
            self.btn_checked.setText("Zakończ analizę")

    def set_exclude_state(self, state):
        """Ustawienie UI w zależności od 'zl_exclusion'."""
        self.btn_exclude.setVisible(False) if not state else self.btn_exclude.setVisible(True)
        if state == 'True':  # Złoże jest wyłączone
            # Ustalenie stylu 'btn_exclude':
            self.btn_exclude.setStyleSheet("QPushButton {background-color: rgb(160, 255, 100)}")
            self.btn_exclude.setText("Włącz złoże")
            # Resetowanie combobox'a:
            self.cmb_exclusion.setCurrentIndex(-1)
            # Załadowanie tekstu do 'txt_exclusion':
            sql = f"SELECT t_exclusion FROM zloza.main WHERE midas_id = {self.zl_id}"
            exclusion_text = self.db_select(sql)[0]
            self.txt_exclusion.set_value(exclusion_text) if exclusion_text else self.txt_exclusion.set_value(None)
            # Ustawienie widoczności widget'ów:
            self.frm_exclusion.setVisible(True)
            self.frm_kop.setVisible(False)
            self.frm_history.setVisible(False)
            self.frm_notes.setVisible(False)
            self.btn_checked.setVisible(False)
            # self.sep_line_2.setVisible(False)
        else:  # Złoże nie jest wyłączone
            # Ustalenie stylu 'btn_exclude':
            self.btn_exclude.setStyleSheet("QPushButton {background-color: rgb(255, 130, 100)}")
            self.btn_exclude.setText("Wyłącz złoże")
            # Ustawienie widoczności widget'ów:
            self.frm_exclusion.setVisible(False)
            self.frm_kop.setVisible(True)
            self.frm_history.setVisible(True)
            self.frm_notes.setVisible(True)
            self.btn_checked.setVisible(True)

    def exclusion_add(self):
        """Przeniesienie tekstu powodu wyłączenia złoża z combobox'a do textedit'a."""
        if self.cmb_exclusion.currentIndex() == -1:
            return
        self.txt_exclusion.add_value(self.cmb_exclusion.currentText())
        self.cmb_exclusion.setCurrentIndex(-1)

    def zl_excluded_layer_update(self):
        """Aktualizacja zawartości warstwy 'midas_wylaczone', jeśli jest konieczna."""
        if not self.is_excluded_show and self.zl_exclusion == 'False':
            return
        excluded_layer = self.dlg.proj.mapLayersByName("midas_wylaczone")[0]
        self.is_excluded_show = False if self.is_excluded_show and self.zl_exclusion == 'False' else True
        with CfgPars() as cfg:
            params = cfg.uri()
        uri = f'''{params} key="fid" table="(SELECT row_number() OVER (ORDER BY v.midas_id) AS fid, v.midas_id AS midas_id, v.ver_id, g.t_pole AS pole, g.geom AS geom FROM zloza.geom_ver AS v INNER JOIN (SELECT midas_id, ver_id, t_pole, geom FROM zloza.geom) AS g ON v.midas_id = g.midas_id AND v.ver_id = g.ver_id INNER JOIN zloza.main AS m ON m.midas_id = v.midas_id WHERE v.midas_id = {self.zl_id} and m.b_exclusion IS true)" (geom) sql='''
        pg_layer_change(uri, excluded_layer)
        stage_refresh()

    def zl_lyr_update(self):
        """Aktualizacja widoku mapy po wybraniu złoża."""
        # Ustawienie zmiennej projektu do podświetlania geometrii wybranego złoża za pomocą stylu warstwy:
        QgsExpressionContextUtils.setProjectVariable(self.proj, 'zl_sel', self.zl_id)
        self.zl_excluded_layer_update()
        lyr = self.proj.mapLayersByName("midas_wylaczone")[0] if self.is_excluded_show else self.proj.mapLayersByName("midas_zloza")[0]
        lyr.triggerRepaint()
        if not self.zl_id:
            self.tv_zloza.setCurrentIndex(QModelIndex())
            self.frm_details.setVisible(False)
            return
        iter = lyr.getFeatures(f'"midas_id" = {self.zl_id}')
        try:
            # Przybliżenie zakresu wyświetlania mapy do obszaru złoża z marginesem:
            feat = QgsFeature()
            iter.nextFeature(feat)
            box = feat.geometry().boundingBox()
            while iter.nextFeature(feat):
                box.combineExtentWith(feat.geometry().boundingBox())
            if not box.width() and not box.height():
                print(f"Złoże {self.zl_id} nie ma geometrii")
                return
            w_off = box.width() * 0.2
            h_off = box.height() * 0.2
            ext = QgsRectangle(box.xMinimum() - w_off,
                                box.yMinimum() - h_off,
                                box.xMaximum() + w_off,
                                box.yMaximum() + h_off
                                )
            self.canvas.setExtent(ext)
        except Exception as err:
            print(f"Nie udało się przybliżyć widoku mapy do złoża {self.zl_id}")

    def zl_notes_update(self):
        """Aktualizacja 'txt_notes' po wybraniu złoża."""
        # Zapisanie w bazie danych aktualnego tekstu, jeśli widget jest w trybie edycji (dla poprzednio wybranego złoża):
        if self.txt_notes.edit:
            self.txt_notes.value_change(self.txt_notes.toPlainText())
            self.txt_notes.edit = False
            self.txt_notes.clearFocus()
        # Wczytanie tekstu notatki aktualnie wybranego złoża do 'txt_notes':
        if not self.zl_id:
            return
        sql = f"SELECT t_notatki FROM zloza.main WHERE midas_id = {self.zl_id}"
        notes_text = self.db_select(sql)[0]
        self.txt_notes.set_value(notes_text) if notes_text and len(notes_text) > 0 else self.txt_notes.set_value(None)

    def zl_history_update(self):
        """Aktualizacja widget'ów 'frm_history' po wybraniu złoża."""
        if not self.zl_id:
            return
        # Stworzenie rekordu dla złoża w bazie danych, jeśli jeszcze nie istnieje:
        if not self.db_record_exists('zloza.zl_dates'):
            self.db_create_record('zloza.zl_dates')
        # Pobranie dat z bazy danych:
        sql = f"SELECT date_dok_s, date_dok_e, date_kon_s, date_kon_e, date_kon_exp FROM zloza.zl_dates WHERE midas_id = {self.zl_id}"
        cols = ['date_dok_s', 'date_dok_e', 'date_kon_s', 'date_kon_e', 'date_kon_exp']
        df_dates = self.df_from_db(sql, cols)
        self.date_dok_s.set_value(str(df_dates.loc[0, 'date_dok_s']))
        self.date_dok_e.set_value(str(df_dates.loc[0, 'date_dok_e']))
        self.date_kon_s.set_value(str(df_dates.loc[0, 'date_kon_s']))
        self.date_kon_e.set_value(str(df_dates.loc[0, 'date_kon_e']))
        self.date_kon_exp.set_value(str(df_dates.loc[0, 'date_kon_exp']))

    def df_zloza_update(self):
        """Ładowanie danych do 'df_zloza'."""
        zl_ids = self.get_zl_ids()
        # Załadowanie danych do 'tv_zloza':
        sql = f"SELECT m.b_checked, m.midas_id, m.t_kop_typ_symbol, k.t_kop_typ_nazwa, s.t_stan_symbol, m.t_stan_zag, m.t_stan_zag_midas, COALESCE(m.t_geom, 'BRAK'), m.b_exclusion FROM zloza.main m INNER JOIN zloza.sl_zloza_stan s ON m.t_stan_zag_midas = s.t_zloze_stan INNER JOIN zloza.sl_kop_typ k ON m.kop_typ_id = k.kop_typ_id WHERE midas_id IN {zl_ids} ORDER BY midas_id;"
        cols = ['check', 'midas_id', 'kopalina gł.', 'kop_tooltip', 'stan zag. wg MIDAS', 'stan zag.', 'stan_tooltip', 'źr. geometrii', 'wył.']
        df_zloza = self.df_from_db(sql, cols)
        self.df_zloza = df_zloza
        # Odznaczenie 'midas_id', jeśli nie ma go na zaktualizowanej liście:
        if self.zl_id and self.zl_id not in zl_ids:
            self.zl_id = None
        # Zmiana zawartości warstw ze złożami:
        with CfgPars() as cfg:
            params = cfg.uri()
        uri = f'''{params} key="fid" table="(SELECT row_number() OVER (ORDER BY v.midas_id) AS fid, v.midas_id AS midas_id, v.ver_id, g.t_pole AS pole, g.geom AS geom FROM zloza.geom_ver AS v INNER JOIN (SELECT midas_id, ver_id, t_pole, geom FROM zloza.geom) AS g ON v.midas_id = g.midas_id AND v.ver_id = g.ver_id INNER JOIN zloza.main AS m ON m.midas_id = v.midas_id WHERE v.midas_id IN {zl_ids} and m.b_exclusion IS false)" (geom) sql='''
        lyr = self.dlg.proj.mapLayersByName("midas_zloza")[0]
        pg_layer_change(uri, lyr)
        stage_refresh()

    def get_zloze_name(self, id):
        """Zwraca nazwę złoża na podstawie 'midas_id'."""
        sql = f"SELECT midas_id, t_zloze_nazwa FROM zloza.sl_zloza_nazwa WHERE midas_id = {id}"
        res = self.db_select(sql, False)
        return res if res else ("", "")

    def db_select(self, sql, all=False):
        """Zwraca wynik kwerendy SELECT."""
        db = PgConn()
        if db:
            res = db.query_sel(sql, all)
            return res if res else None

    def db_update(self, sql):
        """Wykonuje kwerendę UPDATE."""
        db = PgConn()
        if db:
            res = db.query_upd(sql)
            return True if res else False

    def df_from_db(self, sql, cols=[]):
        """Zwraca dataframe ze wskazanymi kolumnami i danymi uzyskanymi z kwerendy sql."""
        empty_df = pd.DataFrame(columns=cols)
        db = PgConn()
        if db:
            df = db.query_pd(sql, cols)
            if isinstance(df, pd.DataFrame):
                return df if len(df) > 0 else empty_df
            else:
                return empty_df
        else:
            return empty_df

    def db_record_exists(self, tbl):
        """Sprawdza, czy w podanej tabeli istnieje rekord dotyczący aktualnego złoża."""
        sql = f"SELECT midas_id FROM {tbl} WHERE midas_id = {self.zl_id}"
        res = self.db_select(sql, False)
        return True if res else False

    def db_create_record(self, tbl):
        """Utworzenie rekordu dla aktualnego złoża w podanej tabeli z bazy danych."""
        sql = f"INSERT INTO {tbl} (midas_id) VALUES ({self.zl_id})"
        res = self.db_update(sql)
        if not res:
            print(f"Error in db_create_record(): {res}")

    def closeEvent(self, event):
        """Zamknięcie okna dialogowego."""
        self.tv_zloza.setCurrentIndex(QModelIndex())


class ZlozaTextBox(QTextEdit):
    """Wyświetla tekst z możliwością edycji i zapisu zmian w bazie danych."""
    def __init__(self, *args, zl_dlg, editable, fn=None):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(150)
        self.zl_dlg = zl_dlg
        self.fn = fn
        self.setReadOnly(not editable)
        if not editable:
            self.viewport().setCursor(Qt.ArrowCursor)
        self.setStyleSheet("QTextEdit{background-color: white; padding-left:10; padding-top:10; padding-bottom:10; padding-right:10; font-size:10pt;}")
        self.edit = False
        self.zl_id = None
        self.attr_void = True
        self.cur_val = None
        self.attr_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cur_val" and not self.attr_void:
            self.value_changed()

    def set_value(self, val):
        """Próba zmiany wartości."""
        if not val or len(str(val)) == 0:  # Empty value
            self.cur_val = None
        else:
            self.cur_val = val

    def add_value(self, val):
        """Próba dodania wartości do tekstu."""
        self.cur_val = f"{self.cur_val} {val}" if self.cur_val else val
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.setFocus(True)

    def db_update(self, txt_val, tbl, attr, sql_bns):
        """Aktualizacja tekstu w bazie danych."""
        if not txt_val:
            sql_text = "NULL"
        else:
            txt = txt_val.replace("'", "''")
            sql_text = f"'{txt}'"
        self.db_attr_change(tbl=tbl, attr=attr, val=sql_text, sql_bns=sql_bns)

    def value_change(self, txt):
        """Zmiana tekstu w bazie danych i z 'cur_val'."""
        self.set_value(txt)
        if self.fn:
            self.run_fn()

    def value_changed(self):
        """Aktualizacja tekstu po zmianie wartości."""
        self.setPlainText(self.cur_val) if self.cur_val else self.clear()

    def db_attr_change(self, tbl, attr, val, sql_bns):
        """Zmiana wartości atrybutu w bazie danych."""
        # print("[db_attr_change(", tbl, ",", attr, "):", val, "]")
        db = PgConn()
        if len(str(val)) == 0:
            val = 'Null'
        sql = f"UPDATE {tbl} SET {attr} = {val}{sql_bns};"
        if db:
            res = db.query_upd(sql)
            if res:
                return True
            else:
                return False
        else:
            return False

    def run_fn(self):
        """Wywołanie funkcji po zmianie tekstu."""
        for fn in self.fn:
            try:
                exec(eval("f'{}'".format(fn)))
            except Exception as err:
                print(f"[run_fn] Błąd przy wprowadzaniu zmiany w bazie danych: {err}")

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.edit = True
        # Zapamiętanie wartości zmiennych - mogą już być zmienione podczas focusOutEvent:
        self.zl_id = self.zl_dlg.zl_id

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.edit:
            return
        self.value_change(self.toPlainText())
        self.edit = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.clearFocus()
        else:
            super().keyPressEvent(event)


class ZlozaDateBox(QFrame):
    """Widget ustalania dla wyrobiska daty aktualności fotomapy."""
    def __init__(self, plg, attr, *args, fn=None):
        super().__init__(*args)
        self.setObjectName("main")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(110, 38)
        self.setStyleSheet("QFrame#main{background-color: transparent; border: none}")
        self.dicts = [
                    {"name": "self.dd", "width": 32, "title_down": "DD", "max_len": 2, "validator": "days", "zero_allowed": False},
                    {"name": "self.dm", "width": 32, "title_down": "MM", "max_len": 2, "validator": "months", "zero_allowed": False},
                    {"name": "self.dy", "width": 40, "title_down": "RRRR", "max_len": 4, "validator": "years", "zero_allowed": False}
                    ]
        for dict in self.dicts:
            fn = ['self.parent().parent().parent().val_changed()']
            _txt2 = ParamBox(self, item="line_edit", max_len=dict["max_len"], validator=dict["validator"], height=26, down_height=12, font_size=10, width=dict["width"], value=" ", val_width=dict["width"], title_down=dict["title_down"], zero_allowed=dict["zero_allowed"], fn=[fn], theme="light")
            exec(f'{dict["name"]} = _txt2')
        self.dd.setGeometry(0, 0, self.dd.width(), self.dd.height())
        self.dm.setGeometry(35, 0, self.dm.width(), self.dm.height())
        self.dy.setGeometry(70, 0, self.dy.width(), self.dy.height())
        self.plg = plg
        self.attr = attr
        self.val_void = True
        self.d_val = None
        self.dd_val = None
        self.dm_val = None
        self.dy_val = None
        self.val_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "dd_val" and not self.val_void:
            self.dd.valbox_1.set_value(val)
        if attr == "dm_val" and not self.val_void:
            self.dm.valbox_1.set_value(val)
        if attr == "dy_val" and not self.val_void:
            self.dy.valbox_1.set_value(val)

    def val_changed(self):
        """Zmieniono wartość jednej z części daty."""
        part_vals = [
            ["self.dd_val", self.dd.valbox_1.text()],
            ["self.dm_val", self.dm.valbox_1.text()],
            ["self.dy_val", self.dy.valbox_1.text()]
        ]
        for part_val in part_vals:
            if len(part_val[1]) == 0:
                # Konwersja pustej wartości:
                new_val = None
            else:
                new_val = part_val[1]
            cur_val = eval(part_val[0])
            if cur_val != new_val:
                # Aktualizacja zmienionej wartości:
                exec(f'{part_val[0]} = new_val')
                # Zmieniono część daty:
                if self.dy_val and (not self.dm_val and part_val[0] != "self.dm_val"):
                    # Autouzupełnienie miesiąca:
                    self.dm_val = "01"
                if self.dy_val and (not self.dd_val and part_val[0] != "self.dd_val"):
                    # Autouzupełnienie dnia:
                    self.dd_val = "01"
                if (part_val[0] == "self.dy_val" and not self.dy_val) or (part_val[0] == "self.dm_val" and not self.dm_val) or (part_val[0] == "self.dd_val" and not self.dd_val):
                    # Reset daty po zmianie wartości na "pustą":
                    self.date_reset()
                    return
                if self.dy_val and self.dm_val and self.dd_val:
                    # Wszystkie części są uzupełnione - ustalenie daty:
                    try:
                        self.d_val = datetime.date(int(self.dy_val), int(self.dm_val), int(self.dd_val))
                    except ValueError:
                        return
                d_sql = self.sql_parser(self.d_val)
                db_attr_change(tbl=f'zloza.zl_dates', attr=self.attr, val=d_sql, sql_bns=f' WHERE midas_id = {self.plg.zl_dlg.zl_id}', user=False)
                self.focus_switcher(part_val[0])
                return

    def sql_parser(self, val):
        """Zwraca wartość prawidłową dla formuły sql."""
        return f"'{val}'" if val else 'Null'

    def focus_switcher(self, obj_txt):
        """Przejście do kolejnego pustego parambox'a."""
        val_list = ["self.dd_val","self.dm_val", "self.dy_val"]
        obj_list = ["self.dd.valbox_1", "self.dm.valbox_1", "self.dy.valbox_1"]
        txt_list = [self.dd.valbox_1.text(), self.dm.valbox_1.text(), self.dy.valbox_1.text()]
        idx = -1
        i = -1
        for val in val_list:
            i += 1
            if val == obj_txt:
                idx = i
                break
        if idx == -1:
            return
        if idx == 0:
            if txt_list[1] == "" or txt_list[1] == "01":
                exec(f"{obj_list[1]}.setFocus()")
        elif idx == 1:
            if len(txt_list[2]) == 0:
                exec(f"{obj_list[2]}.setFocus()")
            elif len(txt_list[2]) > 0 and (txt_list[0] == "" or txt_list[0] == "01"):
                exec(f"{obj_list[0]}.setFocus()")

    def date_reset(self):
        """Kasowanie wartości daty."""
        self.d_val = None
        self.dd_val = None
        self.dm_val = None
        self.dy_val = None
        d_sql = self.sql_parser(self.d_val)
        db_attr_change(tbl=f'zloza.zl_dates', attr={self.attr}, val=d_sql, sql_bns=f' WHERE midas_id = {self.plg.zl_dlg.zl_id}', user=False)

    def set_value(self, val):
        """Ustawienie wartości parambox'ów według danych z db."""
        # Ustalenie aktualnych wartości daty:
        if not val == 'None':
            self.d_val = datetime.datetime.date(datetime.datetime.strptime(val, "%Y-%m-%d"))
            self.dy_val = str(self.d_val.year)
            self.dm_val = str(self.d_val.month).zfill(2)
            self.dd_val = str(self.d_val.day).zfill(2)
        else:
            self.d_val = None
            self.dy_val = None
            self.dm_val = None
            self.dd_val = None
