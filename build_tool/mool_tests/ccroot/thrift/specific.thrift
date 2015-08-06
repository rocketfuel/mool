include "ccroot/common/kvpair.thrift"

namespace cpp second_specific
namespace java org.second.specific
namespace py some.second.specific

typedef i32 MyInteger

const i32 SOME_CONSTANT = 314159
const map<string,string> MAP_CONSTANT = {'hello':'world'}

enum Operation {
  ADD = 1,
  SUBTRACT = 2,
  MULTIPLY = 3,
  DIVIDE = 4
}

struct Payload {
  1: i32 num1 = 0,
  2: i32 num2,
  3: Operation op,
  4: optional string comment,
}

service SpecificMapService extends kvpair.MapService {
   void ping(),
   i32 add(1:i32 num1, 2:i32 num2),
   i32 calculate(1:i32 logid, 2:Payload p),
   oneway void zip()
}
