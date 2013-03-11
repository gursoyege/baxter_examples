import errno

import roslib
roslib.load_manifest('baxter_interface')
import rospy

from baxter_msgs.msg import (
    DigitalIOState,
    DigitalOutputCommand,
)

class DigitalIO(object):
    """
    Interface class for a simple Digital Input and/or Output on the Baxter robot.

    Input       - read input state
    Output      - turn output On/Off
                - read current output state
    """
    def __init__(self, component_id):
        """
        @param component_id - unique id of the digital component
        """
        self._id = component_id
        self._component_type = 'digital_io'
        self._is_output = False

        self._state = {}

        type_ns = '/sdk/robot/' + self._component_type
        topic_base = type_ns + '/' + self._id

        self._sub_state = rospy.Subscriber(
            topic_base + '/state',
            DigitalIOState,
            self._on_io_state)

        rate = rospy.Rate(10)
        timeout = rospy.Time.now() + rospy.Duration(2)
        while not rospy.is_shutdown() and timeout > rospy.Time.now():
            if len(self._state.keys()):
                break
            rate.sleep()
        if not len(self._state.keys()):
            raise IOError(errno.ETIMEDOUT, "Failed to connect to baxter")

        # check if output-capable before creating publisher
        if self._is_output:
            self._pub_output = rospy.Publisher(
                type_ns + '/command',
                DigitalOutputCommand, latch=True)
        # Message is latched because there is a non-zero delay between
        # publisher creation and subscriber connection, where messages could
        # otherwise be lost.
        # See also: http://answers.ros.org/question/32952/with-rospy-messages-dont-seem-to-be-recieved-if-published-soon-after-creating-the-publisher/

    def _on_io_state(self, msg):
        """
        Updates the internally stored state of the Digital Input/Output.
        """
        self._is_output = not msg.isInputOnly
        self._state['state'] = (msg.state == DigitalIOState.PRESSED)

    def state(self):
        """
        Return the latest state of the Digital Input/Output.
        """
        return self._state['state']

    def is_output(self):
        """
        Accessor to check if IO is capable of output.
        """
        return self._is_output

    def set_output(self, value):
        """
        Control the state of the Digital Output.

        @param value bool    - new state {True, False} of the Output.
        """
        if not self._is_output:
            raise IOError(errno.EACCES, "Component is not an output [%s: %s]" %
                (self._component_type, self._id))
        cmd = DigitalOutputCommand()
        cmd.name = self._id
        cmd.value = value
        self._pub_output.publish(cmd)

