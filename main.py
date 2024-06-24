import curses
import random
import time
import socket
import sys
import subprocess
from multiprocessing import Process, Manager, Lock
import os
import pygame
from datetime import datetime

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# Load sound effects
sound1 = pygame.mixer.Sound("sound1.wav")
countdown_sound = pygame.mixer.Sound("countdown.wav")
achievement_sound = pygame.mixer.Sound("achievement.wav")
winning_sound = pygame.mixer.Sound("winning.wav")

CELL_WIDTH = 20  # Fixed width for each cell


def read_words_from_file(file_path):  # Definiert eine Funktion, die eine Datei liest und die Wörter zurückgibt.
    try:
        with open(file_path, 'r') as file:  # Öffnet die Datei im Lesemodus.
            words = file.read().splitlines()  # Liest den gesamten Inhalt der Datei und trennt ihn in Zeilen.
        return words  # Gibt die Liste der Wörter zurück.
    except FileNotFoundError:  # Fängt die Ausnahme ab, falls die Datei nicht gefunden wird.
        print(f"File {file_path} not found.")  # Gibt eine Fehlermeldung aus, dass die Datei nicht gefunden wurde.
        sys.exit(1)  # Beendet das Programm mit einem Fehlercode.



def create_bingo_card(words, size):  # Definiert eine Funktion, die eine Bingo-Karte erstellt.
    unique_words = random.sample(words, size * size)  # Wählt zufällig eine bestimmte Anzahl von einzigartigen Wörtern aus der Liste aus.
    return [unique_words[i * size:(i + 1) * size] for i in range(size)]  # Teilt die ausgewählten Wörter in eine 2D-Liste auf, um die Bingo-Karte zu erstellen.


def display_bingo_card(window, card, start_y, start_x, size, cursor_y=None, cursor_x=None):
    for i in range(size):  # Schleife durch jede Zeile der Bingo-Karte.
        for j in range(size):  # Schleife durch jede Spalte der Bingo-Karte.
            word = card[i][j]  # Hole das Wort an der aktuellen Position.
            if len(word) > CELL_WIDTH - 1:
                word = word[:CELL_WIDTH - 2] + '…'  # Kürze das Wort und füge ein Auslassungszeichen hinzu, wenn es zu lang ist.
            if cursor_y == i and cursor_x == j:
                window.addstr(start_y + i * 2, start_x + j * CELL_WIDTH, f"| {word:<{CELL_WIDTH - 1}}",
                              curses.color_pair(3))  # Hebe das Wort hervor, wenn es sich an der Cursorposition befindet.
            else:
                window.addstr(start_y + i * 2, start_x + j * CELL_WIDTH, f"| {word:<{CELL_WIDTH - 1}}",
                              curses.color_pair(2))  # Zeichne das Wort normal, wenn es sich nicht an der Cursorposition befindet.
        window.addstr(start_y + i * 2, start_x + size * CELL_WIDTH, "|")  # Zeichne die rechte Begrenzung der aktuellen Zeile.
    window.addstr(start_y + size * 2, start_x, "+" + "-" * (CELL_WIDTH * size + size - 1) + "+", curses.color_pair(5))  # Zeichne die untere Begrenzung der Bingo-Karte.
    window.refresh()  # Aktualisiere das Fenster, um die Änderungen anzuzeigen.



def check_word_on_card(card, word):  # Definiert eine Funktion, die überprüft, ob ein bestimmtes Wort auf der Bingo-Karte vorhanden ist.
    for row in card:  # Schleife durch jede Zeile der Bingo-Karte.
        if word in row:  # Überprüft, ob das Wort in der aktuellen Zeile enthalten ist.
            return True  # Gibt True zurück, wenn das Wort gefunden wurde.
    return False  # Gibt False zurück, wenn das Wort in keiner Zeile gefunden wurde.


def mark_word_on_card(card, y, x):
    # Markiert das Wort an den Koordinaten (y, x) auf der Bingo-Karte mit einem "X".
    card[y][x] = "X"


def check_winner(card, size):  # Definiert eine Funktion, die überprüft, ob es einen Gewinner auf der Bingo-Karte gibt.
    # Überprüft die Hauptdiagonale und die Gegendiagonale auf ein "X" in jeder Zelle.
    if all(card[i][i] == "X" for i in range(size)) or all(card[i][size - 1 - i] == "X" for i in range(size)):
        return True  # Gibt True zurück, wenn eine der beiden Diagonalen vollständig mit "X" gefüllt ist.
    for i in range(size):
        # Überprüft jede Zeile und jede Spalte auf ein "X" in jeder Zelle.
        if all(card[i][j] == "X" for j in range(size)) or all(card[j][i] == "X" for j in range(size)):
            return True  # Gibt True zurück, wenn eine Zeile oder Spalte vollständig mit "X" gefüllt ist.
    return False  # Gibt False zurück, wenn keine vollständige Zeile, Spalte oder Diagonale mit "X" gefüllt ist.



