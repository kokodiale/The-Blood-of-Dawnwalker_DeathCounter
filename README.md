# Dawnwalker Death Overlay

Gotowy licznik zgonów do OBS dla **The Blood of Dawnwalker**.

Projekt składa się z dwóch części:

1. **UE4SS mod** wykrywa śmierć gracza i zapisuje licznik do `counter.txt`.
2. **Lokalny serwer + HTML/CSS/JS** pokazuje licznik jako stylizowany overlay w OBS.

> Overlay jest autorskim projektem inspirowanym mrocznym, gotyckim klimatem gry. Repozytorium nie zawiera oficjalnych assetów The Blood of Dawnwalker.

## Struktura repozytorium

```text
Dawnwalker-Death-Overlay/
├─ README.md
├─ start_overlay.bat
├─ server.py
├─ config.json
├─ data/
│  └─ counter.json
├─ overlay/
│  ├─ index.html
│  ├─ styles.css
│  ├─ app.js
│  └─ assets/
│     └─ blood-sigil.svg
└─ ue4ss/
   └─ DawnwalkerDeathCounter/
      ├─ enabled.txt
      └─ Scripts/
         └─ main.lua
```

## 1. Wymagania

- Windows
- OBS Studio
- Python 3
- działające UE4SS przeznaczone dla aktualnego buildu The Blood of Dawnwalker

## 2. Instalacja moda UE4SS

Najpierw upewnij się, że UE4SS działa w grze.

Skopiuj folder:

```text
ue4ss/DawnwalkerDeathCounter
```

do:

```text
<Steam Library>\steamapps\common\The Blood of Dawnwalker\Dawnwalker\Binaries\Win64\ue4ss\Mods\
```

Finalna ścieżka powinna wyglądać tak:

```text
...\ue4ss\Mods\DawnwalkerDeathCounter\Scripts\main.lua
```

Po uruchomieniu gry mod utworzy:

```text
...\ue4ss\Mods\DawnwalkerDeathCounter\counter.txt
```

## 3. Uruchomienie overlayu

Kliknij dwukrotnie:

```text
start_overlay.bat
```

Serwer automatycznie spróbuje znaleźć Steam oraz plik `counter.txt`.

Gdy wszystko działa, zobaczysz w konsoli adres:

```text
http://127.0.0.1:8765
```

Nie zamykaj tego okna podczas streama.

### Jeśli autodetekcja nie znajdzie gry

Otwórz `config.json` i wpisz pełną ścieżkę do `counter.txt`:

```json
{
  "port": 8765,
  "counter_file": "D:/SteamLibrary/steamapps/common/The Blood of Dawnwalker/Dawnwalker/Binaries/Win64/ue4ss/Mods/DawnwalkerDeathCounter/counter.txt",
  "refresh_ms": 250
}
```

W JSON najbezpieczniej używać `/` zamiast `\\` w ścieżkach Windows.

## 4. Dodanie do OBS

W OBS wybierz:

```text
Źródła → + → Przeglądarka
```

Ustaw:

```text
URL:       http://127.0.0.1:8765
Szerokość: 520
Wysokość: 220
FPS:       30
```

Nie zaznaczaj `Local file`.

Tło overlayu jest przezroczyste.

## 5. Test bez umierania

UE4SS udostępnia komendę:

```text
deathcounter_add
```

która dodaje jeden zgon.

Reset licznika:

```text
deathcounter_reset
```

Po zmianie `counter.txt` overlay powinien zaktualizować się w maksymalnie około 0,25 s.

## 6. Tryb demonstracyjny

Jeśli serwer nie znajdzie `counter.txt`, korzysta z wartości z:

```text
data/counter.json
```

Możesz zmienić np.:

```json
{"deaths": 13}
```

i odświeżyć overlay, aby zobaczyć wygląd bez uruchamiania gry.

## 7. Zmiana napisu i stylu

Najważniejsze opcje są na początku `overlay/styles.css`:

```css
:root {
  --panel-width: 470px;
  --blood: #8d1f2a;
  --blood-bright: #c14a4d;
  --bone: #d8d0c2;
}
```

Teksty zmienisz w `overlay/index.html`:

```html
<div class="eyebrow">THE BLOOD REMEMBERS</div>
<div class="title">DEATH TOLL</div>
```

## 8. GitHub

Możesz wrzucić cały folder jako zwykłe repozytorium GitHub.

**Nie włączaj GitHub Pages jako źródła w OBS dla licznika na żywo.** Strona działająca na `github.io` nie ma dostępu do lokalnego `counter.txt`. Do OBS używaj lokalnego adresu `http://127.0.0.1:8765`.

## Bezpieczeństwo

Serwer nasłuchuje wyłącznie na `127.0.0.1`, więc nie wystawia licznika do sieci lokalnej ani Internetu.
