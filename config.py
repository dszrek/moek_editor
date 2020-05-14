#!/usr/bin/python
import os.path
from configparser import ConfigParser


def config(filename='database.ini', section='postgresql'):
    """Parser parametrów konfiguracji, domyślnie czytający database.ini, sekcję 'postgresql'."""

    parser = ConfigParser()  # Stworzenie parsera
    filename = resolve(filename)  # Ustalenie ścieżki do pliku
    parser.read(filename)  # Pobranie zawartości pliku

    db = {}  # Stworzenie słownika
    if parser.has_section(section):
        # Ładowanie parametrów do słownika
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Sekcja {0} nie istnieje w pliku {1}!'.format(section, filename))

    return db

def resolve(name, basepath=None):
    """Zwraca ścieżkę do folderu plugina wraz z nazwą pliku .ini."""
    if not basepath:
      basepath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(basepath, name)
