// FotoAlert – Einstellungen

import SwiftUI

struct SettingsView: View {
    @AppStorage("minScore") private var minScore: Double = 0.5
    @AppStorage("notifyHighPriority") private var notifyHighPriority: Bool = true
    @AppStorage("notifyGoldenHour") private var notifyGoldenHour: Bool = true
    @AppStorage("notifyMilkyWay") private var notifyMilkyWay: Bool = false
    @AppStorage("notifyMeteors") private var notifyMeteors: Bool = true
    @AppStorage("backendURL") private var backendURL: String = "http://localhost:8000"

    @EnvironmentObject var store: OpportunityStore
    @State private var showingRefreshConfirm = false

    var body: some View {
        NavigationStack {
            Form {
                // FILTER
                Section("Filter") {
                    VStack(alignment: .leading) {
                        HStack {
                            Text("Mindest-Score")
                            Spacer()
                            Text("\(Int(minScore * 100))%")
                                .foregroundStyle(.secondary)
                        }
                        Slider(value: $minScore, in: 0.2...0.9, step: 0.05)
                            .tint(.blue)
                    }
                }

                // BENACHRICHTIGUNGEN
                Section("Benachrichtigungen") {
                    Toggle("Besondere Ereignisse (Priorität ≥ 2)", isOn: $notifyHighPriority)
                    Toggle("Goldene Stunde", isOn: $notifyGoldenHour)
                    Toggle("Milchstraße", isOn: $notifyMilkyWay)
                    Toggle("Meteoritenschauer", isOn: $notifyMeteors)
                }

                // BACKEND
                Section("Backend") {
                    HStack {
                        Text("URL")
                        Spacer()
                        TextField("http://…", text: $backendURL)
                            .multilineTextAlignment(.trailing)
                            .foregroundStyle(.secondary)
                            .autocapitalization(.none)
                    }

                    Button("Daten manuell aktualisieren") {
                        showingRefreshConfirm = true
                    }
                    .disabled(store.isLoading)
                }

                // INFO
                Section("Über FotoAlert") {
                    LabeledContent("Version", value: "1.0.0")
                    LabeledContent("Locations", value: "\(store.locations.count)")
                    if let refresh = store.lastRefresh {
                        LabeledContent("Letztes Update", value: refresh.formatted(date: .abbreviated, time: .shortened))
                    }

                    Link("Datenschutz & Lizenz", destination: URL(string: "https://github.com/stephan/fotoalert")!)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Datenquellen")
                            .font(.caption.bold())
                        Text("• Wetter: Open-Meteo (openmeteo.com)\n• Astronomie: Skyfield / JPL DE421\n• Locations: Manuell kuratiert, basierend auf Locationscout")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Einstellungen")
            .confirmationDialog(
                "Daten aktualisieren?",
                isPresented: $showingRefreshConfirm,
                titleVisibility: .visible
            ) {
                Button("Aktualisieren") {
                    Task { await store.refresh() }
                }
                Button("Abbrechen", role: .cancel) {}
            } message: {
                Text("Das Backend berechnet alle Foto-Chancen neu. Dauert ca. 30 Sekunden.")
            }
        }
    }
}
