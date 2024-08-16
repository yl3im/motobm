# zone
MOTOTRBO zone file generator from BrandMeister repeater list. It makes use of [BrandMeister API](https://wiki.brandmeister.network/index.php/API/Halligan_API) to retrieve the the list of actual DMR repeaters and importing them into Motorola DMR radios as zones, filtered by country or location.

## Installation

* `git clone https://github.com/yl3im/motobm.git`
* `python -m venv ./motobm-env`
* `source ./motobm-env/bin/activate`
* `python -m pip install -r requirements.txt`

## Usage

```
usage: python zone.py [-h] [-f] -n NAME -b {vhf,uhf} -t {mcc,qth,gps} [-m MCC] [-q QTH] [-r RADIUS] [-lat LAT] [-lng LNG] [-p] [-6] [-zc ZONE_CAPACITY]

Generate MOTOTRBO zone files from BrandMeister.

optional arguments:
  -h, --help            show this help message and exit
  -f, --force           Forcibly download repeater list even if it exists locally.
  -n NAME, --name NAME  Zone name. Choose it freely on your own.
  -b {vhf,uhf}, --band {vhf,uhf}
                        Repeater band.
  -t {mcc,qth,gps}, --type {mcc,qth,gps}
                        Select repeaters by MCC code, QTH locator index or GPS coordinates.
  -m MCC, --mcc MCC     First repeater ID digits, usually a 3 digits MCC. You can also use a two letter country code instead.
  -q QTH, --qth QTH     QTH locator index like KO26BX.
  -r RADIUS, --radius RADIUS
                        Area radius in kilometers around the center of the chosen QTH locator. Defaults to 100.
  -lat LAT              Latitude of a GPS position.
  -lng LNG, -lon LNG    Longitude of a GPS position.
  -p, --pep             Only select repeaters with defined power.
  -6, --six             Only select repeaters with 6 digit ID.
  -zc ZONE_CAPACITY, --zone-capacity ZONE_CAPACITY
                        Channel capacity within zone. 160 by default as for top models, use 16 for the lite and non-display ones.
```

## Examples

`python zone.py -n 'Germany' -b vhf -t mcc -m 262 -6 -zc 16`

will create XML zone file(s) with all German repeaters for 2m band with 6 digit ID (real repeaters, not just hotspots), split to 16 channels per one zone.

`python zone.py -n 'Lithuania' -b uhf -t mcc -m LT -6`

will create XML zone file(s) with all Lithuanian repeaters for 70 band with 6 digit ID (real repeaters, not just hotspots).

`python zone.py -n 'Paris' -b uhf -t qth -q JN18EU -r 150 -6`

will create XML zone file(s) with all repeaters for 70cm band with 6 digit ID (real repeaters, not just hotspots) 150 kilometers around Paris.

`python zone.py -n 'Stockholm' -b uhf -t gps -lat 59.225 -lon 18.250 -6`

will create XML zone file(s) with all repeaters for 70cm band with 6 digit ID (real repeaters, not just hotspots) 100 kilometers around Stockholm.

In case your latitude and/or longitude have negative values, please refer them this way to avoid errors:

`python zone.py -n 'Minneapolis' -b uhf -t gps -lat 44.9570 -lon " -93.2780" -6`

or

`python zone.py -n 'Minneapolis' -b uhf -t gps -lat 44.9570 -lon=-93.2780 -6`

While creating zone file(s) the script will also output the list of found repeaters like this:

```
 Callsign    RX        TX        CC    City                    URL
----------  --------  --------  ----  ----------------------  -----------------------------------------------------
DB0DVR      144.9875  145.5875  1     Braunschweig  (JO52FF)  https://brandmeister.network/?page=repeater&id=262386
DB0HE       144.8250  144.8250  1     Herten, JO31NO          https://brandmeister.network/?page=repeater&id=262443
DB0KI       144.8750  144.8750  2     Kniebis                 https://brandmeister.network/?page=repeater&id=262010
```

thus giving you additional insight.

## Importing files to CPS2

* Open the XML file contents in text editor, like Notepad.
* Select All. Copy.
* Open CPS2, on its left pane go to `Configuration` -> `Zone/Channel Assignment`, right-click on `Zone` and choose Paste.
* Don't forget to set up the parameters for the new zone, like `Tx Contact Name` and `Rx Group List`. Can be done at once with `Fill Down` feature in CPS2.

## What about CPS16?

Unfortunately, CPS16 doesn't support pasting of XML content. Therefore this method only works for CPS2 which requires a [radio firmware version of R2.10 or higher](https://cwh050.mywikis.wiki/wiki/List_of_software_versions).
