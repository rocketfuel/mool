package com.rocketfuel.ei.common;

import com.google.protobuf.BlockingService;
import com.google.protobuf.RpcController;
import com.google.protobuf.ServiceException;

import com.rocketfuel.ei.common.generated.TestSvcProtos.Dummy;
import com.rocketfuel.ei.common.generated.TestSvcProtos.RpcTestSvc;

import java.io.Closeable;
import java.io.IOException;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Tests for Rpc library.
 */
public class RpcTest {
    private static final Logger LOG = LoggerFactory.getLogger(RpcTest.class);

    private static class IntervalLogger {
        private final long startMillis = System.currentTimeMillis();

        public void logDone(String message) {
            double delta =
                (System.currentTimeMillis() - startMillis) / 1000.00;
            LOG.info("{} {} seconds.", message, delta);
        }
    }

    // Magic number used by the echo service as an addend. We test that the
    // number sent by the client to the server is echoed back after adding this
    // specific added.
    static final int SERVER_CONSTANT = 42;
    static final String LOCAL_HOST = "127.0.0.1";

    class RpcTestClient implements Closeable {
        private final RpcClient rpcClient;
        private final RpcTestSvc.BlockingInterface service;

        public RpcTestClient(String host, int port) throws IOException {
            IntervalLogger intervalLogger = new IntervalLogger();
            rpcClient = RpcClient.getConnectedClient(
                host, port, 1000, "unittest-client-workers",
                null);
            service = RpcTestSvc.newBlockingStub(rpcClient.getChannel());
            intervalLogger.logDone("Client connected:");
        }

        public Dummy echo(Dummy request)
                throws ServiceException {
            return service.echo(rpcClient.getController(), request);
        }

        public void use(int iterCount) throws ServiceException {
            IntervalLogger intervalLogger = new IntervalLogger();
            for (int i = 0; i < iterCount; ++i) {
                Dummy request = Dummy.newBuilder().setDummyValue(i).build();
                Dummy response = echo(request);
                Assert.assertEquals(
                    SERVER_CONSTANT + i,
                    response.getDummyValue());
            }
            intervalLogger.logDone("Client used " + iterCount + " times:");
        }

        @Override
        public void close() throws IOException {
            IntervalLogger intervalLogger = new IntervalLogger();
            rpcClient.close();
            intervalLogger.logDone("Client disconnected:");
        }
    }

    class RpcTestSvcImpl implements RpcTestSvc.BlockingInterface, Closeable {
        private RpcServer rpcServer = null;

        public void startServer() throws Exception {
            IntervalLogger intervalLogger = new IntervalLogger();
            List<BlockingService> services = new ArrayList<BlockingService>();
            services.add(RpcTestSvc.newReflectiveBlockingService(this));

            RpcServer.Config config =
                new RpcServer.Config()
                    .setHostName(LOCAL_HOST)
                    .setPort(0);
            rpcServer = RpcServer.getRunningServer(config, services);
            intervalLogger.logDone("Server started:");
        }

        public RpcServer getRpcServer() {
            return rpcServer;
        }

        @Override
        public void close() throws IOException {
            if (rpcServer != null) {
                IntervalLogger intervalLogger = new IntervalLogger();
                rpcServer.close();
                intervalLogger.logDone("Server stopped:");
            }
        }

        @Override
        public Dummy echo(RpcController controller, Dummy request) {
            return Dummy.newBuilder().setDummyValue(
                SERVER_CONSTANT + request.getDummyValue()).build();
        }
    }

    @Test(groups = "unit")
    public void testRpcStub() throws Exception {
        RpcTestSvcImpl rpcSvcImpl = new RpcTestSvcImpl();
        RpcTestClient client = null;
        try {
            rpcSvcImpl.startServer();
            client = new RpcTestClient(
                LOCAL_HOST, rpcSvcImpl.getRpcServer().getPort());
            client.use(10);
        } finally {
            try {
               client.close();
            } catch (IOException e) {
                System.err.println("Exception: " + e.getMessage());
            }
            try {
                rpcSvcImpl.close();
            } catch (IOException e) {
                System.err.println("Exception: " + e.getMessage());
            }
        }
    }
}
