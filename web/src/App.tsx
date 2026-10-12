import { useEffect, useMemo, useRef, useState } from 'react';
import { alignPredictions } from './align';
import { detect, prepareImage, type InferenceResult, type Prediction } from './roboflow';

const DEFAULT_MODEL = 'ultimate-form/1';
const KEY_STORAGE = 'parkeasy.roboflowKey';
const MODEL_STORAGE = 'parkeasy.modelId';

function readStored(name: string): string {
    try {
        return localStorage.getItem(name) ?? '';
    } catch {
        return '';
    }
}

function writeStored(name: string, value: string | null) {
    try {
        if (value === null) localStorage.removeItem(name);
        else localStorage.setItem(name, value);
    } catch {
        // storage unavailable (private window); the page still works
    }
}

function statusOf(p: Prediction): 'free' | 'occupied' | 'other' {
    if (p.class === 'free') return 'free';
    if (p.class === 'car') return 'occupied';
    return 'other';
}

type Photo = { previewUrl: string; base64: string; width: number; height: number; name: string };

export default function App() {
    const [apiKey, setApiKey] = useState(() => readStored(KEY_STORAGE));
    const [remember, setRemember] = useState(() => readStored(KEY_STORAGE) !== '');
    const [modelId, setModelId] = useState(() => readStored(MODEL_STORAGE) || DEFAULT_MODEL);
    const [photo, setPhoto] = useState<Photo | null>(null);
    const [result, setResult] = useState<InferenceResult | null>(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [minConfidence, setMinConfidence] = useState(0.4);
    const [aligned, setAligned] = useState(true);
    const [dragging, setDragging] = useState(false);
    const [elapsed, setElapsed] = useState<number | null>(null);
    const fileInput = useRef<HTMLInputElement>(null);

    useEffect(() => {
        writeStored(KEY_STORAGE, remember && apiKey ? apiKey : null);
    }, [apiKey, remember]);

    useEffect(() => {
        writeStored(MODEL_STORAGE, modelId && modelId !== DEFAULT_MODEL ? modelId : null);
    }, [modelId]);

    const visible = useMemo(
        () => (result ? result.predictions.filter((p) => p.confidence >= minConfidence) : []),
        [result, minConfidence],
    );
    const layout = useMemo(() => (aligned ? alignPredictions(visible) : visible), [visible, aligned]);
    const counts = useMemo(() => {
        const free = visible.filter((p) => statusOf(p) === 'free').length;
        const occupied = visible.filter((p) => statusOf(p) === 'occupied').length;
        return { free, occupied, total: free + occupied };
    }, [visible]);

    async function run(next: Photo) {
        setError('');
        setResult(null);
        setElapsed(null);
        if (!apiKey.trim()) {
            setError('Enter your Roboflow API key first.');
            return;
        }
        setBusy(true);
        const started = performance.now();
        try {
            const data = await detect(apiKey.trim(), modelId.trim() || DEFAULT_MODEL, next.base64);
            setResult(data);
            setElapsed((performance.now() - started) / 1000);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Something went wrong.');
        } finally {
            setBusy(false);
        }
    }

    async function handleFile(file: File | undefined) {
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            setError('That file is not an image.');
            return;
        }
        try {
            const prepared = await prepareImage(file);
            const next = { ...prepared, name: file.name };
            setPhoto(next);
            await run(next);
        } catch {
            setError('Could not read that image.');
        }
    }

    const width = result?.image.width ?? photo?.width ?? 0;
    const height = result?.image.height ?? photo?.height ?? 0;
    const stroke = Math.max(2, Math.round(Math.max(width, height) / 400));

    return (
        <main>
            <header>
                <h1>ParkEasy model tester</h1>
                <p>
                    Upload a parking-lot photo to see what the detection model finds and the layout
                    generated from it.
                </p>
            </header>

            <section className="panel settings" aria-label="Settings">
                <label>
                    <span>Roboflow API key</span>
                    <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="Paste your key"
                        autoComplete="off"
                        spellCheck={false}
                    />
                </label>
                <label>
                    <span>Model</span>
                    <input
                        type="text"
                        value={modelId}
                        onChange={(e) => setModelId(e.target.value)}
                        placeholder={DEFAULT_MODEL}
                        spellCheck={false}
                    />
                </label>
                <label className="check">
                    <input
                        type="checkbox"
                        checked={remember}
                        onChange={(e) => setRemember(e.target.checked)}
                    />
                    <span>Remember the key in this browser</span>
                </label>
                <p className="note">
                    The key is sent only to Roboflow, straight from your browser. It is never
                    uploaded to this site or stored in the repository.
                </p>
            </section>

            <section
                className={`panel drop${dragging ? ' dragging' : ''}`}
                onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                    e.preventDefault();
                    setDragging(false);
                    void handleFile(e.dataTransfer.files[0]);
                }}
            >
                <p>Drop a parking-lot photo here, or</p>
                <button type="button" onClick={() => fileInput.current?.click()} disabled={busy}>
                    Choose a photo
                </button>
                <input
                    ref={fileInput}
                    type="file"
                    accept="image/*"
                    hidden
                    onChange={(e) => {
                        void handleFile(e.target.files?.[0]);
                        e.target.value = '';
                    }}
                />
                {photo && !busy && (
                    <button type="button" className="secondary" onClick={() => void run(photo)}>
                        Run again on {photo.name}
                    </button>
                )}
            </section>

            {error && (
                <p className="error" role="alert">
                    {error}
                </p>
            )}
            {busy && <p className="status">Detecting spaces…</p>}

            {result && (
                <>
                    <section className="panel stats" aria-label="Counts">
                        <div className="stat free">
                            <strong>{counts.free}</strong>
                            <span>Free</span>
                        </div>
                        <div className="stat occupied">
                            <strong>{counts.occupied}</strong>
                            <span>Occupied</span>
                        </div>
                        <div className="stat">
                            <strong>{counts.total}</strong>
                            <span>Total</span>
                        </div>
                        <div className="controls">
                            <label>
                                <span>Minimum confidence: {Math.round(minConfidence * 100)}%</span>
                                <input
                                    type="range"
                                    min={0.05}
                                    max={0.95}
                                    step={0.05}
                                    value={minConfidence}
                                    onChange={(e) => setMinConfidence(Number(e.target.value))}
                                />
                            </label>
                            <label className="check">
                                <input
                                    type="checkbox"
                                    checked={aligned}
                                    onChange={(e) => setAligned(e.target.checked)}
                                />
                                <span>Align layout to a grid</span>
                            </label>
                        </div>
                    </section>

                    {visible.length === 0 && (
                        <p className="status">
                            No spaces at this confidence. Lower the slider, or try another photo.
                        </p>
                    )}

                    <section className="views">
                        <figure className="panel">
                            <figcaption>Detections</figcaption>
                            <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Photo with detected spaces">
                                {photo && <image href={photo.previewUrl} width={width} height={height} />}
                                {visible.map((p, i) => (
                                    <rect
                                        key={i}
                                        className={`box ${statusOf(p)}`}
                                        x={p.x - p.width / 2}
                                        y={p.y - p.height / 2}
                                        width={p.width}
                                        height={p.height}
                                        strokeWidth={stroke}
                                    >
                                        <title>{`${p.class} ${Math.round(p.confidence * 100)}%`}</title>
                                    </rect>
                                ))}
                            </svg>
                        </figure>
                        <figure className="panel">
                            <figcaption>Layout</figcaption>
                            <svg
                                className="layout"
                                viewBox={`0 0 ${width} ${height}`}
                                role="img"
                                aria-label="Generated parking layout"
                            >
                                <rect width={width} height={height} className="lot" />
                                {layout.map((p, i) => (
                                    <rect
                                        key={i}
                                        className={`space ${statusOf(p)}`}
                                        x={p.x - p.width / 2}
                                        y={p.y - p.height / 2}
                                        width={p.width}
                                        height={p.height}
                                        strokeWidth={stroke}
                                        rx={stroke * 2}
                                    />
                                ))}
                            </svg>
                        </figure>
                    </section>

                    <p className="meta">
                        {result.predictions.length} raw predictions from <code>{modelId}</code>
                        {elapsed !== null && <> in {elapsed.toFixed(1)} s</>} · image sent at {width}×{height}
                    </p>
                    <details className="panel">
                        <summary>Raw response</summary>
                        <pre>{JSON.stringify(result, null, 2)}</pre>
                    </details>
                </>
            )}
        </main>
    );
}
