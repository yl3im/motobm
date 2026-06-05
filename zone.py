#!/usr/bin/env python3

import argparse
from datetime import datetime, timezone
import json
from os.path import exists, getmtime
import time
from xml.sax.saxutils import escape
from tabulate import tabulate

import geopy.distance
import maidenhead
import mobile_codes
import requests
import urllib3


parser = argparse.ArgumentParser(description='Generate MOTOTRBO zone files from BrandMeister.')

parser.add_argument('-f', '--force', action='store_true',
                    help='Forcibly download repeater list even if it exists locally.')
parser.add_argument('-n', '--name', required=True, help='Zone name. Choose it freely on your own.')
parser.add_argument('-b', '--band', choices=['vhf', 'uhf'], required=True, help='Repeater band.')

parser.add_argument('-t', '--type', choices=['mcc', 'qth', 'gps'], required=True,
                    help='Select repeaters by MCC code, QTH locator index or GPS coordinates.')

parser.add_argument('-m', '--mcc', help='First repeater ID digits, usually a 3 digits MCC. '
                                        'You can also use a two letter country code instead.')
parser.add_argument('-q', '--qth', help='QTH locator index like KO26BX.')

parser.add_argument('-r', '--radius', default=100, type=int,
                    help='Area radius in kilometers around the center of the chosen QTH locator. Defaults to 100.')

parser.add_argument('-lat', type=float, help='Latitude of a GPS position.')
parser.add_argument('-lng', '-lon', type=float, help='Longitude of a GPS position.')

parser.add_argument('-p', '--pep', action='store_true', help='Only select repeaters with defined power.')
parser.add_argument('-6', '--six', action='store_true', help='Only select repeaters with 6 digit ID.')
parser.add_argument('-zc', '--zone-capacity', default=160, type=int,
                    help='Channel capacity within zone. 160 by default as for top models, use 16 for the lite and '
                         'non-display ones.')
parser.add_argument('-c', '--customize', action='store_true',
                    help='Include customized values for each channel.')
parser.add_argument('-cs', '--callsign', help='Only list callsigns containing specified string like a region number.')


args = parser.parse_args()

# argparse can't express "this option is required only for this --type", so enforce
# the per-type requirements here after parsing.
if args.type == 'mcc' and not args.mcc:
    parser.error('-t mcc requires -m/--mcc.')
if args.type == 'qth' and not args.qth:
    parser.error('-t qth requires -q/--qth.')
if args.type == 'gps' and (args.lat is None or args.lng is None):
    parser.error('-t gps requires both -lat and -lng/-lon.')
if args.zone_capacity < 1:
    parser.error('-zc/--zone-capacity must be a positive integer.')


# Module-level state shared across functions via `global` (see CLAUDE.md):
# filtered_list  - repeaters kept after filtering
# output_list    - rows for the per-zone summary table
# existing       - count of repeaters per callsign, used to add #N suffixes
# custom_values  - contents of custom-values.xml spliced into each channel
bm_url = 'https://api.brandmeister.network/v2/device'
bm_file = 'BM.json'
filtered_list = []
output_list = []
existing = {}
custom_file = 'custom-values.xml'
custom_values = ''

# Resolve the search centre once up front: from the QTH locator's centre, or from
# the explicit GPS pair. Used by the distance filter in filter_list().
if args.type == 'qth':
    qth_coords = maidenhead.to_location(args.qth, center=True)
if args.type == 'gps':
    qth_coords = (args.lat, args.lng)

# -m/--mcc accepts a numeric prefix or a 2-letter country code; translate the
# latter to its MCC(s) (mcc may be a list for countries with several).
if args.mcc and not str(args.mcc).isdigit():
    try:
        args.mcc = mobile_codes.alpha2(args.mcc).mcc
    except KeyError:
        parser.error(f"unknown country code '{args.mcc}'; use a 2-letter ISO code (e.g. LV) "
                     f"or a numeric MCC prefix.")


def check_custom():
    # Load the optional custom-values.xml snippet (-c/--customize). Create it empty
    # if missing so the run never fails on a first use.
    global custom_file
    global custom_values

    if not exists(custom_file):
        with open(custom_file, 'w') as file:
            file.write('')

    with open(custom_file, 'r') as file:
        custom_values = file.read()


