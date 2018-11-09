#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
# turnout_service.py
#
# G. Thomas
# 2018
#-------------------------------------------------------------------------------

import logging
import os
import signal
import sys
import time
import touchphat
import yaml

from hw_low_level import Servo
from hw_low_level.gpio import GPOProviderPWM
from hw_low_level.pwm import PWMProviderPCA9685
from hw_railroad import Turnout
from pca9685_driver import Device as PCA9685
from threading import Event

class TurnoutService(object):
    '''
    Service for controlling model railroad turnouts
    TODO: A base service class can likely be extracted
    '''
    WAIT_TIMEOUT =  0.02
    EXIT_TIMEOUT =  5.0

    CONFIG_FILE_YAML_READ_EXIT =    1
    CONFIG_FILE_EXISTENCE_EXIT =    2
    CONFIG_LOGGING_READ_EXIT =      3
    CONFIG_SERVICE_READ_EXIT =      4
    CONFIG_SERVICE_ERROR_EXIT =     5
    SHUTDOWN_TIMEOUT_EXIT =         6

    def __init__(self):
        '''
        '''
        self.__logger = logging.getLogger(__name__)

        self.__is_alive = True

        self.__update_rate = TurnoutService.WAIT_TIMEOUT

        # Turnout dictionary so that it's possible to nicely address them
        self.__turnouts = {}

        self.__waiter = Event()
        self.__exit_waiter = Event()

    def run(self, path):
        '''
        Service runner

        Process the config file to create the HW object graph and init the
        communication infrastructure
        Sets up the OS signal handling
        Starts non-exiting run loop that operates the connected turnouts

        This is a blocking call that will only exit if correctly signalled by
        the OS
        '''
        # 1) Process config
        self.__process_config(path)

        # 2) Setup termination handler
        signal.signal(signal.SIGINT, self.__signal_handler)

        # 3) Start run loop
        while self.__is_alive:
            timeout = None

            # Run through each of the turnouts to see if there is work to be done
            for turnout in self.__turnouts.values():
                if turnout.operate(time.time()):
                    timeout = self.__update_rate

            # Wait for an event to wake us up early or process work on a regular
            # interval by using the timeout
            if self.__waiter.wait(timeout):
                # clear the flag so that we eventually do work again
                self.__waiter.clear()

        # 4) run shutdown process
        self.__shutdown()

        # 5) signal process termination
        self.__exit_waiter.set()

    def __process_config(self, path):
        '''
        Process the configuration file to setup logging and the service
        '''
        # 1) Read the file
        config = self.__read_config_file(path)

        try:
            # 2) Process the logging configuration
            self.__configure_logging(config['logging'])
        except Exception as e:
            self.__logger.error(e)

            sys.exit(self.CONFIG_LOGGING_READ_EXIT)

        try:
            # 3) Process the service configuration
            self.__configure_service(config['services']['turnout'])
        except Exception as e:
            self.__logger.error(e)

            sys.exit(self.CONFIG_SERVICE_READ_EXIT)

    def __read_config_file(self, path):
        '''
        Read the service configuration file for furhter processing of the
        logging and service configuration details
        '''
        if os.path.exists(path):
            with open(path, 'r') as config_file:
                try:
                    return yaml.load(config_file)
                except yaml.YAMLError as exc:
                    self.__logger.error(exc)

                    sys.exit(self.CONFIG_FILE_YAML_READ_EXIT)
        else:
            self.__logger.error(f'Config file {path} does not exist')

            sys.exit(self.CONFIG_FILE_EXISTENCE_EXIT)

    def __configure_logging(self, config):
        '''
        Configure the logging output

        Loads the logging configuration file to determine how log calls are
        processed
        '''
        try:
            logging.config.dictConfig(config)
        except:
            logging.basicConfig(level=logging.DEBUG)
            logging.error('Oh shit... logging is borked')

    def __configure_service(self, config):
        '''
        Configure the service , exit with CONFIG_SERVICE_READ_EXIT if there is
        an error

        TODO: This is probably a virtual method in the base class as each
              service will have a different configuration
        '''
        try:
            self.__update_rate = config['update-rate']

            for turnout_config in config['turnouts']:
                turnout_name = turnout_config['name']

                self.__logger.debug(f'Turnout: {turnout_name}')

                outputs = {}

                for output in turnout_config['outputs']:
                    output_name = output['name']

                    self.__logger.debug(f' - Output: {output_name}')

                    output_type = output['type']

                    self.__logger.debug(f'   - Type: {output_type}')

                    if output_type == 'PCA9685':
                        output_address = output['address']

                        self.__logger.debug(f'   - Address: {output_address}')

                        output_device = PCA9685(output_address)

                        output_pin = output['pin']

                        self.__logger.debug(f'   - Pin: {output_pin}')

                        output_pwm_provider = PWMProviderPCA9685(
                            output_device,
                            output_pin)

                        outputs.update({output_name: output_pwm_provider})

                    else:
                        raise ValueError(f'Cannot build output: {output_type}')

                # Servo
                turnout_servo = Servo(outputs['servo'])

                # Frog
                turnout_frog = GPOProviderPWM(outputs['frog'])

                turnout = Turnout(
                    turnout_servo,
                    turnout_frog,
                    turnout_config['angles']['main'],
                    turnout_config['angles']['diverging'],
                    config['angular-speed'])
                turnout.state_changed += self.__transmit

                self.__turnouts.update({turnout_name: turnout})

            # 4) communications
            touchphat.auto_leds = False
            touchphat.on_touch(['A','B','C','D'], self.__receive)

        except:
            self.__logger.error('Something bad happened while processing the \
                service config')

            sys.exit(self.CONFIG_SERVICE_ERROR_EXIT)

    def __receive(self, data):
        '''
        Service receive handler
        '''
        turnout = data.name

        self.__logger.debug(f'RX: {turnout}')

        if turnout in self.__turnouts.keys():
            self.__logger.info('Moving turnout: {turnout}')

            self.__turnouts[turnout].change_route(time.time())

            self.__waiter.set()

    def __transmit(self, data):
        '''
        Service transmit handler
        '''
        self.__logger.info(f'TX: {data}')

    def __signal_handler(self, sig, frame):
        '''
        Handle shutdown signal gracefully
        '''
        self.__logger.info('Received signal to shutdown')

        # 1) Mark run loop as dead
        self.__is_alive = False

        # 2) Signal the loop to wake it up
        self.__waiter.set()

        # 3) Wait to let the loop complete, if it times out terminate
        if not self.__exit_waiter.wait(TurnoutService.EXIT_TIMEOUT):
            self.__logger.error('Timed out waiting for service termination.')

            sys.exit(TurnoutService.SHUTDOWN_TIMEOUT_EXIT)

    def __shutdown(self):
        '''
        Service shutdown process
        '''
        self.__logger.info('Shutting down now.')
