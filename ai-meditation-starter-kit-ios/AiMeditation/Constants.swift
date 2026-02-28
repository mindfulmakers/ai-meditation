//
//  Constants.swift
//  AiMeditation
//
//  Configuration constants
//

import Foundation

enum Constants {
    // MARK: - API Configuration

    /// Base URL for the API backend.
    static var apiBaseUrl: String {
        "http://100.81.0.19"
    }

    /// AllAuth URL for authentication.
    static var allAuthUrl: String {
        "\(normalizedApiBaseUrl)/_allauth/app/v1"
    }

    /// Meditations endpoint mirroring the React app default path.
    static var meditationsUrl: String {
        "\(normalizedApiBaseUrl)/api/ai_meditation_starter_kit/meditations/"
    }

    private static var normalizedApiBaseUrl: String {
        apiBaseUrl.hasSuffix("/") ? String(apiBaseUrl.dropLast()) : apiBaseUrl
    }
}
