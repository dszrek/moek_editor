# -*- coding: utf-8 -*-
import os

from qgis.core import QgsProject, QgsApplication, QgsRasterLayer, QgsVectorLayer, QgsRectangle, QgsField, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.PyQt.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QVariant
from qgis.utils import iface

from .classes import CfgPars

# Zmienne globalne:
dlg = None
with CfgPars() as cfg:
    PARAMS = cfg.uri()
CRS_1992 = QgsCoordinateReferenceSystem(2180)
UI_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep
STYLE_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'styles' + os.path.sep

def dlg_layers(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

def create_qgis_project():
    """Utworzenie nowego projektu QGIS."""
    iface.newProject(False)
    qprj = QgsProject.instance()
    qprj.setTitle("MOEK_editor")
    qprj.setCrs(CRS_1992)
    QgsApplication.processEvents()
    create_project_groups()
    QgsApplication.processEvents()
    create_layers()

def create_project_groups():
    """Utworzenie grup warstw w projekcie."""
    grp_lvl_1 = ["wyrobiska", "flagi", "vn", "MIDAS", "MGSP", "basemaps", "temp"]
    grp_lvl_2 = [
                {"name": "sat", "parent": "basemaps"},
                {"name": "topo", "parent": "basemaps"}
                ]
    proj = QgsProject.instance()
    root = proj.layerTreeRoot()
    # Utworzenie grup głównych:
    for grp in grp_lvl_1:
        _grp = QgsLayerTreeGroup(name=grp)
        node = root.addGroup(grp)
        node.setExpanded(False)
    # Utworzenie podgrup i przypisanie ich do grup głównych:
    for grp in grp_lvl_2:
        for key, val in grp.items():
            if key == "name":
                name = val
            elif key == "parent":
                parent = val
        parent_grp = root.findGroup(parent)
        node = parent_grp.addGroup(name)
        node.setExpanded(False)
    # Ukrycie grupy 'temp':
    root.findGroup("temp").setItemVisibilityChecked(False)
    # Rozwinięcie grup 'wyrobiska' i 'flagi':
    root.findGroup("wyrobiska").setExpanded(True)
    root.findGroup("flagi").setExpanded(True)

def create_layers():
    """Utworzenie warstw w projekcie."""
    proj = QgsProject.instance()
    root = proj.layerTreeRoot()
    uri_pt = "Point?crs=epsg:2180&field=id:integer"
    uri_ln = "LineString?crs=epsg:2180&field=id:integer"
    uri_pg = "Polygon?crs=epsg:2180&field=id:integer"
    lyrs = [
        {"source": "postgres", "name": "wyr_point", "root": False, "parent": "wyrobiska", "visible": True, "uri": '{PARAMS} table="team_0"."wyrobiska" (centroid) sql='},
        {"source": "postgres", "name": "wyr_poly", "root": False, "parent": "wyrobiska", "visible": True, "uri": '{PARAMS} table="team_0"."wyr_geom" (geom) sql='},
        {"source": "postgres", "name": "flagi_z_teren", "root": False, "parent": "flagi", "visible": True, "uri": '{PARAMS} table="team_0"."flagi" (geom) sql='},
        {"source": "postgres", "name": "flagi_bez_teren", "root": False, "parent": "flagi", "visible": True, "uri": '{PARAMS} table="team_0"."flagi" (geom) sql='},
        {"source": "postgres", "name": "wn_kopaliny_pne", "root": True, "pos": 2, "visible": True, "uri": '{PARAMS} table="external"."wn_kopaliny_pne" (geom) srid=4326 sql=', "crs": 4326},
        {"source": "postgres", "name": "powiaty", "root": True, "pos": 3, "visible": True, "uri": '{PARAMS} table="team_0"."powiaty" (geom) sql='},
        {"source": "postgres", "name": "arkusze", "root": True, "pos": 4, "visible": True, "uri": '{PARAMS} table="team_0"."arkusze" (geom) sql='},
        {"source": "postgres", "name": "vn_sel", "root": False, "parent": "vn", "visible": True, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
        {"source": "postgres", "name": "vn_user", "root": False, "parent": "vn", "visible": True, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
        {"source": "postgres", "name": "vn_other", "root": False, "parent": "vn", "visible": False, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
        {"source": "postgres", "name": "vn_null", "root": False, "parent": "vn", "visible": False, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
        {"source": "postgres", "name": "vn_all", "root": False, "parent": "vn", "visible": False, "uri": '{PARAMS} table="team_0"."team_viewnet" (geom) sql='},
        {"source": "virtual", "name": "powiaty_mask", "root": True, "pos": 6, "visible": True, "uri": '?query=Select%20st_union(geometry)%20from%20powiaty'},
        {"source": "postgres", "name": "midas_zloza", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} table="external"."midas_zloza" (geom) sql='},
        {"source": "postgres", "name": "midas_wybilansowane", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} table="external"."midas_wybilansowane" (geom) sql='},
        {"source": "postgres", "name": "midas_obszary", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} table="external"."midas_obszary" (geom) sql='},
        {"source": "postgres", "name": "midas_tereny", "root": False, "parent": "MIDAS", "visible": True, "uri": '{PARAMS} table="external"."midas_tereny" (geom) sql='},
        {"source": "postgres", "name": "mgsp_pkt_kop", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_pkt_kop" (geom) sql='},
        {"source": "postgres", "name": "mgsp_zloza_p", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_p" (geom) sql='},
        {"source": "postgres", "name": "mgsp_zloza_a", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_a" (geom) sql='},
        {"source": "postgres", "name": "mgsp_zloza_wb_p", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_wb_p" (geom) sql='},
        {"source": "postgres", "name": "mgsp_zloza_wb_a", "root": False, "parent": "MGSP", "visible": True, "uri": '{PARAMS} table="external"."mgsp_zloza_wb_a" (geom) sql='},
        {"source": "postgres", "name": "smgp_wyrobiska", "root": True, "pos": 9, "visible": True, "uri": '{PARAMS} table="external"."smgp_wyrobiska" (geom) sql='},
        {"source": "wms", "name": "Google Satellite", "root": False, "parent": "sat", "visible": True, "uri": 'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0'},
        {"source": "wms", "name": "Google Hybrid", "root": False, "parent": "sat", "visible": False, "uri": 'crs=EPSG:3857&format&tilePixelRatio=2&type=xyz&url=http://mt0.google.com/vt/lyrs%3Dy%26hl%3Den%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0'},
        {"source": "wms", "name": "Geoportal", "root": False, "parent": "sat", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/jpeg&layers=ORTOFOTOMAPA&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/WMTS/guest/wmts/ORTO?service%3DWMTS%26request%3DgetCapabilities'},
        {"source": "wms", "name": "Geoportal HD", "root": False, "parent": "sat", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/jpeg&layers=ORTOFOTOMAPA&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMTS/HighResolution?service%3DWMTS%26request%3DgetCapabilities'},
        {"source": "gdal", "name": "Google Earth Pro", "root": False, "parent": "sat", "visible": False, "uri": '{UI_PATH}ge.jpg', "crs": -1},
        {"source": "wms", "name": "Google Map", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0'},
        {"source": "wms", "name": "OpenStreetMap", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:3857&format&type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0'},
        {"source": "wms", "name": "Topograficzna", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/jpeg&layers=MAPA TOPOGRAFICZNA&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/WMTS/guest/wmts/TOPO?service%3DWMTS%26request%3DgetCapabilities'},
        {"source": "wms", "name": "BDOT", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/png&layers=BDOT10k&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/WMTS/guest/wmts/BDOT10k?service%3DWMTS%26request%3DgetCapabilities'},
        {"source": "wms", "name": "BDOO", "root": False, "parent": "topo", "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/png&layers=BDOO&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/WMTS/guest/wmts/BDOO?service%3DWMTS%26request%3DgetCapabilities'},
        {"source": "wms", "name": "ISOK", "root": False, "parent": "basemaps", "pos": 0, "visible": False, "uri": 'crs=EPSG:2180&dpiMode=0&featureCount=10&format=image/jpeg&layers=ISOK_Cien&styles=default&tileMatrixSet=EPSG:2180&url=https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMTS/ShadedRelief?service%3DWMTS%26request%3DgetCapabilities'},
        {"source": "memory", "name": "edit_poly", "root": False, "parent": "temp", "visible": True, "uri": "Polygon?crs=epsg:2180&field=id:integer", "attrib": [QgsField('part', QVariant.Int)]},
        {"source": "memory", "name": "backup_poly", "root": False, "parent": "temp", "visible": False, "uri": "Polygon?crs=epsg:2180&field=id:integer", "attrib": [QgsField('part', QVariant.Int)]}
        ]

    i = 0
    i_max = len(lyrs)
    for l_dict in lyrs:
        QgsApplication.processEvents()
        i += 1
        dlg.splash_screen.p_bar.setValue(i * 100 / i_max)
        QgsApplication.processEvents()
        raw_uri = l_dict["uri"]
        uri = eval("f'{}'".format(raw_uri))
        if l_dict["source"] == "wms" or l_dict["source"] == "gdal":
            lyr = QgsRasterLayer(uri, l_dict["name"], l_dict["source"])
        else:
            lyr = QgsVectorLayer(uri, l_dict["name"], l_dict["source"])
        if not lyr.isValid():
            print(f'Nie udało się załadować warstwy {l_dict["name"]}')
        if l_dict["source"] == "memory":
            lyr.setCustomProperty("skipMemoryLayersCheck", 1)
            pr = lyr.dataProvider()
            pr.addAttributes(l_dict["attrib"])
            lyr.updateFields()
        if "crs" in l_dict:
            lyr.setCrs(CRS_1992)
        proj.addMapLayer(lyr, False)
        if l_dict["root"]:
            parent_grp = root
            parent_grp.insertChildNode(l_dict["pos"], QgsLayerTreeLayer(lyr))
            parent_grp.findLayer(lyr).setItemVisibilityChecked(l_dict["visible"])
        else:
            if "pos" in l_dict:
                parent_grp = root.findGroup(l_dict["parent"])
                parent_grp.insertChildNode(l_dict["pos"], QgsLayerTreeLayer(lyr))
                parent_grp.findLayer(lyr).setItemVisibilityChecked(False)
            else:
                parent_grp = root.findGroup(l_dict["parent"])
                node = parent_grp.addLayer(lyr)
                node.setItemVisibilityChecked(l_dict["visible"])
        lyr.loadNamedStyle(f'{STYLE_PATH}{l_dict["name"].lower()}.qml')
