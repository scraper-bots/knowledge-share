// swift-tools-version:5.10
import PackageDescription

let swiftSettings: [SwiftSetting] = [
    .enableUpcomingFeature("DisableOutwardActorInference"),
    .enableExperimentalFeature("StrictConcurrency"),
]

let package = Package(
    name: "FitnessBackend",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        // Vapor framework
        .package(url: "https://github.com/vapor/vapor.git", from: "4.65.2"),
        // Fluent ORM
        .package(url: "https://github.com/vapor/fluent.git", from: "4.5.0"),
        // Fluent PostgreSQL driver
        .package(url: "https://github.com/vapor/fluent-postgres-driver.git", from: "2.5.0"),
    ],
    targets: [
        // Application library target
        .target(
            name: "App",
            dependencies: [
                .product(name: "Vapor", package: "vapor"),
                .product(name: "Fluent", package: "fluent"),
                .product(name: "FluentPostgresDriver", package: "fluent-postgres-driver"),
            ],
            swiftSettings: [
                // Apply unsafe flags to suppress concurrency warnings in the App target
                .unsafeFlags([
                    "-Xfrontend", "-warn-concurrency",
                    "-Xfrontend", "-enable-actor-data-race-checks",
                    "-Xfrontend", "-disable-implicit-concurrency-module-import"
                ])
            ]
        ),
        // Executable target
        .executableTarget(
            name: "Run",
            dependencies: [
                .target(name: "App"),
            ],
            path: "Sources/Run",
            swiftSettings: swiftSettings
        ),
        // Test target
        .testTarget(
            name: "AppTests",
            dependencies: [
                .target(name: "App"),
                .product(name: "XCTVapor", package: "vapor"),
            ],
            swiftSettings: swiftSettings
        ),
    ]
)
