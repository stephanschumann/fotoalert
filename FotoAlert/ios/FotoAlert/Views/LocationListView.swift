// FotoAlert – Locations-Liste

import SwiftUI

struct LocationListView: View {
    @EnvironmentObject var store: OpportunityStore
    @State private var searchText = ""
    @State private var selectedCategory: String? = nil

    let categories = [
        "Schloss & Historisch",
        "Skyline & Architektur",
        "Natur & Landschaft",
        "Wasser & Spiegelung",
        "Aussichtspunkt",
        "Industrie & Urban",
        "Milchstraße & Astro",
    ]

    var filtered: [PhotoLocation] {
        store.locations
            .filter { loc in
                (selectedCategory == nil || loc.category == selectedCategory) &&
                (searchText.isEmpty || loc.name.localizedCaseInsensitiveContains(searchText) ||
                 loc.description.localizedCaseInsensitiveContains(searchText))
            }
            .sorted { $0.name < $1.name }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Kategorie-Filter
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        FilterChip(label: "Alle", isSelected: selectedCategory == nil) {
                            selectedCategory = nil
                        }
                        ForEach(categories, id: \.self) { cat in
                            FilterChip(label: cat.components(separatedBy: " ").first ?? cat,
                                       isSelected: selectedCategory == cat) {
                                selectedCategory = selectedCategory == cat ? nil : cat
                            }
                        }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                }
                .background(Color(.systemGroupedBackground))

                // Liste
                List(filtered) { location in
                    NavigationLink {
                        LocationDetailView(location: location)
                    } label: {
                        LocationRow(location: location)
                    }
                }
                .listStyle(.plain)
            }
            .searchable(text: $searchText, prompt: "Location suchen")
            .navigationTitle("Locations")
        }
    }
}

struct FilterChip: View {
    let label: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.subheadline)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? Color.blue : Color(.systemGray5))
                .foregroundStyle(isSelected ? .white : .primary)
                .clipShape(Capsule())
        }
    }
}

struct LocationRow: View {
    let location: PhotoLocation

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: categoryIcon(location.category))
                .foregroundStyle(.blue)
                .frame(width: 32, height: 32)
                .background(Color.blue.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            VStack(alignment: .leading, spacing: 2) {
                Text(location.name)
                    .font(.subheadline.bold())
                Text(location.category)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            DifficultyBadge(difficulty: location.difficulty, label: location.difficultyLabel)
        }
        .padding(.vertical, 4)
    }

    func categoryIcon(_ cat: String) -> String {
        if cat.contains("Schloss") { return "building.columns.fill" }
        if cat.contains("Skyline") { return "building.2.fill" }
        if cat.contains("Natur") { return "leaf.fill" }
        if cat.contains("Wasser") { return "water.waves" }
        if cat.contains("Aussicht") { return "binoculars.fill" }
        if cat.contains("Industrie") { return "wrench.and.screwdriver.fill" }
        if cat.contains("Astro") { return "sparkles" }
        return "mappin.fill"
    }
}

// MARK: - Location Detail

struct LocationDetailView: View {
    let location: PhotoLocation
    @EnvironmentObject var store: OpportunityStore

    var locationOpportunities: [PhotoOpportunity] {
        store.opportunities
            .filter { $0.location_id == location.id }
            .sorted { $0.overall_score > $1.overall_score }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {

                // Header
                VStack(alignment: .leading, spacing: 6) {
                    Text(location.category)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(location.name)
                        .font(.title2.bold())
                    Text(location.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal)

                // Focal Lengths
                HStack {
                    ForEach(location.focal_length_suggestions, id: \.self) { fl in
                        Label("\(fl)mm", systemImage: "camera.aperture")
                            .font(.subheadline)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color.blue.opacity(0.1))
                            .foregroundStyle(.blue)
                            .clipShape(Capsule())
                    }
                }
                .padding(.horizontal)

                // Alignment Notes
                if !location.solar_alignment_note.isEmpty {
                    infoCard(icon: "sun.max.fill", color: .orange,
                             title: "Sonnen-Alignment", text: location.solar_alignment_note)
                }
                if !location.lunar_alignment_note.isEmpty {
                    infoCard(icon: "moon.fill", color: .indigo,
                             title: "Mond-Alignment", text: location.lunar_alignment_note)
                }
                if !location.special_notes.isEmpty {
                    infoCard(icon: "info.circle.fill", color: .teal,
                             title: "Hinweise", text: location.special_notes)
                }
                if !location.access_note.isEmpty {
                    infoCard(icon: "figure.walk", color: .green,
                             title: "Zugang", text: location.access_note)
                }

                // Upcoming Opportunities
                if !locationOpportunities.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Kommende Chancen")
                            .font(.headline)
                            .padding(.horizontal)

                        ForEach(locationOpportunities.prefix(5)) { opp in
                            OpportunityCard(opportunity: opp)
                                .padding(.horizontal)
                        }
                    }
                }
            }
            .padding(.top)
        }
        .navigationTitle(location.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    func infoCard(icon: String, color: Color, title: String, text: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .foregroundStyle(color)
                .font(.title3)
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline.bold())
                Text(text)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(color.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .padding(.horizontal)
    }
}
