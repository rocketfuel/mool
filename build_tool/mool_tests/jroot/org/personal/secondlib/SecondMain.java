package org.personal.secondlib;

public class SecondMain {
    public static boolean useFirstLib() {
        return 89 == org.personal.firstlib.Main.getSpecialNumber();
    }

    public static void main(String[] args) {
        System.out.println("Hello World.\n");
    }
}
