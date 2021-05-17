# Algorytm

Algorytm szyfrowania/deszyfrowania treści z pliku tekstowego:
1. Podziel wiadomość w pliku wejściowym `in` na części `part` o równej długości `n` znaków (za wyjątkiem ostatniej części, która może mieć dowolną długość `k <= n`).
2. Każdy znak w danej części zapisz w formie jej reprezentacji ASCII (np. `a -> 97`).
3. Wybierz dowolny klucz szyfrujący, oblicz funkcję skrótu `md5` dla jego reprezentacji bitowej i zapisz otrzymaną reprezentację szesnastkową `hex`.
4. Dla każdego indeksu `i = 1 : n` dokonaj operacji `part[i] ^ hex[i mod 32]`, gdzie `part[i]`, `hex[i]` to reprezentacje bitowe `i`-tego znaku odpowiednio tekstów `part` i `hex`, a `^` to operacja alternatywy wykluczającej XOR.
5. Punkt 4. powtarzaj `K` razy za każdym razem zaczynając szyfrowanie o jeden znak później, przechodząc cyklicznie przez cały tekst, tj. dla `j`-tej pętli należy podstawić `part[i] = part[i+j mod |part|]`, gdzie `|part|` to długość tekstu `part`.
6. Połącz zaszyfrowane części w jedną całość w tej samej kolejności w jakiej zostały podzielone i zapisz do pliku wynikowego `out`.

Proces deszyfrowania ze względu na symetrię operacji XOR jest identyczny z procesem szyfrowania, przy czym za plik wejściowy przyjmuje się plik z szyfrogramem `out`.


Ze względu na podział tekstu jawnego na wiele części, możliwe jest zrównoleglenie procesu szyfrowania pliku.
Konieczne jest również wprowadzenie mechanizmów synchronizacyjnych, aby umożliwić połączenie kolejnych części otrzymanego szyfrogramu w odpowiedniej kolejności.

# Wersja równoległa

`parallel.py` - plik z wersją zrównolegloną algorytmu

W wersji równoległej algorytmu skorzystano z mechanizmu kolejkowania, aby rozdzielać zadania pomiędzy procesy.
Wykorzystano dwie kolejki:
- `input_queue` do przechowywania kolejnych części `part` wydzielonych z pliku `in`,
- `output_queue` do przechowywania kolejnych częśći szyfrogramu, które powinny zostać zapisane do pliku `out`

W programie działają równolegle następujące procesy:
- 1 proces `reader_proc` służący do czytania z pliku wejściowego `in` i zapisywania kolejnych części do kolejki `input_queue`
- 1 proces `writer_proc` służący do zapisywania do pliku wyjściowego `out` danych otrzymanych z kolejki `output_queue`
- `n` procesów `worker` wykonujących algorytm szyfrowania pobierając dane z kolejki `input_queue` i zapisując je do kolejki `output_queue`

# Wersja rozproszona

`distributed.py` - plik z wersją rozproszoną algorytmu; część serwerowa,
`client.py` - klient wykonujący obliczenia rozproszone

W wersji rozproszonej algorytmu wykorzystano dodatkowo mechanizm gniazd (socketów) do komunikacji pomiędzy procesami mogącymi działać na różnych komputerach w sieci.


W wersji rozproszonej niezależnie uruchamiane muszą zostać dwa programy:
- `distributed.py` pełni rolę programu zarządzającego, który odpowiada za odczytanie tekstu jawnego z pliku wejściowego `in`, rozdział zadań pomiędzy instancje obliczeniowe, a na koniec połączenie otrzymanych wyników i zapisanie ich do pliku `out`,
- instancje `client.py` pełnią rolę klastrów obliczeniowych, które otrzymują dane od programu zarządzającego, dokonują obliczeń szyfrujących i odsyłają otrzymane wyniki.

W ramach programu zarządzającego `distributed.py` działają, podobnie jak w wersji równoległej, procesy `reader_proc` oraz `writer_proc`, jednak zamiast wielu procesów `worker` działa jeden główny proces programu, który, wykorzystując wielowątkowość, niezależnie komunikuje się z każdym z procesów klienckich, aby przekazać im dane z kolejki `input_queue` i zapisać otrzymane przetworzone dane do kolejki `output_queue`.

W ramach instancji `client.py` działa `n` procesów każdy wykonujący własne obliczenia i korzystający z oddzielnego socketu do komunikacji z programem zarządzającym.
# Pliki pomocnicze

`file_generator.py` - skrypt umożliwiający tworzenie plików o określonej wielkości umieszczając w nich losowe znaki

Przykładowo komenda `python3 file_generator.py test.txt 2` utworzy plik `test.txt` o wielkości 2 MB zawierający zestaw losowych znaków [a-zA-Z0-9].