package com.ScalaDep;

import com.testOne.Main;

/* This code checks if we can use a scala class in java. */
public class ScalaDep {
    public static void main(String[] args){
        Main scalaObj = new Main();
        System.out.println(scalaObj.getObjectString());
    }
}
