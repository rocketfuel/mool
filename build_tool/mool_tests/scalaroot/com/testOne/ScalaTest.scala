// This file is uses Scala Test framework for testing.

package com.testOne

import collection.mutable.Stack
import org.scalatest._

import com.javaDep.JavaDep

class ScalaTest extends FlatSpec {
    "A Stack" should "pop values in last-in-first-out order" in {
        val stack = new Stack[Int]
        stack.push(1)
        stack.push(2)
        assert(stack.pop() === 2)
        assert(stack.pop() === 1)
    }

    it should "throw NoSuchElementException if an empty stack is popped" in {
        val emptyStack = new Stack[String]
        intercept[NoSuchElementException] {
            emptyStack.pop()
        }
    }

    "Resource files" should "be readable from JAR" in {
        println(Main.getResourceText("/com/testTwo/another_resource.txt"))
        assert(1 === 1)
    }

    "Java dependency" should "return a good string" in {
        val javaObj = new JavaDep()
        assert("java" === javaObj.getJavaString())
    }
}
