import Foundation
import SwiftUI
import SwiftyJSON

// MARK: - Enums and Constants

/// Authentication flow types
public enum AuthFlow: String, CaseIterable {
    case login = "login"
    case loginByCode = "login_by_code"
    case signup = "signup"
    case verifyEmail = "verify_email"
    case providerRedirect = "provider_redirect"
    case providerSignup = "provider_signup"
    case mfaAuthenticate = "mfa_authenticate"
    case mfaReauthenticate = "mfa_reauthenticate"
    case reauthenticate = "reauthenticate"
    case mfaTrust = "mfa_trust"
    case mfaWebAuthnSignup = "mfa_webauthn_signup"
    case passwordResetByCode = "password_reset_by_code"
}

/// Authenticator types for MFA
public enum AuthenticatorType: String {
    case totp = "totp"
    case recoveryCodes = "recovery_codes"
    case webauthn = "webauthn"
}

/// Authentication process types
public enum AuthProcess: String {
    case login = "login"
    case connect = "connect"
}

// MARK: - API URLs

struct URLs {
    let baseUrl: String

    init(baseUrl: String) {
        self.baseUrl = baseUrl
    }

    // Meta
    var config: String { "\(baseUrl)/config" }

    // Account
    var changePassword: String { "\(baseUrl)/account/password/change" }
    var emailAddresses: String { "\(baseUrl)/account/email" }
    var authenticators: String { "\(baseUrl)/account/authenticators" }
    var totpAuthenticator: String { "\(baseUrl)/account/authenticators/totp" }
    var recoveryCodesAuthenticator: String { "\(baseUrl)/account/authenticators/recovery-codes" }
    var webauthnAuthenticator: String { "\(baseUrl)/account/authenticators/webauthn" }
    var providers: String { "\(baseUrl)/account/providers" }

    // Auth
    var session: String { "\(baseUrl)/auth/session" }
    var tokenRefresh: String { "\(baseUrl)/tokens/refresh" }
    var login: String { "\(baseUrl)/auth/login" }
    var reauthenticate: String { "\(baseUrl)/auth/reauthenticate" }
    var requestLoginCode: String { "\(baseUrl)/auth/code/request" }
    var confirmLoginCode: String { "\(baseUrl)/auth/code/confirm" }
    var signup: String { "\(baseUrl)/auth/signup" }
    var verifyEmail: String { "\(baseUrl)/auth/email/verify" }
    var requestPasswordReset: String { "\(baseUrl)/auth/password/request" }
    var resetPassword: String { "\(baseUrl)/auth/password/reset" }

    // MFA
    var mfaAuthenticate: String { "\(baseUrl)/auth/2fa/authenticate" }
    var mfaReauthenticate: String { "\(baseUrl)/auth/2fa/reauthenticate" }
    var mfaTrust: String { "\(baseUrl)/auth/2fa/trust" }
    var webauthnAuthenticate: String { "\(baseUrl)/auth/webauthn/authenticate" }
    var webauthnReauthenticate: String { "\(baseUrl)/auth/webauthn/reauthenticate" }
    var webauthnLogin: String { "\(baseUrl)/auth/webauthn/login" }
    var webauthnSignup: String { "\(baseUrl)/auth/webauthn/signup" }

    // Social
    var providerRedirect: String { "\(baseUrl)/auth/provider/redirect" }
    var providerToken: String { "\(baseUrl)/auth/provider/token" }
    var providerSignup: String { "\(baseUrl)/auth/provider/signup" }

    // Sessions
    var sessions: String { "\(baseUrl)/auth/sessions" }
}

// MARK: - Auth Change Event

public enum AuthChangeEvent: Equatable {
    case loggedIn
    case loggedOut
    case reauthenticated
    case reauthenticationRequired
    case flowUpdated
}

// MARK: - AllAuth Client

@MainActor
public class AllAuthClient: ObservableObject {
    public static let shared = AllAuthClient()

    // Settings
    public private(set) var baseUrl: String = ""
    private var urls: URLs!

    // Session token storage key
    private let sessionTokenKey = "allauth_session_token"

