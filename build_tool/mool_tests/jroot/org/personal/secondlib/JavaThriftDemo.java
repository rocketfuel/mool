package org.personal.secondlib;

public class JavaThriftDemo {
    public static void main(String[] args) {
        org.first.kvpair.KeyValuePair kvp = new org.first.kvpair.KeyValuePair();
        org.second.specific.Payload payload = new org.second.specific.Payload();
        System.out.println("Created thrift based objects in Java.\n");
    }
}
