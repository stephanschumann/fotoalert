// FotoAlert – Haupt-Feed

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var store: OpportunityStore

    var body: some View {
        TabView {
            OpportunityFeedView()
                .tabItem { Label("Chancen", systemImage: "sparkles") }

            MapView()
                .tabItem { Label("Karte", systemImage: "map") }

            LocationListView()
                .tabItem { Label("Locations", systemImage: "mappin.and.ellipse") }

            SettingsView()
                .tabItem { Label("Einstellungen", systemImage: "gear") }
        }
        .task { await store.load() }
    }
}

// MARK: - Feed

struct OpportunityFeedView: View {
    @EnvironmentObject var store: OpportunityStore
    @State private var showingDetail: PhotoOpportunity? = nil

    var body: some View {
        NavigationStack {
            Group {
                if store.isLoading && store.opportunities.isEmpty {
                    LoadingView()
                } else if let err = store.error {
                    ErrorView(message: err) {
                        Task { await store.load() }
                    }
                } else {
                    feedContent
                }
            }
            .navigationTitle("FotoAlert")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await store.refresh() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(store.isLoading)
                }
            }
            .sheet(item: $showingDetail) { opp in
                OpportunityDetailView(opportunity: opp)
            }
        }
    }

    var feedContent: some View {
        ScrollView {
            LazyVStack(spacing: 0, pinnedViews: .sectionHeaders) {
                // HIGH PRIORITY ALERT BANNER
                if !store.highPriorityOpportunities.isEmpty {
                    AlertBannerView(opportunities: store.highPriorityOpportunities) { opp in
                        showingDetail = opp
                    }
                    .padding(.horizontal)
                    .padding(.top, 8)
                }

                // HEUTE
                if !store.todayOpportunities.isEmpty {
                    Section {
                        ForEach(store.todayOpportunities) { opp in
                            OpportunityCard(opportunity: opp)
                                .padding(.horizontal)
                                .padding(.vertical, 4)
                                .onTapGesture { showingDetail = opp }
                        }
                    } header: {
                        SectionHeader(title: "Heute", icon: "sun.max")
                    }
                }

                // NÄCHSTE TAGE
                let grouped = Dictionary(grouping: store.upcomingOpportunities) { $0.relativeDayLabel }
                ForEach(grouped.keys.sorted(), id: \.self) { day in
                    Section {
                        ForEach(grouped[day] ?? []) { opp in
                            OpportunityCard(opportunity: opp)
                                .padding(.horizontal)
                                .padding(.vertical, 4)
                                .onTapGesture { showingDetail = opp }
                        }
                    } header: {
                        SectionHeader(title: day, icon: "calendar")
                    }
                }

                if let refresh = store.lastRefresh {
                    Text("Aktualisiert: \(refresh.formatted(date: .omitted, time: .shortened))")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .padding(.vertical, 16)
                }
            }
        }
        .refreshable {
            await store.refresh()
        }
    }
}

// MARK: - Alert Banner

struct AlertBannerView: View {
    let opportunities: [PhotoOpportunity]
    let onTap: (PhotoOpportunity) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Besondere Ereignisse", systemImage: "star.fill")
                .font(.subheadline.bold())
                .foregroundStyle(.yellow)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(opportunities) { opp in
                        AlertChip(opportunity: opp)
                            .onTapGesture { onTap(opp) }
                    }
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(.yellow.opacity(0.5), lineWidth: 1)
                )
        )
        .padding(.bottom, 8)
    }
}

struct AlertChip: View {
    let opportunity: PhotoOpportunity

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Image(systemName: opportunity.eventIcon)
                .font(.title2)
                .foregroundStyle(.yellow)
            Text(opportunity.relativeDayLabel)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(opportunity.location_name)
                .font(.caption.bold())
                .lineLimit(2)
        }
        .padding(12)
        .frame(width: 110)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

// MARK: - Opportunity Card

struct OpportunityCard: View {
    let opportunity: PhotoOpportunity

    var body: some View {
        HStack(spacing: 12) {
            // Score-Kreis
            ScoreCircle(score: opportunity.overall_score, priority: opportunity.alert_priority)
                .frame(width: 56, height: 56)

            VStack(alignment: .leading, spacing: 3) {
                HStack {
                    Image(systemName: opportunity.eventIcon)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(opportunity.event_type)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(opportunity.formattedShootTime)
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.primary)
                }

                Text(opportunity.title)
                    .font(.subheadline.bold())
                    .lineLimit(1)

                Text(opportunity.location_name)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)

                if let hint = opportunity.camera_hints.first {
                    HStack(spacing: 6) {
                        CameraTag(text: "\(hint.focal_length_mm)mm")
                        CameraTag(text: hint.aperture_suggestion)
                        if hint.tripod_required {
                            CameraTag(text: "Stativ", color: .orange)
                        }
                    }
                    .padding(.top, 2)
                }
            }
        }
        .padding(12)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .shadow(color: .black.opacity(0.06), radius: 4, y: 2)
    }
}

struct CameraTag: View {
    let text: String
    var color: Color = .blue

    var body: some View {
        Text(text)
            .font(.system(size: 10, weight: .medium))
            .foregroundStyle(color)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.12))
            .clipShape(Capsule())
    }
}

// MARK: - Score Circle

struct ScoreCircle: View {
    let score: Double
    let priority: Int

    var fillColor: Color {
        switch score {
        case 0.8...: return .green
        case 0.6..<0.8: return .yellow
        default: return .orange
        }
    }

    var body: some View {
        ZStack {
            Circle()
                .stroke(fillColor.opacity(0.2), lineWidth: 4)
            Circle()
                .trim(from: 0, to: score)
                .stroke(fillColor, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                .rotationEffect(.degrees(-90))
            VStack(spacing: 0) {
                Text("\(Int(score * 100))")
                    .font(.system(size: 16, weight: .bold, design: .rounded))
                Text("%")
                    .font(.system(size: 9, weight: .medium))
                    .foregroundStyle(.secondary)
            }
        }
        .overlay(alignment: .topTrailing) {
            if priority >= 2 {
                Image(systemName: "exclamationmark.circle.fill")
                    .font(.system(size: 12))
                    .foregroundStyle(.yellow)
                    .background(Circle().fill(Color(.systemBackground)))
            }
        }
    }
}

// MARK: - Section Header

struct SectionHeader: View {
    let title: String
    let icon: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(title)
                .font(.subheadline.bold())
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(.regularMaterial)
    }
}

// MARK: - Utilities

struct LoadingView: View {
    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
            Text("Berechne Foto-Chancen…")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct ErrorView: View {
    let message: String
    let onRetry: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "wifi.exclamationmark")
                .font(.largeTitle)
                .foregroundStyle(.secondary)
            Text("Verbindung fehlgeschlagen")
                .font(.headline)
            Text(message)
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            Button("Erneut versuchen", action: onRetry)
                .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
