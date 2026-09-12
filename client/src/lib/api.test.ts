import { expect, test } from 'vitest';
import {
	apiBase,
	audioUrl,
	catalogEntriesUrl,
	catalogFilesUrl,
	catalogScanSocketUrl,
	DEFAULT_API_BASE,
	fetchFiles,
	fetchListing,
	parseScanProgress,
	scanPercent
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
	channels: 1,
	bpm: 128,
	key: 'Cm',
	tags: ['one-shot', 'kick']
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

test('files url includes offset, prefix, query, and sort', () => {
	expect(catalogFilesUrl({ offset: 50, prefix: 'Drums', q: 'kick', sort: 'name' }, BASE)).toBe(
		'http://127.0.0.1:8000/catalog/files?offset=50&prefix=Drums&q=kick&sort=name'
	);
});

test('files url appends repeated tag filters', () => {
	expect(catalogFilesUrl({ tags: ['kick', 'loop'] }, BASE)).toBe(
		'http://127.0.0.1:8000/catalog/files?tag=kick&tag=loop'
	);
});

test('audio url encodes each path segment', () => {
	expect(audioUrl('Pack/kick 01.wav', BASE)).toBe(
		'http://127.0.0.1:8000/audio/Pack/kick%2001.wav'
	);
});

test('scan socket url upgrades http to ws', () => {
	expect(catalogScanSocketUrl(BASE)).toBe('ws://127.0.0.1:8000/catalog/scan');
	expect(catalogScanSocketUrl('https://nas:8000/')).toBe('wss://nas:8000/catalog/scan');
});

test('parseScanProgress reads a running snapshot', () => {
	expect(parseScanProgress('{"status":"running","done":12,"total":48}')).toEqual({
		status: 'running',
		done: 12,
		total: 48
	});
	expect(parseScanProgress('nope')).toBeNull();
	expect(scanPercent({ status: 'running', done: 1, total: 4 })).toBe(25);
	expect(scanPercent({ status: 'running', done: 0, total: 0 })).toBe(0);
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
