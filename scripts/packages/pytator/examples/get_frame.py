#!/usr/bin/env python3

"""
Fetch frame(s) and save to disk

Example usage:

# Saves 400.jpg and 500.jpg from a single request
python3 examples/get_frame.py --url <SERVER>/rest --project <proj>  --token <TOKEN> --output {:d}.jpg --detile 10323 400 500

# Saves 400.jpg
python3 examples/get_frame.py --url <SERVER>/rest --project <proj>  --token <TOKEN> --output 400.jpg 10323 400

# Saves tile.jpg (400,500,600,700)
python3 examples/get_frame.py --url <SERVER>/rest --project <proj>  --token <TOKEN> --output tile.jpg 10323 400 500 600 700

"""

import argparse
import pytator
import cv2

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    pytator.tator.cli_parser(parser)
    parser.add_argument('--output', help="file name or format string to output to.")
    parser.add_argument('--detile', action='store_true')
    parser.add_argument('media', type=int)
    parser.add_argument('frames', nargs='+', type=int)
    args = parser.parse_args()

    tator = pytator.Tator(args.url, args.token, args.project)

    if args.detile:
        code,bgr_data = tator.GetFrame.get_bgr(args.media, args.frames)
        if code == 200:
            if args.output:
                for idx,frame in enumerate(bgr_data):
                    output_file=args.output.format(args.frames[idx])
                    print(f"Outputing to {output_file}")
                    cv2.imwrite(output_file, frame)
        else:
            print("ERROR {code}")
    else:
        code,img_data = tator.GetFrame.get_encoded_img(args.media, args.frames)
        if code == 200:
            if args.output:
                with open(args.output, 'wb') as fp:
                    print(f"Outputing to {args.output}")
                    fp.write(img_data)
    

