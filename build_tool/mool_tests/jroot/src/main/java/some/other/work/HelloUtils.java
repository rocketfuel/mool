package some.other.work;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public class HelloUtils {
    @Deprecated
    public void forceCompilerWarning() {
        // Writing a deprecated method which forces a compiler warning. This is
        // used to make sure that compiler warnings are ignored when
        // ignore_compiler_warnings flag is used.
    }

    public void useResource(String resourcePath) throws Exception {
        StringBuffer sb = new StringBuffer();
        BufferedReader br = new BufferedReader(
            new InputStreamReader(
                HelloUtils.class.getResourceAsStream(resourcePath), "UTF-8"));
        for (int c = br.read(); c != -1; c = br.read()) {
            sb.append((char) c);
        }
        br.close();
        System.out.println(sb.toString());
    }

    public int getSpecialNumber() {
        return 31;
    }

    public String getSpecialString() {
        return "Hello World";
    }
}
