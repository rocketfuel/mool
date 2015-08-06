package com.example.serviceone;

import com.example.services.ServiceDemo;

public class ServiceOne implements ServiceDemo {
    @Override
    public String getName(){
        return "ServiceOne";
    }
}
