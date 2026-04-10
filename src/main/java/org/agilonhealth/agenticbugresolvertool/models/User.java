package org.agilonhealth.agenticbugresolvertool.models;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Document(collection = "users")
@Data
public class User {
    @Id
    private Long id;
    private String name;
    private String email;
}
