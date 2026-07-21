🇵🇱 Polski · 🇬🇧 [English version](README.md)

# Optymalizacja produkcji i transportu — model MILP

Model programowania całkowitoliczbowego mieszanego (MILP), który wspólnie optymalizuje **planowanie produkcji** oraz **dystrybucję/dobór floty** dla producenta dwóch produktów obsługującego trzech klientów. Zbudowany i rozwiązany w Solverze Excela, zweryfikowany krzyżowo niezależnym solverem open-source.

**Wynik optymalny: zysk 213 750 PLN**, osiągnięty przez produkcję na pełen popyt i konsolidację dostaw w największym pojeździe, z jednym kursem średniej ciężarówki domykającym ładunek, którego duże auto nie wypełnia opłacalnie.

---

## Problem

Producent wytwarza dwa produkty (P1, P2) na dwóch maszynach (M1, M2) i dostarcza je trzem klientom (C1, C2, C3) flotą trzech typów pojazdów. Celem jest dobór wielkości produkcji, przydziału dostaw i liczby kursów każdego pojazdu tak, aby **zmaksymalizować zysk całkowity**:

```
zysk = przychód − koszt produkcji − koszt stały maszyn − koszt pracy − koszt transportu
```

## Struktura modelu

**Zmienne decyzyjne**
- Wielkość produkcji per produkt: `P1`, `P2`
- Sztuki wysłane per (pojazd, klient, produkt): `x[v,c,p]` — całkowite
- Liczba kursów per (pojazd, klient): `t[v,c]` — całkowite
- Maszyna włączona/wyłączona: `y[m]` — binarna

**Funkcja celu (maksymalizacja)** — zysk zdefiniowany powyżej.

**Ograniczenia**
- **Produkcja ≤ popyt** — produkcja każdego produktu nie może przekroczyć łącznego popytu rynkowego.
- **Wydajność maszyn** — godziny na każdej maszynie ≤ 300 h, bramkowane binarną włączenia maszyny. Każda sztuka obu produktów przechodzi przez obie maszyny.
- **Podaż** — łączna liczba wysłanych sztuk produktu ≤ jego produkcja.
- **Zaspokojenie popytu** — dostawa do każdego klienta równa jego popytowi, per produkt (równość).
- **Pojemność pojazdów** — sztuki przewiezione przez pojazd do klienta ≤ kursy × pojemność.
- **Agregacja kursów** — łączne kursy pojazdu = suma jego kursów per klient.

## Dane wejściowe

| Produkt | Cena [PLN] | Koszt prod. [PLN] |
|---|---|---|
| P1 | 900 | 500 |
| P2 | 650 | 400 |

| Klient | Popyt P1 | Popyt P2 | Odległość [km] |
|---|---|---|---|
| C1 | 200 | 200 | 40 |
| C2 | 300 | 300 | 110 |
| C3 | 300 | 375 | 240 |

| Maszyna | P1 [h/szt.] | P2 [h/szt.] | Limit [h] | Koszt stały [PLN] |
|---|---|---|---|---|
| M1 | 0,10 | 0,15 | 300 | 12 000 |
| M2 | 0,15 | 0,10 | 300 | 9 000 |

| Pojazd | Typ | Pojemność | Paliwo [PLN/km] | Koszt stały [PLN/kurs] |
|---|---|---|---|---|
| V1 | mały bus | 10 | 1,8 | 180 |
| V2 | średnia ciężarówka | 22 | 2,0 | 420 |
| V3 | duża ciężarówka | 34 | 2,1 | 530 |

**Praca:** stała 120 000 PLN + zmienna 85 PLN/szt.
**Koszt kursu** pojazdu do klienta = `odległość × paliwo + koszt stały`.

## Wyniki

| Składnik | Wartość [PLN] |
|---|---|
| Przychód | 1 288 750 |
| − Koszt produkcji | 750 000 |
| − Koszt stały maszyn | 21 000 |
| − Praca | 262 375 |
| − Transport | 41 625 |
| **= Zysk (funkcja celu)** | **213 750** |

