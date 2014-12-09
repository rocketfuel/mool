package some.work;

import org.testng.Assert;
import org.testng.annotations.Test;

public class DriverTest {
    @Test(groups = {"disabled"})
    public void testDisabled() {
        // This test would clearly fail if it ran. It is included to ensure that
        // it does not run when we run all unit tests from the command line, since
        // it belongs to the "disabled" group. The test groups can be configured in
        // the test rule including this test (in the BLD file).
        Assert.assertEquals(2, 1);
    }

    @Test(groups = {"unit", "integration"})
    public void testDriver() {
        Driver driver = new Driver();
        // Using "actual, expected" order per
        // http://testng.org/javadoc/org/testng/Assert.html.
        Assert.assertEquals(driver.getSpecialNumber(), 31);
    }

    @Test(groups = {"unit"})
    public void testDefault() {
        Assert.assertEquals(1, 1);
        System.out.println("Java default test passed.!!!");
    }
}
