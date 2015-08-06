/*Code file details.*/
#include "ccroot/samples/person_utils.h"

#include "ccroot/common/address.pb.h"
#include "ccroot/samples/person.pb.h"

#include <stdio.h>

using ccroot_common::Address;
using std::string;

namespace ccroot_samples {

void use_person_proto() {
  Person person;
  person.set_id(1234);
  person.set_name("John Doe (CC indirect)");

  Address* home_address = person.add_addresses();
  home_address->set_text("100 Pleasant Dr, Somewhere, USA");
  home_address->set_type(1);

  Address* office_address = person.add_addresses();
  office_address->set_text("100 Main St, Somewhere, USA");
  office_address->set_type(2);

  // Check the constructed person object.
  printf("\n%s\n", person.DebugString().c_str());

  // Copy it out to a different object and print the contents.
  string data;
  person.SerializeToString(&data);
  Person another_person;
  another_person.ParseFromString(data);
  printf("%d\n", another_person.id());
  printf("%s\n", another_person.name().c_str());
  for (int i = 0; i < another_person.addresses_size(); ++i) {
    printf("%d: %s\n", another_person.addresses(i).type(),
           another_person.addresses(i).text().c_str());
}

}

}  // ccroot_samples