    // JWT token storage
    private let jwtRefreshTokenKey = "allauth_jwt_refresh_token"
    private var _jwtAccessToken: String?

    // Published auth change for UI updates
    @Published public var lastAuthChange: AuthChangeEvent?
    @Published public var lastAuthResponse: JSON?

    private init() {}

    // MARK: - Setup

    public func setup(baseUrl: String) {
        self.baseUrl = baseUrl
        self.urls = URLs(baseUrl: baseUrl)
    }

    // MARK: - Session Token Management

    public var sessionToken: String? {
        get {
            UserDefaults.standard.string(forKey: sessionTokenKey)
        }
        set {
            if let token = newValue {
                UserDefaults.standard.set(token, forKey: sessionTokenKey)
            } else {
                UserDefaults.standard.removeObject(forKey: sessionTokenKey)
            }
        }
    }

    // MARK: - JWT Token Management

    /// JWT access token (short-lived, stored in memory only)
    public var jwtAccessToken: String? {
        get { _jwtAccessToken }
        set { _jwtAccessToken = newValue }
    }

    /// JWT refresh token (long-lived, stored in Keychain)
    public var jwtRefreshToken: String? {
        get { KeychainHelper.read(key: jwtRefreshTokenKey) }
        set {
            if let token = newValue {
                try? KeychainHelper.save(key: jwtRefreshTokenKey, value: token)
            } else {
                KeychainHelper.delete(key: jwtRefreshTokenKey)
            }
        }
    }

    /// Clear all JWT tokens
    public func clearJWTTokens() {
        jwtAccessToken = nil
        jwtRefreshToken = nil
    }

    // MARK: - HTTP Request Handler

    public func request(
        method: String,
        url: String,
        data: [String: Any]? = nil,
        headers: [String: String] = [:],
        autoRefreshJWT: Bool = true
    ) async throws -> JSON {
        guard let requestUrl = URL(string: url) else {
            throw AllAuthError.invalidURL
        }

        var request = URLRequest(url: requestUrl)
        request.httpMethod = method

        // Set headers
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("django-allauth-swift-app", forHTTPHeaderField: "User-Agent")

        // Prefer JWT Bearer auth if available, otherwise use session token
        if let accessToken = jwtAccessToken {
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        } else if let token = sessionToken {
            request.setValue(token, forHTTPHeaderField: "X-Session-Token")
        }

        // Add custom headers
        for (key, value) in headers {
            request.setValue(value, forHTTPHeaderField: key)
        }

        // Set body for non-GET requests
        if let data = data, method != "GET" {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: data)
        }

