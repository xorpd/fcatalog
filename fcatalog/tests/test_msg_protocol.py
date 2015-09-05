import pytest
import struct
from fcatalog.proto.msg_protocol import Msg,MsgDef,Serializer,\
        SerializeError,DeserializeError,\
        pack_msg_type,unpack_msg_type

def test_msg_pack_unpack():
    """
    Make sure pack_msg_type and unpack_msg_type work correctly.
    """
    data = pack_msg_type(6,b'abcdefg')
    msg_type, msg_data = unpack_msg_type(data)
    assert msg_type == 6
    assert msg_data == b'abcdefg'
    

def test_msg_pack_unpack_error():
    """
    Check handling of errors with pack_msg_type and unpack_msg_type
    """
    # We can't unpack data that is too short:
    with pytest.raises(DeserializeError):
        unpack_msg_type(b'12')
    with pytest.raises(DeserializeError):
        unpack_msg_type(b'123')

    # This one doesn't raise an exception:
    unpack_msg_type(b'1234')
    with pytest.raises(DeserializeError):
        unpack_msg_type(b'123')

##################################################################

class DummyMsg(MsgDef):
    afields = ['a_int','b_str']

    def serialize(self,msg_inst):
        """
        Serialize a msg_inst to data bytes.
        """
        msg_data = b''

        # Write the integer as a dword.
        a_int = msg_inst.get_field('a_int')
        if not isinstance(a_int,int):
            raise SerializeError('a_int is not an integer!')
        # Assert the a_int is a dword:
        if not (0 <= a_int <= 0xffffffff):
            raise SerializeError('a_int is not a dword!')


        msg_data += struct.pack('I',a_int)

        b_str = msg_inst.get_field('b_str')
        b_str_bytes = b_str.encode('UTF-8')
        # Write the length of b_str as a dword:
        msg_data += struct.pack('I',len(b_str_bytes))
        # Write b_str:
        msg_data += b_str_bytes

        return msg_data


    def deserialize(self,msg_data):
        """
        Deserialize msg_data to msg_inst.
        """
        msg_inst = self.get_msg()

        a_int = struct.unpack('I',msg_data[0:4])[0]
        msg_inst.set_field('a_int',a_int)
        msg_data = msg_data[4:]
        b_str_len = struct.unpack('I',msg_data[0:4])[0]
        msg_data = msg_data[4:]

        if len(msg_data) != b_str_len:
            raise DeserializeError('b_str length is invalid!')

        b_str = msg_data.decode('UTF-8')
        msg_inst.set_field('b_str',b_str)

        return msg_inst

class OtherMsg(MsgDef):
    afields = ['c_int']

    def serialize(self,msg_inst):
        """
        Serialize a msg_inst to data bytes.
        """
        msg_data = b''

        # Write the integer as a dword.
        c_int = msg_inst.get_field('c_int')
        if not isinstance(c_int,int):
            raise SerializeError('c_int is not an integer!')
        # Assert the a_int is a dword:
        if not (0 <= c_int <= 0xffffffff):
            raise SerializeError('c_int is not a dword!')

        msg_data += struct.pack('I',c_int)

        return msg_data


    def deserialize(self,msg_data):
        """
        Deserialize msg_data to msg_inst.
        """
        msg_inst = self.get_msg()

        c_int = struct.unpack('I',msg_data[0:4])[0]
        msg_inst.set_field('c_int',c_int)
        return msg_inst


dummy_proto_def = {
        0:DummyMsg,\
        1:OtherMsg }

dummy_ser = Serializer(dummy_proto_def)


def test_serialize_deserialize():
    """
    Serialize and deserialize a simple message, and make sure everything is
    correct.
    """
    # Serialize and deserialize DummyMsg instance:
    msg_dummy = dummy_ser.get_msg('DummyMsg')
    msg_dummy.set_field('a_int',5)
    msg_dummy.set_field('b_str','hello world')
    data = dummy_ser.serialize_msg(msg_dummy)
    msg_dummy2 = dummy_ser.deserialize_msg(data)
    # Verify that the deserialization is correct:
    assert msg_dummy.get_field('a_int') == msg_dummy2.get_field('a_int')
    assert msg_dummy.get_field('b_str') == msg_dummy2.get_field('b_str')
    data2 = dummy_ser.serialize_msg(msg_dummy2)
    assert data == data2

    # Serialize and Deserialize OtherMsg instance:
    other_msg = dummy_ser.get_msg('OtherMsg')
    other_msg.set_field('c_int',8)
    data = dummy_ser.serialize_msg(other_msg)
    other_msg2 = dummy_ser.deserialize_msg(data)
    assert other_msg.get_field('c_int') == other_msg2.get_field('c_int')
    data2 = dummy_ser.serialize_msg(other_msg2)
    assert data == data2


def test_serialize_deserialize_error():
    """
    Check some serialize and deserialize errors.
    """
    other_msg = dummy_ser.get_msg('OtherMsg')
    # I put bytes into c_int, instead of an integer:
    other_msg.set_field('c_int',b'asklfjalskjfkalsjdf')
    # We expect a SerializeError here:
    with pytest.raises(SerializeError):
        dummy_ser.serialize_msg(other_msg)

    # We shouldn't be able to deserialize this data:
    rand_data = b'askldfjlk3490f3490fsdfsdfkj'
    with pytest.raises(DeserializeError):
        dummy_ser.deserialize_msg(rand_data)






