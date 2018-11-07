#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
# test.py
#
# G. Thomas
# 2018
#-------------------------------------------------------------------------------

import argparse

from turnout_service import TurnoutService

def __generate_cli():
    '''
    Generate command line arguments
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c',
        '--config',
        default = 'config.yml',
        help = 'Application configuration')

    return parser.parse_args()

if __name__ == '__main__':
    # 1) Setup command line arguments
    args = __generate_cli()

    # 2) Create service
    service = TurnoutService()

    # 3) Run the service, this is a blocking call
    service.run(args.config)





