export function formatDuration(seconds: number | null): string {
	if (seconds === null || !Number.isFinite(seconds)) {
		return '—';
	}
	if (seconds < 60) {
		return `${seconds.toFixed(2)}s`;
	}
	const total = Math.round(seconds);
	const minutes = Math.floor(total / 60);
	const remainder = total % 60;
	return `${minutes}:${String(remainder).padStart(2, '0')}`;
}

export function formatSize(bytes: number): string {
	if (bytes < 1024) {
		return `${bytes} B`;
	}
	if (bytes < 1024 * 1024) {
		return `${(bytes / 1024).toFixed(1)} KB`;
	}
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
