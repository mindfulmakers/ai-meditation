import Foundation
import SwiftUI
import SwiftyJSON

struct MeditationRecord: Identifiable, Equatable {
    let id: String
    let title: String
    let durationMs: Int
    let timelineEntries: [JSON]

    init?(json: JSON) {
        guard let id = json["id"].string,
              let title = json["title"].string,
              let durationMs = json["durationMs"].int else {
            return nil
        }

        self.id = id
        self.title = title
        self.durationMs = max(0, durationMs)
        self.timelineEntries = json["timeline"].arrayValue
    }
}

enum PlaybackEventKind: String, Equatable {
    case wav
    case effect
    case ahap
    case unknown
}

struct PlaybackEvent: Equatable {
    let atMs: Int
    let kind: PlaybackEventKind
    let rawKind: String
    let file: String?
    let effectId: String?

    static func extract(from timelineEntries: [JSON]) -> [PlaybackEvent] {
        timelineEntries
            .map { entry in
                let atMs = max(0, entry["atMs"].int ?? 0)
                let rawKind = entry["kind"].string ?? "unknown"
                let file = entry["file"].string
                let effectId = entry["effectId"].string

                if rawKind == "wav", file != nil {
                    return PlaybackEvent(
                        atMs: atMs,
                        kind: .wav,
                        rawKind: rawKind,
                        file: file,
                        effectId: effectId
                    )
                }

                if rawKind == "effect", effectId != nil {
                    return PlaybackEvent(
                        atMs: atMs,
                        kind: .effect,
                        rawKind: rawKind,
                        file: file,
                        effectId: effectId
                    )
                }

                if rawKind == "ahap" {
                    return PlaybackEvent(
                        atMs: atMs,
                        kind: .ahap,
                        rawKind: rawKind,
                        file: file,
                        effectId: effectId
                    )
                }

                return PlaybackEvent(
                    atMs: atMs,
                    kind: .unknown,
                    rawKind: rawKind,
                    file: file,
                    effectId: effectId
                )
            }
            .sorted { first, second in first.atMs < second.atMs }
    }

    var kindLabel: String {
        kind == .unknown ? rawKind : kind.rawValue
    }

    var targetLabel: String {
        switch kind {
        case .wav, .ahap:
            return file ?? "trigger"
        case .effect:
            return effectId ?? "trigger"
        case .unknown:
            return file ?? effectId ?? "trigger"
        }
    }

    var triggerDescription: String {
        switch kind {
        case .effect:
            return "[\(atMs)ms] effect: \(effectId ?? "unknown")"
        case .wav:
            return "[\(atMs)ms] wav: \(file ?? "unknown")"
        case .ahap:
            if let file {
                return "[\(atMs)ms] ahap: \(file)"
            }
            return "[\(atMs)ms] ahap"
        case .unknown:
            return "[\(atMs)ms] \(rawKind)"
        }
    }
}

enum VisualEffectId: String, CaseIterable {
    case calmBreath = "calm-breath"
    case softPulse = "soft-pulse"
    case starfield = "starfield"

    var displayName: String {
        switch self {
        case .calmBreath:
            return "Calm Breath"
        case .softPulse:
            return "Soft Pulse"
        case .starfield:
            return "Starfield"
        }
    }

    var gradient: [Color] {
        switch self {
        case .calmBreath:
            return [Color.cyan.opacity(0.9), Color.blue.opacity(0.7)]
        case .softPulse:
            return [Color.mint.opacity(0.8), Color.teal.opacity(0.8)]
        case .starfield:
            return [Color.indigo.opacity(0.85), Color.black.opacity(0.95)]
        }
    }
}
