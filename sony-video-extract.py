#!/usr/bin/env python3
import os
from datetime import datetime
import argparse
from pathlib import Path
import subprocess
from PIL import Image
from datetime import timedelta

import shutil
import xml.etree.ElementTree as ET
import ffmpeg


def parse_arguments():
  # Create an argument parser
  parser = argparse.ArgumentParser(
      description="Copy media and rename them with creation date")

  # Add the source directory argument
  parser.add_argument("-s", "--source-directory", nargs="?", default=os.getcwd(),
                      help="Source directory path containing the video files (default: current working directory)")

  # Add the destination directory argument
  parser.add_argument("-d", "--destination-directory", nargs="?", default="ProcessedMedia",
                      help="Destination folder path (default: ProcessedMedia)")

  # Add the include subdirectories switch
  parser.add_argument("-r", "--include-subdirectories", action="store_true",
                      default=False, help="Include subdirectories in the source directory")

  # Add the grouping method
  parser.add_argument("-g", "--group-by", nargs="?", default="month",
                      help="Group by [year,month,day,cluster]")

  # Parse the command-line arguments
  args = parser.parse_args()

  # Get the source directory, destination directory, and include subdirectories flag from the arguments
  source_directory = args.source_directory
  destination_directory = args.destination_directory
  include_subdirectories = args.include_subdirectories
  group_by = args.group_by

  return source_directory, destination_directory, include_subdirectories, group_by


class Media:
  video_extensions = (".mp4", ".mkv", ".avi")
  audio_extensions = (".mp3", ".wav", ".flac")
  image_extensions = (".jpg", ".jpeg", ".png", ".gif")
  media_extensions = video_extensions + audio_extensions + image_extensions

  def __init__(self, file_path):
    self.file_path = file_path
    self.filename = os.path.basename(file_path)
    self.file_extension = os.path.splitext(self.filename)[1]
    self.is_media = self.is_media()
    self.media_type = self.determine_media_type()
    self.creation_date = self.extract_creation_date()
    self.destination_group = ""

  def set_additional_attributes(self, destination_group):
    self.destination_group = destination_group

  def extract_creation_date(self):
    # Use ffprobe to extract the creation date metadata
    if self.media_type == "video":
      command = [
          "ffprobe", "-v", "quiet", "-print_format", "compact=print_section=0:nokey=1:escape=csv",
          "-show_entries", "format_tags=creation_time", self.file_path
      ]
      output = subprocess.check_output(command).decode("utf-8").strip()
      # Parse the creation date
      creation_date = datetime.strptime(
          output, "%Y-%m-%dT%H:%M:%S.%fZ")

    elif self.media_type == "image":
      try:
        with Image.open(self.file_path) as img:
          info = img._getexif()
          if info is not None and 36867 in info:
            creation_time_str = info[36867]
            creation_date = datetime.strptime(
                creation_time_str, '%Y:%m:%d %H:%M:%S')

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

  def rename(self, destination_directory, split_by="year"):
    # Extract date components
    year, month, day = self.creation_date.strftime("%Y-%m-%d").split("-")
    time_slug = self.creation_date.strftime("%H_%M_%S")

    # Format the new filename
    new_filename = f"{year}-{month}-{day}-{time_slug}-{self.filename}"

    # Set the destination file path
    if split_by == "month":
      destination_path = os.path.join(
          destination_directory, year, month, new_filename)
    elif split_by == "year":
      destination_path = os.path.join(
          destination_directory, year, new_filename)
    elif split_by == "day":
      destination_path = os.path.join(
          destination_directory, year, month, day, new_filename)
    elif split_by == "cluster":
      destination_path = os.path.join(
          destination_directory, year, self.destination_group, new_filename)
    else:
      destination_path = os.path.join(
          destination_directory, new_filename)
    print(f'Destination Path: {destination_path}')
    return destination_path

    # Rename the file and move it to the destination directory
    # Path(self.file_path).rename(destination_path)
    # print(f'Destination Path: {destination_path}')


def get_media_files(source_directory, include_subdirectories):
  media_files = []
  for root, dirs, files in os.walk(source_directory):
    if not include_subdirectories and root != source_directory:
      continue
    for file in files:
      file_path = os.path.join(root, file)
      media = Media(file_path)
      if media.is_media:
        media_files.append(media)
  return media_files


def rename_videos(source_directory, destination_directory, include_subdirectories, reverse_sort=False):

  media_files = get_media_files(source_directory, include_subdirectories)

  # print(f'Video files found: {media_files}')
  for media in media_files:
    print(f'Media >>> {media.filename}')
    print(f'      >>> {media.file_path}')
    print(f'      >>> {media.file_extension}')
    print(f'      >>> {media.creation_date}')
    print(f'      >>> {media.is_media}')
    media.rename(destination_directory)
    print()

  # for filename in video_files:
  #   file_path = os.path.join(source_directory, filename)
  #   creation_time = os.path.getmtime(file_path)
  #   creation_date = datetime.datetime.fromtimestamp(creation_time)
  #   creation_date_formated = creation_date.strftime("%Y-%m-%d-%H:%M:%S")

  #   print(f"{filename} - {creation_date_formated}")


# # def rename_media_files(source_directory, destination_directory, include_subdirectories):
#     # Create the destination folder if it doesn't exist
#     Path(destination_directory).mkdir(parents=True, exist_ok=True)

#     # Get a list of all media files in the source directory
#     # Process each media file
#     for media in media_files:
#         media.rename(destination_directory)

def group_objects_by_datetime(objects, time_threshold):
  sorted_objects = sorted(objects, key=lambda obj: obj.creation_date)

  grouped_objects = []
  current_group = [sorted_objects[0]]
  # Initialize group number
  group_number = 1
  # Set Group number for first object
  sorted_objects[0].set_additional_attributes(group_number)

  for i in range(1, len(sorted_objects)):
    current_object = sorted_objects[i]
    previous_object = sorted_objects[i-1]
    time_diff = current_object.creation_date - previous_object.creation_date
    if time_diff > time_threshold:
        # Add the current group to the grouped_objects list with the group number
      grouped_objects.append((group_number, current_group))
      current_group = [current_object]
      group_number += 1  # Increment group number
    else:
      current_group.append(current_object)
    current_object.set_additional_attributes(group_number)

  # Add the last group
  grouped_objects.append((group_number, current_group))

  return grouped_objects


if __name__ == "__main__":
  # Parse the command-line arguments
  source_directory, destination_directory, include_subdirectories, group_by = parse_arguments()

  time_threshold = timedelta(hours=24)  # Example time threshold of 1 hour
  media_objects = get_media_files(source_directory, include_subdirectories)
  grouped_objects = group_objects_by_datetime(media_objects, time_threshold)

  # Process or print the grouped objects with group numbers
  for group_number, group_objects in grouped_objects:
    print(f"Group {group_number}:")
    for obj in group_objects:
      print(obj.creation_date, obj.filename, obj.destination_group)
    print("---")  # Print a separator between groups

  print(
      f'Proof, that objects are changed in place. Group of first object is:\n{media_objects[0].destination_group}')
