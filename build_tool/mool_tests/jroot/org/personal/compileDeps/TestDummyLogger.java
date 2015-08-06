package org.personal.compileDeps;

import java.io.*;
import java.util.Properties;
import java.util.ArrayList;
import java.util.List;

import org.testng.Assert;
import org.testng.annotations.Test;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;

public class TestDummyLogger {
    private BufferedReader reader = null;

    public final DummyLogger logger = new DummyLogger();
    public static final String logFile = "dummyLogger.log";

    @BeforeClass(groups = {"unit"})
    public void startReading() throws IOException {
        reader = new BufferedReader(new FileReader(logFile));
    }

    @AfterClass(groups = {"unit"})
    public void stopReading() throws IOException {
        reader.close();
    }

    public List<String> readNewLog() {
        String line;
        List<String> records = new ArrayList<String>();
        try {
            while((line = reader.readLine()) != null) {
                records.add(line);
            }
            return records;
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    public static String makeLogMsg(String msg, String level)
    {
        return level + " org.personal.compileDeps.DummyLogger - " + msg;
    }

    @Test(groups = {"unit"})
    public void testLogLevel() throws Exception {
        String msg = "This is a warning message.";
        logger.logMessage(msg, DummyLogger.LogLevel.WARN);
        List<String> logs = readNewLog();
        Assert.assertEquals(logs.get(0), makeLogMsg(msg, "WARN"));
    }

    @Test(groups = {"unit"})
    public void testDefaultLog() throws Exception {
        String msg = "This should be logged as DEBUG message.";
        logger.log(msg);
        List<String> logs = readNewLog();
        Assert.assertEquals(logs.get(0), makeLogMsg(msg, "DEBUG"));
    }
}
