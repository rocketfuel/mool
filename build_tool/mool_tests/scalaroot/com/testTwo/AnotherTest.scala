package com.testTwo

import com.testOne.Main
import org.scalatest._

class AnotherTest extends FunSuite {
    test("The special number should be 30.") {
    val mainObj = new Main()
        assert(mainObj.getSpecialNumber == 30)
    }
}