def get_input(window, prompt, y=0, x=0):  # Definiert eine Funktion, die eine Eingabe vom Benutzer anfordert und zurückgibt.
    curses.echo()  # Aktiviert die Echo-Funktion, sodass die Eingabe des Benutzers sichtbar ist.
    window.addstr(y, x, prompt, curses.color_pair(4))  # Fügt den Eingabe-Prompt mit der Farbkombination 4 (grüner Text) an die angegebene Position hinzu.
    window.refresh()  # Aktualisiert das Fenster, um die Änderungen anzuzeigen.
    input_str = window.getstr(y, x + len(prompt)).decode('utf-8')  # Liest die Eingabe des Benutzers und dekodiert sie als UTF-8-String.
    curses.noecho()  # Deaktiviert die Echo-Funktion, sodass die Eingabe des Benutzers nicht mehr sichtbar ist.
    window.clear()  # Löscht den Inhalt des Fensters.
    return input_str  # Gibt den eingegebenen String zurück.


def log_event(log_file, event):  # Definiert eine Funktion, die ein Ereignis in eine Logdatei schreibt.
    with open(log_file, 'a') as f:  # Öffnet die Logdatei im Anhängemodus.
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")  # Erstellt einen Zeitstempel im Format Jahr-Monat-Tag-Stunde-Minute-Sekunde.
        f.write(f"{timestamp} {event}\n")  # Schreibt den Zeitstempel und das Ereignis in die Logdatei, gefolgt von einem Zeilenumbruch.



def player_process(player_id, num_players, card_size, words, player_name, server_ip, server_port):
    # Erstellen eines Logdateinamens basierend auf dem aktuellen Datum und der Uhrzeit.
    log_file = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-bingo-Spieler{player_id + 1}.txt"

    def main(stdscr):
        # Initialisiert Farben für curses.
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight-Farbe
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Grüne Textfarbe
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

        # Erstellt die Bingo-Karte und bereitet das Fenster vor.
        card = create_bingo_card(words, card_size)
        window = stdscr
        window.clear()
        window.addstr(0, 0, f"{player_name}'s Karte:", curses.color_pair(1))
        display_bingo_card(window, card, 2, 0, card_size)

        # Loggt den Spielstart und die Kartengröße.
        log_event(log_file, "Start des Spiels")
        log_event(log_file, f"Größe des Spielfelds: ({card_size}x{card_size})")

        # Verbindet sich mit dem Server.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((server_ip, server_port))
                s.setblocking(False)
            except ConnectionRefusedError:
                print(f"Unable to connect to server at {server_ip}:{server_port}")
                sys.exit(1)

            cursor_y, cursor_x = 0, 0
            window.timeout(100)  # Setzt das Timeout auf 100 Millisekunden.

            while True:
                try:
                    # Empfangt das gezogene Wort vom Server.
                    drawn_word = s.recv(1024).decode('utf-8')
                    if drawn_word == 'WIN':
                        # Beendet das Spiel, wenn ein Spieler gewonnen hat.
                        window.addstr(card_size * 2 + 5, 0, f"{player_name} hat gewonnen!", curses.color_pair(1))
                        window.refresh()
                        pygame.mixer.Sound.play(winning_sound)
                        log_event(log_file, "Sieg")
                        time.sleep(300)  # Wartet 5 Minuten.
                        log_event(log_file, "Ende des Spiels")
                        return
                    # Aktualisiert die Anzeige.
                    window.clear()
                    window.addstr(0, 0, f"{player_name}'s Karte: ", curses.color_pair(4))
                    display_bingo_card(window, card, 2, 0, card_size, cursor_y, cursor_x)
                    question_y = 2 + card_size * 2 + 1
                    window.addstr(question_y, 0, f"Haben Sie das Wort {drawn_word} auf der Karte?", curses.color_pair(1))
                except BlockingIOError:
                    pass

                # Verarbeitet Benutzereingaben.
                key = window.getch()
                if key == curses.KEY_UP and cursor_y > 0:
                    cursor_y -= 1
                elif key == curses.KEY_DOWN and cursor_y < card_size - 1:
                    cursor_y += 1
                elif key == curses.KEY_LEFT and cursor_x > 0:
                    cursor_x -= 1
                elif key == curses.KEY_RIGHT and cursor_x < card_size - 1:
                    cursor_x += 1
                elif key == ord('\n'):
                    if check_word_on_card(card, drawn_word) and card[cursor_y][cursor_x] == drawn_word:
                        mark_word_on_card(card, cursor_y, cursor_x)
                        pygame.mixer.Sound.play(achievement_sound)
                        log_event(log_file, f"{drawn_word} ({cursor_x},{cursor_y})")
                        if check_winner(card, card_size):
                            s.sendall(b'WIN')
                            pygame.mixer.Sound.play(winning_sound)
                            window.addstr(card_size * 2 + 5, 0, f"{player_name} hat gewonnen!", curses.color_pair(1))
                            window.refresh()
                            log_event(log_file, "Sieg")
                            time.sleep(300)  # Wartet 5 Minuten.
                            log_event(log_file, "Ende des Spiels")
                            return
                display_bingo_card(window, card, 2, 0, card_size, cursor_y, cursor_x)

    curses.wrapper(main)  # Startet die curses-Hauptschleife.


