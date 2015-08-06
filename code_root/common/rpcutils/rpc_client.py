"""Rpc client library."""
import socket

import common.rpcutils.duplex_protocol_pb2 as duplex_protocol_pb2
import common.rpcutils.rpc_header_pb2 as rpc_header_pb2

CORRELATION_ID = 1


class Error(Exception):
    """The exception class for this module."""


def _int32_pack(byte_count):
    """Protobuf int32 encoder."""
    rpc_header = rpc_header_pb2.RpcHeader()
    rpc_header.byte_count = byte_count
    return rpc_header.SerializeToString()[1:]


def _int32_unpack(bytes_text):
    """Protobuf int32 decoder."""
    rpc_header = rpc_header_pb2.RpcHeader()
    rpc_header.ParseFromString(chr(0x08) + bytes_text)
    return rpc_header.byte_count


class RpcClient(object):
    """Rpc Client shim for managing socket level communication."""
    def __init__(self, host, port):
        """Initializer."""
        self.host = host
        self.port = port
        self.socket = None

    def _get_addr_info(self):
        """Get address info."""
        return socket.getaddrinfo(
            self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM)

    def _send_raw_bytes_from_text(self, msg):
        """Send raw bytes down the socket."""
        total_sent = 0
        while total_sent < len(msg):
            count = self.socket.send(msg[total_sent:])
            if count == 0:
                raise Error('Socket connection to server broken.')
            total_sent += count

    def _send_proto(self, msg):
        """Send a wire payload protocol buffer object to the server."""
        msg = msg.SerializeToString()
        self._send_raw_bytes_from_text(''.join(_int32_pack(len(msg))))
        self._send_raw_bytes_from_text(msg)

    def _receive_raw_bytes(self, count):
        """Receive raw bytes from server."""
        chunks = []
        total_received = 0
        while total_received < count:
            chunk = self.socket.recv(count - total_received)
            if not chunk:
                raise Error('Socket connection to server broken.')
            chunks.append(chunk)
            total_received += len(chunk)
        return chunks

    def _receive_proto(self):
        """Receive a wire payload protocol buffer object from the server."""
        # The int32 packaging documentation guarantees that the length field
        # will be a sequence of bytes with MSB set to 1 (0 or more) followed by
        # exactly one byte where MSB is set to 0.
        chunks = []
        while True:
            chunk = ''.join(self._receive_raw_bytes(1))
            assert 1 == len(chunk)
            chunks.append(chunk)
            if ord(chunk) < 0x80:
                break
        bytes_expected = _int32_unpack(''.join(chunks))
        bytes_received = ''.join(self._receive_raw_bytes(bytes_expected))
        wire_payload = duplex_protocol_pb2.WirePayload()
        wire_payload.ParseFromString(bytes_received)
        return wire_payload

    def connect(self, timeout_seconds=None):
        """Connect to server."""
        for item in self._get_addr_info():
            address_family, sock_type, protocol, _, server_address = item
            candidate = None
            opened = False
            try:
                candidate = socket.socket(address_family, sock_type, protocol)
                opened = True
                candidate.settimeout(timeout_seconds)
                candidate.connect(server_address)
            except socket.error:
                if opened:
                    candidate.close()
                continue
            self.socket = candidate
            break
        if self.socket is None:
            raise Error(
                'Could not open socket to {}:{}'.format(
                    self.host, self.port))
        # For AF_INET6 address family, a four-tuple (host, port, flowinfo,
        # scopeid) is returned by socket.getsockname. But for AF_INET (ipv4)
        # a (host, pair) is returned. Since we want do be able to handle both
        # we use AF_UNSPEC as address family during connection establishment
        # and ignore the last 2 members if server is using ipv6.
        socket_address = self.socket.getsockname()
        assert (len(socket_address) == 2 or len(socket_address) == 4)
        client_ip, client_port = socket_address[:2]
        wire_payload = duplex_protocol_pb2.WirePayload()
        wire_payload.connectRequest.correlationId = CORRELATION_ID
        wire_payload.connectRequest.clientPID = '1'
        wire_payload.connectRequest.clientHostName = str(client_ip)
        wire_payload.connectRequest.clientPort = client_port
        wire_payload.connectRequest.compress = False
        self._send_proto(wire_payload)
        wire_payload = self._receive_proto()
        assert wire_payload.connectResponse is not None
        assert wire_payload.connectResponse.correlationId == CORRELATION_ID
        assert not wire_payload.connectResponse.compress

    def get_rpc_response_bytes(self, service_name, method_name, in_bytes):
        """Perform rpc query and get the returned bytes."""
        wire_payload = duplex_protocol_pb2.WirePayload()
        wire_payload.rpcRequest.correlationId = CORRELATION_ID
        wire_payload.rpcRequest.serviceIdentifier = service_name
        wire_payload.rpcRequest.methodIdentifier = method_name
        wire_payload.rpcRequest.requestBytes = in_bytes
        wire_payload.rpcRequest.timeoutMs = 0
        self._send_proto(wire_payload)
        wire_payload = self._receive_proto()
        assert wire_payload.rpcResponse is not None
        assert wire_payload.rpcResponse.correlationId == CORRELATION_ID
        return wire_payload.rpcResponse.responseBytes

    def close(self):
        """Close the connection."""
        assert self.socket is not None
        self.socket.close()
        self.socket = None
