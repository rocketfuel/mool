package org.personal.firstlib;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public class Main {
    public static String getResourceText(String resourcePath) throws Exception {
        StringBuffer sb = new StringBuffer();
        BufferedReader br = new BufferedReader(
            new InputStreamReader(
                Main.class.getResourceAsStream(resourcePath), "UTF-8"));
        for (int c = br.read(); c != -1; c = br.read()) {
            sb.append((char) c);
        }
        br.close();
        return sb.toString();
    }

    public static int getSpecialNumber() {
        return 89;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Hello World.\n");
        System.out.println(getResourceText("/org/personal/firstlib/prod_data00.txt"));
    }
}
