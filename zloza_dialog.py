# -*- coding: utf-8 -*-
import os
import pandas as pd

from qgis.core import QgsApplication, QgsRectangle, QgsFeature, QgsExpressionContextUtils
from qgis.PyQt.QtCore import Qt, QModelIndex
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic

from .classes import ZlozaDFM, KopalinyDFM, PgConn, CfgPars
from .main import active_pow_listed, pg_layer_change

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
        self.zl_exclusion = None
        self.frm_details.setVisible(False)
        self.frm_dok.setVisible(False)
        self.frm_update.setVisible(False)
        self.frm_filter.setVisible(False)
        self.frm_exclusion.setVisible(False)
        self.frm_kop.setVisible(True)
        self.btn_kop.setVisible(False)
        self.sep_line_1.setVisible(True)
        self.sep_line_2.setVisible(False)
        self.btn_refresh.clicked.connect(self.df_zloza_update)
        self.df_zloza = pd.DataFrame(columns=['check', 'midas_id', 'kopalina gł.', 'kop_tooltip', 'stan zag. wg MIDAS', 'stan_tooltip', 'źr. geometrii', 'wył.'])
        self.df_kopaliny = pd.DataFrame(columns=['kop_typ_id', '', 'typ kopaliny', 'ranga kopaliny', 'stan zagospodarowania'])
        self.init_tv_zloza()
        self.init_tv_kopaliny()
        self.init_void = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "df_zloza" and not self.init_void:
            # Aktualizacja zawartości 'tv_zloza' po zmianie w 'df_zloza':
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            self.mdl_zloza.setDataFrame(val)
            QgsApplication.restoreOverrideCursor()
        elif attr == "df_kopaliny" and not self.init_void:
            # Aktualizacja zawartości 'tv_kopaliny' po zmianie w 'df_kopaliny':
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            self.mdl_kopaliny.setDataFrame(val)
            QgsApplication.restoreOverrideCursor()
        elif attr == "zl_id" and not self.init_void:
            # Przekazanie id wybranego złoża do modelu tableview'u:
            self.mdl_zloza.sel_id = val
            # Aktualizacja 'tv_kopaliny':
            sql = f"SELECT DISTINCT ON (k.sys_typ_id) k.sys_typ_id, k.kop_typ_id, s.t_kop_typ_symbol, s.t_kop_typ_nazwa, k.t_kop_ranga, k.t_stan_zag FROM zloza.zl_kopaliny AS k INNER JOIN zloza.sl_kop_typ AS s ON s.kop_typ_id = k.kop_typ_id WHERE k.midas_id = {val} ORDER BY k.sys_typ_id"
            cols = ['sys_typ_id', 'kop_typ_id', '', 'typ kopaliny', 'ranga kopaliny', 'stan zagospodarowania']
            df = self.df_from_db(sql, cols) if val else pd.DataFrame(columns=['kop_typ_id', '', 'typ kopaliny', 'ranga kopaliny', 'stan zagospodarowania'])
            df = df.sort_values(by=['ranga kopaliny']).reset_index(drop=True)
            self.df_kopaliny = df
            # Aktualizacja zawartości 'frm_head':
            l_zl = self.get_zloze_name(val) if val else None
            self.l_zl.setText(f"[{l_zl[0]}] {l_zl[1]}" if val else "")
            # Ustawienie widoczności'frm_details':
            self.frm_details.setVisible(False) if val == None else self.frm_details.setVisible(True)
            # Ustawienie zmiennej projektu do podświetlania geometrii wybranego złoża za pomocą stylu warstwy:
            QgsExpressionContextUtils.setProjectVariable(self.proj, 'zl_sel', val)
            lyr = self.proj.mapLayersByName("midas_zloza")[0]
            lyr.triggerRepaint()
            if not val:
                self.tv_zloza.setCurrentIndex(QModelIndex())
                self.frm_details.setVisible(False)
                return
            iter = lyr.getFeatures(f'"midas_id" = {val}')
            try:
                # Przybliżenie zakresu wyświetlania mapy do obszaru złoża z marginesem:
                feat = QgsFeature()
                iter.nextFeature(feat)
                box = feat.geometry().boundingBox()
                while iter.nextFeature(feat):
                    box.combineExtentWith(feat.geometry().boundingBox())
                if not box.width() and not box.height():
                    print(f"Złoże {val} nie ma geometrii")
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
                print(f"Nie udało się przybliżyć widoku mapy do złoża {val}")

    def init_tv_zloza(self):
        """Utworzenie tableview'a 'tv_zloza'."""
        self.mdl_zloza = ZlozaDFM(df=self.df_zloza, tv=self.tv_zloza)
        self.tv_zloza.selectionModel().selectionChanged.connect(self.tv_zloza_change)

    def init_tv_kopaliny(self):
        """Utworzenie tableview'a 'tv_kopaliny'."""
        self.mdl_kopaliny = KopalinyDFM(df=self.df_kopaliny, tv=self.tv_kopaliny)
        # self.tv_kopaliny.selectionModel().selectionChanged.connect(self.tv_kopaliny_change)

    def tv_zloza_change(self):
        """Zmiana selekcji wiersza w 'tv_zloza'."""
        sel_tv = self.tv_zloza.selectionModel()
        index = sel_tv.currentIndex()
        # Aktualizacja zaznaczonego wiersza w 'tv_zloza':
        if index.row() != -1:
            zl_id = int(index.sibling(index.row(), 1).data())
            if zl_id != self.zl_id:
                self.zl_id = zl_id
            self.zl_exclusion = index.sibling(index.row(), 7).data()  # WARNING: Należy zaktualizować numer kolumny, jeśli struktura 'tv_zloza' ulegnie zmianie
        else:
            self.zl_id = None
            self.zl_exlusion = None

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

    def df_zloza_update(self):
        """Ładowanie danych do 'df_zloza'."""
        zl_ids = self.get_zl_ids()
        # Załadowanie danych do 'tv_zloza':
        sql = f"SELECT m.b_checked, m.midas_id, m.t_kop_typ_symbol, k.t_kop_typ_nazwa, s.t_stan_symbol, m.t_stan_zag, COALESCE(m.t_geom, 'BRAK'), m.b_exclusion FROM zloza.main m INNER JOIN zloza.sl_zloza_stan s ON m.t_stan_zag = s.t_zloze_stan INNER JOIN zloza.sl_kop_typ k ON m.kop_typ_id = k.kop_typ_id WHERE midas_id IN {zl_ids} ORDER BY midas_id;"
        cols = ['check', 'midas_id', 'kopalina gł.', 'kop_tooltip', 'stan zag. wg MIDAS', 'stan_tooltip', 'źr. geometrii', 'wył.']
        df_zloza = self.df_from_db(sql, cols)
        self.df_zloza = df_zloza
        # Odznaczenie 'midas_id', jeśli nie ma go na zaktualizowanej liście:
        if self.zl_id and self.zl_id not in zl_ids:
            self.zl_id = None
        # Zmiana zawartości warstw ze złożami:
        with CfgPars() as cfg:
            params = cfg.uri()
        uri = f'''{params} key="fid" table="(SELECT row_number() OVER (ORDER BY v.midas_id) AS fid, v.midas_id AS midas_id, v.ver_id, g.t_pole AS pole, g.geom AS geom FROM zloza.geom_ver AS v INNER JOIN (SELECT midas_id, ver_id, t_pole, geom FROM zloza.geom) AS g ON v.midas_id = g.midas_id AND v.ver_id = g.ver_id WHERE v.midas_id IN {zl_ids})" (geom) sql='''
        lyr = self.dlg.proj.mapLayersByName("midas_zloza")[0]
        pg_layer_change(uri, lyr)

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

    def closeEvent(self, event):
        """Zamknięcie okna dialogowego."""
        self.zl_id = None
