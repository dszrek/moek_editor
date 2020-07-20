# -*- coding: utf-8 -*-
import os

from PyQt5.QtWidgets import QWidget, QFrame, QSpinBox, QComboBox, QToolButton, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QPixmap, QPen, QIcon, QColor, QBrush, QFont
from qgis.core import QgsProject
from qgis.utils import iface

from .viewnet import vn_zoom
from .main import vn_cfg
from .classes import PgConn

ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'ui' + os.path.sep
dlg = None

def dlg_sequences(_dlg):
    """Przekazanie referencji interfejsu dockwigetu do zmiennej globalnej."""
    global dlg
    dlg = _dlg

def sequences_load():
    """Załadowanie z db ustawień użytkownika, dotyczących sekwencyjnego wczytywania podkładów mapowych."""
    # print("[sequences_load]")
    for s in range(1,3):  # Iteracja dla sekwencji nr 1 i nr 2
        seq = db_seq(s)  # Pobranie danych sekwencji
        if seq:  # Sekwencja nie jest pusta
            # Ustawienie parametru empty w przycisku sekwencji:
            dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].empty = False
            # Aktualizacja ilości podkładów sekwencji seqcfgbox'ie:
            dlg.p_vn.widgets["scg_seq" + str(s)].cnt = len(seq)
        else:  # Sekwencja jest pusta
            # Ustawienie parametru empty w przycisku sekwencji:
            dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].empty = True
            # Aktualizacja ilości podkładów sekwencji seqcfgbox'ie:
            dlg.p_vn.widgets["scg_seq" + str(s)].cnt = 0
            seq = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
        # Czyszczenie przycisku sekwencji z danych sekwencji:
        dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].maps.clear()
        # Aktualizacja seqcfg'ów:
        m = 0
        for map in seq:
            # Wczytanie danych do przycisku sekwencji:
            if map[0] > 0:  # Pominięcie w przycisku pustych podkładów
                dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(s)].maps.append([map[0], map[1]])
            # Wczytanie danych do seqcfg'ów (obiektów przechowujących ustawienia podkładów mapowych z sekwencji):
            dlg.p_vn.widgets["scg_seq" + str(s)].scgs["scg_" + str(m)].spinbox.value = map[1]  # Opóźnienie
            dlg.p_vn.widgets["scg_seq" + str(s)].scgs["scg_" + str(m)].map = map[0]  # Id mapy
            m += 1


def db_seq(num):
    """Sprawdzenie, czy w tabeli basemaps z aktywnego teamu dla zalogowanego użytkownika są ustawienia dla sekwencji nr 1 lub 2."""
    # print("[db_seq]")
    db = PgConn()
    sql = "SELECT map_id, i_delay_" + str(num) + " FROM team_" + str(dlg.team_i) + ".basemaps WHERE user_id = " + str(dlg.user_id) + " AND i_order_" + str(num) + " IS NOT NULL ORDER BY i_order_" + str(num) + " ASC;"
    if db:
        res = db.query_sel(sql, True)
        if res:
            return res
        else:
            return False

def db_sequence_update(seq, list):
    """Aktualizacja sekwencji w db."""
    # print("[db_sequence_update]")
    if db_sequence_reset(seq):
        print("Wyczyszczono sekwencję w db.")
    else:
        print("Nie udało się wyczyścić sekwencji!")
        return
    db = PgConn()
    sql = "UPDATE team_" + str(dlg.team_i) + ".basemaps AS bm SET i_order_" + str(seq) + " = d.i_order_" + str(seq) + ", i_delay_" + str(seq) + " = d.i_delay_" + str(seq) + " FROM (VALUES %s) AS d (map_id, i_order_" + str(seq) + ", i_delay_" + str(seq) + ") WHERE bm.map_id = d.map_id AND bm.user_id = " + str(dlg.user_id) + ";"
    if db:
        db.query_exeval(sql, list)

def db_sequence_reset(seq):
    """Wyczyszczenie w db dotychczasowych ustawień sekwencji."""
    # print(f"[db_sequence_reset]: {seq}")
    db = PgConn()
    # Aktualizacja i_order_[seq] = NULL i i_delay)[seq] dla użytkownika w tabeli 'basemaps':
    sql = "UPDATE team_" + str(dlg.team_i) + ".basemaps SET i_order_" + str(seq) + " = NULL, i_delay_" + str(seq) + " = NULL WHERE user_id = " + str(dlg.user_id) + ";"
    if db:
        res = db.query_upd(sql)
        if res:
            return True
        else:
            return False
    else:
        return False

def next_map():
    """Przejście do następnej mapy w aktywnej sekwencji. Funkcja pod skrót klawiszowy."""
    if dlg.p_vn.widgets["sqb_seq"].num > 0:
        dlg.p_vn.widgets["sqb_seq"].next_map()

def prev_map():
    """Przejście do następnej mapy w aktywnej sekwencji. Funkcja pod skrót klawiszowy."""
    if dlg.p_vn.widgets["sqb_seq"].num > 0:
        dlg.p_vn.widgets["sqb_seq"].prev_map()