        let acceptHeader = request.value(forHTTPHeaderField: "Accept") ?? "<none>"
        let contentTypeHeader = request.value(forHTTPHeaderField: "Content-Type") ?? "<none>"
        print("[AllAuthClient] \(method) \(url)")
        print("[AllAuthClient] request Accept: \(acceptHeader), Content-Type: \(contentTypeHeader)")

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AllAuthError.invalidResponse
        }

        let responseContentType = httpResponse.value(forHTTPHeaderField: "Content-Type") ?? "<none>"
        print("[AllAuthClient] HTTP \(httpResponse.statusCode), content-type: \(responseContentType), bytes: \(responseData.count)")
        print("[AllAuthClient] response body preview: \(responseBodyPreview(from: responseData))")
        if !responseContentType.lowercased().contains("application/json") {
            print("[AllAuthClient] WARNING: response content-type is not JSON")
        }

        // Handle 401 with JWT auto-refresh
        if httpResponse.statusCode == 401 && autoRefreshJWT && jwtRefreshToken != nil {
            _ = try await refreshJWT()
            return try await self.request(method: method, url: url, data: data, headers: headers, autoRefreshJWT: false)
        }

        let json = try JSON(data: responseData)

        // Handle session token from response
        if let newToken = json["meta"]["session_token"].string {
            sessionToken = newToken
        }

        // Handle JWT tokens from response (when using JWT token strategy).
        // allauth responses may provide tokens under either `data` or `meta`.
        if let accessToken = json["data"]["access_token"].string ?? json["meta"]["access_token"].string {
            jwtAccessToken = accessToken
        }
        if let refreshToken = json["data"]["refresh_token"].string ?? json["meta"]["refresh_token"].string {
            jwtRefreshToken = refreshToken
        }

        // Handle 410 Gone - token expired
        if httpResponse.statusCode == 410 {
            sessionToken = nil
            clearJWTTokens()
            throw AllAuthError.sessionExpired
        }

        // Dispatch auth change events only for auth-related responses
        if json["meta"]["is_authenticated"].exists() {
            await handleAuthChange(json: json, previousAuth: lastAuthResponse)
            lastAuthResponse = json
        }

        return json
    }

    private func responseBodyPreview(from data: Data) -> String {
        let maxBytes = 500
        let previewData = data.prefix(maxBytes)
        return String(data: previewData, encoding: .utf8) ?? "<non-utf8>"
    }

    private func handleAuthChange(json: JSON, previousAuth: JSON?) async {
        // Only process auth changes for responses that contain auth metadata
        // Non-auth endpoints (like /account/email) don't include this field
        guard json["meta"]["is_authenticated"].exists() else {
            return
        }

        let previouslyAuthenticated = previousAuth?["meta"]["is_authenticated"].bool ?? false
        let currentlyAuthenticated = json["meta"]["is_authenticated"].bool ?? false
        let status = json["status"].intValue

        if !previouslyAuthenticated && currentlyAuthenticated && status == 200 {
            lastAuthChange = .loggedIn
        } else if previouslyAuthenticated && !currentlyAuthenticated && status == 401 {
            lastAuthChange = .loggedOut
        } else if status == 401 {
            // Check for reauthentication flow
            let flows = json["data"]["flows"].arrayValue
            let hasReauthFlow = flows.contains { flow in
                flow["id"].string == AuthFlow.reauthenticate.rawValue ||
                flow["id"].string == AuthFlow.mfaReauthenticate.rawValue
            }
            if hasReauthFlow {
                lastAuthChange = .reauthenticationRequired
            }
        } else if status == 200 && json["data"]["flows"].exists() {
            lastAuthChange = .flowUpdated
        }
    }

    // MARK: - Meta Endpoints

    public func getConfig() async throws -> JSON {
        return try await request(method: "GET", url: urls.config)
    }

    // MARK: - Auth Endpoints

    public func getAuth() async throws -> JSON {
        return try await request(method: "GET", url: urls.session)
    }

    public func login(email: String, password: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.login,
            data: ["email": email, "password": password]
        )
    }

    public func login(username: String, password: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.login,
            data: ["username": username, "password": password]
        )
    }

    public func logout() async throws -> JSON {
        let result = try await request(method: "DELETE", url: urls.session)
        sessionToken = nil
        clearJWTTokens()
        return result
    }

    /// Refresh the JWT access token using the refresh token
    public func refreshJWT() async throws -> JSON {
        guard let refreshToken = jwtRefreshToken else {
            throw AllAuthError.apiError("No refresh token available")
        }
        return try await request(
            method: "POST",
            url: urls.tokenRefresh,
            data: ["refresh_token": refreshToken]
        )
    }

    public func signUp(email: String, password: String, username: String? = nil) async throws -> JSON {
        var data: [String: Any] = [
            "email": email,
            "password": password
        ]
        if let username = username {
            data["username"] = username
        }
        return try await request(method: "POST", url: urls.signup, data: data)
    }

    public func reauthenticate(password: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.reauthenticate,
            data: ["password": password]
        )
    }

    // MARK: - Login by Code (Passwordless)

    public func requestLoginCode(email: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.requestLoginCode,
            data: ["email": email]
        )
    }

    public func confirmLoginCode(code: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.confirmLoginCode,
            data: ["code": code]
        )
    }

    // MARK: - Password Reset

    public func requestPasswordReset(email: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.requestPasswordReset,
            data: ["email": email]
        )
    }

    public func getPasswordReset(key: String) async throws -> JSON {
        return try await request(
            method: "GET",
            url: urls.resetPassword,
            headers: ["X-Password-Reset-Key": key]
        )
    }

    public func resetPassword(key: String, password: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.resetPassword,
            data: ["key": key, "password": password]
        )
    }

    // MARK: - Email Verification

    public func getEmailVerification(key: String) async throws -> JSON {
        return try await request(
            method: "GET",
            url: urls.verifyEmail,
            headers: ["X-Email-Verification-Key": key]
        )
    }

    public func verifyEmail(key: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.verifyEmail,
            data: ["key": key]
        )
    }

    // MARK: - Email Address Management

    public func getEmailAddresses() async throws -> JSON {
        return try await request(method: "GET", url: urls.emailAddresses)
    }

    public func addEmailAddress(email: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.emailAddresses,
            data: ["email": email]
        )
    }

    public func deleteEmailAddress(email: String) async throws -> JSON {
        return try await request(
            method: "DELETE",
            url: urls.emailAddresses,
            data: ["email": email]
        )
    }

    public func setPrimaryEmailAddress(email: String) async throws -> JSON {
        return try await request(
            method: "PATCH",
            url: urls.emailAddresses,
            data: ["email": email, "primary": true]
        )
    }

    public func requestEmailVerification(email: String) async throws -> JSON {
        return try await request(
            method: "PUT",
            url: urls.emailAddresses,
            data: ["email": email]
        )
    }

    // MARK: - Password Change

    public func changePassword(currentPassword: String?, newPassword: String) async throws -> JSON {
        var data: [String: Any] = ["new_password": newPassword]
        if let current = currentPassword {
            data["current_password"] = current
        }
        return try await request(method: "POST", url: urls.changePassword, data: data)
    }

    // MARK: - MFA - TOTP

    public func getTOTPAuthenticator() async throws -> JSON {
        return try await request(method: "GET", url: urls.totpAuthenticator)
    }

    public func activateTOTP(code: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.totpAuthenticator,
            data: ["code": code]
        )
    }

    public func deactivateTOTP() async throws -> JSON {
        return try await request(method: "DELETE", url: urls.totpAuthenticator)
    }

    public func authenticateTOTP(code: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.mfaAuthenticate,
            data: ["code": code]
        )
    }

    public func reauthenticateTOTP(code: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.mfaReauthenticate,
            data: ["code": code]
        )
    }

    // MARK: - MFA - Recovery Codes

    public func getRecoveryCodes() async throws -> JSON {
        return try await request(method: "GET", url: urls.recoveryCodesAuthenticator)
    }

    public func generateRecoveryCodes() async throws -> JSON {
        return try await request(method: "POST", url: urls.recoveryCodesAuthenticator)
    }

    public func authenticateWithRecoveryCode(code: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.mfaAuthenticate,
            data: ["code": code]
        )
    }

    public func reauthenticateWithRecoveryCode(code: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.mfaReauthenticate,
            data: ["code": code]
        )
    }

    // MARK: - MFA - WebAuthn

    public func getWebAuthnAuthenticators() async throws -> JSON {
        return try await request(method: "GET", url: urls.webauthnAuthenticator)
    }

    public func addWebAuthnAuthenticator(name: String, credential: [String: Any]) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.webauthnAuthenticator,
            data: ["name": name, "credential": credential]
        )
    }

    public func updateWebAuthnAuthenticator(id: String, name: String) async throws -> JSON {
        return try await request(
            method: "PUT",
            url: urls.webauthnAuthenticator,
            data: ["id": id, "name": name]
        )
    }

    public func deleteWebAuthnAuthenticators(ids: [String]) async throws -> JSON {
        return try await request(
            method: "DELETE",
            url: urls.webauthnAuthenticator,
            data: ["authenticators": ids]
        )
    }

    public func getWebAuthnAuthenticateOptions() async throws -> JSON {
        return try await request(method: "GET", url: urls.webauthnAuthenticate)
    }

    public func authenticateWebAuthn(credential: [String: Any]) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.webauthnAuthenticate,
            data: ["credential": credential]
        )
    }

    public func getWebAuthnReauthenticateOptions() async throws -> JSON {
        return try await request(method: "GET", url: urls.webauthnReauthenticate)
    }

    public func reauthenticateWebAuthn(credential: [String: Any]) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.webauthnReauthenticate,
            data: ["credential": credential]
        )
    }

    public func getWebAuthnLoginOptions() async throws -> JSON {
        return try await request(method: "GET", url: urls.webauthnLogin)
    }

    public func loginWebAuthn(credential: [String: Any]) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.webauthnLogin,
            data: ["credential": credential]
        )
    }

    public func getWebAuthnSignupOptions() async throws -> JSON {
        return try await request(method: "GET", url: urls.webauthnSignup)
    }

    public func signupWebAuthn(name: String, credential: [String: Any]) async throws -> JSON {
        return try await request(
            method: "PUT",
            url: urls.webauthnSignup,
            data: ["name": name, "credential": credential]
        )
    }

    public func getPasswordlessWebAuthnOptions() async throws -> JSON {
        return try await request(
            method: "GET",
            url: "\(urls.webauthnAuthenticator)?passwordless"
        )
    }

    // MARK: - MFA - Trust

    public func trustDevice() async throws -> JSON {
        return try await request(method: "POST", url: urls.mfaTrust)
    }

    // MARK: - Authenticators List

    public func getAuthenticators() async throws -> JSON {
        return try await request(method: "GET", url: urls.authenticators)
    }

    // MARK: - Social Account Providers

    public func getProviders() async throws -> JSON {
        return try await request(method: "GET", url: urls.providers)
    }

    public func disconnectProvider(providerId: String, accountUid: String) async throws -> JSON {
        return try await request(
            method: "DELETE",
            url: urls.providers,
            data: ["provider": providerId, "account": accountUid]
        )
    }

    public func authenticateWithProviderToken(
        providerId: String,
        token: String,
        tokenType: String = "access_token",
        process: AuthProcess = .login
    ) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.providerToken,
            data: [
                "provider": providerId,
                "token": ["access_token": token],
                "process": process.rawValue
            ]
        )
    }

    public func completeProviderSignup(email: String) async throws -> JSON {
        return try await request(
            method: "POST",
            url: urls.providerSignup,
            data: ["email": email]
        )
    }

    // MARK: - Sessions Management

    public func getSessions() async throws -> JSON {
        return try await request(method: "GET", url: urls.sessions)
    }

    public func deleteSessions(ids: [String]) async throws -> JSON {
        return try await request(
            method: "DELETE",
            url: urls.sessions,
            data: ["sessions": ids]
        )
    }
}

