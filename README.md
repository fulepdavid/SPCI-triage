## COMEN eszköz

- A monitort DHCP-re állítottuk, és megkapta a 10.64.5.217 IP címet
- Eszköz IP címének beállítása: Menu -> System -> Maintain -> Network Setup -> LAN1 IP
- Céleszközhöz kapcsolódó beállítások: Menu -> System -> Maintain -> Network Setup -> HL7 Setup
- Céleszköz fixen beállítva: a fejlesztői PC-re, 5000-es port.
- Jelszó 5188

### Egyéb átkonfigurált beállítások

- Periodikus vérnyomás mérés kikapcsolása : Főoldalon NIBP box -> Interval: Manual
- Alarmok kikapcsolása: Menu -> Device -> Volume

### Megoldandó probléma

- **Accept new patients ablak ne ugrojon fel: A kódban benne van, hogy kattintsunk az ezt eltütnető helyre, de a valóságban mégsem tűnik el. Először azonban kb. egy órát kell várni, hogy előjöjjön így a megoldása igencsak lassú.**

## Egérszimulátor

- Az egérszimulátor DHCP-n van, a kapott cím kiderítése\_
    - MAC: 02:08:dc:77:9b:2d
    - Ugyanazon az alhálózaton futó linuxon: (Kalmár Ádám gépe)
        - sudo nmap -sn 10.64.0.0/21
        - ip neigh | grep -i "02:08:dc:77:9b:2d"
    - Ezután az adott IP címen elérhető böngészőből, 80-as port: admin/mousesym
- Vérnyomásmérés elindítása a szimulátor segítségével: `python mousesym/tools/mousesym_client.py --host 10.64.4.235 --key mousesym "MOVE 0 0" "CLICK 220 75"`

## Fájl struktúra

- config.py: Beállítások: időkorlátok, a kiosk, a mérőgép és a HL7-szerver címei, a mérőgép kulcsa környezeti változóból, és a fájl-útvonalak kezelése.

- content.py: A klinikai tartalom: a menük, a kérdőívek, a személyes adatok lépése, a vérnyomásmérés lépése és a záró képernyő szövege.

- device.py: A vérnyomásmérő indítása: az egérparancsok elküldése a mérőgépnek, majd a HL7-hallgató eredményére várakozás.

- hl7_codes.py: A HL7/MDC kódtáblák és mértékegységek, amelyeket a parser használ.

- hl7_listener.py: A beépített HL7-szerver: a monitor üzeneteinek fogadása, nyugtázása (ACK), a mérési időablak és az SpO₂-értékek ideiglenes tárolása.

- hl7_parser.py: Az ORU^R01 üzenetek feldolgozása, az értékek kinyerése és ellenőrzése.

- layout.py: A fejléc, a lábléc (navigáció, nyelvváltó, lépésszámláló, Tovább gomb) és a kérdőív keretének felépítése.

- questions.py: A kérdéstípusok megjelenítése, a válaszok kezelése, a mérés eredményének lekérdezése, a bp_answer és a BP_FIELDS szerkezet, valamint a dupla kattintás elleni védelem.

- report.py: A PDF elkészítése magyarul, a TAJ-szám és a dátum formázása, és az értékek soronkénti megjelenítése.

- search.py: A keresőképernyő: kulcsszavas keresés a menükben, a billentyűzettel.

- strings.py: A felület kétnyelvű szövegei (nem klinikai tartalom).

- theme.py: A színek, a betűtípusok és a CustomTkinter megjelenési beállításai.

- **triage.py: A belépési pont és az App osztály: az ablak, a navigáció, az időkorlát, a záró képernyő, a mentési hibakezelés és az indítás.**

- validation.py: A beviteli szabályok (TAJ hossza és számjegyei, dátum formátuma), amelyek a content.py-ban adatként vannak megadva.

- widgets.py: A virtuális billentyűzet.

- hl7_original mappa: Úgy kaptuk a COMEN eszköz mellett, amely az érkező adatokat hivatott egy webes felületen megjeleníteni. Ennek egy része került át a hl7 fájlokba.

- mousesym mappa: Egy egérként funkciónáló eszköz a COMEN mellett, ami arra jó, hogy a képernyőn megadott helyre tudjuk kattintani (elindíthassuk a mérést)

## Projekt lokális futtatása

- Virtuális környezet létrehozása
- Virtuális környezet aktiválása
- python triage.py

## Későbbi tennivalók Claude javaslatai alapján

- PDFs are still unencrypted and never deleted. Answers stay in memory until the next questionnaire or the timeout. The debug_rejected.txt dump can contain patient fields, so it must be removed before use.
- Stable IDs and canonical values for sending: Choice answers and question labels are still multilingual dicts. Only the BP data dict and the TAJ id are canonical. send_data() is still a stub.
