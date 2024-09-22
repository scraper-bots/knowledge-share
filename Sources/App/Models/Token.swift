import Fluent
import Vapor

final class Token: Model, Content, @unchecked Sendable {
    static let schema = "tokens"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "value")
    var value: String

    @Parent(key: "user_id")
    var user: User

    @Field(key: "created_at")
    var createdAt: Date?

    init() {}

    init(id: UUID? = nil, value: String, userID: UUID, createdAt: Date = Date()) {
        self.id = id
        self.value = value
        self.$user.id = userID
        self.createdAt = createdAt
    }
}
