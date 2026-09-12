export const LOCATION_IDS = ['all', 'downloaded', 'recent'] as const;

export type LocationId = (typeof LOCATION_IDS)[number];

export const LOCATIONS: { id: LocationId; label: string; icon: string }[] = [
	{ id: 'all', label: 'All Samples', icon: 'icon-[lucide--music]' },
	{ id: 'downloaded', label: 'Downloaded', icon: 'icon-[lucide--download]' },
	{ id: 'recent', label: 'Recently Added', icon: 'icon-[lucide--clock]' }
];

const LOCATION_SET = new Set<string>(LOCATION_IDS);

export function parseLocation(raw: string | null): LocationId {
	if (raw !== null && LOCATION_SET.has(raw)) {
		return raw as LocationId;
	}
	return 'all';
}

export function emptyListText(location: LocationId): string {
	if (location === 'downloaded') {
		return 'No cached samples.';
	}
	if (location === 'recent') {
		return 'No samples modified in the last 7 days.';
	}
	return 'No samples in the library.';
}
