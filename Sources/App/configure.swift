import Fluent
import FluentPostgresDriver
import Vapor

public func configure(_ app: Application) throws {
    // Database configuration
    let hostname = Environment.get("DB_HOST") ?? "localhost"
    let port = Environment.get("DB_PORT").flatMap(Int.init) ?? 5432
    let username = Environment.get("DB_USER") ?? "postgres"
    let password = Environment.get("DB_PASSWORD") ?? ""
    let database = Environment.get("DB_NAME") ?? "postgres"

    var tlsConfiguration: TLSConfiguration?
    if Environment.get("DB_TLS") == "true" {
        tlsConfiguration = TLSConfiguration.makeClientConfiguration()
        tlsConfiguration?.certificateVerification = .none // Adjust as needed
    }

    // Updated to use the new 'postgres' method with 'PostgresConfiguration'
    let postgresConfig = PostgresConfiguration(
        hostname: hostname,
        port: port,
        username: username,
        password: password,
        database: database,
        tlsConfiguration: tlsConfiguration
    )

    app.databases.use(.postgres(
        configuration: postgresConfig
    ), as: .psql)

    // Register migrations
    app.migrations.add(CreateUser())
    app.migrations.add(CreateFitnessData())
    app.migrations.add(CreateToken())

    // Automatically run migrations
    try app.autoMigrate().wait()

    // Register routes
    try routes(app)
}
