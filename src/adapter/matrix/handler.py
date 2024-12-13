import logging
import time

from datetime import datetime

from generic.api import label_pb2
from generic.api.configuration import ConfigurationItem, Configuration
from generic.api.label import Label, Sort
from generic.api.parameter import Type, Parameter
from generic.handler import Handler as AbstractHandler

def _response(name, channel='matrix', parameters=None):
    """ Helper method to create a response Label. """
    return Label(Sort.RESPONSE, name, channel, parameters=parameters)

def _stimulus(name, channel='matrix', parameters=None):
    """ Helper method to create a stimulus Label. """
    return Label(Sort.STIMULUS, name, channel, parameters=parameters)

class Handler(AbstractHandler):
    """
    This class handles the interaction between AMP and the Matrix SUT.
    """

    def __init__(self):
        super().__init__()

    # TODO In case you don't use sockets, there's no need to change this method. 
    # TODO Just call it from stimulate when you receive the response of your SUT.
    def send_message_to_amp(self, raw_message: str):
        """
        Send a message back to AMP. The message from the SUT needs to be converted to a Label.

        Args:
            raw_message (str): The message to send to AMP.
        """
        logging.debug('response received: {label}'.format(label=raw_message))

        if raw_message == 'RESET_PERFORMED':
            # After 'RESET_PERFORMED', the SUT is ready for a new test case.
            self.adapter_core.send_ready()
        else:
            label = self._message2label(raw_message)
            self.adapter_core.send_response(label)

    def start(self):
        """
        Start a test.
        """

        # old methods for SmartDoor
        # end_point = self.configuration.items[0].value
        # self.sut = SmartDoorConnection(self, end_point)
        # self.sut.connect()

        # TODO START!!

        # make sure to send ready, else the amp will not do testing.
        # IMPORTANT: this is part of the generic adapter. Only necassery for sending ready.
        # In other case just use send_message_to_amp
        self.adapter_core.send_ready()

    def reset(self):
        """
        Prepare the SUT for the next test case.
        """
        logging.info('Resetting the SUT for a new test case')

        # old methods for SmartDoor
        # self.sut.send('RESET')

        # TODO RESET!!

        # make sure to send this to AMP too, so it knows that the SUT has reset
        self.send_message_to_amp("RESET_PERFORMED")

    def stop(self):
        """
        Stop the SUT from testing.
        """
        logging.info('Stopping the plugin handler')

        # old methods for SmartDoor
        # self.sut.stop()
        # self.sut = None

        # TODO STOP!!
        
        logging.debug('Finished stopping the plugin handler')

    def stimulate(self, pb_label: label_pb2.Label):
        """
        Processes a stimulus of a given label at the SUT.

        Args:
            pb_label (label_pb2.Label): stimulus that the Axini Modeling Platform has sent
        """

        label = Label.decode(pb_label)
        sut_msg = self._label2message(label)

        # send confirmation of stimulus back to AMP
        pb_label.timestamp = time.time_ns()
        pb_label.physical_label = bytes(sut_msg, 'UTF-8')
        self.adapter_core.send_stimulus_confirmation(pb_label)

        # leading spaces are needed to justify the stimuli and responses
        logging.info('      Injecting stimulus @SUT: ?{name}'.format(name=label.name))
        
        # old methods for SmartDoor
        # self.sut.send(sut_msg)
        
        # TODO SENDING!!

        # this is some example sending, should be replaced by your own logic.
        time.sleep(0.25)
        if label.name == "open":
            # TODO ACTION ON REAL SUT
            self.send_message_to_amp("opened")
        elif label.name == "close":
            # TODO ACTION ON REAL SUT
            self.send_message_to_amp("closed")

    # TODO This method should contain the labels your SUT supports
    def supported_labels(self):
        """
        The labels supported by the adapter.

        Returns:
             [Label]: List of all supported labels of this adapter
        """
        return [
            _stimulus('open'),
            _response('opened'),
            _stimulus('close'),
            _response('closed'),

            # old labels for SmartDoor, left here to give Syntax for parameters (if you need those)
            # _stimulus('lock', parameters=[Parameter('passcode', Type.INTEGER)]),
            # _response('locked'),
            # _stimulus('unlock', parameters=[Parameter('passcode', Type.INTEGER)]),
            # _response('unlocked'),
            # _stimulus('reset'),
            # _response('invalid_command'),
            # _response('invalid_passcode'),
            # _response('incorrect_passcode'),
            # _response('shut_off'),
        ]

    # TODO This method is only useful if you have to make a connection to some API
    # TODO If you just use Python, you can safely ignore this. Should not give bugs :)
    def default_configuration(self) -> Configuration:
        """
        The default configuration of this adapter.

        Returns:
            Configuration: the default configuration required by this adapter.
        """
        return Configuration([ConfigurationItem(\
            name='endpoint',
            tipe=Type.STRING,
            description='Base websocket URL of the SmartDoor API',
            value='ws://localhost:3001'),
        ])

    # TODO The following methods (_label2message and _message2label) should not be touched
    # TODO They encode for the communication between Adapter and AMP.
    def _label2message(self, label: Label):
        """
        Converts a Protobuf label to a SUT message.

        Args:
            label (Label)
        Returns:
            str: The message to be sent to the SUT.
        """

        sut_msg = None
        command_name = label.name.upper()
        if label.name in ['lock', 'unlock']:
            sut_msg = '{msg}:{passcode}'.format(msg=command_name, passcode=label.parameters[0].value)
        else:
            sut_msg = '{msg}'.format(msg=command_name)

        return sut_msg

    def _message2label(self, message: str):
        """
        Converts a SUT message to a Protobuf Label.

        Args:
            message (str)
        Returns:
            Label: The converted message as a Label.
        """

        label_name = message.lower()
        label = Label(
            sort=Sort.RESPONSE,
            name=label_name,
            channel='matrix',
            physical_label=bytes(message, 'UTF-8'),
            timestamp=datetime.now())

        return label
