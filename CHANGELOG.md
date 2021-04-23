# Changelog (dziennik zmian):

## [0.3.0] - 2021-04-20
### Dodano
- Uruchamianie wtyczki z otwartym "własnym" plikiem projektowym (możliwość korzystania z dodatkowych warstw danych).
- Do głównego okna wtyczki dodano panele "Flagi" i "Wyrobiska" z przyciskami filtrującymi wyświetlane obiekty.
- Aby zminimalizować ilość zajętego miejsca okna wtyczki w doku, wprowadzono możliwość "zwijania" niektórych paneli.
- Do panelu powiatów dodano przycisk włączenia/wyłączenia trybu maskowania obszarów spoza aktywnych powiatów.
- Wszystkie ustawienia stanu i widoczności paneli oraz warstw obiektów są zapamiętywane na poziomie zespołu (każdy zespół może mieć swój zestaw ustawień) i wczytywane przy uruchamianiu wtyczki (lub przełączaniu między zespołami).
- Wprowadzono podział wyrobisk na: "wyrobiska przed kontrolą terenową", "wyrobiska potwierdzone" i "wyrobiska odrzucone".
- Po kliknięciu na mapie w symbol punktu WN_PNE, pojawia się panel WN_Kopaliny_PNE z informacjami dotyczącymi danego punktu.
- Punkty WN_PNE zostały przypisane do powiatów i na mapie wyświetlane są wyłącznie te, które należą do aktywnego powiatu/powiatów.
- Punkty WN_PNE leżące w zasięgu 1 km bufora od granic powiatów, są przypisane do wszystkich przyległych powiatów - wykonawca może w panelu WN_Kopaliny_PNE wyłączyć powiaty, do których punkt nie należy.
- Wprowadzono możliwość przełączania się pomiędzy punktami WN_PNE, wpisując znany numer 'id_arkusz' (należy wpisać pełną nazwę, np. '0778_008', a nie '778_008').

### Zmieniono
- Wygląd i sposób wyświetlania etykiet powiatów.
- Zmodyfikowano adresy WMS, aby wyświetlały polskie nazwy miejscowości.

### Poprawiono
- Program nie zawiesza się przy zamykaniu, gdy wtyczka jest włączona (nie trzeba już wyłączać wtyczki przed zamknięciem QGIS).
- Wiele drobnych błędów.
