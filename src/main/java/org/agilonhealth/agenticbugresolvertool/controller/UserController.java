package org.agilonhealth.agenticbugresolvertool.controller;

import org.agilonhealth.agenticbugresolvertool.models.User;
import org.agilonhealth.agenticbugresolvertool.repository.UserRepo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/v1/agilon")
public class UserController {

    @Autowired
    private UserRepo userRepo;

    @PostMapping("/user")
    public void setUser(@RequestBody User user){
        // Removed hardcoded values
        userRepo.save(user);
    }
}
