package org.personal.firstlib;

import org.testng.Assert;
import org.testng.annotations.Test;

public class MainTest {
    @Test(groups = {"unit"})
    public void testDefault() {
        Assert.assertEquals(1, 1);
        System.out.println("Java default test passed.!!!");
    }

    @Test(groups = {"unit"})
    public void testReadFromFile() throws Exception {
        System.out.println(Main.getResourceText("/org/personal/firstlib/prod_data00.txt"));
        System.out.println(Main.getResourceText("/org/personal/firstlib/test_data01.txt"));
        System.out.println(Main.getResourceText("/org/personal/firstlib/test_data02.txt"));
        Assert.assertEquals(1, 1);
    }
}
