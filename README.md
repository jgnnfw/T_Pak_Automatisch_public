# (Halb-)Automatischer T-Pak Ausfüller

Dies ist ein Programm zum einfacheren Ausfüllen von T-Pak. Deine Garmin Aktivitäten werden heruntergeladen und automatisch auf T-Pak geladen. Insbesondere Intensitätsbereiche werden direkt aus den bei Garmin gespeicherten Bereichen übertragen.

## Anforderungen

- Laptop oder PC nötig
- Aktivitäten müssen mit Garmin aufgenommen sein
- Lücken in vorheriger T-Pak Ausfüllung können vom Programm nicht erkannt werden

## Programm ausführen

### Programm herunterladen

(Windows, python und git installiert; für andere Betriebssysteme sind die commands anzupassen)
```bash
cd <C:\Pfad\zu\lokalem\Speicherort\für\Programm>
git clone https://github.com/jgnnfw/T_Pak_Automatisch_public
cd T_Pak_Automatisch_public
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.text
rename User_Sensible_Information_TEMPLATE.ini User_Sensible_Information.ini
```

Öffne dann die Datei `User_Sensible_Information.ini` (Sollte jetzt so umbenennt worden sein) in einem Text editor und gebe deine Daten ein. Ändere nichts an der Struktur der Datei! Speichere die Datei danach. Im Folgenden ist eine Anleitung, um die T-Pak Daten zu finden.

### T-Pak User ID und Token finden

Dieser Schritt könnte etwas schwieriger sein. Er ist bereits in der `User_Sensible_Information.ini` Datei beschrieben, hier aber noch leicht ausführlicher:

1. In einem Browser (auf Firefox funktioniert es sicher) navigiere zu https://www.t-pak.ch/user-profile/profile und logge dich falls nötig ein.
2. Öffne die Entwickler-Tools meist mit `CTRL + SHIFT + I` oder `F12` oder in einem Menu ersichtlich. Öffne dort den Tab `Netzwerkanalyse`. Lade nun die T-Pak Seite neu.
3. Nun sollten ganz viele Meldungen erscheinen. Suche dort eine grüne Meldung heraus, die `profile` heisst, oder von `api/users/profile` stammt.
4. Finde unter den Anfrage-Kopfzeilen ganz unten den `X-Auth-Token`, ein Wirrwarr von Buchstaben und Zahlen. Kopiere diesen bei der ini-Datei in das Token Feld. Falls du das Programm länger brauchst, könnte es sein, dass du diesen Token erneut finden musst, da er sich aktualisieren kann.
5. Unter der Antwort, finde irgendwo `"id":"..."` bei `userData`, eine wahrscheinlich vierstellige Zahl. Du könntest etwas suchen/scrollen müssen. Das ist die Id, unter der dich T-Pak intern erkannt. Füge auch sie in der ini-Datei ein.

### Ausführen

```bash
cd <C:\Pfad\zu\lokalem\Speicherort\für\Programm>
cd T_Pak_Automatisch_public
.venv\Scripts\python.exe web_app.py
```

Falls alles funktioniert, sollten einige Zeilen in der Konsole auftauchen und nach etwa 10 Sekunden ein Fenster im Browser erscheinen, das etwa weitere 5 Sekunden für das Laden braucht.

## Eintragen

Das Eintragen von Aktivitäten sollte relativ selbsterklärend sein. Das Programm lädt nur Aktivitäten, die nach dem Datum der letzten im T-Pak eingetragenen Aktivität herunter.

- Mit dem Button `Alle Aktivitäten anzeigen` können alle Aktivitätstypen angezeigt werden, nicht nur vorgeschlagene.
- Mit dem `Streching`-Button werden 5 Minuten Stretching **hinzugefügt**.
- Wird der `M(anuell)`-Button angewählt, wird die Aktivität **nicht** hochgeladen. Die Aktivität kann somit manuell auf T-Pak hochgeladen werden.
- Mit dem `Alle hochladen`-Button werden alle Aktivitäten hochgeladen (ausser solche mit `M`-Button). Konnten nicht alle hochgeladen werden, sollte der Anmeldescreen erneut erscheinen.

Bei allen Aktivitäten, bei denen `OL Wettkampf` ausgewählt wurde, sucht das Programm nach Resultaten auf der `o-l.ch` Website. 

## Bugs/Probleme/FAQ

- Beim ersten Mal hochladen mit diesem Programm sollten keine Lücken mehr in der Nachtragung des T-Pak vorhanden sein. Falls diese existieren, entweder manuell nachtragen oder die Aktivitäten nach der Lücke löschen, damit das Programm alle erneut hochladen kann. Eine Option mit Startdatum wurde (noch) nicht entwickelt.
- Die Software wurde für Laptops/PCs entwickelt und sollte nicht auf kleineren Bildschirmen verwendet werden.
- Es wurde absichtlich kein Kommentarfeld oder weitere Felder hinzugefügt, die manuell übertragen werden müssen. Wenn nötig, bitte den `M`-Button klicken und die Aktivität manuell auf T-Pak hochladen.

Bugs bitte via github Issue melden. Pull-request und Forks sind willkommen.

## KI Verwendung

Grosse Teile dieses Programms basieren auf Antworten von Claude.
