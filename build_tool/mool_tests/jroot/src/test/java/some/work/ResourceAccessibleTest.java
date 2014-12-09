package some.work;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

import org.testng.annotations.Test;

public class ResourceAccessibleTest{
    @Test(groups = {"unit"})
    public void testResourceIsAccessible() throws IOException{
        String filename = "src/main/java/some/work/some_resource.txt";
        BufferedReader handle = new BufferedReader(new FileReader(filename));
        handle.readLine();
        handle.close();
        System.out.println("Resources accessible on physical file system. Test passed!!");
    }
}
