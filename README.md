# Media Extractor

Use this python utility to load media files from your sd card and categorize them
Example usage:

**Windows**
```powershell
python.exe sony-video-extract.py --include-subdirectories -s "C:\Users\matej.kostros\Downloads\mediaDump" -d "C:\Users\matej.kostros\Downloads\mediaDumpProcessed" -g cluster -t "24" -o "video"

```
**Linux**
```bash
python sony-video-extract.py --include-subdirectories -s "/mnt/media/sdcard" -d "~/Media/" -g cluster -t "24" -o "video"
```

**Usage**
```
python3 sony-video-extract.py -h
usage: sony-video-extract.py [-h] [-s [SOURCE_DIRECTORY]] [-d [DESTINATION_DIRECTORY]] [-r] [-t [TIMEFRAME]] [-g [GROUP_BY]] [-l] [-o [OPTIMIZE_SIZE]] [-q [QUALITY]]

Copy media and rename them with creation date

options:
  -h, --help            show this help message and exit
  -s [SOURCE_DIRECTORY], --source-directory [SOURCE_DIRECTORY]
                        Source directory path containing the video files (default: current working directory)
  -d [DESTINATION_DIRECTORY], --destination-directory [DESTINATION_DIRECTORY]
                        Destination folder path (default: ProcessedMedia)
  -r, --include-subdirectories
                        Include subdirectories in the source directory
  -t [TIMEFRAME], --timeframe [TIMEFRAME]
                        How many hours should be used when groupping media together
  -g [GROUP_BY], --group-by [GROUP_BY]
                        Group media files by [year,month,day,cluster]
  -l, --list-only       If set, only script will only list media which will be processed
  -o [OPTIMIZE_SIZE], --optimize-size [OPTIMIZE_SIZE]
                        If set, it converts your media files to be more space efficient withminimal impact on media quality. Options: [none(default)|all|audio|video|image]
  -q [QUALITY], --quality [QUALITY]
                        Configures the quality of media convertion in percentage
```
**Prerequisites for Linux**
```
python -m pip install pillow
sudo apt install ffmpeg
```
