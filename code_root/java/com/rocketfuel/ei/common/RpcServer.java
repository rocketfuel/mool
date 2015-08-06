package com.rocketfuel.ei.common;

import com.google.protobuf.BlockingService;
import com.googlecode.protobuf.pro.duplex.CleanShutdownHandler;
import com.googlecode.protobuf.pro.duplex.PeerInfo;
import com.googlecode.protobuf.pro.duplex.RpcConnectionEventNotifier;
import com.googlecode.protobuf.pro.duplex.execute.RpcServerCallExecutor;
import com.googlecode.protobuf.pro.duplex.execute.SameThreadExecutor;
import com.googlecode.protobuf.pro.duplex.listener.RpcConnectionEventListener;
import com.googlecode.protobuf.pro.duplex.server.DuplexTcpServerPipelineFactory;
import com.googlecode.protobuf.pro.duplex.util.RenamingThreadFactoryProxy;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.util.concurrent.EventExecutorGroup;

import java.io.Closeable;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * The generic RPC server.
 */
public final class RpcServer implements Closeable {
    /**
     * Users of RpcServer are expected to fill out a config instance, construct
     * RpcServer and then call "startServer". Some fields in Config must be
     * set before it can be used. Some other fields are optional. List is
     * provided below:
     *    - Mandatory:
     *        setHostName
     *        setPort
     *
     *    - Optional:
     *        setServiceName
     *        setConnectionEventListener
     *        setServerCallExecutor
     *        setParentLoop
     *        setChildLoop
     *        setRcvBufSize
     *        setSndBufSize
     */
    public static class Config {
        // These settings must be specified.
        private String hostName;
        private int port;

        // These settings have acceptable defaults.
        private String serviceName = "defaultService";
        private int sndBufSize = 1048576;
        private int rcvBufSize = 1048576;
        private RpcConnectionEventListener listener = null;
        private RpcServerCallExecutor executor = null;
        private EventLoopGroup parentLoop = null;
        private EventLoopGroup childLoop = null;

        public Config setHostName(String hostName) {
            this.hostName = hostName;
            return this;
        }

        public Config setPort(int port) {
            this.port = port;
            return this;
        }

        public Config setServiceName(String serviceName) {
            this.serviceName = serviceName;
            return this;
        }

        public Config setConnectionEventListener(
            RpcConnectionEventListener listener) {
            this.listener = listener;
            return this;
        }

        public Config setServerCallExecutor(RpcServerCallExecutor executor) {
            this.executor = executor;
            return this;
        }

        public Config setParentLoop(EventLoopGroup parentLoop) {
            this.parentLoop = parentLoop;
            return this;
        }

        public Config setChildLoop(EventLoopGroup childLoop) {
            this.childLoop = childLoop;
            return this;
        }

        public Config setSndBufSize(int sndBufSize) {
            this.sndBufSize = sndBufSize;
            return this;
        }

        public Config setRcvBufSize(int rcvBufSize) {
            this.rcvBufSize = rcvBufSize;
            return this;
        }
    }

    // Static utility methods.
    private static void shutdownGroup(
        EventExecutorGroup  group) throws IOException {
        if (group == null) {
            return;
        }
        group.shutdownGracefully();
        try {
            group.awaitTermination(
                Long.MAX_VALUE, TimeUnit.NANOSECONDS);
        } catch (InterruptedException e) {
            throw new IOException("Failed to close group: ", e);
        }
    }

    private static void shutdownService(
        ExecutorService  service) throws IOException {
        if (service == null) {
            return;
        }
        service.shutdown();
        // The default is a SameThreadExecutor instance and it does not support
        // awaitTermination. It throws an explicit IllegalState exception.
    }

    // Fields.
    private final PeerInfo serverInfo;
    private Config config;
    private Channel channel;
    private boolean shutdownExecutor = false;
    private boolean shutdownParentLoop = false;
    private boolean shutdownChildLoop = false;
    private boolean closed = false;

    // Methods.
    /**
     * Start server with provided services and return the RpcServer object. The
     * server would continue running till the object is closed.
     */
    public static RpcServer getRunningServer(
        Config config, List<BlockingService> services)
        throws IOException, InterruptedException {
        RpcServer result = null;
        RpcServer temporary = null;
        try {
            temporary = new RpcServer(config);
            temporary.start(services);
            // Transfer ownership to caller.
            result = temporary;
            temporary = null;
        } finally {
            if (temporary != null) {
                temporary.close();
            }
        }
        return result;
    }

