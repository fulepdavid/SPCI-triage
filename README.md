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
