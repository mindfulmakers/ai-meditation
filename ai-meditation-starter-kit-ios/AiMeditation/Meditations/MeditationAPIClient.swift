import Foundation
import OpenbaseShared
import SwiftyJSON

enum MeditationAPIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case missingJWTToken
    case httpError(statusCode: Int)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The meditations endpoint URL is invalid."
        case .invalidResponse:
            return "The server returned an invalid response."
        case .missingJWTToken:
            return "No JWT token is available. Please log in again."
        case let .httpError(statusCode):
            return "The server returned status code \(statusCode)."
        }
    }
}

@MainActor
final class MeditationAPIClient {
    private let authClient: AllAuthClient

    init(authClient: AllAuthClient) {
        self.authClient = authClient
    }

    static func live() -> MeditationAPIClient {
        MeditationAPIClient(authClient: .shared)
    }

    func fetchMeditations() async throws -> [MeditationRecord] {
        print("[MeditationAPIClient] fetchMeditations called, url: \(Constants.meditationsUrl)")
        guard let url = URL(string: Constants.meditationsUrl) else {
            print("[MeditationAPIClient] ERROR: invalid URL")
            throw MeditationAPIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("django-allauth-swift-app", forHTTPHeaderField: "User-Agent")

        let data = try await fetchAuthorizedData(request: request, mayRefreshJWT: true)
        print("[MeditationAPIClient] response data (\(data.count) bytes): \(String(data: data.prefix(500), encoding: .utf8) ?? "<non-utf8>")")
        let json = try JSON(data: data)
        guard let payload = json.array else {
            print("[MeditationAPIClient] WARNING: response is not a JSON array, got: \(json.type)")
            return []
        }

        let records = payload.compactMap(MeditationRecord.init(json:))
        print("[MeditationAPIClient] parsed \(records.count) meditations from \(payload.count) items")
        return records
    }

    func fetchAudioData(filePathOrUrl: String) async throws -> Data {
        guard let url = resolvedAudioURL(from: filePathOrUrl) else {
            throw MeditationAPIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("*/*", forHTTPHeaderField: "Accept")
        request.setValue("django-allauth-swift-app", forHTTPHeaderField: "User-Agent")

        return try await fetchAuthorizedData(request: request, mayRefreshJWT: true)
    }

    private func fetchAuthorizedData(request: URLRequest, mayRefreshJWT: Bool) async throws -> Data {
        var authorizedRequest = request
        print("[MeditationAPIClient] getAccessToken...")
        let accessToken = try await getAccessToken()
        print("[MeditationAPIClient] got token: \(accessToken)")
        authorizedRequest.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        let acceptHeader = authorizedRequest.value(forHTTPHeaderField: "Accept") ?? "<none>"
        print("[MeditationAPIClient] request Accept: \(acceptHeader)")

        print("[MeditationAPIClient] sending \(authorizedRequest.httpMethod ?? "?") \(authorizedRequest.url?.absoluteString ?? "nil")")
        let (data, response) = try await URLSession.shared.data(for: authorizedRequest)
        print("[MeditationAPIClient] received response, \(data.count) bytes")

        guard let httpResponse = response as? HTTPURLResponse else {
            print("[MeditationAPIClient] ERROR: response is not HTTPURLResponse")
            throw MeditationAPIError.invalidResponse
        }

        let contentType = httpResponse.value(forHTTPHeaderField: "Content-Type") ?? "<none>"
        print("[MeditationAPIClient] HTTP \(httpResponse.statusCode), content-type: \(contentType)")

        if httpResponse.statusCode == 401,
           mayRefreshJWT,
           authClient.jwtRefreshToken != nil {
            print("[MeditationAPIClient] 401 – refreshing JWT and retrying")
            _ = try await authClient.refreshJWT()
            return try await fetchAuthorizedData(request: request, mayRefreshJWT: false)
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            print("[MeditationAPIClient] ERROR: HTTP \(httpResponse.statusCode), body: \(String(data: data.prefix(500), encoding: .utf8) ?? "<non-utf8>")")
            throw MeditationAPIError.httpError(statusCode: httpResponse.statusCode)
        }

        if !contentType.lowercased().hasPrefix("audio/") {
            print("[MeditationAPIClient] response body preview: \(String(data: data.prefix(500), encoding: .utf8) ?? "<non-utf8>")")
        }

        return data
    }

    private func resolvedAudioURL(from filePathOrUrl: String) -> URL? {
        if let absoluteURL = URL(string: filePathOrUrl), absoluteURL.scheme != nil {
            return absoluteURL
        }

        guard let baseURL = URL(string: Constants.apiBaseUrl) else {
            return nil
        }

        return URL(string: filePathOrUrl, relativeTo: baseURL)?.absoluteURL
    }

    private func getAccessToken() async throws -> String {
        if let accessToken = authClient.jwtAccessToken, !accessToken.isEmpty {
            return accessToken
        }

        if authClient.jwtRefreshToken != nil {
            _ = try await authClient.refreshJWT()
            if let refreshedToken = authClient.jwtAccessToken, !refreshedToken.isEmpty {
                return refreshedToken
            }
        }

        throw MeditationAPIError.missingJWTToken
    }
}
