export const KEY_ROOTS = [
	'C',
	'C#',
	'D',
	'D#',
	'E',
	'F',
	'F#',
	'G',
	'G#',
	'A',
	'A#',
	'B'
] as const;

export const BPM_RANGES = [
	{ id: '70-90', label: '70–90', min: 70, max: 90 },
	{ id: '90-110', label: '90–110', min: 90, max: 110 },
	{ id: '110-130', label: '110–130', min: 110, max: 130 },
	{ id: '130-150', label: '130–150', min: 130, max: 150 },
	{ id: '150+', label: '150+', min: 150, max: null }
] as const;

const KEY_ROOT_SET = new Set<string>(KEY_ROOTS);
const BPM_IDS = new Set<string>(BPM_RANGES.map((range) => range.id));

export function parseKey(raw: string | null): string {
	if (raw !== null && KEY_ROOT_SET.has(raw)) {
		return raw;
	}
	return '';
}

export function parseBpm(raw: string | null): string {
	if (raw !== null && BPM_IDS.has(raw)) {
		return raw;
	}
	return '';
}