def seq(_num):
    """Aktywowanie wybranej sekwencji lub jej deaktywacja, jeśli już jest aktywna. Funkcja pod skrót klawiszowy."""
    if dlg.p_vn.widgets["sqb_seq"].num == _num:  # Sekwencja jest aktywna, następuje deaktywacja
        dlg.p_vn.widgets["sqb_seq"].num = 0
    else:  # Sekwencja zostaje aktywowana
        if dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(_num)].empty:  # Sekwencja jest pusta, przejście do ustawień
            dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(_num)].button.setChecked(False)
            dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(_num)].cfg_clicked()
        else:  # Sekwencja nie jest pusta, następuje jej aktywacja
            dlg.p_vn.widgets["sqb_seq"].num = _num


class MoekSeqBox(QFrame):
    """Pojemnik z przyciskami obsługującymi sekwencyjne wczytywanie podkładów mapowych."""
    i_changed = pyqtSignal()
    num_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.ge = MoekButton(name="ge_sync", size=50, checkable=True)
        self.seq_ctrl = MoekSeqCtrlButton()
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(0)
        self.hlay.addWidget(self.seq_ctrl)
        self.sqb_btns = {}
        for r in range(1, 3):
            _sqb = MoekSeqButton(num=r)
            exec('self.hlay.addWidget(_sqb)')
            sqb_name = f'sqb_{r}'
            self.sqb_btns[sqb_name] = _sqb
        self.hlay.addWidget(self.ge)
        self.setLayout(self.hlay)
        self.num_changed.connect(self.num_change)
        self.i_changed.connect(self.i_change)
        self.num = 0  # Numer aktywnej sekwencji (0 - brak aktywnej sekwencji)
        self.i = 0  # Liczba porządkowa aktualnego podkładu mapowego w aktywnej sekwencji

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "i":
            self.i_changed.emit()
        elif attr == "num":
            self.num_changed.emit(val)

    def enter_setup(self, seq):
        """Przejście do strony ustawień którejś sekwencji."""
        dlg.p_vn.widgets["sab_seq" + str(seq)].combobox_update(seq)  # Aktualizacja combobox'a
        dlg.p_vn.box.setCurrentIndex(seq)  # Przełączenie panelu na stronę ustawień sekwencji

    def exit_setup(self):
        """Zamknięcie strony ustawień dla którejś sekwencji."""
        sid = dlg.p_vn.box.currentIndex()
        scb = dlg.p_vn.widgets["scg_seq" + str(sid)]  # Referencja seqcfgbox'a
        if scb.cnt == 1:  # Nie może być tylko jednego podkładu mapowego w sekwencji
            m_text = "Aby zapisać zmiany w sekwencji, należy wybrać conajmniej 2 podkłady. Naciśnięcie Tak spowoduje wyjście z ustawień bez zapisania zmian."
            reply = QMessageBox.question(iface.mainWindow(), "Kontynuować?", m_text, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                dlg.p_vn.bar.cfg_btn.setChecked(True)
                return
            else:
                sequences_load()  # Przeładowanie ustawień sekwencji
                dlg.p_vn.widgets["sqb_seq"].num = 0  # Deaktywacja sekwencji
                dlg.p_vn.box.setCurrentIndex(0)  # Przejście do strony głównej panelu
                return
        # Utworzenie listy z ustawieniami sekwencji:
        scgs = dlg.p_vn.widgets["scg_seq" + str(sid)].findChildren(MoekSeqCfg)  # Referencje do seqcfg'ów
        m_list = []
        order = 0
        for scg in scgs:
            if scg.map > 0:
                m_list.append((scg.map, order, scg.spinbox.value))
                order += 1
        # Aktualizacja sekwencji w db:
        db_sequence_update(sid, m_list)
        sequences_load()
        dlg.p_vn.widgets["sqb_seq"].num = 0  # Deaktywacja sekwencji
        dlg.p_vn.box.setCurrentIndex(0)  # Przejście do strony głównej panelu

    def i_change(self):
        """Zmiana bieżącego podkładu mapowego w aktywnej sekwencji."""
        try:
            self.change_map()
        except KeyError:
            pass
        self.seq_ctrl.seq_dial.active = self.i  # Aktualizacja kontrolki (kolory prostokącików)

    def num_change(self):
        """Zmiana aktywnej sekwencji."""
        self.i = 0  # Przejście do pierwszej mapy z sekwencji
        seqbtns = self.findChildren(MoekSeqButton)  # Referencje do przycisków sekwencji
        # Aktualizacja wyglądu przycisków:
        for seqbtn in seqbtns:
            seqbtn.active = True if seqbtn.num == self.num else False
        self.seq_ctrl.setEnabled(False) if self.num == 0 else self.seq_ctrl.setEnabled(True)

    def change_map(self):
        """Zmiana podkładu mapowego."""
        map_id = self.sqb_btns["sqb_" + str(self.num)].maps[self.i][0]
        dlg.p_map.map = map_id

    def player(self):
        """Odtwarzanie sekwencyjnego wczytywania podkładów mapowych."""
        # Przerwanie poprzedniego sekwencyjnego wczytywania, jeśli jeszcze trwa:
        try:
            self.timer.stop()
            self.timer.deleteLater()
            self.sqb_btns["sqb_" + str(self.num)].progbar.value = 0
        except (AttributeError, RuntimeError):
            pass
        self.i = 0  # Przejście do pierwszego podkładu mapowego z sekwencji
        delay = self.sqb_btns["sqb_" + str(self.num)].maps[self.i][1]  # Pobranie opóźnienia
        self.set_timer(delay)  # Uruchomienie stopera
        vn_zoom()  # Przybliżenie widoku mapy do nowego vn'a

    def set_timer(self, period):
        """Ustawienie i odpalenie funkcji odmierzającej czas."""
        self.period = period  # Całkowity czas
        self.tick = period / 10  # Interwał odświeżania progressbar'a
        self.tack = 0  # Wartość dla progressbar'a
        self.lasted = 0.0  # Czas, który już minął
        # Stworzenie stopera i jego odpalenie:
        self.timer = QTimer(self, interval=self.tick * 1000)
        self.timer.timeout.connect(self.run_timer)
        self.timer.start()  # Odpalenie stopera

    def run_timer(self):
        """Funkcja odmierzająca czas."""
        self.lasted += self.tick
        self.tack += 1
        # if self.tack == 5:
        #     iface.mapCanvas().refresh()
        # Odświeżenie progressbar'a:
        self.sqb_btns["sqb_" + str(self.num)].progbar.value = self.tack
        if self.lasted >= self.period:  # Czas dobiegł końca
            # Kasowanie licznika:
            self.timer.stop()
            self.timer.deleteLater()
            self.sqb_btns["sqb_" + str(self.num)].progbar.value = 0
            if self.i < len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1:
                self.next_map(player=True)  # Wczytanie kolejnego podkładu

    def prev_map(self):
        """Wczytanie poprzedniego podkładu mapowego z sekwencji."""
        if self.i > 0:  # Można się jeszcze cofnąć w sekwencji
            self.i -= 1  # Przejście do poprzedniego podkładu mapowego
        else:  # Przejście do ostatniego podkładu mapowego z aktywnej sekwencji
            self.i = len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1

    def next_map(self, player=False):
        """Wczytanie kolejnego podkładu mapowego z sekwencji."""
        if self.i < len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1:  # Pozostał jeszcze conajmniej jeden podkład do wczytania
            self.i += 1  # Przejście do następnego podkładu mapowego
            # Odpalenie stopera, jeśli uruchomiony jest player:
            if player and self.i < len(self.sqb_btns["sqb_" + str(self.num)].maps) - 1:
                delay = self.sqb_btns["sqb_" + str(self.num)].maps[self.i][1]
                self.set_timer(delay)  # Odpalenie stopera
        else:  # Powrót do początku sekwencji
            self.i = 0


class MoekSeqCtrlButton(QFrame):
    """Przycisk-kontrolka sterujący sekwencją podkładów mapowych."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(50, 50)
        self.seq_dial = MoekSeqDial(self)
        self.seq_prev = MoekButton(self, hsize=50, name="seq_prev")
        self.seq_next = MoekButton(self, hsize=50, name="seq_next")
        self.seq_dial.setGeometry(0, 0, 50, 50)
        self.seq_prev.setGeometry(0, 0, 25, 50)
        self.seq_next.setGeometry(25, 0, 25, 50)
        self.seq_prev.clicked.connect(self.prev_clicked)
        self.seq_next.clicked.connect(self.next_clicked)

    def changeEvent(self, event):
        """Ustawienie widoczności wskaźników kontrolki (kolorowe prostokąciki) w zależności od stanu przycisku."""
        self.seq_dial.setVisible(True) if self.isEnabled() else self.seq_dial.setVisible(False)

    def prev_clicked(self):
        """Naciśnięcie przycisku przejścia do następnego podkładu w sekwencji."""
        self.parent().prev_map()

    def next_clicked(self):
        """Naciśnięcie przycisku przejścia do poprzedniego podkładu w sekwencji."""
        self.parent().next_map()


class MoekSeqButton(QFrame):
    """Przycisk obsługujący sekwencyjne wczytywanie podkładów mapowych."""
    empty_changed = pyqtSignal()
    activated = pyqtSignal(bool)

    def __init__(self, *args, num):
        super().__init__(*args)
        self.num = num
        self.empty = None
        self.progbar = MoekSeqProgressBar(self)
        self.progbar.setGeometry(0, 0, 50, 50)
        self.button = MoekButton(self, name="seq" + str(num), checkable=True)
        self.button.setFixedSize(25, 25)
        self.button.setGeometry(12.5, 12.5, 25, 25)
        self.button.clicked.connect(self.btn_clicked)
        self.cfg_btn = MoekButton(self, name="seq_cfg", icon="seqcfg", checkable=False)
        self.cfg_btn.setFixedSize(19, 19)
        self.cfg_btn.setGeometry(15.5, 32, 19, 19)
        self.maps = []
        self.empty_changed.connect(self.empty_change)
        self.activated.connect(self.active_change)
        self.cfg_btn.clicked.connect(self.cfg_clicked)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "empty":
            self.empty_changed.emit()
        elif attr == "active":
            self.activated.emit(val)

    def active_change(self, value):
        """Zmiana trybu active."""
        self.progbar.active = True if value else False
        self.button.setChecked(True) if value else self.button.setChecked(False)
        if value:
            # Aktualizacja ilości wskaźników na kontrolce (prostokącików):
            self.parent().seq_ctrl.seq_dial.all = len(self.maps)
        if self.empty:
            self.button.set_icon("seq_empty")
            self.cfg_btn.set_icon("seqcfg")
        else:
            self.button.set_icon("seq" + str(self.num))
            self.cfg_btn.set_icon("seqcfg1") if value else self.cfg_btn.set_icon("seqcfg0")

    def empty_change(self):
        # print(f"empty_change: {self.empty}")
        """Zmiana wypełnienia sekwencji (są lub nie ma podkładów)."""
        self.set_style(False) if self.empty else self.set_style(True)

    def set_style(self, value):
        """Modyfikacja stylu przycisku przy zmianie atrybutu empty."""
        self.button.set_icon("seq" + str(self.num)) if value else self.button.set_icon("seq_empty")
        if value:
            self.cfg_btn.setEnabled(True)
            self.cfg_btn.set_icon("seqcfg1") if self.active else self.cfg_btn.set_icon("seqcfg0")
        else:
            self.cfg_btn.setEnabled(False)

    def btn_clicked(self):
        """Zmiana kategorii map po wciśnięciu przycisku lub wejście do ustawień, jeśli sekwencja jest pusta."""
        if self.button.isChecked():
            if self.empty:
                self.button.setChecked(False)
                self.cfg_clicked()  # Wejście do ustawień sekwencji
            else:
                self.parent().num = self.num  # Aktywacja sekwencji
        else:
            self.parent().num = 0  # Deaktywacja sekwencji

    def cfg_clicked(self):
        """Wejście do trybu ustawień sekwencji."""
        dlg.p_vn.bar.cfg_btn.setChecked(True)
        vn_cfg(seq=self.num)

class MoekSeqDial(QWidget):
    """Wskaźnik kolejności i ilości podkładów mapowych w sekwencji."""
    active_changed = pyqtSignal(int)
    all_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.setFixedSize(50, 50)
        self.active_changed.connect(self.dial_change)
        self.all_changed.connect(self.dial_change)
        self.active = 0
        self.all = 0
        self.modified = False
        self.pixmap = QPixmap()

        self.r = [
                    [
                    [20, 4], [26, 4]
                    ],
                    [
                    [16, 4], [23, 4], [30, 4]
                    ],
                    [
                    [16, 3], [21, 3], [26, 3], [31, 3]
                    ],
                    [
                    [16, 2], [20, 2], [24, 2], [28, 2], [32, 2]
                    ]
                ]

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.active_changed.emit(val)
        elif attr == "all":
            self.all_changed.emit(val)

    def dial_change(self):
        """Zmiana trybu active."""
        self.modified = True
        self.update()

    def paintEvent(self, e):
        """Funkcja rysująca."""
        if self.modified:
            _pixmap = QPixmap(self.size())
            _pixmap.fill(QColor(255, 255, 255))
            painter = QPainter(_pixmap)
            brush = QBrush()
            brush.setColor(QColor(255, 192, 0))
            brush.setStyle(Qt.SolidPattern)
            for r in range(self.all):
                _list = self.r[self.all - 2][r]
                _rect = QRect(_list[0], 21, _list[1], 8)
                painter.fillRect(_rect, brush)
            brush.setColor(QColor(52, 132, 240))
            _list = self.r[self.all - 2][self.active]
            _rect = QRect(_list[0], 21, _list[1], 8)
            painter.fillRect(_rect, brush)
            self.pixmap = _pixmap
            self.modified = False
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap)


class MoekSeqProgressBar(QWidget):
    """Wskaźnik upływu czasu przy zmianie mapy podczas sekwencyjnego wczytywania podkładów mapowych."""
    activated = pyqtSignal(bool)
    value_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.setFixedSize(50, 50)
        self.value = 0
        self.min_value = 0
        self.max_value = 10
        self.start_angle = 26
        self.end_angle = 26
        self.arcWidth = 5
        self.bg_color = QColor()
        self.pg_color = QColor()
        self.activated.connect(self.active_change)
        self.value_changed.connect(self.repaint)
        self.active = False

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "active":
            self.activated.emit(val)
        elif attr == "value":
            self.value_changed.emit(val)

    def active_change(self, value):
        """Zmiana trybu active."""
        self.bg_color = QColor(52, 132, 240, 77) if value else QColor(255, 192, 0, 77)
        self.pg_color = QColor(52, 132, 240) if value else QColor(255, 192, 0)
        self.repaint()

    def paintEvent(self, e):
        """Funkcja rysująca."""
        width = self.width()
        height = self.height()

        painter = QPainter()
        painter.begin(self)
        painter.translate(width/2-0.5, height/2-0.5)
        radius = 22 - self.arcWidth
        painter.setBrush(Qt.NoBrush)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(self.arcWidth)
        pen.setCapStyle(Qt.RoundCap)
        pen.setColor(self.bg_color)

        angle_all = 360.0 - self.start_angle - self.end_angle
        angle_current = angle_all * ((self.value - self.min_value) / (self.max_value - self.min_value))
        angle_other = angle_all - angle_current
        rect = QRect(-radius, -radius, radius * 2, radius * 2)

        painter.setPen(pen)
        painter.drawArc(rect, (270 - self.start_angle - angle_current - angle_other) * 16, angle_all * 16)
        pen.setColor(self.pg_color)
        painter.setPen(pen)
        painter.drawArc(rect, (270 - self.start_angle - angle_current) * 16, angle_current * 16)
        painter.setBrush(self.bg_color) if self.parent().empty else painter.setBrush(self.pg_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse (-3, 14, 6, 6)
        painter.end()


class MoekSeqAddBox(QFrame):
    """Pojemnik na wiget'y używane do dodawania podkładów mapowych do sekwencji."""
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.setFixedHeight(32)
        self.combobox = MoekComboBox(height=24, border=1)
        self.add_btn = MoekButton(name="add")
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(8, 4, 2, 4)
        self.hlay.setSpacing(6)
        self.hlay.addWidget(self.combobox, 10)
        self.hlay.addWidget(self.add_btn, 1)
        self.setLayout(self.hlay)
        self.maps = []
        self.add_btn.clicked.connect(self.add_basemap)

    def combobox_update(self, _id):
        """Aktualizacja combobox'a o listę dostępnych i jeszcze nieaktywnych podkładów mapowych."""
        # print(f"combobox_update: {_id}")
        scg = dlg.p_vn.widgets["scg_seq" + str(_id)].findChildren(MoekSeqCfg)  # Referencje seqcfg'ów
        # Lista wszystkich włączonych podkładów mapowych:
        maps = [map["id"] for map in dlg.p_map.all if map["enabled"]]
        # Lista numerów podkładów, które już są dodane do sekwencji:
        scg_maps = [s.map for s in scg]
        # Lista numerów podkładów, które powinny znaleźć się w combobox'ie:
        avail_maps = list(set(maps) - set(scg_maps))
        # Lista z danymi do zasilenia combobox'a:
        cmb_list = [[map["id"], map["name"]] for map in dlg.p_map.all if map["id"] in avail_maps]
        self.combobox.clear()
        # Populacja combobox'a:
        for m in cmb_list:
            self.combobox.addItem(m[1], m[0])

    def add_basemap(self):
        """Dodanie wybranego w combobox'ie podkładu mapowego do pojemnika ustawień sekwencji."""
        map_id = self.combobox.currentData(Qt.UserRole)
        scb = dlg.p_vn.widgets["scg_seq" + str(self.id)]  # Referencja seqcfgbox'a
        sid = scb.cnt  # Numer seqcfg'a, który będzie populowany
        scg = scb.scgs["scg_" + str(sid)]  # Referencja seqcfg'a
        scg.spinbox.value = 1  # Ustalenie opóźnienia nowoaktywowanego seqcfg'a
        scg.map = map_id  # Ustalenie mapy dla nowoaktywowanego seqcfg'a
        scb.cnt += 1  # Dodanie do aktywnych jednego seqcfg'a z puli seqcfbox'a
        # Wczytanie danych do przycisku sekwencji:
        dlg.p_vn.widgets["sqb_seq"].sqb_btns["sqb_" + str(self.id)].maps.append([scg.map, scg.spinbox.value])


class MoekSeqCfgBox(QFrame):
    """Pojemnik na wybrane podkłady mapowe w trybie ustawień sekwencji."""
    cnt_changed = pyqtSignal(int)

    def __init__(self, _id):
        super().__init__()
        self.id = _id
        self.height = int()
        self.vlay = QVBoxLayout()
        self.vlay.setContentsMargins(0, 6, 0, 6)
        self.vlay.setSpacing(6)
        self.scgs = {}
        self.lns = {}
        for c in range(5):
            _ln = MoekHLine()
            self.vlay.addWidget(_ln)
            ln_name = f'ln_{c}'
            self.lns[ln_name] = _ln
            _scg = MoekSeqCfg(_id=c)
            self.vlay.addWidget(_scg)
            scg_name = f'scg_{c}'
            self.scgs[scg_name] = _scg
        self.setLayout(self.vlay)
        self.cnt = int()
        self.cnt_changed.connect(self.cnt_change)


    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "cnt":
            self.cnt_changed.emit(val)

    def cnt_change(self):
        """Zmiana ilości aktywnych seqcfg'ów w seqcfgbox'ie."""
        # Obejście problemów z sizePolicy przy zmianie ilości widocznych seqcfg'ów:
        self.height = 83+38*(self.cnt - 1)  # Obliczenie wysokości pojemnika
        # Ustawienie odpowiedniej wysokości pojemnika:
        if self.size().height() != 480:  # Pominięcie zmiany przy starcie plugin'u
            self.parent().parent().setMinimumHeight(self.height)
            self.parent().parent().setMaximumHeight(self.height)
        c = 0
        for scg in self.scgs:
            # Wyświetlenie odpowiedniej liczby seqcfg'ów i linii separacyjnych:
            self.scgs["scg_" + str(c)].setVisible(True) if c < self.cnt else self.scgs["scg_" + str(c)].setVisible(False)
            self.lns["ln_" + str(c)].setVisible(True) if c < self.cnt else self.lns["ln_" + str(c)].setVisible(False)
            # Ustawienie atrybutu last na ostatnim aktywnym seqcfg'u:
            if c == self.cnt - 1:
                self.scgs["scg_" + str(c)].last = True
            else:
                self.scgs["scg_" + str(c)].last = False
            c += 1
        sab = dlg.p_vn.widgets["sab_seq" + str(self.id)]  # Referencja seqaddbox'a
        sab.combobox_update(self.id)  # Aktualizacja combobox'a
        # Uniemożliwienie dodania do sekwencji więcej niż 5 podkładów mapowych:
        sab.add_btn.setEnabled(False) if self.cnt == 5 else sab.add_btn.setEnabled(True)


class MoekSeqCfg(QFrame):
    """Obiekt listy wybranych podkładów mapowych w trybie ustawień sekwencji."""
    map_changed = pyqtSignal()
    last_changed = pyqtSignal()

    def __init__(self, _id):
        super().__init__()
        self.id = _id
        self.setObjectName("box")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setFixedHeight(25)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(3, 0, 2, 0)
        self.hlay.setSpacing(4)
        self.order = MoekOrder()
        self.label = MoekSeqLabel(self)
        self.label.setObjectName("lbl")
        self.spinbox = MoekSeqSpinBox(self)
        self.del_btn = MoekButton(name="del", size=24)
        self.hlay.addWidget(self.order)
        self.hlay.addWidget(self.label)
        self.hlay.addWidget(self.spinbox)
        self.hlay.addWidget(self.del_btn)
        self.setLayout(self.hlay)
        self.map = int()
        self.last = False
        self.del_btn.clicked.connect(self.del_clicked)
        self.map_changed.connect(self.map_change)
        self.last_changed.connect(self.last_change)
        self.setStyleSheet("""
                               QFrame#box {background-color: white; border: none; border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px}
                               QFrame#lbl {color: rgb(52, 132, 240); qproperty-alignment: AlignCenter}
                               """)

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "map":
            self.map_changed.emit()
        elif attr == "last":
            self.last_changed.emit()

    def resizeEvent(self, e):
        """Zmiana szerokości seqcfg'a - aktualizacja labela w seqcfg'u."""
        super().resizeEvent(e)
        self.findChildren(MoekSeqLabel)[0].label_update()

    def map_change(self):
        """Zmiana mapy w seqcfg'u."""
        for map in dlg.p_map.all:
            if map["id"] == self.map:
                self.label.setText(map["name"])

    def del_clicked(self):
        """Wyczyszczenie wybranego seqcfg'u."""
        # bid = self.parent().parent().id  # Numer seqcfgbox'a
        seqcfgs = []  # Lista z danymi z pozostałych po kasowaniu seqcfg'ów
        # Zapamiętanie danych z pozostałych po kasowaniu seqcfg'ów:
        for scg in self.parent().findChildren(MoekSeqCfg):
            if scg.id != self.id:
                seqcfgs.append([scg.map, scg.spinbox.value])
        # Czyszczenie wszystkich seqcfg'ów:
        for scg in self.parent().findChildren(MoekSeqCfg):
            scg.map, scg.spinbox.value = 0, 0
        # Wczytanie danych do nowych seqcfg'ów:
        for i in range(self.parent().cnt - 1):
            self.parent().scgs["scg_" + str(i)].spinbox.value = seqcfgs[i][1]
            self.parent().scgs["scg_" + str(i)].map = seqcfgs[i][0]
        self.parent().cnt -= 1  # Aktualizacja ilości aktywnych seqcfg'ów
        # dlg.p_vn.widgets["sab_seq" + str(self.parent().id)].combobox_update(self.parent().id)  # Aktualizacja combobox'a

    def last_change(self):
        """Dostosowanie przycisków zmiany kolejności."""
        self.order.way = "up" if self.last else "both"
        if self.id == 0 and self.parent().cnt > 1:
            self.order.way = "down"
        elif self.id == 0 and self.parent().cnt <= 1:
            self.order.way = "none"


class MoekOrder(QFrame):
    """Przycisk-kontrolka wiget'u obsługującego sekwencyjne wczytywanie podkładów mapowych."""
    way_changed = pyqtSignal(str)

    def __init__(self, *args, way="both"):
        super().__init__(*args)
        self.setFixedSize(24, 24)
        self.up_btn = MoekButton(self, name="order_up", size=24, hsize=12)
        self.down_btn = MoekButton(self, name="order_down", size=24, hsize=12)
        self.up_btn.setGeometry(0, 1, 24, 12)
        self.down_btn.setGeometry(0, 12, 24, 12)
        self.way_changed.connect(self.way_change)
        self.way = way
        self.up_btn.clicked.connect(lambda: self.order_change(way="up"))
        self.down_btn.clicked.connect(lambda: self.order_change(way="down"))

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "way":
            self.way_changed.emit(val)

    def way_change(self):
        """Działanie przycisków góra/dół w zależności od atrybutu way."""
        if self.way == "both":
            self.up_btn.setEnabled(True)
            self.down_btn.setEnabled(True)
        elif self.way == "up":
            self.up_btn.setEnabled(True)
            self.down_btn.setEnabled(False)
        elif self.way == "down":
            self.up_btn.setEnabled(False)
            self.down_btn.setEnabled(True)
        elif self.way == "none":
            self.up_btn.setEnabled(False)
            self.down_btn.setEnabled(False)

    def order_change(self, way):
        """Zamiana kolejności dwóch sąsiadujących seqcfg'ów."""
        bid = self.parent().parent().id
        id_1 = self.parent().id
        id_2 = id_1 - 1 if way == "up" else id_1 + 1
        map_1 = dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].map
        delay_1 = dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].spinbox.value
        map_2 = dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].map
        delay_2 = dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].spinbox.value
        dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].spinbox.value = delay_2
        dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].spinbox.value = delay_1
        dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_1)].map = map_2
        dlg.p_vn.widgets["scg_seq" + str(bid)].scgs["scg_" + str(id_2)].map = map_1


