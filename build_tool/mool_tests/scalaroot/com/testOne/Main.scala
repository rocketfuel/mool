package com.testOne;

import scala.io.Source
import java.io.File

object Main {
    var constant = 100
    val variable = 100

    def getResourceText(resourcePath: String): String = {
        val reader = Source.fromURL(getClass.getResource(resourcePath), "UTF-8")
        reader.getLines().mkString("\n")
    }

    def getClassNumber(): Int = {
        val classObject = new Main()
        classObject.getSpecialNumber
    }

    def getSpecialString = "This string is returned by a scala object."

    def main(args: Array[String]): Unit = {
        // Test if we can access methods of object from class with same name.
        val classObject = new Main()
        println(classObject.getObjectString)
        if(classObject.getSpecialNumber != classObject.classConstant + classObject.classVariable) {
            println("This is unexpected behaviour. Test failed!")
            System.exit(1)
        }

        val file = Source.fromURL(getClass.getResource("/com/testOne/resource_data.txt"))
        file.getLines().foreach(line => println(line))
    }
}

class Main {
    var classConstant = 13
    val classVariable = 17
    var classString = "A constant string defined in scala Main class."

    def getSpecialNumber = this.classVariable + this.classConstant

    def getObjectString = Main.getSpecialString
}
