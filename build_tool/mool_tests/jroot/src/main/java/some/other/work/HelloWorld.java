package some.other.work;

class LocalClass {
    HelloUtils utils = new HelloUtils();

    public void execute() {
        System.out.println("Inside local class of another package.");
    }

    public int getSpecialNumber() {
        utils.forceCompilerWarning();
        return utils.getSpecialNumber();
    }

    public String getHelloString() {
        return utils.getSpecialString();
    }
}

public class HelloWorld {
    LocalClass local = new LocalClass();

    public int getSpecialNumber() {
        return local.getSpecialNumber();
    }

    public String getSpecialString() {
        return local.getHelloString();
    }

    public void execute() {
        local.execute();
    }
}
