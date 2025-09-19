# Obsługa potencjometrów k1 i k2 w EuroPi

Źródło: [EuroPi Documentation](https://allen-synthesis.github.io/EuroPi/api_reference.html#knobs)

---

## Podstawy

- **k1** i **k2** to analogowe potencjometry (gałki) na panelu EuroPi.
- Służą do sterowania parametrami, wybierania pozycji menu, zmian ustawień w czasie rzeczywistym.

---

## Odczyt wartości

### `.value()` lub `.percent()`
- Zwraca wartość zmiennoprzecinkową **0.0 – 1.0**
- Przykład:
  ```python
  v = k1.value()      # np. 0.42
  p = k2.percent()    # np. 0.87
  ```

### `.range(max_value)` lub `.read_position(max_value)`
- Zwraca wartość całkowitą **0 ... max_value-1**
- Przeskalowuje położenie potencjometru do zadanej liczby kroków.
- Przykład:
  ```python
  idx = k1.range(10)            # 0..9
  pos = k2.read_position(8)     # 0..7
  ```

---

## Praktyczne zastosowania

- **Płynna regulacja parametru**:
  ```python
  cutoff = int(k1.value() * 10000)  # zakres 0..9999
  ```

- **Wybór pozycji menu**:
  ```python
  menu_idx = k1.range(4)            # przełącza między 4 pozycjami
  ```

- **Precyzyjna, dyskretna zmiana**:
  ```python
  octave = k2.range(8)              # wybiera oktawę 0..7
  ```

---

## Podsumowanie

- Do prostych menu i wyborów — **`.range(n)`/`.read_position(n)`**
- Do płynnych parametrów — **`.value()`/`.percent()`**

---

### Fragment z oficjalnej dokumentacji

> **k1** and **k2** are the two panel potentiometers.  
> The `.value()` method returns a value between 0.0 and 1.0.  
> The `.range(n)` method returns a value between 0 and n-1, mapping the knob position to discrete steps.

Źródło: [EuroPi Documentation: API Reference](https://allen-synthesis.github.io/EuroPi/api_reference.html#knobs)