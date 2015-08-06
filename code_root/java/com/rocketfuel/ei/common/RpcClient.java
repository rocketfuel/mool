package com.rocketfuel.ei.common;

import com.google.protobuf.RpcController;

import com.googlecode.protobuf.pro.duplex.CleanShutdownHandler;
import com.googlecode.protobuf.pro.duplex.PeerInfo;
import com.googlecode.protobuf.pro.duplex.RpcClientChannel;
import com.googlecode.protobuf.pro.duplex.client.DuplexTcpClientPipelineFactory;
import com.googlecode.protobuf.pro.duplex.util.RenamingThreadFactoryProxy;

import io.netty.bootstrap.Bootstrap;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioSocketChannel;

import java.io.Closeable;
import java.io.IOException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * The generic RPC client. Must be closed after construction to avoid any
 * resource leaks. Should not be reused after closing. Currently reuse is
 * blocked by marking "connect" a private method.
 */
public final class RpcClient implements Closeable {
    private final String host;
    private final int port;
    private final int timeoutMillis;

    private RpcClientChannel channel;
    private RpcController controller;
    private EventLoopGroup workers;

    private RpcClient(String host, int port, int timeoutMillis) {
        this.host = host;
        this.port = port;
        this.timeoutMillis = timeoutMillis;
    }

    /**
     * A leak-free mechanism for allocating a conected client object.
     */
    public static RpcClient getConnectedClient(
        String host, int port, int timeoutMillis, String threadPoolName,
        NioEventLoopGroup providedGroup) throws IOException {
        RpcClient result = null;
        RpcClient internal = null;
        try {
            internal = new RpcClient(host, port, timeoutMillis);
            internal.connect(
                (threadPoolName == null) ? "default" : threadPoolName,
                providedGroup);
            // Transfer ownership to out-parameter.
            result = internal;
            internal = null;
        } finally {
            if (internal != null) {
                internal.close();
            }
        }
        return result;
    }

    public RpcClientChannel getChannel() {
        return channel;
    }

    public RpcController getController() {
        return controller;
    }

    private void connect(String threadPoolName,
                         NioEventLoopGroup providedGroup) throws IOException {
        PeerInfo serverInfo = new PeerInfo(host, port);
        if (providedGroup != null) {
            workers = providedGroup;
        } else {
            workers = new NioEventLoopGroup(1, new RenamingThreadFactoryProxy(
                            threadPoolName,
                            Executors.defaultThreadFactory()));
        }
        // These workers must be shutdown before process exits. This is
        // guaranteed if the caller of this class calls close(). However, we do
        // not have many fault injection based tests and such error cases are
        // prone to be buggy. Lets help the user by "remembering" to shutdown
        // even if the caller forgets to close(). This additional help is ok
        // since shutdown is idempotent.
        (new CleanShutdownHandler()).addResource(workers);
        DuplexTcpClientPipelineFactory clientFactory =
            new DuplexTcpClientPipelineFactory();
        clientFactory.setRpcLogger(new NullLogger());
        Bootstrap bootstrap = new Bootstrap()
                .group(workers)
                .handler(clientFactory)
                .channel(NioSocketChannel.class)
                .option(ChannelOption.TCP_NODELAY, true)
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, timeoutMillis)
                .option(ChannelOption.SO_SNDBUF, 1048576)
                .option(ChannelOption.SO_RCVBUF, 1048576);
        channel = clientFactory.peerWith(serverInfo, bootstrap);
        controller = channel.newRpcController();
    }

    @Override
    public void close() throws IOException {
        if (channel != null) {
            channel.close();
        }
        if (workers != null) {
            workers.shutdownGracefully();
            try {
                workers.awaitTermination(Long.MAX_VALUE, TimeUnit.NANOSECONDS);
            } catch (InterruptedException e) {
                throw new IOException("Failed to close, client", e);
            }
        }
    }
}
