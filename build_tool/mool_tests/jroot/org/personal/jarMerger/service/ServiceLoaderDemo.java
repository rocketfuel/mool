package com.example.serviceloaderdemo;

import java.util.*;
import com.example.services.ServiceDemo;

public class ServiceLoaderDemo {
  public static void main(String[] args) {
      ServiceLoader<ServiceDemo> services = ServiceLoader.load(ServiceDemo.class);
      List<String> names = new ArrayList<String>();

      for (ServiceDemo service : services) {
          names.add(service.getName());
      }
      if(names.contains("ServiceOne") && names.contains("ServiceTwo"))
          System.out.println("Both the services were loaded successfully.");
      else {
          System.out.println("Couldn't load all services! Jar merger failed.");
          System.exit(1);
      }
  }
}
