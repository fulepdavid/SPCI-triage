# COMEN NC6 MONITOR

Működő, függőségmentes Python alkalmazás: MLLP/TCP fogadó, ORU megfigyelésfeldolgozás, HL7 ACK, webes felület, REST API, JSONL előzmény és CSV export. A kód a megadott NC6 interfészfeltételekre épül. A fejlesztés során a 192.168.0.118 címről tényleges NC_Monitor / KC574337852G HL7 forgalom érkezett: R01 hullámforma és R40 eseményüzenetek. A teljes számszerű vitális adatátvitel még nincs valódi készülékkel validálva; a szimulátor szintetikus HL7 üzenetet küld.

## 1. Telepítés

Telepíts Python 3-at (új telepítéshez támogatott, friss Python verziót használj). A kód minimuma Python 3.7; Windows és Linux alatt kizárólag standard könyvtárakat használ. Bontsd ki a projektet írható mappába.

```powershell
cd C:\eleresi\ut\comen_monitor
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nincs letöltendő külső Python csomag; a pip lépés opcionális. A GUI nem használ CDN-t vagy frontend frameworköt. Modern Chrome, Edge vagy Firefox szükséges.

## 2. Indítás Windows alatt

Dupla kattintás a `run.bat` fájlra, vagy:

```powershell
.venv\Scripts\python.exe app.py
```

Konzol:

```text
HL7 listening: 0.0.0.0:5000
Web interface: http://127.0.0.1:8080
```

Nyisd meg a http://127.0.0.1:8080 címet. Leállítás: Ctrl+C. Másik konfiguráció: `python app.py --config config-lab.json`. A data/logs útvonala mindig a projekt mappájához viszonyított.

Linux:

```bash
cd comen_monitor
python3 -m venv .venv
.venv/bin/python app.py
```

## 3. Python csomagok

Külső csomag nincs. A TCP fogadó socketserver, a webszerver http.server, a tárolás json, a tesztek unittest alapúak.

## 4. NC6 beállítása

1. A PC és az NC6 legyen elérhető egymás számára az intézményi hálózaton. Példa: PC `192.168.0.100`, monitor `192.168.0.118`, megfelelő hálózati maszk.
2. A készülék saját kézikönyvének HL7/hálózati beállításainál engedélyezd a paraméterküldést. Cél szerver IP: **a PC LAN IP-címe**, a példában `192.168.0.100`; cél TCP port: **5000**. A `127.0.0.1` és `0.0.0.0` nem használható a monitor célcímeként.
3. A megadott interfészprofil szerint a monitor legyen TCP kliens, MLLP keretezéssel (`0B … 1C 0D`), HL7 v2.6 ORU^R01 üzenetekkel. A fogadó alapértelmezésben ACK-ot küld ugyanazon kapcsolaton.
4. Engedélyezd a PC tűzfalán a bejövő TCP 5000 kapcsolatot a monitor IP-jéről. A 8080 port csak akkor kell más gépről, ha a webfelületet onnan is néznéd.
5. Küldj mérést, ellenőrizd a Live data és Raw HL7 nézeteket. A sorozatszámot szükség esetén rögzítsd: `"device_ids": {"192.168.0.118": "KC574337852G"}`.

A gyártó nyilvános termékoldala HL7 támogatást igazol, de nem részletezi az NC6 menüútvonalait, sorozatszám-mezőjét, ACK módját vagy teljes OBX kódtárát. Ezekhez az adott firmware interfészleírása szükséges; a fenti v2.6/5000/MLLP profil a feladatban megadott feltétel. Nincs kitalált szervizjelszó vagy menüútvonal.

## 5. Teszt valódi monitor nélkül

Indítsd az alkalmazást, majd egy második terminálban a projekt mappájából:

```powershell
python simulator.py --count 60 --fragment --batch 2
```

A szimulátor hétbájtos darabokban küld, több frame-et összefűz, és minden ACK AA kódját és MSA-2 korrelációját ellenőrzi. Alapértékek: SpO2 97%, Pulse 72 bpm, SYS/DIA/MAP 126/78/94 mmHg. A kapcsolat végén Disconnected jelenik meg; később újrafuttatva újracsatlakozik. Több monitorhoz indíts másik terminált: `python simulator.py --device SECOND --count 60`.

A hőmérséklet és légzésszám valós MDC kódját nem kaptuk meg. Az ismeretlen OBX adatok az Összes OBX panelen látszanak. A szimulátor saját, **nem valódi MDC** `SIM_TEMP` és `SIM_RESP` azonosítókat használ. A hozzájuk tartozó kártyák kipróbálásához állítsd be és indítsd újra:

```json
"extra_codes": {
  "SIM_TEMP": {"key": "temperature", "unit": "Cel"},
  "SIM_RESP": {"key": "respiration_rate", "unit": "/min"}
}
```

Éles eszköznél ezeket cseréld ellenőrzött gyártói kódokra. A küldött mértékegység elsőbbséget élvez; nincs egységátváltás vagy klinikai értékelés.

Automatizált tesztek:

```powershell
python -m unittest discover -s tests -v
```

Tesztelt: minden frame-vágási pont, byte-onkénti érkezés, több frame, szinkronhelyreállítás, méretkorlát, parser, ismeretlen kód, nullérték, NaN elutasítás, ACK azonosító és címzés; valódi localhost TCP/HTTP integráció, hibás üzenet utáni működés, újracsatlakozás, több eszköz, régi adat, CSV és újraindításkori history-visszaolvasás. A tesztek ideiglenes könyvtárat és szabad portokat használnak.

## API és adatmodell

- `GET /api/health`: alkalmazás és HL7 listener állapot.
- `GET /api/latest`: legutóbbi eszközüzenet; `?device_id=KC574337852G` szűrés.
- `GET /api/devices`: eszközök, connected/fresh és adatok.
- `GET /api/history`: tárolt üzenetsorok; opcionális `device_id` és `limit` (1…history_size).
- `GET /api/history.csv`: azonos szűrés, értékek és mértékegységek, UTF-8 BOM.
- `GET /api/raw`: a futás utolsó 200 nyers üzenete.
- `GET /api/settings`: konfiguráció, csak olvasható.

A history üzenetenkénti pillanatkép. Ott a hiányzó OBX nem örököl értéket egy korábbi mérésből. A Live nézet és latest API paraméterenként megőrzi az utolsó értéket saját received_at/fresh/age_seconds mezőkkel: hullámformaüzenet nem fiatalítja a mérést. Régi kártya halványul; az egérrel rámutatva látható az időbélyeg. Az összes legutóbbi OBX a `observations` listában marad; azonos ismert kód ismétlődésénél a kártyán az utolsó szerepel. Az OBX-11 státusz és OBX-14 nyers mérési idő megmarad; a GUI frissessége a PC fogadási idejére vonatkozik. A `connected` TCP-kapcsolatot, a felső `fresh` alapból legfeljebb 15 másodperces üzenetet jelent. Hálózati csend esetén a kapcsolat nyitva maradhat, de az adat régivé válik.

Az eszközazonosítás sorrendje: konfigurált IP→ID, OBX-18 első komponens, az észlelt NC_Monitor profilnál MSH-4 első komponens, MSH-3 első komponens, IP. Más általános alkalmazásnévnél állíts be IP→ID hozzárendelést, hogy a monitorok ne olvadjanak össze. Az észlelt R40 eseményüzenetek nyersen naplózódnak, AE választ kapnak saját R40 triggerrel; riasztásfeldolgozás nincs.

## Naplók és korlátok

- `logs/app.log`: strukturált JSON sorok, 5 MB rotáció és 3 másolat.
- `data/hl7_raw.log`: fogadási idő/IP/eredeti HL7 JSON sorokban; a CR karakterek visszaállíthatók. Tartalmazhat PID adatot.
- `data/measurements.jsonl`: minden elfogadott ORU megfigyelései. Induláskor az utolsó history_size sor visszatöltődik; hibás JSON sor kimarad. A Live data új üzenetre vár.

Az AA ACK a feldolgozás és sikeres fájlírás után készül; AE feldolgozási hibánál. Nem értelmezhető MSH esetén nem készíthető megbízható korrelált ACK: a hiba naplózódik. Original/application ACK mód támogatott, enhanced commit ACK (CA/CE/CR) nincs implementálva. A parser a szükséges ORU részhalmazt kezeli, nem teljes HL7 validátor. NM numerikus érték és egyéb típusok nyers értéke támogatott; összetett SN értékek nem alakulnak skaláris méréssé. Nincs ACK-újraküldés deduplikáció: ismételt ORU ismét szerepel a historyban.

A history és raw fájlok folyamatosan nőnek; archiválásuk üzemeltetési feladat. A memóriabeli history korlátos. Nincs hitelesítés vagy TLS: a fogadó helyi/megbízható hálózatra készült, internetre közvetlenül ne tedd ki. Kizárólag helyi webeléréshez `web_host` legyen `127.0.0.1`. A megjelenítő nem helyettesíti a monitor riasztásait.

Források: [COMEN NC6/NC7 termékoldal](https://en.comen.com/products/NC6%26NC7), [HL7 Australia ACK útmutató](https://hl7.org.au/archive/hl7v2wg/8-Acknowledgement_31588902.html), [Microsoft HL7 MSA](https://learn.microsoft.com/en-us/biztalk/adapters-and-accelerators/accelerator-hl7/message-acknowledgment-segment).
