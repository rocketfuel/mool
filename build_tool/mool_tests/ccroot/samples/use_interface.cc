/*Code file details.*/
#include "ccroot/samples/use_interface.h"

namespace ccroot_samples {

void use_interface(UseInterface* interface) {
  if (interface) {
    interface->use();
  }
}

}  // ccroot_samples
