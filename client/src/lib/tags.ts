export const FACET_FORM = 'form';
export const FACET_ROLE = 'role';
export const FACET_FUNCTION = 'function';
export const FACET_ORDER = [FACET_FORM, FACET_ROLE, FACET_FUNCTION] as const;

export type TagFacet = (typeof FACET_ORDER)[number];

export const FACET_LABELS: Record<TagFacet, string> = {
	form: 'Form',
	role: 'Role',
	function: 'Function'
};

export const TAGS_BY_FACET: Record<TagFacet, readonly string[]> = {
	form: ['loop', 'one-shot'],
	role: [
		'kick',
		'snare',
		'clap',
		'hat',
		'ride',
		'crash',
		'tom',
		'perc',
		'bass',
		'synth',
		'pad',
		'keys',
		'guitar',
		'vocal',
		'fx'
	],
	function: ['melody', 'chord', 'arp', 'rhythm', 'texture', 'riser', 'impact', 'sweep']
};

export const TAG_FACET: Readonly<Record<string, TagFacet>> = Object.fromEntries(
	FACET_ORDER.flatMap((facet) => TAGS_BY_FACET[facet].map((slug) => [slug, facet]))
);

export function parseTags(raw: readonly string[]): string[] {
	const byFacet: Partial<Record<TagFacet, string>> = {};
	for (const slug of raw) {
		const facet = TAG_FACET[slug];
		if (facet === undefined || byFacet[facet] !== undefined) {
			continue;
		}
		byFacet[facet] = slug;
	}
	return FACET_ORDER.flatMap((facet) => {
		const slug = byFacet[facet];
		return slug === undefined ? [] : [slug];
	});
}

export function tagForFacet(tags: readonly string[], facet: TagFacet): string {
	return tags.find((slug) => TAG_FACET[slug] === facet) ?? '';
}

export function setFacetTag(tags: readonly string[], facet: TagFacet, slug: string): string[] {
	if (slug !== '' && TAG_FACET[slug] !== facet) {
		return parseTags(tags);
	}
	const next = tags.filter((tag) => TAG_FACET[tag] !== facet);
	if (slug !== '') {
		next.push(slug);
	}
	return parseTags(next);
}