class MoekSeqSpinBox(QFrame):
    """Widget z centralnie umieszczonym labelem i przyciskami zmiany po jego obu stronach + przycisk konfiguracyjny."""
    value_changed = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(*args)
        self.setObjectName("frm")
        self.setFixedSize(26, 25)
        self.label = QLabel(self)
        self.label.setObjectName("lbl")
        self.label.setGeometry(2, -1, 12, 25)
        self.spinner = MoekSpinner(self)
        self.spinner.setGeometry(13, 1, 12, 25)
        self.set_style(True)
        self.min = 1
        self.max = 9
        self.value_changed.connect(self.value_change)
        self.value = 1

    def __setattr__(self, attr, val):
        """Przechwycenie zmiany atrybutu."""
        super().__setattr__(attr, val)
        if attr == "value":
            self.value_changed.emit(val)

    def setEnabled(self, value):
        super().setEnabled(value)
        self.label.setVisible(value)
        self.spinner.setVisible(value)
        self.set_style(value)

    def set_style(self, value):
        """Modyfikacja stylesheet przy zmianie setEnabled."""
        if value:
            self.setStyleSheet("""
                    QFrame#frm {border: none; border-radius: 0px}
                    QFrame#lbl {color: rgb(52, 132, 240); font-size: 10pt; font-weight: normal; qproperty-alignment: AlignCenter}
                    """)#QFrame#frm {border: 1px solid rgb(52, 132, 240); border-radius: 0px}
        else:
            self.setStyleSheet("""
                    QFrame#frm {border: none; border-radius: 0px}
                    """)

    def value_change(self):
        """Zmiana wartości spinbox'a."""
        self.spinner.down_btn.setEnabled(False) if self.value == self.min else self.spinner.down_btn.setEnabled(True)
        self.spinner.up_btn.setEnabled(False) if self.value == self.max else self.spinner.up_btn.setEnabled(True)
        self.label.setText(str(self.value))


