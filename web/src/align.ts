import type { Prediction } from './roboflow';

// TypeScript port of RectangleAligner in parkinglotlayout/generate-layout.py:
// box edges that sit within `threshold` pixels of each other are snapped to a
// shared line, so rows and columns of spaces line up.

function clusterLines(sorted: number[], threshold: number): number[] {
    if (sorted.length === 0) return [];
    const lines: number[] = [];
    let cluster = [sorted[0]];
    for (const value of sorted.slice(1)) {
        if (value - cluster[cluster.length - 1] <= threshold) {
            cluster.push(value);
        } else {
            lines.push(cluster.reduce((a, b) => a + b, 0) / cluster.length);
            cluster = [value];
        }
    }
    lines.push(cluster.reduce((a, b) => a + b, 0) / cluster.length);
    return lines;
}

function snap(value: number, lines: number[], threshold: number): number {
    let best = value;
    let bestDistance = Infinity;
    for (const line of lines) {
        const distance = Math.abs(line - value);
        if (distance < bestDistance) {
            best = line;
            bestDistance = distance;
        }
    }
    return bestDistance <= threshold ? best : value;
}

export function alignPredictions(predictions: Prediction[], threshold = 30): Prediction[] {
    const edges = predictions.map((p) => ({
        left: p.x - p.width / 2,
        right: p.x + p.width / 2,
        top: p.y - p.height / 2,
        bottom: p.y + p.height / 2,
    }));
    const byValue = (a: number, b: number) => a - b;
    const xLines = clusterLines(edges.flatMap((e) => [e.left, e.right]).sort(byValue), threshold);
    const yLines = clusterLines(edges.flatMap((e) => [e.top, e.bottom]).sort(byValue), threshold);

    return predictions.map((p, i) => {
        const left = snap(edges[i].left, xLines, threshold);
        const right = snap(edges[i].right, xLines, threshold);
        const top = snap(edges[i].top, yLines, threshold);
        const bottom = snap(edges[i].bottom, yLines, threshold);
        // Keep the original box if snapping would collapse it.
        if (right - left < 2 || bottom - top < 2) return p;
        return {
            ...p,
            x: (left + right) / 2,
            y: (top + bottom) / 2,
            width: right - left,
            height: bottom - top,
        };
    });
}
