import Fluent
import Vapor

final class User: Model, Content, @unchecked Sendable {
    static let schema = "users"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "username")
    var username: String

    @Field(key: "passwordHash")
    var passwordHash: String

    init() {}

    init(id: UUID? = nil, username: String, passwordHash: String) {
        self.id = id
        self.username = username
        self.passwordHash = passwordHash
    }
}

// Extensions for additional functionality
extension User {
    struct Create: Content {
        let username: String
        let password: String
    }

    struct Public: Content {
        let id: UUID?
        let username: String
    }

    func convertToPublic() -> Public {
        Public(id: id, username: username)
    }

    struct Login: Content {
        let username: String
        let password: String
    }
}
