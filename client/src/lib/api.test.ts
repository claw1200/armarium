import { expect, test } from 'vitest';
import {
	apiBase,
	audioUrl,
	catalogEntriesUrl,
	catalogFilesUrl,
	DEFAULT_API_BASE,
	fetchFiles,
	fetchListing
} from './api';

const BASE = 'http://127.0.0.1:8000';

const kick = {
	name: 'kick.wav',
	path: 'Drums/Kicks/kick.wav',
	parent_path: 'Drums/Kicks',
	size_bytes: 100,
	format: 'wav',
	duration_seconds: 0.1,
	sample_rate: 44100,
	channels: 1
};

test('apiBase uses a configured origin', () => {
	expect(apiBase('http://nas:8000/')).toBe('http://nas:8000');
});

test('apiBase falls back to the local server', () => {
	expect(apiBase(undefined)).toBe(DEFAULT_API_BASE);
	expect(apiBase('  ')).toBe(DEFAULT_API_BASE);
});

test('catalog url omits path at the library root', () => {
	expect(catalogEntriesUrl('', BASE)).toBe('http://127.0.0.1:8000/catalog/entries');
});

test('catalog url includes a nested folder path', () => {
	expect(catalogEntriesUrl('Drums/Kicks', BASE)).toBe(
		'http://127.0.0.1:8000/catalog/entries?path=Drums%2FKicks'
	);
});

test('files url omits default pagination', () => {
	expect(catalogFilesUrl({}, BASE)).toBe('http://127.0.0.1:8000/catalog/files');
});

test('files url includes offset, prefix, and sort', () => {
	expect(catalogFilesUrl({ offset: 50, prefix: 'Drums', sort: 'name' }, BASE)).toBe(
		'http://127.0.0.1:8000/catalog/files?offset=50&prefix=Drums&sort=name'
	);
});

test('audio url encodes each path segment', () => {
	expect(audioUrl('Pack/kick 01.wav', BASE)).toBe(
		'http://127.0.0.1:8000/audio/Pack/kick%2001.wav'
	);
});

test('fetchListing returns json from a successful response', async () => {
	const listing = {
		path: 'Drums/Kicks',
		folders: [],
		files: [kick]
	};
	const result = await fetchListing(
		'Drums/Kicks',
		async () => new Response(JSON.stringify(listing)),
		BASE
	);
	expect(result).toEqual(listing);
});

test('fetchListing throws when the catalog is unavailable', async () => {
	await expect(
		fetchListing('Drums', async () => new Response('nope', { status: 500 }), BASE)
	).rejects.toThrow('Catalog request failed (500)');
});

test('fetchFiles returns a catalog page', async () => {
	const page = { items: [kick], total: 1, limit: 50, offset: 0 };
	const result = await fetchFiles({}, async () => new Response(JSON.stringify(page)), BASE);
	expect(result).toEqual(page);
});

test('fetchFiles throws when the catalog is unavailable', async () => {
	await expect(
		fetchFiles({ offset: 50 }, async () => new Response('nope', { status: 500 }), BASE)
	).rejects.toThrow('Catalog request failed (500)');
});
