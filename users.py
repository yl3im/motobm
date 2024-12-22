#!/usr/bin/env python3

import argparse
import json
from os.path import exists

import requests
import urllib3

import unicodedata

parser = argparse.ArgumentParser(description='Generate MOTOTRBO contacts file from RadioId.net data')

parser.add_argument('-f', '--force', action='store_true',
                    help='Forcibly download user list even if it exists locally')
parser.add_argument('-c', '--country', required=True, help='Country name'
                                        'As per RadioID.net')

args = parser.parse_args()

radioid_url = 'https://radioid.net/api/dmr/user/?'
radioid_file = 'radioid_' + args.country + '.json'
existing = {}

def download_file():

    if not exists(radioid_file) or args.force:
        download_ext_path = f'country={args.country}' if args.country else print('Country name is required.') and exit(1)


        download_full_path = radioid_url + download_ext_path

        print(f'Downloading from {download_full_path}')

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(download_full_path, verify=False)
        response.raise_for_status()

        with open(radioid_file, 'wb') as file:
            file.write(response.content)

        print(f'Saved to {radioid_file}')


def process_contacts():
    f = open(radioid_file, 'r')
    json_list = json.loads(f.read())

    idx = 0
    channels = ''
    for item in json_list['results']:
        idx += 1
        channels += format_channel(item)
    
    f.close()

    print(f'Processed {idx} records.')

    write_zone_file(args.country,
f'''<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<config>
  <category name="PCRContacts">
    {channels}
  </category>
</config>''')

def format_channel(item):
    global existing

    city = unicodedata.normalize('NFKD', item['city']).encode('ascii', 'ignore').decode('utf-8').strip()
    name = unicodedata.normalize('NFKD', item['fname']).encode('ascii', 'ignore').decode('utf-8').strip()
    surname = unicodedata.normalize('NFKD', item['surname']).encode('ascii', 'ignore').decode('utf-8').strip()
    
    # max len 16 chars
    contact_name = f'{item["callsign"]} {name} {surname}'.strip()[:16]

    if not contact_name in existing: existing[contact_name] = 0
    existing[contact_name] += 1
    if existing[contact_name] > 1:
        # cut contact name to 14 chars and add space and number
        contact_name = f'{contact_name[:14]} {existing[contact_name]}'

    return f'''<set name="PCRContacts" alias="{contact_name}">
      <field name="ContactName">{contact_name}</field>
      <collection name="DigitalCalls">
        <set name="DigitalCalls" index="0" key="PRIVCALL">
          <field name="DU_CALLALIAS">{contact_name}</field>
          <field name="DU_CALLLSTID">{item["id"]}</field>
          <field name="DU_ROUTETYPE" Name="Regular">REGULAR</field>
          <field name="DU_CALLPRCDTNEN">False</field>
          <field name="DU_RINGTYPE" Name="No Style">NOSTYLE</field>
          <field name="DU_TXTMSGALTTNTP" Name="Repetitive">REPETITIVE</field>
          <field name="DU_CALLTYPE" Name="Private Call">PRIVCALL</field>
          <field name="DU_OVCMCALL">False</field>
          <field name="DU_CALLTYPEPART2">0</field>
          <field name="DU_UKPOTCFLG">False</field>
          <field name="DU_RVRTPERS_Zone" Name="None">NONE</field>
          <field name="DU_RVRTPERS" Name="Selected">SELECTED</field>
          <field name="CallType">Digital Calls-Private Call</field>
          <field name="PeudoCallId">{item["id"]}</field>
        </set>
      </collection>
      <collection name="CapacityPlusCalls" />
      <collection name="PhoneCalls" />
      <field name="Comments"></field>
    </set>
'''


def write_zone_file(zone_alias, contents):
    zone_file_name = zone_alias + ".xml"
    zone_file = open(zone_file_name, "wt")
    zone_file.write(contents)
    zone_file.close()
    print(f'Contact file "{zone_file_name}" written\n')


if __name__ == '__main__':
    download_file()
    process_contacts()
