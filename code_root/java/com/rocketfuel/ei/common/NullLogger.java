package com.rocketfuel.ei.common;

import com.google.protobuf.Message;
import com.googlecode.protobuf.pro.duplex.PeerInfo;
import com.googlecode.protobuf.pro.duplex.logging.RpcLogger;

/**
 * An RpcLogger implementation which does not log anything.
 */
public class NullLogger implements RpcLogger {
    @Override
    public void logCall(PeerInfo client, PeerInfo server, String signature,
                        Message request, Message response, String errorMessage,
                        int correlationId, long requestTS, long responseTS) {
    }

    @Override
    public void logOobResponse(PeerInfo client, PeerInfo server,
                               Message message, String signature,
                               int correlationId, long eventTS) {
    }

    @Override
    public void logOobMessage(PeerInfo client, PeerInfo server,
                              Message message, long eventTS) {
    }
}
