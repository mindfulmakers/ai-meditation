import AVFoundation
import CoreHaptics
import Foundation

enum MeditationHapticsError: LocalizedError {
    case missingAHAPFile
    case unsupportedAHAPPayload
    case hapticsUnavailable

    var errorDescription: String? {
        switch self {
        case .missingAHAPFile:
            return "AHAP event is missing its file."
        case .unsupportedAHAPPayload:
            return "The AHAP file payload is invalid."
        case .hapticsUnavailable:
            return "Haptics are unavailable on this device."
        }
    }
}

@MainActor
final class MeditationLibraryViewModel: ObservableObject {
    @Published var meditations: [MeditationRecord] = []
    @Published var isLoadingMeditations = false
    @Published var selectedMeditationId: String?
    @Published var isPlaying = false
    @Published var currentMs = 0
    @Published var recentTriggers: [String] = []
    @Published var activeEffect: VisualEffectId?
    @Published var errorMessage: String?

    var selectedMeditation: MeditationRecord? {
        guard let selectedMeditationId else {
            return nil
        }
        return meditations.first { $0.id == selectedMeditationId }
    }

    var selectedTimeline: [PlaybackEvent] {
        guard let selectedMeditation else {
            return []
        }

        return PlaybackEvent.extract(from: selectedMeditation.timelineEntries)
    }

    var progressValue: Double {
        guard let selectedMeditation else {
            return 0
        }

        let denominator = max(1, selectedMeditation.durationMs)
        let clampedCurrent = max(0, currentMs)
        return min(1, Double(clampedCurrent) / Double(denominator))
    }

    private let apiClient: MeditationAPIClient
    private var progressTask: Task<Void, Never>?
    private var playbackStartDate: Date?
    private var scheduledWorkItems: [DispatchWorkItem] = []
    private var activeAudioPlayers: [AVAudioPlayer] = []
    private var hapticEngine: CHHapticEngine?
    private var activeHapticPlayers: [CHHapticPatternPlayer] = []

    init(apiClient: MeditationAPIClient? = nil) {
        self.apiClient = apiClient ?? .live()
    }

    deinit {
        progressTask?.cancel()
        for item in scheduledWorkItems {
            item.cancel()
        }
        for player in activeAudioPlayers {
            player.stop()
        }
        for player in activeHapticPlayers {
            try? player.stop(atTime: CHHapticTimeImmediate)
        }
        hapticEngine?.stop()
    }

    func loadMeditations() async {
        guard !isLoadingMeditations else {
            return
        }

        isLoadingMeditations = true
        errorMessage = nil

        do {
            let fetchedMeditations = try await apiClient.fetchMeditations()
            meditations = fetchedMeditations

            if selectedMeditationId == nil {
                selectedMeditationId = fetchedMeditations.first?.id
            }
        } catch {
            print("[MeditationLibraryVM] loadMeditations error: \(error)")
            errorMessage = "Failed to load meditations: \(error.localizedDescription)"
        }

        isLoadingMeditations = false
    }

    func selectMeditation(id: String) {
        stopPlayback(resetMs: true)
        recentTriggers = []
        selectedMeditationId = id
    }

