/*Header file details.*/
#ifndef __CCROOT_SAMPLES_USE_INTERFACE__
#define __CCROOT_SAMPLES_USE_INTERFACE__

namespace ccroot_samples {

class UseInterface {
 public:
  virtual void use() = 0;
};

void use_interface(UseInterface* interface);

}  // ccroot_samples

#endif  // __CCROOT_SAMPLES_USE_INTERFACE__
