package org.agilonhealth.agenticbugresolvertool;

import org.agilonhealth.agenticbugresolvertool.controller.UserController;
import org.agilonhealth.agenticbugresolvertool.models.User;
import org.agilonhealth.agenticbugresolvertool.repository.UserRepo;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.verify;

class UserControllerTest {

    @Mock
    private UserRepo userRepo;

    @InjectMocks
    private UserController userController;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testSetUser() {
        User user = new User();
        when(userRepo.save(user)).thenReturn(user);

        userController.setUser(user);

        verify(userRepo).save(user);
    }
}
