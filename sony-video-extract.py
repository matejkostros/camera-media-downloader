#!/usr/bin/env python3

import os
import platform
from datetime import datetime
import argparse
import subprocess
from datetime import timedelta
from PIL import Image


import shutil
import xml.etree.ElementTree as ET


def parse_arguments():
  # Create an argument parser
  parser = argparse.ArgumentParser(description="Copy media and rename them with creation date")

  # Add the source directory argument
  parser.add_argument("-s",
                      "--source-directory",
                      nargs="?",
                      default=os.getcwd(),
                      help="Source directory path containing the video files (default: current working directory)")

  # Add the destination directory argument
  parser.add_argument("-d",
                      "--destination-directory",
                      nargs="?",
                      default="ProcessedMedia",
                      help="Destination folder path (default: ProcessedMedia)")

  # Add the include subdirectories switch
  parser.add_argument("-r",
                      "--include-subdirectories",
                      action="store_true",
                      default=False,
                      help="Include subdirectories in the source directory")

  # Add the groupping range
  parser.add_argument("-t",
                      "--timeframe",
                      nargs="?",
                      default=24,
                      type=int,
                      help="How many hours should be used when groupping media together")

  # Add the grouping method
  parser.add_argument("-g",
                      "--group-by",
                      nargs="?",
                      default="month",
                      help="Group media files by [year,month,day,cluster]")

  # Add the include subdirectories switch
  parser.add_argument("-l",
                      "--list-only",
                      action="store_true",
                      default=False,
                      help="If set, only script will only list media which will be processed")

  # Optimize media file size with ffmpeg or image convert
  parser.add_argument("-o",
                      "--optimize-size",
                      nargs="?",
                      default="none",
                      help=f"If set, it converts your media files to be more space efficient with"
                      f"minimal impact on media quality. Options: [none(default)|all|audio|video|image]")

  parser.add_argument("-q",
                      "--quality",
                      nargs="?",
                      default=100,
                      type=int,
                      help=f"Configures the quality of media convertion in percentage")

  # Parse the command-line arguments
  args = parser.parse_args()

  # Get the source directory, destination directory, and include subdirectories flag from the arguments
  source_directory = args.source_directory
  destination_directory = args.destination_directory
  include_subdirectories = args.include_subdirectories
  timeframe = timedelta(hours=args.timeframe)
  group_by = args.group_by
  list_only = args.list_only
  optimize_size = args.optimize_size
  quality = args.quality

  return (source_directory, destination_directory, include_subdirectories, timeframe, group_by, list_only,
          optimize_size, quality)


class InvalidDatetimeAttributeException(Exception):
  pass


