import requests
import json
import base64

def retrieve_key():
    try:
        file = open('.keystore-dev', 'r')
    except OSError:
        file = open('.keystore', 'r')
    key = file.read()
    file.close()
    return key


def start_dog_recognition():
    global api_key

    with open('assets/shih-tzu_01.jpg', 'rb') as file:
        image = file.read()
    image_as_b64 = base64.b64encode(image).decode('ascii')

    url = 'https://vision.googleapis.com/v1/images:annotate'
    params = {'key': api_key}
    payload = {
        "requests": [
            {
                "features": [
                    {
                        "maxResults": 50,
                        "type": "LABEL_DETECTION"
                    },
                ],
                "image": {
                    "content": f"{image_as_b64}"
                }
            }
        ]
    }

    request = requests.post(url, params=params, data=json.dumps(payload))

    print(request.status_code)
    print(request.json())


if __name__ == '__main__':
    api_key = retrieve_key()
    start_dog_recognition()
