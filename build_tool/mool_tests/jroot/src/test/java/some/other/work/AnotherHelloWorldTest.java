package some.other.work;

import org.testng.Assert;
import org.testng.annotations.Test;

public class AnotherHelloWorldTest {
    @Test(groups = {"unit"})
    public void testDefault() {
        HelloWorld helloWorld = new HelloWorld();
        Assert.assertEquals(helloWorld.getSpecialString(), "Hello World");
    }
}
