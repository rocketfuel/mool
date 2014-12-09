package some.work;

public class BinWithNoDependencies {
    private static class InternalClass {
        void showText() {
            System.out.println("Some text from InternalClass.");
        }
    }

    public static void main(String[] args) {
        InternalClass internalObject = new InternalClass();
        System.out.println("\nRunning Binary with no dependencies!");
        internalObject.showText();
    }
}
