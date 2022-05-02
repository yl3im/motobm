import argparse
import json
from os.path import exists
from urllib import request

parser = argparse.ArgumentParser(description='Generate MOTOTRBO zone files from BrandMeister.')

parser.add_argument('-n', '--name', required=True, help='Zone name.')
parser.add_argument('-b', '--band', choices=['vhf', 'uhf'], required=True, help='Repeater band.')

parser.add_argument('-t', '--type', choices=['mcc'], required=True,
                    help='Select repeaters by MCC code, QTH locator index or GPS coordinates. '
                         'Only MCC option is implemented as of now.')
parser.add_argument('-m', '--mcc', help='First repeater ID digits, usually a 3 digits MCC.')

parser.add_argument('-f', '--force', action='store_true',
                    help='Forcibly download repeater list even if it exists locally.')
parser.add_argument('-p', '--pep', action='store_true', help='Only select repeaters with defined power.')
parser.add_argument('-6', '--six', action='store_true', help='Only select repeaters with 6 digit ID.')
parser.add_argument('-zc', '--zone-capacity', default=160, type=int,
                    help='Channel capacity within zone. 160 by default as for top models, use 16 for the lite ones.')

args = parser.parse_args()

bm_url = 'https://api.brandmeister.network/v1.0/repeater/?action=LIST'
bm_file = 'BM.json'
filtered_list = []
existing = {}


def download_file():
    if not exists(bm_file) or args.force:
        print(f'Downloading from {bm_url}')
        request.urlretrieve(bm_url, bm_file)
        print(f'Saved to {bm_file}')


def filter_list():
    global filtered_list
    global existing

    f = open(bm_file, "r")

    for item in json.loads(f.read()):
        if not ((args.band == 'vhf' and item['rx'].startswith('1')) or (
                args.band == 'uhf' and item['rx'].startswith('4'))):
            continue

        if args.type == 'mcc' and not item['repeaterid'].startswith(args.mcc):
            continue

        if args.pep and (not str(item['pep']).isdigit() or str(item['pep']) == '0'):
            continue

        if args.six and not len(item['repeaterid']) == 6:
            continue

        if item['callsign'] == '':
            item['callsign'] = item['repeaterid']

        item['callsign'] = item['callsign'].split()[0]

        if any((existing['rx'] == item['rx'] and existing['tx'] == item['tx'] and existing['callsign'] == item[
            'callsign']) for existing in filtered_list):
            continue

        if not item['callsign'] in existing: existing[item['callsign']] = 0
        existing[item['callsign']] += 1
        item['turn'] = existing[item['callsign']]

        filtered_list.append(item)

    f.close()


def process_channels():
    channel_chunks = [filtered_list[i:i + args.zone_capacity] for i in range(0, len(filtered_list), args.zone_capacity)]
    chunk_number = 0

    for chunk in channel_chunks:
        channels = ''
        chunk_number += 1

        for item in chunk:
            channels += format_channel(item)

        if len(channel_chunks) == 1:
            zone_alias = args.name
        else:
            zone_alias = f'{args.name} #{chunk_number}'

        write_zone_file(zone_alias, f'''<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<config>
  <category name="Zone">
    <set name="Zone" alias="{zone_alias}" key="NORMAL">
      <collection name="ZoneItems">
        {channels}
      </collection>
      <field name="ZP_ZONEALIAS">{zone_alias}</field>
      <field name="ZP_ZONETYPE" Name="Normal">NORMAL</field>
      <field name="ZP_ZVFNLITEM" Name="None">NONE</field>
      <field name="Comments"></field>
    </set>
  </category>
</config>
''')


def format_channel(item):
    global existing

    if existing[item['callsign']] == 1:
        ch_alias = item['callsign']
    else:
        ch_alias = f"{item['callsign']} #{item['turn']}"

    ch_rx = item['rx']
    ch_tx = item['tx']
    ch_cc = item['colorcode']

    print(f"{ch_alias} Rx: {ch_rx} Tx: {ch_tx} CC: {ch_cc} ID: {item['repeaterid']}")

    if item['rx'] == item['tx']:
        return f'''
<set name="ConventionalPersonality" alias="{ch_alias}" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="2">SLOT2</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_tx}</field>
  <field name="CP_RXFREQ">{ch_rx}</field>
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
</set>
    '''

    return f'''
<set name="ConventionalPersonality" alias="{ch_alias} TS1" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="1">SLOT1</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_tx}</field>
  <field name="CP_RXFREQ">{ch_rx}</field>
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
</set>
<set name="ConventionalPersonality" alias="{ch_alias} TS2" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="2">SLOT2</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_tx}</field>
  <field name="CP_RXFREQ">{ch_rx}</field>
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
</set>
    '''


def write_zone_file(zone_alias, contents):
    zone_file_name = zone_alias + ".xml"
    zone_file = open(zone_file_name, "wt")
    zone_file.write(contents)
    zone_file.close()
    print(f'Zone "{zone_file_name}" file written.\n')


if __name__ == '__main__':
    download_file()
    filter_list()
    process_channels()
