#!/usr/bin/python
"""Takes an iOS video screen recording from an iPhone XS Max and adds an overlay of an iPhone XS Max device frame, then outputs to a new video file."""

import argparse
import os
import subprocess
import sys
import uuid

NAME = 'iphoneoverlay.py'
VERSION = '1.0.1.20181021'
AUTHOR = 'Carl Windus'
LICENSE = 'Python code is licensed under Apache License 2.0.'
APPLE_COPYRIGHT = 'Apple, the Apple logo, Apple TV, Apple Watch, iPad, iPhone, iPod, iPod touch, iTunes, the iTunes logo, Mac, iMac, MacBook, MacBook Pro, MacBook Air, macOS, and QuickTime are trademarks of Apple Inc., registered in the U.S. and other countries.'

DEVICE_FRAMES_PATH = 'device_frames'

DEVICE_FRAMES = {
    'landscape': {
        'iphoneXSmax': {
            'filename': os.path.join(DEVICE_FRAMES_PATH, 'iPhone-XS-Max-Landscape-Space-Gray.png'),
            'padding': '1748:888',
            'scale': 'transpose=2,scale=1640:-1',
        }
    },
    'portrait': {
        'iphoneXSmax': {
            'filename': os.path.join(DEVICE_FRAMES_PATH, 'iPhone-XS-Max-Portrait-Space-Gray.png'),
            'padding': '888:1748',
            'scale': 'scale=-1:1640',
        }
    },
}

DEVICE_FRAMES_SUPPORTED = list(set(DEVICE_FRAMES['landscape'].keys() + DEVICE_FRAMES['portrait'].keys()))


class DeviceFrameOverlayToVideo():
    @staticmethod
    def overlay(video_in, device_frame, orientation=None, video_out=None, colour=None, remove_tmp=True):
        try:
            # Video to temporarily create in order to overlay image
            tmp_video = '/tmp/{}.mp4'.format(str(uuid.uuid1()).replace('-', ''))

            # Video input
            video_in = os.path.expanduser(video_in) if video_in.startswith('~') else video_in
            video_in = os.path.expandvars(video_in) if '$' in video_in else video_in
            video_in_ext = os.path.splitext(video_in)[1]

            # Device frame to use
            if device_frame in DEVICE_FRAMES_SUPPORTED:
                # Assume an orientation if not provided. Default is portrait
                if not orientation:
                    orientation = 'portrait'
                else:
                    orientation = orientation

                # Create variables used in the ffmpeg command
                padding = DEVICE_FRAMES[orientation][device_frame]['padding']
                scale = DEVICE_FRAMES[orientation][device_frame]['scale']
                device_frame = DEVICE_FRAMES[orientation][device_frame]['filename']
            else:
                print('Please specify a device frame. Supported device frames are listed below.')
                print('\t{}'.format(DEVICE_FRAMES['landscape'].keys()))
                print('\t{}'.format(DEVICE_FRAMES['portrait'].keys()))
                sys.exit(1)

            # Video output (final file)
            if not video_out:
                video_out = video_in.replace(video_in_ext, '_overlay{}'.format(video_in_ext))
            else:
                video_out = os.path.expanduser(video_out) if video_out.startswith('~') else video_out
                video_out = os.path.expandvars(video_out) if '$' in video_out else video_out

            # Background colour
            if colour:
                colour = colour
            else:
                colour = '#000000'

            # Resize and centre
            print('Resizing source video to match device frame {} image size in {} orientation.'.format(os.path.basename(device_frame), orientation))
            resize_cmd = ['/usr/local/bin/ffmpeg', '-y', '-v', 'quiet', '-stats', '-i', video_in, '-vf', '{}:force_original_aspect_ratio=decrease,pad={}:(ow-iw)/2:(oh-ih)/2:color={},setsar=1,format=rgb24'.format(scale, padding, colour), '-codec:a', 'copy', '-an', tmp_video]
            subprocess.call(resize_cmd)

            # Overlay
            overlay_cmd = ['/usr/local/bin/ffmpeg', '-y', '-v', 'quiet', '-stats', '-i', tmp_video, '-i', '"{}"'.format(device_frame), '-filter_complex', '\"overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2\"', '-codec:a', 'copy', '"{}"'.format(video_out)]

            # overlay_cmd doesn't play well unless passed out to shell, so re-format cmd
            overlay_cmd = ' '.join(overlay_cmd)
            print('Overlaying device frame and saving new video to {}'.format(video_out))
            subprocess.call(overlay_cmd, shell=True)

            # Clean up tmp file
            if remove_tmp:
                try:
                    os.remove(tmp_video)
                except Exception:
                    try:
                        os.remove(tmp_video)
                    except Exception:
                        raise

        except Exception as e:
            raise
            print(e)
            sys.exit(1)


class SaneUsageFormat(argparse.HelpFormatter):
    """Sane Help Output. https://stackoverflow.com/a/9643162 (Matt Wilkie)"""
    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []

            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(option_string)

                return '%s %s' % (', '.join(parts), args_string)

            return ', '.join(parts)

    def _get_default_metavar_for_optional(self, action):
        return action.dest.upper()


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=SaneUsageFormat)

    parser.add_argument('-i', '--input',
                        type=str,
                        nargs=1,
                        dest='video_in',
                        metavar='<filename.mp4>',
                        help='Screen recording to add device frame to.',
                        required=True)

    parser.add_argument('-o', '--output',
                        type=str,
                        nargs=1,
                        dest='video_out',
                        metavar='<filename.mp4>',
                        help='Destination video filename.',
                        required=False)

    parser.add_argument('-c', '--bg-colour',  # Queen's English!
                        type=str,
                        nargs=1,
                        dest='bg_colour',
                        metavar='"#ffffff"',
                        help='Background colour. If specifying RGB code, quote the code. For example: "#ffffff"',
                        required=False,
                        default=['#000000'])

    parser.add_argument('--overlay)',
                        type=str,
                        nargs=1,
                        dest='dev_frame',
                        metavar='<device frame>',
                        choices=DEVICE_FRAMES_SUPPORTED,
                        help='Device frame to use as overlay.',
                        required=True,
                        default=['iphoneXSmax'])

    parser.add_argument('--orientation)',
                        type=str,
                        nargs=1,
                        dest='orientation',
                        metavar='<orientation>',
                        choices=['portrait', 'landscape'],
                        help='Orientation of final video. Defaults to portrait.',
                        required=False,
                        default=['portrait'])

    parser.add_argument('-v', '--version',
                        action='version',
                        version='{} version {} by {}. {}\n{}'.format(NAME, VERSION, AUTHOR, LICENSE, APPLE_COPYRIGHT))

    if not len(sys.argv) > 1:
        parser.print_usage()
        sys.exit(1)
    else:
        args = parser.parse_args()
        args = vars(args)

        result = dict()
        video_in = args.get('video_in')[0]
        extension = os.path.splitext(video_in)[1]
        video_out = args['video_out'][0] if args['video_out'] else video_in.replace(extension, '_overlay{}'.format(extension))
        bg_colour = args['bg_colour'][0]
        dev_frame = args['dev_frame'][0]
        orientation = args['orientation'][0]

        result['video_in'] = video_in
        result['video_out'] = video_out
        result['bg_colour'] = bg_colour
        result['dev_frame'] = dev_frame
        result['orientation'] = orientation

        return result


def main():
    args = parse_args()

    recording = DeviceFrameOverlayToVideo()
    recording.overlay(video_in=args['video_in'], device_frame=args['dev_frame'], orientation=args['orientation'], video_out=args['video_out'], colour=args['bg_colour'])


if __name__ == '__main__':
    main()
