namespace cpp first_kvpair
namespace java org.first.kvpair
namespace py some.first.kvpair

struct KeyValuePair {
  1: i32 key
  2: string value
}

service MapService {
  KeyValuePair getPair(1: i32 key)
}
