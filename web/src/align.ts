import type { Prediction } from './roboflow';

// Lines the detected boxes up into a tidy layout. Boxes are grouped into rows,
// each row gets a shared top and bottom, and neighbouring spaces meet at a
// single boundary halfway between their detected edges, so no space is drawn
// over the one beside it.
//
// This replaces a direct port of RectangleAligner in
// parkinglotlayout/generate-layout.py, which snapped every edge to the nearest
// cluster of edges. Spaces are about as wide as that clustering distance, so
// an edge could jump to a neighbour's line and stretch a space across it.

interface Box {
    index: number;
    start: number; // along the row
    end: number;
    lo: number; // across the row
    hi: number;
}

function median(values: number[]): number {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = sorted.length >> 1;
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function groupRows(boxes: Box[], tolerance: number): Box[][] {
    const sorted = [...boxes].sort((a, b) => a.lo + a.hi - (b.lo + b.hi));
    const rows: Box[][] = [];
    let centreSum = 0;
    for (const box of sorted) {
        const centre = (box.lo + box.hi) / 2;
        const row = rows[rows.length - 1];
        if (row && centre - centreSum / row.length <= tolerance) {
            row.push(box);
            centreSum += centre;
        } else {
            rows.push([box]);
            centreSum = centre;
        }
    }
    return rows;
}

function alignRow(row: Box[], gapLimit: number): void {
    // Shared top and bottom, except for boxes that clearly do not fit the row.
    const lo = median(row.map((b) => b.lo));
    const hi = median(row.map((b) => b.hi));
    const reach = (hi - lo) / 4;
    for (const box of row) {
        if (Math.abs(box.lo - lo) <= reach) box.lo = lo;
        if (Math.abs(box.hi - hi) <= reach) box.hi = hi;
    }

    // Neighbours that overlap or nearly touch share one boundary.
    row.sort((a, b) => a.start + a.end - (b.start + b.end));
    for (let i = 1; i < row.length; i++) {
        const prev = row[i - 1];
        const cur = row[i];
        if (cur.start - prev.end > gapLimit) continue; // a real gap, e.g. a driveway
        const boundary = (prev.end + cur.start) / 2;
        if (boundary - prev.start < 2 || cur.end - boundary < 2) continue;
        prev.end = boundary;
        cur.start = boundary;
    }
}

export function alignPredictions(predictions: Prediction[]): Prediction[] {
    if (predictions.length < 2) return predictions;

    // Spaces sit side by side along their short edge. When the boxes are wider
    // than tall the rows run vertically, so work on swapped axes.
    const upright = median(predictions.map((p) => p.width)) <= median(predictions.map((p) => p.height));
    const boxes: Box[] = predictions.map((p, index) => {
        const [along, across, size, depth] = upright
            ? [p.x, p.y, p.width, p.height]
            : [p.y, p.x, p.height, p.width];
        return {
            index,
            start: along - size / 2,
            end: along + size / 2,
            lo: across - depth / 2,
            hi: across + depth / 2,
        };
    });

    const size = median(boxes.map((b) => b.end - b.start));
    const depth = median(boxes.map((b) => b.hi - b.lo));
    for (const row of groupRows(boxes, depth / 2)) alignRow(row, size / 2);

    const result = [...predictions];
    for (const box of boxes) {
        const along = (box.start + box.end) / 2;
        const across = (box.lo + box.hi) / 2;
        const p = predictions[box.index];
        result[box.index] = upright
            ? { ...p, x: along, y: across, width: box.end - box.start, height: box.hi - box.lo }
            : { ...p, x: across, y: along, width: box.hi - box.lo, height: box.end - box.start };
    }
    return result;
}