def download_file():
    # Fetch the BrandMeister device list, but only when it's missing or -f/--force
    # is given; otherwise reuse the cached BM.json to avoid re-downloading.
    if not exists(bm_file) or args.force:
        print(f'Downloading from {bm_url}')

        # TLS verification is intentionally disabled (upstream cert issue); silence
        # the resulting urllib3 warning. See CLAUDE.md.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(bm_url, verify=False)
        response.raise_for_status()

        with open(bm_file, 'wb') as file:
            file.write(response.content)

        print(f'Saved to {bm_file}')
    else:
        # Cached copy reused: warn if it's stale so the user knows to pass -f.
        age_days = (time.time() - getmtime(bm_file)) / 86400
        if age_days > 7:
            print(f'Warning: {bm_file} is {age_days:.0f} days old. Use -f to download a fresh copy.')


def xml_escape(value):
    # Escape &, <, > plus quotes/apostrophes so values are safe inside XML
    # attributes and elements (channels are built by string interpolation).
    return escape(str(value), {'"': '&quot;', "'": '&apos;'})


def check_distance(loc1, loc2):
    # Great-circle distance in km between two (lat, lng) pairs.
    return geopy.distance.great_circle(loc1, loc2).km


def has_coords(item):
    # BrandMeister uses null or 0/'0' as a "no location" placeholder; treat those as missing.
    try:
        return float(item['lat']) != 0 and float(item['lng']) != 0
    except (TypeError, ValueError):
        return False


