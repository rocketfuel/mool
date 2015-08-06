package org.personal.compileDeps;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DummyLogger {
    private static final Logger LOG = LoggerFactory.getLogger(DummyLogger.class);

    public static enum LogLevel {
        INFO, WARN, DEBUG, ERROR
    };

    public static void logMessage(String message, LogLevel level) {
        switch(level) {
            case INFO: LOG.info(message);
                       break;
            case WARN: LOG.warn(message);
                       break;
            case DEBUG: LOG.debug(message);
                       break;
            case ERROR: LOG.error(message);
                       break;
        }
    }

    public static void log(String message) {
        LOG.debug(message);
    }

    public static void main(String[] args)
    {
        logMessage("This is an INFO message.", LogLevel.INFO);
        logMessage("This is an WARNING message.", LogLevel.WARN);
        logMessage("This is an DEBUG message.", LogLevel.DEBUG);
        logMessage("This is an ERROR message!", LogLevel.ERROR);
        log("This is a generic log message.");
    }
}
