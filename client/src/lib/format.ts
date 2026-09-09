export function formatDuration(seconds: number | null): string {
	if (seconds === null || !Number.isFinite(seconds)) {
		return '—';
	}
	const rounded = Math.round(seconds);
	const total = seconds > 0 ? Math.max(1, rounded) : 0;
	const minutes = Math.floor(total / 60);
	const remainder = total % 60;
	return `${minutes}:${String(remainder).padStart(2, '0')}`;
}

export function formatAudioFormat(format: string): string {
	return format.toUpperCase();
}

export function fileStem(name: string): string {
	const lastDot = name.lastIndexOf('.');
	if (lastDot <= 0) {
		return name;
	}
	return name.slice(0, lastDot);
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
