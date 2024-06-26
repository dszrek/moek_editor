# -*- coding: utf-8 -*-
import os

from qgis.core import QgsApplication, QgsRasterLayer, QgsVectorLayer, QgsField, QgsLayerTreeLayer, QgsCoordinateReferenceSystem
from qgis.PyQt.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QVariant
from qgis.utils import iface
from datetime import datetime

from .classes import CfgPars, PgConn
from .main import flag_layer_update, wyr_layer_update, parking_layer_update, marsz_layer_update

# Zmienne globalne:
dlg = None
with CfgPars() as cfg:
    PARAMS = cfg.uri()
CRS_1992 = QgsCoordinateReferenceSystem("EPSG:2180")
UI_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep
STYLE_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'styles' + os.path.sep

def dlg_layers(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

class LayerManager:
    """Menedżer warstw projektu."""
    def __init__(self, dlg):
        self.root = dlg.proj.layerTreeRoot()
        self.groups_tree = [
            {'level': 0, 'layers': ['powiaty', 'arkusze', 'powiaty_mask']},
            {'name': 'wyrobiska', 'level': 1, 'layers': ['wyr_szare', 'wyr_fioletowe', 'wyr_zielone', 'wyr_poly']},
            {'name': 'flagi', 'level': 1, 'layers': ['flagi_z_teren', 'flagi_bez_teren']},
            # {'name': 'komunikacja', 'level': 1, 'layers': ['parking_planowane', 'parking_odwiedzone', 'marszruty']},
            # {'name': 'wn_kopaliny', 'level': 1, 'layers': ['wn_pne', 'wn_link']},
            {'name': 'vn', 'level': 1, 'layers': ['vn_sel', 'vn_user', 'vn_other', 'vn_null', 'vn_all']},
            {'name': 'MIDAS', 'level': 1, 'layers': ['midas_zloza', 'midas_wybilansowane', 'midas_obszary', 'midas_tereny']},
            {'name': 'MGSP', 'level': 1, 'layers': ['mgsp_pkt_kop', 'mgsp_zloza_p', 'mgsp_zloza_a', 'mgsp_zloza_wb_p', 'mgsp_zloza_wb_a']},
            {'name': 'basemaps', 'level': 1, 'layers': ['ISOK'], 'subgroups': ['sat', 'topo']},
            {'name': 'sat', 'level': 2, 'parent': 'basemaps', 'layers': ['Google Satellite', 'Google Hybrid', 'Geoportal', 'Geoportal Archiwalny', 'Google Earth Pro']},
            {'name': 'topo', 'level': 2, 'parent': 'basemaps', 'layers': ['Google Map', 'OpenStreetMap', 'Topograficzna', 'BDOT', 'BDOO']},
            {'name': 'temp', 'level': 1, 'layers': ['wyr_point', 'edit_poly', 'backup_poly']}
            ]
        self.lyrs = [
            {"source": "postgres", "name": "wyr_zielone", "root": False, "parent": "wyrobiska", "visible": True, "uri": '{PARAMS} table="team_0"."wyrobiska" (centroid) sql='},
            {"source": "postgres", "name": "wyr_fioletowe", "root": False, "parent": "wyrobiska", "visible": True, "uri": '{PARAMS} table="team_0"."wyrobiska" (centroid) sql='},
            {"source": "postgres", "name": "wyr_szare", "root": False, "parent": "wyrobiska", "visible": True, "uri": '{PARAMS} table="team_0"."wyrobiska" (centroid) sql='},
            {"source": "postgres", "name": "wyr_poly", "root": False, "parent": "wyrobiska", "visible": True, "uri": '{PARAMS} table="team_0"."wyr_geom" (geom) sql='},
            {"source": "postgres", "name": "flagi_z_teren", "root": False, "parent": "flagi", "visible": True, "uri": '{PARAMS} table="team_0"."flagi" (geom) sql='},
            {"source": "postgres", "name": "flagi_bez_teren", "root": False, "parent": "flagi", "visible": True, "uri": '{PARAMS} table="team_0"."flagi" (geom) sql='},
            # {"source": "postgres", "name": "parking_planowane", "root": False, "parent": "komunikacja", "visible": True, "uri": '{PARAMS} table="team_0"."parking" (geom) sql='},
            # {"source": "postgres", "name": "parking_odwiedzone", "root": False, "parent": "komunikacja", "visible": True, "uri": '{PARAMS} table="team_0"."parking" (geom) sql='},
            # {"source": "postgres", "name": "marszruty", "root": False, "parent": "komunikacja", "visible": True, "uri": '{PARAMS} table="team_0"."marsz" (geom) sql='},
            # {"source": "postgres", "name": "wn_pne", "root": False, "parent": "wn_kopaliny", "visible": True, "uri": '{PARAMS} table="external"."wn_pne" (geom) sql='},
            # {"source": "memory", "name": "wn_link", "root": False, "parent": "wn_kopaliny", "visible": True, "uri": "LineString?crs=epsg:2180&field=id:integer", "attrib": [QgsField('wyr_id', QVariant.Int, "int"), QgsField('wn_id', QVariant.String, "string", 0)]},
            {"source": "postgres", "name": "powiaty", "root": True, "pos": 2, "visible": True, "uri": '{PARAMS} table="team_0"."powiaty" (geom) sql='},
            {"source": "postgres", "name": "arkusze", "root": True, "pos": 3, "visible": True, "uri": '{PARAMS} table="team_0"."arkusze" (geom) sql='},
            {"source": "postgres", "name": "vn_sel", "root": False, "parent": "vn", "visible": True, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
            {"source": "postgres", "name": "vn_user", "root": False, "parent": "vn", "visible": True, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
            {"source": "postgres", "name": "vn_other", "root": False, "parent": "vn", "visible": False, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
            {"source": "postgres", "name": "vn_null", "root": False, "parent": "vn", "visible": False, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
            {"source": "postgres", "name": "vn_all", "root": False, "parent": "vn", "visible": False, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
            {"source": "virtual", "name": "powiaty_mask", "root": True, "pos": 5, "visible": True, "uri": '?query=Select%20st_union(geometry)%20from%20powiaty'},
            {"source": "postgres", "name": "midas_zloza", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} key="id" table="(SELECT m.* FROM external.midas_zloza m LEFT JOIN external.midas_blacklist b USING(id_zloza) WHERE b.id_zloza IS NULL)" (geom) sql='},
            {"source": "postgres", "name": "midas_wybilansowane", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} key="id1" table="(SELECT m.* FROM external.midas_wybilansowane m LEFT JOIN external.midas_blacklist b USING(id_zloza) WHERE b.id_zloza IS NULL)" (geom) sql='},
            {"source": "postgres", "name": "midas_obszary", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} key="id1" table="(SELECT m.* FROM external.midas_obszary m LEFT JOIN external.midas_blacklist b ON m.id_zloz = b.id_zloza WHERE b.id_zloza IS NULL)" (geom) sql='},
            {"source": "postgres", "name": "midas_tereny", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} key="id1" table="(SELECT m.* FROM external.midas_tereny m LEFT JOIN external.midas_blacklist b ON m.id_zloz = b.id_zloza WHERE b.id_zloza IS NULL)" (geom) sql='},
            {"source": "postgres", "name": "mgsp_pkt_kop", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_pkt_kop" (geom) sql='},
            {"source": "postgres", "name": "mgsp_zloza_p", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_p" (geom) sql='},
            {"source": "postgres", "name": "mgsp_zloza_a", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_a" (geom) sql='},
            {"source": "postgres", "name": "mgsp_zloza_wb_p", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_wb_p" (geom) sql='},
            {"source": "postgres", "name": "mgsp_zloza_wb_a", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_wb_a" (geom) sql='},
            {"source": "postgres", "name": "smgp_wyrobiska", "root": True, "pos": 8, "visible": True, "uri": '{PARAMS} table="external"."smgp_wyrobiska" (geom) sql='},
            {"source": "wms", "name": "Google Satellite", "root": False, "parent": "sat", "visible": True, "uri": 'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0'},
            {"source": "wms", "name": "Google Hybrid", "root": False, "parent": "sat", "visible": False, "uri": 'crs=EPSG:3857&format&tilePixelRatio=2&type=xyz&url=http://mt0.google.com/vt/lyrs%3Dy%26hl%3Dpl%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0'},
            {"source": "wms", "name": "Geoportal", "root": False, "parent": "sat", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/jpeg&layers=ORTOFOTOMAPA&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMTS/StandardResolution?service%3DWMTS%26request%3DgetCapabilities'},
            {"source": "wms", "name": "Geoportal Archiwalny", "root": False, "parent": "sat", "visible": False, "uri": f'IgnoreGetFeatureInfoUrl=1&IgnoreGetMapUrl=1&contextualWMSLegend=0&SmoothPixmapTransform=1&IgnoreReportedLayerExtents=1&crs=EPSG:2180&format=image/jpeg&layers=Raster&styles=&version=1.1.1&url=https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolutionTime?TIME={datetime.now():%Y}-{datetime.now():%m}-{datetime.now():%d}T00%3A00%3A00.000%2B01%3A00'},
            {"source": "gdal", "name": "Google Earth Pro", "root": False, "parent": "sat", "visible": False, "uri": '{UI_PATH}ge.jpg', "crs": -1},
            {"source": "wms", "name": "Google Map", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26hl%3Dpl%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0'},
            {"source": "wms", "name": "OpenStreetMap", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:3857&format&type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0'},
            {"source": "wms", "name": "Topograficzna", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/jpeg&layers=MAPA TOPOGRAFICZNA&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/WMTS/guest/wmts/TOPO?service%3DWMTS%26request%3DgetCapabilities'},
            {"source": "wms", "name": "BDOT", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/png&layers=BDOT10k&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/WMTS/guest/wmts/BDOT10k?service%3DWMTS%26request%3DgetCapabilities'},
            {"source": "wms", "name": "BDOO", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=7&featureCount=10&format=image/png&layers=G2_MOBILE_500&styles=default&tileMatrixSet=EPSG:2180&url=http://mapy.geoportal.gov.pl/wss/service/WMTS/guest/wmts/G2_MOBILE_500?service%3DWMTS%26request%3DgetCapabilities'},
            {"source": "wms", "name": "ISOK", "root": False, "parent": "basemaps", "pos": 0, "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/jpeg&layers=Cieniowanie&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMTS/ShadedRelief?service%3DWMTS%26request%3DgetCapabilities'},
            {"source": "postgres", "name": "wyr_point", "root": False, "parent": "temp", "visible": False, "uri": '{PARAMS} table="team_0"."wyrobiska" (centroid) sql='},
            {"source": "memory", "name": "edit_poly", "root": False, "parent": "temp", "visible": True, "uri": "Polygon?crs=epsg:2180&field=id:integer", "attrib": [QgsField('part', QVariant.Int, "int")]},
            {"source": "memory", "name": "backup_poly", "root": False, "parent": "temp", "visible": False, "uri": "Polygon?crs=epsg:2180&field=id:integer", "attrib": [QgsField('part', QVariant.Int, "int")]},
            {"source": "memory", "name": "edit_line", "root": False, "parent": "temp", "visible": True, "uri": "LineString?crs=epsg:2180&field=id:integer", "attrib": [QgsField('part', QVariant.Int, "int")]},
            {"source": "memory", "name": "backup_line", "root": False, "parent": "temp", "visible": False, "uri": "LineString?crs=epsg:2180&field=id:integer", "attrib": [QgsField('part', QVariant.Int, "int")]}
            ]
        self.lyr_vis = [["wyr_point", True], ["flagi_z_teren", None], ["flagi_bez_teren", None]]  #, ["parking_planowane", None], ["parking_odwiedzone", None], ["marszruty", None], ["wn_pne", None]]
        self.lyr_cnt = len(self.lyrs)
        self.lyrs_names = [i for s in [[v for k, v in d.items() if k == "name"] for d in self.lyrs] for i in s]

    def project_check(self):
        """Sprawdzenie struktury warstw projektu."""
        if len(dlg.proj.mapLayers()) == 0:
            # QGIS nie ma otwartego projektu, tworzy nowy:
            self.project_create()
            return True
        else:
            QgsApplication.processEvents()
            # QGIS ma otwarty projekt - sprawdzanie jego struktury:
            valid = self.structure_check()
            QgsApplication.processEvents()
            if valid:
                return True
            else:
                m_text = f"Brak wymaganych warstw lub grup warstw w otwartym projekcie. Naciśnięcie Tak spowoduje przebudowanie struktury projektu, naciśnięcie Nie przerwie proces uruchamiania wtyczki."
                reply = QMessageBox.question(dlg.app, "Moek_Editor", m_text, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return False
                else:
                    lyr_missing = self.structure_check(rebuild=True)
                    if len(lyr_missing) > 0:
                        result = self.layers_create(lyr_missing)
                        return result
                    else:
                        return True

    def project_create(self):
        """Utworzenie nowego projektu QGIS."""
        iface.newProject(promptToSaveFlag=False)
        # Zmiana tytułu okna QGIS'a:
        dlg.proj.setCrs(CRS_1992)
        # iface.mainWindow().setWindowTitle(new_title)
        QgsApplication.processEvents()
        self.groups_create()
        QgsApplication.processEvents()
        self.layers_create()
        return True

    def groups_create(self):
        """Utworzenie grup warstw w projekcie."""
        for grp in self.groups_tree:
            if grp["level"] == 1:
                # Utworzenie grup głównych:
                grp_node = self.root.addGroup(grp["name"])
                grp_node.setExpanded(False)
                if "subgroups" in grp:
                    # Utworzenie podgrup:
                    for sgrp in grp["subgroups"]:
                        sgrp_node = grp_node.addGroup(sgrp)
                        sgrp_node.setExpanded(False)
        # Ukrycie grupy 'temp':
        self.root.findGroup("temp").setItemVisibilityChecked(False)

    def layers_create(self, missing=None):
        """Utworzenie warstw w projekcie. Podanie atrybutu 'missing' spowoduje, że tylko wybrane warstwy będą dodane."""
        # Ustalenie ilości dodawanych warstw:
        i_max = len(missing) if missing else self.lyr_cnt
        # Utworzenie listy ze słownikami warstw do dodania:
        lyrs = []
        if missing:
            for l_dict in self.lyrs:
                if l_dict["name"] in missing:
                    lyrs.append(l_dict)
        else:
            lyrs = self.lyrs
        i = 0
        # Dodanie warstw:
        for l_dict in lyrs:
            QgsApplication.processEvents()
            i += 1
            dlg.splash_screen.p_bar.setValue(i * 100 / self.lyr_cnt)
            QgsApplication.processEvents()
            raw_uri = l_dict["uri"]
            uri = eval("f'{}'".format(raw_uri))
            if l_dict["source"] == "wms" or l_dict["source"] == "gdal":
                lyr = QgsRasterLayer(uri, l_dict["name"], l_dict["source"])
                lyr_required = False
            else:
                lyr = QgsVectorLayer(uri, l_dict["name"], l_dict["source"])
                lyr_required = True
            if not lyr.isValid() and not lyr_required:
                m_text = f'Nie udało się poprawnie wczytać podkładu mapowego: {l_dict["name"]}. Naciśnięcie Tak spowoduje kontynuowanie uruchamiania wtyczki (podkład mapowy nie będzie wyświetlany), naciśnięcie Nie przerwie proces uruchamiania wtyczki. Jeśli problem będzie się powtarzał, zaleca się powiadomienie administratora systemu.'
                reply = QMessageBox.question(dlg.app, "Moek_Editor", m_text, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return False
            elif not lyr.isValid() and lyr_required:
                m_text = f'Nie udało się poprawnie wczytać warstwy: {l_dict["name"]}. Jeśli problem będzie się powtarzał, proszę o powiadomienie administratora systemu.'
                QMessageBox.critical(dlg.app, "Moek_Editor", m_text)
                return False
            if l_dict["source"] == "memory":
                lyr.setCustomProperty("skipMemoryLayersCheck", 1)
                pr = lyr.dataProvider()
                pr.addAttributes(l_dict["attrib"])
                lyr.updateFields()
            if "crs" in l_dict:
                lyr.setCrs(CRS_1992)
            dlg.proj.addMapLayer(lyr, False)
            if l_dict["root"]:
                parent_grp = self.root
                parent_grp.insertChildNode(l_dict["pos"], QgsLayerTreeLayer(lyr))
                parent_grp.findLayer(lyr).setItemVisibilityChecked(l_dict["visible"])
            else:
                if "pos" in l_dict:
                    parent_grp = self.root.findGroup(l_dict["parent"])
                    parent_grp.insertChildNode(l_dict["pos"], QgsLayerTreeLayer(lyr))
                    parent_grp.findLayer(lyr).setItemVisibilityChecked(False)
                else:
                    parent_grp = self.root.findGroup(l_dict["parent"])
                    node = parent_grp.addLayer(lyr)
                    node.setItemVisibilityChecked(l_dict["visible"])
            lyr.loadNamedStyle(f'{STYLE_PATH}{l_dict["name"].lower()}.qml')
        return True

    def layers_check(self):
        """Zwraca, czy wszystkie niezbędne warstwy są obecne w projekcie."""
        lyrs = []
        missing = []
        # Utworzenie listy warstw, które znajdują się w projekcie:
        for lyr in dlg.proj.mapLayers().values():
            lyrs.append(lyr.name())
        # Sprawdzenie, czy wszystkie niezbędne warstwy istnieją w projekcie:
        for lyr in self.lyrs_names:
            if lyr not in lyrs:
                print(f"Brakuje warstwy: {lyr}")
                missing.append(lyr)
        return missing

    def structure_check(self, rebuild=False):
        """Zwraca, czy wszystkie niezbędne grupy i warstwy są obecne w projekcie (rebuild=False),
        albo przebudowuje strukturę projektu (przenosi lub tworzy grupy i przenosi warstwy do odpowiednich grup)
        i zwraca listę brakujących warstw (rebuild=True)."""
        missing = []
        for grp in self.groups_tree:
            parent_node = self.root
            grp_node = parent_node.findGroup(grp["name"]) if "name" in grp else parent_node
            if grp["level"] == 2:
                parent_node = self.root.findGroup(grp["parent"])
                grp_node = parent_node.findGroup(grp["name"])
            if not grp_node and not rebuild:
                return False
            elif not grp_node and rebuild:
                moved = self.group_move(parent_node, grp["name"])
                if not moved:
                    parent_node.addGroup(grp["name"])
                grp_node = parent_node.findGroup(grp["name"])
            for lyr_name in grp["layers"]:
                if not self.layer_in_group_found(grp_node, lyr_name) and not rebuild:
                    return False
                elif not self.layer_in_group_found(grp_node, lyr_name) and rebuild:
                    moved = self.layer_to_group_move(grp_node, lyr_name)
                    if not moved:
                        missing.append(lyr_name)
                        continue
                lyr = dlg.proj.mapLayersByName(lyr_name)[0]
                # if not lyr.isValid():
                #     dlg.proj.removeMapLayer(lyr)
                #     missing.append(lyr_name)
        if missing:
            print(f"layer/structure_check - lista brakujących warstw:")
            print(missing)
        return missing if rebuild else True

    def group_move(self, parent_node, grp_name):
        """Przenoszenie grupy (jeśli istnieje) na właściwą pozycję w projekcie."""
        grp_node = self.root.findGroup(grp_name)
        if grp_node:
            # Grupa o podanej nazwie jest w projekcie, ale w innym miejscu i należy ją przenieść:
            parent = grp_node.parent()
            new_grp = grp_node.clone()
            parent_node.insertChildNode(0, new_grp)
            parent.removeChildNode(grp_node)
            return True
        else:
            return False

    def layer_in_group_found(self, grp_node, lyr_name):
        """Zwraca, czy warstwa o podanej nazwie znajduje się w podanej grupie."""
        for child in grp_node.children():
            if child.name() == lyr_name:
                return True
        return False

    def layer_to_group_move(self, grp_node, lyr_name):
        """Przenoszenie warstwy (jeśli istnieje) do właściwej grupy."""
        try:
            lyr = self.root.findLayer(dlg.proj.mapLayersByName(lyr_name)[0].id())
        except Exception as err:
            print(f"layers/layer_to_group_move: {err}")
            return False
        # Warstwa o podanej warstwie jest w projekcie, ale w innej grupie i należy ją przenieść:
        parent = lyr.parent()
        new_lyr = lyr.clone()
        grp_node.insertChildNode(0, new_lyr)
        parent.removeChildNode(lyr)
        return True

    def grp_vis_change(self, grp_name, val):
        """Zmiana parametru widoczności warstw z podanej grupy dla MultiMapTool."""
        if grp_name == "flagi":
            if not val:
                dlg.obj.flag = None
            lyr_names = ["flagi_z_teren", "flagi_bez_teren"]
        # elif grp_name == "komunikacja":
        #     if not val:
        #         dlg.obj.parking = None
        #         dlg.obj.marsz = None
        #     lyr_names = ["parking_planowane", "parking_odwiedzone", "marszruty"]
        elif grp_name == "wyrobiska":
            if not val:
                dlg.obj.wyr = None
            for _list in self.lyr_vis:
                if _list[0] == "wyr_point":
                    _list[1] = False if not val else True
                    return
        for lyr_name in lyr_names:
            for _list in self.lyr_vis:
                if _list[0] == lyr_name:
                    _list[1] = False if not val else dlg.cfg.get_val(_list[0])

    def lyr_vis_change(self, lyr_name, val):
        """Zmiana parametru widoczności warstwy dla MultiMapTool."""
        for _list in self.lyr_vis:
            if _list[0] == lyr_name:
                _list[1] = val

class PanelManager:
    """Menedżer ustawień (widoczność, rozwinięcie itp.) paneli."""
    def __init__(self, dlg):
        self.callback_void = True
        self.dlg = dlg
        self.cfg = []
        self.cfg_dicts = [
            {'name': 'team', 'action': 'panel_state', 'btn': None, 'callback': 'dlg.p_team.set_state(val)', 'cb_void': False, 'value': None},  # ------------------------------------------------------ 0 -- 0
            {'name': 'powiaty', 'action': 'panel_state', 'btn': None, 'callback': 'dlg.p_pow.set_state(val)', 'cb_void': False, 'value': None},  # ---------------------------------------------------- 1 -- 1
            {'name': 'powiaty_mask', 'action': 'lyr_vis', 'btn': dlg.p_pow_mask.box.widgets["btn_pow_mask"], 'callback': None, 'cb_void': False, 'value': None},  # ----------------------------------- 2 -- 2
            {'name': 'vn', 'action': 'panel_state', 'btn': None, 'callback': 'dlg.p_vn.set_state(val)', 'cb_void': False, 'value': None},  # ---------------------------------------------------------- 3 -- 3
            {'name': 'external', 'action': 'panel_state', 'btn': None, 'callback': 'dlg.p_ext.set_state(val)', 'cb_void': False, 'value': None},  # --------------------------------------------------- 4 -- 4
            # {'name': 'wn_pne', 'action': 'lyr_vis', 'btn': dlg.p_ext.box.widgets["btn_wn"], 'callback': None, 'cb_void': False, 'value': None},  # -------------------------------------------------- 5
            {'name': 'MIDAS', 'action': 'grp_vis', 'btn': dlg.p_ext.box.widgets["btn_midas"], 'callback': None, 'cb_void': False, 'value': None},  # -------------------------------------------------- 6 -- 5
            {'name': 'midas_zloza', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # -------------------------------------------------------------------------- 7 -- 6
            {'name': 'midas_wybilansowane', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ------------------------------------------------------------------ 8 -- 7
            {'name': 'midas_obszary', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ------------------------------------------------------------------------ 9 -- 8
            {'name': 'midas_tereny', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ------------------------------------------------------------------------- 10 - 9
            {'name': 'MGSP', 'action': 'grp_vis', 'btn': dlg.p_ext.box.widgets["btn_mgsp"], 'callback': None, 'cb_void': False, 'value': None},  # ---------------------------------------------------- 11 - 10
            {'name': 'mgsp_pkt_kop', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ------------------------------------------------------------------------- 12 - 11
            {'name': 'mgsp_zloza_p', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ------------------------------------------------------------------------- 13 - 12
            {'name': 'mgsp_zloza_a', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ------------------------------------------------------------------------- 14 - 13
            {'name': 'mgsp_zloza_wb_p', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ---------------------------------------------------------------------- 15 - 14
            {'name': 'mgsp_zloza_wb_a', 'action': 'lyr_vis', 'btn': None, 'callback': None, 'cb_void': False, 'value': None},  # ---------------------------------------------------------------------- 16 - 15
            {'name': 'smgp_wyrobiska', 'action': 'lyr_vis', 'btn': dlg.p_ext.box.widgets["btn_smgp"], 'callback': None, 'cb_void': False, 'value': None},  # ------------------------------------------ 17 - 16
            {'name': 'flagi', 'action': 'panel_state', 'btn': None, 'callback': 'dlg.p_flag.set_state(val)', 'cb_void': False, 'value': None},  # ----------------------------------------------------- 18 - 17
            {'name': 'flagi_user', 'action': 'postgres', 'btn': dlg.p_flag.widgets["btn_user"], 'callback': 'flag_layer_update()', 'cb_void': True, 'value': None},  # -------------------------------- 19 - 18
            {'name': 'flagi_z_teren', 'action': 'postgres', 'btn': dlg.p_flag.widgets["btn_fchk_vis"], 'callback': 'flag_layer_update()', 'cb_void': True, 'value': None},  # ------------------------- 20 - 19
            {'name': 'flagi_bez_teren', 'action': 'postgres', 'btn': dlg.p_flag.widgets["btn_nfchk_vis"], 'callback': 'flag_layer_update()', 'cb_void': True, 'value': None},  # ---------------------- 21 - 20
            {'name': 'wyrobiska', 'action': 'panel_state', 'btn': None, 'callback': 'dlg.p_wyr.set_state(val)', 'cb_void': False, 'value': None},  # -------------------------------------------------- 22 - 21
            {'name': 'wyr_user', 'action': 'postgres', 'btn': dlg.p_wyr.widgets["btn_user"], 'callback': 'wyr_layer_update(False)', 'cb_void': True, 'value': None},  # ------------------------------- 23 - 22
            {'name': 'wyr_szare', 'action': 'postgres', 'btn': dlg.p_wyr.widgets["btn_wyr_grey_vis"], 'callback': 'wyr_layer_update(False)', 'cb_void': True, 'value': None},  # ---------------------- 24 - 23
            {'name': 'wyr_fioletowe', 'action': 'postgres', 'btn': dlg.p_wyr.widgets["btn_wyr_purple_vis"], 'callback': 'wyr_layer_update(False)', 'cb_void': True, 'value': None},  # ---------------- 25 - 24
            {'name': 'wyr_zielone', 'action': 'postgres', 'btn': dlg.p_wyr.widgets["btn_wyr_green_vis"], 'callback': 'wyr_layer_update(False)', 'cb_void': True, 'value': None}  # -------------------- 26 - 25
            # {'name': 'komunikacja', 'action': 'panel_state', 'btn': None, 'callback': 'dlg.p_komunikacja.set_state(val)', 'cb_void': False, 'value': None},  # -------------------------------------- 27
            # {'name': 'komunikacja_user', 'action': 'postgres', 'btn': dlg.p_komunikacja.widgets["btn_user"], 'callback': 'self.komunikacja_layers_update()', 'cb_void': True, 'value': None},  # ---- 28
            # {'name': 'parking_planowane', 'action': 'postgres', 'btn': dlg.p_komunikacja.widgets["btn_parking_before_vis"], 'callback': 'parking_layer_update()', 'cb_void': True, 'value': None},  # 29
            # {'name': 'parking_odwiedzone', 'action': 'postgres', 'btn': dlg.p_komunikacja.widgets["btn_parking_after_vis"], 'callback': 'parking_layer_update()', 'cb_void': True, 'value': None},  # 30
            # {'name': 'marszruty', 'action': 'postgres', 'btn': dlg.p_komunikacja.widgets["btn_marsz_vis"], 'callback': 'marsz_layer_update()', 'cb_void': True, 'value': None}  # ------------------- 31
                        ]
        self.cfg_dicts_cnt = len(self.cfg_dicts)
        self.cfg_vals = []
        self.old_cfg_vals = []
        self.cfg_mem = []

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cfg_vals":
            if not val:
                return
            cfg_vals = val
            try:
                vals_cnt = len(cfg_vals)
            except Exception as err:
                print(f"PanelManager/setattr: {err}")
                return
            if vals_cnt != self.cfg_dicts_cnt:
                return
            if len(self.old_cfg_vals) != self.cfg_dicts_cnt:
                self.old_cfg_vals = self.cfg_vals.copy()
            for i in range(self.cfg_dicts_cnt):
                if self.cfg_dicts[i]["value"] != self.old_cfg_vals[i]:
                    dlg.freeze_set(True)  # Zablokowanie odświeżania dockwidget'u
                    self.cfg_dicts[i]["value"] = self.cfg_vals[i]
                    self.update_action(self.cfg_dicts[i]["action"], self.cfg_dicts[i]["name"], self.cfg_dicts[i]["btn"], self.cfg_dicts[i]["value"], self.cfg_dicts[i]["callback"], self.cfg_dicts[i]["cb_void"])
                    if any(l[0] == self.cfg_dicts[i]["name"] for l in dlg.lyr.lyr_vis):
                        # Aktualizacja wartości na liście lyr_vis dla multitool'a:
                        dlg.lyr.lyr_vis_change(self.cfg_dicts[i]["name"], bool(self.cfg_dicts[i]["value"]))
            self.old_cfg_vals = self.cfg_vals.copy()
            if self.callback_void:
                self.callback_void = False
            dlg.freeze_set(False)  # Odblokowanie odświeżania dockwidget'u

    def update_action(self, action, name, btn, val, cb, cb_void):
        """Przeprowadza zmiany związane z modyfikacją stanu konfiguracji."""
        val_out = False if val == 0 else True  # Konwersja int na bool
        if action == "lyr_vis":
            dlg.proj.layerTreeRoot().findLayer(dlg.proj.mapLayersByName(name)[0].id()).setItemVisibilityChecked(val_out)
        elif action == "grp_vis":
            dlg.proj.layerTreeRoot().findGroup(name).setItemVisibilityCheckedRecursive(val_out)
        if name == "powiaty":
            dlg.wyr_panel.pow_all = not val_out
        # if name == "flagi" or name == "komunikacja" or name == "wyrobiska" or name == "wn_pne":
        if name == "flagi" or name == "wyrobiska":
            # Zmiana parametru widoczności wszystkich warstw z określonej grupy dla MultiMapTool:
            dlg.lyr.grp_vis_change(name, val_out)
        if btn:
            btn.setChecked(val_out)
        if cb and (not self.callback_void or not cb_void):
            exec(cb)

    def set_val(self, name, val, db=True):
        """Zamienia aktualną wartość (int albo bool) z cfg_dict o podanej nazwie i aktualizuje cfg_vals w bazie danych."""
        # Ustalenie prawidłowej wartości:
        if type(val) == bool:
            # Konwersja danych int na bool:
            val = 1 if val else 0
        else:
            # Zapewnienie, że val ma wartość 0, 1 lub 2:
            val = 0 if not val in range(0, 3) else val
        # Wyszukanie odpowiedniego słownika i podmiana wartości:
        # Aktualizacja self.cfg_vals:
        new_vals = []
        for c_dict in self.cfg_dicts:
            if c_dict["name"] == name:
                # Aktualizacja wartości w zmienianym słowniku:
                c_dict["value"] = val
                if any(l[0] == c_dict["name"] for l in dlg.lyr.lyr_vis):
                    # Aktualizacja wartości na liście lyr_vis dla multitool'a:
                    dlg.lyr.lyr_vis_change(c_dict["name"], bool(val))
            if c_dict["value"] in range(0, 3):
                new_vals.append(c_dict["value"])
            else:
                print(f'layers/set_val: Słownik {c_dict["name"]} ma nieprawidłową wartość {c_dict["value"]}')
                return
        self.cfg_vals = new_vals
        # Aktualizacja bazy danych:
        if db:
            self.cfg_vals_write()

    def get_val(self, name, convert=True):
        """Zwraca aktualną wartość (convert=True: bool, False: int) z cfg_dict o podanej nazwie."""
        val = 0
        for c_dict in self.cfg_dicts:
            if c_dict["name"] == name:
                val = c_dict["value"]
                break
        if convert:
            return False if val == 0 else True
        else:
            return val

    def flag_case(self):
        """Zwraca liczbę wskazującą, które warstwy flag są włączone."""
        flag_vals = [0, 0, 0, 0]
        for c_dict in self.cfg_dicts:
            if c_dict["name"] == "flagi_z_teren" and c_dict["value"] in range(0, 2):
                flag_vals[0] = c_dict["value"]
            elif c_dict["name"] == "flagi_bez_teren" and c_dict["value"] in range(0, 2):
                flag_vals[1] = c_dict["value"]
            elif c_dict["name"] == "flagi_user" and c_dict["value"] in range(0, 2):
                flag_vals[2] = c_dict["value"]
        flag_vals[3] = 1 if dlg.p_pow.is_active() else 0
        case_val = flag_vals[0] + (flag_vals[1] * 2) + (flag_vals[2] * 4) + (flag_vals[3] * 8)
        return case_val

    def wyr_case(self):
        """Zwraca liczbę wskazującą, które warstwy punktowe wyrobisk są włączone."""
        wyr_vals = [0, 0, 0, 0]
        for c_dict in self.cfg_dicts:
            if c_dict["name"] == "wyr_szare" and c_dict["value"] in range(0, 2):
                wyr_vals[0] = c_dict["value"]
            elif c_dict["name"] == "wyr_fioletowe" and c_dict["value"] in range(0, 2):
                wyr_vals[1] = c_dict["value"]
            elif c_dict["name"] == "wyr_zielone" and c_dict["value"] in range(0, 2):
                wyr_vals[2] = c_dict["value"]
            elif c_dict["name"] == "wyr_user" and c_dict["value"] in range(0, 2):
                wyr_vals[3] = c_dict["value"]
        case_val = wyr_vals[0] + (wyr_vals[1] * 2) + (wyr_vals[2] * 4) + (wyr_vals[3] * 8)
        return case_val

    def parking_case(self):
        """Zwraca liczbę wskazującą, które warstwy parkingów są włączone."""
        parking_vals = [0, 0, 0, 0]
        for c_dict in self.cfg_dicts:
            if c_dict["name"] == "parking_planowane" and c_dict["value"] in range(0, 2):
                parking_vals[0] = c_dict["value"]
            elif c_dict["name"] == "parking_odwiedzone" and c_dict["value"] in range(0, 2):
                parking_vals[1] = c_dict["value"]
            elif c_dict["name"] == "komunikacja_user" and c_dict["value"] in range(0, 2):
                parking_vals[2] = c_dict["value"]
        parking_vals[3] = 1 if dlg.p_pow.is_active() else 0
        case_val = parking_vals[0] + (parking_vals[1] * 2) + (parking_vals[2] * 4) + (parking_vals[3] * 8)
        return case_val

    def marsz_case(self):
        """Zwraca liczbę wskazującą, które warstwy parkingów są włączone."""
        marsz_vals = [0, 0, 0]
        for c_dict in self.cfg_dicts:
            if c_dict["name"] == "marszruty" and c_dict["value"] in range(0, 2):
                marsz_vals[0] = c_dict["value"]
            elif c_dict["name"] == "komunikacja_user" and c_dict["value"] in range(0, 2):
                marsz_vals[1] = c_dict["value"]
        marsz_vals[2] = 1 if dlg.p_pow.is_active() else 0
        case_val = marsz_vals[0] + (marsz_vals[1] * 2) + (marsz_vals[2] * 4)
        return case_val

    def cfg_vals_read(self):
        """Wczytanie z bazy danych ustawień paneli do self.cfg_vals."""
        self.cfg_vals = []
        db = PgConn()
        sql = "SELECT t_settings FROM team_users WHERE team_id = " + str(self.dlg.team_i) + " AND user_id = " + str(self.dlg.user_id) + ";"
        if db:
            res = db.query_sel(sql, False)
            if res:
                self.cfg_vals[:0] = res[0]
            else:
                self.cfg_vals[:0] = '1012111111111111121112111'  # '1012111111111111112111211112111'
        if len(self.old_cfg_vals) > 0:
            self.old_cfg_vals = []
            self.old_cfg_vals = list(map(int, self.cfg_vals))  # Zamiana tekstu na cyfry
            self.cfg_vals = self.old_cfg_vals
        else:
            self.cfg_vals = list(map(int, self.cfg_vals))  # Zamiana tekstu na cyfry

    def cfg_vals_write(self):
        """Zapisanie ustawień paneli z self.cfg_vals do bazy danych."""
        cfg_val_txt = str("".join(map(str, self.cfg_vals)))  # Zamiana cyfr na tekst
        db = PgConn()
        sql = "UPDATE public.team_users SET t_settings = '" + cfg_val_txt + "' WHERE team_id = " + str(self.dlg.team_i) + " AND user_id = " + str(self.dlg.user_id) + ";"
        if db:
            db.query_upd(sql)

    def switch_lyrs_on_setup(self, off=True):
        """Włączenie/wyłączenie warstw przy wychodzeniu/wchodzeniu do trybu ustawień."""
        # print(f"switch_lyrs_on_setup: {off}")
        if off:
            # Wyłączanie warstw:
            # lyrs = [5, 6, 11, 17, 18, 22, 27]
            lyrs = [5, 10, 16, 17, 21]
            # print(self.cfg_dicts)
            for lyr in lyrs:
                # Zapamiętanie ustawień warstwy:
                self.cfg_mem.append([self.cfg_dicts[lyr]["name"], self.cfg_dicts[lyr]["value"]])
                # Wyłączenie warstwy:
                self.set_val(self.cfg_dicts[lyr]["name"], 0, db=False)
        elif not off:
            # Włączanie warstw:
            for lyr in self.cfg_mem:
                # Przywrócenie pierwotnych ustawień warstw:
                self.set_val(lyr[0], lyr[1], db=False)
            self.cfg_mem = []  # Wyczyszczenie listy

    def komunikacja_layers_update(self):
        """Aktualizacja warstw parkingów i marszrut."""
        parking_layer_update()
        marsz_layer_update()