def local_datetime(last_seen: str) -> str:
    # The API reports last_seen in UTC; convert it to the machine's local time
    # for display in the summary table.
    utc_dt = datetime.strptime(
        last_seen, "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)

    return utc_dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def filter_list():
    # Read BM.json and build filtered_list by applying every active filter, then
    # deduplicating and tagging each kept repeater with its per-callsign count.
    global filtered_list
    global existing
    global qth_coords

    with open(bm_file, "r") as f:
        json_list = json.loads(f.read())

    # Stable order: group by callsign, then by numeric id within a callsign.
    sorted_list = sorted(json_list, key=lambda k: (k['callsign'], int(k["id"])))

    seen = set()

    for item in sorted_list:
        # Band filter: VHF repeaters have RX starting with 1, UHF with 4. Deliberate;
        # see CLAUDE.md / band-detection memory.
        if not ((args.band == 'vhf' and item['rx'].startswith('1')) or (
                args.band == 'uhf' and item['rx'].startswith('4'))):
            continue

        # MCC filter: keep only repeaters whose id starts with the requested prefix.
        # args.mcc may be a list (country code resolving to several MCCs).
        if args.type == 'mcc':
            is_starts = False

            if isinstance(args.mcc, list):
                for mcc in args.mcc:
                    if str(item['id']).startswith(mcc):
                        is_starts = True
            else:
                if str(item['id']).startswith(args.mcc):
                    is_starts = True

            if not is_starts:
                continue

        # Location filter: drop repeaters without coordinates, then any outside the
        # requested radius around the QTH/GPS centre.
        if args.type == 'qth' or args.type == 'gps':
            if not has_coords(item):
                continue
            if check_distance(qth_coords, (float(item['lat']), float(item['lng']))) > args.radius:
                continue

        # -p/--pep: keep only repeaters that advertise a non-zero power value.
        if args.pep and (not str(item['pep']).isdigit() or str(item['pep']) == '0'):
            continue

        # -6/--six: keep only repeaters with a 6-digit (i.e. full) DMR ID.
        if args.six and not len(str(item['id'])) == 6:
            continue

        # -cs/--callsign: keep only callsigns containing the given substring. The
        # [:-1] slice is intentional; see callsign-filter-slice memory.
        if args.callsign and (not args.callsign in item['callsign'][:-1]):
            continue

        # Fall back to the numeric id when a repeater has no callsign, then keep only
        # the first whitespace-delimited token of the callsign.
        if item['callsign'] == '':
            item['callsign'] = item['id']

        item['callsign'] = item['callsign'].split()[0]

        # Deduplicate on (rx, tx, callsign): the same repeater can appear more than once.
        key = (item['rx'], item['tx'], item['callsign'])
        if key in seen:
            continue
        seen.add(key)

        # Track how many repeaters share this callsign; `turn` is this one's index,
        # used later to append a #N suffix when there's more than one.
        if not item['callsign'] in existing: existing[item['callsign']] = 0
        existing[item['callsign']] += 1
        item['turn'] = existing[item['callsign']]

        filtered_list.append(item)


def process_channels():
    # Split filtered_list into zones of --zone-capacity channels and write one XML
    # file per chunk, printing a summary table for each.
    global output_list

    channel_chunks = [filtered_list[i:i + args.zone_capacity] for i in range(0, len(filtered_list), args.zone_capacity)]
    chunk_number = 0

    for chunk in channel_chunks:
        channels = ''
        chunk_number += 1
        output_list = []  # reset table rows; format_channel() appends to it per repeater

        for item in chunk:
            channels += format_channel(item)

        print('\n',
              tabulate(output_list, headers=['Callsign', 'RX', 'TX', 'CC', 'City', 'Last seen', 'URL'],
                       disable_numparse=True),
              '\n')

        # A single chunk keeps the plain zone name; multiple chunks get a #N suffix.
        if len(channel_chunks) == 1:
            zone_alias = args.name
        else:
            zone_alias = f'{args.name} #{chunk_number}'

        zone_alias_xml = xml_escape(zone_alias)

        write_zone_file(zone_alias, f'''<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<config>
  <category name="Zone">
    <set name="Zone" alias="{zone_alias_xml}" key="NORMAL">
      <collection name="ZoneItems">
        {channels}
      </collection>
      <field name="ZP_ZONEALIAS">{zone_alias_xml}</field>
      <field name="ZP_ZONETYPE" Name="Normal">NORMAL</field>
      <field name="ZP_ZVFNLITEM" Name="None">NONE</field>
      <field name="Comments"></field>
    </set>
  </category>
</config>
''')


def format_channel(item):
    # Build the CPS2 XML for one repeater and record a row for the summary table.
    global existing
    global output_list
    global custom_values

    # Unique callsign keeps its bare alias; shared callsigns get a #N suffix.
    if existing[item['callsign']] == 1:
        ch_alias = item['callsign']
    else:
        ch_alias = f"{item['callsign']} #{item['turn']}"

    ch_rx = item['rx']
    ch_tx = item['tx']
    ch_cc = item['colorcode']

    output_list.append([ch_alias, ch_rx, ch_tx, ch_cc, item['city'], local_datetime(item['last_seen']),
                        f"https://brandmeister.network/?page=device&id={item['id']}"])

    # Escape values interpolated into the XML below; the table row above keeps the raw values.
    ch_alias = xml_escape(ch_alias)
    ch_rx = xml_escape(ch_rx)
    ch_tx = xml_escape(ch_tx)
    ch_cc = xml_escape(ch_cc)

    # Simplex/hotspot (rx == tx): emit a single SLOT2 personality. A duplex
    # repeater instead emits the paired TS1/TS2 personalities below. Note TXFREQ
    # is fed from rx and RXFREQ from tx: the radio transmits on the repeater's
    # input and listens on its output.
    if item['rx'] == item['tx']:
        return f'''
<set name="ConventionalPersonality" alias="{ch_alias}" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="2">SLOT2</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_rx}</field>
  <field name="CP_RXFREQ">{ch_tx}</field>
  <field name="CP_EMACKALERTEN">True</field>
  <field name="CP_CNVPERSALIAS">{ch_alias}</field>
  <field name="CP_TXINHXPLEN" Name="Color Code Free">MTCHCLRCD</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_GPSRVRTPERSIT" Name="Selected">SELECTED</field>
  <field name="CP_OVCMDECODEENABLE">True</field>
  <field name="CP_TXCOMPUDPIPHEADEN" Name="DMR Standard">DMR_UDP_HEADER</field>
  <field name="CP_LOCATIONDATADELIVERYMODE" Name="Follow Data Call Confirmed">FOLLOW_CALL_DATA_SETTING</field>
  <field name="CP_MYCALLADCRTR" Name="Follow Admit Criteria">FOLLOW_ADMIT_CRITERIA</field>
  <field name="CP_TEXTMESSAGETYPE" Name="Advantage">TMS</field>
  <field name="CP_TRANSMITINTERRUPTTYPE" Name="Advantage">PROPRIETARY</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_TOT">180</field>
  <field name="CP_INTRPTMSGDLY">510</field>
{custom_values}
</set>
    '''

    # Duplex repeater: one personality per timeslot (TS1 = SLOT1, TS2 = SLOT2).
    # These blocks are intentionally kept separate rather than deduplicated; see
    # xml-templates-separate memory.
    return f'''
<set name="ConventionalPersonality" alias="{ch_alias} TS1" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="1">SLOT1</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_rx}</field>
  <field name="CP_RXFREQ">{ch_tx}</field>
  <field name="CP_EMACKALERTEN">True</field>
  <field name="CP_CNVPERSALIAS">{ch_alias} TS1</field>
  <field name="CP_TXINHXPLEN" Name="Color Code Free">MTCHCLRCD</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_GPSRVRTPERSIT" Name="Selected">SELECTED</field>
  <field name="CP_OVCMDECODEENABLE">True</field>
  <field name="CP_TXCOMPUDPIPHEADEN" Name="DMR Standard">DMR_UDP_HEADER</field>
  <field name="CP_LOCATIONDATADELIVERYMODE" Name="Follow Data Call Confirmed">FOLLOW_CALL_DATA_SETTING</field>
  <field name="CP_MYCALLADCRTR" Name="Follow Admit Criteria">FOLLOW_ADMIT_CRITERIA</field>
  <field name="CP_TEXTMESSAGETYPE" Name="Advantage">TMS</field>
  <field name="CP_TRANSMITINTERRUPTTYPE" Name="Advantage">PROPRIETARY</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_ARSPLUS" Name="On System/Site Change">ARS_SYS_SITE_CHANGE</field>
  <field name="CP_TOT">180</field>
  <field name="CP_INTRPTMSGDLY">510</field>
{custom_values}
</set>
<set name="ConventionalPersonality" alias="{ch_alias} TS2" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="2">SLOT2</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_rx}</field>
  <field name="CP_RXFREQ">{ch_tx}</field>
  <field name="CP_EMACKALERTEN">True</field>
  <field name="CP_CNVPERSALIAS">{ch_alias} TS2</field>
  <field name="CP_TXINHXPLEN" Name="Color Code Free">MTCHCLRCD</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_GPSRVRTPERSIT" Name="Selected">SELECTED</field>
  <field name="CP_OVCMDECODEENABLE">True</field>
  <field name="CP_TXCOMPUDPIPHEADEN" Name="DMR Standard">DMR_UDP_HEADER</field>
  <field name="CP_LOCATIONDATADELIVERYMODE" Name="Follow Data Call Confirmed">FOLLOW_CALL_DATA_SETTING</field>
  <field name="CP_MYCALLADCRTR" Name="Follow Admit Criteria">FOLLOW_ADMIT_CRITERIA</field>
  <field name="CP_TEXTMESSAGETYPE" Name="Advantage">TMS</field>
  <field name="CP_TRANSMITINTERRUPTTYPE" Name="Advantage">PROPRIETARY</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_ARSPLUS" Name="On System/Site Change">ARS_SYS_SITE_CHANGE</field>
  <field name="CP_TOT">180</field>
  <field name="CP_INTRPTMSGDLY">510</field>
{custom_values}
</set>
    '''


def write_zone_file(zone_alias, contents):
    # Write one zone's XML to "<alias>.xml" for import into CPS2.
    zone_file_name = zone_alias + ".xml"
    with open(zone_file_name, "wt") as zone_file:
        zone_file.write(contents)
    print(f'Zone file "{zone_file_name}" written.\n')


if __name__ == '__main__':
    # Pipeline: optionally load custom values, fetch the list, filter it, write zones.
    if args.customize:
        check_custom()
    download_file()
    filter_list()
    process_channels()
