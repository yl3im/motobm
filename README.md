# motobm
MOTOTRBO zone file generator from BrandMeister repeater list. It makes use of [BrandMeister API](https://wiki.brandmeister.network/index.php/API/Halligan_API) to retrieve the the list of actual DMR repeaters and importing them into Motorola DMR radios as zones, filtered by country or location.

## Installation

`pip install -r requirements.txt` as root or `pip install -r requirements.txt --user` as ordinary user.

## Usage

```
usage: motobm.py [-h] [-f] -n NAME -b {vhf,uhf} -t {mcc,qth,gps} [-m MCC] [-q QTH] [-r RADIUS] [-lat LAT] [-lng LNG] [-p] [-6] [-zc ZONE_CAPACITY]

Generate MOTOTRBO zone files from BrandMeister.

optional arguments:
  -h, --help            show this help message and exit
  -f, --force           Forcibly download repeater list even if it exists locally.
  -n NAME, --name NAME  Zone name.
  -b {vhf,uhf}, --band {vhf,uhf}
                        Repeater band.
  -t {mcc,qth,gps}, --type {mcc,qth,gps}
                        Select repeaters by MCC code, QTH locator index or GPS coordinates.
  -m MCC, --mcc MCC     First repeater ID digits, usually a 3 digits MCC.
  -q QTH, --qth QTH     QTH locator index like KO26BX.
  -r RADIUS, --radius RADIUS
                        Area radius in kilometers around the center of the chosen QTH locator. Defaults to 100.
  -lat LAT              Latitude of a GPS position.
  -lng LNG, -lon LNG    Longitude of a GPS position.
  -p, --pep             Only select repeaters with defined power.
  -6, --six             Only select repeaters with 6 digit ID.
  -zc ZONE_CAPACITY, --zone-capacity ZONE_CAPACITY
                        Channel capacity within zone. 160 by default as for top models, use 16 for the lite ones.
```

## Examples

`motobm.py -n 'Germany' -b vhf -t mcc -m 262 -6 -zc 16`

will create XML zone file(s) with all German repeaters for 2m band with 6 digit ID (real repeaters, not just hotspots), split to 16 channels per one zone.

`motobm.py -n 'Paris' -b uhf -t qth -q JN18EU -r 150 -6`

will create XML zone file(s) with all repeaters for 70cm band with 6 digit ID (real repeaters, not just hotspots) 150 kilometers around Paris.

`motobm.py -n 'Stockholm' -b uhf -t gps -lat 59.225 -lon 18.250 -6`

will create XML zone file(s) with all repeaters for 70cm band with 6 digit ID (real repeaters, not just hotspots) 100 kilometers around Stockholm.

## Importing files to CPS2

* Open the XML file contents in text editor, like Notepad.
* Select All. Copy.
* Open CPS2, on its left pane go to `Configuration` -> `Zone/Channel Assignment`, right-click on `Zone` and choose Paste.

## What about CPS16?

Unfortunately, CPS16 doesn't support pasting of XML content. Therefore this method only works for CPS2 which requires a [radio firmware version of R2.10 or higher](https://cwh050.mywikis.wiki/wiki/List_of_software_versions).