    func playSelectedMeditation() {
        guard let selectedMeditation else {
            return
        }

        stopPlayback(resetMs: true)
        recentTriggers = []
        errorMessage = nil
        isPlaying = true

        let events = PlaybackEvent.extract(from: selectedMeditation.timelineEntries)
        let duration = max(0, selectedMeditation.durationMs)
        playbackStartDate = Date()

        progressTask?.cancel()
        progressTask = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                guard let self,
                      let playbackStartDate = self.playbackStartDate else {
                    return
                }

                self.currentMs = max(0, Int(Date().timeIntervalSince(playbackStartDate) * 1000))
                try? await Task.sleep(nanoseconds: 100_000_000)
            }
        }

        for event in events {
            let workItem = DispatchWorkItem { [weak self] in
                self?.handlePlaybackEvent(event)
            }
            scheduledWorkItems.append(workItem)
            DispatchQueue.main.asyncAfter(deadline: .now() + .milliseconds(event.atMs), execute: workItem)
        }

        let completionWorkItem = DispatchWorkItem { [weak self] in
            guard let self else {
                return
            }
            self.stopPlayback(resetMs: false)
            self.currentMs = duration
        }

        scheduledWorkItems.append(completionWorkItem)
        DispatchQueue.main.asyncAfter(deadline: .now() + .milliseconds(duration), execute: completionWorkItem)
    }

    func stopPlayback(resetMs: Bool) {
        for workItem in scheduledWorkItems {
            workItem.cancel()
        }
        scheduledWorkItems.removeAll()

        progressTask?.cancel()
        progressTask = nil
        playbackStartDate = nil

        for player in activeAudioPlayers {
            player.stop()
            player.currentTime = 0
        }
        activeAudioPlayers.removeAll()

        for player in activeHapticPlayers {
            do {
                try player.stop(atTime: CHHapticTimeImmediate)
            } catch {
                print("[MeditationLibraryVM] stop haptic player error: \(error)")
            }
        }
        activeHapticPlayers.removeAll()

        hapticEngine?.stop()
        self.hapticEngine = nil

        isPlaying = false
        activeEffect = nil

        if resetMs {
            currentMs = 0
        }
    }

    private func handlePlaybackEvent(_ event: PlaybackEvent) {
        switch event.kind {
        case .wav:
            if let file = event.file {
                Task { [weak self] in
                    await self?.playAudio(file: file, atMs: event.atMs)
                }
            }

        case .effect:
            guard let effectId = event.effectId else {
                appendRecentTrigger("[\(event.atMs)ms] effect error: missing effect id")
                return
            }

            guard let resolvedEffect = VisualEffectId(rawValue: effectId) else {
                appendRecentTrigger("[\(event.atMs)ms] effect error: \(effectId)")
                errorMessage = "No visual animation mapped for effect \"\(effectId)\"."
                currentMs = event.atMs
                stopPlayback(resetMs: false)
                return
            }

            activeEffect = resolvedEffect

        case .ahap:
            Task { [weak self] in
                await self?.playAHAP(event: event)
            }

        case .unknown:
            break
        }

        appendRecentTrigger(event.triggerDescription)
    }

    private func playAudio(file: String, atMs: Int) async {
        do {
            let audioData = try await apiClient.fetchAudioData(filePathOrUrl: file)
            let player = try AVAudioPlayer(data: audioData)
            player.prepareToPlay()

            activeAudioPlayers = activeAudioPlayers.filter(\.isPlaying)
            activeAudioPlayers.append(player)
            player.play()
        } catch {
            appendRecentTrigger("[\(atMs)ms] wav error: \(file)")
            errorMessage = "Audio playback failed: \(error.localizedDescription)"
        }
    }

    private func playAHAP(event: PlaybackEvent) async {
        guard let file = event.file else {
            appendRecentTrigger("[\(event.atMs)ms] ahap error: missing file")
            errorMessage = MeditationHapticsError.missingAHAPFile.localizedDescription
            return
        }

        do {
            let payload = try await apiClient.fetchAudioData(filePathOrUrl: file)
            let pattern = try pattern(from: payload)
            let engine = try configuredHapticEngine()
            let player = try engine.makePlayer(with: pattern)
            activeHapticPlayers.append(player)
            try player.start(atTime: CHHapticTimeImmediate)
        } catch {
            appendRecentTrigger("[\(event.atMs)ms] ahap error: \(file)")
            errorMessage = "Haptic playback failed: \(error.localizedDescription)"
        }
    }

    private func pattern(from payload: Data) throws -> CHHapticPattern {
        let temporaryPatternURL = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("ahap")
        defer {
            try? FileManager.default.removeItem(at: temporaryPatternURL)
        }

        do {
            try payload.write(to: temporaryPatternURL, options: .atomic)
            return try CHHapticPattern(contentsOf: temporaryPatternURL)
        } catch {
            throw MeditationHapticsError.unsupportedAHAPPayload
        }
    }

    private func configuredHapticEngine() throws -> CHHapticEngine {
        if let hapticEngine {
            try hapticEngine.start()
            return hapticEngine
        }

        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else {
            throw MeditationHapticsError.hapticsUnavailable
        }

        let hapticEngine = try CHHapticEngine()
        hapticEngine.resetHandler = { [weak self] in
            Task { @MainActor [weak self] in
                guard let self else {
                    return
                }
                do {
                    try self.hapticEngine?.start()
                } catch {
                    print("[MeditationLibraryVM] haptic engine restart error: \(error)")
                }
            }
        }

        self.hapticEngine = hapticEngine
        try hapticEngine.start()
        return hapticEngine
    }

    private func appendRecentTrigger(_ entry: String) {
        var next = recentTriggers
        next.insert(entry, at: 0)
        recentTriggers = Array(next.prefix(8))
    }
}
