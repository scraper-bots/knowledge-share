import Fluent
import Vapor

struct UserController: RouteCollection {
    func boot(routes: RoutesBuilder) throws {
        let users = routes.grouped("users")
        users.post("register", use: register)
        users.post("login", use: login)
    }

    // No changes needed for the functions, but ensure they are thread-safe
    func register(req: Request) throws -> EventLoopFuture<User.Public> {
        let create = try req.content.decode(User.Create.self)
        let passwordHash = try Bcrypt.hash(create.password)
        let user = User(username: create.username, passwordHash: passwordHash)
        return user.save(on: req.db).map {
            user.convertToPublic()
        }
    }

    func login(req: Request) throws -> EventLoopFuture<Token> {
        let userLogin = try req.content.decode(User.Login.self)
        return User.query(on: req.db)
            .filter(\.$username == userLogin.username)
            .first()
            .unwrap(or: Abort(.unauthorized))
            .flatMap { user in
                do {
                    if try Bcrypt.verify(userLogin.password, created: user.passwordHash) {
                        let tokenValue = [UInt8].random(count: 16).base64
                        let token = Token(value: tokenValue, userID: try user.requireID())
                        return token.save(on: req.db).map { token }
                    } else {
                        return req.eventLoop.future(error: Abort(.unauthorized))
                    }
                } catch {
                    return req.eventLoop.future(error: error)
                }
            }
    }
}