    private RpcServer(Config config) {
        this.config = config;
        this.serverInfo = new PeerInfo(config.hostName, config.port);
    }

    /**
     * Start the service.
     */
    private void start(
        List<BlockingService> services) throws InterruptedException {
        DuplexTcpServerPipelineFactory factory =
                new DuplexTcpServerPipelineFactory(serverInfo);
        // Additional help for callers who forget to call close. This is ok
        // because double-shutdowns are safe.
        CleanShutdownHandler shutdownHandler = new CleanShutdownHandler();

        // Reduce logging.
        NullLogger logger = new NullLogger();
        factory.setLogger(logger);

        if (config.executor == null) {
            // protobuf-rpc-pro performanceTips recommends we use
            // SameThreadExecutor if we do not call a client RPC method from
            // within the processing of a server side RPC.
            config.executor = new SameThreadExecutor();
            shutdownExecutor = true;
            shutdownHandler.addResource(config.executor);
        }
        factory.setRpcServerCallExecutor(config.executor);

        if (config.listener != null) {
            RpcConnectionEventNotifier rpcEventNotifier = new
                    RpcConnectionEventNotifier();
            rpcEventNotifier.setEventListener(config.listener);
            factory.registerConnectionEventListener(rpcEventNotifier);
        }

        for (BlockingService service : services) {
            factory.getRpcServiceRegistry().registerService(true, service);
        }

        if (config.parentLoop == null) {
            config.parentLoop = new NioEventLoopGroup(
                1,
                new RenamingThreadFactoryProxy(
                    config.serviceName + "-parentGroup",
                    Executors.defaultThreadFactory()));
            shutdownHandler.addResource(config.parentLoop);
            shutdownParentLoop = true;
        }

        if (config.childLoop == null) {
            config.childLoop = new NioEventLoopGroup(
                1,
                new RenamingThreadFactoryProxy(
                    config.serviceName + "-childGroup",
                    Executors.defaultThreadFactory()));
            shutdownHandler.addResource(config.childLoop);
            shutdownChildLoop = true;
        }

        ServerBootstrap bootstrap = new ServerBootstrap();
        bootstrap.group(config.parentLoop, config.childLoop);
        bootstrap.channel(NioServerSocketChannel.class);
        bootstrap.option(ChannelOption.SO_SNDBUF, config.sndBufSize);
        bootstrap.option(ChannelOption.SO_RCVBUF, config.rcvBufSize);
        bootstrap.childOption(ChannelOption.SO_RCVBUF, config.sndBufSize);
        bootstrap.childOption(ChannelOption.SO_SNDBUF, config.rcvBufSize);
        bootstrap.option(ChannelOption.TCP_NODELAY, true);
        bootstrap.childHandler(factory);
        bootstrap.localAddress(serverInfo.getPort());
        channel = bootstrap.bind().sync().channel();
    }

    /**
     * Get host, port etc to which the server has bound to.
     * <p/>
     * Note: In case of ephemeral ports, the port number returned by PeerInfo is
     * not valid, use port from the connected channel.
     *
     * @return the PeerInfo associated with this Rpc Server.
     */
    public PeerInfo getServerInfo() {
        return serverInfo;
    }

    /**
     * Get channel associated with this Rpc server.
     */
    public Channel getChannel() {
        return channel;
    }

    /**
     * Get host name.
     */
    public String getHostName() {
        return ((InetSocketAddress) channel.localAddress()).getHostName();
    }

    /**
     * Get actual port number, in case ephemeral ports are being used.
     */
    public int getPort() {
        return ((InetSocketAddress) channel.localAddress()).getPort();
    }

    @Override
    public void close() throws IOException {
        if (closed) {
            throw new RuntimeException("RpcServer instance already closed.");
        }
        if (shutdownParentLoop) {
            shutdownGroup(config.parentLoop);

        }
        if (shutdownChildLoop) {
            shutdownGroup(config.childLoop);
        }
        if (shutdownExecutor) {
            shutdownService(config.executor);
        }
        closed = true;
    }
}