- **Produkcja:** P1 = 800, P2 = 875 szt. — pełen popyt jest zaspokojony, bo każda sztuka jest opłacalna, a wydajność maszyn nie jest wąskim gardłem (M1 wykorzystuje 211,25 / 300 h, M2 207,5 / 300 h).
- **Flota:** V3 (duża ciężarówka) wykonuje **49 kursów** (12 → C1, 17 → C2, 20 → C3); V2 (średnia) wykonuje **1 kurs** → C2; V1 **nie jest używany**.
- Ten jeden kurs V2 przewozi dokładnie 22 sztuki do C2, które zostają po zapełnieniu dużej ciężarówki — jedyne miejsce, gdzie częściowy kurs średniej ciężarówki bije zarówno dodatkowy pełny kurs dużego auta, jak i kilka kursów małego busa.

## Kluczowe założenia

- **Koszt kursu = stały + zmienny.** Część stała (`Fixed cost pln/trip`) to bundel kosztów wyjazdu: kierowca, załadunek/obsługa, dyspozycja i zużycie na cykl — koszt per wyjazd, nie per okres czy per km. Rozłożony na większą pojemność obniża koszt na sztukę, co daje ekonomię skali napędzającą konsolidację ładunku w większe pojazdy i dobór rozmiaru auta do reszty ładunku (right-sizing).
- **Oba produkty przechodzą przez obie maszyny** — ograniczenia maszynowe modelują łączny czas obu etapów.
- **Pojazdy wożą produkty mieszane** — pojemność liczona w sztukach niezależnie od produktu.
- **Dostępność floty jest nieograniczona** — liczba kursów nie jest limitowana per pojazd; model dobiera wykorzystanie wyłącznie na podstawie kosztu.

## Uwagi metodologiczne

Model jest liniowy, więc rozwiązywany jest silnikiem **Simplex LP**, który Solver automatycznie owija w branch & bound, ponieważ liczby kursów i wielkości dostaw są zadeklarowane jako całkowite — Simplex LP rozwiązuje relaksacje ciągłe, a branch & bound wymusza całkowitość na wierzchu. (`Integer Optimality (%)` to sam w sobie parametr branch & bound i dla czystego LP w ogóle by nie istniał.)

**Kluczowe ustawienie: `Integer Optimality (%) = 0,00001`.**
Domyślna tolerancja całkowitoliczbowa Solvera Excela (1–5%) zatrzymuje się na *pierwszym* rozwiązaniu całkowitym w tym przedziale od oszacowania i melduje je jako „Optimal" — bez udowodnienia optymalności. W tym zadaniu domyślna wartość ukryła **lukę 494 PLN (0,23%)** i całkowicie wykluczyła pojazd V2 z rozwiązania, dając wynik wiarygodny, ale błędny (trzy kursy małego busa zamiast jednego kursu średniej ciężarówki). Zaostrzenie tolerancji do ~0 odzyskuje prawdziwe optimum.

Uwaga o wyborze silnika: wczesny przebieg używał **GRG Nonlinear**, który jest nieodpowiedni dla modelu liniowego i zbiegał do suboptymalnego optimum lokalnego. Przejście na Simplex LP jest konieczne dla globalnego optimum całkowitoliczbowego.

**Weryfikacja krzyżowa:** optimum zostało niezależnie odtworzone solverem **HiGHS** (open-source MILP) — identyczny wynik (213 750 PLN, jeden kurs V2), co potwierdza poprawność sformułowania w Excelu i globalną optymalność rozwiązania.

## Jak uruchomić

1. Otwórz `Optimization_Production_Transport.xlsx` w Excelu.
2. `Dane → Solver`. Komórka celu, komórki decyzyjne i ograniczenia są wstępnie skonfigurowane.
3. Silnik: **Simplex LP**. W `Opcje → All Methods` ustaw **Integer Optimality (%) = 0,00001**.
4. `Rozwiąż`. Funkcja celu powinna osiągnąć **213 750**.

---

*Autor: [LukaszB-DA](https://github.com/LukaszB-DA) · Projekt portfolio — optymalizacja produkcji i transportu (MILP) / operations research.*