class MoekSpinner(QFrame):
    """Przycisk-kontrolka wiget'u obsługującego sekwencyjne wczytywanie podkładów mapowych."""

    def __init__(self, *args, size="S"):
        super().__init__(*args)
        self.setFixedSize(12, 24)
        self.up_btn = MoekButton(name="up" + size, size=12)
        self.down_btn = MoekButton(name="down" + size, size=12)
        self.vlay = QVBoxLayout()
        self.vlay.setContentsMargins(0, 0, 0, 0)
        self.vlay.setSpacing(0)
        self.vlay.addWidget(self.up_btn)
        self.vlay.addWidget(self.down_btn)
        self.setLayout(self.vlay)
        self.up_btn.clicked.connect(self.up_clicked)
        self.down_btn.clicked.connect(self.down_clicked)

    def up_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk prev_btn."""
        self.parent().value += 1

    def down_clicked(self):
        """Uruchomienie funkcji po kliknięciu na przycisk next_bnt."""
        self.parent().value -= 1

class MoekSeqLabel(QLabel):
    """Fabryka napisów."""
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(25)
        self.setWordWrap(True)
        self.contract()

    def contract(self):
        """Skrócenie szerokości label'u przed pojawieniem się przycisków."""
        self.setFixedWidth(self.width() - 92)

    def setText(self, text):
        """Aktualizacja po zmianie tekstu."""
        super().setText(text)
        self.label_update()

    def label_update(self):
        """Aktualizacja labela po modyfikacji seqbox'a."""
        lbl_width = self.label_width()
        self.setFixedWidth(lbl_width)
        self.font_resize(lbl_width)

    def label_width(self):
        """Zwraca dostępną szerokość dla label'u."""
        btns_width = 92
        spb_width = self.parent().width()
        if spb_width == 640:  # Szerokość bazowa przy tworzeniu widget'u
            spb_width = 196  # Formatowanie do minimalnej szerokości
        # Ustalenie szerokości label'u:
        return spb_width - btns_width

    def font_resize(self, l_w):
        """Zmniejszenie rozmiaru czcionki, jeśli napis się nie mieści."""
        f_size = 9
        marg = 2
        f = QFont("Segoe UI", f_size)
        f.setPointSize(f_size)
        self.setFont(f)
        f_w = self.fontMetrics().boundingRect(self.text()).width() + marg
        while l_w < f_w:
            f_size -= 1
            f.setPointSize(f_size)
            self.setFont(f)
            f_w = self.fontMetrics().boundingRect(self.text()).width() + marg
            if f_size == 8:  # Ograniczenie zmniejszenia czcionki
                return


