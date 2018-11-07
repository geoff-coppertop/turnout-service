# Model Railroad Turnout Microservice

This is a microservice that is able to operate model railroad turnouts.

Turnouts are controlled by a servo (for point motion) and a relay (for controlling the powered frog). Turnouts are modelled by a simple state machine with 4 states,

- two transient ones when the points are moving and external stimulus is ignored(main_transition, diverging_transition)
- two stationary ones when the point are idle and external stimulus is accepted.

This service is designed to be able to operate many turnouts but work so far has been done focused on hardware that makes use of a PCA9685 connected via an I2C bus.

Details of turnout operation can be found [here](<https://github.com/geoff-coppertop/python-hw-railroad>).

## Configuration

A single configuration file is used to configure logging and service construction. Two top level dictionary keys are used,

- logging: Logging configuration is done per the standard python yaml format
- service: Configures the turnouts controlled by the service. It should follow the format shown in the [example_config.yml](<./example_config.yml>)

## Build

The turnout-service is designed to be run in a containerized environment with privilieged access to the host os for physical interaction. The docker image can be built using the following command,

- docker build -t coppertopgeoff/turnout-service .

This should then be pushed on commit to docker hub using the following command,

- docker push coppertopgeoff/turnout-service

If tags are to be assigned they should be in the format MMddYY.

## Operation

The turnout-service makes use of the Raspberry Pi hardware and will not run in docker hosted on other platforms. The docker image should be run with the following command,

- docker run --rm -t --privileged coppertopgeoff/turnout-service

It may be possible in the future to reduce the privilege required to specific devices.