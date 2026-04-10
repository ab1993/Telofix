package org.agilonhealth.agenticbugresolvertool.repository;

import org.agilonhealth.agenticbugresolvertool.models.User;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface UserRepo extends MongoRepository<User, Long> {
}