class MoekHBox(QFrame):
    """Zawartość panelu w kompozycji QHBoxLayout."""
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.hlay = QHBoxLayout()
        self.hlay.setContentsMargins(0, 0, 0, 0)
        self.hlay.setSpacing(0)
        self.setLayout(self.hlay)


class MoekButton(QToolButton):
    """Fabryka guzików."""
    def __init__(self, *args, size=25, hsize=0, name="", icon="", visible=True, enabled=True, checkable=False, tooltip=""):
        super().__init__(*args)
        name = icon if len(icon) > 0 else name
        self.setVisible(visible)
        self.setEnabled(enabled)
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.wsize = size if hsize == 0 else size
        self.hsize = size if hsize == 0 else hsize
        self.setFixedSize(self.wsize, self.hsize)
        self.setIconSize(QSize(self.wsize, self.hsize))
        self.setAutoRaise(True)
        self.setStyleSheet("QToolButton {border: none}")
        self.set_icon(name)

    def set_icon(self, name):
        """Zmiana ikony przycisku."""
        icon = QIcon()
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(self.wsize, self.hsize), mode=QIcon.Normal, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0_act.png", size=QSize(self.wsize, self.hsize), mode=QIcon.Active, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_0.png", size=QSize(self.wsize, self.hsize), mode=QIcon.Selected, state=QIcon.Off)
        icon.addFile(ICON_PATH + name + "_dis.png", size=QSize(self.wsize, self.hsize), mode=QIcon.Disabled, state=QIcon.Off)
        if self.isCheckable():
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(self.wsize, self.hsize), mode=QIcon.Normal, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1_act.png", size=QSize(self.wsize, self.hsize), mode=QIcon.Active, state=QIcon.On)
            icon.addFile(ICON_PATH + name + "_1.png", size=QSize(self.wsize, self.hsize), mode=QIcon.Selected, state=QIcon.On)
        self.setIcon(icon)


