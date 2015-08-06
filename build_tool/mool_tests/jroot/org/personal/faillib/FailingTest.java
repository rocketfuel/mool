package org.personal.faillib;

import java.lang.RuntimeException;
import org.testng.Assert;
import org.testng.annotations.Test;

public class FailingTest {
    @Test(groups = {"unit"})
    public void oneIsNotTwo() {
        Assert.assertEquals(1, 2);
        throw new RuntimeException("This shouldn't be printed.");
    }
}
