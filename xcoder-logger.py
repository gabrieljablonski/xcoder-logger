#!/usr/bin/python3
import os
import logging
from logging.handlers import RotatingFileHandler
from time import sleep

from subpiper import subpiper


DEFAULT_MAX_FILE_SIZE = 2*int(2**20)  # 2 MiB
DEFAULT_MAX_FILE_COUNT = 5
DEFAULT_BASE_LOG_PATH = "/viacast/{}/logs"


if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='XCoder Service Logger', add_help=False)
  required = parser.add_argument_group('required arguments')
  optional = parser.add_argument_group('optional arguments')

  required.add_argument('-s', '--service', help='xcoder service name.', required=True)

  optional.add_argument(
    '-h',
    '--help',
    action='help',
    default=argparse.SUPPRESS,
    help='show this message.',
  )
  optional.add_argument(
    '-p', 
    '--path', 
    help='path where logs will be written. defaults to "/viacast/<service>/logs/". directory is created if it does not exist.',
  )
  optional.add_argument(
    '-m', 
    '--max-file-size', 
    type=int,
    help='max log file size. defaults to 2 MiB.'
  )
  optional.add_argument(
    '-n', 
    '--max-file-count', 
    type=int,
    help='max log file count. old files are named as "<log-path>/<service>.log.<n>". defaults to 5.'
  )
  optional.add_argument(
    '-d',
    '--show-timestamp',
    action='store_true',
    help='add a timestamp to log messages.'
  )
  optional.add_argument(
    '-l',
    '--show-log-level',
    action='store_true',
    help='add [INFO] to stdout messages and [ERROR] for stderr.'
  )
  optional.add_argument(
    '-c', 
    '--no-console', 
    action='store_true',
    help='do not write logs to stdout.'
  )
  optional.add_argument(
    '-t', 
    '--write-tmp', 
    action='store_true', 
    help='also write logs to "/tmp/<service>.log".'
  )

  args = parser.parse_args()
  service = args.service
  base_log_path = args.path or DEFAULT_BASE_LOG_PATH.format(service)
  max_file_size = args.max_file_size or DEFAULT_MAX_FILE_SIZE
  max_file_count = args.max_file_size or DEFAULT_MAX_FILE_COUNT
  show_timestamp = args.show_timestamp
  show_log_level = args.show_log_level
  write_stdout = not args.no_console
  write_tmp = args.write_tmp

  if not os.path.exists(base_log_path):
    os.mkdir(base_log_path)

  handler = RotatingFileHandler(
    "{}/{}.log".format(base_log_path, service), 
    maxBytes=max_file_size,
    backupCount=max_file_count,
    encoding='utf8'
  )

  handlers = [handler]
  if write_tmp:
    tmp_path = "/tmp/{}.log".format(service)
    tmp = logging.FileHandler(
      "/tmp/{}.log".format(service), 
      encoding='utf8'
    )
    handlers.append(tmp)
  if write_stdout:
    handlers.append(logging.StreamHandler())

  log_format = u'%(message)s'
  if show_log_level:
    log_format = u'[%(levelname)-5s] ' + log_format
  if show_timestamp:
    log_format = u'[%(asctime)s.%(msecs)03d] ' + log_format

  logging.basicConfig(
    handlers=handlers,
    level=logging.INFO,
    format=log_format,
    datefmt='%Y-%m-%dT%H:%M:%S'
  )
  logging._defaultFormatter = logging.Formatter(u'%(message)s')

  def stdout_cb(line):
    logging.info(line)
  def stderr_cb(line):
    logging.error(line)

  if write_tmp:
    logging.info('Will write to "/tmp/{}.log"'.format(service))

  command = "/viacast/{}/sbin/{}.sh".format(service, service)
  logging.info("Running '{}'...".format(command))
  retcode, *_ = subpiper(
    cmd=command,
    stdout_callback=stdout_cb,
    stderr_callback=stderr_cb,
  )
  logging.info("Process exited with code {}.".format(retcode))
