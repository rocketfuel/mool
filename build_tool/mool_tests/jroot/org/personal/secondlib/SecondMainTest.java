package org.personal.secondlib;

import org.testng.Assert;
import org.testng.annotations.Test;

public class SecondMainTest {
    @Test(groups = {"unit"})
    public void testDefault() {
        Assert.assertEquals(1, 1);
        Assert.assertTrue(SecondMain.useFirstLib());
        System.out.println(org.personal.firstlib.Main.getSpecialNumber());
        System.out.println("Java default test (SecondMain) passed.!!!");
    }
}