def handle_player_connection(conn, addr, shared_state, num_players, lock, player_names):
    # Bestimmt die Spieler-ID basierend auf der Adresse des Spielers und der Anzahl der Spieler.
    player_id = addr[1] % num_players

    while True:
        with lock:
            drawn_word = shared_state['drawn_word']  # Holt das gezogene Wort aus dem gemeinsam genutzten Zustand.

        conn.sendall(drawn_word.encode('utf-8'))  # Sendet das gezogene Wort an den Spieler.

        try:
            player_response = conn.recv(1024).decode('utf-8')  # Empfängt die Antwort des Spielers.
        except ConnectionResetError:
            break  # Beendet die Schleife, wenn die Verbindung zurückgesetzt wurde.

        if not player_response:
            break  # Beendet die Schleife, wenn keine Spielerantwort empfangen wurde.

        with lock:
            if player_response == 'WIN':
                shared_state['winner'] = player_id + 1  # Setzt den Gewinner im gemeinsam genutzten Zustand.
                break  # Beendet die Schleife, wenn ein Spieler gewonnen hat.


def master_process(num_players, words, shared_state, server_ip, server_port, lock, player_names):
    # Erstellt einen Dateinamen für das Log basierend auf dem aktuellen Datum und der Uhrzeit.
    log_file = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-bingo-Master.txt"

    def main(stdscr):
        # Initialisiert Farben für curses.
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Grüne Textfarbe
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Weißer Text auf blauem Hintergrund
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLUE)     # Roter Text auf blauem Hintergrund

        window = stdscr
        window.clear()
        window.addstr(0, 0, "Master Terminal: Buzzword Bingo Game")  # Zeigt den Titel des Spiels an.

        log_event(log_file, "Start des Spiels")  # Schreibt den Spielstart in das Logfile.

        max_y, max_x = stdscr.getmaxyx()
        timer_window = curses.newwin(3, 30, 0, max_x - 30)  # Erstellt ein neues Fenster für den Timer.

        round_count = 0  # Zählt die Runden.
        drawn_words = set()  # Hält die bereits gezogenen Wörter fest.

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((server_ip, server_port))  # Bindet den Socket an die angegebene IP-Adresse und Portnummer.
                s.listen(num_players)  # Setzt den Socket in den Listen-Modus für die Anzahl der Spieler.
                s.setblocking(False)
                connections = []

                # Akzeptiert Verbindungen von allen Spielern.
                while len(connections) < num_players:
                    try:
                        conn, addr = s.accept()
                        connections.append(conn)
                        # Startet einen neuen Prozess für die Behandlung der Spieler-Verbindung.
                        Process(target=handle_player_connection, args=(conn, addr, shared_state, num_players, lock, player_names)).start()
                    except BlockingIOError:
                        pass

                while True:
                    with lock:
                        if shared_state['winner']:
                            break  # Beendet die Schleife, wenn ein Gewinner festgestellt wurde.

                    round_count += 1  # Erhöht die Rundenanzahl.
                    drawn_word = random.choice(words)  # Wählt ein zufälliges Wort aus der Wortliste.
                    while drawn_word in drawn_words:
                        drawn_word = random.choice(words)  # Wählt erneut, falls das Wort bereits gezogen wurde.
                    drawn_words.add(drawn_word)  # Fügt das gezogene Wort der Menge der gezogenen Wörter hinzu.

                    with lock:
                        shared_state['drawn_word'] = drawn_word  # Aktualisiert den gezogenen Wort im gemeinsamen Zustand.

                    window.clear()
                    window.addstr(0, 0, f"Runde {round_count}: Das gezogene Wort lautet: {drawn_word}",
                                  curses.color_pair(1))  # Zeigt das gezogene Wort und die Runde an.
                    log_event(log_file, f"Runde {round_count}: Das gezogene Wort lautet: {drawn_word}")  # Schreibt das Ereignis in das Logfile.

                    window.refresh()

                    # Sendet das gezogene Wort an alle verbundenen Spieler.
                    for conn in connections:
                        conn.sendall(drawn_word.encode('utf-8'))

                    start_time = time.time()
                    countdown_seconds = 30
                    play_countdown_sound = True

                    while True:
                        remaining_time = countdown_seconds - int(time.time() - start_time)
                        if remaining_time < 0:
                            break

                        for color_pair in [2, 3]:
                            timer_window.clear()
                            timer_window.addstr(0, 7, f"Zeit übrig: {remaining_time} Sekunden",
                                                curses.color_pair(color_pair))
                            timer_window.refresh()
                            time.sleep(0.5)

                        if remaining_time <= 10 and play_countdown_sound:
                            pygame.mixer.Sound.play(countdown_sound)
                            play_countdown_sound = False

                        with lock:
                            if shared_state['winner']:
                                break

                    with lock:
                        if shared_state['winner']:
                            break

                    end_time = time.time() + 2
                    while time.time() < end_time:
                        time.sleep(0.1)

                    time.sleep(2)

                winner_id = shared_state['winner']
                for conn in connections:
                    conn.sendall(b'WIN')

                window.addstr(4, 0, f"{player_names[winner_id - 1]} hat gewonnen!", curses.color_pair(1))
                window.refresh()
                log_event(log_file, f"{player_names[winner_id - 1]} hat gewonnen!")
                log_event(log_file, "Ende des Spiels")
                time.sleep(300)  # Wartet 5 Minuten, bevor das Programm beendet wird.

        except KeyboardInterrupt:
            window.addstr(4, 0, "Das Spiel wurde vom Benutzer abgebrochen.", curses.color_pair(1))
            window.refresh()
            log_event(log_file, "Abbruch")
            time.sleep(2)

    curses.wrapper(main)  # Startet die curses-Hauptschleife.


