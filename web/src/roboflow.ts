export interface Prediction {
    x: number; // centre
    y: number; // centre
    width: number;
    height: number;
    confidence: number;
    class: string;
}

export interface InferenceResult {
    image: { width: number; height: number };
    predictions: Prediction[];
}

const ENDPOINT = 'https://serverless.roboflow.com/infer/object_detection';

/** Calls Roboflow's hosted inference API directly from the browser. */
export async function detect(
    apiKey: string,
    modelId: string,
    imageBase64: string,
): Promise<InferenceResult> {
    let response: Response;
    try {
        response = await fetch(ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // The key travels in the request body, not the URL.
            body: JSON.stringify({
                api_key: apiKey,
                model_id: modelId,
                image: { type: 'base64', value: imageBase64 },
                confidence: 0.05, // ask for everything; the slider filters client-side
            }),
        });
    } catch {
        // Roboflow sends no CORS headers on some error responses, so a rejected
        // key can surface here as a network failure.
        throw new Error(
            'Could not reach Roboflow. Check the API key and your connection, then try again.',
        );
    }

    if (!response.ok) {
        let detail = '';
        try {
            const body = await response.json();
            detail = body.message ?? body.detail ?? '';
        } catch {
            // not JSON
        }
        if (response.status === 401 || response.status === 403) {
            throw new Error('Roboflow rejected the API key.');
        }
        throw new Error(`Roboflow returned ${response.status}${detail ? `: ${detail}` : ''}.`);
    }

    const data = await response.json();
    // A single image can come back as an object or a one-element list.
    const result = Array.isArray(data) ? data[0] : data;
    if (!result?.predictions || !result?.image) {
        throw new Error('Unexpected response from Roboflow.');
    }
    return result as InferenceResult;
}

/** Downscales large photos and returns base64 JPEG data plus an object URL for display. */
export async function prepareImage(
    file: File,
    maxSide = 1600,
): Promise<{ base64: string; previewUrl: string; width: number; height: number }> {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    const width = Math.round(bitmap.width * scale);
    const height = Math.round(bitmap.height * scale);

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d')!.drawImage(bitmap, 0, 0, width, height);
    bitmap.close();

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    return { base64: dataUrl.split(',')[1], previewUrl: dataUrl, width, height };
}
