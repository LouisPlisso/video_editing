Simple python script to edit (keep selections of a video/audio file, and them merge/concat them)

The script is a wrapper around ffmpeg (has to be installed on the system) and works on Mac and Linux.

Here is the help output
```
usage: trim_video.py [-h] [--version] [-q | -v] [-d DELETE_AFTER]
                     [-e EXTENSION] -f DESC_FILE -w OUT_FILE
                     in_file

positional arguments:
  in_file               input file

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -q, --quiet, --silent
                        run as quiet mode
  -v, --verbose         run as verbose mode
  -d DELETE_AFTER, --delete DELETE_AFTER
                        delete intermediate files after completion(default
                        Fallse)
  -e EXTENSION, --extension EXTENSION
                        extension to use (default .mov)
  -f DESC_FILE, --desc-file DESC_FILE
                        description file
  -w OUT_FILE           output file
```
