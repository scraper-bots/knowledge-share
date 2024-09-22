import Fluent
import Vapor

final class FitnessData: Model, Content, @unchecked Sendable {
    static let schema = "fitness_data"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "steps")
    var steps: Int

    @Field(key: "calories")
    var calories: Int

    @Field(key: "date")
    var date: Date

    @Parent(key: "user_id")
    var user: User

    init() {}

    init(id: UUID? = nil, steps: Int, calories: Int, date: Date, userID: UUID) {
        self.id = id
        self.steps = steps
        self.calories = calories
        self.date = date
        self.$user.id = userID
    }
}
