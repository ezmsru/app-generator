package com.template.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "app", "{{PROJECT_NAME}}");
    }

    @GetMapping("/")
    public Map<String, String> root() {
        return Map.of("message", "Hello from {{PROJECT_NAME}}");
    }
}
