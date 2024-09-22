import Fluent

struct CreateFitnessData: Migration {
    func prepare(on database: Database) -> EventLoopFuture<Void> {
        database.schema("fitness_data")
            .id()
            .field("user_id", .uuid, .required, .references("users", "id"))
            .field("type", .string, .required)
            .field("value", .double, .required)
            .field("date", .datetime, .required)
            .create()
    }

    func revert(on database: Database) -> EventLoopFuture<Void> {
        database.schema("fitness_data").delete()
    }
}