class MoekHLine(QFrame):
    """Linia pozioma."""
    def __init__(self, px=1):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(px)
        self.setStyleSheet("QFrame {background-color: rgba(52, 132, 240, 77)}")


class MoekComboBox(QComboBox):
    """Fabryka rozwijanych."""
    def __init__(self, name="", height=25, border=2, b_round="none"):
        super().__init__()
        self.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        self.setAutoFillBackground(False)
        if b_round == "right":
            B_CSS = "border-top-right-radius: 3px; border-bottom-right-radius: 3px;"
        elif b_round == "all":
            B_CSS = "border-radius: 6px;"
        else:
            B_CSS = ""

        self.setStyleSheet("""
                            QComboBox {
                                border: """ + str(border) + """px solid rgb(52, 132, 240);
                                """ + B_CSS + """
                                padding: 0px 5px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                color: rgb(52, 132, 240);
                                font-size: 8pt;
                            }
                            QComboBox:disabled {
                                border: """ + str(border) + """px solid rgb(150, 150, 150);
                                """ + B_CSS + """
                                padding: 0px 5px 0px 5px;
                                min-width: 1px;
                                min-height: """ + str(height) + """px;
                                color: rgb(140, 140, 140);
                                font-size: 8pt;
                            }
                            QComboBox::indicator {
                                background-color:transparent;
                                selection-background-color:transparent;
                                color:transparent;
                                selection-color:transparent;
                            }
                            QComboBox::item:selected {
                                padding-left: 0px;
                                background-color: rgb(52, 132, 240);
                                color: white;
                            }
                            QComboBox::item:!selected {
                                background-color: white;
                                color: rgb(52, 132, 240);
                            }
                            QComboBox:on {
                                padding-top: 3px;
                                padding-left: 4px;
                                background-color: rgb(52, 132, 240);
                                color: white;
                            }
                            QComboBox::drop-down {
                                subcontrol-origin: padding;
                                subcontrol-position: center right;
                                width: 12px;
                                right: 5px;
                                border: none;
                                background: transparent;
                            }
                            QComboBox::down-arrow {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """down_arrow.png');
                            }
                            QComboBox::down-arrow:disabled {
                                image: url('""" + ICON_PATH.replace("\\", "/") + """down_arrow_dis.png');
                            }
                            QComboBox QAbstractItemView {
                                border: """ + str(border) + """px solid rgb(52, 132, 240);
                                background-color: transparent;
                            }
                            QComboBox QAbstractItemView::item {
                                padding-top: 3px;
                                padding-left: 4px;
                                border: """ + str(border) + """px solid rgb(52, 132, 240);
                                background-color: transparent;
                                font-size: 9pt;
                            }
                           """)

        self.findChild(QFrame).setWindowFlags(Qt.Popup | Qt.NoDropShadowWindowHint | Qt.FramelessWindowHint)
