package some.work;

import java.io.IOException;

import org.apache.commons.lang3.StringUtils;

import some.other.work.HelloUtils;
import some.other.work.HelloWorld;

class LocalClass {
    public void execute() {
        System.out.println("Inside local class.");
    }
}

public class Driver {
    public int getSpecialNumber() {
        some.other.work.HelloWorld helloWorld = new some.other.work.HelloWorld();
        return helloWorld.getSpecialNumber();
    }

    public void execute(String[] args) {
        System.out.println("\nHello World!");
        LocalClass local = new LocalClass();
        local.execute();
    }

    public static void main(String[] args) throws Exception {
        Driver driver = new Driver();
        driver.execute(args);
        HelloWorld helloWorld = new HelloWorld();
        helloWorld.execute();
        DriverUtils driverUtils = new DriverUtils();
        driverUtils.execute();
        final String bigString = "This is a really big string that can be "
                + "abbreviated for demo purposes.";
        System.out.println(StringUtils.abbreviate(bigString, 30));
        HelloUtils helloUtils = new HelloUtils();
        helloUtils.useResource("/src/main/java/some/work/some_resource.txt");
    }
}