class Media:
  video_extensions = (".mp4", ".mkv", ".avi")
  audio_extensions = (".mp3", ".wav", ".flac")
  image_extensions = (".jpg", ".jpeg", ".png", ".gif")
  media_extensions = video_extensions + audio_extensions + image_extensions

  def __init__(self, file_path, destination_root):
    self.file_path = file_path
    self.destination_root = destination_root
    self.filename = os.path.basename(file_path)
    self.filename_clean, self.file_extension = os.path.splitext(self.filename)
    self.is_media = self.is_media()
    self.media_type = self.determine_media_type()
    self.creation_date = self.extract_creation_date()
    self.destination_group = 1

  def set_destination_group(self, destination_group):
    self.destination_group = destination_group

  def extract_creation_date(self):
    # Use ffprobe to extract the creation date metadata
    if self.media_type == "video":
      command = [
          "ffprobe", "-v", "quiet", "-print_format", "compact=print_section=0:nokey=1:escape=csv", "-show_entries",
          "format_tags=creation_time", self.file_path
      ]
      output = subprocess.check_output(command).decode("utf-8").strip()
      # Parse the creation date
      creation_date = datetime.strptime(output, "%Y-%m-%dT%H:%M:%S.%fZ")

    elif self.media_type == "image":
      try:
        with Image.open(self.file_path) as img:
          info = img._getexif()
          if info is not None and 36867 in info:
            creation_time_str = info[36867]
            creation_date = datetime.strptime(creation_time_str, '%Y:%m:%d %H:%M:%S')

      except (IOError, OSError, AttributeError):
        creation_time = os.path.getmtime(self.file_path)
        creation_date = datetime.fromtimestamp(creation_time)

    else:
      creation_time = os.path.getmtime(self.file_path)
      creation_date = datetime.fromtimestamp(creation_time)

    return creation_date

  def determine_media_type(self):
    file_extension = self.file_extension.lower()
    if file_extension in Media.video_extensions:
      return "video"
    elif file_extension in Media.audio_extensions:
      return "audio"
    elif file_extension in Media.image_extensions:
      return "image"
    else:
      return "unknown"

  def is_media(self):
    file_extension = self.file_extension.lower()
    if file_extension in Media.media_extensions:
      return True
    else:
      return False

  def process_video(self, input_file, output_file, quality):
    operating_system = platform.system()

    if operating_system == "Windows":
      ffmpeg_executable = r'C:\Users\matej.kostros\OneDrive - ZOOM International a.s\Desktop\Software\ffmpeg.exe'
    else:
      ffmpeg_executable = "ffmpeg"
    # stream = ffmpeg.input(input_file)
    # stream = ffmpeg.output(stream,
    #                        output_file,
    #                        vcodec="hevc",
    #                        vtag="hvc1",
    #                        crf=20,
    #                        preset='fast',
    #                        pix_fmt='yuv420p',
    #                        acodec="aac",
    #                        audio_bitrate="192k"
    #                        )
    # ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    ffmpeg_cmd = [
        ffmpeg_executable, "-y", "-i", input_file, "-c:v", "hevc", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-crf", "20", output_file
    ]

    # Execute the ffmpeg command
    subprocess.run(ffmpeg_cmd)

  def process_image(self, input_file, output_file, quality=90):
    if "png" in self.file_extension.lower():
      with Image.open(input_file) as image:
        image.save(output_file, format='PNG')
    else:
      image = Image.open(input_file)
      image.save(output_file, optimize=True, quality=quality)

  def file_copy(self, source, destination):
    shutil.copy2(source, destination)

  def destination_filename(self):
    # Format the new filename
    destination_filename = f"{self.creation_date.strftime('%Y-%m-%d-%H_%M_%S')}-" \
                   f"{self.filename_clean.lstrip('_')}{self.file_extension}"

    return destination_filename

  def destination_path(self, group_by):

    year, month, day = self.creation_date.strftime("%Y-%m-%d").split("-")
    destination = self.destination_root

    # Set the destination directory
    if group_by == "month":
      destination_folder = os.path.join(destination, year, month)
    elif group_by == "year":
      destination_folder = os.path.join(destination, year)
    elif group_by == "day":
      destination_folder = os.path.join(destination, year, month, day)
    elif group_by == "cluster":
      destination_folder = os.path.join(destination, year, f'group-{self.destination_group}')
    else:
      destination_folder = os.path.join(destination)

    return os.path.join(destination_folder, self.destination_filename())

  def load(self, group_by, optimize_size, quality):
    source = self.file_path
    print(f'Loading: {source}', end='\t')
    destination_path = self.destination_path(group_by)
    destination_dir = os.path.dirname(destination_path)
    os.makedirs(destination_dir, exist_ok=True)

    if optimize_size != "none":
      if self.media_type == optimize_size == 'video':
        self.process_video(source, destination_path, quality)
      elif self.media_type == optimize_size == 'image':
        self.process_image(source, destination_path, quality)
      else:
        self.file_copy(source, destination_path)
    else:
      self.file_copy(source, destination_path)

    print(f'Finished: {destination_path}')


def sort_media_objects(media_objects):
  for obj in media_objects:
    if not hasattr(obj, 'creation_date') and not isinstance(obj.creation_date, datetime):
      raise InvalidDatetimeAttributeException(f"Object {obj} has an invalid datetime attribute.")
  return sorted(media_objects, key=lambda obj: obj.creation_date)


def get_media_files(source_directory, destination_directory, include_subdirectories):
  media_files = []
  for root, dirs, files in os.walk(source_directory):
    if not include_subdirectories and root != source_directory:
      continue
    for file in files:
      file_path = os.path.join(root, file)
      media = Media(file_path, destination_directory)
      if media.is_media:
        media_files.append(media)

  return sort_media_objects(media_files)


def group_media_by_datetime(objects, time_threshold):
  sorted_objects = sort_media_objects(objects)

  grouped_objects = []
  current_group = [sorted_objects[0]]
  # Initialize group number
  group_number = 1

  for i in range(1, len(sorted_objects)):
    current_object = sorted_objects[i]
    previous_object = sorted_objects[i - 1]
    time_diff = current_object.creation_date - previous_object.creation_date
    if time_diff > time_threshold:
      # Add the current group to the grouped_objects list with the group number
      grouped_objects.append((group_number, current_group))
      current_group = [current_object]
      group_number += 1  # Increment group number
    else:
      current_group.append(current_object)
    current_object.set_destination_group(destination_group=group_number)

  # Add the last group
  grouped_objects.append((group_number, current_group))

  return grouped_objects


if __name__ == "__main__":
  # Parse the command-line arguments
  source_directory, destination_directory, include_subdirectories, \
    timeframe, group_by, list_only, optimize_size, quality = parse_arguments()

  time_threshold = timedelta(hours=24)  # Example time threshold of 1 hour
  media_objects = get_media_files(source_directory, destination_directory, include_subdirectories)
  group_media_by_datetime(media_objects, timeframe)

  # Process the grouped objects with group numbers
  for media in media_objects:
    media.load(group_by, optimize_size, quality)
    # print(f'Source: {media.file_path}, \t Destination {media.destination_path}')

  # # Media Destination
  # for media in media_objects:
  #   print(f'{media.destination_path}')
