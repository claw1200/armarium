export type SidebarLink = {
	id: string;
	label: string;
};

export type FilterGroup = {
	id: string;
	label: string;
	options: string[];
};

export const favouriteFolders: SidebarLink[] = [
	{ id: 'all', label: 'All Samples' },
	{ id: 'recents', label: 'Recents' },
	{ id: 'drums', label: 'Drums' },
	{ id: 'percussion', label: 'Percussion' },
	{ id: 'melodic', label: 'Melodic' },
	{ id: 'fx', label: 'FX' }
];

export const sidebarTags: SidebarLink[] = [
	{ id: 'kick', label: 'kick' },
	{ id: 'snare', label: 'snare' },
	{ id: 'hat', label: 'hat' },
	{ id: 'bass', label: 'bass' },
	{ id: 'loop', label: 'loop' },
	{ id: 'one-shot', label: 'one-shot' }
];

export const filterGroups: FilterGroup[] = [
	{ id: 'instruments', label: 'Instruments', options: ['Drums', 'Bass', 'Synth', 'Vocals', 'Guitar'] },
	{ id: 'genres', label: 'Genres', options: ['House', 'Techno', 'Hip Hop', 'Cinematic', 'Pop'] },
	{ id: 'key', label: 'Key', options: ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] },
	{ id: 'bpm', label: 'BPM', options: ['70–90', '90–110', '110–130', '130–150', '150+'] },
	{ id: 'type', label: 'One-Shots & Loops', options: ['One-Shots', 'Loops'] }
];

export const filterTags = [
	'fx',
	'impacts',
	'cinematic',
	'game audio',
	'edm',
	'percussion',
	'drums',
	'atmos',
	'riser',
	'sweep'
];

export const sortOptions = ['Most recent', 'Name', 'Duration', 'Most popular'] as const;
