import SwiftUI

struct TimelineVisualView: View {
    let effect: VisualEffectId?

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: effect?.gradient ?? [Color.gray.opacity(0.5), Color.gray.opacity(0.85)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .overlay {
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(.white.opacity(0.18), lineWidth: 1)
                }

            VStack(spacing: 8) {
                Text("Visuals")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.white.opacity(0.9))
                Text(effect?.displayName ?? "Idle")
                    .font(.headline)
                    .foregroundStyle(.white)
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: 180)
        .animation(.easeInOut(duration: 0.3), value: effect)
    }
}
