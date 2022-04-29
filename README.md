# motobm
MOTOTRBO zone generator from BrandMeister repeater list

## Usage

```
usage: motobm.py [-h] -n NAME -b {vhf,uhf} -t {mcc} [-m MCC] [-f] [-p] [-6]

Generate MOTOTRBO zones from BrandMeister.

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Zone name.
  -b {vhf,uhf}, --band {vhf,uhf}
                        Repeater band.
  -t {mcc}, --type {mcc}
                        Select repeaters by MCC code or GPS location.
  -m MCC, --mcc MCC     First repeater ID digits, usually a 3 digits MCC.
  -f, --force           Forcibly download repeater list even if it exists locally.
  -p, --pep             Only select repeaters with defined power.
  -6, --six             Only select repeaters with 6 digit ID.
```

For example: 

`python3 motobm.py -n 'My Zone' -b vhf -t mcc -m 262 -6`

will create an XML zone file with all German repeaters for 2m band with 6 digit ID (real repeaters, not just hotspots)

## ToDo

* location based search (GPS area)
* split zone file to several ones due to CPS2 restrictions
* ... you name it :)