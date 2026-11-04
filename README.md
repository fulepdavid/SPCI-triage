* Hálózati beállítások
- A monitort DHCP-re állítottuk, és megkapta a 10.64.6.233 IP címet
  Menü: System / xxx /
- A monitor beállítása, hogy hova küldje a mérési adatokat:
  - Fixen beállítva: a fejlesztői PC-re, 5000-es port.

## Egérszimulátor
- Az egérszimulátor DHCP-n van, a kapott cím kiderítése_
  - MAC: 02:08:dc:77:9b:2d
  - Ugyanazon az alhálózaton futó linuxon: (Kalmár Ádám gépe)
    - sudo nmap -sn 10.64.0.0/21
    - ip neigh | grep -i "02:08:dc:77:9b:2d"
  - Ezután az adott IP címen elérhető böngészőből, 80-as port: admin/mousesym
  - Vérnyomásmérés elindítása a szimulátor segítségével: `python tools/mousesym_client.py 10.64.6.233 --key mousesym "MOVE 0 0" "CLICK 220 75`

## COMEN eszköz
- Eszköz IP címének beállítása: Menu -> System -> Maintain -> Network Setup -> LAN1 IP
- Céleszközhöz kapcsolódó beállítások: Menu -> System -> Maintain -> Network Setup -> HL7 Setup
- Jelszó 5188
