# motobm
MOTOTRBO zone file generator from BrandMeister repeater list

## Usage

```
usage: motobm.py [-h] -n NAME -b {vhf,uhf} -t {mcc} [-m MCC] [-f] [-p] [-6] [-zc ZONE_CAPACITY]

Generate MOTOTRBO zone files from BrandMeister.

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Zone name.
  -b {vhf,uhf}, --band {vhf,uhf}
                        Repeater band.
  -t {mcc}, --type {mcc}
                        Select repeaters by MCC code, QTH locator index or GPS coordinates. Only MCC option is implemented as of now.
  -m MCC, --mcc MCC     First repeater ID digits, usually a 3 digits MCC.
  -f, --force           Forcibly download repeater list even if it exists locally.
  -p, --pep             Only select repeaters with defined power.
  -6, --six             Only select repeaters with 6 digit ID.
  -zc ZONE_CAPACITY, --zone-capacity ZONE_CAPACITY
                        Channel capacity within zone. 160 by default as for top models, use 16 for the lite ones.
```

For example: 

`python3 motobm.py -n 'My Zone' -b vhf -t mcc -m 262 -6 -zc 16`

will create XML zone file(s) with all German repeaters for 2m band with 6 digit ID (real repeaters, not just hotspots), split to 16 channels per one zone.

## ToDo

* location based search (GPS area)
* ... you name it :)