def main():
    # Eingabe der Anzahl der Spieler
    num_players_str = input("Bitte geben Sie die Anzahl der Spieler ein: ")
    num_players = int(num_players_str)

    # Eingabe der Größe der Bingo-Karten
    card_size_str = input("Bitte geben Sie die Größe der Bingo-Karten (z.B. 5 für 5x5) ein: ")
    card_size = int(card_size_str)

    # Eingabe der Namen der Spieler
    player_names = [input(f"Name des Spielers {i + 1}: ") for i in range(num_players)]

    # Liest die Wörter aus der Datei "words.txt"
    words = read_words_from_file("words.txt")

    # Konfiguration für den Server
    server_ip = '127.0.0.1'
    server_port = 65432

    # Initialisiert den gemeinsamen Zustand und den Lock für die Synchronisation
    manager = Manager()
    shared_state = manager.dict()
    shared_state['drawn_word'] = ''
    shared_state['winner'] = 0
    lock = Lock()

    # Initialisiert die Markierungen der Spieler in shared_state
    for i in range(num_players):
        shared_state[f"player_{i}_marked"] = False

    players = []

    # Startet den Master-Prozess in einem separaten Prozess
    master_process_instance = Process(target=master_process, args=(
        num_players, words, shared_state, server_ip, server_port, lock, player_names))
    master_process_instance.start()

    # Startet die Spieler-Prozesse für jeden Spieler
    for i in range(num_players):
        # Bestimmt den Befehl je nach Betriebssystem für das Starten eines neuen Terminals oder einer neuen CMD-Sitzung
        if os.name == 'nt':
            player_terminal_command = f'start cmd /k python {sys.argv[0]} {i} {num_players} {card_size} "{player_names[i]}" {server_ip} {server_port}'
        else:
            player_terminal_command = f'x-terminal-emulator -e "python3 {sys.argv[0]} {i} {num_players} {card_size} {player_names[i]} {server_ip} {server_port}"'

        # Startet den Spieler-Prozess mit dem entsprechenden Befehl
        player_process_instance = subprocess.Popen(player_terminal_command, shell=True)
        players.append(player_process_instance)

    # Wartet auf das Ende des Master-Prozesses
    master_process_instance.join()

    # Beendet alle Spieler-Prozesse
    for player in players:
        player.terminate()


if __name__ == "__main__":
    # Wenn das Skript direkt ausgeführt wird, wird die `main()` Funktion aufgerufen
    if len(sys.argv) > 1:
        # Wenn Argumente übergeben werden, wird angenommen, dass ein einzelner Spielerprozess gestartet wird
        player_id = int(sys.argv[1])
        num_players = int(sys.argv[2])
        card_size = int(sys.argv[3])
        player_name = sys.argv[4]
        server_ip = sys.argv[5]
        server_port = int(sys.argv[6])
        words = read_words_from_file("words.txt")
        player_process(player_id, num_players, card_size, words, player_name, server_ip, server_port)
    else:
        # Ansonsten wird die `main()` Funktion aufgerufen, um das Spiel für mehrere Spieler zu starten
        main()
