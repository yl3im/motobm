import argparse
import json
import typing

import maidenhead
import mobile_codes
from tabulate import tabulate

from templatex import ZONE, CONVENTIONAL_PERSONALITY_RX_TX, CONVENTIONAL_PERSONALITY
from utils import download_file, check_distance, write_text_file


def parse_args() -> argparse.Namespace:
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

    return parser.parse_args()


def filter_list(f_path: str, args: argparse.Namespace, qth_coords: typing.Tuple[float, float]) -> typing.Tuple[
    typing.List[dict], dict]:
    with open(f_path, "r") as f:
        json_list = json.load(f)

    sorted_list = sorted(json_list, key=lambda k: (k['callsign'], int(k["id"])))

    filtered_list = []
    existing = {}

    for item in sorted_list:
        band = args.band
        rx = item['rx']
        if not ((band == 'vhf' and rx.startswith('1')) or (band == 'uhf' and rx.startswith('4'))):
            continue

        if args.type == 'mcc':
            is_starts = False

            if type(args.mcc) is list:
                for mcc in args.mcc:
                    if str(item['id']).startswith(mcc):
                        is_starts = True
            else:
                if str(item['id']).startswith(args.mcc):
                    is_starts = True

            if not is_starts:
                continue

        if (args.type in ['qth', 'gps']) and check_distance(qth_coords, (item['lat'], item['lng'])) > args.radius:
            continue

        if args.pep and (not str(item['pep']).isdigit() or str(item['pep']) == '0'):
            continue

        if args.six and not len(str(item['id'])) == 6:
            continue

        if item['callsign'] == '':
            item['callsign'] = item['id']

        item['callsign'] = item['callsign'].split()[0]

        if any((existing['rx'] == item['rx'] and existing['tx'] == item['tx'] and existing['callsign'] == item[
            'callsign']) for existing in filtered_list):
            continue

        if not item['callsign'] in existing:
            existing[item['callsign']] = 0

        existing[item['callsign']] += 1
        item['turn'] = existing[item['callsign']]

        filtered_list.append(item)

    return filtered_list, existing


def process_channels(args: argparse.Namespace, filtered_list: typing.List[dict], existing: typing.Dict) -> None:
    channel_chunks = [filtered_list[i:i + args.zone_capacity] for i in range(0, len(filtered_list), args.zone_capacity)]
    chunk_number = 0

    for chunk in channel_chunks:
        channels = ''
        chunk_number += 1
        output_list = []

        for item in chunk:
            channels += format_channel(item, existing, output_list)

        print('\n',
              tabulate(output_list, headers=['Callsign', 'RX', 'TX', 'CC', 'City', 'Last seen', 'URL'],
                       disable_numparse=True),
              '\n')

        if len(channel_chunks) == 1:
            zone_alias = args.name
        else:
            zone_alias = f'{args.name} #{chunk_number}'

        zone_alias += ".xml"

        write_text_file(zone_alias, ZONE.format(zone_alias=zone_alias, channels=channels))
        print(f'Zone file "{zone_alias}" written.\n')


def format_channel(item: typing.Dict, existing: typing.Dict, output_list: typing.List[typing.List]) -> str:
    callsign = item['callsign']

    if existing[callsign] == 1:
        ch_alias = callsign
    else:
        ch_alias = f"{callsign} #{item['turn']}"

    ch_rx = item['rx']
    ch_tx = item['tx']
    ch_cc = item['colorcode']

    output_list.append([
        ch_alias, ch_rx, ch_tx, ch_cc, item['city'], item['last_seen'],
        f"https://brandmeister.network/?page=repeater&id={item['id']}"
    ])

    args = dict(
        ch_alias=ch_alias, ch_cc=ch_cc, ch_rx=ch_rx, ch_tx=ch_tx
    )

    if item['rx'] == item['tx']:
        return CONVENTIONAL_PERSONALITY_RX_TX.format(**args)
    return CONVENTIONAL_PERSONALITY.format(**args)


def main():
    args = parse_args()

    bm_url = 'https://api.brandmeister.network/v2/device'
    bm_file = 'BM.json'

    print(f'Downloading from {bm_url}')
    if download_file(bm_file, bm_url, args.force):
        print(f'Saved to {bm_file}')
    else:
        print(f'File {bm_file} already exists. Skip.')

    if args.type == 'qth':
        qth_coords = maidenhead.to_location(args.qth, center=True)
    elif args.type == 'gps':
        qth_coords = (args.lat, args.lng)
    else:
        qth_coords = (0, 0)

    if args.mcc and not str(args.mcc).isdigit():
        args.mcc = mobile_codes.alpha2(args.mcc)[4]

    filtered_list, existing = filter_list(bm_file, args, qth_coords)
    process_channels(args, filtered_list, existing)


if __name__ == '__main__':
    main()
