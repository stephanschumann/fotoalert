// FotoAlert – Opportunity-Detail-Ansicht

import SwiftUI
import MapKit

struct OpportunityDetailView: View {
    let opportunity: PhotoOpportunity
    @Environment(\.dismiss) var dismiss
    @State private var reminderSet = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {

                    // HERO HEADER
                    heroHeader

                    // SCORE BREAKDOWN
                    scoreBreakdown
                        .padding(.horizontal)

                    Divider().padding(.horizontal)

                    // ASTRONOMIE
                    astronomySection
                        .padding(.horizontal)

                    Divider().padding(.horizontal)

                    // KAMERA-EMPFEHLUNGEN
                    cameraSection
                        .padding(.horizontal)

                    Divider().padding(.horizontal)

                    // ZEITFENSTER
                    timeWindowSection
                        .padding(.horizontal)

                    Divider().padding(.horizontal)

                    // MINI-KARTE
                    mapSection

                    // AKTIONEN
                    actionButtons
                        .padding(.horizontal)
                        .padding(.bottom, 32)
                }
            }
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Schließen") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    ShareLink(item: shareText)
                }
            }
        }
    }

    // MARK: Hero Header

    var heroHeader: some View {
        ZStack(alignment: .bottomLeading) {
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [.indigo.opacity(0.8), .purple.opacity(0.5)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(height: 200)

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Image(systemName: opportunity.eventIcon)
                        .font(.title2)
                    Text(opportunity.event_type)
                        .font(.subheadline)
                }
                .foregroundStyle(.white.opacity(0.9))

                Text(opportunity.title)
                    .font(.title2.bold())
                    .foregroundStyle(.white)

                HStack {
                    Image(systemName: "mappin.fill")
                    Text(opportunity.location_name)
                }
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.8))
            }
            .padding()

            // Score-Overlay
            HStack {
                Spacer()
                VStack {
                    Text("\(opportunity.scorePercent)%")
                        .font(.system(size: 36, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                    Text("Score")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.7))
                }
                .padding()
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 0))
    }

    // MARK: Score Breakdown

    var scoreBreakdown: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Score-Übersicht")
                .font(.headline)

            HStack(spacing: 16) {
                ScoreBar(label: "Astronomie", value: opportunity.astronomy_score, color: .purple)
                ScoreBar(label: "Wetter", value: opportunity.weather_score, color: .blue)
                ScoreBar(label: "Location", value: opportunity.location_score, color: .green)
            }

            if !opportunity.description.isEmpty {
                Text(opportunity.description)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .padding(.top, 4)
            }
        }
    }

    // MARK: Astronomie

    var astronomySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Astronomie", systemImage: "moon.stars.fill")
                .font(.headline)

            if let phase = opportunity.moon_phase, let illum = opportunity.moon_illumination_pct {
                InfoRow(icon: "moon.fill", label: "Mondphase", value: "\(phase) (\(Int(illum))%)")
            }
            if let az = opportunity.celestial_azimuth {
                InfoRow(icon: "arrow.up.right.circle", label: "Azimut (Himmelsobjekt)", value: "\(Int(az))°")
            }
            if let alt = opportunity.celestial_altitude {
                InfoRow(icon: "arrow.up", label: "Höhe", value: "\(String(format: "%.1f", alt))°")
            }
            if let subAz = opportunity.subject_azimuth {
                InfoRow(icon: "mappin.circle", label: "Azimut (Motiv)", value: "\(Int(subAz))°")
            }
            if let sunrise = opportunity.sunrise_utc {
                InfoRow(icon: "sunrise.fill", label: "Sonnenaufgang",
                        value: sunrise.formatted(date: .omitted, time: .shortened) + " (UTC)")
            }
            if let sunset = opportunity.sunset_utc {
                InfoRow(icon: "sunset.fill", label: "Sonnenuntergang",
                        value: sunset.formatted(date: .omitted, time: .shortened) + " (UTC)")
            }
        }
    }

    // MARK: Kamera

    var cameraSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Kamera-Empfehlungen", systemImage: "camera.fill")
                .font(.headline)

            ForEach(opportunity.camera_hints, id: \.focal_length_mm) { hint in
                CameraHintCard(hint: hint)
            }
        }
    }

    // MARK: Zeitfenster

    var timeWindowSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Zeitfenster (Ortszeit Berlin)", systemImage: "clock.fill")
                .font(.headline)

            let tz = TimeZone(identifier: "Europe/Berlin")!

            HStack {
                VStack(alignment: .leading) {
                    Text("Optimal")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(opportunity.shoot_time.formatted(
                        .dateTime.hour().minute().timeZone(TimeZoneOverride.specific(tz))
                    ))
                    .font(.title3.bold().monospacedDigit())
                }
                Spacer()
                VStack(alignment: .center) {
                    Text("Start")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(opportunity.shoot_window_start.formatted(
                        .dateTime.hour().minute().timeZone(TimeZoneOverride.specific(tz))
                    ))
                    .font(.subheadline.monospacedDigit())
                }
                Spacer()
                VStack(alignment: .trailing) {
                    Text("Ende")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(opportunity.shoot_window_end.formatted(
                        .dateTime.hour().minute().timeZone(TimeZoneOverride.specific(tz))
                    ))
                    .font(.subheadline.monospacedDigit())
                }
            }
            .padding()
            .background(Color(.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }

    // MARK: Mini-Map

    @State private var region = MKCoordinateRegion()

    var mapSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Standort", systemImage: "map.fill")
                .font(.headline)
                .padding(.horizontal)

            Map(coordinateRegion: .constant(MKCoordinateRegion(
                center: CLLocationCoordinate2D(
                    latitude: opportunity.shoot_time.timeIntervalSince1970 > 0 ? 52.5 : 52.5,
                    longitude: 13.4
                ),
                span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
            )))
            .frame(height: 180)
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .padding(.horizontal)
        }
    }

    // MARK: Aktionen

    var actionButtons: some View {
        VStack(spacing: 12) {
            Button {
                NotificationService.shared.scheduleLocalReminder(
                    title: "📸 \(opportunity.title)",
                    body: "Jetzt losgehen – optimale Aufnahmezeit in 30 Minuten!",
                    at: opportunity.shoot_time,
                    opportunityId: opportunity.id
                )
                reminderSet = true
            } label: {
                Label(
                    reminderSet ? "Erinnerung gesetzt ✓" : "Erinnerung setzen (30 Min vorher)",
                    systemImage: reminderSet ? "bell.fill" : "bell"
                )
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(reminderSet)

            if !opportunity.location_name.isEmpty {
                Button {
                    openInMaps()
                } label: {
                    Label("In Apple Maps öffnen", systemImage: "map")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }
        }
    }

    // MARK: Helpers

    var shareText: String {
        """
        📸 FotoAlert: \(opportunity.title)
        📍 \(opportunity.location_name)
        🕐 \(opportunity.formattedDate), \(opportunity.formattedShootTime)
        📊 Score: \(opportunity.scorePercent)%
        🎯 \(opportunity.description)
        """
    }

    func openInMaps() {
        let query = opportunity.location_name.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        if let url = URL(string: "maps://?q=\(query)") {
            UIApplication.shared.open(url)
        }
    }
}

// MARK: - Supporting Views

struct ScoreBar: View {
    let label: String
    let value: Double
    let color: Color

    var body: some View {
        VStack(spacing: 4) {
            ZStack(alignment: .bottom) {
                RoundedRectangle(cornerRadius: 4)
                    .fill(color.opacity(0.15))
                    .frame(width: 40, height: 80)
                RoundedRectangle(cornerRadius: 4)
                    .fill(color)
                    .frame(width: 40, height: 80 * value)
            }
            Text(label)
                .font(.system(size: 9))
                .foregroundStyle(.secondary)
            Text("\(Int(value * 100))%")
                .font(.caption.bold())
        }
    }
}

struct InfoRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundStyle(.secondary)
                .frame(width: 20)
            Text(label)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(.subheadline.bold())
        }
    }
}

struct CameraHintCard: View {
    let hint: CameraHint

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 12) {
                Image(systemName: "camera.aperture")
                    .font(.title3)
                    .foregroundStyle(.blue)
                VStack(alignment: .leading, spacing: 2) {
                    Text("\(hint.focal_length_mm)mm · \(hint.aperture_suggestion) · \(hint.shutter_suggestion)")
                        .font(.subheadline.bold())
                    Text(hint.iso_suggestion)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            if hint.tripod_required {
                Label("Stativ empfohlen", systemImage: "camera.on.rectangle")
                    .font(.caption)
                    .foregroundStyle(.orange)
            }

            if !hint.extra_tip.isEmpty {
                Text(hint.extra_tip)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.top, 2)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}
