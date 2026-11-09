## COMEN eszköz
- A monitort DHCP-re állítottuk, és megkapta a 10.64.5.217 IP címet
- Eszköz IP címének beállítása: Menu -> System -> Maintain -> Network Setup -> LAN1 IP
- Céleszközhöz kapcsolódó beállítások: Menu -> System -> Maintain -> Network Setup -> HL7 Setup
- Céleszköz fixen beállítva: a fejlesztői PC-re, 5000-es port.
- Jelszó 5188

### Egyéb átkonfigurált beállítások
- Periodikus vérnyomás mérés kikapcsolása
- Alarmok kikapcsolása

## Egérszimulátor
- Az egérszimulátor DHCP-n van, a kapott cím kiderítése_
  - MAC: 02:08:dc:77:9b:2d
  - Ugyanazon az alhálózaton futó linuxon: (Kalmár Ádám gépe)
    - sudo nmap -sn 10.64.0.0/21
    - ip neigh | grep -i "02:08:dc:77:9b:2d"
  - Ezután az adott IP címen elérhető böngészőből, 80-as port: admin/mousesym
- Vérnyomásmérés elindítása a szimulátor segítségével: `python mousesym/tools/mousesym_client.py --host 10.64.4.235 --key mousesym "MOVE 0 0" "CLICK 220 75"`


