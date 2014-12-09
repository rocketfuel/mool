"""PersonMainClass implementation."""
import pyroot.first_service.first_module.address_pb2 as address_pb2
import pyroot.second_service.another_module.person_pb2 as person_pb2


class PersonMainClass(object):
  """Person Main class implementation."""
  def __init__(self):
    """Initializer."""

  @classmethod
  def use_protos(cls):
    """Sample method to use protos."""
    # Create a person object.
    first_person = person_pb2.Person()
    first_person.id = 1234
    first_person.name = 'John Doe (Python)'
    home_address = address_pb2.Address()
    home_address.text = '100 Pleasant Dr, Somewhere, USA'
    home_address.type = 1
    office_address = address_pb2.Address()
    office_address.text = '100 Main St, Somewhere, USA'
    office_address.type = 2
    first_person.addresses.extend([home_address, office_address])

    # Print the debug string.
    print 'DebugString: "{}"'.format(str(first_person))

    # Save the serialized string.
    serialized_string = first_person.SerializeToString()

    # Use the serialized string to create another object.
    another_person = person_pb2.Person()
    another_person.ParseFromString(serialized_string)
    print 'id is: ', another_person.id
    print 'name is: ', another_person.name
    print 'addresses are: '
    for address in another_person.addresses:
      print ' '.join([str(address.type), address.text])


def main_func():
  """Main function."""
  print '-----------------------------'
  PersonMainClass().use_protos()
