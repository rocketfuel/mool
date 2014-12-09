package some.other.work;

import com.google.protobuf.ByteString;
import com.google.protobuf.InvalidProtocolBufferException;

public class ProtoSampleUtils {
    public void execute() throws InvalidProtocolBufferException {
        System.out.println("Constructing proto object.");
        AddressProto.Address homeAddress = AddressProto.Address.newBuilder()
                .setText("100 Pleasant Dr, Somewhere, USA")
                .setType(1)
                .build();
        AddressProto.Address officeAddress = AddressProto.Address.newBuilder()
                .setText("100 Main St, Somewhere, USA")
                .setType(2)
                .build();
        PersonProto.Person person = PersonProto.Person.newBuilder()
                .setId(1234)
                .setName("John Doe (Java)")
                .addAddresses(homeAddress)
                .addAddresses(officeAddress)
                .build();
        System.out.println("Printing debug string.");
        System.out.println(person.toString());
        ByteString byteString = person.toByteString();
        PersonProto.Person anotherPerson = PersonProto.Person.parseFrom(byteString);
        System.out.println("Printing debug string of duplicated object.");
        System.out.println(anotherPerson.toString());
    }
}
