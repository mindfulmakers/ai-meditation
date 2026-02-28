//
//  HomeView.swift
//  AiMeditation
//
//  Main meditation dashboard after authentication.
//

import OpenbaseShared
import SwiftUI
import SwiftyJSON

struct HomeView: View {
    @StateObject private var viewModel = MeditationLibraryViewModel()
    @State private var showLogoutSheet = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Meditation Library")
                    .font(.largeTitle.bold())
                Text("Select a meditation and play its timeline events.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(.red)
                        .padding(10)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.red.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                }

                meditationListSection
                playbackSection
            }
            .padding()
        }
        .navigationTitle("AI Meditation")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showLogoutSheet = true
                } label: {
                    Label("Sign Out", systemImage: "rectangle.portrait.and.arrow.right")
                }
            }
        }
        .sheet(isPresented: $showLogoutSheet) {
            LogoutView()
                .presentationDetents([.medium])
        }
        .task {
            await viewModel.loadMeditations()
        }
        .onDisappear {
            viewModel.stopPlayback(resetMs: false)
        }
    }

    private var meditationListSection: some View {
        GroupBox("Available Meditations") {
            VStack(alignment: .leading, spacing: 10) {
                if viewModel.isLoadingMeditations {
                    ProgressView("Loading meditations...")
                        .frame(maxWidth: .infinity, alignment: .leading)
                } else if viewModel.meditations.isEmpty {
                    Text("No meditations available.")
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                } else {
                    ForEach(viewModel.meditations) { meditation in
                        if viewModel.selectedMeditation?.id == meditation.id {
                            Button {
                                viewModel.selectMeditation(id: meditation.id)
                            } label: {
                                Text(meditation.title)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            .buttonStyle(.borderedProminent)
                        } else {
                            Button {
                                viewModel.selectMeditation(id: meditation.id)
                            } label: {
                                Text(meditation.title)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var playbackSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .firstTextBaseline) {
                    Text(viewModel.selectedMeditation?.title ?? "Select a meditation")
                        .font(.headline)
                    Spacer(minLength: 8)
                    Text(viewModel.selectedMeditation.map { "\($0.durationMs) ms" } ?? "No selection")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                ProgressView(value: viewModel.progressValue)
                Text("\(viewModel.currentMs)ms / \(viewModel.selectedMeditation?.durationMs ?? 0)ms")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                HStack(spacing: 10) {
                    Button("Play Timeline") {
                        viewModel.playSelectedMeditation()
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(viewModel.selectedMeditation == nil || viewModel.isPlaying)

                    Button("Stop") {
                        viewModel.stopPlayback(resetMs: true)
                    }
                    .buttonStyle(.bordered)
                    .disabled(!viewModel.isPlaying && viewModel.currentMs == 0)
                }

                TimelineVisualView(effect: viewModel.activeEffect)

                GroupBox("Timeline Events") {
                    if viewModel.selectedTimeline.isEmpty {
                        Text("This meditation has no timeline events.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else {
                        VStack(spacing: 6) {
                            ForEach(Array(viewModel.selectedTimeline.enumerated()), id: \.offset) { _, event in
                                HStack {
                                    Text("\(event.atMs)ms")
                                        .font(.caption.monospacedDigit())
                                    Spacer(minLength: 8)
                                    Text(event.kindLabel)
                                        .font(.caption)
                                    Spacer(minLength: 8)
                                    Text(event.targetLabel)
                                        .lineLimit(1)
                                        .truncationMode(.middle)
                                        .font(.caption)
                                }
                                .padding(.horizontal, 8)
                                .padding(.vertical, 6)
                                .background(Color.secondary.opacity(0.08))
                                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                            }
                        }
                    }
                }

                GroupBox("Recent Triggers") {
                    if viewModel.recentTriggers.isEmpty {
                        Text("No events triggered yet.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else {
                        VStack(alignment: .leading, spacing: 6) {
                            ForEach(Array(viewModel.recentTriggers.enumerated()), id: \.offset) { _, entry in
                                Text(entry)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        } label: {
            Text("Playback")
        }
    }
}

#Preview {
    NavigationStack {
        HomeView()
            .environmentObject(AuthContext.shared)
            .environmentObject(AuthNavigationManager(authContext: AuthContext.shared))
    }
}
