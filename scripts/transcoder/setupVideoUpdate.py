#!/usr/bin/env python3

import pytator
import os
import sys
import json

RESOLUTIONS=[144,360,480,720,1080]
MAX_RESOLUTION=max(RESOLUTIONS)

def determine_update(media_element):
    height = media_element['height']
    media_files = media_element['media_files']
    streaming_files = []
    if media_files:
        streaming_files = media_files.get('streaming',[])
    expected=[res for res in RESOLUTIONS if res < height]
    if height <= MAX_RESOLUTION:
        expected.append(height)
    print(f"Given {height}; we expect {expected}")
    actual=[info['resolution'][0] for info in streaming_files if 'resolution' in info]
    missing = [res for res in expected if res not in actual]
    print(f"Missing resolutions = {missing}")

    if media_files.get('audio',None):
        audio_required=False
    else:
        audio_required=True
    print(f"Audio Required = {audio_required}")
    return missing, audio_required
        
if __name__ == '__main__':
    media_ids = os.getenv('TATOR_MEDIA_IDS')
    print(f"processing = {media_ids}")
    media_ids = [int(m) for m in media_ids.split(',')]
    rest_svc = os.getenv('TATOR_API_SERVICE')
    work_dir = os.getenv('TATOR_WORK_DIR')
    token=os.getenv('TATOR_AUTH_TOKEN')
    project_id=os.getenv('TATOR_PROJECT_ID')
    
    tator=pytator.Tator(rest_svc, token, project_id)
    work=[]

    for media_id in media_ids:
        media_element=tator.Media.get(media_id)
        missing, audio_required=determine_update(media_element)
        if len(missing) == 0 and audio_required is False:
            continue
        if len(missing) == 0:
            missing = ['audio']

        video_dir = os.path.join(work_dir,
                                 str(media_element['id']))
        video_fp = os.path.join(work_dir,
                                str(media_element['id']),
                                media_element['name'])
        dest_dir = os.path.join(video_dir,
                                'scratch')
        os.makedirs(dest_dir, exist_ok=True)
        tator.Media.downloadFile(media_element, video_fp)
        work.append({"id": str(media_element['id']),
                     "resolutions": ",".join(str(x) for x in missing), # must be string for cli
                     "source": video_fp,
                     "dest": dest_dir})
    with open('/work/update-list.json', 'w') as work_f:
        json.dump(work, work_f)
    
