package some.work;

import some.other.work.ProtoSampleUtils;

import com.google.protobuf.InvalidProtocolBufferException;

public class ProtoSampleMain {
    public static void main(String[] args) throws InvalidProtocolBufferException {
        ProtoSampleUtils utils = new ProtoSampleUtils();
        utils.execute();
    }
}
