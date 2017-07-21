import os, zipfile
import sys
from urllib2 import quote

DURL = "https://data.bl.uk"

BAT_TEMPLATE = """
@echo off
echo This downloader will get {number} files, and use 
echo approximately {size} storage space. Please ensure 
echo that you have enough space. This script will download
echo to a subdirectory called downloads
echo Do you wish to proceed? (Y/N)
set INPUT=
set /P INPUT=Type input: %=%
If /I "%INPUT%"=="y" goto download
If /I "%INPUT%"=="n" goto stopscript
:download
wget.exe -N -P downloads -i "filelist.txt"
:stopscript
echo End.
"""

SH_TEMPLATE = """
#!/bin/bash
function download()
{{
  exec wget -N -P downloads -i "filelist.txt"
}}

echo "This downloader will get {number} files, and use" 
echo "approximately {size} storage space. Please ensure" 
echo "that you have enough space. This script will download" 
echo "to a subdirectory called 'downloads'"
read -n 1 -p "Do you wish to proceed? (Y/N)" resp

case $resp in
  [yY]) echo ; download;;
  *) echo "Exiting" ;;
esac
"""

def sizeof_fmt(num, suffix='B'):
  for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
    if abs(num) < 1024.0:
      return "%3.1f%s%s" % (num, unit, suffix)
    num /= 1024.0
  return "%.1f%s%s" % (num, 'Yi', suffix)

def scan_files(prefix, p):
  url_list = []
  size = 0
  for root, drs, files in os.walk(p):
    # prune dot directories:
    drs = [x for x in drs if not x.startswith(".")]
    for name in files:
      if not name.startswith(".") or name.startswith("~"):
        size += os.path.getsize(os.path.join(root, name))
        frags = [prefix]
        frags += os.path.split(root)
        frags.append(quote(name))
        url_list.append("/".join(frags))
  return url_list, size

if __name__=="__main__":
  if len(sys.argv) != 2:
    print("Usage: python build_downloader_zip.py 'DATASET/DIRECTORYOFFILES'")
    print(" - run this script with the path to the directory of files to be downloaded.")
    print("   it assumes that the first directory is the dataset name.")
    sys.exit(2)
    
  path_to_files = sys.argv[-1]
  dataset, filedir = os.path.split(path_to_files)
  with zipfile.ZipFile(os.path.join(dataset, "{0}_downloader.zip".format(dataset)), "w") as dszip:
    dszip.write(os.path.join("downloaderfiles", "wget.exe"), "wget.exe")
    dszip.write(os.path.join("downloaderfiles","LICENCE"), "LICENCE")
    dszip.write(os.path.join("downloaderfiles","README"), "README")
    urls, rawsize = scan_files(DURL, path_to_files)
    size = sizeof_fmt(rawsize)
    bat_file = BAT_TEMPLATE.format(number=len(urls), size=size)
    sh_file = SH_TEMPLATE.format(number=len(urls), size=size)
    url_file = "\n".join(urls)
    dszip.writestr("download.bat", bat_file.encode("utf-8"))
    dszip.writestr("download.sh", sh_file.encode("utf-8"))
    dszip.writestr("filelist.txt", url_file.encode("utf-8"))
  print("Created {0} to download {1} files, with a total size {2}".format(os.path.join(dataset, "{0}_downloader.zip".format(dataset)), len(urls), size))