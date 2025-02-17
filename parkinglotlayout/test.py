from inference_sdk import InferenceHTTPClient
import base64

with open("parkinglotlayout/parkinglotimages/parkinglot7.jpg", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="hZHL7nrK0z63BmXWx6dI"
)

result = client.run_workflow(
    workspace_name="parkeasy",
    workflow_id="detect-count-and-visualize-2",
    images={
        "image": [encoded_string]
    },
    use_cache=True # cache workflow definition for 15 minutes
)

print(result)