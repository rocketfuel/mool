package some.other.work;

import org.testng.Assert;
import org.testng.annotations.Test;

public class HelloWorldTest {
    @Test(groups = {"unit"})
    public void testDefault() {
        HelloWorld helloWorld = new HelloWorld();
        Assert.assertEquals(helloWorld.getSpecialNumber(), 31);
    }
}
