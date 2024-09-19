from pieraknet.buffer import Buffer
from pieraknet.packets.packet import Packet

# Example packet: b'\x84\x00\x00\x00\x40\x00\x90\x00\x00\x00\t\xb3;\xc81\xbe\xfb\x96*\x00\x00\x00\x00\x00\x00\xdb\xf2\x00'
# x84: Packet ID
# Sequence number: uint24le (en este caso \x00\x00\x00)
# Flags (byte): (en este caso \x40)
#   reliability_type = top 3 bits
#   fourth bit is 1 when the frame is fragmented and part of a compound.
# Length IN BITS (unsigned short): Length of the body in bits. (en este caso \x00\x90)
# Reliable Frame Index (uint24le): only if reliable (en este caso \x00\x00\x00)
# Sequenced Frame Index (uint24le): only if sequenced (en este caso \x00\x00\x00)
# --- ORDER --- 
# Ordered Frame Index (uint24le): only if ordered (en este caso \x00)
# Order Channel (byte): only if ordered (en este caso \x00)
# --- FRAGMENT ---
# Compound Size (int): only if fragmented (en este caso \x00\x00\x00)
# Compound ID (short): only if fragmented (en este caso \x00\x00)
# Index (int): only if fragmented (en este caso \x00\x00\x00\x00)
# --- BODY ---
# Body (length in bits / 8): only if not fragmented (en este caso \xdb\xf2\x00)



#ID	Name                    Reliable    Ordered    Sequenced
#0	unreliable			    
#1	unreliable sequenced		          x	           x
#2	reliable	              x		
#3	reliable ordered 	      x           x	
#4	reliable sequenced	      x           x	           x
#5	unreliable (+ ACK receipt)			
#6	reliable (+ ACK receipt)  x		
#7	reliable ordered (+ ACK receipt)x	  x	

class Frame:
    def __init__(self, server=None):
        self.server = server
        self.flags = 0
        self.length_in_bits = 0
        self.reliable_frame_index = 0
        self.sequenced_frame_index = 0
        self.ordered_frame_index = 0
        self.order_channel = 0
        self.compound_size = 0
        self.compound_id = 0
        self.index = 0
        self.body = b''

    def decode(self, buffer: Buffer):
        self.flags = buffer.read_byte()
        reliability_type = (self.flags >> 5) & 0x07
        is_fragmented = (self.flags >> 4) & 0x01

        self.server.logger.debug(f"Fragmented Frame: {is_fragmented}")
        self.server.logger.debug(f"Read Frame Flags: {self.flags}")

        self.length_in_bits = buffer.read_unsigned_short()
        self.server.logger.debug(f"Read Length in Bits: {self.length_in_bits}")

        if reliability_type in {2, 3, 4, 6, 7}:
            self.reliable_frame_index = buffer.read_uint24le()
            self.server.logger.debug(f"Read Reliable Frame Index: {self.reliable_frame_index}")

        if reliability_type in {1, 4}:
            self.sequenced_frame_index = buffer.read_uint24le()
            self.server.logger.debug(f"Read Sequenced Frame Index: {self.sequenced_frame_index}")

        if reliability_type in {1, 3, 4, 7}:
            self.ordered_frame_index = buffer.read_uint24le()
            self.order_channel = buffer.read_byte()
            self.server.logger.debug(f"Read Ordered Frame Index: {self.ordered_frame_index}")
            self.server.logger.debug(f"Read Order Channel: {self.order_channel}")

        if is_fragmented:
            self.compound_size = buffer.read_int()
            self.server.logger.debug(f"Read Compound Size: {self.compound_size}")
            self.compound_id = buffer.read_short()
            self.server.logger.debug(f"Read Compound ID: {self.compound_id}")
            self.index = buffer.read_int()
            self.server.logger.debug(f"Read Index: {self.index}")

        body_length = (self.length_in_bits + 7) // 8
        self.body = buffer.read(body_length)
        self.server.logger.debug(f"Read Body (Length {body_length} bytes): {self.body}")

    def encode(self, buffer: Buffer):
        if not isinstance(self.flags, int) or not isinstance(self.length_in_bits, int):
            raise TypeError("flags and length_in_bits must be integers")

        buffer.write_byte(self.flags)
        self.server.logger.debug(f"Written Frame Flags: {self.flags}")

        buffer.write_unsigned_short(self.length_in_bits)
        self.server.logger.debug(f"Written Length in Bits: {self.length_in_bits}")

        reliability_type = (self.flags >> 5) & 0x07
        is_fragmented = (self.flags >> 4) & 0x01

        if reliability_type in {2, 3, 4, 6, 7}:
            buffer.write_uint24le(self.reliable_frame_index)
            self.server.logger.debug(f"Written Reliable Frame Index: {self.reliable_frame_index}")

        if reliability_type in {1, 4}:
            buffer.write_uint24le(self.sequenced_frame_index)
            self.server.logger.debug(f"Written Sequenced Frame Index: {self.sequenced_frame_index}")

        if reliability_type in {1, 3, 4, 7}:
            buffer.write_uint24le(self.ordered_frame_index)
            buffer.write_byte(self.order_channel)
            self.server.logger.debug(f"Written Ordered Frame Index: {self.ordered_frame_index}")
            self.server.logger.debug(f"Written Order Channel: {self.order_channel}")

        if is_fragmented:
            buffer.write_int(self.compound_size)
            buffer.write_short(self.compound_id)
            buffer.write_int(self.index)
            self.server.logger.debug(f"Written Compound Size: {self.compound_size}")
            self.server.logger.debug(f"Written Compound ID: {self.compound_id}")
            self.server.logger.debug(f"Written Index: {self.index}")

        buffer.write(self.body)
        self.server.logger.debug(f"Written Body (Length {len(self.body)} bytes): {self.body}")
        return buffer.getvalue()