// MARK: - Errors

public enum AllAuthError: LocalizedError {
    case invalidURL
    case invalidResponse
    case sessionExpired
    case apiError(String)

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .sessionExpired:
            return "Session expired. Please log in again."
        case .apiError(let message):
            return message
        }
    }
}

// MARK: - JSON Response Helpers

public extension JSON {
    /// Check if the response indicates success (status 200)
    var isSuccess: Bool {
        return self["status"].intValue == 200
    }

    /// Check if authentication is required
    var requiresAuth: Bool {
        return self["status"].intValue == 401
    }

    /// Check if there are pending flows
    var hasPendingFlows: Bool {
        return self["data"]["flows"].arrayValue.contains { $0["is_pending"].boolValue }
    }

    /// Get specific pending flow
    func pendingFlow(of type: AuthFlow) -> JSON? {
        return self["data"]["flows"].arrayValue.first {
            $0["id"].string == type.rawValue && $0["is_pending"].boolValue
        }
    }

    /// Get all errors
    var errors: [(param: String?, message: String)] {
        return self["errors"].arrayValue.map { error in
            (error["param"].string, error["message"].stringValue)
        }
    }

    /// Get error for specific field
    func error(for field: String) -> String? {
        return self["errors"].arrayValue.first { $0["param"].string == field }?["message"].string
    }

    /// Get general errors (not associated with a field)
    var generalErrors: [String] {
        return self["errors"].arrayValue
            .filter { $0["param"].string == nil }
            .map { $0["message"].stringValue }
    }

    /// Get user from auth response
    var user: JSON? {
        return self["data"]["user"].exists() ? self["data"]["user"] : nil
    }

    /// Check if user is authenticated
    var isAuthenticated: Bool {
        return self["meta"]["is_authenticated"].bool ?? false
    }
}
