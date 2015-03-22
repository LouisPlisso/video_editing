#!/usr/bin/env python
'Module to trim out part of a video file'

from __future__ import division, print_function
import sys
import os
import argparse
import logging
import subprocess
import tempfile

VERSION = '%(prog)s 1.1'

# for interactive call: do not add multiple times the handler
if 'LOG' not in locals():
    LOG = None
LOG_LEVEL = logging.ERROR
FORMATER_STRING = ('%(asctime)s - %(filename)s:%(lineno)d - '
                   '%(levelname)s - %(message)s')

def configure_log(level=LOG_LEVEL, log_file=None):
    'Configure logger'
    if LOG:
        LOG.setLevel(level)
        return LOG
    log = logging.getLogger('%s log' % os.path.basename(__file__))
    if log_file:
        handler = logging.FileHandler(filename=log_file)
    else:
        handler = logging.StreamHandler(sys.stderr)
    log_formatter = logging.Formatter(FORMATER_STRING)
    handler.setFormatter(log_formatter)
    log.addHandler(handler)
    log.setLevel(level)
    return log

LOG = configure_log()

EXTENSION = '.mov'

def run_command(command):
    'Return the process object after wait call on shell command'
    LOG.debug('Running command: %s', command)
    try:
        process = subprocess.Popen(command, shell=True)
        process.wait()
        return process
    except OSError, msg:
        LOG.exception(msg)

def concat_interm_files(all_files, out_file, delete_after):
    'Concat all intermediate files and delete them if required'
    list_file = tempfile.NamedTemporaryFile(prefix='list_file_', dir='.',
                                            suffix='.txt', delete=False)
    LOG.info('list file is: %s', list_file.name)
    with open(list_file.name, 'w') as list_file_stream:
        for file_name in all_files:
            list_file_stream.write("file '%s'\n" % file_name)
    process = run_command('/usr/local/bin/ffmpeg -f concat -i %s -c copy -y %s'
                          % (list_file.name, out_file))
    if process.returncode != 0:
        LOG.error('could concatene files into %s', out_file)
        return False
    LOG.info('output written to: %s', out_file)
    if delete_after:
        for file_name in all_files:
            os.remove(file_name)
        os.remove(list_file.name)
    return True

def do_job(in_file, out_file, times_to_keep,
           delete_after=False, extension=EXTENSION):
    'Cut and concat all intermediate files'
    file_pattern = 'trim'
    all_files = []
    for index, (start, end) in enumerate(times_to_keep):
        prefix = '_'.join((file_pattern, str(index), ''))
        cur_file = tempfile.NamedTemporaryFile(prefix=prefix,
                                               suffix=extension,
                                               dir='.',
                                               delete=False)
        LOG.info('working on cur_file: %s', cur_file.name)
        process = run_command("/usr/local/bin/ffmpeg "
                              "-i %s -ss '%s' -to '%s' -y %s 2>&1"
                              % (in_file, start, end, cur_file.name))
        if process.returncode != 0:
            LOG.error('could not work on %s', cur_file)
            continue
        all_files.append(cur_file.name)
    return concat_interm_files(all_files, out_file, delete_after)

def parse_desc_file(desc_file):
    '''Return the list of times to keep
    >>> expected_times = [
    ... ('0:02', '0:41'),
    ... ('0:49', '1:39'),
    ... ('1:48', '2:36'),
    ... ('2:53', '3:07'),
    ... ('3:31', '3:38'),
    ... ('3:49', '4:55'),
    ... ('5:07', '5:34'),
    ... ('6:22', '6:48'),
    ... ('6:58', '7:40'),
    ... ('7:42', '7:49'),
    ... ('8:29', '8:35'),
    ... ('8:43', '9:24'),
    ... ('10:15', '11:16'),
    ... ('11:18', '11:54')]
    >>> times_to_keep = parse_desc_file([
    ... '0:02 0:41',
    ... '0:49 1:39',
    ... '1:48 2:36',
    ... '2:53 3:07',
    ... '   ',
    ... 'xx',
    ... 'a b c',
    ... '3:31 3:38',
    ... '   3:49 4:55',
    ... '5:07    5:34',
    ... '6:22 6:48   ',
    ... '6:58 7:40',
    ... '7:42 7:49',
    ... '8:29 8:35',
    ... '8:43 9:24',
    ... '10:15 11:16',
    ... '11:18 11:54',
    ... ''])
    >>> times_to_keep == expected_times
    True
    '''
    times_to_keep = []
    for line in desc_file:
        try:
            start, end = line.strip().split()
        except ValueError:
            LOG.error('Could not parse line: %s', line)
            continue
        times_to_keep.append((start, end))
    return times_to_keep

def create_parser():
    'Return the argument parser'
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help=argparse.SUPPRESS)
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument('-q', '--quiet', '--silent', dest='quiet',
                           action='store_true', default=False,
                           help='run as quiet mode')
    verbosity.add_argument('-v', '--verbose', dest='verbose',
                           action='store_true', default=False,
                           help='run as verbose mode')
    parser.add_argument('-d', '--delete', dest='delete_after', default=False,
                        help=('delete intermediate files after completion '
                              '(default False)'))
    parser.add_argument('-e', '--extension', dest='extension',
                        default=EXTENSION,
                        help='extension to use (default %s)' % EXTENSION)
    parser.add_argument('-f', '--desc-file', dest='desc_file', required=True,
                        help='description file', type=argparse.FileType('r'))
    parser.add_argument('-w', dest='out_file', required=True,
                        help='output file', type=argparse.FileType('w'))
    parser.add_argument('in_file', help='input file',
                        type=argparse.FileType('r'))
    return parser

def main(argv=None):
    'Program wrapper'
    if argv is None:
        argv = sys.argv[1:]
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.verbose:
        LOG.setLevel(logging.INFO)
    if args.quiet:
        LOG.setLevel(logging.CRITICAL)
    if args.debug:
        LOG.setLevel(logging.DEBUG)
    if not (args.out_file.name.lower().endswith(args.extension)
            and args.in_file.name.lower().endswith(args.extension)):
        parser.error('Provide input/output file with extension according to %s'
                     % args.extension)
    times_to_keep = parse_desc_file(args.desc_file)
    if do_job(args.in_file.name, args.out_file.name, times_to_keep,
              delete_after=args.delete_after, extension=args.extension):
        return 0
    else:
        return 1

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    sys.exit(main())

