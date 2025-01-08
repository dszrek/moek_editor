import os
import time
from datetime import date
import shutil
import pandas as pd
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox

DOWNLOAD_PATH = f"{os.path.sep}{os.path.sep}pgi.local{os.path.sep}pig_dfs2{os.path.sep}Projekty{os.path.sep}MGsP2{os.path.sep}NE_MONITORING{os.path.sep}Dane_NE_odbiory{os.path.sep}MIDAS_KARTY{os.path.sep}{os.getlogin().lower()}"
CARDS_PATH = f"{os.path.sep}{os.path.sep}pgi.local{os.path.sep}pig_dfs2{os.path.sep}Projekty{os.path.sep}MGsP2{os.path.sep}NE_MONITORING{os.path.sep}Dane_NE_odbiory{os.path.sep}MIDAS_KARTY"


class WebScraper:
    """Web scraper oparty na selenium używany do pobierania danych ze źródeł internetowych."""
    def __init__(self, plg):
        self.plg = plg
        self.dlg = self.plg.dockwidget
        self.zl_dlg = self.plg.zl_dlg
        self.cag_access = True if os.access('\\\pgi.local\pig_dfs2\Projekty\CAG\Dokumenty CAG', os.R_OK) else False  # Sprawdzenie, czy jest dostęp do repozytorium CAG
        self.drv_midas_headless = None
        self.drv_midas = None
        self.drv_rog = None
        self.drv_dok = None
        self.loc_midas = None
        self.loc_rog = None
        self.loc_dok = None
        self.zl_dlg.btn_midas_card.clicked.connect(self.get_midas_card)
        self.zl_dlg.btn_midas_det.clicked.connect(lambda: self.go_midas("szczegóły"))
        self.zl_dlg.btn_midas_kop.clicked.connect(lambda: self.go_midas("kopaliny"))
        self.zl_dlg.btn_midas_rog.clicked.connect(self.go_rog)
        self.zl_dlg.btn_cbdg_dok.clicked.connect(self.go_dok)

    def init_midas_headless(self):
        """Initialising the Chrome browser instance in the background and opening the 'MIDAS - Złoża kopalin' website."""
        opt = ChromeOptions()
        opt.add_experimental_option('detach', True)
        opt.add_argument("--start-maximized")
        opt.add_argument("--headless=new")
        opt.add_argument("--disable-gpu")
        opt.add_argument("--disable-features=DownloadBubble,DownloadBubbleV2")
        opt.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_PATH
        })
        self.drv_midas_headless = Chrome(options=opt)
        self.drv_midas_headless.get('http://geoportal.pgi.gov.pl/midas-web')
        m_btn = self.drv_midas_headless.find_element('xpath', '//*[@id="btnAccepted"]')
        m_btn.click()
        m_btn = self.drv_midas_headless.find_element('xpath', '//*[@id="toolbarId:main_Zloza:anchor"]')
        m_btn.click()

    def init_midas(self):
        """Zainicjowanie instancji przeglądarki Chrome i otwarcie strony internetowej 'MIDAS - Złoża kopalin'."""
        opt = ChromeOptions()
        opt.add_experimental_option('detach', True)
        opt.add_argument("--start-maximized")
        self.drv_midas = Chrome(options=opt)
        self.drv_midas.get('http://geoportal.pgi.gov.pl/midas-web')
        try:
            m_btn = WebDriverWait(self.drv_midas, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnAccepted"]')))
            m_btn.click()
        except:
            self.drv_reset("midas")
            self.init_midas()
        try:
            m_btn = WebDriverWait(self.drv_midas, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="toolbarId:main_Zloza:anchor"]')))
            m_btn.click()
        except:
            self.drv_reset("midas")
            self.init_midas()
        self.loc_midas = "main"

    def go_midas(self, dest):
        """Przekierowanie strony 'MIDAS - Zloza' do określonego okna."""
        QgsApplication.setOverrideCursor(Qt.WaitCursor)
        if not self.drv_midas:
            self.init_midas()
        else:
            is_ok = self.midas_back()
            if not is_ok:
                self.drv_reset("midas")
                self.go_midas(dest)
                return
        try:
            m_fld1 = WebDriverWait(self.drv_midas, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_nr_zloza"]')))
            m_fld1.clear()
            m_fld1.send_keys(str(self.zl_dlg.zl_id))
        except Exception as error:
            m_fld1 = WebDriverWait(self.drv_midas, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_nr_zloza"]')))
            m_fld1.clear()
            m_fld1.send_keys(str(self.zl_dlg.zl_id))
        m_btn1 = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_btnWyszukaj"]')))
        try:
            m_btn1.click()
        except Exception as error:
            m_btn1 = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_btnWyszukaj"]')))
            m_btn1.click()
        if dest == "szczegóły":
            m_btn2 = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_tabListaWynikow:{str(self.zl_dlg.zl_id)}:wyszukiwanie_zloza_szczegoly_zloza"]')))
            try:
                m_btn2.click()
            except:
                m_btn2 = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_tabListaWynikow:{str(self.zl_dlg.zl_id)}:wyszukiwanie_zloza_szczegoly_zloza"]')))
                m_btn2.click()
            self.loc_midas = "szczegóły"
            QgsApplication.restoreOverrideCursor()
            return
        m_btn2 = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_tabListaWynikow:{str(self.zl_dlg.zl_id)}:wyszukiwanie_zloza_zloza_kopaliny"]')))
        try:
            m_btn2.click()
        except:
            m_btn2 = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_tabListaWynikow:{str(self.zl_dlg.zl_id)}:wyszukiwanie_zloza_zloza_kopaliny"]')))
            m_btn2.click()
        self.loc_midas = "kopaliny"
        if dest == "kopaliny":
            QgsApplication.restoreOverrideCursor()
            return
        wait = WebDriverWait(self.drv_midas, 20).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[2]/div/div/span/table/tbody/tr[2]/td/div/div[2]/form/div[1]/div[2]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr/td/div/table/tbody/tr')))
        kop_cnt = len(self.drv_midas.find_elements('xpath', '/html/body/div[2]/div[2]/div/div/span/table/tbody/tr[2]/td/div/div[2]/form/div[1]/div[2]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr/td/div/table/tbody/tr'))
        for k in range(kop_cnt):
            k += 1
            kop_fld = WebDriverWait(self.drv_midas, 20).until(EC.presence_of_element_located((By.XPATH, f'/html/body/div[2]/div[2]/div/div/span/table/tbody/tr[2]/td/div/div[2]/form/div[1]/div[2]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr/td/div/table/tbody/tr[{str(k)}]/td[1]/div')))
            if kop_fld.text == self.plg.obj.kop_typ_txt:
                kop_btn = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[2]/div[2]/div/div/span/table/tbody/tr[2]/td/div/div[2]/form/div[1]/div[2]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr/td/div/table/tbody/tr[{str(k)}]/td[4]/div/center/input')))
                try:
                    kop_btn.click()
                except:
                    kop_btn = WebDriverWait(self.drv_midas, 20).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[2]/div[2]/div/div/span/table/tbody/tr[2]/td/div/div[2]/form/div[1]/div[2]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr/td/div/table/tbody/tr[{str(k)}]/td[4]/div/center/input')))
                    kop_btn.click()
                self.loc_midas = "zasoby"
                break
        QgsApplication.restoreOverrideCursor()

    def midas_back(self):
        """Przekierowanie strony 'MIDAS - Zloza' do okna startowego."""
        if self.loc_midas == "szczegóły":
            try:
                r0_btn = WebDriverWait(self.drv_midas, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="_f_zs:btnPowrot"]')))
                r0_btn.click()
            except:
                return False
        elif self.loc_midas == "zasoby":
            try:
                r1_btn = WebDriverWait(self.drv_midas, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="id_form:id_zamknij_button"]')))
                r1_btn.click()
            except:
                return False
            try:
                r2_btn = WebDriverWait(self.drv_midas, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="_podTypKopZloz:btnPowrot"]')))
                r2_btn.click()
            except:
                return False
        elif self.loc_midas == "kopaliny":
            try:
                r2_btn = WebDriverWait(self.drv_midas, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="_podTypKopZloz:btnPowrot"]')))
                r2_btn.click()
            except:
                return False
        # Check if session is expired:
        try:
            WebDriverWait(self.drv_midas, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainPanel"]/tbody/tr[3]/td/table/tbody/tr/td/center/label')))
            return False
        except:
            self.loc_midas = "main"
            return True

    def init_rog(self):
        """Zainicjowanie instancji przeglądarki Chrome i otwarcie strony internetowej „MIDAS - Rejestr Obszarów Górniczych”."""
        opt = ChromeOptions()
        opt.add_experimental_option('detach', True)
        opt.add_argument("--start-maximized")
        self.drv_rog = Chrome(options=opt)
        self.drv_rog.get('http://geoportal.pgi.gov.pl/midas-web')
        try:
            m_btn = WebDriverWait(self.drv_rog, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnAccepted"]')))
            m_btn.click()
        except:
            self.drv_reset("rog")
            self.init_rog()
        try:
            m_btn = WebDriverWait(self.drv_rog, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="toolbarId:main_Rog:anchor"]')))
            m_btn.click()
        except:
            self.drv_reset(self.drv_rog)
            self.init_rog()

    def go_rog(self):
        """Przekierowanie strony 'MIDAS - ROG' do określonego okna."""
        QgsApplication.setOverrideCursor(Qt.WaitCursor)
        if not self.drv_rog:
            self.init_rog()
        else:
            is_ok = self.rog_back()
            if not is_ok:
                self.drv_reset("rog")
                self.go_rog()
                return
        try:
            m_fld1 = WebDriverWait(self.drv_rog, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wyszu_przestrzeni_content:wyszu_przestrzeni_field10"]')))
            m_fld1.clear()
            m_fld1.send_keys(str(self.zl_dlg.zl_id))
        except Exception as error:
            m_fld1 = WebDriverWait(self.drv_rog, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wyszu_przestrzeni_content:wyszu_przestrzeni_field10"]')))
            m_fld1.clear()
            m_fld1.send_keys(str(self.zl_dlg.zl_id))
        m_btn1 = WebDriverWait(self.drv_rog, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wyszu_przestrzeni_content:wyszukaj"]')))
        try:
            m_btn1.click()
        except Exception as error:
            m_btn1 = WebDriverWait(self.drv_rog, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wyszu_przestrzeni_content:wyszukaj"]')))
            m_btn1.click()
        QgsApplication.restoreOverrideCursor()

    def rog_back(self):
        """Przekierowanie strony 'MIDAS - ROG' do okna startowego."""
        try:
            r_btn = WebDriverWait(self.drv_rog, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="szczegoly_og:szczegoly_og_btnZamknijId"]')))
            r_btn.click()
            return True
        except:
            pass
        try:
            m_fld1 = WebDriverWait(self.drv_rog, 1).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wyszu_przestrzeni_content:wyszu_przestrzeni_field10"]')))
        except:
            return False
        return True

    def init_dok(self):
        """Zainicjowanie instancji przeglądarki Chrome i otwarcie strony internetowej 'CBDG Dokumenty'."""
        opt = ChromeOptions()
        opt.add_experimental_option('detach', True)
        opt.add_argument("--start-maximized")
        self.drv_dok = Chrome(options=opt)
        self.drv_dok.get('https://dokumenty.pgi.gov.pl/wyszukiwarka/')
        try:
            m_btn = WebDriverWait(self.drv_dok, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ispmodal"]/div/div/div[3]/button')))
            m_btn.click()
        except:
            self.drv_reset("dok")
            self.init_dok()

    def go_dok(self):
        """Przekierowanie strony 'CBDG Dokumenty' do określonego okna."""
        QgsApplication.setOverrideCursor(Qt.WaitCursor)
        if not self.drv_dok:
            self.init_dok()
        else:
            is_ok = self.dok_back()
            if not is_ok:
                self.drv_reset("dok")
                self.go_dok()
                return
        df_dok = pd.DataFrame(columns=['cbdg_id', 'tytuł', 'rok', 'nr inw.', 'nr kat.', 'rep_inw', "rep_kat"])
        m_btn1 = WebDriverWait(self.drv_dok, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app-btn-clear"]')))
        try:
            m_btn1.click()
        except Exception as error:
            m_btn1 = WebDriverWait(self.drv_dok, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app-btn-clear"]')))
            m_btn1.click()
        try:
            m_fld1 = WebDriverWait(self.drv_dok, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dokument-query"]/div[4]/div[1]/div/div[1]/span/span[1]/span/ul/li/input')))
        except:
            m_fld1 = WebDriverWait(self.drv_dok, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dokument-query"]/div[4]/div[1]/div/div[1]/span/span[1]/span/ul/li/input')))
        zl_name = self.zl_dlg.get_zloze_name(self.zl_dlg.zl_id)
        m_fld1.send_keys(f"{zl_name[0]} {zl_name[1]}")
        is_ok = self.wait_for_result('//*[@id="select2-ZlozaId-results"]/li')
        if not is_ok:
            QgsApplication.restoreOverrideCursor()
            return
        try:
            r_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app-btn-search"]')))
            r_btn.click()
        except:
            r_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app-btn-search"]')))
            r_btn.click()
        try:
            l1_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div[3]/div/div[1]/div[1]/div/label/span')))
            l1_btn.click()
        except:
            l1_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div[3]/div/div[1]/div[1]/div/label/span')))
            l1_btn.click()
        try:
            l2_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '/html/body/span/span/span[2]/ul/li[4]')))
            l2_btn.click()
        except:
            l2_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '/html/body/span/span/span[2]/ul/li[4]')))
            l2_btn.click()
        time.sleep(0.3)
        dok_cnt = len(self.drv_dok.find_elements('xpath', '/html/body/div[3]/div/div[3]/div/div[2]/div/table/tbody/tr'))
        # Sprawdzenie, czy jest dokumentacja do złoża:
        is_empty = False
        if dok_cnt == 1:
            empty_txt = WebDriverWait(self.drv_dok, 2).until(EC.presence_of_element_located((By.XPATH, f'/html/body/div[3]/div/div[3]/div/div[2]/div/table/tbody/tr/td'))).text
            if empty_txt == "Brak danych":
                is_empty = True
        if is_empty:
            # Brak dokumentacji:
            QgsApplication.restoreOverrideCursor()
            QMessageBox.information(None, "MOEK_Editor", f"Brak dokumentacji do złoża {self.zl_dlg.zl_id}")
            return
        for d in reversed(range(1, dok_cnt + 1)):
            dok_data = {}
            # Rozwinięcie tabeli z informacjami o dokumentach:
            try:
                d_btn = WebDriverWait(self.drv_dok, 2).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[3]/div/div[3]/div/div[2]/div/table/tbody/tr[{d}]/td[2]')))
                d_btn.click()
            except:
                self.drv_dok.execute_script("window.scrollBy(0,-350)","")
                d_btn = WebDriverWait(self.drv_dok, 2).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[3]/div/div[3]/div/div[2]/div/table/tbody/tr[{d}]/td[2]')))
                d_btn.click()
            # Pozyskanie cbdg_id:
            try:
                d_id = WebDriverWait(self.drv_dok, 2).until(EC.presence_of_element_located((By.XPATH, f'/html/body/div[3]/div/div[3]/div/div[2]/div/table/tbody/tr[{d}]/td[1]'))).text
                dok_data["cbdg_id"] = d_id
                d_txt = '//*[@id="numeryArchiwalne-' + str(d_id) + '"]/div[2]'
            except:
                continue
            # Pozyskanie tytułu dokumentu:
            try:
                d_title = WebDriverWait(self.drv_dok, 2).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="{d_id}"]/td[3]/div/div[2]/div[2]'))).text
                dok_data["tytuł"] = d_title
            except:
                continue
            # Pozyskanie roku dokumentacji:
            try:
                d_year = WebDriverWait(self.drv_dok, 2).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="rokWydania-{d_id}"]/div[2]'))).text
                dok_data["rok"] = d_year
            except:
                continue
            # Pozyskanie informacji o dokumencie:
            try:
                d_list = WebDriverWait(self.drv_dok, 2).until(EC.presence_of_element_located((By.XPATH, d_txt)))
            except:
                continue
            arch_cnt = len(self.drv_dok.find_elements('xpath', f'{d_txt}/ul/li'))
            arch_ids = []
            if arch_cnt > 0:
                for i in range(1, arch_cnt + 1):
                    i_txt = WebDriverWait(self.drv_dok, 2).until(EC.presence_of_element_located((By.XPATH, f'{d_txt}/ul/li[{i}]'))).text
                    if "CAG PIG" in i_txt:
                        arch_ids = self.extract_arch_number(i_txt)
            else:
                i_txt = WebDriverWait(self.drv_dok, 2).until(EC.presence_of_element_located((By.XPATH, f'{d_txt}'))).text
                if "CAG PIG" in i_txt:
                    arch_ids = self.extract_arch_number(i_txt)
            for arch_id in arch_ids:
                if arch_id["is_inw"]:
                    dok_data["nr inw."] = arch_id["id"]
                    dok_data["rep_inw"] = self.check_repository(arch_id["id"])
                else:
                    dok_data["nr kat."] = arch_id["id"]
                    dok_data["rep_kat"] = self.check_repository(arch_id["id"])
            if not "rep_inw" in dok_data:
                dok_data["rep_inw"] = False
            if not "rep_kat" in dok_data:
                dok_data["rep_kat"] = False
            # Dodanie wiersza do dataframe'u:
            row_df = pd.DataFrame(dok_data, index=[0])
            df_dok = pd.concat([df_dok, row_df]).reset_index(drop=True)

        # Przekazanie danych do 'df_dok':
        self.zl_dlg.df_dok = df_dok.sort_values(by=["rok"], ascending=[False]).reset_index(drop=True)
        # Pokazanie tabeli z dokumentami:
        self.zl_dlg.frm_dok.setVisible(True)
        self.drv_dok.execute_script("window.scrollBy(0,0)","")
        QgsApplication.restoreOverrideCursor()

    def extract_arch_number(self, txt):
        """Wyodrębnienie numeru archiwalnego z podanego ciągu znaków."""
        result_list = []
        txt_list = txt.split(" ")
        if "Inw." in txt_list:
            inw_idx = txt_list.index("Inw.")
            num_txt = txt_list[inw_idx + 1].replace("/", "_").replace("ł", "l")
            if txt_list[inw_idx + 2] == "CUG":
                num_txt = f"{num_txt}_CUG"
            result_list.append({"id": num_txt, "is_inw": True})
        if "Kat." in txt_list:
            kat_idx = txt_list.index("Kat.")
            num_txt = txt_list[kat_idx + 1].replace("/", "_").replace("ł", "l")
            if txt_list[kat_idx + 2] == "CUG":
                num_txt = f"{num_txt}_CUG"
            result_list.append({"id": num_txt, "is_inw": False})
        return result_list

    def check_repository(self, arch_id):
        """Sprawdzenie, czy dokument jest dostępny w repozytorium CAG."""
        if not self.cag_access:
            return False
        zc_path = f"\\\pgi.local\pig_dfs2\Projekty\CAG\Dokumenty CAG\Dokumentacje złożowe\{arch_id}\ZC"
        skany_path = f"\\\pgi.local\pig_dfs2\Projekty\CAG\Dokumenty CAG\Dokumentacje złożowe\{arch_id}\Skany"
        return True if os.path.isdir(zc_path) or os.path.isdir(skany_path) else False

    def open_dok_folder(self, arch_id):
        """Otworzenie eksploratora plików ze ścieżką do dokumentu."""
        os.startfile(f"\\\pgi.local\pig_dfs2\Projekty\CAG\Dokumenty CAG\Dokumentacje złożowe\{arch_id}")

    def wait_for_result(self, xpath):
        """Oczekiwanie na wynik wyszukiwania i zatwierdzenie go, jeśli wyraźnie odnosi się do bieżącego złoża."""
        for i in range(0, 20):
            try:
                search = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            except:
                continue
            try:
                s_txt = search.text
            except:
                continue
            if s_txt == "Trwa wyszukiwanie…" or s_txt == "":
                time.sleep(0.1)
                continue
            elif search.text == "Brak wyników":
                return False
            else:
                id_txt = search.text.split(" ", 1)[0]
                if id_txt != str(self.zl_dlg.zl_id):
                    return False
                res = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, f'{xpath}[1]')))
                res.click()
                return True
        return False

    def dok_back(self):
        """Przekierowanie strony 'CBDG Dokumenty' do okna startowego."""
        try:
            u_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/button')))
            u_btn.click()
            time.sleep(1)
        except:
            pass
        try:
            r_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app-btn-back-search"]/span')))
            r_btn.click()
            return True
        except:
            pass
        try:
            m_btn = WebDriverWait(self.drv_dok, 1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app-btn-clear"]')))
        except:
            return False
        return True

    def get_midas_card(self):
        """Pobranie karty złoża z serwisu sieciowego MIDAS (jeśli jeszcze nie ściagnięta) i otworzenie pliku pdf."""
        # Sprawdzenie czy karta nie jest już ściągnięta:
        file_exists = os.path.isfile(os.path.join(CARDS_PATH, f"{self.zl_dlg.zl_id}.pdf"))
        if file_exists:
            # Otwo:
            os.startfile(os.path.join(CARDS_PATH, f"{self.zl_dlg.zl_id}.pdf"))
        else:
            # Download the pdf:
            self.midas_card_download()

    def midas_card_download(self):
        """Pobranie karty złoża z serwisu sieciowego MIDAS."""
        QgsApplication.setOverrideCursor(Qt.WaitCursor)
        # Wyczyszczenie folderu pobranych pdf'ów:
        if os.path.isdir(DOWNLOAD_PATH):
            shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True, onerror=None)
        # Uruchomienie w tle stronę MIDAS, jeśli jeszcze nie została otwarta:
        if not self.drv_midas_headless:
            self.init_midas_headless()
        # Webscraping:
        try:
            m_fld1 = self.drv_midas_headless.find_element('xpath', '//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_nr_zloza"]')
            m_fld1.clear()
            m_fld1.send_keys(str(self.zl_dlg.zl_id))
            m_btn = self.drv_midas_headless.find_element('xpath', '//*[@id="wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_btnWyszukaj"]')
            m_btn.click()
            m_btn = WebDriverWait(self.drv_midas_headless, 10).until(EC.element_to_be_clickable((By.ID, "wyszukiwanie_zloza_f_ws:wyszukiwanie_zloza_tabListaWynikow:" + str(self.zl_dlg.zl_id) + ":wyszukiwanie_zloza_btnKartaZloza")))
            m_btn.click()
            m_fld2 = WebDriverWait(self.drv_midas_headless, 10).until(EC.element_to_be_clickable((By.ID, "kartaZloza_karta_zloza_form:id_stan_na_dzien_txt")))
            m_fld2.clear()
            m_fld2.send_keys(date.today().year - 1)
            m_btn = self.drv_midas_headless.find_element('xpath', '//*[@id="kartaZloza_karta_zloza_form:kartaZloza_raport"]')
            m_btn.click()
            m_btn = self.drv_midas_headless.find_element('xpath', '//*[@id="kartaZloza_hidelink"]')
            m_btn.click()
            self.download_callback()
        except Exception as error:
            QgsApplication.restoreOverrideCursor()
            QMessageBox.critical(None, "MOEK_Editor", "Nastąpił błąd podczas pobierania karty złoża z bazy MIDAS. \n Błąd: {}".format(error))
            self.drv_midas_headless.quit()
            self.drv_midas_headless = None
        QgsApplication.restoreOverrideCursor()

    def download_callback(self):
        """Przeniesienie pliku pdf do folderu repozytorium, zmiana jego nazwy i otworzenie."""
        for i in range(0, 20):
            if os.path.isfile(os.path.join(DOWNLOAD_PATH, 'KartaZloza.pdf')):
                # Przeniesienie pliku pdf do folderu repozytorium ze zmienioną nazwą:
                shutil.copy2(os.path.join(DOWNLOAD_PATH, 'KartaZloza.pdf'), os.path.join(CARDS_PATH, f"{self.zl_dlg.zl_id}.pdf"))
                # Wyczyszczenie folderu pobranych pdf'ów:
                shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True, onerror=None)
                # Otworzenie pliku:
                os.startfile(os.path.join(CARDS_PATH, f"{self.zl_dlg.zl_id}.pdf"))
                return
            else:
                time.sleep(1)

    def drv_reset(self, _obj):
        """Resetowanie driver'a po wystąpieniu błędu lub jego zamknięciu."""
        drv = f"self.drv_{_obj}"
        loc = f"self.loc_{_obj}"
        exec(f"{drv}.quit()")
        exec(f"{drv} = None")
        exec(f"{loc} = None")
        QgsApplication.restoreOverrideCursor()

    def close(self):
        """Czyszczenie po zamknięciu klasy."""
        if self.drv_midas_headless:
            self.drv_midas_headless.quit()
            self.drv_midas_headless = None
        if self.drv_midas:
            self.drv_reset("midas")
        if self.drv_rog:
            self.drv_reset("rog")
        if self.drv_dok:
            self.drv_reset("dok")
